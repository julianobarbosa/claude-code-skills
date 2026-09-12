// Shared helpers for the ship-tag tools (TypeScript, run via bun).
// Import these; do not execute this file directly.
//
// Every subprocess runs through execFileSync with an argument array, never a
// shell string, so a version, branch or file name is never re-interpreted by a
// shell. That also sidesteps the interactive-shell traps these tools replaced:
// zsh has no PIPESTATUS, and `rg -q` under `set -o pipefail` reports a found
// match as missing because the upstream command dies on SIGPIPE.

import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { basename, join } from "node:path";

/** The constant Azure DevOps API resource id: the same for every org, not a secret. */
export const ADO_RESOURCE = "499b84ac-1321-427f-aa17-267ca6975798";
export const API = "api-version=7.1";

/** A guard refused: nothing was written. Exit code 3. */
export class Refusal extends Error {}
/** Bad invocation. Exit code 2. */
export class UsageError extends Error {}

export function fail(msg: string, code = 1): never {
  console.error(`ERROR: ${msg}`);
  process.exit(code);
}

export function note(msg: string): void {
  console.error(`>> ${msg}`);
}

/** Machine-readable result line on stdout. */
export function out(key: string, value: string | number | boolean): void {
  console.log(`${key}=${value}`);
}

/** Run main(); map Refusal to exit 3, UsageError to 2, anything else to 1.
 *  Tools throw instead of calling fail() inside cleanup scopes, because
 *  process.exit() skips `finally` blocks and would leak worktrees. */
export async function run(main: () => void | Promise<void>): Promise<void> {
  try {
    await main();
  } catch (e: any) {
    const code = e instanceof Refusal ? 3 : e instanceof UsageError ? 2 : 1;
    fail(e?.message ?? String(e), code);
  }
}

export interface ShOpts {
  allowFail?: boolean;
  cwd?: string;
  env?: Record<string, string>;
  input?: string;
}

/** Run a command with an argument array (no shell). Returns trimmed stdout.
 *  stdin is closed unless `input` is given. Errors name only the command and its
 *  first argument, never the full argv, because a push can carry an auth header. */
export function sh(cmd: string, args: string[], o: ShOpts = {}): string {
  try {
    return execFileSync(cmd, args, {
      encoding: "utf8",
      cwd: o.cwd,
      env: o.env ? { ...process.env, ...o.env } : process.env,
      input: o.input ?? "",
      stdio: ["pipe", "pipe", "pipe"],
      maxBuffer: 64 * 1024 * 1024,
    }).trim();
  } catch (e: any) {
    if (o.allowFail) return "";
    const stderr = String(e?.stderr ?? "").trim().split("\n").slice(-6).join("\n");
    throw new Error(`${cmd} ${args[0] ?? ""} failed${stderr ? `:\n${stderr}` : ""}`);
  }
}

export function git(args: string[], o: ShOpts = {}): string {
  return sh("git", args, o);
}

// ---------------------------------------------------------------- SemVer 2.0.0

