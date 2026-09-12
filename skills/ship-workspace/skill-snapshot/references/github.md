# Ship — GitHub path

Detail for the GitHub half of `ship`. Read this when the remote is `github.com` (or a custom SSH host alias for GitHub).

## Auth

The GitHub path creates the PR with **Octokit** (`@octokit/rest`). It needs a token, resolved in order: `GH_TOKEN`, `GITHUB_TOKEN`, then `gh auth token` (so an existing `gh auth login` just works). The push step (`ship-push.ts`) still uses `git` — there's no OAuth-Bearer fallback like Azure, so if `git push` fails, fix the credential (`gh auth login` / SSH key) rather than working around it.

**Custom SSH host aliases:** this very repo uses `git@github-julianomb:julianobarbosa/claude-code-skills.git`. The host (`github-julianomb`) doesn't contain `github.com`, so `ship-detect.ts` falls back to matching the substring `github`. If detection ever returns `unknown`, set `SHIP_PLATFORM=github` for the command.

## Opening the PR

`ship-pr.ts` calls `octokit.pulls.create({ owner, repo, base, head, title, body, draft })`, parsing `owner`/`repo` from the remote URL. Pass `--body` or `--body-file` for the description; unlike the old `gh pr create --fill`, there is **no commit-message auto-fill** — with neither flag the body is empty. Add `--draft` for a draft PR.

## Linking issues

GitHub has no `AB#` syntax. Use closing keywords in the PR body so the issue closes on merge:

```
Closes #123
Fixes #123
```

There is no GitHub equivalent of the Azure "transition Board state" step — `--transition` is ignored on GitHub. Issue state follows the closing keyword at merge time.

## Labels (the GitHub equivalent of Azure "tags")

What Azure DevOps calls PR **tags**, GitHub calls **labels**. Because a PR is an issue on GitHub,
labels go through the **issues** API, keyed by the PR `number` (printed as `pr_number=` by `ship-pr.ts`):

| Action | Octokit call |
|--------|--------------|
| Add | `octokit.issues.addLabels({ owner, repo, issue_number, labels })` |
| List | `octokit.issues.listLabelsOnIssue({ owner, repo, issue_number })` |
| Remove | `octokit.issues.removeLabel({ owner, repo, issue_number, name })` |

A label that doesn't exist on the repo is **auto-created** (with a random color) when first added —
so there's no pre-registration step, the same as Azure's free-form tags. Re-adding an existing label
is a no-op (GitHub dedupes); `removeLabel` on a label the PR doesn't carry 404s (treated as non-fatal).

```bash
# At PR open:
bun scripts/ship-pr.ts --title "Add report company filter" --body-file /tmp/pr-body.md \
  --tag "feature,needs-review"

# On an existing PR (the pr_number from ship-pr.ts):
bun scripts/ship-tag.ts 123 --add "do-not-merge"
bun scripts/ship-tag.ts 123 --remove "do-not-merge" --list
```

### Recommended labels (best practice)

The same small, consistent vocabulary recommended for Azure applies — GitHub's default labels
(`bug`, `enhancement`, `documentation`, `good first issue`, `help wanted`) are a fine base. Keep
them lowercase and hyphenated; lean on `do-not-merge` / `work-in-progress` for status and reserve
labels for triage, not for data already carried by the linked issue or the target branch. The full
category table lives in `references/azure-devops.md` → **Recommended tags** and is platform-agnostic.

## Auto-merge

```bash
gh pr merge --auto --squash --delete-branch
```

Queues the merge to happen once required checks pass, then deletes the branch. Honors branch protection — it won't bypass required reviews or status checks.

## Gotchas

- **Octokit `pulls.create` needs the branch pushed first** (the `head` ref must exist on the remote). `ship`'s flow pushes (step 3) before opening the PR (step 4); don't reorder.
- **`head` must match the pushed branch name**, not a worktree directory name.
- **No AI attribution** in title or body (see SKILL.md). With no `--body`/`--body-file` the PR body is empty — there's no commit auto-fill, so write a real description.
- **`auto-merge` is still a `gh` command** (`gh pr merge --auto …`) — the Octokit path only opens the PR; cleanup/merge stays as documented above.
