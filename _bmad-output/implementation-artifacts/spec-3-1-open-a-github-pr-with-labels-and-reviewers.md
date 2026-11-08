---
title: 'Story 3.1: Open a GitHub PR with labels and reviewers'
type: 'feature'
created: '2026-11-08'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: 'f100f67b8c42254887b914ed0c1613a08ad0ab10'
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-3-context.md'
  - '{project-root}/_bmad-output/specs/spec-ship-rust-port/cli-contract.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Opening a PR still means running `bun scripts/ship-pr.ts`, which needs bun and `@octokit/rest`. The binary also has no HTTP client yet, and every Epic 3 and 4 story needs one.

**Approach:** Record the HTTP client decision in `skills/ship/`, then add `ship pr` for GitHub remotes with the TS behavior: create the PR, attach labels and reviewers in follow-up calls, and print the same `key=value` lines. Azure Repos comes in Story 3.2.

## Boundaries & Constraints

**Decision (Barbosa, 2026-11-08): `ureq` 3 + `serde_json`, direct REST, for GitHub and Azure DevOps.**
- **Rejected:** `octocrab` (0.54.9) and `azure_devops_rust_api` (0.39.1). Both are maintained, as is `ureq` (3.5.1), all checked on crates.io on 2026-11-08, but they pull in tokio + reqwest.
- **Why `ureq`:** it is blocking and uses rustls TLS (no OpenSSL), keeps the binary small and startup fast (NFR9), and the TS calls only about 8 endpoints.
- **Record:** the decision and its reason go in `skills/ship/HTTP-CLIENT.md`.

**Always:**
- **Flags:** `--title` (required; missing → `--title is required`, exit 2), `--body`, `--body-file` (file wins over `--body`), `--target` (default `main`), `--source` (default: current branch), `-r/--remote` (default `origin`), `--draft`, `--tag` (repeatable, comma-separated), `--no-tag`, `--reviewer` and `--required-reviewer` (repeatable, comma-separated), and `--no-reviewer`. The CSV split and dedupe ports `parseTags`.
- **Ref check:** `--source`, `--target` and `--remote` go through the shared `push.rs` validation (exit 2).
- **Default tags,** when there is no `--tag` and no `--no-tag`: first `defaultTagsFromTitle` (Conventional-Commit type plus scope), else the branch prefix map (`feat|feature→feat`, `fix|hotfix|bugfix→fix`, `docs|doc→docs`, `chore`, `refactor`), else `needs-review`. Each path prints its TS stderr `>> NOTE:` or `>> WARNING:` line verbatim.
- **Platform:** dispatch on `detect_kind` (`SHIP_PLATFORM` applies). `unknown` → `unknown platform for remote '<r>' (<url>); set SHIP_PLATFORM=azure|github`, exit 1. `azure` in this story → a clear "not yet supported by the binary; use bun scripts/ship-pr.ts" message, exit 1.
- **GitHub token:** owner and repo come from `github_owner_repo` (an unparseable URL → `could not parse owner/repo from <url>`, exit 1). The token comes from `GH_TOKEN`, then `GITHUB_TOKEN`, then `gh auth token -u <owner>`, then `gh auth token` (NFR6). With none: `no GitHub token: set GH_TOKEN/GITHUB_TOKEN or run \`gh auth login\``, exit 1.
- **Create:** `POST /repos/{o}/{r}/pulls` with `title`, `head`, `base` and `draft`, plus `body` only when it is non-empty. Strings go as JSON, so `&` stays `&`. Then print `platform=github`, `pr_url=` (`html_url`) and `pr_number=`.
- **Labels:** `POST /issues/{n}/labels`, then one `tag_added=` per tag. If this call fails, exit 1 after the PR lines (as in TS).
- **Reviewers:** optional and required reviewers merged and deduped. If any were required, print the TS note that GitHub has no per-PR required reviewer. `POST /pulls/{n}/requested_reviewers`, then one `reviewer_added=<login>` each. On failure, print `>> WARNING: requesting reviewers failed (...); PR is open without them` and exit 0.
- **Other output:** `--related`, if passed, prints its TS NOTE (Azure-only). An API failure prints `ship-pr failed: <status and message>` and exits 1. The help output exits 0.
- **Requests:** `Authorization: Bearer <token>`, `Accept: application/vnd.github+json`, `X-GitHub-Api-Version` and a `User-Agent: ship/<version>`. The base URL is `SHIP_GITHUB_API_URL`, default `https://api.github.com`, a seam for tests and GitHub Enterprise.
- **Reuse:** the stdout/BrokenPipe handling and the exit-code plumbing from `push`.

