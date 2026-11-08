---
title: 'Story 2.1: Push the current branch with ship push'
type: 'feature'
created: '2026-11-08'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: '873e9b452957135ad890b74dfe3f15cccd1852f5'
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-2-context.md'
  - '{project-root}/_bmad-output/specs/spec-ship-rust-port/cli-contract.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Pushing a branch for delivery still needs `bun scripts/ship-push.ts`. On Azure Repos that script is what keeps a stale stored credential from blocking a push, and the `ship` binary has no equivalent yet.

**Approach:** Add `ship push [-r REMOTE] [-b BRANCH]` to the crate. It keeps the TS behavior and output: on Azure, push with an `az` Bearer token first and fall back to a normal push. Build the Bearer-or-fallback push as a reusable piece, so `snapshot --push` (Story 2.2) calls the same code.

## Boundaries & Constraints

**Always:** Defaults are `-r origin` and the current branch (`rev-parse --abbrev-ref HEAD`, same as TS). Stderr prints `>> pushing <branch> -> <remote> (<kind>)` before pushing, with `kind` from the existing `detect_kind` (`SHIP_PLATFORM` applies). On `azure`, mint a token with `az account get-access-token --resource 499b84ac-1321-427f-aa17-267ca6975798 --query accessToken -o tsv`. If a token comes back, run `git push -u <remote> <branch>` with `credential.helper` emptied and `http.extraHeader=Authorization: Bearer <token>`. Success prints `push_ok=oauth-bearer`. Otherwise print the TS stderr notice: `>> OAuth Bearer push failed; trying the stored git credential`, or `>> could not mint an az token (is 'az login' done?); trying the stored git credential` when there was no token. Then run the plain `git push -u <remote> <branch>`, which prints `push_ok=normal` on success. `github` and `unknown` go straight to the plain push. git's push progress streams to the terminal (inherited stdio). Any failure of the final push prints `push failed` on stderr and exits 1. An unknown argument exits 2, and `--help` exits 0. `git` and `az` run through argument arrays only. Reuse `git.rs`, `detect_kind` and the stdout/BrokenPipe handling.

**Decision (Barbosa, 2026-11-08): the Bearer settings reach git through the environment.** Both pairs (`credential.helper` = empty, `http.extraHeader` = `Authorization: Bearer <token>`) are passed as `GIT_CONFIG_COUNT`/`GIT_CONFIG_KEY_n`/`GIT_CONFIG_VALUE_n` on the push process only, never as `-c` arguments, so the token stays out of argv and `ps`. Stdout, stderr and exit codes keep byte parity with TS; this is the one intended difference, and it is in mechanism only.

**Never:** No `--force`, `--force-with-lease` or `+refspec`, and no other retry beyond the one documented fallback. The token never appears in stdout, stderr, the remote URL, the git config on disk or any file. No PAT handling (`AZURE_DEVOPS_*_PAT`), which belongs to Epic 3's REST calls. No change to `detect`/`preflight`, `scripts/*.ts`, `package.json` or `SKILL.md`. No new dependencies and no network calls beyond the push itself.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| GitHub push | github remote, new branch | upstream set; stdout `push_ok=normal` | N/A |
| Azure, az logged in | `SHIP_PLATFORM=azure`, `az` prints a token | Bearer push succeeds; stdout `push_ok=oauth-bearer`; token absent from stdout, stderr and `.git/config` | N/A |
| Azure, az logged out | `az` exits non-zero or is missing | "could not mint" notice; plain push; `push_ok=normal` | N/A |
| Azure, Bearer push fails | token minted, Bearer push rejected | "OAuth Bearer push failed" notice; plain push runs once | plain push fails → `push failed`, exit 1 |
| Rejected push | remote has diverged history | nothing pushed, no force attempted | `push failed`, exit 1, no `push_ok` |
| Flags | `-r up -b feat/x`, `--remote`/`--branch` | pushes `feat/x` to `up` | unknown flag → exit 2 |
| Missing remote | `-r nope` | stderr names kind `unknown`; push fails | `push failed`, exit 1 |

</frozen-after-approval>

## Code Map

