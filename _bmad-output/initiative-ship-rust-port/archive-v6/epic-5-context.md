# Epic 5 Context: Cut over: ship with no bun

<!-- Generated from planning artifacts. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Complete the port of the `ship` skill from seven TypeScript scripts to one Rust binary by proving the binary matches the scripts, then switching the skill over and deleting the scripts. After this epic the skill runs on a machine with no bun and no `node_modules`, and cutover rests on measured evidence (output parity and startup speed) rather than trust.

## Stories

- Story 5.1: Prove parity and startup speed against the TS scripts
- Story 5.2: Switch the skill to the binary and retire the TS scripts

## Requirements & Constraints

- Parity: every flag, environment variable, `key=value` stdout line and exit code of the TS scripts must be preserved. The parity check must report any difference in `key=value` lines or exit codes across all seven subcommands (`detect`, `preflight`, `push`, `pr`, `tag`, `open`, `snapshot`), and the run must show none.
- Parity is exercised on one Azure Repos clone and one GitHub clone: read-only subcommands run directly; write subcommands run in a dry-run or throwaway-branch variant so no real delivery state is damaged.
- Startup speed: record median startup per subcommand for both implementations. The binary must be faster for every subcommand, and `detect` and `preflight` must have a median under 50 ms on Linux/WSL2. The 50 ms figure is a default adopted without confirmation; it should be revisited before 5.1 if wrong.
- The parity and benchmark tooling itself must not use npm, npx or Python (Rust only in build, test and install).
- Cutover: every `bun scripts/ship-*.ts` invocation in `SKILL.md`, its references and `assets/` becomes `ship <subcommand>` with identical flags. The bun-install setup note is replaced by the binary install step recorded in Epic 1.
- Remove `scripts/*.ts`, `package.json`, `tsconfig.json` and `node_modules` from `skills/ship/`. The TS scripts are retired, not kept side by side.
- Final acceptance: on a host with no bun, a full ship run (preflight, push, PR with work item, tags, reviewers) succeeds on both the Azure and the GitHub repo.
- Cross-cutting rules still apply to anything this epic touches: git/az/gh are called with argument arrays, tokens never printed or logged, no AI attribution in commits or PRs, Linux/WSL2 and macOS only, no behavior changes during the port.
- `ship-tag` (the release skill) and the `merge`, `commit` and `azure-devops` skills are out of scope.

## Technical Decisions

- One binary with subcommands (`ship detect|preflight|push|pr|tag|open|snapshot`) replaces the seven scripts.
- The TS scripts are the reference implementation for output formats and edge cases until they are deleted; `cli-contract.md` is the parity catalog (flags, env vars, stdout keys, exit codes such as `snapshot` refusing an existing tag with exit 3 and `preflight` always exiting 0).
- Binary distribution (committed per-platform builds, `cargo install`, or GitHub Releases) is decided and documented in Epic 1; the install step in `SKILL.md` must follow that decision. Supported prebuilt targets are Linux x86_64 (WSL2) and macOS arm64.
- Behavioral gotchas the port keeps and parity runs should not mask: Azure create drops `completionOptions` (set by a post-create update and read back); a GitHub 404 on create usually means the wrong account; `TF400813` right after a UPN rename is ADO's identity cache; PR titles are passed literally and `&` is never escaped.
- Existing `ship-lib.test.ts` cases are the parity baseline and are ported to Rust tests (in earlier epics); they must still pass when the TS files are removed.

## Cross-Story Dependencies

- Story 5.2 requires Story 5.1 passing: the TS scripts are deleted only after parity and speed are demonstrated.
- Both stories depend on Epics 1-4 being complete: all seven subcommands exist in the binary, and the distribution/install step from Story 1.3 is available to document in `SKILL.md`.
- Story 5.2's final no-bun acceptance run uses the same Azure and GitHub repos as Story 5.1.
