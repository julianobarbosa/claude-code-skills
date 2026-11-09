---
title: 'Story 3.3: Create and assign work items when none exist'
type: 'feature'
created: '2026-11-08'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: 'a194d881d96297d41ca40fe74856b80859c02b3e'
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-3-context.md'
  - '{project-root}/skills/ship/HTTP-CLIENT.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** When an Azure branch has no verifiable work item, `ship pr` currently refuses with exit 1 (Story 3.2's guard). The TS script creates one item per task instead, so the operator is never asked for an id.

**Approach:** Replace the guard with the TS creation path. Create one work item from the PR title, or one per `--task`/`--tasks-file` line. Assign each to `--assignee`/`SHIP_ADO_ASSIGNEE` and link them all to the PR in its create call. Print the ids the API returned.

## Boundaries & Constraints

**Always:**
- **New flags:** `--task <title>` (repeatable), `--tasks-file <f>` (one title per line, trimmed, blank lines skipped, appended after the `--task` values), `--assignee <upn>` and `--work-item-type <type>` (default `Task`).
- **Assignee:** `--assignee`, else `SHIP_ADO_ASSIGNEE`, else the TS default `you@example.com`. An empty value means unassigned.
- **Unreadable `--tasks-file`:** `cannot read --tasks-file <f>: <err>`, exit 1, before any request.
- **Branch inference:** skipped whenever any task is given (TS L165), so a number in the branch never preempts explicit tasks.
- **Resolution:**
  - **Existing item** (`--work-item`, or the inferred id): verify and link it, as in Story 3.2.
  - **Otherwise, unless `--no-create-work-item`:** create one item per task, or one from the PR `--title` when no task was given. This includes a `--work-item` or inferred id that is not found.
  - **With `--no-create-work-item`:** Story 3.2's behavior is unchanged.
- **Create call:** `POST {org}/{project}/_apis/wit/workitems/${type}?api-version=7.1` with `Content-Type: application/json-patch+json`. The body is `[{op:"add",path:"/fields/System.Title",value:<t>}]`, plus `{op:"add",path:"/fields/System.AssignedTo",value:<assignee>}` when the assignee is non-empty.
  - **Encoding:** the project and the `$type` segment are percent-encoded (`User Story` → `%24User%20Story`).
  - **Auth:** the same credentials and fallback as Story 3.2.
- **Per created item:**
  - stderr: `>> created <type> #<id> assigned to <assignee or "<unassigned>">: <t>`.
  - stdout: `work_item_created=<id>`, printed immediately, before `platform=azure`, as in TS.
  - The id is the `id` field of the API response, never invented.
- **Linking:** created ids join the linked list. The `AB#<…>` substitution, `workItemRefs` and `work_items=<ids>` then cover them, as for an existing item.
- **Failure:** a failed create prints `ship-pr failed: …` and exits 1. Items already created before the failure stay, and their `work_item_created=` lines are already printed (TS behavior).

**Never:**
- **Ids:** never print an id the API did not return.
- **Updates:** never create more than one item per task, never create when `--no-create-work-item` is set, and never update or transition items (Story 3.5).
- **Scope:** reviewers, `--related`, completion options and `--transition` stay as Story 3.2 left them. No change to `scripts/*.ts`, `package.json` or `SKILL.md`. No new dependencies.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| No id, no tasks | branch `feat/x`, `SHIP_ADO_ASSIGNEE=a@b` | one `Task` titled with the PR title, assigned `a@b`; `work_item_created=<id>` before `platform=azure`; PR `workItemRefs` has it; `work_items=<id>` | N/A |
| Two tasks | `--task "A" --task "B"` | two creates in order; two `work_item_created=` lines; `work_items=<idA> <idB>` | N/A |
| Tasks file | `--tasks-file f` with ` A `, blank, `B` (+ `--task C` first) | creates C, A, B | unreadable file → exit 1, no request |
| Tasks skip branch id | branch `feature/42-x`, `--task A` | no read of 42; one create | N/A |
| Not-found id | `--work-item 9999` → 404 | one item created from the title, linked | N/A |
| Type + assignee | `--work-item-type "User Story" --assignee c@d` | URL `.../workitems/%24User%20Story`; AssignedTo `c@d` | N/A |
| Unassigned | `--assignee ""` | no AssignedTo op; stderr says `<unassigned>` | N/A |
| Disabled | `--no-create-work-item`, no real id | no create; Story 3.2 warning/unlinked behavior | N/A |
| Create fails | second create 400 | first item's line already printed | `ship-pr failed: …`, exit 1, no PR |
| Auth fallback | bearer 401 on the create | fallback line; PAT used for the create and the rest | N/A |

