# Epic 3 Context: Open and manage PRs

<!-- Compiled from planning artifacts. Edit freely. Regenerate with compile-epic-context if planning docs change. -->

## Goal

Let the operator open pull requests from the `ship` binary on GitHub and Azure Repos, and edit PR tags afterwards. On Azure, a PR never reaches review without a verified or newly created Board work item, with tags, reviewers, related links and state transitions handled as the TypeScript scripts do today. This is the first epic that calls the platform REST APIs, so it also settles the HTTP/SDK client decision. Note: there is no PRD, architecture or UX document; intent comes from the port spec and its CLI parity catalog.

## Stories

- Story 3.1: Open a GitHub PR with labels and reviewers
- Story 3.2: Open an Azure PR linked to an existing work item
- Story 3.3: Create and assign work items when none exist
- Story 3.4: Add optional and required reviewers on Azure
- Story 3.5: Transition work items on open and on completion
- Story 3.6: Link related work items without closing them
- Story 3.7: Manage tags on an existing PR with `ship tag`

## Requirements & Constraints

- `pr` flags: `--title`, `--body`, `--body-file`, `--source`, `--target`, `--remote`, `--draft`, `--work-item`, `--work-item-type`, `--task` (repeatable), `--tasks-file`, `--assignee`, `--no-create-work-item`, `--transition`, `--related` (repeatable, comma-separated), `--tag` (repeatable, comma-separated), `--no-tag`, `--reviewer`, `--required-reviewer`, `--no-reviewer`, `--no-complete-transition`. Stdout keys: `platform`, `pr_url`, `pr_id`, `pr_number`, `work_item`, `work_item_created`, `work_items`, `related_linked`, `tag_added`, `reviewer_added`, `reviewer_skipped`, `complete_transitions_work_items`.
- `tag <id>` takes `--pr`, `--add`, `--remove`, `--list`, `--remote`, and prints `pr_id`, `pr_number`, `tag_added`, `tag_removed`. Re-adding an existing tag succeeds; a missing GitHub label is created.
- Azure PR: one create call carries the work-item link, tags, reviewers and `--draft`. A work item is verified by a read before use; a branch number that is not a real item is reported and not linked. With no real item, one is created per `--task`/`--tasks-file` entry (or one from the PR title), assigned to `--assignee` or `SHIP_ADO_ASSIGNEE`, type default `Task`; `--no-create-work-item` disables creation. The ids printed are the ones the API returned.
- `completionOptions.transitionWorkItems=true` is set by a separate update after create (create silently drops it), unless `--no-complete-transition`; `complete_transitions_work_items` is read back from that update response, never echoed from the flag. `--transition` and these flags are ignored on GitHub.
- `--related` ids are verified and linked as *Related* to the PR's own work item, never to the PR, so completing the PR cannot close an epic. Print `related_linked=<own>-><id>` and warn when the PR body or a commit message mentions a related id (`#<id>` or `AB#<id>`).
- Tags: `--tag`, else derived from the Conventional-Commit title, else from the branch prefix, else `needs-review` with a warning; `--no-tag` adds none. Reviewers: optional and required UPNs resolve to identities on Azure; unresolvable ones print `reviewer_skipped=<name>` and the PR still opens; `SHIP_ADO_DEFAULT_REVIEWER` applies on Azure when none is given; `--no-reviewer` adds none. On GitHub, labels and reviewers are attached in follow-up calls after create.
- Auth: Azure uses the `az` token first, and `AZURE_DEVOPS_EXT_PAT`/`AZURE_DEVOPS_PAT` only after a 401/403 or when `az` is logged out. GitHub uses `GH_TOKEN`/`GITHUB_TOKEN`, then `gh auth token -u <owner>`, then the active account. Tokens appear only in `Authorization` headers, never in output, logs or URLs.
- Titles are sent literally (`&` stays `&`). Nothing in a title, body or commit carries AI attribution.
- Gotchas to keep: a GitHub 404 on create usually means the wrong account, not a missing repo; `TF400813` right after an Entra UPN rename is ADO's identity cache, not a code fault.
- Flags, env vars (`SHIP_PLATFORM` applies), `key=value` stdout and exit codes keep parity with `ship-pr.ts` and `ship-tag.ts`, the reference for formats and for exit codes beyond 0.

