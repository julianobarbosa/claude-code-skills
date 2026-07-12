#!/usr/bin/env bun
// Manage tags (Azure DevOps "PR tags" / GitHub PR "labels") on a pull request.
// Tags communicate at-a-glance state to reviewers — work-in-progress, DO NOT
// MERGE, hotfix, area/type — per Microsoft's "Add tags to a pull request" guidance
// (https://learn.microsoft.com/azure/devops/repos/git/pull-requests#add-tags-to-a-pull-request).
//
// Usage:
//   bun ship-tag.ts <pr-id> --add "tag1,tag2" [--add tag3 ...]
//   bun ship-tag.ts <pr-id> --remove "tag1" [--remove tag2 ...]
//   bun ship-tag.ts <pr-id> --list
//   bun ship-tag.ts --pr <pr-id> --add hotfix [-r remote]
//
// <pr-id>      The pull request id. Azure: the numeric PR id (ship-pr.ts prints
//              `pr_id=`). GitHub: the PR number (ship-pr.ts prints `pr_number=`).
// --add T      Tag(s) to add. Comma-separated and/or repeatable. Empty/blank
//              names are dropped. ADO creates the tag definition if new; GitHub
//              auto-creates a missing label (random color) on the repo.
// --remove T   Tag(s) to remove. Comma-separated and/or repeatable.
// --list       Print the PR's current tags, one per line (default if no --add/--remove).
// -r, --remote Git remote to resolve coordinates from (default: origin).
//
// Tags are visible to the team but reversible and low-blast — no destructive
// confirm. Auth mirrors ship-pr.ts: a configured PAT, falling back to an az OAuth
// bearer on a 401/403 (an under-scoped PAT can't write labels a full member can).

import { readFileSync } from "node:fs";
import { Octokit } from "@octokit/rest";
import {
  sh, remoteUrl, detectKind, adoParts, adoConnection, isAuthError, parseTags,
} from "./ship-lib.ts";

function fail(msg: string, code = 1): never {
  console.error(msg);
  process.exit(code);
}

// ---- args ----
let prId = "", remote = "origin", list = false;
const addFlags: string[] = [];
const removeFlags: string[] = [];

const argv = process.argv.slice(2);
let i = 0;
const take = (flag: string): string => {
  const v = argv[++i];
  if (v === undefined) fail(`${flag} requires a value`, 2);
  return v;
};
for (; i < argv.length; i++) {
  const a = argv[i];
  switch (a) {
    case "--pr": prId = take(a); break;
    case "--add": addFlags.push(take(a)); break;
    case "--remove": removeFlags.push(take(a)); break;
    case "--list": list = true; break;
    case "-r": case "--remote": remote = take(a); break;
    case "-h": case "--help":
      console.log(readFileSync(new URL(import.meta.url), "utf8")
        .split("\n").filter((l) => l.startsWith("//")).map((l) => l.slice(3)).join("\n"));
      process.exit(0);
    default:
      if (!prId && /^\d+$/.test(a)) prId = a;
      else fail(`unknown arg: ${a}`, 2);
  }
}
if (!prId) fail("a pull request id is required (positional or --pr)", 2);

const addTags = parseTags(addFlags);
const removeTags = parseTags(removeFlags);
if (!addTags.length && !removeTags.length) list = true; // default action

const url = remoteUrl(remote);
const kind = detectKind(url);

async function runAzure(): Promise<void> {
  const parts = adoParts(url);
  if (!parts) fail(`could not parse org/project/repo from ${url}`);
  const { orgUrl, project, repo } = parts!;
  const id = Number(prId);

  let { conn, usingPat } = adoConnection(orgUrl);
  let git = await conn.getGitApi();
  const authFallback = async <T>(op: () => Promise<T>): Promise<T> => {
    try {
      return await op();
    } catch (e) {
      if (!usingPat || !isAuthError(e)) throw e;
      console.error(">> PAT auth failed (401/403); falling back to az OAuth bearer token");
      ({ conn } = adoConnection(orgUrl, { forceBearer: true }));
      git = await conn.getGitApi();
      usingPat = false;
      return await op();
    }
  };

  for (const name of addTags) {
    await authFallback(() => git.createPullRequestLabel({ name }, repo, id, project));
    console.log(`tag_added=${name}`);
  }
  for (const name of removeTags) {
    try {
      await authFallback(() => git.deletePullRequestLabels(repo, id, name, project));
      console.log(`tag_removed=${name}`);
    } catch (e: any) {
      // a tag that isn't on the PR yields 404 — non-fatal
      console.error(`>> could not remove '${name}': ${e?.message ?? e}`);
    }
  }
  if (list) {
    const labels = await authFallback(() => git.getPullRequestLabels(repo, id, project));
    console.log("platform=azure");
    for (const l of labels) if (l.name) console.log(l.name);
  }
}

async function runGitHub(): Promise<void> {
  const m = url.match(/github\.com[:/]([^/]+)\/([^/]+?)(?:\.git)?$/);
  if (!m) fail(`could not parse owner/repo from ${url}`);
  const [, owner, repo] = m!;
  const token = process.env.GH_TOKEN || process.env.GITHUB_TOKEN || sh("gh", ["auth", "token"], { allowFail: true });
  if (!token) fail("no GitHub token: set GH_TOKEN/GITHUB_TOKEN or run `gh auth login`");
  const octokit = new Octokit({ auth: token });
  const issue_number = Number(prId); // a PR is an issue on GitHub

  if (addTags.length) {
    await octokit.issues.addLabels({ owner, repo, issue_number, labels: addTags });
    for (const name of addTags) console.log(`tag_added=${name}`);
  }
  for (const name of removeTags) {
    try {
      await octokit.issues.removeLabel({ owner, repo, issue_number, name });
      console.log(`tag_removed=${name}`);
    } catch (e: any) {
      console.error(`>> could not remove '${name}': ${e?.message ?? e}`);
    }
  }
  if (list) {
    const { data } = await octokit.issues.listLabelsOnIssue({ owner, repo, issue_number });
    console.log("platform=github");
    for (const l of data) console.log(l.name);
  }
}

async function main(): Promise<void> {
  switch (kind) {
    case "azure": await runAzure(); break;
    case "github": await runGitHub(); break;
    default: fail(`unknown platform for remote '${remote}' (${url}); set SHIP_PLATFORM=azure|github`);
  }
}

main().catch((err) => fail(err?.message ? `ship-tag failed: ${err.message}` : String(err)));
