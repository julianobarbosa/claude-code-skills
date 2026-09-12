#!/usr/bin/env bun
// Tag a completed release and publish its source tarball as an Azure Artifacts
// Universal Package, then prove the published copy is the one that was built.
//
// End state, each part read back from its authority:
//   - annotated tag vX.Y.Z on the merge commit of a COMPLETED pull request
//     (or an explicit --commit), message = "<package> X.Y.Z" + CHANGELOG section
//   - <package>@X.Y.Z in the feed, holding the sdist built from that commit in a
//     clean worktree with SOURCE_DATE_EPOCH pinned, plus a generated README.md
//     (install, verify, use, what changed); the feed Description says the same
//     in brief and is read back after publish
//   - a fresh download matches the built file's sha256
//   - with --install-test: that download installs and reports version X.Y.Z
//
// Usage:
//   bun ReleasePublish.ts --version X.Y.Z (--pr <id> | --commit <sha>) --feed <feed>
//        [--package <name>] [--feed-project <project>] [--stage-dir <dir>]
//        [--install-test] [--no-publish] [--dry-run]
//
// --feed may come from SHIP_TAG_FEED. --stage-dir publishes a directory you built
// yourself instead of running `uv build --sdist`.
// Exit codes: 0 ok · 1 failure · 2 usage · 3 refused by a guard (nothing written)

import { existsSync, readdirSync, rmSync, writeFileSync } from "node:fs";
import { join } from "node:path";
import {
  API, Refusal, UsageError, adoParts, azRest, git, gitPush, localTagCommit, note, out,
  parseSemver, prUrl, remoteTagCommit, repoWeb, run, sh, sha256File, tempDir, today, withWorktree,
} from "./Lib.ts";
import { notesFor, parse } from "./Changelog.ts";
import { consoleScripts, renderDescription, renderReadme, requiresPython, type ReleaseInfo } from "./ReleaseDocs.ts";

const USAGE =
  "Usage: bun ReleasePublish.ts --version X.Y.Z (--pr <id> | --commit <sha>) --feed <feed> [--package <name>] [--feed-project <p>] [--stage-dir <dir>] [--install-test] [--no-publish] [--dry-run]";

// Universal Package names, per the az CLI quickstart: lowercase, start and end
// with a letter or digit, only letters, digits and non-consecutive - _ . in
// between. (The Pipelines task reference is stricter: letters, digits, dashes.)
const UPACK_NAME = /^[a-z0-9](?:[a-z0-9]|[-_.](?![-_.]))*[a-z0-9]$|^[a-z0-9]$/;

function tomlProject(text: string): { name?: string; version?: string } {
  const table = text.match(/^\[project\][ \t]*\r?\n([\s\S]*?)(?=^\[|(?![\s\S]))/m)?.[1] ?? "";
  return {
    name: table.match(/^name\s*=\s*"([^"]+)"/m)?.[1],
    version: table.match(/^version\s*=\s*"([^"]+)"/m)?.[1],
  };
}

function installTest(tarball: string, pkg: string, version: string): string {
  const dir = tempDir("ship-tag-venv-");
  try {
    sh("uv", ["venv", "-q", join(dir, "v")]);
    const py = join(dir, "v", "bin", "python");
    sh("uv", ["pip", "install", "-q", "--python", py, tarball]);
    const got = sh(py, ["-c", "import importlib.metadata as m, sys; print(m.version(sys.argv[1]))", pkg]);
    if (got !== version) throw new Error(`installed ${pkg} reports ${got}, expected ${version}`);
    return got;
  } finally {
    rmSync(dir, { recursive: true, force: true });
  }
}

