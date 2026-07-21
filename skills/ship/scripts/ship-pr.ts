#!/usr/bin/env bun
// Open a pull request on the detected platform (Azure Repos via azure-devops-node-api,
// GitHub via @octokit/rest), link work item(s), and optionally transition Board state.
//
// Usage:
//   bun ship-pr.ts --title T [--body B | --body-file F] [--target main] [--source BR]
//                  [--work-item ID] [--task "title" ...] [--tasks-file F]
//                  [--assignee UPN] [--work-item-type TYPE] [--no-create-work-item]
//                  [--transition STATE] [--tag "t1,t2" ...] [--reviewer UPN ...]
//                  [--required-reviewer UPN ...] [--draft] [-r remote]
//
// Prerequisites in one shot: on Azure, the work item, tags/labels, and reviewers
// are packed into the single createPullRequest call — no create-then-patch round
// trips. On GitHub, labels and reviewers are attached in follow-up calls because
// the create API doesn't accept them.
//
// Work-item association (Azure Repos + Boards):
//   On Azure, the PR is always linked to at least one Board work item. The id is
//   taken from --work-item (or inferred from the branch) and VERIFIED to exist. If
//   no real work item is found, one is CREATED per task (each assigned to the
//   configured user) and linked to the PR — so a PR is never opened without
//   traceability.
//
// --work-item   Existing Board id to link. Verified via the SDK; if it doesn't
//               resolve, the create path runs instead.
// --task        Title for a work item to create (repeatable — one item per task).
//               With none given and no work item found, one item is created from
//               the PR --title.
// --tasks-file  File with one task title per line (combined with --task flags).
// --assignee    UPN/email the created work items are assigned to. Default:
//               $SHIP_ADO_ASSIGNEE, else you@example.com.
// --work-item-type  Type for created items (default: Task; e.g. "User Story", Bug).
// --no-create-work-item  Disable auto-creation; link only a pre-existing --work-item.
// --transition  Azure only: sets each linked/created item's state AFTER the PR is
//               created (e.g. Resolved). Skipped on GitHub.
// --tag         PR tag(s)/label(s). Comma-separated and/or repeatable. e.g.
//               --tag hotfix,WIP. On Azure these ride along in the create call.
//               Or manage tags later with ship-tag.ts.
// --reviewer    Reviewer(s) to add when the PR opens — OPTIONAL (non-blocking).
//               UPN/email on Azure (resolved to an identity via the identities
//               API; unresolved names are warned + skipped, never fatal), or a
//               username on GitHub. Comma-separated and/or repeatable.
// --required-reviewer  Same, but marked REQUIRED on Azure (blocks completion).
//               GitHub has no per-PR "required" reviewer (that's branch policy),
//               so these are just requested like any other reviewer there.

import { readFileSync } from "node:fs";
import * as azdev from "azure-devops-node-api";
import { Octokit } from "@octokit/rest";
import {
  sh, currentBranch, remoteUrl, detectKind, adoParts, adoToken, parseWorkItem, parseTags,
} from "./ship-lib.ts";

function fail(msg: string, code = 1): never {
  console.error(msg);
  process.exit(code);
}

// HTTP Authorization header matching the SDK's auth: a PAT uses Basic (empty user
// + PAT); otherwise an az OAuth bearer. Used for the raw identities lookup below,
// which the SDK doesn't expose a typed client for in this version.
function azAuthHeader(pat: string | undefined): string {
  if (pat) return `Basic ${Buffer.from(":" + pat).toString("base64")}`;
  return `Bearer ${adoToken()}`;
}

