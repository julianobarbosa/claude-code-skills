#!/usr/bin/env bun
// Push the current (or named) branch and set upstream.
// On Azure DevOps, if the normal push fails on auth, mint an OAuth token and
// retry with a Bearer header — the fallback for when SSH and the HTTPS
// credential helper are both unavailable but `az` is logged in.
//
// Usage: bun ship-push.ts [-r remote] [-b branch]

import { execFileSync } from "node:child_process";
import { currentBranch, remoteUrl, detectKind, adoToken } from "./ship-lib.ts";

function fail(msg: string, code = 1): never {
  console.error(msg);
  process.exit(code);
}

// Run git with inherited stdio so push progress streams. Returns true on success.
function git(args: string[]): boolean {
  try {
    execFileSync("git", args, { stdio: "inherit" });
    return true;
  } catch {
    return false;
  }
}

let remote = "origin";
let branch = "";
const argv = process.argv.slice(2);
for (let i = 0; i < argv.length; i++) {
  switch (argv[i]) {
    case "-r": case "--remote": remote = argv[++i]; break;
    case "-b": case "--branch": branch = argv[++i]; break;
    case "-h": case "--help":
      console.log("Usage: bun ship-push.ts [-r remote] [-b branch]");
      process.exit(0);
    default: fail(`unknown arg: ${argv[i]}`, 2);
  }
}
if (!branch) branch = currentBranch();

const url = remoteUrl(remote);
const kind = detectKind(url);
console.error(`>> pushing ${branch} -> ${remote} (${kind})`);

if (git(["push", "-u", remote, branch])) {
  console.log("push_ok=normal");
  process.exit(0);
}

if (kind !== "azure") {
  fail("push failed and remote is not Azure DevOps; not attempting OAuth fallback");
}

console.error(">> normal push failed; trying Azure DevOps OAuth Bearer fallback");
let token: string;
try {
  token = adoToken();
} catch {
  fail("failed to mint token (is 'az login' done?)");
}
if (!token) fail("failed to mint token (is 'az login' done?)");

// Token is passed as a request header, never in the URL. It is short-lived (~60 min).
if (!git(["-c", `http.extraHeader=Authorization: Bearer ${token}`, "push", "-u", remote, branch])) {
  fail("OAuth Bearer push also failed");
}
console.log("push_ok=oauth-bearer");
