---
tracker_id: ""
type: initiative
title: "ship runs as a compiled binary on a host with no bun"
sources: ["_bmad-output/initiative-ship-rust-port/archive-v6/epics.md", "_bmad-output/initiative-ship-rust-port/spec-ship-rust-port/spec-ship-rust-port.md"]
companions: ["_bmad-output/initiative-ship-rust-port/spec-ship-rust-port/cli-contract.md", "_bmad-output/initiative-ship-rust-port/implementation-readiness/implementation-readiness.md"]
after: []
status: in-progress
risk: medium
---

# ship runs as a compiled binary on a host with no bun

## Description

The `ship` skill delivers branches through seven TypeScript scripts that need bun and `node_modules` on every host that runs them. This initiative ports those scripts to one Rust binary with subcommands, keeping every flag, environment variable, `key=value` stdout line and exit code in `cli-contract.md` intact, so the skill works on a clean Linux/WSL2 or macOS machine with no JavaScript runtime installed. There is no PRD and no architecture document: the requirements below come from `archive-v6/epics.md`, which derived them from `spec-ship-rust-port` and `skills/ship/SKILL.md`.

## Outcome

The operator installs one prebuilt binary and runs the whole delivery flow from it, with no bun, npm, npx or Python anywhere in build, test or install.

## Requirements

R1 (FR1): `ship detect` prints platform, remote, url, Azure org_url/project/repo, branch and inferred work item, matching `ship-detect.ts`; `SHIP_PLATFORM` overrides detection.
R2 (FR2): `ship preflight` prints `branch`, `commits_ahead_of_upstream`, `staged`, `unstaged`, `untracked` and `scope_clean`, matching `ship-preflight.ts`, and always exits 0.
R3 (FR3): `ship push` pushes the current branch and sets upstream; on Azure it uses an `az` Bearer token with `credential.helper` emptied and falls back to the stored credential when `az` is logged out; reports `push_ok=oauth-bearer|normal`; never force-pushes.
R4 (FR4): `ship pr` opens a PR on the detected platform; on Azure it verifies the work item or creates one per task assigned to `SHIP_ADO_ASSIGNEE`, and links it.
R5 (FR5): `ship pr --related` verifies each id and links it Related to the PR's own work item, never to the PR.
R6 (FR6): `ship pr --transition` moves each linked or created item after the PR opens; `completionOptions.transitionWorkItems` is set by a post-create update and read back from that response.
R7 (FR7): `ship pr` applies tags from `--tag`, else the Conventional-Commit title, else the branch prefix, else `needs-review` with a warning; `--no-tag` disables.
R8 (FR8): `ship pr` adds optional and required reviewers, resolving Azure UPNs and skipping unresolvable ones with `reviewer_skipped`; `SHIP_ADO_DEFAULT_REVIEWER` applies on Azure when none is given.
R9 (FR9): On GitHub, `ship pr` creates the PR, then attaches labels and reviewers in follow-up calls.
R10 (FR10): `ship tag <pr-id>` adds, removes and lists PR tags (Azure) or labels (GitHub).
R11 (FR11): `ship open` lists browser profiles from `Local State`, resolves an email to a profile directory, opens a URL in it, and `--set-default` writes `~/.config/ship/open.json`; works from WSL and macOS.
R12 (FR12): `ship snapshot` creates an annotated tag on HEAD named `v<YYYY.MM.DD-HHMM>`, refuses an existing tag with exit 3, and `--push` pushes it with the same auth as R3.
R13 (FR13): A prebuilt binary runs all seven subcommands on a clean Linux/WSL2 and a clean macOS host with no bun installed.
R14 (NFR1): Behavioral parity: every flag, environment variable, `key=value` stdout line and exit code in `cli-contract.md` is preserved.
R15 (NFR2): `git`, `az` and `gh` are subprocess calls built from argument arrays, never shell strings.
R16 (NFR3): Tokens appear only in `Authorization` headers, are short-lived, and are never printed, logged or put in URLs; every Bearer git call empties `credential.helper`.
R17 (NFR4): No AI attribution in any commit, PR title or PR body the binary writes.
R18 (NFR5): Azure auth order is `az account get-access-token` first; the PAT variables only after a 401/403 or when `az` is logged out.
R19 (NFR6): GitHub auth order is `GH_TOKEN`/`GITHUB_TOKEN`, then `gh auth token -u <owner>`, then the active account.
R20 (NFR7): Supported hosts are Linux/WSL2 and macOS.
R21 (NFR8): Rust only; no Python, npm or npx in build, test or install.
R22 (NFR9): Startup per subcommand is faster than the bun script it replaces, with a median under 50 ms for `detect` and `preflight` on Linux/WSL2.

