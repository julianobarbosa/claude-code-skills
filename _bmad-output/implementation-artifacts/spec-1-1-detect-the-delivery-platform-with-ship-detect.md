---
title: 'Story 1.1: Detect the delivery platform with ship detect'
type: 'feature'
created: '2026-11-08'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: 'e0633e18b98942870ba5dc7c6c86891b6c4c9557'
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
  - '{project-root}/_bmad-output/specs/spec-ship-rust-port/cli-contract.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The first step of the ship flow (`bun scripts/ship-detect.ts`) needs bun and `node_modules`. Nothing in Rust exists yet, so no later story has a crate to build on.

**Approach:** Create the Rust crate under `skills/ship/` that builds one `ship` binary with subcommands, and implement `ship detect` with byte-identical output to `ship-detect.ts`. Port the detect-related pure helpers and their test cases.

## Boundaries & Constraints

**Always:** Output parity with `ship-detect.ts`: same keys, same values, same line order (`platform`, `remote`, `url`, `branch`, then `org_url`/`project`/`repo` only for a parsable Azure URL, then `work_item` only when non-empty). Optional positional `[remote]`, default `origin`. `SHIP_PLATFORM=azure|github` overrides detection. `git` runs through `std::process::Command` with an argument array, never a shell. Unparsable Azure URLs omit the three Azure keys rather than failing. A missing remote yields `url=` (empty) and `platform=unknown`, like the TS `allowFail` path.

**Never:** No network calls, no HTTP crates, no async runtime in this story. Do not modify or delete any `scripts/*.ts` file, `package.json` or `SKILL.md` (cutover is Story 5.2). No npm, npx or Python in build or test. No `preflight` or other subcommands yet beyond what `--help` lists.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| GitHub clone | origin `https://github.com/julianobarbosa/claude-code-skills.git`, branch `main` | `platform=github` `remote=origin` `url=…` `branch=main`; no Azure keys, no `work_item` | N/A |
| Azure HTTPS | `https://dev.azure.com/myorg/myproj/_git/myrepo` | adds `org_url=https://dev.azure.com/myorg` `project=myproj` `repo=myrepo` | N/A |
| Azure SSH / legacy | `git@ssh.dev.azure.com:v3/org/proj/repo`, `https://org.visualstudio.com/proj/_git/repo` | same three Azure keys; `%20` in project/repo decoded | invalid `%` sequence kept raw, never panics |
| Work item on branch | branch `feature/837-foo` or `AB#1234` | `work_item=837` / `work_item=1234` | none found: line omitted |
| Override | `SHIP_PLATFORM=github` on an Azure URL | `platform=github`, no Azure keys | other values ignored |
| No such remote | `ship detect nope` | `platform=unknown`, `remote=nope`, `url=` | exit 0, like TS |
| Not a git repo | run outside a repo | `platform=unknown`, `remote=origin`, `url=` printed, then the branch lookup fails (same as TS) | error on stderr, non-zero exit |

</frozen-after-approval>

## Code Map

- `skills/ship/scripts/ship-detect.ts` -- reference behavior and line order; leave untouched.
- `skills/ship/scripts/ship-lib.ts` -- port `detectKind` (L44), `decodeSegment` + `adoParts` (L55-75, both regexes), `parseWorkItem` (L246), `githubOwnerRepo` (L257), `currentBranch`/`remoteUrl` (L33-41). Do not port anything Azure-auth or SDK related.
- `skills/ship/scripts/ship-lib.test.ts` -- test cases to port 1:1: `parseWorkItem` (L122), `detectKind` (L128), `adoParts` (L134), `githubOwnerRepo` (L147, including both alias cases).
- `skills/ship/.gitignore` -- currently `node_modules/`, `bun.lock`; add `target/`.
- No existing Rust anywhere in the repo; `cargo 1.96.1` is installed.

## Tasks & Acceptance

**Execution:**
- [x] `skills/ship/Cargo.toml` -- package `ship`, bin `ship`, edition 2024 (or the newest the toolchain supports), deps `clap` (derive) and `regex` only, `[profile.release]` with `lto`/`strip` -- one small binary, fast startup
- [x] `skills/ship/src/main.rs` -- clap CLI with `detect [REMOTE]` subcommand and `--version`; dispatch only -- keeps subcommands addable by later stories
- [x] `skills/ship/src/lib.rs` (+ `src/git.rs`, `src/detect.rs` as needed) -- ported helpers and `detect` printing -- pure functions testable without git
- [x] `skills/ship/src/lib.rs` tests -- port the four test groups plus the I/O matrix parse cases (SSH v3, visualstudio, `%20`, bad `%`) -- parity proof for the pure logic
- [x] `skills/ship/.gitignore` -- add `target/` -- keep build output out of git

**Acceptance Criteria:**
- Given this repo, when running `ship detect` and `bun scripts/ship-detect.ts` from the same directory, then `diff` of their stdout is empty.
- Given a scratch repo with an Azure HTTPS remote and branch `feature/837-foo`, when running both, then stdout is identical and includes the three Azure keys and `work_item=837`.
- Given `ship --help` or `ship detect --help`, then usage prints and the exit code is 0.

## Implementation Notes