await run(() => {
  let version = "";
  let pr = "";
  let commitArg = "";
  let feed = process.env.SHIP_TAG_FEED ?? "";
  let pkg = "";
  let feedProject = "";
  let stageDir = "";
  let doInstall = false;
  let noPublish = false;
  let dry = false;
  const argv = process.argv.slice(2);
  for (let i = 0; i < argv.length; i++) {
    switch (argv[i]) {
      case "--version": version = argv[++i] ?? ""; break;
      case "--pr": pr = argv[++i] ?? ""; break;
      case "--commit": commitArg = argv[++i] ?? ""; break;
      case "--feed": feed = argv[++i] ?? ""; break;
      case "--package": pkg = argv[++i] ?? ""; break;
      case "--feed-project": feedProject = argv[++i] ?? ""; break;
      case "--stage-dir": stageDir = argv[++i] ?? ""; break;
      case "--install-test": doInstall = true; break;
      case "--no-publish": noPublish = true; break;
      case "--dry-run": dry = true; break;
      case "-h": case "--help": console.log(USAGE); return;
      default: throw new UsageError(`unknown arg: ${argv[i]}\n${USAGE}`);
    }
  }
  const sv = parseSemver(version);
  if (!sv) throw new UsageError(`--version must be SemVer (X.Y.Z), got '${version}'\n${USAGE}`);
  version = sv.raw;
  // Universal Package versions must be lowercase and can't carry +build metadata.
  if (/[A-Z+]/.test(version)) throw new UsageError(`Universal Package versions must be lowercase with no +build metadata, got '${version}'`);
  if (!!pr === !!commitArg) throw new UsageError(`give exactly one of --pr or --commit\n${USAGE}`);
  if (!feed && !noPublish) throw new UsageError(`--feed (or SHIP_TAG_FEED) is required unless --no-publish\n${USAGE}`);
  if (stageDir && !existsSync(stageDir)) throw new UsageError(`--stage-dir not found: ${stageDir}`);
  const tag = `v${version}`;
  const ado = adoParts();
  if (!ado) throw new UsageError("origin is not an Azure DevOps remote");

  git(["fetch", "-q", "--prune", "--tags", "origin"]);

  // ---- guards: all of them run before anything is written
  let commit = "";
  if (pr) {
    const p = azRest("get", prUrl(ado, pr), undefined, { allowFail: true });
    if (!p) throw new Refusal(`PR ${pr} not found (or az is not logged in)`);
    // mergeStatus=succeeded only means "no conflicts"; completion is `status`.
    if (p.status !== "completed") throw new Refusal(`PR ${pr} is ${p.status} (mergeStatus=${p.mergeStatus}); tag only after it completes`);
    commit = p.lastMergeCommit?.commitId ?? "";
    const target = String(p.targetRefName).replace(/^refs\/heads\//, "");
    out("pr_target", target);
    if (!target.endsWith(tag)) note(`PR ${pr} merged into ${target}, not a ${tag} release branch`);
  } else {
    commit = git(["rev-parse", "--verify", `${commitArg}^{commit}`], { allowFail: true });
  }
  if (!commit) throw new Refusal("could not resolve the release commit");
  if (!git(["cat-file", "-t", commit], { allowFail: true })) throw new Refusal(`commit ${commit.slice(0, 7)} is not fetched locally`);

  const py = git(["show", `${commit}:pyproject.toml`], { allowFail: true });
  const proj = py ? tomlProject(py) : {};
  if (!pkg) pkg = proj.name ?? "";
  if (!pkg) throw new UsageError("--package is required when pyproject.toml has no [project] name");
  pkg = pkg.toLowerCase();
  if (!UPACK_NAME.test(pkg)) throw new UsageError(`'${pkg}' is not a valid Universal Package name (lowercase, digits, single - _ . separators)`);
  if (proj.version && proj.version !== version) {
    throw new Refusal(`pyproject.toml at ${commit.slice(0, 7)} says version ${proj.version}, not ${version}`);
  }

  const rt = remoteTagCommit(tag);
  const lt = localTagCommit(tag);
  if ((rt && rt !== commit) || (lt && lt !== commit)) {
    throw new Refusal(`tag ${tag} already exists at ${(rt || lt).slice(0, 7)}, not ${commit.slice(0, 7)}`);
  }

  const feedBase = feedProject
    ? `https://feeds.dev.azure.com/${encodeURIComponent(ado.org)}/${encodeURIComponent(feedProject)}`
    : `https://feeds.dev.azure.com/${encodeURIComponent(ado.org)}`;
  const listUrl = `${feedBase}/_apis/packaging/feeds/${encodeURIComponent(feed)}/packages?protocolType=UPack&packageNameQuery=${encodeURIComponent(pkg)}&includeAllVersions=true&${API}`;
  const versionsInFeed = (): string[] =>
    (azRest("get", listUrl)?.value ?? [])
      .filter((p: any) => p.name === pkg)
      .flatMap((p: any) => (p.versions ?? []).map((v: any) => v.version));
  if (!noPublish && versionsInFeed().includes(version)) {
    throw new Refusal(`${pkg}@${version} is already in feed ${feed}; versions are immutable, cut the next patch instead`);
  }

  out("version", version);
  out("commit", commit.slice(0, 7));
  out("package", pkg);
  out("feed", noPublish ? "none" : feed);
  out("tag_exists", rt === commit);
  if (dry) {
    out("dry_run", true);
    return;
  }

  // ---- 1. annotated tag on the release commit
  if (rt !== commit) {
    if (!lt) {
      const changelog = git(["show", `${commit}:CHANGELOG.md`], { allowFail: true });
      const notes = changelog ? notesFor(changelog, version) : "";
      // --cleanup=verbatim: the default mode strips lines starting with '#',
      // which would delete every `### Added` heading from the notes.
      const args = ["tag", "-a", tag, commit, "--cleanup=verbatim", "-m", `${pkg} ${version}`];
      if (notes) args.push("-m", notes);
      git(args);
    }
    gitPush(["origin", `refs/tags/${tag}`]);
  }
  if (remoteTagCommit(tag) !== commit) throw new Error(`origin's ${tag} does not resolve to ${commit.slice(0, 7)}`);
  out("tag", tag);

  // ---- 2. build (or take a prebuilt stage)
  let stage = stageDir;
  const ownStage = !stageDir;
  if (ownStage) stage = tempDir("ship-tag-stage-");
  try {
    if (ownStage) {
      const epoch = git(["log", "-1", "--format=%ct", commit]);
      withWorktree(commit, (dir) => {
        sh("uv", ["--directory", dir, "build", "--sdist", "--out-dir", stage], { env: { SOURCE_DATE_EPOCH: epoch } });
      });
      // uv writes a .gitignore into --out-dir; the package must hold only the tarball.
      rmSync(join(stage, ".gitignore"), { force: true });
    }
    const entries = readdirSync(stage);
    const tarballs = entries.filter((f) => f.endsWith(".tar.gz"));
    if (ownStage && (entries.length !== 1 || tarballs.length !== 1)) {
      throw new Error(`stage holds [${entries.join(", ")}]; expected exactly one .tar.gz`);
    }
    if (!tarballs.length) throw new Error(`no .tar.gz in ${stage}`);
    const artifact = join(stage, tarballs[0]);
    const top = tarballs[0].replace(/\.tar\.gz$/, "");
    const infoVersion = sh("tar", ["-xzOf", artifact, `${top}/PKG-INFO`], { allowFail: true }).match(/^Version:\s*(\S+)/m)?.[1];
    if (infoVersion && infoVersion !== version) throw new Error(`${tarballs[0]} PKG-INFO says ${infoVersion}, not ${version}`);
    const sum = sha256File(artifact);
    out("artifact", tarballs[0]);
    out("sha256", sum);
    out("pkg_info_version", infoVersion ?? "n/a");

    // What a consumer sees: README.md next to the tarball, and a feed Description
    // saying what changed and how to install. Both are immutable once published,
    // so both come from the tagged commit and its CHANGELOG section.
    const changelogAt = git(["show", `${commit}:CHANGELOG.md`], { allowFail: true });
    const info: ReleaseInfo = {
      pkg, version, tag, commit, date: today(), orgUrl: ado.orgUrl, feed, feedProject,
      tarball: tarballs[0], sha256: sum,
      notes: changelogAt ? notesFor(changelogAt, version) : "",
      compareUrl: changelogAt ? (parse(changelogAt).refs.find((r) => r.label.replace(/^v/, "") === version)?.url ?? "") : "",
      scripts: py ? consoleScripts(py) : [],
      requiresPython: py ? requiresPython(py) : "",
      repoBase: repoWeb().base,
    };
    if (ownStage) {
      writeFileSync(join(stage, "README.md"), renderReadme(info));
      out("readme", "README.md");
    }
    const description = renderDescription(info);
    out("description_chars", description.length);

    if (noPublish) {
      out("published", false);
      if (doInstall) out("install_version", installTest(artifact, pkg, version));
      return;
    }

    // ---- 3. publish, then read back from the feed (publish's own output lacks name/version)
    const scope = feedProject ? ["--scope", "project", "--project", feedProject] : [];
    sh("az", [
      "artifacts", "universal", "publish", "--organization", ado.orgUrl, "--feed", feed,
      "--name", pkg, "--version", version, "--path", stage,
      "--description", description, "-o", "none", ...scope,
    ]);
    if (!versionsInFeed().includes(version)) throw new Error(`${pkg}@${version} is not listed in feed ${feed} after publish`);
    out("published", true);
    // The feed's Description is what people read first; confirm it landed intact.
    const listed = (azRest("get", listUrl)?.value ?? []).find((p: any) => p.name === pkg);
    const versions = listed?.id
      ? azRest("get", `${feedBase}/_apis/packaging/feeds/${encodeURIComponent(feed)}/packages/${listed.id}/versions?${API}`, undefined, { allowFail: true })
      : null;
    const stored = String((versions?.value ?? []).find((v: any) => v.version === version)?.description ?? "");
    out("description_readback", stored.trim() === description.trim());
    if (stored.trim() !== description.trim()) note(`feed stored a ${stored.length}-char description, not the ${description.length} chars sent`);

    // ---- 4. download into an empty dir and compare bytes
    const dl = tempDir("ship-tag-dl-");
    try {
      sh("az", [
        "artifacts", "universal", "download", "--organization", ado.orgUrl, "--feed", feed,
        "--name", pkg, "--version", version, "--path", dl, "-o", "none", ...scope,
      ]);
      for (const f of readdirSync(stage)) {
        const got = join(dl, f);
        if (!existsSync(got)) throw new Error(`download did not contain ${f}`);
        if (sha256File(got) !== sha256File(join(stage, f))) throw new Error(`downloaded ${f} differs from the staged file`);
      }
      out("download_sha256_match", true);
      if (doInstall) out("install_version", installTest(join(dl, tarballs[0]), pkg, version));
    } finally {
      rmSync(dl, { recursive: true, force: true });
    }
  } finally {
    if (ownStage) rmSync(stage, { recursive: true, force: true });
  }
});
