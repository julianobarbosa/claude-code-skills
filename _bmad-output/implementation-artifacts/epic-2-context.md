# Epic 2 Context: Push and checkpoint

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Let the operator push the current branch and cut snapshot tags from the `ship` binary, on Azure Repos and GitHub, with the Azure Bearer-token auth and stored-credential fallback the TypeScript scripts use today. A stale stored credential must never block delivery, and a push must never be forced. This is the first epic that talks to a remote, so it establishes the auth handling the PR epic reuses. Note: there is no PRD, architecture or UX document; intent comes from the port spec and its CLI parity catalog.

## Stories

- Story 2.1: Push the current branch with `ship push`
- Story 2.2: Save a checkpoint with `ship snapshot`

## Requirements & Constraints

- `push` accepts `-r/--remote` and `-b/--branch`, pushes the branch, sets upstream, and prints `push_ok=oauth-bearer` or `push_ok=normal`. A rejected push exits non-zero and is never retried with force.
- On Azure, the push authenticates with a short-lived token from `az account get-access-token`, sent as an `Authorization: Bearer` header with `credential.helper` emptied. When `az` is logged out it falls back to the stored git credential. On GitHub it pushes normally.
- `snapshot` creates an annotated tag on HEAD named `v<YYYY.MM.DD-HHMM>`. `--daily` gives `v<YYYY.MM.DD>`; `--name` sets the name exactly. The tag message's first paragraph is `Snapshot <tag> — <branch> @ <shorthash>`; each repeatable `-m/--message` becomes its own paragraph.
- `snapshot` prints `tag`, `commit`, `branch` and `pushed` (`false` unless `--push`). An existing tag is refused with exit 3 and is never moved.
- `snapshot --push` pushes the tag with the same auth order as `push` and prints `pushed=true`.
- Azure auth order: `az` token first; `AZURE_DEVOPS_EXT_PAT`/`AZURE_DEVOPS_PAT` only after a 401/403 or when `az` is logged out.
- Tokens appear only in `Authorization` headers: never printed, logged, put in the remote URL, or left in output. Every Bearer git call empties `credential.helper`.
- `git` and `az` are called through argument arrays, never shell strings. Nothing the binary writes carries AI attribution.
- Flags, env vars (`SHIP_PLATFORM` applies), `key=value` stdout and exit codes keep parity with `ship-push.ts` and `ship-snapshot.ts`, which are the reference for formats and for exit codes beyond 0 and 3.
- Supported hosts: Linux/WSL2 and macOS. Rust only; no Python, npm or npx.

## Technical Decisions

- Platform detection and the git-subprocess helper come from Epic 1; reuse them rather than reimplementing. Azure vs GitHub is chosen by the same detection `ship detect` uses.
- Push auth is a shared building block: `snapshot --push` must call the same Bearer-or-fallback path as `push`, so build it once (Story 2.1) and reuse it (Story 2.2).
- Epic 2 needs no REST client: `az` and `git` are subprocesses only. The HTTP/SDK crate decision is deferred to Epic 3 (Story 3.1).
- Port the matching `ship-lib` test cases as Rust unit tests where the logic is pure (tag naming, message paragraphs, auth selection).
- Deferred from Epic 1, relevant here: branch lookup via `rev-parse --abbrev-ref HEAD` prints `HEAD` on a detached head and fails on an unborn branch, and `push` and `snapshot` both consume the branch. Keep parity with the TS behavior unless the fix is made in both, and do not silently diverge.

## Cross-Story Dependencies

- Depends on Epic 1: the crate and CLI skeleton, subcommand dispatch, detection and the git helper from Stories 1.1-1.2.
- Story 2.2's `--push` depends on the auth path built in Story 2.1.
- Epic 3 reuses the Azure token acquisition and the PAT-fallback order established here.
- Epic 5 benchmarks `push` and `snapshot` against the TS scripts, using a throwaway branch for the write paths.
