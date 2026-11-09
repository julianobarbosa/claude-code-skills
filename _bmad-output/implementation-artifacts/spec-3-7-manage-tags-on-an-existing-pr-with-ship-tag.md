---
title: 'Story 3.7: Manage tags on an existing PR with ship tag'
type: 'feature'
created: '2026-11-09'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: 'c63ddb969f446f44c3f656ff4a55109bc7ebdc86'
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-3-context.md'
  - '{project-root}/skills/ship/HTTP-CLIENT.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** The binary has no `ship tag`, so changing a PR's tags or labels after review starts still needs bun and `ship-tag.ts`.

**Approach:** Port `ship-tag.ts` as `ship tag`: add, remove and list tags on an Azure PR (`pr_id`) or GitHub labels on a PR (`pr_number`). It reuses the platform detection, credentials and HTTP clients from `ship pr`.

## Boundaries & Constraints

**Always:**
- **Args (TS parity):**
  - The PR id is a digits-only positional or `--pr <id>`.
  - `--add`/`--remove` are repeatable and comma-separated, through `parse_tags`.
  - `--list` is the default when there is nothing to add or remove.
  - `-r/--remote` defaults to `origin` and is checked with `validate_target(remote, None)`, exit 2.
  - With no id: exit 2 `a pull request id is required (positional or --pr)`. An unknown or extra arg exits 2.
- **Order:** adds, then removes, then the list.
  - An add failure is fatal: exit 1 `ship-tag failed: <err>`.
  - A remove failure prints stderr `>> could not remove '<name>': <err>`, the loop goes on, and the run exits 0.
  - The list prints `platform=<azure|github>`, then one tag name per line.
- **Azure** (`{org}/{project}/_apis/git/repositories/{repo}/pullRequests/{id}/labels`, api-version 7.1):
  - Add: one `POST` per tag, body `{"name":<tag>}`, then `tag_added=<tag>`.
  - Remove: `DELETE …/labels/<enc(name)>`, then `tag_removed=<tag>`.
  - List: `GET`, the names from `value[].name`.
  - Credential order, the fallback line and the 203/3xx rule are the same as `ship pr`. With no credential: exit 1 with the TS message.
- **GitHub** (issues API):
  - Add: one `POST issues/{n}/labels` with every tag. GitHub creates a missing label. Then one `tag_added=` line per tag.
  - Remove: `DELETE issues/{n}/labels/<enc(name)>`.
  - List: `GET issues/{n}/labels`, first page only, as TS.
  - The token comes from `github::token(owner)`. With none: exit 1 with the TS message.
- **Azure 404 (approved deviation, Barbosa 2026-11-09, option B):**
  - The TS reports a 404 as success, because `typed-rest-client` resolves it. Rust treats a 404 like any other error instead.
  - A 404 on an add or on the list exits 1 with `ship-tag failed: HTTP 404…`.
  - A 404 on a remove prints the could-not-remove warning.
  - The TS bug is logged in `deferred-work.md`, not fixed there.
- Re-adding a tag that is already on the PR succeeds.
- An unknown platform exits 1 with the TS `unknown platform … set SHIP_PLATFORM=azure|github` message.
- Credentials appear only in `Authorization` headers.

**Never:** No change to `scripts/*.ts`, `package.json`, `SKILL.md` or `ship pr` output. No new dependencies.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Azure add | `ship tag 9 --add "a,b" --add a` | two POSTs; `tag_added=a`, `tag_added=b` | N/A |
| Azure list default | `ship tag 9` | `platform=azure`, then names | N/A |
| Remove missing | GitHub DELETE answers 404 | `>> could not remove 'x': HTTP 404…` | exit 0 |
| Add then list | `--add hotfix --list` | `tag_added=hotfix`, then `platform=…` and the list | N/A |
| GitHub add | `ship tag 7 --add new-label` | one POST `{"labels":["new-label"]}`; `tag_added=new-label` | N/A |
| Add fails | POST answers 500 | `ship-tag failed: HTTP 500…` | exit 1 |
| No id | `ship tag --add a` | no request | exit 2 |
| Fallback | bearer answers 401, PAT works | TS fallback line; later calls use the PAT | N/A |
| Azure 404 | a label POST or GET answers 404 | `ship-tag failed: HTTP 404…`, no `tag_added=` | exit 1 |

</frozen-after-approval>

## Code Map

