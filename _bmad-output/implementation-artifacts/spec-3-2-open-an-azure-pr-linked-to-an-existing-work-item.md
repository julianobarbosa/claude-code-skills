---
title: 'Story 3.2: Open an Azure PR linked to an existing work item'
type: 'feature'
created: '2026-11-08'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: '3ad72a83822c518f53da40b711995f8ef099f6ca'
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-3-context.md'
  - '{project-root}/skills/ship/HTTP-CLIENT.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** On an Azure Repos remote, `ship pr` exits with "not yet supported", so opening an Azure PR still needs `bun scripts/ship-pr.ts` and `azure-devops-node-api`.

**Approach:** Add the Azure path to `ship pr` for an *existing* work item:
1. Check the work item exists.
2. Create the PR in one call that carries the work-item link, tags and `--draft`.
3. Print the TS keys.

The auth order is the `az` token, then a PAT after a 401/403 (NFR5). Creating work items, reviewers, transitions/completion options and related links stay for Stories 3.3-3.6.

## Boundaries & Constraints

**Decision (Barbosa, 2026-11-08): the work-item key is `work_items=` (TS parity).** It holds the space-separated ids of linked items and supersedes the epics AC's `work_item` wording.

**Always:**
- **Coordinates:** `org_url`, `project` and `repo` come from the existing `ado_parts` (unparseable → `could not parse org/project/repo from <url>`, exit 1).
- **Credentials, in order:**
  - **az token:** the existing `git::try_ado_token`, sent as `Bearer`.
  - **PAT:** `AZURE_DEVOPS_EXT_PAT`, else `AZURE_DEVOPS_PAT`, sent as `Basic base64(":" + pat)`.
  - **None:** `no Azure DevOps credential: run 'az login' (or set AZURE_DEVOPS_EXT_PAT)`, exit 1.
  - **Fallback:** any call that returns 401 or 403 moves to the next credential once, printing the TS line `>> bearer auth failed (401/403); falling back to pat`, and later calls stay on it.
- **Work-item id:** `--work-item`, else `parse_work_item(branch)`. Read it with `GET {org}/_apis/wit/workitems/{id}?api-version=7.1`.
  - **Exists:** `>> linking existing work item <id>`; the id is linked.
  - **Missing, with `--no-create-work-item`:** `>> WARNING: work item <id> not found and --no-create-work-item set; PR will not link it`; the PR opens unlinked.
  - **Creation needed:** no real id and no `--no-create-work-item` is the Story 3.3 create path. Exit 1 with a clear "creating work items is not yet supported by the binary; pass --work-item <id> or --no-create-work-item, or use bun scripts/ship-pr.ts" message, before anything is created. The never-open-a-PR-without-a-work-item invariant must not be broken silently.
- **Placeholder:** when ids are linked, `AB#<...>` placeholders in the body become `AB#<id>` (space-separated), with the TS `>> substituted AB# placeholder -> …` line.
- **Create:** `POST {org}/{project}/_apis/git/repositories/{repo}/pullrequests?api-version=7.1` with `sourceRefName`/`targetRefName` (`refs/heads/…`), `title`, `description` (only if non-empty), `isDraft` (only if `--draft`), `workItemRefs: [{id: "<id>"}]`, and `labels: [{name}]` (only if tags). The project and repo are percent-encoded in the path.
- **Stdout, in this order:** `platform=azure`, `pr_id=`, `pr_url={org}/{encodeURIComponent(project)}/_git/{encodeURIComponent(repo)}/pullrequest/{id}`, `work_items=<ids>` (only if any), then one `tag_added=` per tag.
- **API failure:** `ship-pr failed: …`, exit 1.
- **Not yet supported on Azure:**
  - `--reviewer`, `--required-reviewer` and `--related` exit 1 with a "not yet supported on Azure by the binary" message.
  - When neither reviewer flag nor `--no-reviewer` is given, a set `SHIP_ADO_DEFAULT_REVIEWER` prints `>> NOTE: SHIP_ADO_DEFAULT_REVIEWER is not applied yet (Story 3.4)` and does not block.
