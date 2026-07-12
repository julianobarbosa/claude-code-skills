// Shared helpers for the `ship` skill (TypeScript, run via bun).
// Import these; do not execute this file directly.
//
// Git/branch/remote work stays as subprocess calls — it is inherently a git
// operation, not an API one. The Azure DevOps and GitHub REST surfaces use their
// official SDKs (azure-devops-node-api, @octokit/rest). All subprocess calls go
// through execFile with an argument array — never a shell string — so nothing is
// interpolated into a shell.

import { execFileSync } from "node:child_process";
import * as azdev from "azure-devops-node-api";

export type Platform = "azure" | "github" | "unknown";

export interface AdoParts {
  orgUrl: string;
  project: string;
  repo: string;
}

/** Run a command with an argument array (no shell). Returns trimmed stdout.
 *  With { allowFail: true }, a non-zero exit yields "" instead of throwing. */
export function sh(cmd: string, args: string[], opts: { allowFail?: boolean } = {}): string {
  try {
    return execFileSync(cmd, args, { encoding: "utf8" }).trim();
  } catch (err) {
    if (opts.allowFail) return "";
    throw err;
  }
}

/** Current checked-out branch name. */
export function currentBranch(): string {
  return sh("git", ["rev-parse", "--abbrev-ref", "HEAD"]);
}

/** Fetch URL of a remote (default: origin). Empty string if the remote is unset. */
export function remoteUrl(remote = "origin"): string {
  return sh("git", ["remote", "get-url", remote], { allowFail: true });
}

/** Classify a remote URL. Override with SHIP_PLATFORM=azure|github when detection
 *  is wrong (e.g. a custom SSH host alias that hides the real host). */
export function detectKind(url: string = remoteUrl()): Platform {
  const override = process.env.SHIP_PLATFORM;
  if (override === "azure" || override === "github") return override;
  if (/dev\.azure\.com|visualstudio\.com/.test(url)) return "azure";
  if (/github/.test(url)) return "github";
  return "unknown";
}

/** decodeURIComponent that falls back to the raw segment when it is not valid
 *  percent-encoding (a project/repo name with a literal % must not throw). */
function decodeSegment(s: string): string {
  try {
    return decodeURIComponent(s);
  } catch {
    return s;
  }
}

/** Parse an Azure DevOps remote URL into org URL / project / repo.
 *  Handles HTTPS (dev.azure.com), SSH (ssh.dev.azure.com:v3/...), and legacy
 *  *.visualstudio.com. Returns null if the URL is not an Azure DevOps URL.
 *  project/repo are decoded display names — re-encode them when building URLs. */
export function adoParts(url: string = remoteUrl()): AdoParts | null {
  let m = url.match(/dev\.azure\.com[^:/\s]*[:/]+(?:v3\/)?([^/]+)\/([^/]+)\/(?:_git\/)?([^/]+)$/);
  if (m) return { orgUrl: `https://dev.azure.com/${m[1]}`, project: decodeSegment(m[2]), repo: decodeSegment(m[3].replace(/\.git$/, "")) };
  m = url.match(/([^/@.]+)\.visualstudio\.com\/([^/]+)\/(?:_git\/)?([^/]+)$/);
  if (m) return { orgUrl: `https://dev.azure.com/${m[1]}`, project: decodeSegment(m[2]), repo: decodeSegment(m[3].replace(/\.git$/, "")) };
  return null;
}

/** Mint a short-lived Azure DevOps OAuth access token via the logged-in az CLI.
 *  499b84ac-1321-427f-aa17-267ca6975798 is the constant Azure DevOps API resource
 *  id (not a secret — the same for every org). Used as a git Bearer header and as
 *  the bearer for the azure-devops-node-api WebApi connection. */
export function adoToken(): string {
  return sh("az", [
    "account", "get-access-token",
    "--resource", "499b84ac-1321-427f-aa17-267ca6975798",
    "--query", "accessToken", "-o", "tsv",
  ]);
}

/** True if an SDK error is a 401/403 — the signal to fall back from a PAT to the
 *  az OAuth bearer (an under-scoped PAT fails write calls a full org member can make). */
export function isAuthError(e: any): boolean {
  const code = e?.statusCode ?? e?.status;
  if (code === 401 || code === 403) return true;
  return /\((?:401|403)\)/.test(String(e?.message ?? e));
}

/** Build an Azure DevOps WebApi connection. Prefers a configured PAT
 *  (AZURE_DEVOPS_EXT_PAT / AZURE_DEVOPS_PAT, the standard `az devops` credential);
 *  otherwise mints an az OAuth bearer. `usingPat` lets the caller retry with the
 *  bearer on a 401/403 — see isAuthError and the authFallback pattern in ship-pr.ts. */
export function adoConnection(
  orgUrl: string,
  opts: { forceBearer?: boolean } = {},
): { conn: azdev.WebApi; usingPat: boolean } {
  const pat = opts.forceBearer ? "" : (process.env.AZURE_DEVOPS_EXT_PAT || process.env.AZURE_DEVOPS_PAT);
  const handler = pat ? azdev.getPersonalAccessTokenHandler(pat) : azdev.getBearerHandler(adoToken());
  return { conn: new azdev.WebApi(orgUrl, handler), usingPat: !!pat };
}

/** Split a CSV/repeated-flag tag list into clean, de-duplicated names.
 *  Drops empty/whitespace entries so they never reach the label API. */
export function parseTags(values: string[]): string[] {
  const out: string[] = [];
  for (const v of values) {
    for (const part of v.split(",")) {
      const name = part.trim();
      if (name && !out.includes(name)) out.push(name);
    }
  }
  return out;
}

/** Best-effort extraction of a work-item id from a branch name or commit subject.
 *  Recognizes `AB#1234`, `AB1234`, and a number delimited by / _ - (e.g.
 *  feature/1234-foo). Returns the id or "". Heuristic — confirm it exists before
 *  trusting it (see adoWorkItemExists in ship-pr.ts). */
export function parseWorkItem(s: string = currentBranch()): string {
  let m = s.match(/[Aa][Bb]#?(\d{1,7})/);
  if (m) return m[1];
  m = s.match(/(?:^|[/_-])(\d{2,7})(?:[/_-]|$)/);
  if (m) return m[1];
  return "";
}
