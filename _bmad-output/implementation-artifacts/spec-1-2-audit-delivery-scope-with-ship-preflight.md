---
title: 'Story 1.2: Audit delivery scope with ship preflight'
type: 'feature'
created: '2026-11-08'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: 'd6b91e48772bfd88df9ec5a7277e2d2e74a3f80c'
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
  - '{project-root}/_bmad-output/specs/spec-ship-rust-port/cli-contract.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The scope audit that guards against leaving a changed file out of a PR (`bun scripts/ship-preflight.ts`) still needs bun. The `ship` binary from Story 1.1 has only `detect`.

**Approach:** Add `ship preflight [REMOTE]` to the existing crate, printing the same `key=value` lines and stderr warnings as `ship-preflight.ts`, and port `parsePorcelainStatus` and `scopeAudit` with their test cases.

## Boundaries & Constraints

**Always:** Output keys and order: `branch`, `commits_ahead_of_upstream`, `staged`, `unstaged`, `untracked`, `scope_clean` (`true`/`false`). Commits ahead come from `git log --oneline @{u}..` and are `0` when there is no upstream. Warnings go to stderr with the TS wording: `>> WARNING: N file(s) changed but not staged: a, b`, `>> WARNING: N untracked file(s): …`, and the `>> Confirm these don't belong in this PR before committing (the PR #192 guard).` line when not clean. Exit 0 whenever the branch lookup succeeds (advisory, never blocks). The positional `[REMOTE]` is accepted and ignored, as in TS. `git` through argument arrays only. Reuse `git.rs` and the stdout/BrokenPipe handling from Story 1.1.

**Decision (Barbosa, 2026-11-08): fix the TS trim bug in Rust.** `ship-lib.ts` `sh()` trims the whole porcelain output, so a leading-space first line (` M b.txt`) loses its first character and parses as staged. `ship preflight` parses untrimmed porcelain: one unstaged file reports `staged=0 unstaged=1 scope_clean=false`. This is the one intended difference from the TS output; every other case keeps byte parity. The TS fix ships separately.

**Decision (Barbosa, 2026-11-08, after review): pass `--untracked-files=normal` explicitly.** A `status.showUntrackedFiles=no` config otherwise hides every untracked file and the guard reports clean (review triage row 4). Output on default config is unchanged, so parity holds on every matrix row.

**Never:** No change to `ship detect` output. Do not modify `scripts/*.ts`, `package.json` or `SKILL.md`. No new dependencies. No network calls.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Clean, pushed | upstream set, nothing ahead, clean tree | `commits_ahead_of_upstream=0`, all counts 0, `scope_clean=true`, no stderr warnings | N/A |
| Ahead of upstream | 2 local commits after `@{u}` | `commits_ahead_of_upstream=2` | N/A |
| No upstream | new branch | `commits_ahead_of_upstream=0` | git's own stderr may show; exit 0 |
| Staged only | `M  a`, `A  b` | `staged=2`, `scope_clean=true` | N/A |
| Mixed | staged + unstaged + untracked | each counted, `scope_clean=false`, the three stderr lines | exit 0 |
| Rename | `R  old -> new` | counts once as staged (new path) | N/A |
| Both columns | `MM a` | counted in staged and unstaged | N/A |
| Ignored | `!! x` | not counted | N/A |
| Unstaged first line | only ` M b.txt` changed | `staged=0`, `unstaged=1`, `scope_clean=false`, warnings name `b.txt` (TS prints `staged=1 scope_clean=true`: the fixed bug) | exit 0 |
| Not a git repo | outside a repo | nothing on stdout | error on stderr, non-zero exit |

</frozen-after-approval>

## Code Map

