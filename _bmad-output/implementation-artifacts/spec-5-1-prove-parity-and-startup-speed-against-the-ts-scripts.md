---
title: 'Prove parity and startup speed against the TS scripts'
type: 'feature'
created: '2026-11-12'
status: 'awaiting-operator'
baseline_revision: 'ccadd3810438da2f5cf5c7fc40ac20804863199c'
review_loop_iteration: 0
followup_review_recommended: true
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-5-context.md'
  - '{project-root}/_bmad-output/specs/spec-ship-rust-port/cli-contract.md'
warnings: [oversized]
deferred:
  - summary: >-
      An interrupted run (Ctrl-C, SIGKILL) skips cleanup, so the scratch dir and, under --live, real draft PRs, branches and labels can be left behind.
    evidence: |-
      Cleanup runs only on normal return or early error return; ScratchRoot::drop does not run on a signal, and nothing traps SIGINT. Verified by reading execute() and ScratchRoot.
    location: >-
      skills/ship/examples/parity.rs (execute, ScratchRoot)
    severity: medium
  - summary: >-
      The push-to-sink guard (assert_pushes_to_sink / pushInsteadOf reroute) has no automated test.
    evidence: |-
      Only exercised by real harness runs (2026-11-12, both platforms). A test needs local git, which the spec's pure-logic test rule excludes; a regression could push hermetic branches to the real remote.
    location: >-
      skills/ship/examples/parity.rs (Scratch::assert_pushes_to_sink, make_scratch)
    severity: medium
  - summary: >-
      fingerprint() (source-clone-unchanged check) has no test proving a new tag, branch or config key changes it.
    evidence: |-
      Only errors_and_hygiene_failures_fail_the_run checks a hand-set flag; needs local git like the item above.
    location: >-
      skills/ship/examples/parity.rs (fingerprint)
    severity: low
  - summary: >-
      check_source/validate branches (not a repo, no origin, wrong platform, binary or scripts missing) are untested.
    evidence: |-
      missing_inputs_are_usage_errors covers parse_args only; the rest spawns git and bun.
    location: >-
      skills/ship/examples/parity.rs (validate, check_source)
    severity: low
  - summary: >-
      Story 5.2 must decide the harness's fate once scripts/*.ts are deleted (delete examples/parity.rs or keep as frozen evidence).
    evidence: |-
      After cutover the --scripts default disappears and validate always fails; the example stays compiled in CI.
    location: >-
      skills/ship/examples/parity.rs, skills/ship/PARITY.md
    severity: low
operator_actions:
  - "Log in to az with an account authorized on the Azure DevOps org, then rerun `cargo run --release --example parity -- --github <repo> --azure <azure clone> --azure-pr <id>` from skills/ship and confirm `tag --list <id> (live read)` is `same`."
  - "Approve and run the `--live` tier once against the GitHub and the Azure clone (it opens throwaway draft PRs), and confirm every `live …` case is `same` with no LEFTOVER lines."
  - "Run the parity harness on a macOS arm64 host and confirm the binary beats bun on every timing row."
  - "Run `ship open <pr url> --profile <email>` without --dry-run on WSL and on macOS and confirm the PR opens in the profile signed in with that email."
  - "Confirm or change the 50 ms detect/preflight startup threshold (NFR9), adopted as an unconfirmed default on 2026-11-08."
---

<intent-contract>

## Intent

**Problem:** Cutover (Story 5.2) deletes the TS scripts, but nothing yet proves the `ship` binary prints the same `key=value` lines and exit codes as each `bun scripts/ship-*.ts`, or that it starts faster (NFR9).

**Approach:** Add a Rust-only parity harness (a cargo example) that takes one Azure clone and one GitHub clone, builds disposable scratch clones whose pushes land in a local bare sink, runs every subcommand through both implementations side by side, diffs `key=value` stdout and exit codes, times median startup per subcommand, and exits non-zero on any difference or speed miss. An opt-in `--live` tier covers the write paths that need a real remote (throwaway draft PRs, tag add/remove, cleanup).

