---
title: 'Story 2.2: Save a checkpoint with ship snapshot'
type: 'feature'
created: '2026-11-08'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: 'e44f9ddd9135ebf8fdc11e976df185b559e1b664'
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-2-context.md'
  - '{project-root}/_bmad-output/specs/spec-ship-rust-port/cli-contract.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Saving a return point before risky work still means running `bun scripts/ship-snapshot.ts`, so it needs bun.

**Approach:** Add `ship snapshot [-m PARA]... [--daily] [--name TAG] [--push]` to the crate with the TS behavior: an annotated, self-describing tag on HEAD, refused if it already exists, and optionally pushed through Story 2.1's `git::push_with_auth`.

## Boundaries & Constraints

**Always:**
- **Preconditions:** `git rev-parse --short HEAD` must succeed. If it fails, print `not a git repo, or no commits yet — nothing to snapshot` and exit 2. The branch comes from the existing `current_branch`, as in TS.
- **Tag name:** `--name` wins. Otherwise the name is `date +v%Y.%m.%d-%H%M`, or `date +v%Y.%m.%d` with `--daily`, run as a `date` subprocess so the local TZ applies exactly as in TS. No new crate.
- **Existing tag:** if `git rev-parse -q --verify refs/tags/<name>` succeeds, print `tag '<name>' already exists. Use --name <other>, or drop --daily for minute granularity.` and exit 3. The tag is not moved.
- **Tag message:** `git tag -a <name> -m "Snapshot <name> — <branch> @ <shorthash>"`, then one `-m` per `--message`/`-m` in the given order, each passed verbatim through the argument array.
- **Stderr:** `>> created annotated tag <name> -> <shorthash> (<branch>)`.
- **`--push`:** the remote is `origin`. Stderr prints `>> pushing tag <name> -> origin (<kind>)`. The push goes through `git::push_with_auth(kind, "origin", &[name])`, the same token handling and fallback as `ship push`. If it fails, print `tag '<name>' created locally, but push failed`, exit 1, and keep the local tag.
- **Stdout, in this order:** `tag=`, `commit=` (short hash), `branch=`, `pushed=`.
- **Errors:** an unknown flag exits 2 and `--help` exits 0. The stdout/BrokenPipe handling is reused.

**Decision (Barbosa, 2026-11-08): `pushed=` keeps the TS values.** `pushed=no` without `--push`; `pushed=yes-oauth-bearer` when the Bearer push succeeded; `pushed=yes` when the plain push succeeded. This supersedes the epics AC's `false`/`true` wording.

