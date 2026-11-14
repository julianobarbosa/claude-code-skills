---
status: final
stepsCompleted: [1, 2, 3, 4]
inputDocuments:
  - _bmad-output/specs/spec-ship-rust-port/SPEC.md
  - _bmad-output/specs/spec-ship-rust-port/cli-contract.md
  - skills/ship/SKILL.md
---

# ship Rust port - Epic Breakdown

## Overview

This document breaks the `ship` Rust port into epics and stories. There is no PRD or Architecture document: the requirements come from `SPEC-ship-rust-port` (capabilities become FRs, constraints become NFRs), its `cli-contract.md` parity catalog, and `skills/ship/SKILL.md` as the behavior reference.

## Requirements Inventory

### Functional Requirements

FR1: `ship detect` prints platform (`azure|github|unknown`), remote, url, Azure org_url/project/repo, branch and inferred work item, matching `ship-detect.ts`; `SHIP_PLATFORM` overrides detection. (CAP-1)
FR2: `ship preflight` prints `branch`, `commits_ahead_of_upstream`, `staged`, `unstaged`, `untracked` and `scope_clean`, matching `ship-preflight.ts`, and always exits 0. (CAP-2)
FR3: `ship push` pushes the current branch and sets upstream; on Azure it uses an `az` Bearer token with `credential.helper` emptied and falls back to the stored credential when `az` is logged out; reports `push_ok=oauth-bearer|normal`; never force-pushes. (CAP-3)
FR4: `ship pr` opens a PR on the detected platform; on Azure it verifies the `--work-item` (or branch-inferred id), or creates one item per `--task`/`--tasks-file` entry assigned to `SHIP_ADO_ASSIGNEE`, and links it. (CAP-4)
FR5: `ship pr --related` verifies each id and links it *Related* to the PR's own work item, never to the PR. (CAP-4)
FR6: `ship pr --transition` moves each linked or created item after the PR opens; `completionOptions.transitionWorkItems` is set by a post-create update (unless `--no-complete-transition`) and `complete_transitions_work_items` is read back from that response. (CAP-4)
FR7: `ship pr` applies tags/labels from `--tag`, else derives them from the Conventional-Commit title, else the branch prefix, else `needs-review` with a warning; `--no-tag` disables. (CAP-4)
FR8: `ship pr` adds `--reviewer` (optional) and `--required-reviewer` (required on Azure) entries, resolving Azure UPNs to identities and skipping unresolvable ones with `reviewer_skipped`; `SHIP_ADO_DEFAULT_REVIEWER` applies on Azure when none is given; `--no-reviewer` disables. (CAP-4)
FR9: On GitHub, `ship pr` creates the PR, then attaches labels and reviewers in follow-up calls. (CAP-4)
FR10: `ship tag <pr-id>` adds, removes and lists PR tags (Azure) or labels (GitHub). (CAP-5)
FR11: `ship open` lists browser profiles from `Local State`, resolves an email to a profile directory, opens a URL in it (`--dry-run` resolves only), and `--set-default` writes `~/.config/ship/open.json`; works from WSL (Windows Edge/Chrome) and macOS. (CAP-6)
FR12: `ship snapshot` creates an annotated tag on HEAD named `v<YYYY.MM.DD-HHMM>` (`--daily`, `--name` override), with each `-m` as its own paragraph, refuses an existing tag with exit 3, and `--push` pushes it with the same auth as FR3. (CAP-7)
FR13: A prebuilt binary runs all seven subcommands on a clean Linux/WSL2 and a clean macOS host with no bun installed. (CAP-8)

### NonFunctional Requirements

