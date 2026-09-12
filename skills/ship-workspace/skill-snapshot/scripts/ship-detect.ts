#!/usr/bin/env bun
// Print the delivery platform and coordinates for a remote, as key=value lines.
// Usage: bun ship-detect.ts [remote]   (default remote: origin)

import { currentBranch, remoteUrl, detectKind, adoParts, parseWorkItem } from "./ship-lib.ts";

const remote = process.argv[2] ?? "origin";
const url = remoteUrl(remote);
const kind = detectKind(url);

console.log(`platform=${kind}`);
console.log(`remote=${remote}`);
console.log(`url=${url}`);
console.log(`branch=${currentBranch()}`);

if (kind === "azure") {
  const parts = adoParts(url);
  if (parts) {
    console.log(`org_url=${parts.orgUrl}`);
    console.log(`project=${parts.project}`);
    console.log(`repo=${parts.repo}`);
  }
}

const wi = parseWorkItem();
if (wi) console.log(`work_item=${wi}`);
