---
title: 'Story 1.3: Install a prebuilt binary without bun'
type: 'feature'
created: '2026-11-08'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: 'd92f14d35593f5b2f9d80bb1465d1eab99f45e9f'
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-1-context.md'
  - '{project-root}/_bmad-output/specs/spec-ship-rust-port/SPEC.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** `ship detect` and `ship preflight` exist only as source; using them still means a Rust toolchain and a local build. Nothing produces binaries for the two supported hosts, and nothing in CI builds or tests the crate.

**Approach:** Record the distribution decision in `skills/ship/`, add GitHub Actions that test the crate on every PR and build release binaries for Linux x86_64 and macOS arm64, and document a one-step install that needs no bun, npm, npx or Python.

## Boundaries & Constraints

**Always:** Binaries for `x86_64-unknown-linux-musl` (static, so any WSL2 distro runs it) and `aarch64-apple-darwin`, built on GitHub-hosted runners (macOS arm64 cannot be built on this WSL host). Each binary ships with a SHA-256 checksum, and the install step verifies it. `ship --version` prints the crate version, which matches the release tag. CI runs `cargo test` and `cargo clippy --all-targets -- -D warnings` on PRs touching `skills/ship/**` (closes the deferred CI item). The decision record states the choice and its reason. No npm, npx or Python anywhere in the workflows or install step.

**Decision (Barbosa, 2026-11-08): GitHub Releases.** Actions builds both targets when a `ship-v*` tag is pushed and attaches each binary with its `.sha256`; install downloads the asset for the host's OS/arch (`gh release download` or `curl`) and verifies the checksum. The repo is public, so released binaries are public.

**Decision (Barbosa, 2026-11-08): stop at a verified workflow.** This story proves the release build on the story's own pull request (a `pull_request` trigger builds both targets and uploads workflow artifacts only; `workflow_dispatch` does the same once merged, since GitHub only dispatches workflows present on the default branch). It creates no tag and no GitHub Release. The first `ship-v0.1.0` release is cut later on an explicit go-ahead. The install test therefore runs against the workflow artifacts.

**Never:** No change to `ship` behavior or output. Do not modify `scripts/*.ts`, `package.json`, or the SKILL.md flow (cutover is Story 5.2); an install section may be added to `skills/ship/` docs. No secrets beyond the default `GITHUB_TOKEN`. No release is published as part of building or testing the workflow.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| PR touches `skills/ship/**` | pull_request | CI job runs test + clippy, green | failing test or warning fails the job |
| PR elsewhere | pull_request on other paths | Rust CI job does not run | N/A |
| Release build | release trigger | two binaries + `.sha256` files produced; each runs `--version` on its own runner | build or smoke failure fails the run; nothing published |
| Install, Linux/WSL2 | host without bun, Rust or node | documented step puts a working `ship` on PATH; `ship detect`, `ship preflight` run | checksum mismatch aborts install with a clear message |
| Install, macOS arm64 | same | same | same |
| Version check | `ship --version` | `ship <crate version>` equal to the release tag's version | N/A |

</frozen-after-approval>

## Code Map

