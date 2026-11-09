---
title: 'Story 3.6: Link related work items without closing them'
type: 'feature'
created: '2026-11-09'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: '36417e7686b749ee7b24c4a424c6a49cd4f9ce1f'
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-3-context.md'
  - '{project-root}/skills/ship/HTTP-CLIENT.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** On Azure, `ship pr --related` stops with exit 1 ("not yet supported on Azure by the binary"). So the binary cannot relate a long-lived epic or backlog item to a PR without letting Complete close it.

**Approach:** Port the TS `--related` flow from `ship-pr.ts`:
- verify each related id before anything is written;
- warn when the body or a commit mentions one;
- after create, add a *Related* relation from each of the PR's own items to each related id. The PR itself never references a related id.

## Boundaries & Constraints

**Always:**
- **Before platform dispatch (every platform, TS L170-177):**
  - Branch-number inference is skipped when `--related` is non-empty.
  - An explicit `--work-item` equal to a related id fails with exit 2: `work item <id> is both --work-item and --related; a related item is never linked to the PR`.
- **Verify (Azure, after the client exists, before the own item is resolved):** each related id is read in order. A missing item, or any read error, gives exit 2 `--related <id>: work item not found` (TS maps every failure to not-found). Nothing is created.
- **Mention warning:** read the commit messages with `git log --format=%B <remote>/<target>..<source>`, best-effort (git failing means empty text). For each id mentioned in the final body or in those messages (`#<id>`/`AB#<id>`, case-insensitive, not part of a longer number or word), stderr gets `>> WARNING: <where> mention #<id>; Azure Repos may link it to the PR, and Complete would then close it. Reword it (e.g. "item <id>") before completing.`. `<where>` is `the PR body`, `a commit message`, or both joined by ` and `.
- **Link (after `work_items=`, before the completion PATCH, TS L360-374):**
  - With no own item: stderr `>> WARNING: --related given but the PR has no work item of its own to relate it to; nothing linked`.
  - Otherwise, for each own × related pair: `PATCH {org}/{project}/_apis/wit/workitems/{own}?api-version=7.1`, `application/json-patch+json`, body `[{"op":"add","path":"/relations/-","value":{"rel":"System.LinkTypes.Related","url":"<real org URL>/_apis/wit/workItems/<rid>","attributes":{"comment":"Related via PR <prId>"}}}]`.
  - On success, stdout `related_linked=<own>-><rid>`. On failure, stderr `>> WARNING: could not link work item <own> Related to <rid>: <err>`, and the loop continues.
- The relation URL uses the real org URL from the remote, never the `SHIP_ADO_API_URL` seam.
- Related ids never appear in `workItemRefs` or the PR body. Exit is 0 once the PR exists. Credentials appear only in the `Authorization` header.
- Port the TS `parseRelatedIds` and `mentionsWorkItem` test cases as Rust unit tests.

**Never:** No change to GitHub output beyond the global exit-2 check; the existing NOTE stays. No `ship tag`, no change to `scripts/*.ts`, `package.json` or `SKILL.md`, no new dependencies.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Happy | `--work-item 42 --related 7,AB#8` | GETs 7, 8, 42; create has refs `[42]` only; `related_linked=42->7`, `related_linked=42->8` after `work_items=42`, before `complete_transitions_work_items=` | N/A |
| Created own | `--task a --task b --related 7` | `related_linked=501->7`, `502->7` | N/A |
| Missing | the GET for 7 answers 404 | no POST/PATCH sent | exit 2 |
| Branch id | branch `feat/7-x`, `--related 7`, no `--work-item` | no inference; one item is created from the title and related to 7 | N/A |
| Both | `--work-item 7 --related 7` (Azure or GitHub) | no request | exit 2 |
| Mention | body `see AB#7`, a commit `fixes #7` | WARNING naming both; PR still opens | exit 0 |
| No own | `--no-create-work-item`, own id missing, `--related 7` | "nothing linked" WARNING | exit 0 |
| Link fails | the relation PATCH answers 400 | WARNING; the next pair and the later steps still run | exit 0 |

</frozen-after-approval>

## Code Map

