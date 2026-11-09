---
title: 'Story 3.5: Transition work items on open and on completion'
type: 'feature'
created: '2026-11-09'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: '167bf4358de7352b5de054e8f2bf2b643102f859'
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-3-context.md'
  - '{project-root}/skills/ship/HTTP-CLIENT.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** On Azure, `ship pr` leaves the Board untouched after the PR opens. The PR's "Complete linked work items after merging" box is never pre-checked, and there is no `--transition`, so linked items stay open behind a merged PR.

**Approach:** Port the two TS post-create steps:
1. Always PATCH the PR's `completionOptions.transitionWorkItems`: `true` by default, an explicit `false` with `--no-complete-transition`. Print the value the response carries.
2. With `--transition <state>`, PATCH each linked or created item's `System.State`.

Both steps are best-effort, so the PR is never failed after it exists.

## Boundaries & Constraints

**Always:**
- **New flags:** `--transition <state>` and `--no-complete-transition`. Both are accepted and ignored on GitHub, with no output.
- **Order after `work_items=`:** the completion PATCH, then the transitions, then the existing `tag_added=` and `reviewer_added=` lines (TS L376-404).
- **Completion PATCH:**
  - Request: `PATCH {org}/{project}/_apis/git/repositories/{repo}/pullrequests/{pr_id}?api-version=7.1`, `Content-Type: application/json`, body `{"completionOptions":{"transitionWorkItems":<bool>}}`.
  - It runs on every Azure PR, with or without linked items (TS parity).
  - Output: `complete_transitions_work_items=<v>`, where `<v>` is the response's `completionOptions.transitionWorkItems` as `true`/`false`, or `unset` when that field is absent, null or not a boolean.
  - Failure (non-2xx, transport error, or every credential rejected): stderr `>> WARNING: could not set "complete linked work items" to <bool> on PR <id>: <err>`, then stdout `complete_transitions_work_items=unset`.
- **Transition:** only when `--transition` is non-empty and at least one item is linked. For each linked id, in order:
  - stderr: `>> transitioning work item <id> -> <state>`
  - Request: `PATCH {org}/{project}/_apis/wit/workitems/{id}?api-version=7.1`, `Content-Type: application/json-patch+json`, body `[{"op":"add","path":"/fields/System.State","value":<state>}]`.
  - On success, stdout: `work_item=<id> state=<state>`.
  - On failure, stderr `>> WARNING: could not transition work item <id> -> <state>: <err>`, and the loop continues.
- **Auth:** both PATCHes use the client's credential and fallback, like every other call. A transition with no linked items is skipped silently.
- **Exit code:** 0 once the PR is created, whatever these steps report. Credentials appear only in the `Authorization` header.

**Never:**
- Echo the flag as the printed completion value, or put `completionOptions` in the create payload (ADO drops it).
- Fail the run or skip tags and reviewers because a PATCH failed.
- Scope creep: no `--related` work (Story 3.6), no `ship tag`, no GitHub behavior change. No change to `scripts/*.ts`, `package.json` or `SKILL.md`. No new dependencies.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Default | linked item 42, no flags | PATCH body `transitionWorkItems:true`; `complete_transitions_work_items=true` after `work_items=42`, before `tag_added=` | N/A |
| Opt out | `--no-complete-transition` | PATCH body `false`; prints the response value | N/A |
| Read back | response with `completionOptions: null` | `complete_transitions_work_items=unset` | N/A |
| PATCH fails | PR PATCH answers 500 | WARNING; `=unset`; tags and reviewers still print | exit 0 |
| Transition | `--transition Resolved`, items 501, 502 | two json-patch PATCHes in order; `work_item=501 state=Resolved`, `work_item=502 state=Resolved` after the completion line | N/A |
| Bad state | the 501 PATCH answers 400 | WARNING for 501; 502 still transitions | exit 0 |
| No items | `--transition Resolved`, nothing linked | no transition request or line; completion PATCH still sent | N/A |
| Auth fallback | bearer 401 on a PATCH, PAT set | fallback line; the PATCH is retried with the PAT | N/A |
| GitHub | `--transition X --no-complete-transition` | output and requests unchanged | N/A |