- `skills/ship/scripts/ship-preflight.ts` -- reference: output order, stderr wording, `-h/--help`, ignored `[remote]`.
- `skills/ship/scripts/ship-lib.ts` -- port `parsePorcelainStatus` (L201) and `scopeAudit` (L229); `sh()` (L23) trims stdout, the source of the fixed bug.
- `skills/ship/scripts/ship-lib.test.ts` -- port `parsePorcelainStatus` (L19-64) and `scopeAudit` (L66-97) test groups 1:1.
- `skills/ship/src/git.rs` -- `run()` trims stdout; porcelain must be read untrimmed (trailing newline handling only) to get the fix.
- `skills/ship/src/main.rs`, `src/detect.rs`, `tests/detect.rs` -- Story 1.1 patterns to reuse: clap subcommand, locked stdout + BrokenPipe exit 0, scratch-repo integration tests with golden strings.
- `_bmad-output/implementation-artifacts/sprint-status.yaml` -- Story 1.1 still `review` though merged (PR #21); set it `done` in this change.

## Tasks & Acceptance

**Execution:**
- [x] `skills/ship/src/lib.rs` -- port `PorcelainStatus`, `parse_porcelain_status`, `ScopeAudit`, `scope_audit` with the TS test groups -- pure logic, testable without git
- [x] `skills/ship/src/git.rs` -- add helpers for `log --oneline @{u}..` (allow fail → 0) and `status --porcelain` -- subprocess stays in one module
- [x] `skills/ship/src/preflight.rs` -- print the six lines and stderr warnings -- mirrors `detect.rs`
- [x] `skills/ship/src/main.rs` -- add `preflight [REMOTE]` subcommand -- dispatch only
- [x] `skills/ship/tests/preflight.rs` -- scratch-repo integration tests with golden stdout for the I/O matrix rows -- pins output without bun
- [x] `_bmad-output/implementation-artifacts/sprint-status.yaml` -- Story 1.1 `review` → `done` -- PR #21 merged

**Acceptance Criteria:**
- Given any matrix row, when running `ship preflight` and `bun scripts/ship-preflight.ts` in the same scratch repo, then stdout and exit code are identical, except the "Unstaged first line" row, where Rust reports the file as unstaged.
- Given `ship preflight --help`, then usage prints and exit is 0.
- Given `cargo test` and `cargo clippy --all-targets -- -D warnings`, then both pass and the Story 1.1 detect tests still pass.

## Implementation Notes

- New `src/preflight.rs` and `tests/preflight.rs`; `lib.rs` gains `parse_porcelain_status`/`scope_audit` (13 TS cases ported + first-line and wording tests); `git.rs` splits `run()` into a trimming wrapper over `run_raw()` so porcelain is read untrimmed (the approved fix).
- Stderr warnings always print, even when a stdout write fails; BrokenPipe still exits 0. Test helpers in both integration files isolate git from global/system config and `GIT_DIR`-style env.
- Parity evidence (bun reference from a scratchpad `bun install` copy): 9 matrix rows SAME in stdout, stderr and exit code; `unstaged-first-line` DIFF as decided; not-a-repo both exit 1 with empty stdout; `--help` exits 0 in both.
- Triage row 4 resolved by the principal's follow-up decision: `status_porcelain()` passes `--untracked-files=normal`; `show_untracked_files_no_config_cannot_hide_new_files` fails without the flag and passes with it; parity unchanged (9 SAME, 1 intended DIFF). Collapsed untracked directories (`?? dir/`) stay as TS and remain deferred.
- Verified after review patches: `cargo test` 40 unit + 7 detect + 13 preflight, green on 3 consecutive runs; `cargo clippy --all-targets -D warnings` clean; closed-pipe repro prints the untracked warning and exits 0.

## Spec Change Log

## Review Triage Log

Pass 1 (blind-hunter BH, edge-case-hunter EC, verification-gap VG). Parity with `ship-preflight.ts` is frozen apart from the trim-bug fix, so other TS-inherited behavior is deferred.

| # | Finding | Verdict | Evidence | Route |
|---|---|---|---|---|
| 1 | VG-other/EC10: a closed stdout returns before the stderr scope warnings print | medium | Reproduced: untracked `u`, `(sleep; ship preflight) \| true` → rc=0, no `>> WARNING`. TS `console.error` is independent of stdout. Introduced by this change; the guard goes silent. | patch |
| 2 | VG1: no preflight test closes stdout early | medium | Only `tests/detect.rs` has the closed-pipe test. Same root as 1: the patch adds it. | patch (with 1) |
| 3 | BH7/EC11/EC12: test helpers inherit global/system git config and `GIT_DIR`-style env | low | `git()` and `preflight()` in `tests/preflight.rs` set no `GIT_CONFIG_GLOBAL`/`NOSYSTEM`; a global `showUntrackedFiles=no` or pre-push hook breaks goldens elsewhere. New code; env-only fix. | patch |
| 4 | BH3/EC1: `status.showUntrackedFiles=no` hides untracked files → `scope_clean=true` | high | Reproduced: porcelain empty with the config set. Plain `git status --porcelain`, identical in TS. Pre-existing; changing the flag set is outside the approved parity exception. | defer |
| 5 | EC2/BH9: untracked directories collapse to one `?? dir/` entry | low | Default `-unormal`, same as TS. Pre-existing. | defer (with 4) |
| 6 | BH4/EC3/VG-other: failed `git status` reads as a clean tree | medium | `unwrap_or_default()` mirrors TS `allowFail`. Pre-existing fail-open. | defer |
| 7 | BH2/EC4/EC5/EC6: C-quoted paths, arrow inside quoted rename, unmerged `UU`/`AA` handling | low | Same parser as TS; unmerged still count as unclean. Pre-existing. `-z` parsing is the fix. | defer |
| 8 | BH1/BH8/EC7/EC8: no-upstream reports 0 ahead; `log --oneline` count inflatable by `log.showSignature` | medium | Same command and count as TS. Pre-existing. | defer |
| 9 | EC9: unborn branch fails before any output | low | Same `rev-parse --abbrev-ref` as TS; already deferred from Story 1.1 (branch lookup entry). | defer (carried) |
| 10 | BH5: AC1 parity evidence not recorded | false | Parity run (9 SAME, 1 expected DIFF, norepo and `--help` matching) is recorded in Implementation Notes at completion; fix is a spec edit. | reject |
| 11 | BH6: sprint says in-progress while spec says in-review; spec file untracked | false | Step 5 moves sprint-status to `review` and commits the spec with the code; workflow order, not a defect. | reject |
| 12 | BH10: `ScopeAudit::warning` unused by the binary | false | Design Notes require porting it for helper parity. | reject |
| 13 | BH9-test: no-upstream test leaves git's `fatal:` stderr unasserted | low | Spec allows git's stderr there; pinning git's wording adds brittleness. Rarely matters. | reject |
| 14 | EC13: clap rejects extra positionals where TS ignores them | low | Same as Story 1.1 row 17; SKILL.md never passes extras. | reject |
| 15 | EC14: non-BrokenPipe write errors (ENOSPC) exit 1 | false | Failing loudly when stdout cannot be written is correct; "advisory" means scope findings never block. | reject |

## Design Notes

TS `scopeAudit` also builds a one-line `warning` string that `ship-preflight.ts` never prints (it prints its own three stderr lines). Port the field and its tests for parity of the helper; the binary prints the script's lines.

## Verification

**Commands:**
- `cargo test --manifest-path skills/ship/Cargo.toml` -- expected: all unit and integration tests pass
- `cargo clippy --manifest-path skills/ship/Cargo.toml --all-targets -- -D warnings` -- expected: clean
- parity script against the scratchpad TS reference (`bun install` copy) for every matrix row -- expected: identical stdout and exit code, apart from the documented difference