NFR1: Behavioral parity: every flag, environment variable, `key=value` stdout line and exit code in `cli-contract.md` is preserved.
NFR2: `git`, `az` and `gh` are subprocess calls built from argument arrays, never shell strings.
NFR3: Tokens appear only in `Authorization` headers, are short-lived, and are never printed, logged or put in URLs; every Bearer git call empties `credential.helper`.
NFR4: No AI attribution in any commit, PR title or PR body the binary writes.
NFR5: Azure auth order is `az account get-access-token` first; `AZURE_DEVOPS_EXT_PAT`/`AZURE_DEVOPS_PAT` only after a 401/403 or when `az` is logged out.
NFR6: GitHub auth order is `GH_TOKEN`/`GITHUB_TOKEN`, then `gh auth token -u <owner>`, then the active account.
NFR7: Supported hosts are Linux/WSL2 and macOS.
NFR8: Rust only; no Python, npm or npx in build, test or install.
NFR9: Startup per subcommand is faster than the bun script it replaces, with a median under 50 ms for `detect` and `preflight` on Linux/WSL2. (Added from Barbosa's 2026-11-08 answer; 50 ms is the YOLO-mode default, change it before Story 5.1 if it is wrong.)

### Additional Requirements

- No Architecture document exists. Decisions the stories depend on and nothing records yet: the binary layout (one binary with subcommands is assumed), the HTTP or SDK crates for Azure DevOps and GitHub, and how the binary is distributed (committed builds, `cargo install`, or GitHub Releases).
- `SKILL.md` invocations change from `bun scripts/ship-x.ts` to `ship x` at cutover; the TypeScript scripts are retired afterwards (assumed).
- The existing `ship-lib.test.ts` cases are the parity baseline and are ported to Rust tests (assumed).
- Gotchas the port must keep (from `SKILL.md`): `createPullRequest` drops `completionOptions`; a GitHub 404 on create usually means the wrong account; `TF400813` right after a UPN rename is ADO's identity cache; titles are passed literally so `&` is never escaped.
- `ship-tag` (the release skill) is out of scope unless decided otherwise.

### UX Design Requirements

Not applicable: a CLI with no UI.

### FR Coverage Map

FR1: Epic 1 - `ship detect` (Story 1.1)
FR2: Epic 1 - `ship preflight` (Story 1.2)
FR3: Epic 2 - `ship push` with Azure Bearer auth (Story 2.1)
FR4: Epic 3 - Azure PR with verified or created work items (Stories 3.2, 3.3)
FR5: Epic 3 - related work items (Story 3.6)
FR6: Epic 3 - transitions and completion options (Story 3.5)
FR7: Epic 3 - tag derivation (Stories 3.1, 3.2)
FR8: Epic 3 - Azure reviewers (Story 3.4); GitHub reviewers (Story 3.1)
FR9: Epic 3 - GitHub PR with labels and reviewers (Story 3.1)
FR10: Epic 3 - `ship tag` (Story 3.7)
FR11: Epic 4 - `ship open` (Stories 4.1, 4.2)
FR12: Epic 2 - `ship snapshot` (Story 2.2)
FR13: Epic 1 - prebuilt binaries (Story 1.3); Epic 5 - bun-free cutover (Story 5.2)
NFR9: Epic 5 - startup benchmark (Story 5.1)
NFR1-NFR8: every story (cross-cutting; restated in acceptance criteria where a story touches them)

## Epic List

### Epic 1: First binary: inspect a repo
The operator installs a prebuilt `ship` binary with no bun and runs `ship detect` and `ship preflight`, getting the same output as the TS scripts. Settles the distribution decision.
**FRs covered:** FR1, FR2, FR13 (build and distribution)

### Epic 2: Push and checkpoint
The operator pushes branches and cuts snapshot tags from the binary, with Azure Bearer auth and the stored-credential fallback.
**FRs covered:** FR3, FR12

### Epic 3: Open and manage PRs
The operator opens PRs on GitHub and Azure Repos from the binary with work items, related links, transitions, tags and reviewers, and edits PR tags afterwards.
**FRs covered:** FR4, FR5, FR6, FR7, FR8, FR9, FR10

### Epic 4: Open a PR in the right browser profile
The operator opens any PR URL in the browser profile signed in with a chosen email, from WSL or macOS.
**FRs covered:** FR11

### Epic 5: Cut over: ship with no bun
`SKILL.md` drives the binary, the TS scripts are retired, and parity plus startup speed are proven on one Azure and one GitHub repo.
**FRs covered:** FR13 (final), NFR9

## Epic 1: First binary: inspect a repo

The operator installs a prebuilt `ship` binary with no bun and runs `ship detect` and `ship preflight`, getting the same output as the TS scripts.

### Story 1.1: Detect the delivery platform with `ship detect`

As an operator,
I want `ship detect` to report the platform, remote, Azure coordinates, branch and inferred work item of the repo I am in,
So that the first step of the ship flow runs from a compiled binary.

**Acceptance Criteria:**

**Given** a Rust crate under `skills/ship/` that builds a `ship` binary with `cargo build --release`
**When** I run `ship detect` in an Azure Repos clone and in a GitHub clone
**Then** it prints `platform`, `remote`, `url`, `org_url`, `project`, `repo`, `branch` and `work_item` with the same values and line order as `bun scripts/ship-detect.ts` in the same repo
**And** `SHIP_PLATFORM=azure|github` overrides detection, an SSH host alias that cannot be parsed prints `platform=unknown`, and the `detectKind`, `adoParts`, `parseWorkItem` and `githubOwnerRepo` cases from `ship-lib.test.ts` pass as Rust unit tests
**And** `git` is called through an argument array, never a shell string (NFR2), and `ship --help` and `ship detect --help` exit 0

### Story 1.2: Audit delivery scope with `ship preflight`

As an operator,
I want `ship preflight` to tell me what would be delivered and whether files outside the change are left behind,
So that I catch scope mistakes before committing.

**Acceptance Criteria:**

**Given** a repo with commits ahead of upstream plus staged, unstaged and untracked files
**When** I run `ship preflight`
**Then** it prints `branch`, `commits_ahead_of_upstream`, `staged`, `unstaged`, `untracked` and `scope_clean` with the same values as `ship-preflight.ts`
**And** it exits 0 in every case, including a branch with no upstream (advisory, never blocks)
**And** the `parsePorcelainStatus` and `scopeAudit` cases from `ship-lib.test.ts` pass as Rust unit tests

### Story 1.3: Install a prebuilt binary without bun

As an operator on a new machine,
I want to install `ship` as a prebuilt binary,
So that I never run `bun install` or keep `node_modules` to use the skill.

**Acceptance Criteria:**

**Given** the distribution choice (committed per-platform builds, `cargo install` from the repo, or GitHub Releases) recorded as a decision in `skills/ship/` with its reason
**When** a release of the binary is produced
**Then** binaries exist for Linux x86_64 (WSL2) and macOS arm64, built without npm, npx or Python (NFR8)
**And** on a host with no bun installed, following the documented install step gives a working `ship detect` and `ship preflight`
**And** `ship --version` prints the version that release recorded

## Epic 2: Push and checkpoint

The operator pushes branches and cuts snapshot tags from the binary, with Azure Bearer auth and the stored-credential fallback.

### Story 2.1: Push the current branch with `ship push`

As an operator,
I want `ship push` to push my branch and set its upstream on either platform,
So that a stale stored credential never blocks delivery.

**Acceptance Criteria:**

**Given** a feature branch in an Azure Repos clone with `az` logged in
**When** I run `ship push`
**Then** the push uses `az account get-access-token` as an `Authorization: Bearer` header with `credential.helper` emptied, sets upstream, and prints `push_ok=oauth-bearer`
**And** with `az` logged out it falls back to the stored git credential and prints `push_ok=normal`; on GitHub it pushes normally
**And** `-r/--remote` and `-b/--branch` work as in `ship-push.ts`, a rejected push exits non-zero without retrying with force, and the token never appears in output, logs or the remote URL (NFR3, NFR5)

### Story 2.2: Save a checkpoint with `ship snapshot`

As an operator,
I want `ship snapshot` to tag HEAD with a self-describing annotated tag,
So that I have a return point before risky work.

**Acceptance Criteria:**

**Given** a repo on any branch
**When** I run `ship snapshot -m "why" -m "verification"`
**Then** an annotated tag named `v<YYYY.MM.DD-HHMM>` is created on HEAD whose first paragraph is `Snapshot <tag> — <branch> @ <shorthash>` and each `-m` is its own paragraph, and it prints `tag`, `commit`, `branch` and `pushed=false`
**And** `--daily` names it `v<YYYY.MM.DD>`, `--name` sets it exactly, and an existing tag is refused with exit 3 without moving it
**And** `--push` pushes the tag with the same auth order as Story 2.1 and prints `pushed=true`

## Epic 3: Open and manage PRs

The operator opens PRs on GitHub and Azure Repos from the binary with work items, related links, transitions, tags and reviewers, and edits PR tags afterwards.

### Story 3.1: Open a GitHub PR with labels and reviewers

As an operator on a GitHub repo,
I want `ship pr` to open a PR with labels and requested reviewers,
So that GitHub delivery runs from the binary end to end.

**Acceptance Criteria:**

**Given** a pushed branch in a GitHub repo, and the HTTP client choice for the GitHub and Azure DevOps REST APIs (a crate such as `octocrab` or `azure_devops_rust_api`, or direct REST calls) recorded as a decision in `skills/ship/` with its reason, after checking each candidate crate is maintained
**When** I run `ship pr --title "<t>" --body-file <f>` with optional `--tag`, `--reviewer`, `--draft`, `--source`, `--target`
**Then** the PR is created, labels and reviewers are attached in follow-up calls, and it prints `platform`, `pr_url`, `pr_number` and one `tag_added`/`reviewer_added` line each
**And** with no `--tag`, labels derive from the Conventional-Commit title, else the branch prefix, else `needs-review` with a warning; `--no-tag` adds none; the `parseTags` and `defaultTagsFromTitle` test cases pass
**And** the token comes from `GH_TOKEN`/`GITHUB_TOKEN`, else `gh auth token -u <owner>`, else the active account (NFR6); the title is sent literally so `&` stays `&`; nothing in the title or body carries AI attribution (NFR4)

### Story 3.2: Open an Azure PR linked to an existing work item

As an operator on Azure Repos,
I want `ship pr` to open a PR linked to a work item that is verified to exist,
So that no PR reaches review without a real Board item.

**Acceptance Criteria:**

**Given** a pushed branch in an Azure Repos clone and a work item id from `--work-item` or the branch name
**When** I run `ship pr --title "<t>" --body-file <f> --no-create-work-item`
**Then** the id is checked with a work-item read before use, and the PR is created in one call carrying the work-item link, tags and `--draft`, printing `pr_url`, `pr_id` and `work_item`
**And** a branch number that is not a real work item is reported and not linked
**And** Azure auth tries the `az` token first and the PAT variables only after a 401/403 or with `az` logged out (NFR5)

### Story 3.3: Create and assign work items when none exist

As an operator,
I want `ship pr` to create one work item per task when no real item is linked,
So that I am never asked for a work-item id.

**Acceptance Criteria:**

**Given** an Azure branch with no verifiable work item
**When** I run `ship pr` with no `--task`, with repeated `--task "<title>"`, or with `--tasks-file <file>`
**Then** one item is created from the PR title, or one per task, each assigned to `--assignee` or `SHIP_ADO_ASSIGNEE`, linked to the PR, and printed as `work_item_created=<id>` plus `work_items=<ids>`
**And** `--work-item-type "User Story"|Bug` sets the type (default `Task`) and `--no-create-work-item` disables creation
**And** the created ids printed are the ones the API returned

### Story 3.4: Add optional and required reviewers on Azure

As an operator,
I want to name reviewers by UPN on Azure PRs,
So that the PR records who was asked to review.

**Acceptance Criteria:**

**Given** an Azure PR being opened
**When** I pass `--reviewer` and `--required-reviewer` (comma-separated and repeatable)
**Then** each UPN is resolved to an identity and added in the create call, printing `reviewer_added=<name> required=<bool>`
**And** an unresolvable name prints `reviewer_skipped=<name>` and the PR still opens
**And** with neither flag, `SHIP_ADO_DEFAULT_REVIEWER` is added as optional if set, and `--no-reviewer` adds none

### Story 3.5: Transition work items on open and on completion

As an operator,
I want linked work items to move state when the PR opens and when it completes,
So that the Board stays truthful without manual clicks.

**Acceptance Criteria:**

**Given** an Azure PR with linked or created work items
**When** I pass `--transition <state>`
**Then** each item moves to that state after the PR opens
**And** unless `--no-complete-transition` is passed, `completionOptions.transitionWorkItems=true` is set by an update after create, and `complete_transitions_work_items` is printed from the update response, not from the flag
**And** the flags are ignored on GitHub

### Story 3.6: Link related work items without closing them

As an operator,
I want `--related <id>` to tie a long-lived item to the PR's own work item,
So that completing the PR never closes an epic or backlog item.

**Acceptance Criteria:**

**Given** an Azure PR whose own item is from `--work-item` or created in Story 3.3
**When** I pass `--related <id>` (comma-separated or repeatable)
**Then** each id is verified, linked *Related* to the own item, never linked to the PR, and printed as `related_linked=<own>-><id>`
**And** a warning is printed when the PR body or a commit message mentions a related id (`#<id>` or `AB#<id>`)
**And** the `parseRelatedIds` and `mentionsWorkItem` test cases pass

### Story 3.7: Manage tags on an existing PR with `ship tag`

As an operator,
I want to add, remove and list tags or labels on an open PR,
So that I can change its triage signal after review starts.

**Acceptance Criteria:**

**Given** an open PR on Azure (`pr_id`) or GitHub (`pr_number`)
**When** I run `ship tag <id> --add "a,b"`, `--remove "a"` or `--list`
**Then** tags change on the platform and it prints `tag_added`/`tag_removed` lines or the current list
**And** re-adding an existing tag succeeds without error, and a missing GitHub label is created
**And** `--pr` and `-r/--remote` behave as in `ship-tag.ts`

## Epic 4: Open a PR in the right browser profile

The operator opens any PR URL in the browser profile signed in with a chosen email, from WSL or macOS.

### Story 4.1: Resolve an email to a browser profile

As an operator with several signed-in browser accounts,
I want `ship open` to list profiles and resolve an email to one,
So that I can see which account a PR will open under.

**Acceptance Criteria:**

**Given** Edge or Chrome installed on Windows (seen from WSL) or on macOS
**When** I run `ship open --list-profiles`
**Then** it prints `browser=` and one `profile=<dir>\t<email>\t<name>` line per account read from that browser's `Local State`, matching `ship-open.ts`
**And** `ship open <url> --profile <email> --dry-run` prints the resolved `profile_dir` without launching, and an unknown email falls back to the Default profile with a note on stderr
**And** `--set-default <email> [--browser edge|chrome]` writes `~/.config/ship/open.json` (or under `XDG_CONFIG_HOME`) in the same format the TS script reads

### Story 4.2: Launch the PR in the chosen profile

As an operator,
I want `ship open <url> --profile <email>` to open the PR in that account's window,
So that I review with the right permissions.

**Acceptance Criteria:**

**Given** a resolved profile from Story 4.1
**When** I run `ship open <url> --profile <email>`
**Then** on WSL it launches the Windows browser through `cmd.exe start` with that profile directory, and on macOS through `open -a`, printing `opened_url` and `profile_dir`
**And** the launch arguments are an array, never a shell string, so a URL with `&` opens intact (NFR2)
**And** with no `--profile`, the remembered default email is used when set

## Epic 5: Cut over: ship with no bun

`SKILL.md` drives the binary, the TS scripts are retired, and parity plus startup speed are proven on one Azure and one GitHub repo.

### Story 5.1: Prove parity and startup speed against the TS scripts

As an operator,
I want a repeatable check that runs every subcommand through the TS script and the binary side by side,
So that cutover rests on evidence, not trust.

**Acceptance Criteria:**

**Given** one Azure Repos clone and one GitHub clone
**When** the parity check runs every read-only subcommand and a dry-run or throwaway-branch variant of every write subcommand through both implementations
**Then** it reports any difference in `key=value` lines or exit codes, and the run shows none
**And** it records median startup time per subcommand for both, and the binary is faster for each, with `detect` and `preflight` under a 50 ms median on Linux/WSL2 (NFR9)
**And** the check needs no npm, npx or Python (NFR8)

### Story 5.2: Switch the skill to the binary and retire the TS scripts

As an operator,
I want the ship skill to call `ship <subcommand>` and nothing else,
So that the skill works on a machine with no bun.

**Acceptance Criteria:**

**Given** Story 5.1 passing
**When** `SKILL.md`, its references and `assets/` are updated
**Then** every `bun scripts/ship-*.ts` invocation becomes `ship <subcommand>` with the same flags, and the bun-install setup note is replaced by the install step from Story 1.3
**And** `scripts/*.ts`, `package.json`, `tsconfig.json` and `node_modules` are removed from `skills/ship/`
**And** on a host with no bun, a full ship run (preflight, push, PR with work item, tags, reviewers) succeeds on the Azure and the GitHub repo