## Boundaries & Constraints

**Always:** Rust std only plus existing crate deps; spawn `bun`, `git`, the binary, and (live cleanup only) `gh`/`az` from argument arrays, never a shell string. The source clones passed in are never written to: all work happens in scratch clones under the system temp dir, removed at the end. Compare only stdout lines matching `^[a-z_]+=` plus the exit code; stderr is human text and is ignored. Both implementations run the same case in identical scratch state (same branch name, same commits built with a fixed author/committer identity and date). Reports and the committed doc carry case labels, verdicts, exit codes and timings only — never stdout values (Azure org/project/repo names must not reach this public repo). Unit tests of the harness's pure logic run under plain `cargo test` with no bun, network or clones.

**Never:** npm, npx or Python anywhere (NFR8). No writes to a real remote outside `--live`. No change to `src/` behavior unless the harness exposes a real parity difference on a contract case. Do not compare cases outside the contract that a story already recorded as an accepted deviation (dash-prefixed positional remote, e.g. `detect --bogus`, Story 1-1 finding 17).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| All same, fast | both impls agree on every case; binary faster | case table all `same`, timing table all `pass`, exit 0 | none |
| Key differs | one case prints `scope_clean=true` vs `false` | case marked `DIFF`, both key lists printed to the console, harness exits 1 | continue remaining cases |
| Exit differs | TS exits 1, binary 2 | `DIFF (exit 1 vs 2)`, exit 1 | continue |
| Volatile ids | live `pr` prints `pr_number=41` vs `42` | values of `pr_url`, `pr_id`, `pr_number`, `work_item` normalized (digit runs → `<N>`) before compare: `same` | none |
| Slow binary | binary median ≥ TS median, or `detect`/`preflight` ≥ 50 ms on Linux | timing row `FAIL`, exit 1 | 50 ms rule skipped (noted) off Linux |
| Missing input | `--azure` or `--github` path absent / not a git repo / binary not built | usage error naming the missing piece, exit 2 | no scratch dirs left behind |
| Optional live read | `--github-pr`/`--azure-pr` not given | `tag --list` case reported `skipped`, not counted as pass | none |

</intent-contract>

## Code Map

- `skills/ship/scripts/ship-{detect,preflight,push,snapshot,tag,pr,open}.ts` -- reference implementations, run as `bun <path> <args>`; all accept `--help` (exit 0) except `ship-detect.ts`, which treats any arg as the remote.
- `skills/ship/src/main.rs` -- clap CLI of the binary; `cargo build --release` produces `skills/ship/target/release/ship`.
- `skills/ship/scripts/ship-lib.ts:59` / `src/lib.rs` `detect_kind` -- `SHIP_PLATFORM` only applies when the URL is unknown.
- `skills/ship/scripts/ship-push.ts`, `ship-snapshot.ts` -- Azure kind pushes with an az Bearer `http.extraHeader` + empty `credential.helper` first; harmless over a local sink, so `push_ok=oauth-bearer` is reachable hermetically when `az` can mint a token.
- `skills/ship/Cargo.toml` -- add the `[[example]]` target; no new dependencies.
- `.github/workflows/ship-rust.yml` -- CI runs `cargo test --locked` and clippy `--all-targets -D warnings` with no bun, so example tests must stay pure.
- `skills/ship/DISTRIBUTION.md` -- style reference for the new doc.
- Probe evidence (2026-11-12, this repo): `detect`, `preflight`, `tag 35`, `tag --pr 35 --list`, `open --list-profiles`, `open <url> --dry-run`, and bad-flag exits already match; the current az identity gets 302 from the Azure DevOps org, so live Azure reads need an operator login.

## Tasks & Acceptance