- `skills/ship/scripts/ship-pr.ts` L170-177, L254-270, L357-374; `ship-lib.ts` L262-285, `ship-lib.test.ts` L165-186: the reference.
- `skills/ship/src/lib.rs`: `parse_related_ids` already exists (L189). Add `mentions_work_item(text, id) -> bool` beside it. Rust `regex` has no lookahead, so write `(?:^|[^0-9A-Za-z_#])(?:AB)?#<id>(?:[^0-9]|$)`, case-insensitive, with ASCII classes to match JS `\w`. Add the TS cases as unit tests.
- `skills/ship/src/git.rs`: add `commit_messages(remote, target, source) -> String` (an args array, empty on failure), like `log_ahead_of_upstream`.
- `skills/ship/src/azure.rs`:
  - `Client` keeps the real `org_url` (it is already passed to `new`).
  - Add a pure `relation_patch(org_url, rid, pr_id) -> Value` with a unit test.
  - Add `link_related(own, rid, pr_id) -> Result<(), String>` through `send_as(Method::Patch, …)`, like `transition_work_item`.
  - Reuse `work_item_exists` for the verify.
- `skills/ship/src/pr.rs`:
  - `run`: add the both-check and pass the inference skip into `run_azure`, which computes `wanted` at about L200.
  - `run_azure`: remove the fail-fast guard (L173-179); add verify, warning and link in TS order; update the doc comment. `run_github` is unchanged.
- `skills/ship/tests/pr_azure.rs`:
  - Delete `related_flag_fails_fast_without_calling_the_api`.
  - The `happy` mock already answers 200 to a work-item PATCH. Assert the relation body, then cover every matrix row and the secrecy of the new PATCH.
  - For the commit mention, create `refs/remotes/origin/main` at the init commit, then commit on the branch.
