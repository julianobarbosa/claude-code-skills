#!/usr/bin/env bun
// Push the current (or named) branch and set upstream.
// On Azure DevOps, the push authenticates with an az OAuth token as a Bearer
// header FIRST: it is minted from whoever `az login` is right now, so it cannot
// go stale the way a stored HTTPS credential can (an Entra account rename left
// the keychain entry answering 401, 2026-10-26). The stored credential / SSH is
// only the fallback, for when `az` is not logged in.
//
// Usage: bun ship-push.ts [-r remote] [-b branch]

import { execFileSync } from "node:child_process";
import { currentBranch, remoteUrl, detectKind, tryAdoToken, adoBearerGitArgs } from "./ship-lib.ts";

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

if (kind === "azure") {
  // Token is passed as a request header, never in the URL. It is short-lived (~60 min).
  const token = tryAdoToken();
  if (token && git([...adoBearerGitArgs(token), "push", "-u", remote, branch])) {
    console.log("push_ok=oauth-bearer");
    process.exit(0);
  }
  console.error(token
    ? ">> OAuth Bearer push failed; trying the stored git credential"
    : ">> could not mint an az token (is 'az login' done?); trying the stored git credential");
}

if (!git(["push", "-u", remote, branch])) fail("push failed");
console.log("push_ok=normal");