</frozen-after-approval>

## Code Map

- `skills/ship/scripts/ship-pr.ts` L132-141 (`--task`, `--tasks-file`), L161-166 (branch inference rule), L283-297 (create loop and messages) -- reference.
- `skills/ship/src/pr.rs` `run_azure` (~L118-215) -- replace the "creating work items is not yet supported" guard with the create loop. `work_item_created=` must print before `platform=azure`, so the stdout writer (`Out`) has to start before the creates.
- `skills/ship/src/azure.rs` -- add `create_work_item(type, title, assignee) -> Result<u64, String>` on the client, reusing `send`. `send` must support a per-call `Content-Type` (the PR create stays `application/json`) and `$`-segment encoding through `http.rs`'s path encoder.
- `skills/ship/src/main.rs` -- the four new flags on the `pr` subcommand. `--task` and `--tasks-file` are accepted on GitHub too and ignored there, as in TS, so the GitHub tests stay green.
- `skills/ship/tests/pr_azure.rs` -- extend the mock with the work-item POST route, record `Content-Type` and the patch body, and cover every matrix row. Remove or adapt the 3.2 test that asserted the "not yet supported" guard.
- `_bmad-output/implementation-artifacts/sprint-status.yaml` -- 3-2 → `done` (PR #27 merged).

## Tasks & Acceptance

**Execution:**
- [x] `skills/ship/src/azure.rs` -- `create_work_item`, per-call content type
- [x] `skills/ship/src/pr.rs` -- task list, inference rule, create loop, early stdout writer
- [x] `skills/ship/src/main.rs` -- `--task`, `--tasks-file`, `--assignee`, `--work-item-type`
- [x] `skills/ship/tests/pr_azure.rs` -- matrix rows; adapt the old guard test
- [x] `skills/ship/HTTP-CLIENT.md` -- add the work-item create endpoint to the Azure section
- [x] `_bmad-output/implementation-artifacts/sprint-status.yaml` -- 3-2 → `done`

**Acceptance Criteria:**
- Given the mock returns ids 501 and 502 for two creates, then stdout is exactly `work_item_created=501`, `work_item_created=502`, `platform=azure`, `pr_id=…`, `pr_url=…`, `work_items=501 502`, then any `tag_added=` lines, and the PR payload's `workItemRefs` is `[{"id":"501"},{"id":"502"}]`.
- Given the stub token and PAT, then neither appears in stdout, stderr, a URL or a body.
- Given `cargo test` and `cargo clippy --all-targets -- -D warnings`, then both pass and every existing test still passes.

## Implementation Notes

## Spec Change Log

## Review Triage Log

**Review skipped** at the principal's request ("ship it", 2026-11-08). Lead checks only:
- `cargo test` (71 + 7 + 33 + 29 + 14 + 17 + 18) passed on two runs, and clippy `-D warnings` is clean.
- `Cargo.toml`, `Cargo.lock`, `scripts/*.ts`, `package.json` and `SKILL.md` are untouched.
- The AC output order is pinned by a test (`work_item_created=501`, `502`, then `platform=azure`, … `work_items=501 502`), as are the `%24User%20Story` path and the `application/json-patch+json` content type.
- Not run against a real Azure DevOps org.

## Verification

**Commands:**
- `cargo test --manifest-path skills/ship/Cargo.toml` -- expected: all green
- `cargo clippy --manifest-path skills/ship/Cargo.toml --all-targets -- -D warnings` -- expected: clean