- `.github/workflows/lint-skills.yml` -- only existing workflow; pattern for path filters on `skills/**`. Leave untouched.
- `skills/ship/Cargo.toml` -- `version = "0.1.0"`, `rust-version = "1.88"`, release profile (`lto`, `strip`, `panic = "abort"`); single source of the version.
- `skills/ship/tests/*.rs` -- integration tests need `git` on the runner (present on GitHub-hosted images) and are isolated from global git config.
- `skills/ship/SKILL.md` § setup -- still says `bun install`; do not change the flow, Story 5.2 owns that.
- `_bmad-output/implementation-artifacts/deferred-work.md` -- "No CI job builds or tests the Rust crate" is closed by this story.
- `_bmad-output/implementation-artifacts/sprint-status.yaml` -- Story 1.2 still `review` though merged (PR #22); set it `done`.
- Host facts: only `x86_64-unknown-linux-gnu` target installed locally; no `cross`/`zig`; no existing tags or releases in the repo.

## Tasks & Acceptance

**Execution:**
- [x] `skills/ship/DISTRIBUTION.md` -- decision record: channel, targets, checksum, versioning, reason -- AC 1
- [x] `.github/workflows/ship-rust.yml` -- PR job: test + clippy on `skills/ship/**` -- closes deferred CI item
- [x] `.github/workflows/ship-release.yml` -- triggers `push: tags: ship-v*`, `workflow_dispatch`, and `pull_request` on `skills/ship/**` and the workflow file; build matrix (linux musl on ubuntu, aarch64-apple-darwin on macos-14), smoke `--version`, `.sha256` per binary; on tag, create the GitHub Release with the assets; on PR or dispatch, upload workflow artifacts only -- AC 2
- [x] `skills/ship/install.sh` -- detect OS/arch, download the matching asset (release by tag, or a local directory of downloaded artifacts for testing), verify SHA-256, install to `~/.local/bin` (overridable) -- AC 3 (POSIX shell only)
- [x] `_bmad-output/implementation-artifacts/sprint-status.yaml` -- Story 1.2 `review` → `done`

**Acceptance Criteria:**
- Given the workflows, when `actionlint` (or `gh workflow view` after push) checks them, then they parse and the Rust CI job passes on the PR.
- Given the release workflow's run on this story's pull request, then both binaries and checksums are uploaded as artifacts, each printed `ship 0.1.0` on its own runner, and no tag or release exists afterwards.
- Given a Linux host with bun, node and Rust removed from PATH, when `install.sh` runs against the downloaded workflow artifacts, then `ship detect` and `ship preflight` run.

## Implementation Notes

- New: `.github/workflows/ship-rust.yml` (test + clippy on PRs), `.github/workflows/ship-release.yml` (musl on ubuntu, aarch64-apple-darwin on macos-14; `--version` smoke; install.sh positive and wrong-checksum steps on each runner; release job only on a `push` of a `ship-v*` tag), `skills/ship/install.sh` (POSIX, SHA-256 verified, `SHIP_ASSET_DIR` for workflow artifacts), `skills/ship/DISTRIBUTION.md`. Deferred CI entry removed from `deferred-work.md`.
- Local evidence after review patches: `actionlint` 1.7.12 and `shellcheck` clean; `cargo test` 40 + 7 + 14 green; clippy `-D warnings` clean. With `PATH=/usr/bin:/bin` (no bun, node or cargo), install from a local asset dir printed `ship 0.1.0`, and `ship detect`/`ship preflight` ran. A corrupted binary exited 1 with `checksum mismatch` and installed nothing; an unknown repo exited 1 with `cannot list releases`; a non-running binary exited 1 with `does not run`.
- Still owed to the PR run: the real musl and macOS arm64 builds, their `--version` smoke, both install steps on each runner, and confirming no tag or release exists afterwards. The local install used a gnu build named as the musl asset.

## Spec Change Log

## Review Triage Log

Pass 1 (blind-hunter BH, edge-case-hunter EC, verification-gap VG).

| # | Finding | Verdict | Evidence | Route |
|---|---|---|---|---|
| 1 | BH1/EC1/EC15: `workflow_dispatch` on a `ship-v*` tag ref runs the `release` job | medium | `release` gates only on `startsWith(github.ref, 'refs/tags/ship-v')`; dispatch accepts tag refs. Breaks the frozen "no release" rule for manual runs. | patch |
| 2 | VG1/BH4: no automated run of `install.sh` (positive or checksum-mismatch) | medium | Neither workflow invokes it; only my manual local run did. A checksum regression would ship green. | patch |
| 3 | VG-other/BH2/EC3: `curl … \| sed \| head` makes `\|\| die` unreachable | low | Pipeline status is `head`'s; POSIX sh has no pipefail. Rate-limit 403 reports "no release found". Direct correction. | patch |
| 4 | EC11/BH11: install reports success when the installed binary cannot run | medium | `echo "…$(ship --version)"` ignores the substitution's failure under `set -e`; wrong-arch `SHIP_ASSET_DIR` gives exit 0 and an empty version. | patch |
| 5 | EC12: INT/TERM trap cleans up but does not exit | low | Ctrl-C mid-download removes `$WORK` and the script continues into confusing errors. Direct correction. | patch |
| 6 | EC7: `SHIP_VERSION=v0.1.0` builds `ship-vv0.1.0` | low | Plausible input; one-line prefix strip. | patch |
| 7 | BH9 (part), BH12 (part), BH13: DISTRIBUTION.md lacks checksum threat model, artifact-download command, non-targets | low | Doc gaps a user meets on first install; three lines. | patch |
| 8 | EC5: minified API JSON makes greedy `.*` pick the last tag | false | `api.github.com/repos/cli/cli/releases` returns pretty-printed JSON, one key per line; checked this session. | reject |
| 9 | EC4/EC16/BH3: "latest" may pick a prerelease or after >100 releases; `gh release create` marks repo-wide Latest | low | The workflow never creates prereleases and the repo has no other releases. Fix adds sorting/pagination. | reject |
| 10 | EC2: release re-run fails "already exists" | low | Rare manual re-run; fix adds a branch. | reject |
| 11 | EC8/EC9/EC10/EC13: version pin ignored with `SHIP_ASSET_DIR`; `$DEST/ship` is a dir; stray temp after 2nd `mv`; Rosetta shell | low | Unlikely in everyday use; each fix adds a guard or branch. | reject |
| 12 | BH10/EC14: version read via `sed` breaks on workspace versions | false | `skills/ship/Cargo.toml` has `[package]` first with a literal `version`; the bad read does not occur. | reject |
| 13 | BH5: static-link claim never asserted; no `musl-tools` | low | Pure-Rust deps link statically on musl; harm only arrives with a future C dependency. Adds a step. | reject |
| 14 | BH6: toolchain floats on `stable`; MSRV untested | low | A new lint turns PRs red visibly, never silently; pinning is a policy choice beyond a direct correction. | reject |
| 15 | BH7: no `cargo fmt --check` | low | Missing nicety, no defect. | reject |
| 16 | BH8: release build on every ship PR, macOS minutes | false | Public repo: Actions minutes on standard runners are free. | reject |
| 17 | BH9 (rest): no build provenance; actions pinned by tag | low | A tampered release needs repo compromise, which defeats any in-repo check; attestation is new surface. | reject |
| 18 | BH12 (rest): no curl one-liner, uninstall note | low | Enhancements, no defect. | reject |
| 19 | BH11-tracking: spec `in-review` vs sprint `in-progress`; empty notes | false | Workflow order: step 5 moves sprint to `review` and fills Implementation Notes. | reject |

## Verification

**Commands:**
- `cargo test --manifest-path skills/ship/Cargo.toml` -- expected: still green
- workflow lint (e.g. `actionlint` if available, else YAML parse) -- expected: clean
- after push: the Rust CI job on the PR -- expected: green
- local install test with a restricted PATH -- expected: `ship --version` and `ship detect` work