**Never:** Never move, delete or overwrite a tag. No `-f` on `git tag`, and no force or `+refspec` on the push. Never put the token in argv, output or on disk (Story 2.1's guarantees carry over). No change to `push`, `detect`, `preflight`, `scripts/*.ts`, `package.json` or `SKILL.md`. No new dependencies.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Default name | `-m why -m verified` on `main` | tag matches `^v\d{4}\.\d{2}\.\d{2}-\d{4}$` on HEAD; message paragraphs are subject, `why`, `verified`; `pushed=no` | N/A |
| Daily | `--daily` | name matches `^v\d{4}\.\d{2}\.\d{2}$` | N/A |
| Exact name | `--name pre-migration` | tag `pre-migration` | N/A |
| Collision | tag already exists | nothing created; existing tag still points where it did | exit 3, message above |
| No message | no `-m` | annotated tag with the subject only | N/A |
| Not a repo / no commits | empty repo or outside one | nothing on stdout | exit 2 |
| Push | `--push`, origin reachable (Azure stub token, or GitHub) | tag on the remote; `pushed=yes-oauth-bearer` (Azure stub) or `pushed=yes` (GitHub) | N/A |
| Push fails | `--push`, origin rejects | local tag kept | exit 1, "created locally, but push failed" |
| Bad name | `--name +v1`, `--name -x`, `--name a:b`, or a name `git check-ref-format` rejects | nothing created or pushed | exit 2, clear message |

</frozen-after-approval>

## Code Map

- `skills/ship/scripts/ship-snapshot.ts` -- reference for the flow, messages and exit codes 1/2/3. `--annotate-note` appears in its header comment but is not implemented: do not port it.
- `skills/ship/src/git.rs` -- reuse `run`/`run_raw`, `current_branch`, `remote_url` and `push_with_auth`. `push -u` on a tag writes no branch config (checked with git 2.53), so the shared `push -u -- origin <tag>` is safe.
- `skills/ship/src/push.rs` -- `validate_target` already rejects `+`/`-`/`:`. Reuse it or share it for the tag name, and add `git check-ref-format refs/tags/<name>`. A `+`/`-` name passes check-ref-format (checked), so both checks are needed.
- **Known stderr difference on `--push`:** the shared `push_with_auth` prints `>> could not mint an az token…` when `az` is logged out, and the TS snapshot prints nothing there. Keep the shared notice; it is accepted and recorded (stdout and exit codes are unaffected).
- `skills/ship/src/main.rs`, `tests/push.rs` -- clap pattern and the scratch-repo, bare-remote and stub-`az` helpers to reuse. The tests must give `git tag` an identity (`-c user.name/user.email` or env) and `tag.gpgSign=false` in the isolated config.
- `_bmad-output/implementation-artifacts/sprint-status.yaml` -- Story 2.1 still `review` though merged (PR #24); set it `done`.

## Tasks & Acceptance

**Execution:**
- [x] `skills/ship/src/snapshot.rs` -- the snapshot flow and output above -- mirrors `push.rs`
- [x] `skills/ship/src/main.rs` -- `snapshot` subcommand: repeatable `-m/--message`, `--daily`, `--name`, `--push` -- dispatch only
- [x] `skills/ship/src/git.rs` (or `push.rs`) -- share the name/branch validation; add tag helpers (exists, create) -- one subprocess module
- [x] `skills/ship/tests/snapshot.rs` -- scratch-repo tests for every matrix row, with tag-message assertions via `git cat-file -p <tag>` -- pins behavior without bun or network
- [x] `_bmad-output/implementation-artifacts/sprint-status.yaml` -- 2-1 → `done`

**Acceptance Criteria:**
- Given a matrix row run with `--name` (or a fixed clock where the name is dated), when `ship snapshot` and `bun scripts/ship-snapshot.ts` run in identical scratch repos, then stdout, the `>>` lines and the exit code match, except for the recorded `could not mint` notice.
- Given `--push` on Azure with the stub token, then the token appears in no stdout, stderr or `.git/config`.
- Given `cargo test` and `cargo clippy --all-targets -- -D warnings`, then both pass, and every existing test still passes.

## Implementation Notes

- New `src/snapshot.rs`, `tests/snapshot.rs`; `git.rs` gains `short_head`, `date`, `valid_tag_name`, `tag_exists`, `create_tag`/`tag_args`; `push.rs` exposes `is_unsafe_ref`, shared with the tag-name check. `--push` sends `refs/tags/<name>` through Story 2.1's `push_with_auth`.
- Parity run against `ship-snapshot.ts` (scratchpad `bun install` copy), 8 scenarios in fresh repo pairs, comparing stdout, `>>` lines, exit code, tag body and remote tag state: named with two `-m`, no message, collision (3), no commits (2), GitHub push, Azure push with stub token, Azure logged out, push rejected (1). 7 SAME; Azure logged out differs only by the recorded `could not mint` notice. No token in any stdout, stderr or `.git/config`.
- Review fixes, verified after patching: `--name @ --push` now leaves only `refs/tags/@` on the remote and sets no upstream (before: pushed `main`, no tag); `HEAD` is refused with exit 2; tests added for `--name ""`, `--name -x` as separate args, the `--daily` collision, `@`, and a tag sharing a branch name.
- Verified: `cargo test` 50 + 7 + 14 + 17 + 18 green on two runs; clippy `-D warnings` clean.

## Spec Change Log

## Review Triage Log

Pass 1 (blind-hunter BH, edge-case-hunter EC, verification-gap VG).

| # | Finding | Verdict | Evidence | Route |
|---|---|---|---|---|
| 1 | EC2/BH1/EC1/VG-other: bare tag name in the push; `--name @` pushes the branch, a same-named branch makes the push ambiguous | high | Reproduced: `snapshot --name @ --push` left the remote with only `refs/heads/main` (upstream set), no tag, `pushed=yes`. Fix: push `refs/tags/<name>`. | patch |
| 2 | EC3: `--name HEAD` passes validation, `git tag` refuses → exit 1 generic | low | Direct one-line reject in `validate_name`. | patch |
| 3 | VG1/BH3: `--name ""` → dated name, unpinned | low | Matches TS `if (!name)`; test-only. | patch |
| 4 | VG2: `allow_hyphen_values` on `--name` unexercised | low | Bad-name loop uses only `--name=<v>`. Test-only. | patch |
| 5 | BH8: dated-name collision untested | low | Exit-3 tests use only `--name`. Test-only. | patch |
| 6 | EC4: a `-m` paragraph starting with `#` is silently dropped | medium | Reproduced: `-m '#123 fixed' -m keep` → body has only the subject and `keep`. git's default `--cleanup=strip`; identical in TS `git tag -a -m`. Changing it alters tag bodies vs TS, so it needs the principal's call like the 1.2 trim fix. | defer |
| 7 | BH2/EC5: exit 1 covers both push failure and tag-creation failure; create race → 1 not 3 | low | Same as TS; race needs two snapshots in one minute. Fix adds branches. | reject |
| 8 | BH6: detached HEAD gives `branch=HEAD` | low | Same as TS; already deferred from Story 1.1 (branch lookup). | defer (carried) |
| 9 | BH7/EC6: tests read `%(contents)`, not `cat-file -p` | low | The paragraphs are the contract and are asserted; tagger/object headers are git's. | reject |
| 10 | BH4/VG-other: parity evidence missing | false | Ran this session: 8 scenarios, 7 SAME, 1 the recorded `could not mint` notice (Implementation Notes). | reject |
| 11 | BH5: spec untracked; status mismatch | false | Workflow order: step 5 commits the spec and moves sprint to `review`. | reject |
| 12 | BH9: `is_unsafe_ref` lives in `push.rs`; SKILL.md not updated | low | Placement is cosmetic; SKILL.md cutover is Story 5.2 by plan. | reject |

## Verification

**Commands:**
- `cargo test --manifest-path skills/ship/Cargo.toml` -- expected: all green
- `cargo clippy --manifest-path skills/ship/Cargo.toml --all-targets -- -D warnings` -- expected: clean
- parity run against the TS reference for each matrix row -- expected: identical stdout, `>>` lines and exit code, apart from the recorded notice