**Never:**
- **Token:** never in output, the URL, logs or files.
- **Content:** add nothing to the title or body (no AI attribution, NFR4).
- **Scope:** no Azure create path or Azure-only flags (`--work-item`, `--task`, `--transition`, …); they arrive in Stories 3.2-3.6. No change to `scripts/*.ts`, `package.json` or `SKILL.md`.
- **Dependencies:** no async runtime and no OpenSSL. Dependencies beyond `ureq` and `serde_json` need a reason in `HTTP-CLIENT.md`.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Typed title | `--title "docs(finops): x"` | labels `docs`,`finops`; NOTE line; `tag_added=docs`, `tag_added=finops` | N/A |
| Branch prefix | title `update x`, branch `fix/y` | label `fix`; NOTE names the prefix | N/A |
| Fallback | untyped title, branch `y` | `needs-review` + WARNING | N/A |
| Explicit / none | `--tag "hotfix, wip,hotfix"` / `--no-tag` | `hotfix`,`wip` once each / no labels call | N/A |
| Reviewers | `--reviewer a,b --required-reviewer c` | one requested-reviewers call; three `reviewer_added=`; GitHub note | call fails → WARNING, exit 0 |
| Draft + literal | `--draft`, title `a & b`, body file | JSON carries `draft:true`, title `a & b`, body verbatim | N/A |
| Empty body | no body | `body` omitted from the create JSON | N/A |
| Token order | env set / unset with `gh` stub | env wins; else `gh auth token -u <owner>`; else `gh auth token` | none → exit 1 |
| Create fails | API 422/404 | no PR lines | `ship-pr failed: …`, exit 1 |
| Not GitHub | azure / unknown remote | nothing created | exit 1 with the messages above |

</frozen-after-approval>

## Code Map

