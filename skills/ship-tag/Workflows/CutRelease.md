# Cut a release

Turn an open PR into a release candidate on its own branch, instead of merging it straight into the base.

## Done looks like

- `release/vX.Y.Z` exists on origin at the base branch's tip (read back with `git ls-remote`).
- The PR targets `release/vX.Y.Z` (read back from the PR API), with reviewers and work items unchanged.
- With `--bump`, the PR's source branch carries a merge of the base plus `chore(release): X.Y.Z`. That commit sets the version file, refreshes the lockfile, and moves CHANGELOG `[Unreleased]` into `[X.Y.Z]`. It lands as a fast-forward.
- Against the release branch, the PR diff is exactly the intended files: `git diff --stat origin/release/vX.Y.Z...origin/<source>`.
- You know what the release branch enforces: `enabled_policies_on_release_branch` counts only the policies whose scope covers the branch (repo-wide, an exact match, or a prefix), and `blocking_policies` names the ones that hold completion. Check a live PR with `policy/evaluations?artifactId=vstfs:///CodeReview/CodeReviewId/<projectId>/<prId>` (artifactId URL-encoded, `api-version=7.1-preview.1`); an empty `value` means nothing blocks completion.

## Before running

- The PR is open (use `ship`), and CHANGELOG.md `[Unreleased]` holds its entries.
- Pick X.Y.Z by SemVer: breaking change means major, new capability means minor, fixes only means patch. Before 1.0.0, a breaking change bumps minor. The tool refuses a version that isn't greater than the latest SemVer tag.
- The branch is `release/vX.Y.Z` (use `--prefix hotfix/` for an out-of-band fix). Never name the branch exactly like the tag.

## Tool contract

```bash
T=~/.claude/skills/ship-tag/Tools/ReleaseCut.ts
bun $T --version 1.4.0 --pr 123 --bump --dry-run                  # guards and plan, writes nothing
bun $T --version 1.4.0 --pr 123 --bump --description-file pr.md
```

Output keys: `pr`, `source`, `current_target`, `release_branch`, `base`, `latest_tag`, `bump`, `release_branch_created`, `bump_files`, `bump_pushed`, `target`, `status`, `merge_status`, `description_updated`, `enabled_policies_on_release_branch`.

Exit 3 means a guard refused and nothing was written: the release branch or tag already exists, the version isn't greater than the latest tag, the PR isn't active, or the description is over 4000 characters.

## Doing it by hand (same contract)

```bash
BASE=$(git rev-parse origin/main)
git push origin "$BASE:refs/heads/release/v1.4.0"

URI="https://dev.azure.com/<org>/<project>/_apis/git/repositories/<repo>/pullrequests/<id>?api-version=7.1"
R=499b84ac-1321-427f-aa17-267ca6975798   # Azure DevOps API resource id, same for every org

# Retarget, alone. Azure DevOps drops any other field sent in the same PATCH.
az rest --method patch --resource $R --uri "$URI" \
  --headers Content-Type=application/json --body '{"targetRefName":"refs/heads/release/v1.4.0"}'
# Description in its own call.
jq -n --rawfile d pr.md '{description:$d}' > desc.json
az rest --method patch --resource $R --uri "$URI" --headers Content-Type=application/json --body @desc.json
```

Version bump by hand: a detached worktree at `origin/<source>`, `git merge origin/main`, edit the version, `uv lock`, `Changelog.ts release X.Y.Z`, commit, `git push origin HEAD:refs/heads/<source>`.

## After the release PR completes

Go to `Workflows/TagAndPublish.md`. Then open a PR from `release/vX.Y.Z` into the base (with `ship`), so the base gets the release too.
