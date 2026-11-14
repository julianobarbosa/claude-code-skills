---
tracker_id: ""
type: epic
title: "The binary inspects a repo without bun"
parent: initiative-ship-rust-port
covers: ["R1", "R2", "R13"]
sources: ["_bmad-output/initiative-ship-rust-port/archive-v6/epics.md"]
companions: []
after: []
status: done
risk: medium
---

# The binary inspects a repo without bun

## Description

The operator installs a prebuilt `ship` binary with no bun and runs `ship detect` and `ship preflight`, getting the same output as the TS scripts. This epic settles the distribution decision for every later epic.

## Outcome

An operator on a clean machine can inspect any repo with the compiled binary and see exactly what the TypeScript scripts printed.

## Requirements

R1 (parent R1): `ship detect` prints platform, remote, url, Azure org_url/project/repo, branch and inferred work item, matching `ship-detect.ts`; `SHIP_PLATFORM` overrides detection.
R2 (parent R2): `ship preflight` prints `branch`, `commits_ahead_of_upstream`, `staged`, `unstaged`, `untracked` and `scope_clean`, matching `ship-preflight.ts`, and always exits 0.
R3 (parent R13): A prebuilt binary runs on a clean Linux/WSL2 and a clean macOS host with no bun installed.

## Constraints

- The binary layout is undecided; one binary with subcommands is assumed and the distribution choice is recorded as a decision in `skills/ship/`.
- The `ship-lib.test.ts` cases for `detectKind`, `adoParts`, `parseWorkItem`, `githubOwnerRepo`, `parsePorcelainStatus` and `scopeAudit` are ported as Rust unit tests.

## Done when

- `ship detect` and `ship preflight` match their TS scripts line for line on an Azure clone and a GitHub clone.
- Binaries exist for Linux x86_64 and macOS arm64, built with no npm, npx or Python.
- The documented install step gives a working binary on a host with no bun, and `ship --version` prints the release version.

## Boundaries

- Write subcommands belong to epics 2 and 3; this epic reads only.
- Must not change: the stdout key order of either subcommand.

## References

- parent — _bmad-output/initiative-ship-rust-port/initiative-ship-rust-port.md, section Requirements
- contract — _bmad-output/initiative-ship-rust-port/spec-ship-rust-port/cli-contract.md
