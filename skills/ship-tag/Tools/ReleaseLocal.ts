#!/usr/bin/env bun
// Cut a release on the current branch without a PR platform.
//
// End state, read back:
//   - one `chore(release): X.Y.Z` commit that sets the version file(s) and moves
//     CHANGELOG [Unreleased] into [X.Y.Z] (compare links from --repo-url, origin,
//     or the links the file already has)
//   - an annotated tag vX.Y.Z on that commit; message "<name> X.Y.Z" plus the
//     release notes, written with --cleanup=verbatim so `###` headings survive
//   - with --push: branch and tag pushed and the tag read back from origin
//
// Use it when there is no remote or PR flow, or when the release commit itself is
// the reviewed step. When the base branch is protected, use ReleaseCut.ts instead;
// a push rejected by branch policy is that signal.
//
// Usage:
//   bun ReleaseLocal.ts --version X.Y.Z [--date YYYY-MM-DD] [--base main]
//                       [--repo-url <url>] [--push] [--dry-run]
//
// Exit codes: 0 ok · 1 failure · 2 usage · 3 refused by a guard (nothing written)

import { existsSync, readFileSync, writeFileSync } from "node:fs";
import {
  Refusal, UsageError, bumpVersionFiles, compareSemver, git, gitPush, localTagCommit, out,
  parseSemver, projectName, remoteTagCommit, remoteUrl, repoWeb, run, today,
} from "./Lib.ts";
import { isIsoDate, notesFor, releaseChangelog } from "./Changelog.ts";

const USAGE = "Usage: bun ReleaseLocal.ts --version X.Y.Z [--date YYYY-MM-DD] [--base main] [--repo-url <url>] [--push] [--dry-run]";

await run(() => {
  let version = "";
  let date = "";
  let base = "main";
  let repoUrl = "";
  let push = false;
  let dry = false;
  const argv = process.argv.slice(2);
  for (let i = 0; i < argv.length; i++) {
    switch (argv[i]) {
      case "--version": version = argv[++i] ?? ""; break;
      case "--date": date = argv[++i] ?? ""; break;
      case "--base": base = argv[++i] ?? ""; break;
      case "--repo-url": repoUrl = argv[++i] ?? ""; break;
      case "--push": push = true; break;
      case "--dry-run": dry = true; break;
      case "-h": case "--help": console.log(USAGE); return;
      default: throw new UsageError(`unknown arg: ${argv[i]}\n${USAGE}`);
    }
  }
  const sv = parseSemver(version);
  if (!sv) throw new UsageError(`--version must be SemVer (X.Y.Z), got '${version}'\n${USAGE}`);
  version = sv.raw;
  if (date && !isIsoDate(date)) throw new UsageError(`--date must be YYYY-MM-DD, got '${date}'`);
  const top = git(["rev-parse", "--show-toplevel"], { allowFail: true });
  if (!top) throw new UsageError("not inside a git repository");
  process.chdir(top);

  // ---- guards: all of them run before anything is written
  const branch = git(["rev-parse", "--abbrev-ref", "HEAD"]);
  if (branch === "HEAD") throw new Refusal("detached HEAD; check out the branch you are releasing");
  const dirty = git(["status", "--porcelain"]);
  if (dirty) throw new Refusal(`working tree is not clean; commit or stash first:\n${dirty}`);
  const tag = `v${version}`;
  const hasOrigin = !!remoteUrl();
  if (push && !hasOrigin) throw new UsageError("--push needs an origin remote");
  if (localTagCommit(tag) || (hasOrigin && remoteTagCommit(tag))) throw new Refusal(`tag ${tag} already exists; pick the next version`);
  const latest = git(["tag", "--list", "v*"]).split("\n").filter((t) => t && parseSemver(t)).sort(compareSemver).at(-1);
  if (latest && compareSemver(version, latest) <= 0) throw new Refusal(`${tag} is not greater than the latest tag ${latest}`);
  const changelog = existsSync("CHANGELOG.md") ? readFileSync("CHANGELOG.md", "utf8") : "";
  if (changelog && !notesFor(changelog, "unreleased")) throw new Refusal("CHANGELOG.md [Unreleased] has no entries; add them before releasing");
  const name = projectName(top);

  out("version", version);
  out("branch", branch);
  out("latest_tag", latest ?? "none");
  out("changelog", changelog ? "yes" : "none");
  out("push", push);
  if (dry) {
    out("dry_run", true);
    return;
  }

  // ---- 1. version files + changelog, one commit
  const changed = bumpVersionFiles(top, version);
  if (changelog) {
    const web = repoUrl ? repoWeb(repoUrl) : repoWeb();
    writeFileSync("CHANGELOG.md", releaseChangelog(changelog, version, { date: date || today(), web, base }));
    changed.push("CHANGELOG.md");
  }
  if (!changed.length) throw new Refusal("no version file or CHANGELOG.md to update; nothing to release");
  git(["add", ...changed]);
  git(["commit", "-q", "-m", `chore(release): ${version}`]);
  const commit = git(["rev-parse", "HEAD"]);

  // ---- 2. annotated tag; --cleanup=verbatim keeps the `###` headings in the notes
  const notes = changelog ? notesFor(readFileSync("CHANGELOG.md", "utf8"), version) : "";
  const args = ["tag", "-a", tag, "--cleanup=verbatim", "-m", `${name} ${version}`];
  if (notes) args.push("-m", notes);
  git(args);
  if (localTagCommit(tag) !== commit) throw new Error(`${tag} does not point at ${commit.slice(0, 7)}`);
  out("commit", commit.slice(0, 7));
  out("tag", tag);
  out("files", changed.join(","));

  // ---- 3. optional push, read back
  if (push) {
    gitPush(["origin", `HEAD:refs/heads/${branch}`]);
    gitPush(["origin", `refs/tags/${tag}`]);
    if (remoteTagCommit(tag) !== commit) throw new Error(`origin's ${tag} does not resolve to ${commit.slice(0, 7)}`);
  }
  out("pushed", push);
});
