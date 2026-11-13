---
epic: 4
date: 2026-11-12
verdict: accepted-with-open-items
criteria: declared
headless: false
---

# Epic 4 Retrospective: Open a PR in the right browser profile

## Epic summary

- **Epic:** Epic 4 — Open a PR in the right browser profile (`FR11` / `CAP-6`)
- **Diff range:** `79a51b26baaaa2204870be8456efa2d548e87483^..874b0fef482e78d920d5d6808534c78f99c4d78b` (baseline `9ed209af063a0288d2c86cc632af8b967368a6d6` → `874b0fef482e78d920d5d6808534c78f99c4d78b`; 4 commits: 2 feature commits + 2 PR merge commits, `merges_measured: 2 / 2`)
- **Stories completed:**
  - `4-1-resolve-an-email-to-a-browser-profile` (`done` — commit `79a51b2`, merged in PR #34 `7031ea0`)
  - `4-2-launch-the-pr-in-the-chosen-profile` (`done` — commit `d08ac6a`, merged in PR #35 `874b0fe`; `sprint-status.yaml` synced from `review` → `done` with operator confirmation prior to Phase 1)
- **Pending stories:** None (`pending_stories: []`)
- **Evidence inventory:**
  - **Available:**
    - Epic & contract specs: `_bmad-output/planning-artifacts/epics.md` (lines 278–309), `_bmad-output/implementation-artifacts/epic-4-context.md`, `_bmad-output/specs/spec-ship-rust-port/SPEC.md` (`CAP-6`), `_bmad-output/specs/spec-ship-rust-port/cli-contract.md`
    - Story specs: `spec-4-1-resolve-an-email-to-a-browser-profile.md`, `spec-4-2-launch-the-pr-in-the-chosen-profile.md`
    - Reference implementation: `skills/ship/scripts/ship-open.ts`
    - Git diff & commit attribution via `git_evidence.py`
    - Sprint tracking & deferred ledger: `sprint-status.yaml`, `deferred-work.md`
  - **Missing / narrowed scope:**
    - **Session logs:** Raw coding-CLI transcripts for Stories 4.1 and 4.2 are not stored in the repository (`.bmad-loop/runs/` is gitignored and empty in this worktree); process-lesson analysis relies on the recorded `Implementation Notes` and `Review Triage Log` sections in `spec-4-1` and `spec-4-2` plus worktree hygiene evidence (e.g., an orphan nested `skills/ship/.git` directory dated 2026-11-10 removed with operator confirmation before Phase 1).
    - **Prior retrospectives:** None (`epic-1`, `epic-2`, and `epic-3` retrospectives remain `optional`).

## Findings

### Aggregate views

- **F1. Spec reconciliation: launch wording is still stale in the contract and the epic.** `epic-4-context.md` ("Launch mechanics") records the deliberate deviation from `cmd.exe start` / `open -a` and says to "have the contract/epics wording corrected rather than regress". Neither was corrected: `_bmad-output/planning-artifacts/epics.md:306` still says WSL launches through `cmd.exe start` and macOS through `open -a`, and `_bmad-output/specs/spec-ship-rust-port/cli-contract.md:39` says the same. The as-built (`skills/ship/src/open.rs:299-345`) uses `powershell.exe -NoProfile -Command Start-Process …` on WSL and `open -na … --args` on macOS, matching `ship-open.ts`. Epic 5's parity check reads the contract, so the stale wording will be re-flagged as a regression. **Disposition:** fix now (spec reconciliation, proposed). **Prevention:** when a story records an "epics text is stale" deviation, its Definition of Done includes the contract edit in the same PR.
- **F2. Pattern divergence: `SHIP_OPEN_*` test seams are undocumented.** `open.rs:89` (`SHIP_OPEN_MNT_C`), `open.rs:227` (`SHIP_OPEN_OS`) and `open.rs:348` (`SHIP_OPEN_LAUNCH_LOG`) are read by the shipped binary, but no spec or `SKILL.md` names them. The earlier overrides (`SHIP_PLATFORM`, `SHIP_GITHUB_API_URL`, `SHIP_ADO_API_URL`) are all listed in `cli-contract.md`. `SHIP_OPEN_LAUNCH_LOG` turns a real launch into an append to an arbitrary file that still exits 0, so a stray value in an operator's environment would make `ship open` silently do nothing. **Disposition:** defer (low; the variable is test-only in practice). **Prevention:** add every new `SHIP_*` override to the contract's environment table when it is introduced.
- **F3. Size growth: `open.rs` is the crate's largest module (768 lines) but not a god-class.** `git diff --stat 9ed209a 874b0fe` shows `src/open.rs` +768 and `tests/open.rs` +646. About 210 of the 768 lines are the `#[cfg(test)]` block (`open.rs:559`); the rest separates pure helpers (`local_state_path`, `parse_profiles`, `pick_browser`, `resolve`, `merge_config`, `launch_plan`, `ps_quote`) from IO (`detect_os`, `win_user`, `launch`, `run_inner`) as `epic-4-context.md` asked. `run_inner` (`open.rs:417-558`, about 140 lines) is the one long function. **Disposition:** accept as-is.
- **F4. Duplication map: clean.** `find_binary_on_path` (`open.rs:274`) and the `XDG_CONFIG_HOME` config path (`open.rs:219`) have no other implementations in `src/` (`rg` over `src/*.rs`). Nothing from Epics 1–3 was re-implemented. **Disposition:** none.
- **F5. Architecture delta: one new leaf module.** `src/lib.rs` +1 (`pub mod open`) and `src/main.rs` +23 (subcommand wiring); `open` imports none of `git`, `http`, `azure` or `github`, and `Cargo.toml` changed by one line (`Cargo.lock` +30). No new cross-module dependency or cycle. **Disposition:** none.
- **F6. Known deferred item carried forward.** `deferred-work.md` (entry from `spec-4-1`) records that the WSL `Local State` path is built from `%USERNAME%` and a hard-coded `/mnt/c`, which misses domain-suffixed profile folders. Inherited from the TS for parity; it works on this host. **Disposition:** defer (already tracked).

### Diff-scope review

`bmad-review` ran three lenses (adversarial, edge-case-hunter, verification-gap) as independent reviewers. Each reviewed `git diff 9ed209a 874b0fe` over `src/open.rs`, `src/main.rs`, `src/lib.rs` and `tests/open.rs`, with the 4.1→4.2 seam weighted. I re-checked every finding kept below against `open.rs` or `scripts/ship-open.ts` myself; I dropped or merged reports that did not hold up or repeated another. "Parity" means the TS reference behaves the same way.

**Input handling and injection (4.1 parsing meets 4.2 launch)**

- **R1. A dash-leading URL reaches the browser as a flag. Regression from the TS; confirmed by running it.** `ship open --dry-run -- --gpu-launcher=x` printed `opened_url=--gpu-launcher=x` and exited 0, and a real run passes that value to the browser's argv. `ship-open.ts:208` rejects any `-`-prefixed argument (`unknown arg: --`, exit 2). Found by: adversarial #1, edge-case #1. **Disposition:** fix now.
- **R2. An option value can swallow the next flag, which now opens a real window. Parity, but now with a real effect; confirmed by running it.** `ship open --profile --dry-run https://x/y` took `--dry-run` as the email, fell back to Default and **really launched Edge** during this retro (2026-11-12, one stray tab on the principal's desktop). The TS does the same (`argv[++i]`), but before 4.2 a non-dry run exited 2, so this was harmless. Found by: adversarial #12. **Disposition:** fix now (reject `-`-prefixed values for `--profile`, `--set-default`, `--browser`).
- **R3. Curly quotes escape the PowerShell quoting. Parity.** `ps_quote` (`open.rs:263-265`) doubles only ASCII `'`, as does `ship-open.ts:164`. PowerShell also treats U+2018–U+201B as single quotes, so a URL containing one ends the string, and whatever follows it runs as PowerShell on WSL. Found by: adversarial #1, edge-case #2. **Disposition:** fix now.
- **R4. A URL containing whitespace splits into extra browser arguments on WSL. Parity.** `Start-Process` joins `-ArgumentList` with bare spaces (the reason the profile value is double-quoted, `open.rs:308`), but the URL is not quoted the same way. Found by: adversarial #1, edge-case #3. **Disposition:** fix now, with URL validation (http/https only; no whitespace, control characters or `"`).
- **R5. An empty PATH entry is searched as the current directory.** `find_binary_on_path` (`open.rs:277`) joins a candidate onto `""`, so with PATH `:/usr/bin` a `./google-chrome` in the working directory can run. Found by: adversarial #11, edge-case #8. **Disposition:** fix now (skip empty and relative entries).

**Launch behavior differences**

- **R6. Launch-failure exit code and message differ from the TS. Unrecorded deviation.** A failing `powershell.exe` / `open` makes the TS `execFileSync` throw (exit 1, stack trace). The Rust exits 2 with `failed to launch …: exited with status N` and drops the child's stderr (`open.rs:360-376`). Found by: edge-case #7 and #11, adversarial #5. **Disposition:** accept the exit 2 (it matches the contract's "exit 2 for every failure" shape) and record it as a deviation; defer surfacing the child's stderr.
- **R7. Linux detach uses `process_group(0)`, not `setsid`.** `open.rs:378-381` vs `ship-open.ts:174` (`detached: true`). Whether the browser survives a terminal hangup was not tested. Found by: adversarial #4, edge-case #12. **Disposition:** defer (native Linux is best-effort per `epic-4-context.md`).
- **R8. On Linux the binary search is cut off from the state directory.** Chrome's `Local State` is read from `~/.config/google-chrome`, but `chromium` is an accepted binary, and the browser is picked by `Local State` existence alone. Parity. Found by: adversarial #2 and #3, edge-case #5 and #6. **Disposition:** defer.
- **R9. `--dry-run` never builds the launch plan,** so a Linux dry run reports success where the real run exits 2 (missing binary). Found by: adversarial #6, edge-case #9. **Disposition:** defer.
- **R10. An empty `HOME` gives relative config and state paths.** `open.rs:425` uses `unwrap_or_default()`; the TS uses `homedir()`, which falls back to the passwd entry. Found by: adversarial #8, edge-case #4. **Disposition:** defer (low).
- **R11. A stored-default miss falls back to the Default profile with no machine-readable signal.** Stdout still reports `profile_email=` and exit 0; only a `>>` note marks the fallback. Parity. Found by: adversarial #13. **Disposition:** fix now (principal approved the contract change, 2026-11-12): emit a `profile_fallback=` stdout key; folded into action items 1 and 3.
- **R12. Stale comments left at the 4.1→4.2 seam.** The `run` doc (`open.rs:404-405`) still says non-dry-run exits 2 "until Story 4.2", and the `tests/open.rs:1` header says "Story 4.1 … no browser". Found by all three lenses. **Disposition:** fix now (trivial).

**Verification gaps (each confirmed by a mutation that left all 43 open tests green)**

- **R13. The WSL/macOS launch status check is untested.** Changing `if !status.success()` to `if false` passed.
- **R14. The live Linux spawn is never checked to receive its arguments.** `cmd.args(&plan.args[..0])` passed. The "launch failure" test fails through the log seam, not a real spawn.
- **R15. `detect_os` has no test.** Every test sets `SHIP_OPEN_OS`; disabling the `WSL_DISTRO_NAME` branch passed.
- **R16. The `$HOME/.config/ship/open.json` fallback is untested.** Every test sets `XDG_CONFIG_HOME`; changing the fallback path passed. This breaks TS round-trip on the default setup.
- **R17. Email `.trim()` is untested.** Removing it passed. A padded email would open the wrong account.
- **R18. Executable-bit check and candidate order are untested.** `mode & 0o111 != 0` → `true` passed.

**Disposition:** fix now, as test additions (stub `powershell.exe`/`open` on PATH exiting 1; an argv-recording Linux stub; a pure `detect_os_from`; `env_remove("XDG_CONFIG_HOME")`; padded emails; a non-executable earlier candidate).

Dropped: adversarial #7 (`read_config` silently treats an invalid file as empty). `epic-4-context.md` ("Technical Decisions → Config file") specifies exactly that, so it is contract-conformant parity, not a defect.

## Behavior verification

Run on 2026-11-12 on the principal's WSL host (`Ubuntu-26.04`, Edge installed), commit `2458e07`, with `XDG_CONFIG_HOME` pointed at a temporary directory so the real `~/.config/ship/open.json` was never touched. The release binary and `bun scripts/ship-open.ts` (the reference) were run side by side by a scratch script.

- **Tests:** `cargo test` passed (326 tests across all targets, 0 failed); `cargo clippy --all-targets -- -D warnings` was clean.
- **`--list-profiles`:** same stdout from both: `browser=edge`, `local_state=/mnt/c/Users/…/Edge/User Data/Local State`, then three `profile=` lines (`Default`, `Profile 1`, `Profile 2`). Exit code 0 from both.
- **Unknown email with `--dry-run`:** both printed the same two `>>` notes (fallback to Default, dry run) and the same `opened_url` / `browser` / `profile_dir` / `profile_email` lines. `opened_url=https://example.com/pr?a=1&b=2` kept the `&` intact. Exit code 0 from both.
- **Usage errors:** `--browser firefox`, an unknown flag, and no URL each exited 2 from both.
- **Config round-trip:** `ship open --set-default … --browser edge` wrote `{"defaultProfileEmail": …, "browser": "edge"}`, and the TS script read it back and picked the stored browser and email.
- **Recorded deviation observed:** the TS leaks cmd.exe's UNC-path warning to stderr on every call; the Rust does not (`spec-4-1` line 98, accepted).
- **Not exercised: a real browser launch.** I ran no launch without `--dry-run`, so the `powershell.exe Start-Process` path (WSL) and `open -na` (macOS) were not run against a real browser. In tests, launches go through the `SHIP_OPEN_LAUNCH_LOG` seam. Only the Linux spawn path runs for real (`linux_launch_live_spawns_without_launch_log`). The `&`-in-URL and `Profile 2` guarantees are therefore proven at the argument-array level, not end to end. `epic-4-context.md` ("Cross-Story Dependencies") already says real-launch verification needs a manual check on each OS.

## Previous-retro follow-through

No prior retrospective documents exist (`epic-1-retrospective`, `epic-2-retrospective`, and `epic-3-retrospective` are `optional` in `sprint-status.yaml`), and `sprint-status.yaml` carries no `action_items` key yet — nothing from earlier retrospectives to follow through on.

## Action items

All items are **proposed**; none has been applied. The principal decides what runs.

1. **Harden `ship open` input before the Epic 5 cutover** (remediation; owner: Barbosa via `bmad-build`). Covers R1–R5 and R12: reject `--` and `-`-prefixed URLs and option values (exit 2, `unknown arg:` as in the TS); accept only http/https URLs with no whitespace, control characters or `"`; make `ps_quote` double U+2018–U+201B as well as `'`; skip empty and relative PATH entries; fix the stale comments. Also R11: print `profile_fallback=` on stdout when a stored default misses. Rust only: the TS is not patched (principal, 2026-11-12) and retires in Story 5-2. Runs in parallel with Epic 5.
2. **Close the six verification gaps** (remediation; owner: Barbosa via `bmad-build`, same branch as item 1). Covers R13–R18. Done means each listed mutation now fails a test.
3. **Reconcile the contract with the as-built** (spec reconciliation; owner: Barbosa). Covers F1, F2 and R6: in `epics.md:306` and `cli-contract.md:39`, replace `cmd.exe start` / `open -a` with `powershell.exe Start-Process` / `open -na … --args`; add `SHIP_OPEN_OS`, `SHIP_OPEN_MNT_C` and `SHIP_OPEN_LAUNCH_LOG` to the environment table as test-only; record the launch-failure exit 2 deviation; add the new `profile_fallback=` stdout key (R11) to the `ship open` output contract.
4. **Add real-launch checks on WSL and macOS to Story 5-1's parity checklist** (process; owner: Barbosa). Covers the behavior-verification gap: one real `ship open` per OS with a URL containing `&` and a `Profile 2` target, with the opened profile confirmed by eye.
5. **Process lesson: when a story records a deviation from the contract, the contract edit lands in the same PR** (process; owner: Barbosa). The same applies to every new `SHIP_*` override. Prevents a repeat of F1/F2.
6. **Log the deferred findings in `deferred-work.md`** (process; owner: Barbosa). R7, R8, R9, R10, plus R6's dropped child stderr, so a later run can pick them up without re-investigating.

## Acceptance verdict

**Machine verdict: rejected**, overridden by the principal (see below). Criteria: **declared** (`epics.md` Stories 4.1 and 4.2).

- Both stories are `done` (`pending_stories: []`).
- The 4.1 criteria hold in the evidence: list format, dry-run resolution with a stderr fallback note, and `--set-default` round-trip with the TS (Behavior verification).
- The 4.2 criteria hold at the argument level: an array launch with `&` intact, and the remembered default is used. The launch mechanics deviate from the criterion's wording, an accepted deviation awaiting the contract fix (F1). A real WSL/macOS launch was not exercised.
- **Blocking: R1.** The port accepts a dash-leading URL that the reference rejects and hands it to the browser as a flag. That breaks the epic's parity principle (`epic-4-context.md`, last Technical Decision) on an argument-handling path NFR2 exists to protect. With R3, the WSL launch path can be steered by URL content.

**Human decision (Barbosa, 2026-11-12): accepted-with-open-items.** Epic 5 proceeds in parallel; action item 1 is the tracked open item that clears R1.

## Decisions

1. **Verdict:** override the machine verdict to **accepted-with-open-items** and fix in parallel with Epic 5, rather than holding the cutover.
2. **TS fixes:** Rust only. R3 and R4 stay in `ship-open.ts` until it retires in Story 5-2.
3. **R11:** approved. Add a `profile_fallback=` stdout key; the contract edit lands with the code (action items 1 and 3).
