---
title: 'Story 4.1: Resolve an email to a browser profile'
type: 'feature'
created: '2026-11-09'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: '9ed209af063a0288d2c86cc632af8b967368a6d6'
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-4-context.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The binary has no `ship open`, so seeing which signed-in browser account a PR will open under still needs bun and `ship-open.ts`.

**Approach:** Port the resolution half of `ship-open.ts` as `ship open`. It covers `--list-profiles`, `--set-default`, and `<url> --dry-run` email-to-profile resolution, with the same stdout, stderr `>>` notes, config file and exit codes. Launching a window is Story 4.2.

## Boundaries & Constraints

**Always:**
- **Args (TS parity):**
  - Positional `<url>`, `--profile <email>`, `--browser <b>`, `--list-profiles`, `--set-default <email>`, `--dry-run`.
  - Value flags take the next arg verbatim (`allow_hyphen_values`), and the last occurrence wins (`overrides_with`).
  - A `--browser` value other than `edge`/`chrome` exits 2 with `--browser must be edge or chrome (got <v>)`.
  - An unknown flag or a second positional exits 2.
- **OS detection:** macOS by `target_os`, else WSL (`WSL_DISTRO_NAME`, `/proc/version` contains "microsoft", or `/mnt/c` exists), else Linux. The test seam `SHIP_OPEN_OS=macos|wsl|linux` overrides it, the same way `SHIP_ADO_API_URL` is a seam.
- **Paths:** `Local State` paths per OS and browser, and the WSL Windows user from `cmd.exe /c echo %USERNAME%` stdout (trimmed), all as in the TS. An empty user exits 2 with the TS message.
- **Config:** `$XDG_CONFIG_HOME/ship/open.json`, else `~/.config/ship/open.json`.
  - A missing, unparseable or non-object file reads as empty.
  - A stored `browser` other than edge/chrome, or a non-string email, is ignored.
  - `--set-default` keeps every existing key and overwrites `defaultProfileEmail`, plus `browser` when it is given. It writes 2-space pretty JSON plus `\n`, with the parent dir created, so a fresh file is byte-identical to the TS output.
  - `--set-default` runs before any browser detection. An empty email exits 2 with `--set-default needs an email`.
- **Browser pick:** `--browser`; else the stored browser if its `Local State` exists; else installed ones in `chrome`, `edge` order; else the stored browser; else exit 2 with the TS message.
- **Profiles:** read from `profile.info_cache` in file key order. The dir is the key, the email is `user_name` (default `""`) and the name is `name` (default the dir). A missing or unparseable `Local State` exits 2 with the TS message.
- **Resolution:** the wanted email is `--profile`, then the stored default, trimmed and compared case-insensitively. A miss prints the TS "falling back to the Default profile" note. A stored default that matches prints the "using stored default" note. Otherwise the `Default` dir is used, else the first profile; with no profiles, exit 2.
- **Output:** stdout `opened_url`, `browser`, `profile_dir`, `profile_email`. The `--list-profiles` and `--set-default` lines and the stderr `>>` notes are verbatim from the TS.
- Every error message is the TS text, printed bare to stderr. Exit codes are 0 on success and 2 on every error above.
- **Key order (decision, Barbosa 2026-11-09, option A):** enable `serde_json`'s `preserve_order` feature (adds `indexmap`). `info_cache` keeps file key order for listing and the first-profile fallback, and `--set-default` keeps the existing config key order, as the TS spread does. This is the only new dependency.
- Without `--dry-run`, after resolving, print stderr `>> launching a browser is not implemented yet (Story 4.2); use --dry-run` and exit 2.