## Constraints

- No architecture document exists. The binary layout (one binary with subcommands is assumed), the HTTP or SDK crates for Azure DevOps and GitHub, and the distribution mechanism are undecided and are recorded as decisions inside the stories that first need them.
- The existing `ship-lib.test.ts` cases are the parity baseline and are ported to Rust tests.
- Gotchas the port must keep: `createPullRequest` drops `completionOptions`; a GitHub 404 on create usually means the wrong account; `TF400813` right after a UPN rename is ADO's identity cache; titles are passed literally so `&` is never escaped.

## Done when

- Every subcommand of the binary matches its TypeScript script on the `cli-contract.md` catalog, proved by a side-by-side parity run on one Azure and one GitHub repo.
- A prebuilt binary installs and runs on a clean Linux/WSL2 and a clean macOS host with no bun.
- `SKILL.md` invokes `ship <subcommand>` only, and `scripts/*.ts`, `package.json`, `tsconfig.json` and `node_modules` are gone from `skills/ship/`.
- Median startup for `detect` and `preflight` is under 50 ms on Linux/WSL2 and faster than the bun scripts for every subcommand.

## Boundaries

- `ship-tag` (the release skill) is out of scope unless decided otherwise.
- R14 to R21 are cross-cutting: they are restated in the acceptance criteria of each story that touches them rather than owned by one epic.
- Tracer path: `ship detect` and `ship preflight` prove the binary and its distribution (epic 1), `ship push` and `ship snapshot` prove write auth (epic 2), `ship pr` and `ship tag` prove the platform APIs (epic 3), `ship open` proves host launching (epic 4), and the cutover retires the scripts (epic 5).

## References

- parent — none; this is the top initiative
- epics — _bmad-output/initiative-ship-rust-port/archive-v6/epics.md, section Requirements Inventory
- spec — _bmad-output/initiative-ship-rust-port/spec-ship-rust-port/spec-ship-rust-port.md
- contract — _bmad-output/initiative-ship-rust-port/spec-ship-rust-port/cli-contract.md
- readiness — _bmad-output/initiative-ship-rust-port/implementation-readiness/implementation-readiness.md

## Notes

- Assumption: one binary with subcommands, rather than seven binaries. Recorded in epics.md as an open architecture decision.
- Open question: distribution mechanism (committed per-platform builds, `cargo install`, or GitHub Releases) is settled inside story 1.3.
- Open question: the HTTP or SDK crates for the GitHub and Azure DevOps REST APIs are settled inside story 3.1.
- Decision: 2026-11-14 — migrated from the v6 layout; initiative named after its content, `ship-rust-port`, rather than the project name.
- Decision: 2026-11-14 — story 5.1's v6 status `awaiting-operator` maps to v7 `in-review`.
- Action item: Harden ship open input (Rust only): reject dash-leading URLs and option values, http/https-only URLs without whitespace or quotes, ps_quote doubles U+2018-U+201B, skip empty PATH entries, fix stale comments, emit profile_fallback= on stdout (R1-R5, R11, R12) — owner Barbosa, epic 4.
- Action item: Close the six ship open verification gaps so each surviving mutation fails a test (R13-R18) — owner Barbosa, epic 4.
- Action item: Reconcile the contract: powershell Start-Process / open -na launch wording in epics.md and cli-contract.md, document SHIP_OPEN_* test seams, launch-failure exit 2, and the profile_fallback= key (F1, F2, R6, R11) — owner Barbosa, epic 4.
- Action item: Add real-launch checks on WSL and macOS to the Story 5-1 parity checklist — owner Barbosa, epic 4.
- Action item: Process: when a story records a contract deviation or a new SHIP_* override, the contract edit lands in the same PR — owner Barbosa, epic 4.
- Action item: Log deferred findings R6 stderr, R7, R8, R9, R10 in deferred-work.md — owner Barbosa, epic 4.
