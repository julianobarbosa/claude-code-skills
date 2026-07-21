---
name: ship
description: >-
  End-to-end branch delivery: commit (no AI attribution) → push → open a pull request → ensure a
  Board work item exists (create one per task, assigned to the configured user, if none) and link
  it → after merge, clean up branch and worktree. Auto-detects the platform from the remote —
  Azure Repos + Boards (azure-devops-node-api SDK; OAuth Bearer push fallback via `az`) or GitHub
  (Octokit; `gh` for auth). Scripts are TypeScript, run via `bun`. Use whenever
  asked to "ship", "ship it", "ship this branch", "open a PR", "push and open a PR", "raise a PR",
  "deliver this", "send this for review", or "create a PR and link the work item" — and when a
  direct push to main is blocked and the change needs to go through a PR instead. Also covers
  snapshotting the current state as an annotated git tag — use whenever asked to "save the current
  state", "tag this", "snapshot the state", "create a checkpoint", "tag a release point", or "mark
  where we are" (a git-tag checkpoint, distinct from PR labels/tags). Also opens a just-created (or
  any) PR in a chosen browser account profile — use whenever asked to "open the PR in my browser",
  "open it in Edge/Chrome", or "open the PR as <account>".
allowed-tools:
  - Bash
  - Read
metadata:
  platform: azure-devops, github
---

# Ship

`ship` takes a finished branch the last mile: commit it cleanly, push it (working around Azure
DevOps auth when needed), open a pull request, link it to its work item, and — once it's merged —
tear down the branch and worktree. It auto-detects whether you're on **Azure Repos** or **GitHub**
and follows the matching path, so the same command works at your organization and in a github.com repo.

It is deliberately narrow. It does *not* merge locally, run pipelines, or manage backlogs — it
hands a reviewable PR to the platform and cleans up after the merge.

## When to use this vs. neighbors

- **`ship`** — the PR-based delivery flow: push → PR → (merge happens via the platform) → cleanup.
- **`commit`** — just stage + commit + push the current branch, no PR.
- **`merge`** — merge a branch into `main` *locally* (fast-forward) and clean up. Use this when there's
  no PR gate; use `ship` when changes must go through review/policy.
- **`azure-devops`** — the deep REST/MCP toolbox (WIQL, batch updates, pipelines, comment threads).
  `ship` calls only the thin slice it needs; reach for `azure-devops` for anything richer.

## The flow

Run `bun scripts/ship-detect.ts` first — it prints the platform, the Azure org/project/repo (if
any), the branch, and an inferred work-item id. Everything below branches on that.

> **One-time setup:** the scripts depend on `azure-devops-node-api` and `@octokit/rest`. Run
> `bun install` in the skill dir (`~/.claude/skills/ship/`) once before first use.

### 0. Preflight
- Confirm there's something to deliver: `git status` and `git log --oneline @{u}.. 2>/dev/null`.
- Note the platform from `ship-detect.ts`. If it says `unknown` (e.g. a custom SSH host alias),
  set `SHIP_PLATFORM=azure` or `SHIP_PLATFORM=github` for the session.

### 1. Commit — as the author, never as the tool
Stage only files for this task and commit. **Never add AI attribution** — no
`Generated with Claude`, no `Co-Authored-By: Claude`. Commits are authored by the human; tooling
provenance does not belong in git history (this repo's `commit-msg` hook strips trailers as a
backstop, but don't rely on it — don't write them in the first place). If pre-commit hooks fail on
*unrelated* issues, `--no-verify` is acceptable; if they flag *your* change, fix it.