**Never:** No change to `scripts/*.ts`, `package.json`, `SKILL.md`, or any other subcommand's behavior. No launch code, no `cmd.exe start`, `powershell.exe` or `open`. No shell strings (NFR2).

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| List | chrome `Local State` with Default, Profile 2 (one with no `user_name`) | `browser=chrome`, `local_state=<path>`, `profile=Default\t(no account)\t<name>`, `profile=Profile 2\tb@x.com\tWork`, in file order | N/A |
| Dry-run hit | `u --profile B@X.com --dry-run` | `profile_dir=Profile 2`, `profile_email=b@x.com`, dry-run note | N/A |
| Unknown email | `u --profile nope@x --dry-run` | fallback note; `profile_dir=Default` | exit 0 |
| Stored default | config email `b@x.com`, no `--profile` | "using stored default" note; Profile 2 | N/A |
| Set default | `--set-default a@x --browser edge`, no config | file `{"defaultProfileEmail":"a@x","browser":"edge"}` pretty; `default_profile_email=a@x`, `browser=edge` | N/A |
| Set keeps keys | existing `{"browser":"chrome","x":1}` + `--set-default a@x` | keys kept, email added, `browser=chrome` printed | N/A |
| No browser | no `Local State` anywhere, no `--browser` | TS "no supported browser" message | exit 2 |
| Bad browser | `--browser firefox` | TS message | exit 2 |
| No url | `ship open` | TS "need a <url>" message | exit 2 |
| URL with `&` | `"https://x/?a=1&b=2" --dry-run` | `opened_url` is the URL intact | N/A |
| Not dry-run | `u --profile b@x.com` | resolution notes, then the 4.2 note | exit 2 |

</frozen-after-approval>

## Code Map

- `skills/ship/scripts/ship-open.ts`: the reference for every message, the output order and the exit codes. Lines 100-151 hold the paths, config and browser pick; lines 178-262 hold the args, set-default, list and resolution.
- `skills/ship/src/main.rs`: add an `Open` variant to `Command`. Use a positional `Option<String>`, value flags with `allow_hyphen_values` + `overrides_with`, and bools with `overrides_with`. `--browser` is a `String` validated in `open.rs` so the message matches. Dispatch to `ship::open::run(&ship::open::Args{..})` -> `io::Result<u8>`.
- `skills/ship/src/open.rs` (new):
  - Pure functions with unit tests: `local_state_path(browser, os, home, win_user)`, `parse_profiles(&str)`, `pick_browser(explicit, stored, installed)`, `resolve(profiles, wanted, from_flag)` (it returns the chosen profile and the note), and `merge_config(existing, email, browser)`.
  - `run` does the IO: env, files and `cmd.exe` through `std::process::Command` args.
  - Follow `snapshot.rs` for the `run -> io::Result<u8>` shape with locked stdout.