**Execution:**
- `skills/ship/examples/parity.rs` -- implement the harness: flags `--azure <clone>`, `--github <clone>`, `--azure-pr <id>`, `--github-pr <id>`, `--open-profile <email>`, `--runs <n>` (default 15), `--report <file>`, `--live`, `--ship <bin>` (default `target/release/ship`), `--scripts <dir>` (default `scripts/`). Per platform and per impl build a scratch clone of the given clone with origin set back to the real URL, a throwaway branch `ship-parity-<nonce>`, and `url.<sink>.pushInsteadOf=<real url>`. Hermetic cases: detect; detect with `SHIP_PLATFORM` set; preflight clean; preflight after a fixed-date commit plus one modified and one untracked file; push; preflight after push; snapshot `--name` with `-m`; same snapshot again (exit 3); snapshot `--name` other `--push`; push/snapshot unknown flag; pr without `--title`; `tag` without id. Live reads: `tag --list <id>` when an id is given. Host-level: `open --list-profiles`, `open <url> --dry-run [--profile]`. Timing: median of `--runs` runs per impl for `detect`, `preflight` (real runs in the scratch clone) and `push|pr|tag|snapshot|open --help`, one warm-up run discarded. `--live`: push `ship-parity-<nonce>-ts`/`-rs` to the real remote, `pr --draft --title "chore: ship parity check (throwaway)" --no-create-work-item`, `tag <id> --add ship-parity`, `--remove ship-parity`, `--list`, then best-effort cleanup (GitHub `gh pr close --delete-branch`; Azure abandon via `az repos pr update --status abandoned` and `git push --delete`), printing anything it could not clean. Print the case and timing tables; write them as markdown to `--report`; exit 0 only when every compared case is `same` and every timing row passes. Pure logic (kv parsing, normalization, comparison, median, pass rules, report rendering) lives in functions with `#[cfg(test)]` tests covering the I/O matrix rows.
- `skills/ship/Cargo.toml` -- add `[[example]] name = "parity"`, `test = true` so `cargo test` runs its unit tests.
- `skills/ship/PARITY.md` -- how to run, what each tier covers, the latest recorded agent run (case counts and timing table, no stdout values), and the operator checklist: live Azure reads with an authorized login, the `--live` tier on both repos, a macOS run, and real-launch checks of `ship open` on WSL and macOS (Epic 4 retro item 4).

**Acceptance Criteria:**
- Given a GitHub clone and an Azure clone, when `cargo run --release --example parity -- --azure <a> --github <g> --github-pr <n>` runs on Linux/WSL2, then every hermetic, host-level and supplied live-read case reports `same` and the harness exits 0.
- Given the same run, when timing completes, then each subcommand row shows the binary median below the TS median and `detect`/`preflight` binary medians under 50 ms, and the markdown report holds both tables.
- Given the source clones, when the harness finishes (pass or fail), then their `git status`, branches, tags and config are unchanged and no scratch directory remains.
- Given CI with no bun, when `cargo test --locked` and `cargo clippy --all-targets -- -D warnings` run, then both pass, including the harness unit tests.
- Given the harness source and `PARITY.md`, when searched for `npm`, `npx` or `python` invocations, then there are none (NFR8).

## Spec Change Log

## Review Triage Log

