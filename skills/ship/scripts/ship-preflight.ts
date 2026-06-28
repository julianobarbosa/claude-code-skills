#!/usr/bin/env bun
// Preflight check before a ship: is there anything to deliver, and is the working
// tree scope clean? Prints key=value lines + human warnings. Advisory only — always
// exits 0 (it never blocks; the human decides). Run this first, before committing.
//
// Usage: bun ship-preflight.ts [remote]   (default remote: origin)
//
// The scope check guards the PR #192 class of miss: a changed file in another dir is
// left unstaged and silently omitted from the PR. When scope_clean=false, surface the
// listed files and confirm they're intentionally excluded before committing.

import { sh, currentBranch, scopeAudit } from "./ship-lib.ts";

if (process.argv.includes("-h") || process.argv.includes("--help")) {
  console.log("bun ship-preflight.ts [remote] — anything-to-deliver + working-tree scope audit");
  process.exit(0);
}

console.log(`branch=${currentBranch()}`);

// Anything to deliver? Commits ahead of the upstream (empty if no upstream yet — a
// not-yet-pushed branch still has unpushed local commits, surfaced separately below).
const ahead = sh("git", ["log", "--oneline", "@{u}.."], { allowFail: true });
const aheadCount = ahead ? ahead.split("\n").length : 0;
console.log(`commits_ahead_of_upstream=${aheadCount}`);

const audit = scopeAudit(sh("git", ["status", "--porcelain"], { allowFail: true }));
console.log(`staged=${audit.staged.length}`);
console.log(`unstaged=${audit.unstaged.length}`);
console.log(`untracked=${audit.untracked.length}`);
console.log(`scope_clean=${audit.ok}`);

if (audit.unstaged.length) console.error(`>> WARNING: ${audit.unstaged.length} file(s) changed but not staged: ${audit.unstaged.join(", ")}`);
if (audit.untracked.length) console.error(`>> WARNING: ${audit.untracked.length} untracked file(s): ${audit.untracked.join(", ")}`);
if (!audit.ok) console.error(">> Confirm these don't belong in this PR before committing (the PR #192 guard).");