// Resolve a reviewer UPN/email to an Azure DevOps identity GUID (what the PR
// reviewers payload needs). A value that already looks like a GUID passes through.
// Best-effort: any failure returns null so the caller can skip + warn, never abort
// the PR. Uses the vssps identities endpoint (Accounts/Identity area).
async function resolveAzureIdentity(orgUrl: string, header: string, upn: string): Promise<string | null> {
  if (/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(upn)) return upn;
  const org = orgUrl.replace(/^https:\/\/dev\.azure\.com\//, "").replace(/\/$/, "");
  const api = `https://vssps.dev.azure.com/${org}/_apis/identities?searchFilter=General&filterValue=${encodeURIComponent(upn)}&api-version=7.1`;
  try {
    const res = await fetch(api, { headers: { Authorization: header, Accept: "application/json" } });
    if (!res.ok) return null;
    const data: any = await res.json();
    return data?.value?.[0]?.id ?? null;
  } catch {
    return null;
  }
}

// ---- args ----
let title = "", body = "", bodyFile = "", target = "main", sourceBranch = "";
let workItem = "", transition = "", remote = "origin", wiType = "Task";
let assignee = process.env.SHIP_ADO_ASSIGNEE || "you@example.com";
let draft = false, createWi = true;
const tasks: string[] = [];
const tagFlags: string[] = [];
const reviewerFlags: string[] = [];
const requiredReviewerFlags: string[] = [];

const argv = process.argv.slice(2);
for (let i = 0; i < argv.length; i++) {
  const a = argv[i];
  switch (a) {
    case "--title": title = argv[++i]; break;
    case "--body": body = argv[++i]; break;
    case "--body-file": bodyFile = argv[++i]; break;
    case "--target": target = argv[++i]; break;
    case "--source": sourceBranch = argv[++i]; break;
    case "--work-item": workItem = argv[++i]; break;
    case "--task": tasks.push(argv[++i]); break;
    case "--tasks-file":
      for (const line of readFileSync(argv[++i], "utf8").split("\n")) {
        const t = line.trim();
        if (t) tasks.push(t);
      }
      break;
    case "--assignee": assignee = argv[++i]; break;
    case "--work-item-type": wiType = argv[++i]; break;
    case "--no-create-work-item": createWi = false; break;
    case "--transition": transition = argv[++i]; break;
    case "--tag": { const v = argv[++i]; if (v === undefined) fail("--tag requires a value", 2); tagFlags.push(v); break; }
    case "--reviewer": { const v = argv[++i]; if (v === undefined) fail("--reviewer requires a value", 2); reviewerFlags.push(v); break; }
    case "--required-reviewer": { const v = argv[++i]; if (v === undefined) fail("--required-reviewer requires a value", 2); requiredReviewerFlags.push(v); break; }
    case "--draft": draft = true; break;
    case "-r": case "--remote": remote = argv[++i]; break;
    case "-h": case "--help":
      console.log(readFileSync(new URL(import.meta.url), "utf8")
        .split("\n").filter((l) => l.startsWith("//")).map((l) => l.slice(3)).join("\n"));
      process.exit(0);
    default: fail(`unknown arg: ${a}`, 2);
  }
}
if (!title) fail("--title is required", 2);
if (!sourceBranch) sourceBranch = currentBranch();
// Branch-name inference is a last-resort heuristic for the no-flags case ONLY.
// When the caller passed --task/--tasks-file they explicitly asked for item
// creation — a number scraped from the branch must not preempt it (real incidents:
// chore/19-4-* linked unrelated Epic #19; bmad/story-24-2-* linked Epic #24
// despite --task, 2026-07-13). Existence-verification downstream can't catch
// these because the mis-parsed id IS a real (wrong) item.
if (!workItem && tasks.length === 0) workItem = parseWorkItem(sourceBranch);

const url = remoteUrl(remote);
const kind = detectKind(url);
if (bodyFile) body = readFileSync(bodyFile, "utf8");
const tags = parseTags(tagFlags);
const optionalReviewers = parseTags(reviewerFlags);        // reuse CSV split + dedupe
const requiredReviewers = parseTags(requiredReviewerFlags);

// A PR with no label is invisible to triage and to release-note grouping, and no
// platform can gate it — neither ADO nor GitHub has a "require a label" policy.
// So when the caller passed no --tag, derive a type label from the branch prefix
// (feat/…, fix/…) rather than opening the PR bare. Warn, never fail: `ship` is
// shared across repos and a hard failure would break unrelated flows.
const TYPE_FROM_BRANCH: Record<string, string> = {
  feat: "feat", feature: "feat", fix: "fix", hotfix: "fix", bugfix: "fix",
  docs: "docs", doc: "docs", chore: "chore", refactor: "refactor",
};
if (tags.length === 0) {
  const prefix = sourceBranch.split("/")[0]?.toLowerCase() ?? "";
  const derived = TYPE_FROM_BRANCH[prefix];
  if (derived) {
    tags.push(derived);
    console.error(`>> NOTE: no --tag given; derived '${derived}' from branch prefix '${prefix}/'`);
  } else {
    console.error(`>> WARNING: opening PR with no tag/label (branch '${sourceBranch}' has no recognised type prefix)`);
  }
}

// Same idea for reviewers: a PR with no reviewer record leaves no trace that
// anyone was asked. SHIP_ADO_DEFAULT_REVIEWER supplies a non-blocking default
// when the caller named none. Unset = previous behaviour, no reviewer.
if (optionalReviewers.length === 0 && requiredReviewers.length === 0) {
  const fallback = (process.env.SHIP_ADO_DEFAULT_REVIEWER ?? "").trim();
  if (fallback) {
    optionalReviewers.push(...parseTags([fallback]));
    console.error(`>> NOTE: no reviewer given; using SHIP_ADO_DEFAULT_REVIEWER (${fallback})`);
  }
}

async function runAzure(): Promise<void> {
  const parts = adoParts(url);
  if (!parts) fail(`could not parse org/project/repo from ${url}`);
  const { orgUrl, project, repo } = parts!;

  // Prefer a configured PAT (the standard ADO credential, used by `az devops`).
  // The az-OAuth token only works when the logged-in az identity is an org member;
  // when it differs from the ADO identity it resolves to anonymous (TF400813).
  const pat = process.env.AZURE_DEVOPS_EXT_PAT || process.env.AZURE_DEVOPS_PAT;
  const handler = pat ? azdev.getPersonalAccessTokenHandler(pat) : azdev.getBearerHandler(adoToken());
  const conn = new azdev.WebApi(orgUrl, handler);
  let wit = await conn.getWorkItemTrackingApi();
  let git = await conn.getGitApi();
  let usingPat = !!pat;

  // A PAT that is present but under-scoped (e.g. Code-only, missing Work Items /
  // Pull Request write) makes the write calls below 401 even though the az OAuth
  // identity may be a full org member. Detect that and retry once with the bearer.
  const isAuthError = (e: any): boolean => {
    const code = e?.statusCode ?? e?.status;
    if (code === 401 || code === 403) return true;
    return /\((?:401|403)\)/.test(String(e?.message ?? e));
  };
  const authFallback = async <T>(op: () => Promise<T>): Promise<T> => {
    try {
      return await op();
    } catch (e) {
      if (!usingPat || !isAuthError(e)) throw e;
      console.error(">> PAT auth failed (401/403); falling back to az OAuth bearer token");
      const bconn = new azdev.WebApi(orgUrl, azdev.getBearerHandler(adoToken()));
      wit = await bconn.getWorkItemTrackingApi();
      git = await bconn.getGitApi();
      usingPat = false;
      return await op();
    }
  };

  // Resolve the work item(s) to link: verify any inferred/passed id exists,
  // otherwise create one per task (each assigned to `assignee`).
  const wiIds: number[] = [];
  const existing = workItem ? Number(workItem) : NaN;
  let exists = false;
  if (!Number.isNaN(existing)) {
    try { exists = !!(await authFallback(() => wit.getWorkItem(existing)))?.id; } catch { exists = false; }
  }

  if (exists) {
    wiIds.push(existing);
    console.error(`>> linking existing work item ${existing}`);
  } else if (createWi) {
    const titles = tasks.length ? tasks : [title];
    for (const t of titles) {
      const document: any[] = [{ op: "add", path: "/fields/System.Title", value: t }];
      if (assignee) document.push({ op: "add", path: "/fields/System.AssignedTo", value: assignee });
      const created = await authFallback(() => wit.createWorkItem(null, document, project, wiType));
      const id = created.id!;
      console.error(`>> created ${wiType} #${id} assigned to ${assignee || "<unassigned>"}: ${t}`);
      console.log(`work_item_created=${id}`);
      wiIds.push(id);
    }
  } else if (workItem) {
    console.error(`>> WARNING: work item ${workItem} not found and --no-create-work-item set; PR will not link it`);
  }

  // Back-fill the AB#<...> placeholder (from assets/pr-template.md) with the resolved
  // id(s), so the work-item reference renders as a live link instead of literal text.
  if (wiIds.length && /AB#<[^>]*>/.test(body)) {
    body = body.replace(/AB#<[^>]*>/g, wiIds.map((id) => `AB#${id}`).join(" "));
    console.error(`>> substituted AB# placeholder -> ${wiIds.map((id) => `AB#${id}`).join(" ")}`);
  }

  // Resolve reviewers (optional + required) to identity GUIDs so they can ride
  // along in the create call — no separate add-reviewers round trip. Best-effort:
  // an unresolved name is warned + skipped, never blocking the PR.
  const header = azAuthHeader(pat);
  const reviewerRefs: { id: string; isRequired: boolean; upn: string }[] = [];
  for (const [list, isRequired] of [[optionalReviewers, false], [requiredReviewers, true]] as const) {
    for (const upn of list) {
      const id = await resolveAzureIdentity(orgUrl, header, upn);
      if (!id) {
        console.error(`>> WARNING: could not resolve reviewer '${upn}'; skipping`);
        console.log(`reviewer_skipped=${upn}`);
        continue;
      }
      reviewerRefs.push({ id, isRequired, upn });
    }
  }

  const pr = await authFallback(() => git.createPullRequest(
    {
      sourceRefName: `refs/heads/${sourceBranch}`,
      targetRefName: `refs/heads/${target}`,
      title,
      description: body || undefined,
      isDraft: draft || undefined,
      workItemRefs: wiIds.map((id) => ({ id: String(id) })),
      // Tags and reviewers packed into the create payload (one round trip).
      labels: tags.length ? tags.map((name) => ({ name })) : undefined,
      reviewers: reviewerRefs.length ? reviewerRefs.map(({ id, isRequired }) => ({ id, isRequired })) : undefined,
    },
    repo,
    project,
  ));

  const prId = pr.pullRequestId!;
  console.log("platform=azure");
  console.log(`pr_id=${prId}`);
  console.log(`pr_url=${orgUrl}/${encodeURIComponent(project)}/_git/${encodeURIComponent(repo)}/pullrequest/${prId}`);
  if (wiIds.length) console.log(`work_items=${wiIds.join(" ")}`);

  if (transition && wiIds.length) {
    for (const id of wiIds) {
      console.error(`>> transitioning work item ${id} -> ${transition}`);
      await authFallback(() => wit.updateWorkItem(null, [{ op: "add", path: "/fields/System.State", value: transition }], id, project));
      console.log(`work_item=${id} state=${transition}`);
    }
  }

  // Tags + reviewers were attached in the create payload above — just report them.
  for (const name of tags) console.log(`tag_added=${name}`);
  for (const r of reviewerRefs) console.log(`reviewer_added=${r.upn} required=${r.isRequired}`);
}

async function runGitHub(): Promise<void> {
  const m = url.match(/github\.com[:/]([^/]+)\/([^/]+?)(?:\.git)?$/);
  if (!m) fail(`could not parse owner/repo from ${url}`);
  const [, owner, repo] = m!;
  const token = process.env.GH_TOKEN || process.env.GITHUB_TOKEN || sh("gh", ["auth", "token"], { allowFail: true });
  if (!token) fail("no GitHub token: set GH_TOKEN/GITHUB_TOKEN or run `gh auth login`");

  const octokit = new Octokit({ auth: token });
  const { data } = await octokit.pulls.create({
    owner, repo, base: target, head: sourceBranch, title,
    body: body || undefined, draft,
  });
  console.log("platform=github");
  console.log(`pr_url=${data.html_url}`);
  console.log(`pr_number=${data.number}`);

  if (tags.length) {
    // A PR is an issue on GitHub; labels go through the issues API. A missing
    // label is auto-created on the repo (random color).
    await octokit.issues.addLabels({ owner, repo, issue_number: data.number, labels: tags });
    for (const name of tags) console.log(`tag_added=${name}`);
  }

  // GitHub's create API takes no reviewers — request them in a follow-up call.
  // There's no per-PR "required" reviewer (that's a branch-protection rule), so
  // optional and required alike are simply requested.
  const ghReviewers = parseTags([...reviewerFlags, ...requiredReviewerFlags]);
  if (ghReviewers.length) {
    if (requiredReviewers.length) {
      console.error(">> note: GitHub has no per-PR required reviewer (that's branch protection); requesting them as normal reviewers");
    }
    try {
      await octokit.pulls.requestReviewers({ owner, repo, pull_number: data.number, reviewers: ghReviewers });
      for (const r of ghReviewers) console.log(`reviewer_added=${r}`);
    } catch (e: any) {
      console.error(`>> WARNING: requesting reviewers failed (${e?.message ?? e}); PR is open without them`);
    }
  }
}

async function main(): Promise<void> {
  switch (kind) {
    case "azure": await runAzure(); break;
    case "github": await runGitHub(); break;
    default: fail(`unknown platform for remote '${remote}' (${url}); set SHIP_PLATFORM=azure|github`);
  }
}

main().catch((err) => fail(err?.message ? `ship-pr failed: ${err.message}` : String(err)));
