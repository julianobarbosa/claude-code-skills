---
title: 'Story 4.2: Launch the PR in the chosen profile'
type: 'feature'
created: '2026-11-11'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: '7031ea0'
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-4-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Story 4.1 resolved the target profile and URL with `--dry-run`, but running `ship open <url>` without `--dry-run` still prints a "not implemented yet" message and exits 2 without launching the browser window.

**Approach:** Port the launch half of `ship-open.ts` into `ship open`. Launch the chosen browser profile with the given URL on WSL (via `powershell.exe Start-Process`), macOS (via `open -na`), and Linux (via PATH binary detached spawn), printing the verbatim stderr `>> opening in ...` note and stdout keys (`opened_url`, `browser`, `profile_dir`, `profile_email`).

## Boundaries & Constraints

**Always:**
- **Launch Mechanics (following `ship-open.ts` / `epic-4-context.md`, superseding stale `epics.md` wording):**
  - **WSL:** invoke `powershell.exe` with `["-NoProfile", "-Command", "Start-Process <win_exe> -ArgumentList <arg_list>"]` where `arg_list` is `['--profile-directory="DIR"', '<url>']` with each item single-quoted for PowerShell (embedded `'` doubled) and the profile directory double-quoted inside the argument so spaces (`Profile 2`) do not split. Stdio is ignored.
  - **macOS:** invoke `open` with `["-na", "<mac_app>", "--args", format!("--profile-directory={}", profile_dir), url]`. Stdio is ignored.
  - **Linux:** search PATH for candidates (`microsoft-edge`, `microsoft-edge-stable` for Edge; `google-chrome`, `google-chrome-stable`, `chromium` for Chrome) using a Rust PATH search (no shell subshell). If found, spawn detached (`stdin/stdout/stderr` null / ignored) with args `[format!("--profile-directory={}", profile_dir), url]`. If none found, fail with exit 2 and message `no <browser> binary found on PATH (tried <candidates>)`.
- **Arguments safety (NFR2):** Process spawning uses argument arrays, never raw shell strings, ensuring URLs containing `&` and profile names containing spaces remain intact.
- **Stderr & Stdout:**
  - Before launching (when not dry-run), print stderr: `>> opening in <browser> profile "<dir>"[ (<email>)]`.
  - After launching, print stdout in key=value format:
    ```
    opened_url=<url>
    browser=<browser>
    profile_dir=<dir>
    profile_email=<email>
    ```
- **Exit codes:** 0 on success; 2 on missing Linux binary or launch spawn failure.
- **Testability Seam:** A test seam (e.g. `SHIP_OPEN_LAUNCH_CMD` or mock runner) allows automated unit and binary integration tests without launching real desktop windows in CI/sandbox.

**Never:**
- No shell strings (`bash -c`, `sh -c`, `cmd.exe /c start`).
- No regression to Story 4.1 resolution logic, `--list-profiles`, `--set-default`, or `--dry-run` behavior.
- No automatic browser launching from `ship pr` (browser open is always explicit via `ship open`).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Launch WSL Edge | `ship open https://example.com/pr/1 --profile b@x.com` on WSL | Stderr `>> opening in edge profile "Profile 2" (b@x.com)`; executes PowerShell Start-Process with quoted args; stdout keys printed | exit 0 |
| Launch macOS Chrome | `ship open https://example.com/pr/1` on macOS | Stderr `>> opening in chrome profile "Default"`; executes `open -na "Google Chrome" ...`; stdout keys printed | exit 0 |
| Launch Linux Chrome | `ship open https://example.com/pr/1` on Linux with `google-chrome` on PATH | Stderr note printed; spawns `google-chrome` detached; stdout keys printed | exit 0 |
| Linux No Binary | Linux with no browser binary found on PATH | Exit 2; Stderr `no <browser> binary found on PATH (tried ...)` | exit 2 |
| URL with `&` | `ship open "https://example.com/?a=1&b=2"` | PowerShell / open / Linux command receives full URL without splitting on `&` | exit 0 |
| Profile with spaces | Profile directory `Profile 2` | Quoted so browser receives `--profile-directory="Profile 2"` as single argument | exit 0 |

</frozen-after-approval>

## Code Map

- `skills/ship/scripts/ship-open.ts`: Reference implementation, lines 154–176 (launch function per OS).
- `skills/ship/src/open.rs`:
  - Add pure functions: `wsl_launch_cmd`, `macos_launch_cmd`, `linux_find_binary`.
  - Replace lines 384–387 (the Story 4.2 placeholder) with live `launch` implementation.
  - Implement test seam `SHIP_OPEN_LAUNCH_LOG` or command interception for deterministic testing.
