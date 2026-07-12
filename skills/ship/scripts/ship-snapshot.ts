#!/usr/bin/env bun
// Save the current state as an annotated git tag — a lightweight checkpoint you
// can return to. The tag points at HEAD; the working tree doesn't matter.
//
// The name auto-fills from the date so it's never stale, and the first message
// paragraph auto-fills branch + short hash so the tag is self-describing even if
// you pass no message. Extra -m paragraphs (what changed, verification) are
// yours to supply. This is a *git tag* (a commit checkpoint), distinct from
// ship-tag.ts, which manages PR labels/tags — different concept entirely.
//
// Usage:
//   bun ship-snapshot.ts [-m "para"]... [--daily] [--name <tag>] [--push] [--annotate-note "..."]
//
//   -m, --message "<text>"   Extra message paragraph (repeatable). Each becomes
//                            its own blank-line-separated paragraph in the tag.
//   --daily                  Name = v<YYYY.MM.DD> (one tag/day). Default includes
//                            -HHMM so multiple snapshots/day don't collide.
//   --name <tag>             Use this exact tag name, ignoring the date scheme.
//   --push                   Push the tag to origin after creating it (Azure
//                            OAuth Bearer fallback on auth failure, like ship-push).
//   -h, --help               Show usage.
//
// Output (stdout): tag=<name>  commit=<shorthash>  branch=<branch>  pushed=<yes|no>

import { execFileSync } from "node:child_process";
import { sh, currentBranch, remoteUrl, detectKind, adoToken } from "./ship-lib.ts";

function fail(msg: string, code = 1): never {
  console.error(msg);
  process.exit(code);
}

// git with inherited stdio (push progress streams). Returns true on success.
function gitStreamed(args: string[]): boolean {
  try {
    execFileSync("git", args, { stdio: "inherit" });
    return true;
  } catch {
    return false;
  }
}

let daily = false;
let push = false;
let name = "";
const messages: string[] = [];
const argv = process.argv.slice(2);
for (let i = 0; i < argv.length; i++) {
  switch (argv[i]) {
    case "-m": case "--message": messages.push(argv[++i]); break;
    case "--daily": daily = true; break;
    case "--name": name = argv[++i]; break;
    case "--push": push = true; break;
    case "-h": case "--help":
      console.log(
        'Usage: bun ship-snapshot.ts [-m "para"]... [--daily] [--name <tag>] [--push]',
      );
      process.exit(0);
    default: fail(`unknown arg: ${argv[i]}`, 2);
  }
}

// Must be inside a git repo with a commit to point at.
const head = sh("git", ["rev-parse", "--short", "HEAD"], { allowFail: true });
if (!head) fail("not a git repo, or no commits yet — nothing to snapshot", 2);
const branch = currentBranch();

// Tag name: explicit --name wins; otherwise date-based. `date` (not JS Date) so
// the output matches the shell pattern and respects the machine's local TZ.
if (!name) {
  const fmt = daily ? "+v%Y.%m.%d" : "+v%Y.%m.%d-%H%M";
  name = sh("date", [fmt]);
}

// Refuse to clobber an existing tag — a snapshot must never silently move a tag
// someone else relies on. With the default minute-granular name this only bites
// on two snapshots in the same minute; --daily collides for the rest of the day.
if (sh("git", ["rev-parse", "-q", "--verify", `refs/tags/${name}`], { allowFail: true })) {
  fail(
    `tag '${name}' already exists. Use --name <other>, or drop --daily for minute granularity.`,
    3,
  );
}

// Auto subject makes the tag self-describing even with no -m. Extra paragraphs
// follow. execFileSync (via sh) takes an arg array — no shell — so newlines and
// punctuation in messages are passed through verbatim, never re-interpreted.
const subject = `Snapshot ${name} — ${branch} @ ${head}`;
const tagArgs = ["tag", "-a", name, "-m", subject];
for (const m of messages) tagArgs.push("-m", m);
sh("git", tagArgs);
console.error(`>> created annotated tag ${name} -> ${head} (${branch})`);

let pushed = "no";
if (push) {
  const remote = "origin";
  const kind = detectKind(remoteUrl(remote));
  console.error(`>> pushing tag ${name} -> ${remote} (${kind})`);
  if (gitStreamed(["push", remote, name])) {
    pushed = "yes";
  } else if (kind === "azure") {
    // Mirror ship-push: under-scoped/absent git creds but `az` logged in.
    console.error(">> normal push failed; trying Azure DevOps OAuth Bearer fallback");
    let token = "";
    try { token = adoToken(); } catch { /* handled below */ }
    if (!token) fail("tag created locally, but push failed: could not mint token (is 'az login' done?)");
    if (!gitStreamed(["-c", `http.extraHeader=Authorization: Bearer ${token}`, "push", remote, name])) {
      fail(`tag '${name}' created locally, but OAuth Bearer push also failed`);
    }
    pushed = "yes-oauth-bearer";
  } else {
    fail(`tag '${name}' created locally, but push failed (remote is ${kind}; no OAuth fallback)`);
  }
}

console.log(`tag=${name}`);
console.log(`commit=${head}`);
console.log(`branch=${branch}`);
console.log(`pushed=${pushed}`);
