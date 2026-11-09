---
title: 'Story 3.4: Add optional and required reviewers on Azure'
type: 'feature'
created: '2026-11-09'
status: 'done'
route: 'dispatch'
review_loop_iteration: 0
baseline_commit: 'b07c07deaf9882d2fa3d88624e66067297a83908'
context:
  - '{project-root}/_bmad-output/implementation-artifacts/epic-3-context.md'
  - '{project-root}/skills/ship/HTTP-CLIENT.md'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** On Azure, `ship pr` currently refuses `--reviewer`/`--required-reviewer` (exit 1) and does not apply `SHIP_ADO_DEFAULT_REVIEWER`. That leaves an Azure PR with no record of who was asked to review.

**Approach:** Port the TS reviewer path:
- Resolve each UPN to an identity through the identities API, trying the credentials in the same order as every other call.
- Add the resolved reviewers to the PR create call, with `isRequired`.
- Report each one as added or skipped. A name that can't be resolved never blocks the PR.

## Boundaries & Constraints

**Always:**
- **Lists:** `--reviewer` (optional) and `--required-reviewer` (required) are comma-separated and repeatable, split and deduped per list with `parse_tags`, as in TS.
- **Default reviewer:** with neither flag and no `--no-reviewer`, a trimmed non-empty `SHIP_ADO_DEFAULT_REVIEWER` is added as an optional reviewer, and stderr prints `>> NOTE: no reviewer given; using SHIP_ADO_DEFAULT_REVIEWER (<value>)`. This replaces Story 3.2's "not applied yet" NOTE. `--no-reviewer` adds none.
- **Resolution:** run after work-item resolution/creation and before the PR create, optional reviewers first, then required.
  - A value matching a GUID (`^[0-9a-f]{8}-…-[0-9a-f]{12}$`, case-insensitive) passes through unchanged.
  - Otherwise: `GET https://vssps.dev.azure.com/{org}/_apis/identities?searchFilter=General&filterValue=<encodeURIComponent(upn)>&api-version=7.1`, where `{org}` is the org segment of `org_url`. The identity is `value[0].id`.
  - Credentials: start at the credential the client is currently on, and move to the next one after a 401/403 (or 203/3xx), printing `>> identity lookup got HTTP <status>; retrying with the next credential`.
- **Unresolved reviewer:**
  - stderr: `>> WARNING: could not resolve reviewer '<upn>' (<why>); skipping`, where `why` is `HTTP <status>`, `no matching identity`, or the transport error.
  - stdout: `reviewer_skipped=<upn>`, printed at that point, before `platform=azure`.
  - The PR still opens.
- **Create payload:** `reviewers: [{id, isRequired}]` when at least one resolved, otherwise the field is absent.
- **After the PR lines:** after `tag_added=`, print one `reviewer_added=<upn> required=<true|false>` per resolved reviewer, in resolution order.
- **Test seam:** `SHIP_ADO_API_URL` also replaces the `https://vssps.dev.azure.com` origin, with the same https-or-loopback guard. Credentials only ever go in the `Authorization` header.

**Never:**
- **Failures:** never fail the run because a reviewer can't be resolved. Never add reviewers in a separate call after create (the create call carries them, as in TS).
- **GitHub:** behavior unchanged (its reviewer path and tests stay as in Story 3.1).
- **Scope:** no `--related`, `--transition` or completion-options work (Stories 3.5 and 3.6). No change to `scripts/*.ts`, `package.json` or `SKILL.md`. No new dependencies.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Both kinds | `--reviewer a@x,b@x --required-reviewer c@x` | 3 lookups (a, b, c); payload `reviewers` with `isRequired` false, false, true; `reviewer_added=a@x required=false` … `c@x required=true` after `tag_added` | N/A |
| GUID | `--reviewer 1f0e…-…` | no lookup; id passed as is | N/A |
| Unresolvable | lookup returns `value: []` | WARNING `no matching identity`; `reviewer_skipped=<upn>` before `platform=azure`; PR opens without it | exit 0 |
| Lookup HTTP error | 500 | WARNING `HTTP 500`; skipped | exit 0 |
| Lookup auth fallback | bearer 401 on lookup, PAT set | retry line; PAT used; resolved | N/A |
| Default reviewer | no flags, `SHIP_ADO_DEFAULT_REVIEWER=d@x` | NOTE line; d@x added optional | N/A |
| Opt out | `--no-reviewer` with env set | no NOTE, no lookup, no `reviewers` field | N/A |
| Encoding | UPN `o'b+x@y.com` | `filterValue` percent-encoded like `encodeURIComponent` | N/A |
| Secrecy | stub token/PAT | never in stdout, stderr, URLs or bodies | N/A |

</frozen-after-approval>

## Code Map