- Crate: `Cargo.toml` (edition 2024, `rust-version = "1.88"`, clap + regex), `src/main.rs`, `src/lib.rs`, `src/git.rs`, `src/detect.rs`, `tests/detect.rs`; `Cargo.lock` committed; `target/` ignored.
- `\d` written as `[0-9]` (Rust `\d` is Unicode, JS is ASCII). Output goes through a locked stdout; `BrokenPipe` exits 0 quietly.
- Parity evidence: the bun reference needs `node_modules`, absent in this worktree, so it ran from a scratchpad copy of `scripts/` with `bun install`; 11/11 cases identical in stdout and exit code. Golden-output integration tests now pin the same cases without bun.
- Verified after review patches: `cargo test` 25 unit + 7 integration, green on 3 consecutive runs; `cargo clippy --all-targets -D warnings` clean; `ship detect | head -1` exits 0; missing git reports `failed to run git`.

## Spec Change Log

## Review Triage Log

Pass 1 (blind-hunter BH, edge-case-hunter EC, verification-gap VG). Parity with `ship-detect.ts` is frozen intent, so TS-inherited behavior is deferred, not changed.

| # | Finding | Verdict | Evidence | Route |
|---|---|---|---|---|
| 1 | BH1/EC1: `println!` panics on a closed pipe; `panic=abort` gives exit 134 | medium | Reproduced: `ship detect \| head -1` → panic, rc=134. Introduced by this change. | patch |
| 2 | VG1/BH2: no test runs `detect::run`; line order, Azure-key gating, `work_item` omission unpinned | medium | 20 tests are all pure-helper; main.rs ran 0 tests; deleting the `Platform::Azure` guard keeps `cargo test` green. | patch (same root as 3, 4) |
| 3 | VG2: git error contract (missing remote → `url=` exit 0; non-repo → 3 lines, exit 1) untested | medium | No test calls `git::*` or the binary. Same root as 2. | patch |
| 4 | VG3/BH3: spec's parity `diff` passes vacuously when both sides print nothing (no `node_modules` here) | medium | VG ran it: missing binary vs failing bun gave empty diff. Same root as 2: fix with golden-output integration tests. | patch |
| 5 | BH4/EC22: `Cargo.lock` untracked | low | `git status` shows `?? Cargo.lock`; binary crate needs it for reproducible builds. Direct correction: commit it. | patch |
| 6 | BH4/EC21: no `rust-version`; edition 2024 + let-chains need 1.88 | low | `Cargo.toml` has no `rust-version`. One-line addition. | patch |
| 7 | BH6/EC6: git missing gives `ship: No such file or directory` | low | Reproduced with `PATH=/nonexistent`. TS ENOENT names `git`, so this regresses. One `map_err`. | patch |
| 8 | BH9: `about` duplicates `Cargo.toml` description | low | `main.rs` hard-codes it; `#[command(about)]` reads Cargo metadata. Direct deletion. | patch |
| 9 | BH7: work-item parser quirks unpinned by tests (`tab12`, truncation, `AB1234`, lone digit, precedence) | low | No test covers them; pinning tests add no complexity. Behavior itself is TS parity (see 13). | patch |
| 10 | BH5/EC5: remote starting with `-` is read as a git option | low | Real, but `ship-detect.ts` passes `argv[2]` to git identically. Pre-existing. | defer |
| 11 | EC3/EC4: newline in remote name or `%0A` in a path segment injects `key=value` lines | low | Real, identical in TS; needs a hostile remote name. Unlikely and the fix adds guards. | reject |
| 12 | EC2: Azure platform with unparsable URL prints no warning | false | Frozen matrix requires omitting the three keys silently, like TS. | reject |
| 13 | EC7-9: detached HEAD prints `branch=HEAD`; unborn branch fails; tag/branch ambiguity prints `heads/x` | medium | Real, but `currentBranch()` in TS uses the same `rev-parse --abbrev-ref`. Pre-existing; fixing it here breaks parity. | defer |
| 14 | EC10-15, EC19-20: URL classification/parsing gaps (case, non-host match, trailing slash, `DefaultCollection`, `vs-ssh`, project-less form, GitHub port, `SHIP_PLATFORM` case) | medium | Each verified against the identical JS regex or logic. Pre-existing. | defer |
| 15 | EC16-18: work-item false positives (`tab12`→12, 8-digit truncation, date `2026`) | medium | Verified on JS regex. Pre-existing; pinned by 9. | defer |
| 16 | VG4/BH8: no CI job builds or tests the crate | medium | Only `lint-skills.yml` exists, and TS tests are not CI-run either. Pre-existing gap, fits Story 1.3. | defer |
| 17 | VG-other/EC23: clap rejects extra positionals and `-`-prefixed remotes (exit 2) where TS ignores them | low | Real divergence, but SKILL.md never passes extra args; fixing needs trailing-var-arg capture. Rarely met. | reject |

## Design Notes

The JS regexes port to the `regex` crate unchanged: none uses lookaround or backreferences. `adoParts` must try the `dev.azure.com` pattern before the `visualstudio.com` one, and `.git` is stripped from the repo before decoding. `decodeSegment` is a percent-decoder that returns the raw segment on any invalid sequence; hand-roll it (about 15 lines) rather than adding a crate.

`--help` is new relative to the TS script (where `--help` would have been read as a remote name). It is additive and the epics require it.

## Verification

**Commands:**
- `cargo test --manifest-path skills/ship/Cargo.toml` -- expected: all ported tests pass
- `cargo build --release --manifest-path skills/ship/Cargo.toml` -- expected: binary at `skills/ship/target/release/ship`
- `diff <(skills/ship/target/release/ship detect) <(bun skills/ship/scripts/ship-detect.ts)` -- expected: no output
- Same diff in a scratch repo with remote `https://dev.azure.com/myorg/my%20proj/_git/myrepo` on branch `feature/837-foo` -- expected: no output