### 2026-11-12 — Review pass
- verdicts: 32 findings — high 0, medium 11, low 19, false 2, maybe-false 0
- findings:
  - `[medium]` `[patch]` Blind: harness added an "accepted deviation" verdict the spec forbids (recorded deviations are not compared) — removed the verdict; the ` M`-first preflight tree is built but not compared, the staged-first case still is; PARITY.md "Not compared" section.
  - `[medium]` `[patch]` Blind: live leftovers never fail the run — `overall_pass` now requires `leftovers == 0`; test `live_leftovers_fail_the_run`.
  - `[low]` `[reject]` Blind: a repo subdirectory passes validation and fails later with exit 1 — still fails loudly, nothing written to the source; guard adds complexity for a rare input.
  - `[medium]` `[patch]` Blind: harness sent the az token in an unscoped `http.extraHeader` — now reuses `ship::git::bearer_env` + `extra_header_key(url)`.
  - `[medium]` `[patch]` Blind: live Azure PR could notify `SHIP_ADO_DEFAULT_REVIEWER` — live `pr` passes `--no-reviewer`.
  - `[low]` `[reject]` Blind: only `SHIP_PLATFORM` exercised among env vars — both sides inherit the same env; adding cases is new scope with no shown divergence.
  - `[low]` `[patch]` Blind: work-item/reviewer/tag/related/completionOptions `pr` paths never compared, even live — documented the gap in PARITY.md (`--live` section); Story 5.2's full ship run covers them.
  - `[low]` `[reject]` Blind: no `detect <remote>` URL-variety cases — URL classification is covered by the Rust unit tests ported from ship-lib.test.ts; extra cases are new scope.
  - `[false]` `[reject]` Blind: `open` cases prove nothing on a host with no profiles — this host has signed-in profiles; the recorded run compares `--list-profiles` and `--profile <email>` with real data.
  - `[low]` `[reject]` Blind: negative check not reproducible — DIFF detection is covered by unit tests (`a_differing_value_is_a_diff_and_fails_the_run`, `tag_list_label_lines_are_compared`).
  - `[medium]` `[patch]` Blind: stale binary only warned (top-level src only) — now `check_fresh` fails the run, scanning src/ recursively.
  - `[low]` `[defer]` Blind: harness fate after Story 5.2 deletes the TS scripts — deferred to 5.2.
  - `[low]` `[patch]` Blind: scratch root world-readable — created with mode 0700.
  - `[low]` `[patch]` Blind: timing only on GitHub clone; 50 ms never confirmed — added operator action to confirm the threshold; Azure timing rejected (startup does not depend on the remote).
  - `[low]` `[patch]` Blind: DIFF values and report share stdout — PARITY.md now says to use `--report`, not a redirect.
  - `[medium]` `[patch]` Edge: pipe not collected within grace returned empty stdout (false `same`) — now an error → ERROR verdict.
  - `[medium]` `[defer]` Edge: Ctrl-C / panic=abort skips cleanup (scratch dir, live remote objects) — deferred; needs signal handling.
  - `[low]` `[patch]` Edge: operator's global hooks ran during `git clone` — clone now runs with `-c core.hooksPath=<empty dir>`.
  - `[low]` `[patch]` Edge: global `tag.forceSignAnnotated` could hang snapshot — pinned false in scratch clones.
  - `[medium]` `[patch]` Edge: global `push.followTags` could carry snapshot tags to the real remote in `--live` — pinned false.
  - `[low]` `[patch]` Edge: label list truncated at 1000 could delete a pre-existing label — `gh_labels` refuses to compare a full page.
  - `[low]` `[patch]` Edge: unparseable GitHub owner/repo fell into the Azure abandon arm and skipped label checks silently — explicit GitHub error arm plus a LEFTOVER.
  - `[low]` `[reject]` Edge: subdirectory input (duplicate of the Blind finding) — same reasoning.
  - `[low]` `[reject]` Edge: `--report` inside a source clone — operator-chosen path; doc already says to keep it outside.
  - `[low]` `[patch]` Edge: raw multi-line git stderr in the live-setup ERROR cell — report now says "live setup failed (see console)".
  - `[medium]` `[patch]` Edge: accepted-deviation claim vs spec (same root as the first Blind finding) — fixed by the same removal.
  - `[low]` `[patch]` Edge: PARITY.md claimed global config cannot affect results — fixed by the config pins and reworded.
  - `[medium]` `[patch]` VG: `tag --list` cases never compared label names — `parse_with_bare_lines` for `tag … --list`; test `tag_list_label_lines_are_compared`.
  - `[medium]` `[defer]` VG: push-to-sink guard untested — needs local git, outside the spec's pure-test rule; deferred.
  - `[low]` `[defer]` VG: `fingerprint` untested — deferred with the above.
  - `[low]` `[defer]` VG: missing-input test covers parsing only — deferred.
  - `[false]` `[reject]` Intent: awaiting-operator frontmatter / operator_actions missing and run proof is prose only — the audit ran before finalization; frontmatter now carries them, and the parent reran the harness itself (exit 0) after patches.