- `skills/ship/tests/open.rs`:
  - Add test coverage for launch command construction (WSL, macOS, Linux).
  - Add integration tests verifying launch invocation, stdout keys, stderr notes, and URL preservation across OS modes.

## Tasks & Acceptance

**Execution:**
- [x] `skills/ship/src/open.rs` -- implement browser launching for WSL, macOS, and Linux with pure argument builders and test seam -- FR11 (launch half)
- [x] `skills/ship/tests/open.rs` -- integration and unit tests for launch command formatting, PATH search, and process spawning -- NFR2 & parity proof
- [x] `_bmad-output/implementation-artifacts/sprint-status.yaml` -- advance 4-2 to in-progress / review -- tracking

**Acceptance Criteria:**
- Given a resolved profile from Story 4.1, when `ship open <url>` is run without `--dry-run`, then it invokes the platform browser launcher with the profile directory and URL.
- Given a URL containing `&`, when launched, then the URL is passed intact without shell splitting.
- Given `cargo test` and `cargo clippy --all-targets -- -D warnings`, then both pass with zero failures and zero warnings.

## Implementation Notes

- Implemented `launch_plan`, `find_binary_on_path`, `ps_quote`, and `launch` in `skills/ship/src/open.rs`.
- Added `win_exe`, `mac_app`, and `linux_bins` to `Browser`.
- Replaced the Story 4.2 deferred placeholder in `open::run_inner` with active launch invocation, logging `>> opening in <browser> profile "<dir>"` on stderr before launching and emitting standard key=value lines on stdout.
- Implemented `SHIP_OPEN_LAUNCH_LOG` and `SHIP_OPEN_MNT_C` test seams to test full binary launch execution deterministically without launching real GUI windows or touching `/mnt/c`.
- `cargo test`: all 295 unit and integration tests passing.
- `cargo clippy --all-targets -- -D warnings`: clean.

## Spec Change Log

## Review Triage Log

Review used three reviewers: blind-hunter (BH), edge-case-hunter (EC), and verification-gap (VG).

| # | Finding | Verdict | Evidence | Route |
|---|---|---|---|---|
| 1 | BH1/2: Launcher helpers on WSL and macOS (`powershell.exe`, `open`) should wait synchronously for completion | low | Confirmed: `ship-open.ts` used `execFileSync` for WSL/macOS, preventing premature session exit and catching exit errors. | patch |
| 2 | BH3: Stderr status banner emitted before launch planning/validation succeeds | false | `ship-open.ts` lines 263-264 outputs the `>> opening in ...` note before calling `launch()`. Rust preserves reference parity. | reject |
| 3 | BH4: Empty URL string (`""`) bypasses required URL validation | low | Confirmed: TS `if (!url)` rejects falsy/empty strings. Added `.filter(\|u\| !u.is_empty())`. | patch |
| 4 | BH5: Untracked spec artifact omitted from diff patch | false | Story spec is created in-tree during the workflow prior to presentation/commit. | reject |
| 5 | BH6: Sprint status set to `in-progress` instead of `review` | low | Status advanced to `review` upon completion of review pass. | patch |
| 6 | BH7: Missing `chromium-browser` candidate for Linux Chrome | false | `ship-open.ts` specifies `["google-chrome", "google-chrome-stable", "chromium"]`. Parity preserved. | reject |
| 7 | BH8: Incomplete permissions check in `find_binary_on_path` | false | Standard executable bit mask check on Unix suffices for PATH searching. | reject |
| 8 | BH9: Unescaped double quotes in WSL profile directory argument | false | `ship-open.ts` line 165 uses the exact same argument construction without double-quote escaping inside profileDir. | reject |
| 9 | VG1: Subprocess spawning in `launch` is mocked away by test seam across all launch tests | low | Confirmed: added `linux_launch_live_spawns_without_launch_log` to exercise the non-mocked spawn path. | patch |
| 10 | VG2: Subprocess spawn failure error handling in `run_inner` is unexercised | low | Confirmed: added `launch_failure_exits_2_with_error_message` integration test. | patch |
| 11 | VG3: `Browser::linux_bins` candidate resolution for `Browser::Edge` on Linux is untested | low | Confirmed: added `linux_launch_plan_edge_candidates` unit test. | patch |

## Verification

**Commands:**
- `no_proxy="*" NO_PROXY="*" cargo test --manifest-path skills/ship/Cargo.toml` -- all 298 tests passed.
- `cargo clippy --manifest-path skills/ship/Cargo.toml --all-targets -- -D warnings` -- clean.
