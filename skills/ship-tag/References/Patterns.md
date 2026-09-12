# Release patterns, anti-patterns and best practices

Distilled from real release runs through a release branch, a retargeted PR, a tag after review and a Universal Package. Each entry says what goes wrong without it.

## Patterns

| Pattern | What it prevents |
|---|---|
| **One version, five places.** Branch, tag, version file, CHANGELOG heading and package version carry the same `X.Y.Z`, checked before tagging. | A tag that says 1.1.1 on a package whose metadata says 1.1.0. |
| **Release branch from the base tip, PR retargeted.** The PR merges into `release/vX.Y.Z`; the base gets it back through its own PR. | Unreleased work riding into the base, or a release that never reaches it. |
| **Tag after review, on the merge commit.** Gate on the PR API's `status=completed`, then tag `lastMergeCommit`. | A version pointing at code nobody approved. |
| **Annotated tags with the changelog section as the message**, using `--cleanup=verbatim`. | Tags nobody can explain, and release notes whose `###` headings were stripped as comments. |
| **Build from the tagged commit in a clean, detached worktree.** | Shipping the dirty working copy, or another session's uncommitted files. |
| **Reproducible build.** `SOURCE_DATE_EPOCH` set to the tagged commit's timestamp. | Two builds of one tag with different checksums. |
| **The stage holds exactly the artifact.** | Publishing tooling debris (uv's `.gitignore`) into an immutable package. |
| **Verify as the consumer.** Read the version back from the feed, download into an empty directory, compare sha256, install into a fresh venv. | Trusting a publish command whose output doesn't carry the fields you'd check. |
| **Merge the base into the PR branch, don't rebase it.** | Force-pushing a branch that's under review. |
| **Read back every write from its authority.** PR API after PATCH, `ls-remote` after push, feed API after publish. | A PATCH that returns 200 while silently dropping a field. |
| **Guards before writes, exit 3 for a refusal.** | Half-finished releases: a branch created, then a failure on the tag. |
| **No platform, same contract.** Without a remote or PR flow, `ReleaseLocal.ts` still produces one release commit and an annotated tag with intact notes. | Hand-rolled local releases whose tag message lost its `###` headings, or whose tag sits on the wrong commit. |

## Anti-patterns

| Anti-pattern | What actually happened, or would |
|---|---|
| Tagging the PR branch head before merge | If review changes the code, the tag points at unreviewed code. |
| Branch and tag both named `v1.2.3` | `git checkout v1.2.3` becomes ambiguous and tools pick one silently. |
| `targetRefName` and `description` in one PATCH | The retarget applied, the description was dropped, and the response looked like success. |
| Trusting `az artifacts universal publish` output | It printed `null null` for name and version on a successful publish. |
| A placeholder package Description | The feed showed `<pkg> X.Y.Z sdist (tag vX.Y.Z, commit abc1234)`: nothing on what changed or how to install, and the update API can't fix it afterwards. |
| Writing the Description without a budget | Azure Artifacts caps it at 256 characters and rejects the publish (exit 20) after the tag is already pushed. Generate it to fit, and keep the full detail in the packaged README. |
| Trusting `az repos pr show` for labels | It returned no labels while the labels endpoint listed `fix`. |
| Treating a fast non-zero exit as "fixed" | A negative probe failed on `item not found` before reaching the code under test; the real bug shipped. |
| Publishing a plain sdist without deciding its contents | Coverage data, dev scaffolding and tests went into an immutable package. |
| Deleting and re-publishing a version | Consumers holding the old bytes now disagree with the feed; most feeds refuse it anyway. |
| Changelog = `git log` | Merge commits and refactors bury the one line a user needed. |
| Believing one policy query | `az repos policy list --branch` said `[]` while a repo-wide policy covered the branch; `policy/configurations?refName=…` returned a policy scoped `Exact` to `main` for a release branch. Match scopes yourself, and use the PR's `policy/evaluations` for what actually blocks a merge. |
| Ad-hoc shell probes in zsh | `PIPESTATUS` doesn't exist there, and `rg -q` with `pipefail` turned found matches into "MISSING". |

## Best practices

- Decide the version before cutting; the tool refuses anything not greater than the latest SemVer tag.
- Keep CHANGELOG `[Unreleased]` current in every PR; release day only moves it.
- Run every release tool with `--dry-run` first; it evaluates every guard.
- Say out loud when review isn't enforced on the release branch.
- After publishing, give the consumer command, not just "it's published".
- Clean up scratch builds, downloads and worktrees; they're copies of release bytes.
