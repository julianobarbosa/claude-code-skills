#!/usr/bin/env bun
// Cut a release for a pull request that is already open (the `ship` skill opens it).
//
// End state, each part read back:
//   - release/vX.Y.Z exists on origin at the base branch's tip
//   - with --bump: the PR's source branch carries a merge of the base plus one
//     `chore(release): X.Y.Z` commit that sets the version file, refreshes the
//     lockfile and moves CHANGELOG [Unreleased] into [X.Y.Z]; pushed as a
//     fast-forward, never forced
//   - the PR targets release/vX.Y.Z instead of the base
//
// Usage:
//   bun ReleaseCut.ts --version X.Y.Z --pr <id> [--base main] [--bump]
//                     [--description-file <file.md>] [--prefix release/] [--dry-run]
//
// Exit codes: 0 ok · 1 failure · 2 usage · 3 refused by a guard (nothing written)
// Output: key=value lines on stdout; progress on stderr.

import { existsSync, readFileSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import {
  API, Refusal, UsageError, adoParts, azRest, bumpVersionFiles, compareSemver, git, gitPush, localTagCommit,
  note, out, parseSemver, prUrl, remoteBranchSha, remoteTagCommit, repoWeb, run, sh, today, withWorktree,
} from "./Lib.ts";
import { releaseChangelog } from "./Changelog.ts";

const USAGE =
  "Usage: bun ReleaseCut.ts --version X.Y.Z --pr <id> [--base main] [--bump] [--description-file <md>] [--prefix release/] [--dry-run]";

await run(() => {
  let version = "";
  let pr = "";
  let base = "main";
  let bump = false;
  let descFile = "";
  let prefix = "release/";
  let dry = false;
  const argv = process.argv.slice(2);
  for (let i = 0; i < argv.length; i++) {
    switch (argv[i]) {
      case "--version": version = argv[++i] ?? ""; break;
      case "--pr": pr = argv[++i] ?? ""; break;
      case "--base": base = argv[++i] ?? ""; break;
      case "--bump": bump = true; break;
      case "--description-file": descFile = argv[++i] ?? ""; break;
      case "--prefix": prefix = argv[++i] ?? ""; break;
      case "--dry-run": dry = true; break;
      case "-h": case "--help": console.log(USAGE); return;
      default: throw new UsageError(`unknown arg: ${argv[i]}\n${USAGE}`);
    }
  }
  const sv = parseSemver(version);
  if (!sv) throw new UsageError(`--version must be SemVer (X.Y.Z), got '${version}'\n${USAGE}`);
  version = sv.raw;
  if (!/^\d+$/.test(pr)) throw new UsageError(`--pr must be a numeric pull request id\n${USAGE}`);
  if (descFile && !existsSync(descFile)) throw new UsageError(`--description-file not found: ${descFile}`);
  const description = descFile ? readFileSync(descFile, "utf8") : "";
  const tag = `v${version}`;
  const branch = `${prefix}${tag}`;
  const ado = adoParts();
  if (!ado) throw new UsageError("origin is not an Azure DevOps remote; ReleaseCut drives Azure DevOps PRs only");

  git(["fetch", "-q", "--prune", "--tags", "origin"]);

  // ---- guards: all of them run before anything is written
  const prj = azRest("get", prUrl(ado, pr), undefined, { allowFail: true });
  if (!prj) throw new Refusal(`PR ${pr} not found (or az is not logged in)`);
  if (prj.status !== "active") throw new Refusal(`PR ${pr} is ${prj.status}; cut a release only from an active PR`);
  const source = String(prj.sourceRefName).replace(/^refs\/heads\//, "");
  const currentTarget = String(prj.targetRefName).replace(/^refs\/heads\//, "");
  if (remoteBranchSha(branch)) throw new Refusal(`${branch} already exists on origin; refusing to move it`);
  if (remoteTagCommit(tag) || localTagCommit(tag)) throw new Refusal(`tag ${tag} already exists; pick the next version`);
  const semverTags = git(["tag", "--list", "v*"]).split("\n").filter((t) => t && parseSemver(t));
  const latest = semverTags.sort(compareSemver).at(-1);
  if (latest && compareSemver(version, latest) <= 0) throw new Refusal(`${tag} is not greater than the latest tag ${latest}`);
  if (description.length > 4000) throw new Refusal(`description is ${description.length} chars; Azure DevOps caps PR descriptions at 4000`);
  const baseSha = git(["rev-parse", "--verify", `origin/${base}^{commit}`], { allowFail: true });
  if (!baseSha) throw new UsageError(`origin/${base} not found`);

  out("pr", pr);
  out("source", source);
  out("current_target", currentTarget);
  out("release_branch", branch);
  out("base", `${base}@${baseSha.slice(0, 7)}`);
  out("latest_tag", latest ?? "none");
  out("bump", bump);
  if (dry) {
    out("dry_run", true);
    return;
  }

  // ---- 1. release branch at the base tip
  note(`creating ${branch} at ${base} ${baseSha.slice(0, 7)}`);
  gitPush(["origin", `${baseSha}:refs/heads/${branch}`]);
  if (remoteBranchSha(branch) !== baseSha) throw new Error(`${branch} did not read back at ${baseSha.slice(0, 7)}`);
  out("release_branch_created", true);

  // ---- 2. version bump + changelog release on the PR branch, fast-forward only
  if (bump) {
    const pushed = withWorktree(`origin/${source}`, (dir) => {
      try {
        git(["merge", "--no-edit", "-q", `origin/${base}`], { cwd: dir });
      } catch {
        git(["merge", "--abort"], { cwd: dir, allowFail: true });
        throw new Error(`merging ${base} into ${source} conflicts; resolve it on the PR branch, then rerun with --bump`);
      }
      const changed = bumpVersionFiles(dir, version);
      const cl = join(dir, "CHANGELOG.md");
      if (existsSync(cl)) {
        writeFileSync(cl, releaseChangelog(readFileSync(cl, "utf8"), version, { date: today(), web: repoWeb(), base }));
        changed.push("CHANGELOG.md");
      }
      if (!changed.length) {
        note("no version file or CHANGELOG.md found; nothing to bump");
        return false;
      }
      git(["add", ...changed], { cwd: dir });
      git(["commit", "-q", "-m", `chore(release): ${version}`], { cwd: dir });
      gitPush(["origin", `HEAD:refs/heads/${source}`], dir);
      out("bump_files", changed.join(","));
      return true;
    });
    out("bump_pushed", pushed);
  }

  // ---- 3. retarget, then description in its own call
  note(`retargeting PR ${pr}: ${currentTarget} -> ${branch}`);
  azRest("patch", prUrl(ado, pr), { targetRefName: `refs/heads/${branch}` });
  // Azure DevOps applies a retarget and drops other fields sent in the same PATCH.
  if (descFile) azRest("patch", prUrl(ado, pr), { description });
  const back = azRest("get", prUrl(ado, pr));
  const target = String(back.targetRefName).replace(/^refs\/heads\//, "");
  if (target !== branch) throw new Error(`PR ${pr} still targets ${target}`);
  out("target", target);
  out("status", back.status);
  out("merge_status", back.mergeStatus ?? "pending");
  if (descFile) out("description_updated", String(back.description ?? "").trim() === description.trim());

  // ---- 4. is review enforced on the new branch?
  const repoId = prj.repository?.id;
  const pol = repoId
    ? azRest(
        "get",
        `${ado.orgUrl}/${encodeURIComponent(ado.project)}/_apis/policy/configurations?repositoryId=${repoId}&refName=${encodeURIComponent(`refs/heads/${branch}`)}&${API}`,
        undefined,
        { allowFail: true },
      )
    : null;
  // policy/configurations returns the repo's policies whatever refName you pass
  // (a Build policy scoped Exact to main comes back for a release branch too), so
  // the scope is matched here rather than trusted. A scope entry with no refName
  // is repo-wide. The authority for one PR is policy/evaluations on its artifactId.
  const ref = `refs/heads/${branch}`;
  const applies = (p: any) =>
    p.isEnabled &&
    (!p.settings?.scope?.length ||
      p.settings.scope.some((sc: any) =>
        !sc.refName ||
        (sc.matchKind === "Exact" && sc.refName === ref) ||
        (sc.matchKind === "Prefix" && ref.startsWith(sc.refName))));
  const matched = pol?.value ? pol.value.filter(applies) : null;
  out("enabled_policies_on_release_branch", matched ? matched.length : "unknown");
  if (matched?.length) out("blocking_policies", matched.filter((p: any) => p.isBlocking).map((p: any) => p.type?.displayName ?? "?").join(",") || "none");
  if (matched && matched.length === 0) note(`no branch policies cover ${branch}: nothing blocks completing this PR`);
});
