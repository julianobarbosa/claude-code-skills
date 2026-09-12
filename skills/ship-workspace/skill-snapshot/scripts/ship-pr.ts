#!/usr/bin/env bun
// Open a pull request on the detected platform (Azure Repos via azure-devops-node-api,
// GitHub via @octokit/rest), link work item(s), and optionally transition Board state.
//
// Usage:
//   bun ship-pr.ts --title T [--body B | --body-file F] [--target main] [--source BR]
//                  [--work-item ID] [--task "title" ...] [--tasks-file F]
//                  [--assignee UPN] [--work-item-type TYPE] [--no-create-work-item]
//                  [--transition STATE] [--tag "t1,t2" ...] [--draft] [-r remote]
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
//               $SHIP_ADO_ASSIGNEE, else juliano.barbosa@hypera.com.br.
// --work-item-type  Type for created items (default: Task; e.g. "User Story", Bug).
// --no-create-work-item  Disable auto-creation; link only a pre-existing --work-item.
// --transition  Azure only: sets each linked/created item's state AFTER the PR is
//               created (e.g. Resolved). Skipped on GitHub.
// --tag         PR tag(s) to apply after the PR opens (Azure "tags" / GitHub
//               "labels"). Comma-separated and/or repeatable. e.g. --tag hotfix,WIP.
//               Or manage tags later with ship-tag.ts.

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

// ---- args ----
let title = "", body = "", bodyFile = "", target = "main", sourceBranch = "";
let workItem = "", transition = "", remote = "origin", wiType = "Task";
let assignee = process.env.SHIP_ADO_ASSIGNEE || "juliano.barbosa@hypera.com.br";
let draft = false, createWi = true;
const tasks: string[] = [];
const tagFlags: string[] = [];

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
if (!workItem) workItem = parseWorkItem(sourceBranch);

const url = remoteUrl(remote);
const kind = detectKind(url);
if (bodyFile) body = readFileSync(bodyFile, "utf8");
const tags = parseTags(tagFlags);

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

  const pr = await authFallback(() => git.createPullRequest(
    {
      sourceRefName: `refs/heads/${sourceBranch}`,
      targetRefName: `refs/heads/${target}`,
      title,
      description: body || undefined,
      isDraft: draft || undefined,
      workItemRefs: wiIds.map((id) => ({ id: String(id) })),
    },
    repo,
    project,
  ));

  const prId = pr.pullRequestId!;
  console.log("platform=azure");
  console.log(`pr_id=${prId}`);
  console.log(`pr_url=${orgUrl}/${project}/_git/${repo}/pullrequest/${prId}`);
  if (wiIds.length) console.log(`work_items=${wiIds.join(" ")}`);

  if (transition && wiIds.length) {
    for (const id of wiIds) {
      console.error(`>> transitioning work item ${id} -> ${transition}`);
      await authFallback(() => wit.updateWorkItem(null, [{ op: "add", path: "/fields/System.State", value: transition }], id, project));
      console.log(`work_item=${id} state=${transition}`);
    }
  }

  for (const name of tags) {
    await authFallback(() => git.createPullRequestLabel({ name }, repo, prId, project));
    console.log(`tag_added=${name}`);
  }
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
}

async function main(): Promise<void> {
  switch (kind) {
    case "azure": await runAzure(); break;
    case "github": await runGitHub(); break;
    default: fail(`unknown platform for remote '${remote}' (${url}); set SHIP_PLATFORM=azure|github`);
  }
}

main().catch((err) => fail(err?.message ? `ship-pr failed: ${err.message}` : String(err)));