</frozen-after-approval>

## Code Map

- `skills/ship/scripts/ship-pr.ts` L35-36 and L53-62 (flag docs), L348-398 (completion PATCH and transition loop): the reference for messages and order.
- `skills/ship/src/azure.rs`:
  - `send`/`once` handle only GET (no payload) and POST today. Add a method argument (or a PATCH variant) so PATCH reuses the same fallback, headers and redirect rules; existing callers keep their methods.
  - Add `set_complete_transition(pr_id, bool) -> Result<Option<bool>, String>` (`None` = unset) and `transition_work_item(id, state) -> Result<(), String>`. Both use `api_error` for non-2xx.
  - The project and repo are encoded with `http::enc`, as in `create_pr`.
- `skills/ship/src/pr.rs`:
  - `Args` gains `transition: Option<String>` and `no_complete_transition: bool`.
  - In `run_azure`, insert both steps between the `work_items=` line and the `tag_added=` loop, writing through `out`.
  - Update the `run_azure` doc comment. Keep the `--related` guard.
- `skills/ship/src/main.rs`: add the two flags to `Pr` (Azure-only doc strings, `allow_hyphen_values` on `--transition`) and pass them through.
- `skills/ship/tests/pr_azure.rs`:
  - In the `happy` mock, add a PATCH route for `/pullrequests/` that echoes the body's `completionOptions`, and a PATCH route for `/_apis/wit/workitems/` that answers 200.
  - Update every existing exact-stdout assertion for the new `complete_transitions_work_items=true` line.
  - Cover every matrix row, plus a secrecy check on the PATCH requests.
