# Epic 1 Context: First binary: inspect a repo

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Deliver the first prebuilt `ship` binary, with no bun or `node_modules` needed, that runs `ship detect` and `ship preflight` with output identical to the TypeScript scripts they replace. This epic also settles how the binary is distributed, which the rest of the port depends on. Note: there is no PRD, architecture or UX document; intent comes from the port spec and its CLI parity catalog.

## Stories

- Story 1.1: Detect the delivery platform with `ship detect`
- Story 1.2: Audit delivery scope with `ship preflight`
- Story 1.3: Install a prebuilt binary without bun

## Requirements & Constraints

- `detect` prints platform (`azure|github|unknown`), remote, url, Azure org_url/project/repo, branch and inferred work item, in the same keys and line order as the TS script. `SHIP_PLATFORM` forces `azure` or `github` when detection returns `unknown`; an unparseable SSH host alias yields `platform=unknown`.
- `preflight` prints branch, commits ahead of upstream, staged/unstaged/untracked counts and `scope_clean`. It is advisory and always exits 0, including with no upstream.
- Both take an optional positional remote; every subcommand accepts `--help` (exit 0).
- Stdout is `key=value` lines; flags, env vars and exit codes must keep parity with the TS scripts, which are the reference for formats and edge cases.
- `git` is invoked via argument arrays, never shell strings. No AI attribution in anything the binary writes.
- Hosts: Linux/WSL2 and macOS. Build, test and install use Rust only: no Python, npm or npx.
- Success: prebuilt binaries for Linux x86_64 and macOS arm64; on a host without bun, the documented install step yields working `ship detect` and `ship preflight`; `ship --version` prints the release version.
- Startup target (checked in a later epic): median under 50 ms for `detect` and `preflight` on Linux/WSL2.

## Technical Decisions

- One Rust crate under `skills/ship/` builds a single `ship` binary with subcommands (`detect|preflight|push|pr|tag|open|snapshot`); this layout is assumed, not yet recorded as a decision, so Epic 1 should record it.
- Distribution is an open decision this epic must make and record in `skills/ship/` with its reason: committed per-platform builds, `cargo install` from the repo, or GitHub Releases.
- HTTP/SDK crate choice for Azure DevOps and GitHub (raw REST vs a crate such as `octocrab`) is open; Epic 1 needs no network calls, so defer it.
- Port the relevant `ship-lib.test.ts` cases as Rust unit tests: `detectKind`, `adoParts`, `parseWorkItem`, `githubOwnerRepo` (1.1) and `parsePorcelainStatus`, `scopeAudit` (1.2).
- The work item is inferred from the branch name; Azure coordinates come from parsing the remote URL.

## Cross-Story Dependencies

- Story 1.1 creates the crate and CLI skeleton (`--help`, subcommand dispatch, git-subprocess helper) that 1.2 and 1.3 build on.
- Story 1.3 packages whatever 1.1 and 1.2 produce; the version string it prints comes from the release.
- Later epics reuse the detection logic (Epics 2-4) and the distribution mechanism (Epic 5 cutover and startup benchmark).
