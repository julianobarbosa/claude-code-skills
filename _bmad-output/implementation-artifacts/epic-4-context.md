# Epic 4 Context: Open a PR in the right browser profile

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Let the operator open any URL, normally the `pr_url` printed by `ship pr`, in the browser profile signed in with a chosen email, from WSL (Windows Edge/Chrome) or macOS. Review happens on the PR page, and the wrong signed-in account shows the wrong permissions or no access at all, so the binary must resolve an email to the browser's own profile directory instead of guessing. This ports `ship-open.ts` as `ship open`. Note: there is no PRD, architecture or UX document; intent comes from the port spec, its CLI parity catalog and the TypeScript script.

## Stories

- Story 4.1: Resolve an email to a browser profile
- Story 4.2: Launch the PR in the chosen profile

## Requirements & Constraints

- Flags: positional `<url>`, `--profile <email>`, `--browser edge|chrome`, `--list-profiles`, `--set-default <email>`, `--dry-run`, `-h/--help`. Any other flag, or a second positional, is a usage error (exit 2). `--browser` accepts only `edge` or `chrome` (exit 2 otherwise).
- Stdout is `key=value`; stderr carries `>>` notes. Resolve/launch prints `opened_url`, `browser`, `profile_dir`, `profile_email`. `--list-profiles` prints `browser=`, `local_state=`, then one `profile=<dir>\t<email>\t<name>` line per account (an account-less profile shows `(no account)` as the email). `--set-default` prints `default_profile_email=` and, only when a browser was given, `browser=`.
- Exit codes: 0 on success and `--help`; 2 for usage errors, a missing `<url>` (unless `--list-profiles`/`--set-default`), an empty `--set-default`, no supported browser found, a missing or unparseable `Local State`, no profiles, an undeterminable Windows username on WSL, and a missing Linux binary.
- Resolution order for the account: `--profile`, then the stored default email, then the browser's `Default` profile (or the first profile). Email matching is case-insensitive against each profile's signed-in `user_name`. An unknown email falls back to Default with a stderr note; a stored default used silently by the user gets a "using stored default" note. A profile with no account is reachable only as that fallback, never by email.
- Browser choice: `--browser`, else the stored browser if its `Local State` exists, else whichever is installed (chrome preferred when both), else the stored value, else exit 2. Installed means the `Local State` file exists.
- `--dry-run` resolves and prints but never launches. `--set-default` persists and exits before any browser detection.
- Opening is opt-in, never automatic; `SKILL.md` prompts the operator, so the binary must not open a window on its own from `ship pr`.
- Environment: `WSL_DISTRO_NAME` (WSL detection) and `XDG_CONFIG_HOME` (base for the config file).
- Nothing about an account is baked in: the profile map is read live each run; only the default email and browser are remembered.

## Technical Decisions

- **Config file:** `$XDG_CONFIG_HOME/ship/open.json`, else `~/.config/ship/open.json`. Fields `defaultProfileEmail` and `browser`, pretty-printed JSON with a trailing newline, parent directory created. Must round-trip with the TS script (same keys). An unreadable or invalid file is treated as empty. `--set-default` keeps existing fields and overwrites only the email, plus the browser when `--browser` is given. `serde_json` is already a dependency.
- **OS detection:** macOS by platform; WSL if `WSL_DISTRO_NAME` is set, else `/proc/version` contains "microsoft", else `/mnt/c` exists; otherwise native Linux (best effort).
- **`Local State` paths:** WSL `/mnt/c/Users/<winuser>/AppData/Local/{Microsoft/Edge|Google/Chrome}/User Data/Local State`; macOS `~/Library/Application Support/{Microsoft Edge|Google/Chrome}/Local State`; Linux `~/.config/{microsoft-edge|google-chrome}/Local State`. The Windows username comes from `cmd.exe /c echo %USERNAME%` stdout (cmd's UNC-path warning goes to stderr and is ignored). Profiles come from `profile.info_cache`: key is the directory, `user_name` is the email, `name` is the display name (defaults to the directory).
- **Launch mechanics — the epics text is stale here; follow the TS script.** The epics and `cli-contract.md` say WSL launches via `cmd.exe start` and macOS via `open -a`. The shipped script deliberately does not: `cmd.exe /c start` lets WSL interop leave a URL with `&` unquoted, and cmd then splits it as a command separator. The reference launches:
  - WSL: `powershell.exe -NoProfile -Command "Start-Process <msedge.exe|chrome.exe> -ArgumentList '<--profile-directory="DIR">','<url>'"`. Each arg is single-quoted for PowerShell (embedded `'` doubled) and the profile value is double-quoted inside the argument, because `Start-Process` joins with bare spaces and `Profile 2` would otherwise split and open the last-used profile.
  - macOS: `open -na "<Microsoft Edge|Google Chrome>" --args --profile-directory=DIR <url>` (`-n` new instance).
  - Linux: first of `microsoft-edge`, `microsoft-edge-stable` / `google-chrome`, `google-chrome-stable`, `chromium` found on PATH, spawned detached with stdio ignored so the browser outlives `ship`.
  Treat this as a recorded deviation from the epics wording: write it into the 4.2 spec, keep byte-identical behavior, and have the contract/epics wording corrected rather than regress to `cmd.exe start`.
- All launches are argument arrays, never shell strings (NFR2), including the Linux lookup (do not shell out to `bash -lc command -v`; scan PATH in Rust). Tests must prove a URL containing `&` reaches the launcher intact and that a profile directory with a space (`Profile 2`) stays one value.
- Keep pure logic (OS-specific path building, `Local State` parsing, profile resolution, argument construction, PowerShell quoting, config merge) separate from process spawning so it is testable without a browser. Test launch construction by asserting the argument arrays, and cover profile resolution with fixture `Local State` JSON in a temp dir and `XDG_CONFIG_HOME` pointed at a temp dir.
- No network, no token handling; the existing `git`/`az`/`gh` subprocess and ref-validation helpers are not needed here. The crate is a clap-derive binary (`src/main.rs`) plus a library (`src/lib.rs`); add `open` as a new subcommand and module following the pattern of the existing ones. Existing dependencies suffice (`clap`, `serde_json`, `regex`).
- Parity principle from earlier epics applies: the TS script is the reference for stdout, stderr `>>` lines and exit codes; any deviation needs the principal's approval and a note in the story spec.

## Cross-Story Dependencies

- Story 4.2 builds on 4.1's profile resolution and config handling; 4.1 can ship with `--list-profiles`, `--dry-run` and `--set-default` before any launch code exists.
- Depends on Epic 1 only for the crate skeleton and subcommand wiring. Consumes the `pr_url` that Epic 3's `ship pr` prints but does not call it.
- Epic 5 replaces the `bun scripts/ship-open.ts` invocations in `SKILL.md` section 4c with `ship open` and includes it in the parity check; the macOS and WSL launches cannot both run in one CI host, so real-launch verification needs a manual check on each OS.