- `skills/ship/scripts/ship-pr.ts` L107-210, L407-447 -- reference for GitHub-relevant flags, tag defaulting, NOTE/WARNING wording and the GitHub flow. The Azure parts are out of scope.
- `skills/ship/scripts/ship-lib.ts` -- port `parseTags`, `defaultTagsFromTitle` and `githubToken`. `githubOwnerRepo` already exists in Rust as `github_owner_repo`. Port the `ship-lib.test.ts` groups for `parseTags` and `defaultTagsFromTitle` (L101-120) 1:1.
- `skills/ship/src/lib.rs`, `src/git.rs`, `src/push.rs` -- `detect_kind`, `github_owner_repo`, `current_branch`, `remote_url`, ref validation. New HTTP code lives in its own module (e.g. `src/http.rs` or `src/github.rs`) so that Story 3.2 adds `azure.rs` beside it.
- `skills/ship/Cargo.toml` -- add `ureq` 3 (rustls default) and `serde_json`. Run `cargo update`, commit `Cargo.lock`, and keep `--locked` CI green.
- `.github/workflows/ship-release.yml` -- `ring` (via rustls) compiles C for `x86_64-unknown-linux-musl`. If the musl job fails for want of a musl C toolchain, add `sudo apt-get install -y musl-tools` to that matrix leg only. This PR's own run is the proof.
- Tests need no network: a mock HTTP server on `127.0.0.1` in the integration tests (std `TcpListener`, no new dev-dependency unless justified) records each request's method, path, headers and JSON body. Point `SHIP_GITHUB_API_URL` at it, and stub `gh` on `PATH` for the token-order rows.
- Parity: a scratchpad copy of `ship-pr.ts` with `new Octokit({ auth, baseUrl: process.env.SHIP_GITHUB_API_URL })`, run against the same mock, compares stdout, the `>>` lines, the exit code and the captured request bodies. Never edit the repo's `scripts/*.ts`.
- `_bmad-output/implementation-artifacts/sprint-status.yaml` -- 2-2 → `done` (PR #25 merged), epic-2 → `done`.

## Tasks & Acceptance

**Execution:**
- [x] `skills/ship/HTTP-CLIENT.md` -- decision record: choice, candidates with versions/dates, reason, musl note -- AC
- [x] `skills/ship/Cargo.toml`, `Cargo.lock` -- `ureq`, `serde_json`
- [x] `skills/ship/src/lib.rs` -- `parse_tags`, `default_tags_from_title`, branch-prefix map, with the TS test cases
- [x] `skills/ship/src/github.rs` (+ token helper in `git.rs` or `github.rs`) -- token order, create, labels, reviewers
- [x] `skills/ship/src/pr.rs`, `src/main.rs` -- `pr` subcommand, flag parsing, tag/reviewer defaulting, dispatch
- [x] `skills/ship/tests/pr.rs` -- mock-server tests for every matrix row
- [x] `.github/workflows/ship-release.yml` -- `musl-tools` only if the musl build needs it
- [x] `_bmad-output/implementation-artifacts/sprint-status.yaml` -- 2-2 → `done`, epic-2 → `done`

**Acceptance Criteria:**
- Given each matrix row run against the mock server with both `ship pr` and the scratchpad TS copy, then stdout, the `>>` lines, the exit code and the request JSON match. The exception is the error text on API failures, where Octokit's wording differs; the exit code still matches.
- Given a stub token `SECRET-TOKEN-123`, then it appears only in the mock's `Authorization` header, never in stdout, stderr or a URL.
- Given this story's PR, then `ship-rust` CI and both `ship-release` builds (musl and macOS) pass with the new dependencies.

## Implementation Notes

- New `HTTP-CLIENT.md`, `src/github.rs`, `src/pr.rs`, `tests/pr.rs`; `lib.rs` gains `parse_tags`, `default_tags_from_title`, `tag_from_branch_prefix`, `parse_related_ids` (exact port). Dependencies: `ureq` 3 (rustls, `platform-verifier`) and `serde_json`; `cargo tree` has no tokio, reqwest, hyper or OpenSSL link (`openssl-probe` only locates CA bundle paths). `ship-release.yml` installs `musl-tools` on the musl leg (ring needs a musl C compiler).
- Parity: scratchpad copy of `ship-pr.ts` with `baseUrl: process.env.SHIP_GITHUB_API_URL`, same mock server, 16 cases (typed title, branch prefix, fallback, explicit tags, `--no-tag`, reviewers, reviewer failure, draft + literal `&`, empty body, create 422/404, label failure, `--related`, unknown remote, missing title, `--source`). 16/16 match on stdout, `>>` lines, exit code and request JSON; API-failure wording differs as allowed. Rerun after review patches: 16/16.
- Review fixes, verified: token refused for a non-https, non-loopback base URL; OS trust store via `RootCerts::PlatformVerifier` (musl binary +36,864 bytes); a closed stdout no longer skips labels/reviewers; `--related` parsing ported exactly; tests for `errors[]` detail, token precedence, missing `--body-file`; hermetic helpers.
- Real TLS check with the platform verifier: `ship pr` with an invalid token against `api.github.com` returned `HTTP 401: Bad credentials` (handshake OK, nothing created).
- Verified: `cargo test` 64 + 7 + 34 + 14 + 17 + 18 green on two runs; clippy `-D warnings` clean. Owed to this PR's CI: the musl and macOS release builds with the new dependencies.

## Spec Change Log

## Review Triage Log

Pass 1 (blind-hunter BH, edge-case-hunter EC, verification-gap VG).

| # | Finding | Verdict | Evidence | Route |
|---|---|---|---|---|
| 1 | BH2/EC12: `SHIP_GITHUB_API_URL=http://…` sends the Bearer token in cleartext | medium | New surface from this change; any base URL accepted. Require https except loopback. | patch |
| 2 | BH4: ureq's bundled roots ignore the OS trust store | medium | This host has corporate root CAs installed (`/usr/local/share/ca-certificates`); GitHub is not intercepted here (issuer Sectigo), but on an inspecting network every call would fail. Platform verifier fixes it. | patch |
| 3 | BH1/EC10/EC11: Enterprise claimed but `gh auth token` has no `--hostname` | low | Claim is in `HTTP-CLIENT.md` only; owner/repo parsing already needs a "github" host. Doc correction. | patch |
| 4 | BH8: doc says error text is status + message only; code appends `errors[]` | low | Doc correction. | patch |
| 5 | EC8: closed stdout after create skips labels and reviewers | medium | `writeln!` BrokenPipe returns early; `main` maps it to exit 0. TS `console.log` never aborts. Introduced here. | patch |
| 6 | VG-other: `parse_related_ids` accepts `AB34`/`012`, skips `AB`/`#` | low | Diverges from `parseRelatedIds` (ship-lib.ts:266-276), which exits 2. Port exactly. | patch |
| 7 | VG1/VG2/VG3/BH12: untested `errors[]` detail, token precedence, unreadable `--body-file` | medium | No mock returns `errors`; no test sets competing token sources; no missing-file case. Test-only. | patch |
| 8 | BH12/EC17/EC18: two tests bypass the hermetic helper | low | Ambient `SHIP_PLATFORM`/tokens change results. Test-only. | patch |
| 9 | BH6/EC15: any `Word:` title becomes a label (`WIP:` → `wip`) | low | Same regex as TS `defaultTagsFromTitle`; parity. Restricting types changes labels vs TS. | defer |
| 10 | EC3: `--source owner:branch` (cross-fork head) rejected by the ref check | low | Spec routes `--source` through the shared validation; fork PRs are outside the ship flow (push to own remote). | reject |
| 11 | EC16: branch `fix` with no slash counts as prefix `fix/` | false | TS `split("/")[0]` does the same; NOTE text identical (parity run). | reject |
| 12 | EC6/BH7: `--no-tag` with `--tag`, `--no-reviewer` no-op on GitHub | low | Same as TS. | reject |
| 13 | EC7: Azure/unknown read `--body-file` and print the tag NOTE first | low | Same order as TS. | reject |
| 14 | BH5/EC1/EC2/EC4/EC5: existing-PR 422, unpushed branch, detached HEAD, source==target, blank title/target | low | All end in a 422/exit 1 like TS; detached HEAD carried from Story 1.1. | reject |
| 15 | EC9: `org/team` reviewers sent as users | low | Same as TS; warns and exits 0. | reject |
| 16 | EC13: GH_TOKEN with whitespace | low | Same as TS `process.env.GH_TOKEN ||`. | reject |
| 17 | BH3: `gh auth token -u <owner>` misses for org repos | low | Same as TS; falls back to the active account. | reject |
| 18 | BH9: no retry on rate limits/5xx, no `gh` timeout | low | Same as TS. | reject |
| 19 | BH10: double `parse_related_ids`, `"needs-review"` sentinel, `serde_json` pin | low | Cosmetic. | reject |
| 20 | BH11: CI does not assert the musl binary is static or its size | low | Static-pie confirmed manually in Story 1.3; no defect. | reject |
| 21 | BH13: Story 2.2 moved to `done` without review | false | Story 2.2 spec carries a 12-row review triage log; PR #25 merged. | reject |

## Verification

**Commands:**
- `cargo test --manifest-path skills/ship/Cargo.toml` -- expected: all green
- `cargo clippy --manifest-path skills/ship/Cargo.toml --all-targets -- -D warnings` -- expected: clean
- parity run against the patched scratchpad TS copy and the mock server -- expected: identical per the AC
- this PR's CI -- expected: `ship-rust` and both `ship-release` builds green