const SEMVER_RE =
  /^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?(?:\+([0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*))?$/;

export interface SemVer {
  major: number;
  minor: number;
  patch: number;
  pre: string[];
  raw: string;
}

/** Parse X.Y.Z[-pre][+build]; a leading "v" is accepted and dropped from `raw`. */
export function parseSemver(v: string): SemVer | null {
  const raw = v.replace(/^v/, "");
  const m = raw.match(SEMVER_RE);
  if (!m) return null;
  return { major: +m[1], minor: +m[2], patch: +m[3], pre: m[4] ? m[4].split(".") : [], raw };
}

/** SemVer precedence: negative if a < b, 0 if equal, positive if a > b. Build metadata is ignored. */
export function compareSemver(a: string, b: string): number {
  const x = parseSemver(a);
  const y = parseSemver(b);
  if (!x || !y) throw new Error(`not SemVer: ${!x ? a : b}`);
  for (const k of ["major", "minor", "patch"] as const) if (x[k] !== y[k]) return x[k] - y[k];
  // A release outranks any of its pre-releases.
  if (!x.pre.length || !y.pre.length) return y.pre.length - x.pre.length;
  for (let i = 0; i < Math.max(x.pre.length, y.pre.length); i++) {
    const p = x.pre[i];
    const q = y.pre[i];
    if (p === undefined) return -1;
    if (q === undefined) return 1;
    const pn = /^\d+$/.test(p);
    const qn = /^\d+$/.test(q);
    if (pn && qn) {
      if (+p !== +q) return +p - +q;
    } else if (pn !== qn) {
      return pn ? -1 : 1;
    } else if (p !== q) {
      return p < q ? -1 : 1;
    }
  }
  return 0;
}

// ------------------------------------------------------------ remotes and URLs

/** Every URL a remote is known by: `git remote get-url` (insteadOf rewrites
 *  applied) first, then the raw configured value. An alias like "ado:org/proj"
 *  only parses after expansion; a test origin rewritten to a local path only
 *  parses before it. */
export function remoteUrls(remote = "origin"): string[] {
  const expanded = git(["remote", "get-url", remote], { allowFail: true });
  const raw = git(["config", "--get", `remote.${remote}.url`], { allowFail: true });
  return [...new Set([expanded, raw].filter(Boolean))];
}

export function remoteUrl(remote = "origin"): string {
  return remoteUrls(remote)[0] ?? "";
}

export interface AdoParts {
  org: string;
  orgUrl: string;
  project: string;
  repo: string;
}

function decodeSegment(s: string): string {
  try {
    return decodeURIComponent(s);
  } catch {
    return s;
  }
}

/** Parse an Azure DevOps remote (HTTPS, SSH v3, or legacy *.visualstudio.com).
 *  project/repo are decoded display names; re-encode them when building URLs. */
export function adoParts(url?: string): AdoParts | null {
  if (url === undefined) {
    for (const u of remoteUrls()) {
      const p = adoParts(u);
      if (p) return p;
    }
    return null;
  }
  let m = url.match(/dev\.azure\.com[^:/\s]*[:/]+(?:v3\/)?([^/]+)\/([^/]+)\/(?:_git\/)?([^/]+)$/);
  if (!m) m = url.match(/([^/@.]+)\.visualstudio\.com\/([^/]+)\/(?:_git\/)?([^/]+)$/);
  if (!m) return null;
  const org = decodeSegment(m[1]);
  return {
    org,
    orgUrl: `https://dev.azure.com/${encodeURIComponent(org)}`,
    project: decodeSegment(m[2]),
    repo: decodeSegment(m[3].replace(/\.git$/, "")),
  };
}

export type RepoKind = "azure" | "github" | "unknown";
export interface RepoWeb {
  kind: RepoKind;
  base: string;
}

/** Browser base URL of the repository, used for changelog compare links. */
export function repoWeb(url?: string): RepoWeb {
  if (url === undefined) {
    for (const u of remoteUrls()) {
      const w = repoWeb(u);
      if (w.kind !== "unknown") return w;
    }
    return { kind: "unknown", base: "" };
  }
  const a = adoParts(url);
  if (a) {
    return {
      kind: "azure",
      base: `${a.orgUrl}/${encodeURIComponent(a.project)}/_git/${encodeURIComponent(a.repo)}`,
    };
  }
  const g = url.match(/github\.com[:/]([^/]+)\/([^/]+?)(?:\.git)?\/?$/);
  if (g) return { kind: "github", base: `https://github.com/${g[1]}/${g[2]}` };
  return { kind: "unknown", base: "" };
}

export function prUrl(a: AdoParts, id: string | number): string {
  return `${a.orgUrl}/${encodeURIComponent(a.project)}/_apis/git/repositories/${encodeURIComponent(a.repo)}/pullrequests/${id}?${API}`;
}

// ----------------------------------------------------------------- git state

/** Commit sha of a branch on origin, or "". */
export function remoteBranchSha(branch: string): string {
  const line = git(["ls-remote", "--heads", "origin", `refs/heads/${branch}`], { allowFail: true });
  return line.split(/\s+/)[0] ?? "";
}

/** Commit a tag on origin points at (peeled for annotated tags), or "". */
export function remoteTagCommit(tag: string): string {
  const txt = git(["ls-remote", "--tags", "origin", `refs/tags/${tag}`, `refs/tags/${tag}^{}`], { allowFail: true });
  if (!txt) return "";
  const rows = txt.split("\n").map((l) => l.split(/\s+/));
  const peeled = rows.find((r) => r[1]?.endsWith("^{}"));
  return (peeled ?? rows[0])[0] ?? "";
}

/** Commit a local tag points at, or "". */
export function localTagCommit(tag: string): string {
  return git(["rev-parse", "-q", "--verify", `refs/tags/${tag}^{commit}`], { allowFail: true });
}

export function adoToken(): string {
  return sh("az", ["account", "get-access-token", "--resource", ADO_RESOURCE, "--query", "accessToken", "-o", "tsv"]);
}

/** git push; against Azure DevOps, a failed push is retried once with an az
 *  OAuth bearer header (the path when no git credential helper is set up). */
export function gitPush(args: string[], cwd?: string): string {
  try {
    return git(["push", ...args], { cwd });
  } catch (first) {
    if (repoWeb().kind !== "azure") throw first;
    note("normal push failed; retrying with an az OAuth bearer header");
    const token = adoToken();
    return git(["-c", `http.extraHeader=Authorization: Bearer ${token}`, "push", ...args], { cwd });
  }
}

// --------------------------------------------------------------- Azure REST

/** `az rest` against Azure DevOps. The body goes through a temp file so it never
 *  hits the argument list. Returns parsed JSON, or null for an empty body (or a
 *  failure when allowFail is set). */
export function azRest(method: "get" | "patch" | "post", uri: string, body?: unknown, o: { allowFail?: boolean } = {}): any {
  const args = ["rest", "--method", method, "--resource", ADO_RESOURCE, "--uri", uri, "-o", "json"];
  let dir = "";
  if (body !== undefined) {
    dir = tempDir("ship-tag-body-");
    const f = join(dir, "body.json");
    writeFileSync(f, JSON.stringify(body));
    args.push("--headers", "Content-Type=application/json", "--body", `@${f}`);
  }
  try {
    const txt = sh("az", args, { allowFail: o.allowFail });
    return txt ? JSON.parse(txt) : null;
  } finally {
    if (dir) rmSync(dir, { recursive: true, force: true });
  }
}

// ------------------------------------------------------------- scratch space

export function tempDir(prefix: string): string {
  return mkdtempSync(join(process.env.SHIP_TAG_TMP || tmpdir(), prefix));
}

/** Run fn inside a detached worktree at `ref`, always removing it afterwards.
 *  Release surgery happens here so a dirty main checkout is never touched. */
export function withWorktree<T>(ref: string, fn: (dir: string) => T): T {
  const parent = tempDir("ship-tag-wt-");
  const dir = join(parent, "wt");
  git(["worktree", "add", "-q", "--detach", dir, ref]);
  try {
    return fn(dir);
  } finally {
    git(["worktree", "remove", "--force", dir], { allowFail: true });
    rmSync(parent, { recursive: true, force: true });
    git(["worktree", "prune"], { allowFail: true });
  }
}

export function sha256File(path: string): string {
  return createHash("sha256").update(readFileSync(path)).digest("hex");
}

/** Local calendar date as YYYY-MM-DD (what a human reading the changelog expects). */
export function today(): string {
  const d = new Date();
  const p = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

// ------------------------------------------------------------ version files

/** Set the project version in pyproject.toml ([project] table only) and/or
 *  package.json. Refreshes uv.lock when pyproject changed. Returns changed paths. */
export function bumpVersionFiles(dir: string, version: string): string[] {
  const changed: string[] = [];
  const py = join(dir, "pyproject.toml");
  if (existsSync(py)) {
    const text = readFileSync(py, "utf8");
    const table = text.match(/^\[project\][ \t]*\r?\n([\s\S]*?)(?=^\[|(?![\s\S]))/m);
    if (table) {
      const body = table[1];
      const next = body.replace(/^(version\s*=\s*)"[^"]*"/m, `$1"${version}"`);
      if (next !== body) {
        writeFileSync(py, text.replace(body, next));
        changed.push("pyproject.toml");
        if (existsSync(join(dir, "uv.lock"))) {
          sh("uv", ["--directory", dir, "lock"]);
          changed.push("uv.lock");
        }
      }
    }
  }
  const pj = join(dir, "package.json");
  if (existsSync(pj)) {
    const obj = JSON.parse(readFileSync(pj, "utf8"));
    if (typeof obj.version === "string" && obj.version !== version) {
      obj.version = version;
      writeFileSync(pj, JSON.stringify(obj, null, 2) + "\n");
      changed.push("package.json");
    }
  }
  return changed;
}

/** Project name for tag subjects: pyproject [project] name, package.json name, or the directory. */
export function projectName(dir: string): string {
  const py = join(dir, "pyproject.toml");
  if (existsSync(py)) {
    const table = readFileSync(py, "utf8").match(/^\[project\][ \t]*\r?\n([\s\S]*?)(?=^\[|(?![\s\S]))/m)?.[1] ?? "";
    const n = table.match(/^name\s*=\s*"([^"]+)"/m)?.[1];
    if (n) return n;
  }
  const pj = join(dir, "package.json");
  if (existsSync(pj)) {
    const n = JSON.parse(readFileSync(pj, "utf8")).name;
    if (typeof n === "string" && n) return n;
  }
  return basename(dir);
}
