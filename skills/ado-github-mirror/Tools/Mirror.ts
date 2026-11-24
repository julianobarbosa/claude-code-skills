#!/usr/bin/env bun
/**
 * Mirror.ts — seed (or re-sync) a GitHub mirror of an Azure Repos repository.
 *
 * Creates the GitHub repo if it is missing, bare-clones the Azure DevOps source
 * (refs/heads/* + refs/tags/* only), force-pushes those refs to GitHub with --prune,
 * then proves every branch and tag SHA matches on both sides. Exit 0 only on a
 * verified mirror. Optional --write-pipeline drops the sync pipeline into a checkout.
 *
 * Every external command runs through an argv array (never a shell string), and no
 * token is ever placed on a command line, in a URL, or in output.
 */
import { existsSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { homedir, tmpdir } from "node:os";
import { basename, dirname, join } from "node:path";

type Config = {
  githubOrg?: string;
  visibility?: "private" | "internal";
  pipelineFile?: string;
  variableGroup?: string;
  tokenVariable?: string;
};

const CONFIG_PATH = process.env.ADO_GITHUB_MIRROR_CONFIG ?? join(homedir(), ".config/ado-github-mirror/config.json");
const TEMPLATE = join(dirname(import.meta.path), "MirrorPipeline.yaml");
const ADO_RESOURCE = "499b84ac-1321-427f-aa17-267ca6975798";
const GH_CRED = "!gh auth git-credential";

function usage(code = 0): never {
  console.log(readFileSync(join(dirname(import.meta.path), "Mirror.help.md"), "utf8"));
  process.exit(code);
}

function run(argv: string[], opts: { cwd?: string; allowFail?: boolean; env?: Record<string, string> } = {}) {
  const p = Bun.spawnSync(argv, { cwd: opts.cwd, env: { ...process.env, ...opts.env }, stdout: "pipe", stderr: "pipe" });
  const out = p.stdout.toString().trim();
  const err = p.stderr.toString().trim();
  if (p.exitCode !== 0 && !opts.allowFail) {
    console.error(`✗ ${argv.slice(0, 3).join(" ")} … failed (exit ${p.exitCode})\n${err}`);
    process.exit(1);
  }
  return { ok: p.exitCode === 0, out, err };
}

function parseArgs() {
  const a = Bun.argv.slice(2);
  const get = (f: string) => {
    const i = a.indexOf(f);
    return i >= 0 ? a[i + 1] : undefined;
  };
  if (a.includes("--help") || a.includes("-h")) usage();
  const cfg: Config = existsSync(CONFIG_PATH) ? JSON.parse(readFileSync(CONFIG_PATH, "utf8")) : {};
  return {
    source: get("--source"),
    org: get("--github-org") ?? cfg.githubOrg,
    name: get("--name"),
    visibility: (get("--visibility") ?? cfg.visibility ?? "private") as string,
    adoBearer: a.includes("--ado-bearer"),
    dryRun: a.includes("--dry-run"),
    writePipeline: get("--write-pipeline"),
    cfg,
  };
}

/** Resolve the ADO source URL: explicit flag, else origin of the current checkout. */
function resolveSource(explicit?: string): string {
  const url = explicit ?? run(["git", "remote", "get-url", "origin"], { allowFail: true }).out;
  if (!/dev\.azure\.com|visualstudio\.com/.test(url)) {
    console.error(`✗ source is not an Azure Repos URL: '${url || "(none)"}' — pass --source <url>`);
    process.exit(2);
  }
  return url.replace(/^https:\/\/[^@/]+@/, "https://"); // drop the org@ userinfo; auth comes from helpers
}

/** Env that authenticates the ADO fetch via a Bearer header — env, never argv. */
function adoAuthEnv(useBearer: boolean): Record<string, string> {
  if (!useBearer) return {};
  const tok = run(["az", "account", "get-access-token", "--resource", ADO_RESOURCE, "--query", "accessToken", "-o", "tsv"]).out;
  return { GIT_CONFIG_COUNT: "1", GIT_CONFIG_KEY_0: "http.extraHeader", GIT_CONFIG_VALUE_0: `Authorization: Bearer ${tok}` };
}

function refMap(lines: string): Map<string, string> {
  const m = new Map<string, string>();
  for (const l of lines.split("\n").filter(Boolean)) {
    const [sha, ref] = l.split(/\s+/);
    if (ref.startsWith("refs/heads/") || (ref.startsWith("refs/tags/") && !ref.endsWith("^{}"))) m.set(ref, sha);
  }
  return m;
}

function writePipeline(dest: string, repo: string, cfg: Config) {
  const file = join(dest, cfg.pipelineFile ?? ".azure-pipeline-mirror-github.yaml");
  const body = readFileSync(TEMPLATE, "utf8")
    .replaceAll("__GITHUB_REPO__", repo)
    .replaceAll("__VARIABLE_GROUP__", cfg.variableGroup ?? "github-mirror")
    .replaceAll("__TOKEN_VARIABLE__", cfg.tokenVariable ?? "GITHUB_MIRROR_TOKEN");
  writeFileSync(file, body);
  console.log(`✓ pipeline written: ${file}`);
}

const o = parseArgs();
if (!o.org) {
  console.error("✗ no GitHub org — pass --github-org or set githubOrg in Config.json");
  process.exit(2);
}
const src = resolveSource(o.source);
const name = o.name ?? basename(src).replace(/\.git$/, "");
const repo = `${o.org}/${name}`;
const dst = `https://github.com/${repo}.git`;
console.log(`source: ${src}\ntarget: ${dst} (${o.visibility})`);

// Preflight 1 — GitHub: active membership with an SSO-authorized token. (Listing org repos is NOT a
// valid probe: under SAML enforcement it succeeds and silently returns an empty list.)
const orgProbe = run(["gh", "api", `user/memberships/orgs/${o.org}`, "--jq", ".state"], { allowFail: true });
if (orgProbe.ok && orgProbe.out !== "active") orgProbe.ok = false, orgProbe.err = `membership state '${orgProbe.out}'`;
if (!orgProbe.ok) {
  const saml = /SAML/i.test(orgProbe.err);
  console.error(saml
    ? `✗ gh token is not SSO-authorized for '${o.org}'. Re-login through the enterprise IdP:\n    gh auth refresh -h github.com   (or: gh auth login -h github.com)\n  then authorize the token for the org, and re-run.`
    : `✗ cannot read org '${o.org}': ${orgProbe.err}`);
  process.exit(3);
}

// Preflight 2 — ADO: source readable.
const adoEnv = adoAuthEnv(o.adoBearer);
const srcRefs = run(["git", "ls-remote", src], { allowFail: true, env: adoEnv });
if (!srcRefs.ok) {
  console.error(`✗ cannot read the Azure Repos source (${srcRefs.err.split("\n").pop()}).\n  Fix git credentials, or retry with --ado-bearer (uses the az login's AAD token).`);
  process.exit(3);
}
const want = refMap(srcRefs.out);
console.log(`source refs (heads+tags): ${want.size}`);

const exists = run(["gh", "api", `repos/${repo}`], { allowFail: true }).ok;
if (o.dryRun) {
  console.log(`dry-run: would ${exists ? "re-sync existing" : "create"} ${repo} and push ${want.size} refs`);
  process.exit(0);
}

if (!exists) {
  run(["gh", "repo", "create", repo, `--${o.visibility}`, "--disable-issues", "--disable-wiki",
    "--description", `Read-only mirror of ${src} — Azure DevOps is the source of truth; do not push here.`]);
  console.log(`✓ created ${repo}`);
}

const work = mkdtempSync(join(tmpdir(), "ado-gh-mirror-"));
try {
  const bare = join(work, "src.git");
  run(["git", "clone", "--quiet", "--bare", src, bare], { env: adoEnv });
  run(["git", "-c", "credential.helper=", "-c", `credential.helper=${GH_CRED}`, "push", "--force", "--prune", dst,
    "+refs/heads/*:refs/heads/*", "+refs/tags/*:refs/tags/*"], { cwd: bare });

  // Verify: every source branch/tag SHA exists on GitHub, and nothing extra survives.
  const got = refMap(run(["git", "-c", "credential.helper=", "-c", `credential.helper=${GH_CRED}`, "ls-remote", dst]).out);
  const bad = [...want].filter(([r, s]) => got.get(r) !== s).map(([r]) => r);
  const extra = [...got.keys()].filter((r) => !want.has(r));
  if (bad.length || extra.length) {
    console.error(`✗ mirror mismatch — differing: ${bad.join(", ") || "none"}; extra on GitHub: ${extra.join(", ") || "none"}`);
    process.exit(4);
  }
  const head = run(["git", "symbolic-ref", "HEAD"], { cwd: bare }).out;
  console.log(`✓ verified ${want.size} refs; ${head} = ${want.get(head)?.slice(0, 12)} on both sides`);
  const defBranch = head.replace("refs/heads/", "");
  run(["gh", "api", "-X", "PATCH", `repos/${repo}`, "-f", `default_branch=${defBranch}`], { allowFail: true });
} finally {
  rmSync(work, { recursive: true, force: true });
}

if (o.writePipeline) writePipeline(o.writePipeline, repo, o.cfg);
console.log(`https://github.com/${repo}`);