- **Requests:** the same rules as GitHub (`HTTP-CLIENT.md`): no redirects followed, OS trust store, and the credential in the `Authorization` header only. ADO answers a bad PAT with 203 or a redirect to a sign-in page, so a 203 or 3xx counts as an auth failure, like 401/403.
- **Test seam:** `SHIP_ADO_API_URL` replaces the `https://dev.azure.com` origin of API calls (the https-or-loopback guard applies). The printed `pr_url` still uses the real org URL.

**Never:**
- **Credentials:** never in output, the URL, logs or files.
- **Content:** add nothing to the title or body beyond the documented `AB#` substitution (NFR4).
- **Scope:** do not create, assign, transition or relate work items. Do not PATCH `completionOptions`. No `--task`, `--tasks-file`, `--assignee`, `--work-item-type`, `--transition`, `--no-complete-transition` flags yet. No change to `scripts/*.ts`, `package.json` or `SKILL.md`. No new dependencies.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Existing item | `--work-item 42`, item exists | read 42; create with `workItemRefs [{id:"42"}]`; `pr_id`, `pr_url`, `work_items=42` | N/A |
| From branch | branch `feature/42-x`, no flag | id 42 inferred and verified | N/A |
| Bogus branch number | branch `feature/9999-x`, 404 on read, `--no-create-work-item` | WARNING line; PR created with no `workItemRefs` entry; no `work_items=` | exit 0 |
| Would need creation | no real id, no `--no-create-work-item` | nothing created | exit 1, clear message |
| Tags + draft + literal | `--tag a,b --draft`, title `x & y`, body file with `AB#<id>` | `labels [{a},{b}]`, `isDraft:true`, title verbatim, placeholder replaced; `tag_added=` ×2 | N/A |
| az ok | stub `az` token | `Bearer` header on every call | N/A |
| az 401 → PAT | bearer 401 on the read, PAT set | fallback line; `Basic` used for the read and the create | PAT also 401 → `ship-pr failed`, exit 1 |
| az logged out | `az` exits 1, PAT set | `Basic` from the first call | none → exit 1, message above |
| 203 sign-in page | PAT answered 203 | treated as an auth failure (fallback or exit 1) | N/A |
| Not yet supported | `--reviewer x` / `--related 5` on Azure | nothing created | exit 1 |

</frozen-after-approval>

## Code Map