- `skills/ship/scripts/ship-tag.ts` is the reference for flags, output and error text.
- `skills/ship/src/main.rs`: add the `Tag` subcommand. Shape: positional `Option<String>`, `--pr`, `--add`/`--remove` as `Vec` with `allow_hyphen_values`, `--list`, `-r/--remote` with default `origin`. Dispatch it to `ship::tag::run`.
- `skills/ship/src/tag.rs` (new):
  - Parse into pure pieces (id, add, remove, list), with unit tests.
  - Detect the platform with `git::remote_url` + `detect_kind` + `SHIP_PLATFORM`, as `pr.rs::run` does.
  - The Azure and GitHub flows. Use the `fail(msg, code)` pattern from `pr.rs`.
- `skills/ship/src/lib.rs`: `pub mod tag;`.
- `skills/ship/src/azure.rs`:
  - Add `Method::Delete` and a GET path in `once`.
  - Add `add_pr_label`, `remove_pr_label` and `list_pr_labels` through `send_as`. Reuse `api_error` and the credential fallback.
  - Keep `send`'s GET-when-no-payload behaviour for the existing callers.
- `skills/ship/src/github.rs`: generalise `post` into `send(method, url, Option<&Value>)`. Add `remove_label(number, name)` and `list_labels(number) -> Vec<String>`. Reuse `add_labels` as it is.
- `skills/ship/tests/tag.rs` (new):
  - Use a mock server, a stub `az`/`gh` and scratch repos, copied from the `tests/pr.rs` and `tests/pr_azure.rs` harnesses. Those harnesses are per-file, so there is no shared module.
  - Cover every matrix row, a secrecy assertion (`TOKEN`/`PAT` absent from stdout/stderr) and the request paths and bodies.
