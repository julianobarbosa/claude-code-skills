# Ship — Azure DevOps path

Detail for the Azure Repos + Boards half of `ship`. Read this when the remote is `dev.azure.com` / `*.visualstudio.com`.

## Authentication: the OAuth Bearer fallback

Azure DevOps git over HTTPS needs a credential. On a workstation where the SSH key isn't loaded and no HTTPS credential helper is configured, both push transports fail — but if `az login` is done, you can borrow its token.

`scripts/ship-push.ts` does this automatically: it tries a normal `git push` first, and only on failure mints a token and retries with a Bearer header. The mechanics, if you ever run it by hand:

```bash
TOKEN=$(az account get-access-token --resource 499b84ac-1321-427f-aa17-267ca6975798 --query accessToken -o tsv)
git -c http.extraHeader="Authorization: Bearer $TOKEN" push -u origin <branch>
```

- `499b84ac-1321-427f-aa17-267ca6975798` is the **constant** Azure DevOps API resource id — not a secret, the same for every org.
- The token lives ~60 minutes. Re-mint per command if a long session crosses the boundary.
- The token goes in a **header**, never in the URL — URLs leak to logs, history, and referrers.
- The same token drives the SDK: `ship-pr.ts` passes it to `azdev.getBearerHandler(token)` and builds a `WebApi` connection (no `AZURE_DEVOPS_EXT_PAT` env var needed — that was the CLI path).

## Coordinates

The SDK needs the org URL + project + repo. `ship-pr.ts` parses them from the remote URL (via `adoParts` in `ship-lib.ts`) so it works on any clone, with no reliance on `az devops configure --defaults` machine state. Run `bun scripts/ship-detect.ts` to see what it resolved.

## Linking work items

Two complementary mechanisms — use both:

1. **Hard link** — `az repos pr create --work-items <id> [<id> …]` attaches work item(s) to the PR (space-separated for multiple). This is what drives traceability and, with branch policies, can auto-resolve on completion.
2. **`AB#<id>` mention** — putting `AB#1234` in the PR description (the template does) renders as a live link in the Azure DevOps UI.

`ship-pr.ts` infers the id from the branch name (`feature/AB1234-foo`, `1234-foo`) when `--work-item` is omitted. The inference is a heuristic — pass `--work-item` explicitly when the branch name doesn't carry it.

### Ensure-or-create (a PR always carries a work item)

`ship-pr.ts` **verifies** the resolved id before trusting it (SDK `wit.getWorkItem(id)`), then **creates** items when none exist (`wit.createWorkItem(...)` with a JSON-patch document), and links them on PR create (`git.createPullRequest({ ..., workItemRefs })`). The equivalent CLI calls, for reference:

```bash
# Existence check — the branch parse is a heuristic, so confirm the id is real:
az boards work-item show --id <id> --organization <org_url> --query id -o tsv

# Create one item per task, assigned to a user, and capture the new id:
az boards work-item create --type "Task" --title "<task title>" \
  --assigned-to "you@example.com" \
  --organization <org_url> --project <project> --query id -o tsv
```

The SDK builds the same JSON-patch document the CLI sends — `/fields/System.Title` and
`/fields/System.AssignedTo` on create, `/fields/System.State` on transition.