- `skills/ship/scripts/ship-pr.ts` L225-316, L342-358 (runAzure up to the create call, plus output) -- reference for messages, ordering and payload. Ignore the work-item creation (3.3), the reviewer resolution (3.4), `related` (3.6) and the post-create PATCH/transition (3.5).
- `skills/ship/scripts/ship-lib.ts` -- `adoCredentials`, `adoAuthHeader`, `isAuthError` (401/403), `parseWorkItem` (already ported as `parse_work_item`).
- `skills/ship/src/github.rs` -- the client to mirror (agent settings, base-URL guard, error text). Put the Azure calls in `src/azure.rs`. Factor the shared agent and the https/loopback guard if that is clean, without changing GitHub behavior (its tests must stay green).
- `skills/ship/src/pr.rs` -- replace the Azure "not yet supported" branch with the dispatch into `azure.rs`. Tag defaulting and the parsing stay shared.
- `skills/ship/src/lib.rs` -- `ado_parts`, `parse_work_item`. `src/git.rs` -- `try_ado_token`.
- Base64 for the PAT header: a 10-line encoder in-crate, or `ureq`'s re-export if one exists. No new crate.
- Tests: extend the `tests/pr.rs` mock-server pattern with routes for the work-item GET and the PR POST, a stub `az` on PATH and PAT env vars. The parity copy of `ship-pr.ts` can't be pointed at the mock without patching `azure-devops-node-api` URLs, so parity here is message- and payload-level against the TS source. Record that in Implementation Notes.
- `_bmad-output/implementation-artifacts/sprint-status.yaml` -- 3-1 → `done` (PR #26 merged).

## Tasks & Acceptance

**Execution:**
- [x] `skills/ship/src/azure.rs` -- credentials, auth fallback, work-item read, PR create
- [x] `skills/ship/src/pr.rs` -- Azure dispatch, AB# substitution, the "not yet supported" guards, the default-reviewer NOTE
- [x] `skills/ship/tests/pr.rs` (or `tests/pr_azure.rs`) -- mock-server tests for every matrix row
- [x] `skills/ship/HTTP-CLIENT.md` -- add the Azure section (endpoints, auth order, 203 rule, `SHIP_ADO_API_URL` seam)
- [x] `_bmad-output/implementation-artifacts/sprint-status.yaml` -- 3-1 → `done`

**Acceptance Criteria:**
- Given the stub token `SECRET-TOKEN-123` and PAT `SECRET-PAT-456`, then neither appears in stdout, stderr or any URL; each appears only in an `Authorization` header (the PAT base64-encoded).
- Given any matrix row, then the stdout keys, the `>>` lines and the exit code match what `ship-pr.ts` prints for the same situation, checked line by line against the TS source.
- Given `cargo test` and `cargo clippy --all-targets -- -D warnings`, then both pass and every GitHub `pr` test still passes.

## Implementation Notes

- **Parity is message- and payload-level.** `ship-pr.ts` cannot be pointed at the mock server without patching `azure-devops-node-api` URLs, so stdout keys, `>>` lines and payload fields were checked line by line against `ship-pr.ts` L225-358 and asserted in `tests/pr_azure.rs`; no side-by-side run against the TS script.
- **Deviation from TS (to confirm):** the TS wraps the work-item read in `try/catch` and treats *any* error as "not found". The binary treats only 404 as "not found"; a 5xx, or a 401/403/203/3xx after every credential is rejected, fails the run with `ship-pr failed: HTTP <status>`. Reason: with `--no-create-work-item` a transient 5xx would otherwise open the PR unlinked and claim the item was missing; the matrix row "PAT also 401 → `ship-pr failed`, exit 1" requires the auth case.
- **Shared plumbing:** `src/http.rs` now holds the agent, `check_base(var, base)` (error text names the env var, GitHub's text is unchanged), `enc` and `encode_uri_component` (JS-exact, for the printed `pr_url`). GitHub tests stay green; the two unit tests for `check_base`/`enc` moved with the code.
- **Removed test:** `tests/pr.rs::azure_remote_is_not_supported_yet_and_creates_nothing` asserted the Story 3.1 stub this story replaces; `tests/pr_azure.rs` covers the Azure path.
- **New flags:** only `--work-item` and `--no-create-work-item` were added to `ship pr`. Both are ignored on GitHub.
- `--related` / `--reviewer` / `--required-reviewer` exit 1 before any credential lookup or request.

## Spec Change Log

## Review Triage Log

**Review skipped** at the principal's request ("ship it", 2026-11-08). Lead checks only:
- `cargo test` passed (70 + 7 + 33 + 19 + 14 + 17 + 18) on two runs, and clippy `-D warnings` is clean.
- `cargo tree` adds no crate beyond ureq's own `base64`.
- `scripts/*.ts`, `package.json`, `SKILL.md` and `Cargo.toml` are untouched.

**Deviation from TS kept** (the implementer's call, the safer one): only a 404 on the work-item read means "not found". A 5xx, or an auth failure once every credential is rejected, exits 1 instead of opening an unlinked PR.

## Verification

**Commands:**
- `cargo test --manifest-path skills/ship/Cargo.toml` -- expected: all green
- `cargo clippy --manifest-path skills/ship/Cargo.toml --all-targets -- -D warnings` -- expected: clean
