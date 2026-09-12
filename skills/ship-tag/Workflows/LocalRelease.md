# Local release

Release from the current branch when there is no PR platform in the loop: no remote yet, a repo without branch protection, or a project where the release commit itself is the reviewed step.

## Done looks like

- One `chore(release): X.Y.Z` commit that sets the version file(s), refreshes the lockfile, and moves CHANGELOG `[Unreleased]` into `## [X.Y.Z] - YYYY-MM-DD` with its compare links.
- An annotated tag `vX.Y.Z` on exactly that commit. The message is `<name> X.Y.Z` followed by the release notes, `###` headings intact.
- A clean working tree. With `--push`, the branch and tag are on origin and the tag reads back at the release commit.

## Tool contract

```bash
T=~/.claude/skills/ship-tag/Tools/ReleaseLocal.ts
bun $T --version 1.4.0 --dry-run          # guards and plan, writes nothing
bun $T --version 1.4.0                    # commit + tag, local only
bun $T --version 1.4.0 --push             # also push branch and tag, then read the tag back
```

Compare links come from `--repo-url`, then origin, then the links already in CHANGELOG.md, so a repo with no remote still gets correct links as long as the file has one.

Output keys: `version`, `branch`, `latest_tag`, `changelog`, `push`, `commit`, `tag`, `files`, `pushed`.

Exit 3 means a guard refused and nothing was written: a dirty tree, a detached HEAD, a tag that already exists, a version not greater than the latest tag, or an empty `[Unreleased]`.

## When not to use it

If the base branch is protected, a direct push is rejected. That's the signal to go through `Workflows/CutRelease.md` and `Workflows/TagAndPublish.md`, so the version lands through a PR and the tag goes on the reviewed merge commit.