- `skills/ship/tests/pr.rs`: test the GitHub both-check (exit 2, no request).
- `skills/ship/HTTP-CLIENT.md`: add a row for the relation PATCH.
- `_bmad-output/implementation-artifacts/sprint-status.yaml`: 3-5 → `done` (PR #30 merged).

## Tasks & Acceptance

**Execution:**
- [x] `skills/ship/src/lib.rs` -- `mentions_work_item` and the ported TS test cases
- [x] `skills/ship/src/git.rs` -- `commit_messages`
- [x] `skills/ship/src/azure.rs` -- `org_url` field, `relation_patch`, `link_related`, unit test
- [x] `skills/ship/src/pr.rs` -- global checks, inference skip, verify, warning, link; drop the guard
- [x] `skills/ship/tests/pr_azure.rs` -- matrix rows, relation body and secrecy; drop the fail-fast test
- [x] `skills/ship/tests/pr.rs` -- GitHub both-check
- [x] `skills/ship/HTTP-CLIENT.md` -- relation PATCH row
- [x] `_bmad-output/implementation-artifacts/sprint-status.yaml` -- 3-5 → `done`

**Acceptance Criteria:**
- Given `--work-item 42 --related 7 --no-tag`, when the PR opens, then stdout is exactly `platform=azure`, `pr_id=9`, `pr_url=…`, `work_items=42`, `related_linked=42->7`, `complete_transitions_work_items=true`, and the relation URL starts with `https://dev.azure.com/acme`, not the mock base.
- Given `cargo test` and `cargo clippy --all-targets -- -D warnings`, then both pass and every existing test still passes.

## Implementation Notes

- `lib.rs`: `mentions_work_item` folds case only on `AB` (`(?i:AB)`). A whole-pattern `(?i)` would fold the ASCII classes in Unicode (for example the Kelvin sign), which JS does not do. The TS cases are ported, plus extra edge tests.
- `pr.rs`: the both-check runs in `run` on every platform. `run_azure` takes `related: &[u64]` and runs: verify (any error means not found, exit 2), the mention warning, own-item resolution (inference skipped), and the link loop after `work_items=` and before the completion PATCH. The mention check uses the body before the AB# substitution, as TS does. That substitution only adds own ids, which can never be related ids.
- `azure.rs`: `Client.org_url`, `relation_patch`, `link_related` (via `send_as(Method::Patch)`). `git.rs`: `commit_messages`.
- Tests: 14 new Azure tests and 1 new GitHub test. The fail-fast test is deleted. The matrix "Branch id" row is tested with `feat/77-x`, because `WI_DELIM` needs 2-7 digits, so `feat/7-x` would pass even without the skip. Mutation checks confirmed that the inference skip, the commit-mention check and the real-org relation URL are each caught by a test.
- Verified by the lead: `cargo test` gives 245 passed (81/7/35/73/14/17/18). Clippy `-D warnings` is clean. `scripts/*.ts`, `package.json`, `SKILL.md` and `Cargo.toml` are untouched. Not run against a real Azure DevOps org.
- Known, inherited: on a repo without `<remote>/<target>`, git prints its own `fatal: ambiguous argument` during the mention check (TS does the same).

## Spec Change Log

## Review Triage Log

Pass 1 used three reviewers: blind-hunter (BH), edge-case-hunter (EC) and verification-gap (VG). VG found no gaps; every changed behavior has a test that fails when it regresses.

| # | Finding | Verdict | Evidence | Route |
|---|---|---|---|---|
| 1 | BH2: the HTTP-CLIENT auth paragraph lists only the 3.5 PATCHes as warn-only | low | The relation PATCH also only warns, and `every_credential_rejected_on_the_relation_only_warns` tests that. The fix is a direct doc correction. | patch |
| 2 | BH8: the happy-path `zip([7, 8])` loop cannot catch a change in the PATCH count | low | `zip` stops at the shorter side. The separate `paths` assertion catches it today, so the fix is one direct assert. | patch |
| 3 | BH3/EC1: ADO may reject a duplicate relation, so a re-run would warn instead of print `related_linked=` | maybe-false | The TS comment states ADO accepts a repeat, and the TS behaves the same. Settling it needs a call against a real org. If true, the only effect is a misleading warning while the link already exists. | reject |
| 4 | EC4: a related id mentioned only in the PR title gets no warning | maybe-false | TS does not check the title either. Settling it needs proof that Azure Repos links `#id` in a PR title. If true, a title mention could close an epic on Complete. | defer |
| 5 | BH5: git prints `fatal: ambiguous argument` when `<remote>/<target>` is missing | low | Node `execFileSync` also passes the child's stderr through, so this matches TS. The range cannot start with `-`, because `validate_target` rejects that. | reject |
| 6 | BH6: "the PR body mention #7" is ungrammatical for one place | low | This is TS byte parity, and the text is frozen in the spec. | reject |
| 7 | BH1: the spec says `in-review` while sprint-status says `in-progress` | false | Workflow order: step 5 sets sprint-status to `review`. | reject |
| 8 | BH4: the branch-inference skip applies only on Azure | false | GitHub never infers or uses a work item, so the output cannot differ. | reject |
| 9 | BH7, EC5: spec line references and the `feat/7-x` row are stale, and "final body" is worded loosely | low | The fix would edit this build's spec. Behavior matches the row (no inference), and the AB# substitution only adds own ids. | reject |
| 10 | BH9: `run_azure` has 8 params and a lint allow | low | No named harm. Refactoring is outside the story. | reject |
| 11 | BH10: the regex is compiled on every call | low | It runs twice per id at most. `is_ok_and` cannot fail, because the pattern holds only digits from a u64. | reject |
| 12 | BH11: no tests for a related id equal to a created item, an M×N middle failure, or duplicate `--related` | low | Created ids are new by construction. Dedupe has a unit test. A failure in the middle of the loop is covered by `link failure … next pair`. | reject |
| 13 | EC2: the both-check error prints the raw `--work-item` text | false | TS prints the raw `workItem` the same way. | reject |
| 14 | EC3: `--work-item AB#7 --related 7` skips the both-check | low | This predates the story. TS `Number("AB#7")` is NaN, so it skips the check the same way, and `--work-item` never accepted prefixes. | reject |

## Verification

**Commands:**
- `cargo test --manifest-path skills/ship/Cargo.toml` -- expected: all green
- `cargo clippy --manifest-path skills/ship/Cargo.toml --all-targets -- -D warnings` -- expected: clean