### 2. Branch posture
- **On a feature branch** → good, continue.
- **On `main`/`master`** → you can't open a PR from main into itself. Create a branch and move the
  commit onto it before pushing:
  ```bash
  git branch feature/<slug> && git reset --hard @{u} && git checkout feature/<slug>
  ```
  (Only do this when the commits aren't yet pushed to main. If unsure, stop and ask.)
- A **blocked direct push to main** (branch policy) is the signal to take the PR path — not to
  force-push or bypass the policy.

### 3. Push
```bash
bun scripts/ship-push.ts         # pushes current branch, sets upstream
```
On Azure DevOps, if the normal push fails on auth, this automatically mints an `az` OAuth token and
retries with a Bearer header — the fallback for when neither SSH nor an HTTPS credential helper is
available. See `references/azure-devops.md` for the mechanics.

### 4. Open the PR (+ ensure/link work item, + transition state)

> **Invariant — never ask the user for the work item id.** Resolving → verifying → (if missing)
> creating + assigning + linking the work item is *fully automatic*. A PR must never be surfaced
> as ready without a linked Board work item. If you're about to ask "what's the work-item id?",
> stop — that question is the exact failure this skill exists to prevent. The id comes from
> `--work-item`, the branch name, or a freshly created item; it never comes from a question.
>
> **Code review does not own the work item.** Because ship guarantees a linked item at PR-open,
> the review step — human reviewers or the `code-review` / `bmad-code-review` skills — must not
> re-prompt for or block on a work item. That concern is already satisfied upstream.

Draft a real description — copy `assets/pr-template.md` to a temp file, fill Summary / Changes /
Verification, and keep the `AB#<id>` line so the work item links.

```bash
bun scripts/ship-pr.ts --title "<title>" --body-file /tmp/pr-body.md \
  --work-item <id> --transition Resolved \
  --reviewer alice@corp.com --required-reviewer lead@corp.com --tag needs-review
```
- Platform is auto-detected; the script uses the **azure-devops-node-api** SDK (`createPullRequest`)
  or **Octokit** (`pulls.create`).
- **Prerequisites ride along in the create, not as follow-up round trips.** On Azure the work item,
  tags/labels, and reviewers are all packed into the single `createPullRequest` call. On GitHub the
  create API accepts none of those, so labels + reviewers are attached in follow-up calls — same
  result, just unavoidable there.
- **Reviewers** — `--reviewer <upn|username>` adds an optional (non-blocking) reviewer;
  `--required-reviewer` marks it **required** on Azure (blocks completion). Both are comma-separated
  and/or repeatable. On Azure a UPN/email is resolved to an identity; an unresolvable name is warned
  and skipped (`reviewer_skipped=…`), never blocking the PR. GitHub has no per-PR "required"
  reviewer (that's branch protection), so required ones are just requested. The script prints
  `reviewer_added=<name> required=<bool>` for each.
  When neither flag is given, `$SHIP_ADO_DEFAULT_REVIEWER` (if set) is added as an optional
  reviewer — a PR with no reviewer record leaves no trace that anyone was asked. Unset = no
  reviewer, the prior behaviour.
- **Azure never opens a PR without a linked Board work item.** The script resolves the id from
  `--work-item` (or the branch name), then **verifies it actually exists** via the SDK
  (`getWorkItem`). The branch-name parse is only a heuristic — a branch like `1234-foo` can carry a
  number that isn't a real item, which is why existence is checked, not assumed.
- **If no real work item is found, one is created per task and linked to the PR**, each **assigned
  to** `$SHIP_ADO_ASSIGNEE` (default `you@example.com`; override with `--assignee`).
  Pass `--task "<title>"` once per task (repeatable), or `--tasks-file <file>` (one title per line),
  to create one item each. With no `--task`, a single item is created from the PR `--title`. Type
  defaults to `Task` (`--work-item-type "User Story"|Bug`). Disable creation with
  `--no-create-work-item` to link only a pre-existing id.
  - The script prints `work_item_created=<id>` per created item and `work_items=<ids>` for the set —
    surface the new ids to the user (don't fabricate them; they come from the SDK response).
- `--transition` (Azure only) moves **each** linked/created item *after* the PR opens. State names
  are process-specific (Agile: Resolved; Scrum: Committed; Basic: Doing) — verify the valid next
  state first; see `references/azure-devops.md`. Omit `--transition` to leave the board untouched.
  (Created items start in the type's initial state, e.g. `New`/`To Do`.)
- The script prints `pr_url=…`; surface it to the user.

### 4b. Tag the PR (optional, recommended)
Azure DevOps calls them **tags**; GitHub calls them **labels** — same idea: a small, visible signal
that helps reviewers triage and helps the team organize PRs. Microsoft's guidance is that tags
"communicate extra information to reviewers, such as that the PR is still a work in progress, or is a
hotfix for an upcoming release" ([Add tags to a pull request](https://learn.microsoft.com/azure/devops/repos/git/pull-requests#add-tags-to-a-pull-request)).

**A PR is never opened bare.** With no `--tag`, `ship-pr.ts` derives a type label
from the branch prefix (`feat/…` → `feat`, `fix/`|`hotfix/`|`bugfix/` → `fix`,
`docs/` → `docs`, `chore/` → `chore`, `refactor/` → `refactor`) and prints a
`NOTE`. An unrecognised prefix gets a `WARNING`, not a failure — no platform has a
"require a label" policy, so this is the only enforcement point, and a hard error
here would break repos with other conventions.

Apply tags at PR-open time with `--tag` (comma-separated and/or repeatable):

```bash
bun scripts/ship-pr.ts --title "<title>" --body-file /tmp/pr-body.md \
  --work-item <id> --transition Resolved --tag "hotfix,do-not-merge"
```

…or manage tags on an already-open PR with `ship-tag.ts` (the id is `pr_id=` on Azure / `pr_number=`
on GitHub, both printed by `ship-pr.ts`):

```bash
bun scripts/ship-tag.ts <pr-id> --add "needs-review"     # add
bun scripts/ship-tag.ts <pr-id> --remove "do-not-merge"  # remove
bun scripts/ship-tag.ts <pr-id> --list                   # show current tags
```

Tags are free-form on both platforms (Azure creates the tag definition on first use; GitHub
auto-creates a missing label). For a recommended, consistent tag set — `do-not-merge`, `work-in-progress`,
`hotfix`, plus type/area conventions — see the **Recommended tags** section of
`references/azure-devops.md` / `references/github.md`.

### 4c. Open the PR in the browser (optional)
Review actually happens on the PR page, and **which signed-in account you open it under matters**
when you juggle several (work vs. personal vs. cloud) — the wrong profile shows the wrong
permissions, or no access at all. So after the PR opens, **always surface the `pr_url`**, then ask
whether to open it in the browser. Opening is opt-in, never automatic (a browser window is a visible
side effect; the user asked to be prompted).

`ship-open.ts` resolves an **email → browser profile** by reading the browser's own `Local State`
(the same account map its profile switcher shows), then launches that profile at the URL. It works
on WSL (→ Windows Edge/Chrome) and macOS (→ Chrome/Edge). Nothing is baked in — the map is
discovered live each run, the email is an argument, and only your *default* email is remembered, in
`~/.config/ship/open.json` (outside this skill).

Discover the accounts, then ask the user which one with **AskUserQuestion** (only worth prompting
when there's more than one; offer each account plus a "don't open" choice):

```bash
bun scripts/ship-open.ts --list-profiles   # prints browser= + one `profile=<dir>\t<email>\t<name>` per account
```

Open the PR under the chosen account (add `--dry-run` first if you want to confirm the resolved
profile without a window):

```bash
bun scripts/ship-open.ts "<pr_url>" --profile <email>              # opens; prints opened_url= / profile_dir=
bun scripts/ship-open.ts "<pr_url>" --profile <email> --dry-run    # resolve only, no window
```

Remember the pick as the default so future ships offer it with one keypress:

```bash
bun scripts/ship-open.ts --set-default <email> [--browser edge|chrome]
```

An unknown or omitted email falls back to the browser's Default profile (with a note on stderr)
rather than guessing wrong. This step is independent of the merge/cleanup below — opening the PR to
review it doesn't advance or block anything.

### 5. After merge — cleanup
Do this only once the PR is actually merged (don't delete a branch with an open PR). Mirror the
`merge` skill's cleanup, and **ask before deleting**:
- If the branch was developed in a **worktree**, `cd` to the main repo dir first, then
  `git worktree remove <path>` — you can't delete a branch from inside its own worktree.
- `git branch -d <branch>` (lowercase `-d` refuses unmerged branches — that refusal is the safety
  net; only escalate to `-D` if the user explicitly confirms).
- `git push origin --delete <branch>` (ignore failure if it was local-only).

### 6. Snapshot the state (optional)
Independent of the PR flow — reach for this any time you want a return-to point: after a clean
merge to `main`, before a risky migration, or just to mark "everything works here." It creates an
**annotated git tag** on `HEAD` (the working tree is irrelevant — a tag names a commit).

```bash
bun scripts/ship-snapshot.ts \
  -m "what changed / why you're saving here" \
  -m "verification status"
```

The script auto-fills what's easy to get wrong by hand:
- **Name** defaults to `v<YYYY.MM.DD-HHMM>` (minute-granular so repeated snapshots in a day don't
  collide). Pass `--daily` for a once-a-day `v<YYYY.MM.DD>`, or `--name <tag>` for an exact name.
- **First message paragraph** is auto-generated — `Snapshot <tag> — <branch> @ <shorthash>` — so the
  tag is self-describing even with no `-m`. Each `-m` you add becomes its own paragraph (passed via
  an arg array, so real newlines/punctuation survive — unlike a `\n` inside a single shell string).
- **Collision is refused, not clobbered** (exit 3) — a snapshot must never silently move a tag
  someone relies on.

Tags are **local until pushed** (shared/visible — confirm first, like opening a PR). Add `--push` to
push to `origin`; on Azure it falls back to the `az` OAuth Bearer header the same way `ship-push.ts`
does. The script prints `tag=`, `commit=`, `branch=`, `pushed=`.

## Bundled tools

| Script | Does |
|--------|------|
| `bun scripts/ship-detect.ts [remote]` | Print platform + Azure coordinates + branch + inferred work item |
| `bun scripts/ship-push.ts [-r remote] [-b branch]` | Push + set upstream; Azure OAuth Bearer fallback on auth failure |
| `bun scripts/ship-pr.ts --title … [opts]` | Open PR on the detected platform; ensure/create + link work item(s) (assigned to the configured user); optional Board transition; optional `--tag`; optional `--reviewer`/`--required-reviewer` — work item + tags + reviewers packed into one create call on Azure |
| `bun scripts/ship-tag.ts <pr-id> [--add\|--remove "t1,t2"] [--list]` | Add / remove / list PR tags (Azure) or labels (GitHub) on an existing PR |
| `bun scripts/ship-open.ts <url> [--profile <email>] [--dry-run]` | Open a PR/URL in a chosen browser **account profile** (email→profile via the browser's `Local State`); WSL→Edge/Chrome, macOS→Chrome/Edge; also `--list-profiles`, `--set-default` |
| `bun scripts/ship-snapshot.ts [-m "para"]… [--daily] [--name <tag>] [--push]` | Save current state as an annotated **git tag** (date-named, self-describing subject); optional push with Azure OAuth fallback |

Scripts are TypeScript run via `bun`; shared helpers live in `scripts/ship-lib.ts`. Run `bun install`
in the skill dir once (installs `azure-devops-node-api` + `@octokit/rest`). Git/push stays a
subprocess call (it's a git operation); only the ADO/GitHub REST surfaces use the SDKs. Platform
detail lives in `references/azure-devops.md` and `references/github.md` — read the one matching the
detected platform. The PR description starts from `assets/pr-template.md`.

## Safety

- **Ask before anything destructive or shared-visible** — deleting branches/worktrees, and opening a
  PR (it's visible to the team). Pushing a feature branch and creating a draft are low-risk; a
  ready PR and any branch deletion warrant a confirm.
- **Never force-push** to work around a rejected push. A rejection means diverged history or a
  policy — investigate, don't overwrite.
- **Tokens go in headers, are short-lived, and are never printed or put in URLs.**
- **No AI attribution** anywhere — commit message, PR title, or PR body.

## Gotchas

- Both PR-create paths (Octokit `pulls.create`, ADO `createPullRequest`) require the branch to be
  **pushed first** — keep step 3 before step 4.
- `ship-detect.ts` returning `unknown` is almost always a custom SSH host alias — set `SHIP_PLATFORM`.
  (A `dev.azure.com-<alias>` SSH host is detected as azure but its org/project/repo won't parse —
  same limitation the shell version had; pass coordinates/`--work-item` explicitly if needed.)
- Scripts need deps: if you see `Cannot find module 'azure-devops-node-api'`, run `bun install` in
  the skill dir.
- A linked work item does **not** change state on its own; transitioning is a separate step (4).
- If `AZURE_DEVOPS_EXT_PAT` is set but under-scoped (e.g. Code-only, missing Work Items / Pull
  Request write), `ship-pr.ts` auto-detects the 401/403 and retries with the `az` OAuth bearer
  token — no need to unset the PAT manually. The fallback requires `az login` as an org member.
- Don't hand-roll the PR with raw `az repos pr create` / `gh pr create` and then bolt the work item
  on afterward — that path skips the auto-create+link invariant and forces a manual "what's the id?"
  round-trip with the user. Use `ship-pr.ts` so the work item is guaranteed at PR-open.
- Deleting a branch while its PR is still open abandons the PR — clean up only after merge (step 5).
- `ship-open.ts` matches `--profile <email>` against the browser's **signed-in** account emails, so a
  profile with no account attached is only reachable as the Default fallback, not by email. It
  auto-picks the installed browser (chrome preferred if both) and needs no deps or network — just the
  browser's local `Local State` file. If it can't find that file, the browser isn't installed where
  expected; pass `--browser` or check the path it printed.
- **Three different "tags" — don't mix them up.** (1) PR tags/labels (`--tag`, `ship-tag.ts`) — a
  triage signal on the PR. (2) Work items (step 4) — the traceability link. (3) Git tags
  (`ship-snapshot.ts`) — a commit checkpoint in history. `ship-tag.ts` takes a **PR id**;
  `ship-snapshot.ts` takes **no positional arg** and tags `HEAD`. Same word, three concepts.
- **Re-adding a tag is safe** — Azure `createPullRequestLabel` returns the existing definition rather
  than erroring, and GitHub dedupes; `parseTags` also drops blank/duplicate names from the CSV.
- **`ship-tag.ts` needs the PR id** — Azure uses the numeric `pr_id`, GitHub uses the `pr_number`
  (both emitted by `ship-pr.ts`). On GitHub a tag that names a non-existent label is auto-created.