- `skills/ship/tests/pr.rs` (GitHub): add one test showing the two flags change nothing.
- `skills/ship/HTTP-CLIENT.md`: add rows for the two PATCH endpoints.
- `_bmad-output/implementation-artifacts/sprint-status.yaml`: 3-4 → `done` (PR #29 merged).

## Tasks & Acceptance

**Execution:**
- [x] `skills/ship/src/azure.rs` -- PATCH support in `send`/`once`; `set_complete_transition`, `transition_work_item`; unit tests for the read-back mapping
- [x] `skills/ship/src/pr.rs` -- new `Args` fields; completion and transition steps in TS order
- [x] `skills/ship/src/main.rs` -- `--transition`, `--no-complete-transition`
- [x] `skills/ship/tests/pr_azure.rs` -- PATCH mock routes; matrix rows; adapt the exact-stdout tests
- [x] `skills/ship/tests/pr.rs` -- GitHub ignores both flags
- [x] `skills/ship/HTTP-CLIENT.md` -- document both PATCH endpoints
- [x] `_bmad-output/implementation-artifacts/sprint-status.yaml` -- 3-4 → `done`

**Acceptance Criteria:**
- Given item 42 linked, `--transition Resolved` and tag `feat`, when the PR opens, then stdout is exactly `platform=azure`, `pr_id=9`, `pr_url=…`, `work_items=42`, `complete_transitions_work_items=true`, `work_item=42 state=Resolved`, `tag_added=feat`.
- Given a mock that answers the completion PATCH with `transitionWorkItems:false` while the flag asked for true, then stdout prints `false`, proving the value is read back.
- Given `cargo test` and `cargo clippy --all-targets -- -D warnings`, then both pass and every existing test still passes.

## Implementation Notes

- `azure.rs`: a private `Method { Post, Patch }` goes through `send_as`/`once`. `send` stays POST, a call without a payload stays GET, and the fallback, headers and redirect rules are shared. New: `set_complete_transition` returns `Option<bool>` (`None` = unset), plus `transition_work_item`, `read_back_transition` and `state_patch`, with unit tests for the read-back mapping. `pr.rs`: both steps sit between `work_items=` and `tag_added=`, best-effort.
- Tests: every exact-stdout and path assertion on the Azure path now includes the completion PATCH. Tests that read "the last request" now read the PR create through `pr_create`, because the last request is now the PATCH (the old form would pass vacuously on the PATCH body). Ten new Azure tests cover the matrix, and one GitHub test shows the flags are inert.
- Process note: the Sonnet implementer stopped before finishing (tests and docs incomplete, no report). The lead finished the work. A crate-wide `cargo fmt` was run by mistake and undone (the crate is not rustfmt-clean, and CI runs clippy only), so the diff carries only this story's changes.
- Verified: `cargo test`, 75 + 7 + 34 + 60 + 14 + 17 + 18 after the review patches (57 before them, green on two runs). Clippy `-D warnings` is clean. `scripts/*.ts`, `package.json`, `SKILL.md`, `Cargo.toml` and `Cargo.lock` are untouched. Not run against a real Azure DevOps org.

## Spec Change Log

## Review Triage Log

Pass 1: blind-hunter (BH), edge-case-hunter (EC), verification-gap (VG). VG found no verification gaps.

| # | Finding | Verdict | Evidence | Route |
|---|---|---|---|---|
| 1 | EC1: `--transition`/`--no-complete-transition` given twice exits 2 | low | Confirmed on the built binary; TS takes the last value. Direct fix: `overrides_with` on both. Test added. | patch |
| 2 | EC2/BH10: whitespace or padded state sent untrimmed | low | `filter(!is_empty)` only; `--work-item` is trimmed. Direct fix: `map(str::trim)`. Test added. | patch |
| 3 | BH2/BH3: no test where every credential is rejected on the PATCHes | low | The "never fail after create" promise had no test on the auth-exhausted path. Test added (401 on every PATCH, bearer then PAT). | patch |
| 4 | BH5: `send`/`send_as` doc comments describe the wrong function | low | The fallback loop moved into `send_as`, but its comment stayed on `send`. Comments moved. | patch |
| 5 | BH6: the reason for the explicit `false` was dropped in the port | low | Without it, a maintainer could skip the PATCH when `want == false` and re-open the PR 1347 bug. Comment carried over. | patch |
| 6 | BH7: HTTP-CLIENT auth paragraph says every rejection fails the run | low | The two PATCHes warn instead. Qualifier added. | patch |
| 7 | BH8: table rows after blank lines do not render as a table | low | The 3.3, 3.4 and new rows were separated by blank lines. Rows joined. | patch |
| 8 | BH13: new tests in rustfmt's narrow style, unlike the file | low | The block was re-wrapped at width 120; it fell from about 320 diff lines to about 240. | patch |
| 9 | BH4: `Method::Patch` with no payload would silently send a GET | low | No caller does this; the fix adds a variant and branches. Unlikely in everyday use. | reject |
| 10 | BH9: `allow_hyphen_values` lets `--transition` swallow the next flag | low | Same as TS (`argv[++i]`) and every other value flag in the crate. | reject |
| 11 | BH11: a per-item 403 moves the client to the PAT for good | maybe-false | The same design as TS `authFallback` and Story 3.4 #6; whether ADO answers 403 per item needs a real org. Low if true. | reject |
| 12 | BH12: the read-back is not checked against a real ADO response | false | TS reads the same `upd.completionOptions.transitionWorkItems` in production (PR 1050 and 1347 history), so the response shape is evidenced. | reject |
| 13 | BH1: sprint-status 3-5 is `in-progress` while the spec is `in-review` | false | Workflow order: step 5 sets sprint `review`. | reject |
| 14 | BH14: clippy claim unchecked | false | The lead ran clippy `-D warnings` clean after the last edit (transcript). | reject |
| 15 | EC1 (broader): every other single-value `pr` flag also exits 2 when repeated | low | Not caused by this story. | defer |
| 16 | EC note: a cross-project linked item could pass the org-scoped read, then fail the project-scoped PATCH | maybe-false | The same as TS; the outcome is only a warning. | reject |

## Verification

**Commands:**
- `cargo test --manifest-path skills/ship/Cargo.toml` -- expected: all green
- `cargo clippy --manifest-path skills/ship/Cargo.toml --all-targets -- -D warnings` -- expected: clean