- `skills/ship/scripts/ship-pr.ts` L80-104 (`resolveAzureIdentity`), L212-223 (default reviewer), L305-322 (resolution loop), L330-331 (payload), L398-404 (output) -- reference.
- `skills/ship/src/pr.rs` -- remove the Azure "not yet supported" guard for `--reviewer`/`--required-reviewer` (keep it for `--related`), and replace the default-reviewer NOTE. Resolution goes between work-item handling and `create_payload`. Note the `work_item_created=` → `reviewer_skipped=` → `platform=azure` ordering through the existing `Out` writer.
- `skills/ship/src/azure.rs` -- add `resolve_identity(upn) -> Result<String, String>` (the `Err` is the "why"), reusing the credential list and current index. Extend `create_payload` with reviewers. The vssps URL is built through the same seam helper (`api_org` today).
- `skills/ship/src/http.rs` -- `encode_uri_component` already exists for `pr_url`. Reuse it for `filterValue`.
- `skills/ship/tests/pr_azure.rs` -- add an identities route to the mock (match on path `/{org}/_apis/identities` plus the query), and cover every matrix row. Replace the 3.2 tests that asserted the reviewer guard and the default-reviewer NOTE.
- `_bmad-output/implementation-artifacts/sprint-status.yaml` -- 3-3 → `done` (PR #28 merged).

## Tasks & Acceptance

**Execution:**
- [x] `skills/ship/src/azure.rs` -- `resolve_identity`, reviewers in the payload, vssps seam
- [x] `skills/ship/src/pr.rs` -- default reviewer, resolution loop, output lines; drop the reviewer guard
- [x] `skills/ship/tests/pr_azure.rs` -- matrix rows; adapt the 3.2 guard/NOTE tests
- [x] `skills/ship/HTTP-CLIENT.md` -- add the identities endpoint and its origin
- [x] `_bmad-output/implementation-artifacts/sprint-status.yaml` -- 3-3 → `done`

**Acceptance Criteria:**
- Given `--reviewer a@x --required-reviewer c@x` with both resolving, then stdout ends with `tag_added=…` lines followed by `reviewer_added=a@x required=false` and `reviewer_added=c@x required=true`, and the create body has `reviewers` `[{"id":"<a>","isRequired":false},{"id":"<c>","isRequired":true}]`.
- Given an unresolvable name among resolvable ones, then the PR opens with the others, exit 0, with exactly one `reviewer_skipped=` line.
- Given `cargo test` and `cargo clippy --all-targets -- -D warnings`, then both pass and every existing test still passes.

## Implementation Notes

- `azure.rs`: `resolve_identity` (GUID passthrough, vssps identities lookup, local credential fallback starting at the client's current one, as in TS), reviewers in `create_payload`, `SHIP_ADO_API_URL` also replaces the vssps origin. `pr.rs`: `SHIP_ADO_DEFAULT_REVIEWER` default (trimmed, only with no reviewer flag, off with `--no-reviewer`), resolution after work items and before create, `reviewer_skipped=` before `platform=azure`, `reviewer_added=` after `tag_added=`.
- Review fix, a deliberate deviation from TS: reviewers are deduped by resolved id across both lists with `isRequired` true if either named them, and each UPN is looked up once, so a duplicate id can no longer make ADO reject the create. TS sends both entries.
- Verified: `cargo test` 73 + 7 + 33 + 47 + 14 + 17 + 18 green on two runs; clippy `-D warnings` clean; no dependency change. Not run against a real Azure DevOps org.

## Spec Change Log

## Review Triage Log

Pass 1 (blind-hunter BH, edge-case-hunter EC, verification-gap VG; VG found no verification gaps).

| # | Finding | Verdict | Evidence | Route |
|---|---|---|---|---|
| 1 | BH3/EC1/EC2/VG-other: same person in both lists (or UPN + GUID) sent twice with contradictory `isRequired` | medium | Resolve loop pushes one entry per list; TS does the same, but a duplicate id can make ADO reject the create and fail the whole PR. Direct dedupe, required wins. | patch |
| 2 | EC4: empty `value[0].id` accepted | low | `as_str` without an emptiness check; direct correction. | patch |
| 3 | BH-tests: no 203/3xx case on the identities lookup | low | Only 401/403/500 covered; test-only. | patch |
| 4 | BH6: `reviewer_skipped=` placement and `SHIP_ADO_DEFAULT_REVIEWER` rules undocumented | low | Doc correction. | patch |
| 5 | BH2/EC3: `searchFilter=General` + `value[0]` may pick the wrong identity | maybe-false | Same filter and pick as TS `resolveAzureIdentity`; whether General returns several identities for a full UPN needs a real ADO org to settle. | defer |
| 6 | BH1/EC5: lookup fallback not persisted, repeats per reviewer | low | TS also starts each lookup from `creds[ci]`; extra 401 lines only. | reject |
| 7 | EC6: transport error does not try the next credential | low | Same as TS (`catch` returns the reason). | reject |
| 8 | BH4: unresolved required reviewer skipped with exit 0 | low | Frozen spec: never fail the run on an unresolvable reviewer; same as TS. | reject |
| 9 | BH5: `identity_org` breaks for visualstudio.com remotes | false | `ado_parts` (lib.rs) normalizes every org URL to `https://dev.azure.com/<org>` (confirmed by VG). | reject |
| 10 | BH7/BH8/BH9: `refs` name reuse, 8-arg `create_payload`, duplicated test args | low | Cosmetic. | reject |
| 11 | BH10: sprint `in-progress`; 3-3 `done` without review | false | Workflow order; Story 3.3's review skip is recorded in its spec at the principal's request. | reject |

## Verification

**Commands:**
- `cargo test --manifest-path skills/ship/Cargo.toml` -- expected: all green
- `cargo clippy --manifest-path skills/ship/Cargo.toml --all-targets -- -D warnings` -- expected: clean