## Technical Decisions

- **Open decision owned by Story 3.1:** the HTTP/SDK client for GitHub and Azure DevOps (a crate such as `octocrab` or `azure_devops_rust_api`, or direct REST calls) must be recorded in `skills/ship/` with its reason, after checking each candidate crate is maintained. Release builds target `x86_64-unknown-linux-musl` (static) and `aarch64-apple-darwin`, so the choice must build for both and avoid a system OpenSSL dependency. The crate currently depends only on `clap` and `regex`; `git` and `az` stay subprocesses called with argument arrays.
- **Reuse from Epic 2, do not rebuild:**
  - `git::push_with_auth` is the Bearer-or-fallback push; PR opening assumes the branch was already pushed by it.
  - `git::try_ado_token` mints the Azure token via `az account get-access-token --resource 499b84ac-1321-427f-aa17-267ca6975798`. Epic 3's REST calls use this same token source, then add the PAT fallback on 401/403 or a logged-out `az`, which Epic 2 deliberately left out.
  - `push.rs` holds the shared ref validation (`is_unsafe_ref`, `validate_target`): a remote starting with `-` and a branch starting with `-` or `+` or containing `:` are rejected with exit 2. Reuse it for `--source`, `--target` and `--remote`; do not write a second validator.
  - Platform detection (`detect_kind`, `ado_parts`, `github_owner_repo`, `parse_work_item`) and the git helper from Epic 1 supply the org, project, repo, owner and branch-inferred work item.
- **Parity-with-TS principle, with approved and recorded deviations.** The TS scripts are the reference; the Rust output is byte-compatible in stdout, `>>` stderr lines and exit codes. A deviation is allowed only when the principal approves it and it is written into the story spec. Recorded so far: Bearer settings reach git through `GIT_CONFIG_*` environment variables instead of `-c` arguments (mechanism only, so the token stays out of `ps`); `snapshot` keeps the TS `pushed=` values rather than the epics' `true`/`false`; Story 1.2 carries an approved trim fix. Expect Epic 3 to hit the same choice: fix a TS bug in both or keep it and log it in `deferred-work.md`, never diverge silently.
- Token hygiene lessons from Epic 2 apply to HTTP: scope any credential to the intended host only, never follow it to a redirect on another host, and add tests asserting a stub token appears in no stdout, stderr or file.
- Port the matching `ship-lib` test cases as Rust unit tests: `parseTags`, `defaultTagsFromTitle` (3.1), `parseRelatedIds`, `mentionsWorkItem` (3.6). Keep pure logic (tag derivation, id parsing, payload building) separate from network code so it is testable without HTTP; test the API paths against a local stub server or recorded payloads.
- Deferred and still relevant: branch lookup via `rev-parse --abbrev-ref HEAD` returns `HEAD` when detached and fails on an unborn branch, and `pr` consumes the branch; work-item inference from a branch name yields false ids (`feature/tab12-fix` gives 12, a date prefix gives 2026), which is why the verified read in 3.2 matters.

## Cross-Story Dependencies

- Depends on Epic 1 (crate skeleton, detection, git helper) and Epic 2 (`push_with_auth`, `try_ado_token`, ref validation).
- Story 3.1 comes first: it records the HTTP client decision that every later story in this epic builds on.
- Story 3.2 creates the Azure PR path (work-item read, single create call). Stories 3.3 (created items), 3.4 (reviewers), 3.5 (transitions, completion options) and 3.6 (related links) extend that path and need its PR and work-item ids.
- Story 3.6 links against the own item from 3.2 or 3.3; Story 3.5 transitions items from both.
- Story 3.7 (`ship tag`) reuses the platform and tag handling from 3.1/3.2.
- Epic 4 opens the PR URLs this epic prints (`pr_url`). Epic 5 benchmarks parity on one Azure and one GitHub repo and replaces the `SKILL.md` invocations with `ship pr` and `ship tag`.