- `skills/ship/scripts/ship-push.ts` -- reference for flags, stderr wording, fallback order and exit codes 1/2/0.
- `skills/ship/scripts/ship-lib.ts` L73-101 -- `adoToken`/`tryAdoToken` (az args, trimmed stdout, empty on failure) and `adoBearerGitArgs` (the two config pairs, including why `credential.helper` is emptied).
- `skills/ship/src/git.rs` -- `run`/`run_raw` capture stdout; push needs an inherited-stdio runner that returns success or failure, plus an `az` token helper. Keep subprocess code in one place.
- `skills/ship/src/lib.rs` -- `detect_kind`, `Platform`. Pure helpers here (e.g. building the Bearer config pairs) get unit tests.
- `skills/ship/src/main.rs`, `src/detect.rs`, `tests/preflight.rs` -- clap subcommand pattern, BrokenPipe → exit 0, and scratch-repo integration tests isolated from global git config (`GIT_CONFIG_GLOBAL=/dev/null`, `GIT_CONFIG_NOSYSTEM`). Reuse the helpers.
- Tests reach the Azure path with no network: `SHIP_PLATFORM=azure`, a local bare repo as the remote, and a stub `az` script first on `PATH` that prints a known token or exits 1. A `file://` push ignores the header, which is fine: the code path and output are what's under test.
- `_bmad-output/implementation-artifacts/sprint-status.yaml` -- Story 1.3 still `review` though merged (PR #23); set it `done`. Epic 1 → `done`.

## Tasks & Acceptance

**Execution:**
- [x] `skills/ship/src/git.rs` -- add an inherited-stdio git runner, a Bearer push that takes the token without putting it in argv or on disk (per the decision), and `try_ado_token()` -- one subprocess module, reusable by Story 2.2
- [x] `skills/ship/src/push.rs` -- the push flow and stdout/stderr lines above -- mirrors `detect.rs`
- [x] `skills/ship/src/main.rs` -- `push` subcommand with `-r/--remote`, `-b/--branch` -- dispatch only
- [x] `skills/ship/tests/push.rs` -- scratch-repo tests for every matrix row, with the stub `az` -- pins output without bun or network
- [x] `_bmad-output/implementation-artifacts/sprint-status.yaml` -- 1-3 → `done`, epic-1 → `done`

**Acceptance Criteria:**
- Given a matrix row, when `ship push` and `bun scripts/ship-push.ts` run against the same scratch setup, then stdout, the stderr `>>` lines and the exit code match.
- Given the stub token `SECRET-TOKEN-123`, when the Azure tests run, then that string appears in no stdout, stderr or `.git/config`, and the git push command's argv carries no `-c` with the token (check with a unit test on the command builder).
- Given `cargo test` and `cargo clippy --all-targets -- -D warnings`, then both pass, and the detect and preflight tests still pass.

## Implementation Notes

- New `src/push.rs`, `tests/push.rs`; `src/git.rs` gains `try_ado_token`, `bearer_env` (GIT_CONFIG_* env, appends after a caller's own count), `push_args`, `push_with_auth` (shared with Story 2.2). `main.rs` returns an exit code from `run`.
- Parity run (TS reference from the scratchpad `bun install` copy), 8 scenarios, each in its own fresh scratch repo pair: GitHub, Azure logged in, Azure logged out, Bearer rejected once, both pushes rejected, diverged history, `-r up -b other`, unknown remote. All SAME in stdout, `>>`/`push failed` stderr lines and exit code; the token appeared in no stdout, stderr or `.git/config`.
- `ps` during a live push with a stub token: TS shows `git -c credential.helper= -c http.extraHeader=Authorization: Bearer <TOKEN> push …`; Rust shows the token in no process argv.
- Known non-contract differences: clap's `--help` text and unknown-flag wording (exit codes 0 and 2 match).
- After review patches: `validate_target` rejects a `+`/`-`/`:` branch and a `-` remote (exit 2, no push); argv is `push -u -- <remote> <ref>`; header key scoped to the remote's http(s) origin; `GIT_TERMINAL_PROMPT=0` on the Bearer attempt only. Reproduced before the fix: `-b +main` rewrote a bare remote's `main`; after: exit 2, remote head unchanged.
- `git config --get-urlmatch` with the scoped key: applies to `https://dev.azure.com/…` (also with userinfo and mixed-case host), not to `https://github.com/…` or `https://dev.azure.com.evil.io/…`.
- Verified: `cargo test` 47 + 7 + 14 + 17 green on two runs; clippy clean; parity rerun 8/8 SAME.

## Spec Change Log

## Review Triage Log

Pass 1 (blind-hunter BH, edge-case-hunter EC, verification-gap VG).

| # | Finding | Verdict | Evidence | Route |
|---|---|---|---|---|
| 1 | EC1/EC2: `-b +main` force-pushes; leading `-` values parse as git options | high | Reproduced: `ship push -b +main` after an amend rewrote the bare remote's `main`. Frozen Never bans any `+refspec`. Same in TS, but this change owns the contract. | patch |
| 2 | EC4/EC5/BH2: unscoped `http.extraHeader` sends the token to every HTTP endpoint of the push (redirects, lfs, `SHIP_PLATFORM` override on another host) | medium | `bearer_env` sets `http.extraHeader` with no URL scope; git-lfs reads it. Scope to the remote's origin. | patch |
| 3 | BH1/EC9: rejected token → git prompts on the terminal; fallback never runs | medium | `credential.helper` is emptied and stdin inherited; a 401 asks for a username. `GIT_TERMINAL_PROMPT=0` on the Bearer attempt only. | patch |
| 4 | BH3/EC11: doc overstates the token's privacy; hooks inherit it | low | Env is readable by the same user and by hooks; the decision only promised argv/`ps`/disk. Comment fix. | patch |
| 5 | VG1: az argv and exact header value never asserted | medium | Stub ignores args; hook globs `*Bearer*`. A wrong resource id or a trailing `\n` would ship green and silently fall back on real Azure. | patch |
| 6 | BH5: argv acceptance test is tautological | medium | `push_args` never receives the token. My own `ps` check showed no leak, but no test pins it. | patch |
| 7 | VG3/BH4: "az missing" row untested | medium | Every test has a stub `az` first on PATH. Matrix row coverage gap. | patch |
| 8 | VG2/EC10: caller's `GIT_CONFIG_COUNT` never exercised end to end | low | `isolate()` removes it; unit test passes the count directly. Test-only addition. | patch |
| 9 | BH6: never-forces untested on Azure | low | Only the GitHub diverged case exists. Test-only addition. | patch |
| 10 | BH7: TS parity run not recorded | false | Ran this session: all 8 matrix scenarios byte-identical in stdout, `>>` lines and exit code (Implementation Notes). | reject |
| 11 | BH8: sprint `in-progress` vs spec `in-review` | false | Workflow order; step 5 moves sprint to `review`. | reject |
| 12 | BH9: git's "set up to track" line precedes `push_ok=` on stdout | low | Identical in TS (parity run); Story 2.2 parses the last line. | reject |
| 13 | EC3/BH10: detached HEAD pushes `HEAD`; `-b ""` uses current branch | low | Same as TS `currentBranch()` and `if (!branch)`; already deferred from Story 1.1 (branch lookup entry). | defer (carried) |
| 14 | EC6: SSH Azure remote reports `oauth-bearer` | low | Same as TS; header unused over SSH, push still authenticated. | reject |
| 15 | EC7: non-auth Bearer failure triggers a redundant push and auth wording | low | Same as TS; the second push fails the same way and exits 1. Fix needs stderr parsing. | reject |
| 16 | EC8: `az` call has no timeout | low | Same as TS; fix adds a wait loop. | reject |
| 17 | EC10b: non-numeric `GIT_CONFIG_COUNT` silently becomes 0 | low | Malformed caller env; git itself rejects it. | reject |
| 18 | EC12: stdout write error after a landed push exits 1 | false | Failing loudly on an unwritable stdout is correct; BrokenPipe already exits 0 (as Story 1.2 row 15). | reject |
| 19 | BH11: `tests/push.rs` not gated `cfg(unix)` | false | Supported hosts are Linux and macOS only (Story 1.3); no Windows build exists. | reject |

## Verification

**Commands:**
- `cargo test --manifest-path skills/ship/Cargo.toml` -- expected: all green
- `cargo clippy --manifest-path skills/ship/Cargo.toml --all-targets -- -D warnings` -- expected: clean
- parity run against the TS reference (scratchpad `bun install` copy) for each matrix row -- expected: identical stdout, `>>` lines and exit code