- `--assigned-to` accepts a UPN/email/display name. `ship-pr.ts` defaults it to `$SHIP_ADO_ASSIGNEE` (fallback `you@example.com`); override per-run with `--assignee`.
- One work item is created **per `--task`** (or per line of `--tasks-file`); with no tasks given, a single item is created from the PR title. All created ids are passed to `az repos pr create --work-items` in the same call, so creation and linking happen together.
- Created items start in their type's **initial state** (`New` for Agile/Scrum/CMMI, `To Do` for Basic). Use `--transition` to advance them once the PR is open; it now applies to **every** linked id.
- **Linking an item to an already-open PR** (when you didn't create it at PR-open time) is a separate command: `az repos pr work-item add --id <pr_id> --work-items <id> --organization <org_url>`.
- Report the `work_item_created=<id>` / `work_items=<ids>` lines the script emits — never invent a work-item id; it must come from real `az` output.

## Transitioning Board state

State names depend on the project's **process**, so there's no universal "Resolved". Check before transitioning:

```bash
az boards work-item show --id <id> --query "fields.\"System.WorkItemType\"" -o tsv
```

| Process | Typical states (New → Done) |
|---------|-----------------------------|
| Agile   | New → Active → Resolved → Closed |
| Scrum   | New → Approved → Committed → Done |
| Basic   | To Do → Doing → Done |
| CMMI    | Proposed → Active → Resolved → Closed |

Common pairing: transition to **Resolved/Committed** when the PR opens, and let the PR completion (or a manual step) move it to **Closed/Done**. `ship-pr.ts --transition Resolved` does the open-time half.

Some workflows restrict which transitions are legal from a given state; an illegal transition errors. If it fails, read the current state and pick a reachable next state.

## PR completion options

`ship` opens the PR; merging is usually a human/policy gate. When you do want to drive completion:

```bash
# Set auto-complete so the PR merges once policies pass (squash, delete source branch):
az repos pr update --id <pr_id> --auto-complete true --squash true --delete-source-branch true \
  --organization <org_url>

# Add reviewers:
az repos pr reviewer add --id <pr_id> --reviewers <upn-or-id> --organization <org_url>
```

Merge strategies: `--squash`, `--merge` (no-FF, default), `--rebase`, `--rebase-merge`.

## Tags (PR labels)

Azure DevOps PR **tags** are the same primitive the REST API calls **labels** (`WebApiTagDefinition`).
They surface in the PR "Tags" panel and exist to "communicate extra information to reviewers, such as
that the PR is still a work in progress, or is a hotfix for an upcoming release"
([Add tags to a pull request](https://learn.microsoft.com/azure/devops/repos/git/pull-requests#add-tags-to-a-pull-request)).
They are advisory triage signals — independent of work-item links and of Board state.

`ship-tag.ts` uses the `azure-devops-node-api` `IGitApi` label methods:

| Action | SDK call |
|--------|----------|
| Add | `git.createPullRequestLabel({ name }, repoId, prId, project)` → `WebApiTagDefinition` |
| List | `git.getPullRequestLabels(repoId, prId, project)` → `WebApiTagDefinition[]` |
| Remove | `git.deletePullRequestLabels(repoId, prId, labelIdOrName, project)` |

Tags are **free-form**: the definition is created on first use, so there's no pre-registration step.
Re-adding an existing tag returns the existing definition (not an error); removing a tag the PR
doesn't carry returns 404 (treated as non-fatal). Auth reuses the PAT→`az` OAuth-bearer fallback —
an under-scoped PAT (Code-only, missing **Pull Request** write) 401s, and the script retries with the
bearer.

```bash
# At PR open:
bun scripts/ship-pr.ts --title "Hotfix: cert rotation" --body-file /tmp/pr-body.md \
  --work-item 794 --transition Resolved --tag "hotfix,do-not-merge"

# On an existing PR (numeric pr_id from ship-pr.ts):
bun scripts/ship-tag.ts 41666 --add "work-in-progress"
bun scripts/ship-tag.ts 41666 --remove "work-in-progress" --add "needs-review"
bun scripts/ship-tag.ts 41666 --list

# Equivalent raw REST (reference only — prefer the script):
#   POST   {org}/{project}/_apis/git/repositories/{repo}/pullRequests/{prId}/labels?api-version=7.1
#   GET    …/labels    DELETE …/labels/{labelIdOrName}
```

### Recommended tags (best practice)

Microsoft documents the *purpose* (WIP / DO-NOT-MERGE / hotfix) but leaves the vocabulary to the team.
Keep the set small, lowercase, hyphenated, and consistent — tags only help triage if everyone uses the
same words. A practical starter taxonomy:

| Category | Tags | Use |
|----------|------|-----|
| **Status** (MS-documented) | `work-in-progress`, `do-not-merge` | PR not ready to complete — pairs with draft PRs |
| **Type** | `hotfix`, `bug`, `feature`, `chore`, `docs` | What kind of change this is |
| **Release** (MS-documented) | `hotfix`, `release-blocker`, `next-release` | Ties the PR to a release train |
| **Risk / scope** | `breaking-change`, `security`, `infra`, `db-migration` | Flags that warrant extra reviewer attention |
| **Workflow** | `needs-review`, `needs-rebase`, `blocked` | Where the PR is stuck |

Guidance, distilled: tag for *triage and reviewer attention*, not for data you can get elsewhere — don't
duplicate the linked work item, author, or target branch as tags. Prefer a draft PR + `work-in-progress`
over a "[WIP]" title prefix. Retire `do-not-merge`/`work-in-progress` before completing the PR.

## Deeper API work

For anything beyond open-PR-and-link — WIQL queries, batch work-item updates, pipeline triggers, comment threads — use the **`azure-devops`** skill, which wraps the REST API and MCP tools comprehensively. `ship` deliberately stays narrow: deliver this branch.

## Gotchas

- **Branch policies can block direct push to `main`.** That's the signal to use the PR path, not to force-push. Never bypass a policy.
- **`AZURE_DEVOPS_EXT_PAT` shadows interactive login** — if it holds a stale/expired token, `az repos` fails confusingly. ship-pr.ts always sets a fresh one.
- **Work-item link doesn't change state** — linking and transitioning are independent. You need both if you want the board to move.
- **`--assigned-to` must resolve to an org member** — an email/UPN that isn't a project member errors (or silently leaves the item unassigned on some orgs). Set your default via `$SHIP_ADO_ASSIGNEE`, or pass `--assignee` per run.
- **Created items land in the initial state, not "Active"** — a freshly created Task is `New` (Agile/Scrum) or `To Do` (Basic). If a policy expects in-progress work, add `--transition`.
- **Server-side attribution stripping** is not guaranteed across orgs — never *add* AI attribution in the first place (see SKILL.md).