- `skills/ship/src/lib.rs`: add `pub mod open;`.
- `skills/ship/Cargo.toml`: `serde_json = { version = "1.0.154", features = ["preserve_order"] }`. Other subcommands' request bodies then serialize in insertion order; no test compares raw JSON strings, so the full suite must stay green.
- `skills/ship/tests/open.rs` (new): real-binary tests in the style of `tests/snapshot.rs`, with a `Scratch` temp dir and `env_clear`-free isolation through `HOME`, `XDG_CONFIG_HOME`, `SHIP_OPEN_OS=linux|macos` and `WSL_DISTRO_NAME` removed. A fixture `Local State` goes under the scratch HOME. Cover every matrix row. WSL path building is unit-tested only, because `/mnt/c` is absolute.
- `_bmad-output/implementation-artifacts/sprint-status.yaml`: set 3-7 to `done` (PR #33 is merged at baseline) and move 4-1 and epic-4 through the build statuses.

## Tasks & Acceptance

**Execution:**
- [x] `skills/ship/Cargo.toml` -- enable `serde_json/preserve_order` -- TS profile order and config key order
- [x] `skills/ship/src/open.rs`, `lib.rs`, `main.rs` -- `ship open` resolution with pure-function unit tests -- FR11 (resolve half)
- [x] `skills/ship/tests/open.rs` -- every matrix row against the real binary -- parity proof
- [x] `_bmad-output/implementation-artifacts/sprint-status.yaml` -- 3-7 `done`, 4-1/epic-4 progress -- tracking

**Acceptance Criteria:**
- Given a scratch HOME with Chrome `Local State` (Default, Profile 2, Profile 10 in that key order), when I run `ship open --list-profiles`, then the profile lines come out in that same order.
- Given a config written by `ship open --set-default`, when `bun scripts/ship-open.ts --list-profiles` reads the same `XDG_CONFIG_HOME`, then it picks the same browser (manual, if bun is present).
- Given `cargo test` and `cargo clippy --all-targets -- -D warnings`, then both pass and every existing test still passes.

## Implementation Notes

- Built by a Sonnet subagent from the spec alone, then checked by the lead against the diff. `cargo test` gives 311 passed (94 unit, 21 `open`, plus every existing suite unchanged), and clippy `-D warnings` is clean.
- `src/open.rs` has the pure `local_state_path`, `parse_profiles`, `pick_browser`, `resolve` (it returns the chosen profile and a `Note`) and `merge_config`, plus `run`, which does the I/O. Every error prints its TS text bare and exits 2.
- `Cargo.toml`: `serde_json/preserve_order`, which brings `indexmap` into `Cargo.lock`. Unit and binary tests prove both file key order and config key order.
- Live check on this WSL host: `ship open --list-profiles` stdout is byte-identical to `bun ~/.claude/skills/ship/scripts/ship-open.ts --list-profiles` against the real Edge `Local State` (three profiles). A dry-run with an unknown email falls back to Default with the TS note, and a URL with `&` stays intact. The repo copy of the TS cannot run here (no `node_modules`), so the installed copy was the reference. The implementer reports `--set-default` writes a byte-identical `open.json`.
- Known small differences, all outside the matrix:
  - The tail of the "could not parse … Local State" message is serde's error text, not JavaScript's `SyntaxError`.
  - `cmd.exe` stderr is discarded, so the TS's UNC-path warning no longer leaks.
  - An invalid stored `browser` (for example `firefox`) is ignored per the spec, so `--set-default` keeps it in the file but prints no `browser=` line, where the TS prints `browser=firefox`.
- `cargo fmt --check` still fails on pre-existing files. Only the two new files were formatted.
- Review patches (triage #1-3), applied by the same subagent:
  - WSL binary tests run with an empty `PATH` and with a stub `cmd.exe`.
  - A last-wins test covers `--browser` and `--set-default`.
  - `--set-default` now echoes a raw stored `browser` string, as the TS does.
  - Triage #4, the sprint timestamp, was fixed by the lead.
  - The lead re-ran the suite: `cargo test` 315 passed (25 `open`), clippy clean.

## Spec Change Log

## Review Triage Log

Pass 1 used three Opus reviewers: blind-hunter (BH), edge-case-hunter (EC) and verification-gap (VG). The parity rule is the spec's: `ship-open.ts` behavior is the reference, so a finding that asks Rust to diverge from what the TS does is rejected as parity.

| # | Finding | Verdict | Evidence | Route |
|---|---|---|---|---|
| 1 | VG1: the WSL branch (`SHIP_OPEN_OS=wsl`, `win_user`, the empty-name guard, the user in the path) runs in no test | low | Confirmed: every binary test passes `linux` or `macos`. Dropping the guard or the user would stay green. | patch |
| 2 | VG2: `overrides_with` on `--browser` and `--set-default` is untested | low | Confirmed: only a repeated `--profile` is tested. One test closes it. | patch |
| 3 | EC14: `--set-default` with stored `browser:"firefox"` prints no suffix or `browser=` line, where the TS prints both | low | Confirmed: TS `next.browser` is truthy for any string. The spec's "ignored" covers picking, not this output. | patch |
| 4 | BH1/EC12: `last_updated` went backwards (21:45 to 19:55) | low | Confirmed: the earlier stamp was not in local time. Rewritten to the current local time by the lead. | patch |
| 5 | BH8: on WSL, `%USERNAME%` may not match the profile folder, and `/mnt/c` is hard-coded | maybe-false | Pre-existing TS behavior kept for parity. It works on this host. Settle it on a domain-joined machine. | defer |
| 6 | BH2/EC10: the miss note says "Default" even when the first profile is picked | false | TS lines 249-257 print the same fixed text, and the spec requires it verbatim. | reject |
| 7 | BH3/EC9: with no profiles, a miss prints the fallback note, then "no profiles found" | false | TS prints the miss note before `fail(no profiles)` in the same order. | reject |
| 8 | BH4: `--set-default` overwrites an unparseable config, non-atomically | false | TS `readConfig` returns `{}` on a parse error and `writeFileSync` writes in place. This is parity, and the spec requires it. | reject |
| 9 | BH5/EC3: `--set-default` does not trim, and accepts whitespace | false | TS stores the value as given. The lookup trims, so `" a@x "` still matches. Whitespace-only is TS parity. | reject |
| 10 | BH6: `allow_hyphen_values` lets `--profile --dry-run` eat the flag | false | TS `argv[++i]` does the same, and the spec requires verbatim values. | reject |
| 11 | BH7/EC4: flag combinations with `--set-default` or `--list-profiles` are silently ignored | false | TS exits early on these in the same order. | reject |
| 12 | BH9/EC1/EC13: an unset `HOME` targets `/.config` | low | TS falls back to passwd through `homedir()`. Unset `HOME` is rare, and the fix needs a passwd lookup or a new guard. | reject |
| 13 | BH10/EC6: `/mnt/c` alone means WSL; `SHIP_OPEN_OS` ships in the binary | false | TS uses the same detection. The seam is spec-sanctioned, like `SHIP_ADO_API_URL`. | reject |
| 14 | BH11: `preserve_order` changes JSON ordering crate-wide | false | The full suite (311 tests) passes with it. The spec records the effect, and no test compares raw JSON strings. | reject |
| 15 | BH12: SKILL.md and docs are not updated | false | Epic 5 Story 5.2 owns the SKILL.md switch, and the spec freezes SKILL.md. | reject |
| 16 | BH12: Chromium, Flatpak and beta-channel Linux paths are missing | false | The TS has the same paths; Linux is best-effort in the source. | reject |
| 17 | BH12: no test for a miss without a `Default` dir, or for whitespace and `HOME` | low | The behaviors are TS parity (rows 6, 9, 12), and the unit test `resolve_hit_miss_fallback` covers the no-Default fallback. | reject |
| 18 | EC2: a relative `XDG_CONFIG_HOME` resolves against cwd | false | TS `join(process.env.XDG_CONFIG_HOME, …)` does the same. | reject |
| 19 | EC5: `%USERNAME%` unset makes cmd echo a literal `%USERNAME%` | low | TS does the same. Rare, and the fix adds a guard. | reject |
| 20 | EC7/EC8: a tab or newline in profile fields or the URL breaks `key=value` lines | false | TS prints them raw in the same way. Browser `Local State` names do not hold control characters. | reject |
| 21 | EC11: `--profile ""` and `--profile " "` behave differently | false | Both reach `Default` with no note, as TS `wanted.trim()` does. | reject |

## Verification

**Commands:**
- `cargo test --manifest-path skills/ship/Cargo.toml` -- expected: all green
- `cargo clippy --manifest-path skills/ship/Cargo.toml --all-targets -- -D warnings` -- expected: clean

**Manual checks (if no CLI):**
- On this WSL host: `skills/ship/target/debug/ship open --list-profiles` lists the same lines as `bun skills/ship/scripts/ship-open.ts --list-profiles`.