## Design Notes

Scratch clones keep the real remote URL so detection, Azure coordinate parsing and the Bearer branch all behave as on a real clone, while `pushInsteadOf` reroutes only pushes to a local bare repo: `git remote get-url` ignores `pushInsteadOf`, so both implementations still see the real URL. Each implementation gets its own clone and sink so a push or tag by one never changes the state the other sees. `--help` timing measures interpreter start plus module load for bun (imports are hoisted) versus process start for the binary — the honest startup comparison for subcommands that otherwise need network.

## Verification

**Commands:**
- `cd skills/ship && cargo test --locked` -- expected: all tests pass, including `parity` example tests
- `cd skills/ship && cargo clippy --all-targets -- -D warnings` -- expected: clean
- `cd skills/ship && cargo build --release && cargo run --release --example parity -- --github <this repo> --azure <an Azure clone> --github-pr 35 --report <scratch>/parity.md` -- expected: exit 0, no DIFF, all timing rows pass

## Auto Run Result

Status: awaiting-operator

**Summary.** Added a Rust-only parity harness (`cargo run --release --example parity`) that runs every `ship` subcommand through `bun scripts/ship-*.ts` and the binary side by side in disposable scratch clones (pushes rerouted to a local bare sink), diffs `key=value` stdout (plus label lines for `tag --list`) and exit codes, times median startup per subcommand, and exits non-zero on any DIFF, ERROR, timing miss, leftover or hygiene failure. An opt-in `--live` tier covers draft PRs and tag add/remove/list on the real remotes with cleanup.

**Files changed**
- `skills/ship/examples/parity.rs` — the harness (new), with 18 pure-logic unit tests.
- `skills/ship/Cargo.toml` — `[[example]] parity`, `test = true`; no new dependencies.
- `skills/ship/PARITY.md` — how to run, tiers, safety, what is not compared, latest recorded run, operator checklist (new).
- `_bmad-output/implementation-artifacts/epic-5-context.md` — compiled Epic 5 context (new).

**Review.** 32 findings: 20 patched (medium 9 entries incl. one duplicate row, low 11), 5 deferred (frontmatter `deferred`), 7 rejected (subdirectory input ×2: fails loudly anyway; env-var breadth, URL-variety cases, negative-check reproducibility, report-path-in-source: new scope or already covered; `open` host-dependence and intent-audit finalization: false). Patched by verdict: medium 9, low 11.

**Follow-up review recommended: true.** Two or more medium entries were patched on a first pass. Named unverified risk: the patched `--live` paths (scoped Bearer env for `ls-remote`/`push --delete`, `--no-reviewer`, followTags pin, label truncation guard, leftover-fails-run) have never executed against a real remote.

**Verification**
- `cargo test --locked` — 344 passed, 0 failed (includes the 18 harness tests).
- `cargo clippy --locked --all-targets -- -D warnings` — clean.
- `cargo run --release --example parity -- --github <this repo> --azure <Azure Repos clone> --github-pr 35 --open-profile <email> --report …` on Linux/WSL2 after the patches — exit 0: 32 same, 0 DIFF, 1 skipped (no `--azure-pr`), 0 ERROR; binary faster on all 7 rows; `detect` 11.6 ms and `preflight` 27.4 ms medians (TS ~280–297 ms); source clones unchanged; scratch dir removed.
- No npm/npx/Python in the harness or doc.

**Operator actions owed** (frontmatter `operator_actions`): authorized live Azure `tag --list` read; `--live` tier on both repos; macOS run; real `ship open` launches on WSL and macOS; confirm the 50 ms threshold.

**Residual risks.** Interrupted runs skip cleanup (deferred). Push-to-sink guard and source fingerprint have no automated test (deferred). `pr` work-item/reviewer/tag/completionOptions paths are compared by neither tier; Story 5.2's full ship run is their end-to-end check.
