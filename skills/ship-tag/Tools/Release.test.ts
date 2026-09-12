// Integration tests for ReleaseCut, ReleasePublish and ReleaseLocal.
// "origin" is a local bare repo reached through url.insteadOf, so the remote URL
// still reads as Azure DevOps; a stub `az` on PATH emulates the PR, policy and
// Universal Package calls, including the quirk that a PR PATCH carrying
// targetRefName drops every other field. The publish test builds and installs a
// real sdist, so it needs uv (and hatchling from uv's cache or the network).
//
//   bun test ~/.claude/skills/ship-tag/Tools/Release.test.ts
import { afterAll, beforeAll, describe, expect, test } from "bun:test";
import { createHash } from "node:crypto";
import { chmodSync, mkdirSync, mkdtempSync, readFileSync, readdirSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const TOOLS = import.meta.dir;
const ADO_URL = "https://dev.azure.com/acme/Platform/_git/widget";
let root = "";
let bin = "";
let state = "";
let work = "";

function git(cwd: string, ...args: string[]): string {
  const r = Bun.spawnSync(["git", ...args], { cwd, stdout: "pipe", stderr: "pipe" });
  if (r.exitCode !== 0) throw new Error(`git ${args.join(" ")}: ${r.stderr.toString()}`);
  return r.stdout.toString().trim();
}
function tool(name: string, args: string[], cwd = work) {
  const r = Bun.spawnSync(["bun", join(TOOLS, name), ...args], {
    cwd, stdout: "pipe", stderr: "pipe",
    env: { ...process.env, PATH: `${bin}:${process.env.PATH}`, AZ_STUB_STATE: state },
  });
  const stdout = r.stdout.toString();
  const kv: Record<string, string> = {};
  for (const l of stdout.split("\n")) {
    const i = l.indexOf("=");
    if (i > 0) kv[l.slice(0, i)] = l.slice(i + 1);
  }
  const res = { code: r.exitCode, stdout, stderr: r.stderr.toString(), kv };
  if (res.code !== 0 && process.env.SHIP_TAG_TEST_DEBUG) console.error(res.stderr);
  return res;
}
const st = () => JSON.parse(readFileSync(state, "utf8"));
const setSt = (fn: (s: any) => void) => {
  const s = st();
  fn(s);
  writeFileSync(state, JSON.stringify(s, null, 2));
};
function newRepo(dir: string) {
  mkdirSync(dir, { recursive: true });
  git(dir, "init", "-q", "-b", "main");
  for (const [k, v] of [["user.name", "Test Dev"], ["user.email", "dev@example.com"], ["commit.gpgsign", "false"], ["tag.gpgsign", "false"]]) git(dir, "config", k, v);
}

const HEADER = `# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
`;
const CL_EMPTY = `${HEADER}
## [Unreleased]

## [1.3.0] - 2026-06-02

### Added
- Scheduled reports.

[unreleased]: https://github.com/acme/widget/compare/v1.3.0...HEAD
[1.3.0]: https://github.com/acme/widget/releases/tag/v1.3.0
`;
const CL_PENDING = CL_EMPTY.replace("## [Unreleased]\n", "## [Unreleased]\n\n### Added\n- Scheduled exports.\n\n### Fixed\n- Exports of large reports no longer time out.\n");
const PYPROJECT = (v: string) => `[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "widget"
version = "${v}"
requires-python = ">=3.10"

[project.scripts]
widget = "widget:main"

[tool.hatch.build.targets.wheel]
packages = ["src/widget"]
`;

// Minimal `az`: just the calls the release tools make.
const AZ_STUB = `#!/usr/bin/env bun
import { cpSync, existsSync, mkdirSync, readFileSync, readdirSync, writeFileSync } from "node:fs";
import { join } from "node:path";
const S = process.env.AZ_STUB_STATE;
const st = JSON.parse(readFileSync(S, "utf8"));
const a = process.argv.slice(2);
const opt = (k) => { const i = a.indexOf(k); return i >= 0 ? a[i + 1] : undefined; };
const done = (obj) => { writeFileSync(S, JSON.stringify(st, null, 2)); if (obj !== undefined) console.log(JSON.stringify(obj)); process.exit(0); };
if (a[0] === "rest") {
  const m = opt("--method"), u = opt("--uri");
  const pr = u.match(/pullrequests\\/(\\d+)/)?.[1];
  if (pr && m === "get") { if (!st.prs[pr]) { console.error("TF401180: not found"); process.exit(1); } done(st.prs[pr]); }
  if (pr && m === "patch") {
    const body = JSON.parse(readFileSync(opt("--body").slice(1), "utf8"));
    (st.patches ??= []).push(Object.keys(body));
    // Azure DevOps applies a retarget and silently drops other fields sent with it.
    Object.assign(st.prs[pr], "targetRefName" in body ? { targetRefName: body.targetRefName } : body);
    done(st.prs[pr]);
  }
  if (/policy\\/configurations/.test(u)) done({ value: st.policies });
  const vm = u.match(/packaging\\/feeds\\/[^/]+\\/packages\\/([^/?]+)\\/versions/);
  if (vm) { const name = vm[1].replace(/^pkg-/, ""); done({ value: (st.feed[name] ?? []).map((version) => ({ version, description: st.desc?.[name]?.[version] ?? null })) }); }
  if (/packaging\\/feeds\\/[^/]+\\/packages/.test(u)) {
    const name = new URL(u).searchParams.get("packageNameQuery");
    const vs = st.feed[name] ?? [];
    done({ value: vs.length ? [{ id: "pkg-" + name, name, versions: vs.map((version) => ({ version })) }] : [] });
  }
}
if (a[0] === "artifacts" && a[1] === "universal") {
  const n = opt("--name"), v = opt("--version"), p = opt("--path"), dir = join(st.store, n, v);
  if (a[2] === "publish") {
    const d = opt("--description") ?? "";
    // Azure Artifacts rejects a description over 256 characters (artifacttool exit 20).
    if (d.length > 256) { console.error("The package description provided was " + d.length + " characters long, which is greater than the allowed maximum of 256 characters"); process.exit(1); }
    if ((st.feed[n] ?? []).includes(v)) { console.error("Conflict: version exists"); process.exit(1); }
    mkdirSync(dir, { recursive: true });
    for (const f of readdirSync(p)) cpSync(join(p, f), join(dir, f));
    st.feed[n] = [...(st.feed[n] ?? []), v];
    (st.desc ??= {})[n] = { ...(st.desc?.[n] ?? {}), [v]: opt("--description") ?? null };
    done({ name: null, version: null });
  }
  if (a[2] === "download") {
    if (!existsSync(dir)) { console.error("not found"); process.exit(1); }
    mkdirSync(p, { recursive: true });
    for (const f of readdirSync(dir)) cpSync(join(dir, f), join(p, f));
    done();
  }
}
if (a[0] === "account") { console.log("stub-token"); process.exit(0); }
console.error("az stub: unhandled " + a.join(" "));
process.exit(2);
`;

beforeAll(() => {
  root = mkdtempSync(join(tmpdir(), "ship-tag-it-"));
  bin = join(root, "bin");
  mkdirSync(bin);
  writeFileSync(join(bin, "az"), AZ_STUB);
  chmodSync(join(bin, "az"), 0o755);
  state = join(root, "az-state.json");
  writeFileSync(state, JSON.stringify({ prs: {}, feed: {}, store: join(root, "feed-store"), policies: [] }));
  const origin = join(root, "origin.git");
  git(root, "init", "-q", "--bare", "-b", "main", origin);

  work = join(root, "work");
  newRepo(work);
  git(work, "remote", "add", "origin", ADO_URL);
  git(work, "config", `url.${origin}.insteadOf`, ADO_URL);
  mkdirSync(join(work, "src", "widget"), { recursive: true });
  writeFileSync(join(work, "src", "widget", "__init__.py"), "def main():\n    print(\"widget\")\n");
  writeFileSync(join(work, "pyproject.toml"), PYPROJECT("1.3.0"));
  writeFileSync(join(work, "CHANGELOG.md"), CL_EMPTY);
  git(work, "add", ".");
  git(work, "commit", "-q", "-m", "chore(release): 1.3.0");
  git(work, "tag", "-a", "v1.3.0", "-m", "widget 1.3.0");
  git(work, "push", "-q", "origin", "main", "--tags");
  git(work, "checkout", "-q", "-b", "feat/export");
  writeFileSync(join(work, "src", "widget", "export.py"), "def export():\n    return 1\n");
  writeFileSync(join(work, "CHANGELOG.md"), CL_PENDING);
  git(work, "add", ".");
  git(work, "commit", "-q", "-m", "feat(export): scheduled exports");
  git(work, "push", "-q", "origin", "feat/export");
  git(work, "checkout", "-q", "main");
});
afterAll(() => rmSync(root, { recursive: true, force: true }));

describe("ReleaseCut against a stub Azure DevOps", () => {
  test("refuses a PR that isn't active", () => {
    setSt((s) => { s.prs["7"] = { status: "completed", sourceRefName: "refs/heads/feat/export", targetRefName: "refs/heads/main", repository: { id: "r1" } }; });
    const r = tool("ReleaseCut.ts", ["--version", "1.4.0", "--pr", "7", "--dry-run"]);
    expect(r.code).toBe(3);
    expect(r.stderr).toContain("active PR");
  });

  test("cuts release/v1.4.0, bumps the PR branch, retargets, sends the description separately", () => {
    setSt((s) => {
      s.prs["7"].status = "active";
      s.patches = [];
      // one repo-wide policy (applies) and one scoped Exact to main (does not)
      s.policies = [
        { isEnabled: true, isBlocking: true, type: { displayName: "File size restriction" }, settings: {} },
        { isEnabled: true, isBlocking: true, type: { displayName: "Build" }, settings: { scope: [{ matchKind: "Exact", refName: "refs/heads/main" }] } },
      ];
    });
    const desc = join(root, "desc.md");
    writeFileSync(desc, "## Summary\n\nRelease 1.4.0\n");
    const mainSha = git(work, "rev-parse", "main");
    const r = tool("ReleaseCut.ts", ["--version", "1.4.0", "--pr", "7", "--bump", "--description-file", desc]);
    expect(r.code).toBe(0);
    expect(r.kv.release_branch_created).toBe("true");
    expect(r.kv.bump_files).toBe("pyproject.toml,CHANGELOG.md");
    expect(r.kv.target).toBe("release/v1.4.0");
    expect(r.kv.description_updated).toBe("true");
    expect(r.kv.enabled_policies_on_release_branch).toBe("1");
    expect(r.kv.blocking_policies).toBe("File size restriction");
    expect(git(work, "ls-remote", "--heads", "origin", "release/v1.4.0").split(/\s+/)[0]).toBe(mainSha);
    git(work, "fetch", "-q", "origin");
    expect(git(work, "log", "-1", "--format=%s", "origin/feat/export")).toBe("chore(release): 1.4.0");
    expect(git(work, "show", "origin/feat/export:pyproject.toml")).toContain('version = "1.4.0"');
    const cl = git(work, "show", "origin/feat/export:CHANGELOG.md");
    expect(cl).toMatch(/## \[1\.4\.0\] - \d{4}-\d{2}-\d{2}/);
    expect(cl).toContain("[1.4.0]: https://dev.azure.com/acme/Platform/_git/widget/branchCompare?baseVersion=GTv1.3.0&targetVersion=GTv1.4.0");
    expect(st().patches).toEqual([["targetRefName"], ["description"]]);
  });

  test("refuses to cut the same release twice", () => {
    const r = tool("ReleaseCut.ts", ["--version", "1.4.0", "--pr", "7", "--dry-run"]);
    expect(r.code).toBe(3);
    expect(r.stderr).toContain("already exists");
  });
});

describe("ReleasePublish against a stub feed", () => {
  test("refuses while the PR is still active", () => {
    const r = tool("ReleasePublish.ts", ["--version", "1.4.0", "--pr", "7", "--feed", "f1", "--dry-run"]);
    expect(r.code).toBe(3);
    expect(r.stderr).toContain("tag only after it completes");
  });

  test("tags the merge commit, publishes, and proves the download matches", () => {
    git(work, "fetch", "-q", "origin");
    git(work, "checkout", "-q", "-B", "release/v1.4.0", "origin/release/v1.4.0");
    git(work, "merge", "-q", "--no-ff", "-m", "Merged PR 7: scheduled exports", "origin/feat/export");
    git(work, "push", "-q", "origin", "release/v1.4.0");
    const merge = git(work, "rev-parse", "HEAD");
    git(work, "checkout", "-q", "main");
    setSt((s) => { Object.assign(s.prs["7"], { status: "completed", mergeStatus: "succeeded", lastMergeCommit: { commitId: merge } }); });

    const r = tool("ReleasePublish.ts", ["--version", "1.4.0", "--pr", "7", "--feed", "f1", "--install-test"]);
    if (r.code !== 0) console.error(r.stderr);
    expect(r.code).toBe(0);
    expect(r.kv.tag).toBe("v1.4.0");
    expect(r.kv.pkg_info_version).toBe("1.4.0");
    expect(r.kv.published).toBe("true");
    expect(r.kv.download_sha256_match).toBe("true");
    expect(r.kv.install_version).toBe("1.4.0");
    expect(git(work, "ls-remote", "--tags", "origin", "refs/tags/v1.4.0^{}").split(/\s+/)[0]).toBe(merge);
    const msg = git(work, "for-each-ref", "refs/tags/v1.4.0", "--format=%(contents)");
    expect(msg).toContain("widget 1.4.0");
    expect(msg).toContain("### Added");
    expect(msg).toContain("### Fixed");
    const store = join(st().store, "widget", "1.4.0");
    expect(readdirSync(store).sort()).toEqual(["README.md", "widget-1.4.0.tar.gz"]);
    expect(r.kv.readme).toBe("README.md");
    expect(r.kv.description_readback).toBe("true");
    const desc: string = st().desc.widget["1.4.0"];
    expect(desc.length).toBeLessThanOrEqual(256);
    expect(desc.startsWith("widget 1.4.0 (")).toBe(true);
    expect(desc).toContain("Install: az artifacts universal download --feed f1 --name widget --version 1.4.0 --path . && uv pip install ./widget-1.4.0.tar.gz.");
    expect(desc).toContain("Details: README.md in this package.");
    const sha = createHash("sha256").update(readFileSync(join(store, "widget-1.4.0.tar.gz"))).digest("hex");
    const readme = readFileSync(join(store, "README.md"), "utf8");
    expect(readme).toContain(`echo "${sha}  widget-1.4.0.tar.gz" | sha256sum -c -`);
    expect(readme).toContain("widget --help");
    expect(readme).toContain("## What changed in 1.4.0");
    expect(readme).toContain("Full diff: https://dev.azure.com/acme/Platform/_git/widget/branchCompare?baseVersion=GTv1.3.0&targetVersion=GTv1.4.0");
  }, 240_000);

  test("refuses to publish the same version twice", () => {
    const r = tool("ReleasePublish.ts", ["--version", "1.4.0", "--pr", "7", "--feed", "f1", "--dry-run"]);
    expect(r.code).toBe(3);
    expect(r.stderr).toContain("immutable");
  });
});

describe("ReleaseLocal (no remote)", () => {
  let repo = "";
  beforeAll(() => {
    repo = join(root, "local");
    newRepo(repo);
    writeFileSync(join(repo, "pyproject.toml"), PYPROJECT("1.3.0"));
    writeFileSync(join(repo, "CHANGELOG.md"), CL_EMPTY);
    git(repo, "add", ".");
    git(repo, "commit", "-q", "-m", "chore(release): 1.3.0");
    git(repo, "tag", "-a", "v1.3.0", "-m", "widget 1.3.0");
    writeFileSync(join(repo, "CHANGELOG.md"), CL_PENDING);
    git(repo, "commit", "-q", "-am", "Merged PR 12: scheduled exports");
  });

  test("dry run plans without writing", () => {
    const before = git(repo, "rev-parse", "HEAD");
    const r = tool("ReleaseLocal.ts", ["--version", "1.4.0", "--dry-run"], repo);
    expect(r.code).toBe(0);
    expect(r.kv.dry_run).toBe("true");
    expect(git(repo, "rev-parse", "HEAD")).toBe(before);
    expect(git(repo, "tag", "--list", "v1.4.0")).toBe("");
  });

  test("one release commit, bumped version, inferred links, annotated tag with intact notes", () => {
    const r = tool("ReleaseLocal.ts", ["--version", "1.4.0", "--date", "2026-09-11"], repo);
    expect(r.code).toBe(0);
    expect(r.kv.files).toBe("pyproject.toml,CHANGELOG.md");
    expect(git(repo, "log", "-1", "--format=%s")).toBe("chore(release): 1.4.0");
    expect(readFileSync(join(repo, "pyproject.toml"), "utf8")).toContain('version = "1.4.0"');
    const cl = readFileSync(join(repo, "CHANGELOG.md"), "utf8");
    expect(cl).toContain("## [1.4.0] - 2026-09-11");
    expect(cl).toContain("[1.4.0]: https://github.com/acme/widget/compare/v1.3.0...v1.4.0");
    expect(cl).toContain("[unreleased]: https://github.com/acme/widget/compare/v1.4.0...HEAD");
    expect(git(repo, "cat-file", "-t", "v1.4.0")).toBe("tag");
    expect(git(repo, "rev-parse", "v1.4.0^{commit}")).toBe(git(repo, "rev-parse", "HEAD"));
    const msg = git(repo, "for-each-ref", "refs/tags/v1.4.0", "--format=%(contents)");
    expect(msg).toContain("widget 1.4.0");
    expect(msg).toContain("### Added");
    expect(msg).toContain("### Fixed");
    expect(git(repo, "status", "--porcelain")).toBe("");
  });

  test("refuses an existing tag and a dirty tree", () => {
    expect(tool("ReleaseLocal.ts", ["--version", "1.4.0"], repo).code).toBe(3);
    writeFileSync(join(repo, "scratch.txt"), "x");
    const r = tool("ReleaseLocal.ts", ["--version", "1.5.0"], repo);
    rmSync(join(repo, "scratch.txt"));
    expect(r.code).toBe(3);
    expect(r.stderr).toContain("not clean");
  });
});