- `skills/ship/HTTP-CLIENT.md`: rows for the three Azure label calls and the GitHub remove and list calls.
- `_bmad-output/implementation-artifacts/sprint-status.yaml`: set 3-6 to `done` (PR #31 merged) and 3-7 to the build statuses.

## Tasks & Acceptance

**Execution:**
- [x] `skills/ship/src/azure.rs` -- DELETE support plus the three label calls -- the Azure API surface
- [x] `skills/ship/src/github.rs` -- the generic send, `remove_label`, `list_labels` -- the GitHub API surface
- [x] `skills/ship/src/tag.rs`, `lib.rs`, `main.rs` -- the `ship tag` command with arg-parse unit tests -- FR10
- [x] `skills/ship/tests/tag.rs` -- matrix rows, secrecy, paths and bodies -- proof of parity
- [x] `skills/ship/HTTP-CLIENT.md` -- endpoint rows -- keep the decision record current
- [x] `_bmad-output/implementation-artifacts/sprint-status.yaml` -- 3-6 to `done`
- [x] `_bmad-output/implementation-artifacts/deferred-work.md` -- log the TS Azure-404 bug (deviation B)

**Acceptance Criteria:**
- Given an Azure remote and `ship tag 9 --add hotfix --remove wip --list`, then stdout is exactly `tag_added=hotfix`, `tag_removed=wip`, `platform=azure`, then the mock's names.
- Given a GitHub remote and `ship tag --pr 7 --remove gone` where the DELETE answers 404, then the exit code is 0 and stderr carries the could-not-remove line.
- Given `cargo test` and `cargo clippy --all-targets -- -D warnings`, then both pass and every existing test still passes.

## Implementation Notes

- Done by a Sonnet subagent, then checked by the lead against the diff. `cargo test` gives 278 passed (86/7/35/73/14/17/18/24), and clippy `-D warnings` is clean. Only tested against local mocks, never a real Azure DevOps org or GitHub repo.
- `src/azure.rs`: `Method` now has `Get` and `Delete`. `once` dispatches on the method. `send` picks GET when there is no payload, so existing callers are unchanged. Added `add_pr_label`, `remove_pr_label`, `list_pr_labels` and a pure `label_names`.
- `src/github.rs`: `post` now goes through a generic `send(method, url, payload)`. Added `remove_label` and `list_labels`.
- `src/tag.rs`:
  - A pure `plan()` with unit tests, then the Azure and GitHub flows.
  - A private `Out` writer, so a closed stdout does not skip the adds and removes. It is copied from `pr.rs` so that `pr.rs` stays untouched.
- Arg edge cases, chosen within "digits-only id":
  - A non-digit `--pr` exits 2 with `invalid pull request id: <v>`. The TS would send `NaN` to the API. Here the id also never reaches the URL path.
  - A positional id plus `--pr`: `--pr` wins, as TS `7 --pr 5` does. Review fix #5. TS rejects `--pr 5 7`, but Rust accepts it, because clap cannot see flag order.
- Review patches (triage #1-8) applied by the same subagent, then verified by the lead: `cargo test` gives 283 passed (87/7/35/73/14/17/18/32), and clippy is clean.
- Lead fix: the new Azure rows in `HTTP-CLIENT.md` sat after a blank line, which broke the table. They now join the existing table.
- `cargo fmt --check` already fails on existing code, so formatting was left alone.

## Spec Change Log

## Review Triage Log

Pass 1 used three Opus reviewers: blind-hunter (BH), edge-case-hunter (EC) and verification-gap (VG).

| # | Finding | Verdict | Evidence | Route |
|---|---|---|---|---|
| 1 | VG1: no test closes stdout, so the `Out` keep-going behaviour is unproven | low | Every `tests/tag.rs` run uses `.output()`, so stdout stays open. The fix is one test. | patch |
| 2 | VG2: a GitHub list answering 2xx with a non-array body is untested | low | The only list-failure test uses a 404, which errors before the array check. The fix is one test. | patch |
| 3 | BH2: an Azure DELETE answering 204 with an empty body is untested | low | The empty body parses to `Null` and 204 passes `200..300`, so this should work, but nothing proves it. The fix is one test. | patch |
| 4 | BH3: a partial add failure is untested | low | Both add-failure tests fail on the first POST. The fix is one test. | patch |
| 5 | BH4/EC5: `7 --pr 5` exits 2, but TS runs on PR 5 | medium | Confirmed in `plan`: the `(Some, Some)` arm errors. The spec asks for TS arg parity, and the deviation was never approved. Fix: `--pr` wins. TS still errors on `--pr 5 7`; Rust accepts it, because clap cannot see flag order. | patch |
| 6 | EC6: `--list --list` exits 2, but TS accepts it | low | Clap rejects a repeated bool flag. The fix is `overrides_with`. | patch |
| 7 | EC1: `--remove .` or `--remove ..` sends `DELETE …/labels/.` | medium | `http::enc` keeps dots. A server that normalizes the path could read this as `DELETE issues/{n}/labels`, which on GitHub removes every label. Fix: skip such a name with a warning. | patch |
| 8 | BH13: GitHub cleartext-seam refusal and secrecy asserts are missing | low | Only the Azure seam is tested, and three GitHub tests skip `no_secrets`, which the spec requires. | patch |
| 9 | BH1: re-adding an existing tag is not verified against real Azure | maybe-false | The mock answers 200 to every POST. Settling it needs a real org; if ADO answers 409, the AC fails. | defer |
| 10 | BH7: the GitHub list reads only the first page (30) | low | This is TS parity and is pinned by the frozen spec. It is a pre-existing TS behaviour. | defer |
| 11 | BH5: clap error text differs from TS `unknown arg` | low | Exit codes match. `ship pr` uses clap the same way, so this is crate-wide precedent. The fix would add custom parsing. | reject |
| 12 | BH6: `--remove --list` makes `--list` a tag | low | TS `take()` does the same, so this is parity. | reject |
| 13 | BH8: GitHub list does not drop empty names | false | TS GitHub prints every `l.name` without a filter, and GitHub rejects empty label names. | reject |
| 14 | BH9: `Out` is duplicated from `pr.rs` | low | Drift between two private copies is possible but has no named harm. Extracting it is a refactor across `pr.rs`. | reject |
| 15 | BH10: `github::send` repeats its headers, and `post` lost its doc comment | low | This is cosmetic. | reject |
| 16 | BH11: `SKILL.md` still documents `bun ship-tag.ts` | false | Epic 5 Story 5.2 owns the `SKILL.md` switch, and the spec freezes `SKILL.md`. | reject |
| 17 | BH12: new files are not rustfmt-clean | low | `cargo fmt --check` is not enforced in the crate. | reject |
| 18 | BH14: the 3-6 `done` claim is unsupported, and the status words differ | false | `origin/main` HEAD c63ddb969f446f44c3f656ff4a55109bc7ebdc86 is "Merge pull request #31 … 3-6-related-links". `in-review` and `review` are each workflow file's own word. | reject |
| 19 | VG-other: a POST or PATCH with no payload sends an empty body | low | No caller does this. It is only a trap for future code. | reject |
| 20 | EC2: a GUID-shaped tag name may be read as a label id on Azure | maybe-false | It would need a tag named like a GUID; if true it is low. | reject |
| 21 | EC3: `eprintln!` panics when stderr is closed | low | This pattern is pre-existing across the crate (`pr.rs`), and the case is rare. | reject |
| 22 | EC4: the same tag in `--add` and `--remove` is added then removed | false | TS does the same, the output reports both, and the order is the spec's. | reject |

## Verification

**Commands:**
- `cargo test --manifest-path skills/ship/Cargo.toml` -- expected: all green
- `cargo clippy --manifest-path skills/ship/Cargo.toml --all-targets -- -D warnings` -- expected: clean
