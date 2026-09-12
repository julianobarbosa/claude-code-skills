---
name: ship-tag
version: 1.0.0
description: "Cut, tag and publish versioned releases and build CHANGELOG.md in Keep a Changelog 1.1.0 format: release/vX.Y.Z branch, PR retarget, version bump, annotated tag on the reviewed merge commit, reproducible tar.gz published as an Azure Artifacts Universal Package, read back and checksum-verified. USE WHEN release, cut a release, version tag, tag vX.Y.Z, release branch, publish package, tar.gz, universal package, changelog, CHANGELOG.md, keep a changelog, release notes, yanked. NOT FOR PR labels or opening PRs (use ship)."
---

# ship-tag

`ship` gets a change reviewed. `ship-tag` turns reviewed changes into a release someone else can install: one version string, carried the same way by a release branch, an annotated tag, the version file, the CHANGELOG heading and a published package, each read back from its authority rather than assumed.

> **Not `ship`'s `ship-tag.ts`.** That script manages PR *labels*. This skill is about *release versions*: git tags, release branches, packages and the changelog.

## Workflow Routing

| Trigger | Workflow |
|---|---|
| "add a changelog entry", "create CHANGELOG.md", "release notes", "backfill the changelog", "lint the changelog" | `Workflows/Changelog.md` |
| "cut a release", "release branch", "don't merge into main, target a release branch", "bump the version" | `Workflows/CutRelease.md` |
| "PR merged, tag it", "tag and publish", "publish the tar.gz", "universal package" | `Workflows/TagAndPublish.md` |
| "release locally", "no remote", "tag a release without a PR", "cut 1.4.0 on this branch" | `Workflows/LocalRelease.md` |

## What a finished release looks like

- One SemVer string `X.Y.Z` agrees in all five places: branch `release/vX.Y.Z`, tag `vX.Y.Z`, the version file (`pyproject.toml` / `package.json`), the `## [X.Y.Z] - YYYY-MM-DD` heading in CHANGELOG.md, and the package version in the feed.
- The tag and the package both come from the merge commit of a pull request whose status is `completed`. Nothing unreviewed carries the version.
- The artifact was built from that commit in a clean worktree with `SOURCE_DATE_EPOCH` pinned, and the copy a consumer downloads matches the built file's sha256 and installs.
- A consumer can act on the package without asking anyone: the feed Description says what changed, how to install and how to run it, and a generated `README.md` inside the package has the full install, checksum and usage steps.
- CHANGELOG.md tells users what changed, in the six Keep a Changelog categories, with compare links, and passes `Changelog.ts lint --strict`.
- The base branch gets the release back through its own PR, so a release branch never becomes a dead end.

## Tools

Run from inside the target repo. No npm dependencies: the tools call `git`, `az` and `uv` with argument arrays, never through a shell.

| Tool | Does |
|---|---|
| `bun ~/.claude/skills/ship-tag/Tools/Changelog.ts init\|add\|release\|yank\|notes\|links\|lint` | Create and maintain CHANGELOG.md. `add` follows the file's own layout; `release` moves `[Unreleased]` into a dated version and writes its compare links; `links` backfills missing ones; `lint` enforces Keep a Changelog 1.1.0 |
| `bun ~/.claude/skills/ship-tag/Tools/ReleaseCut.ts --version X.Y.Z --pr <id> [--bump]` | Create `release/vX.Y.Z` from the base tip, land the version bump and changelog release on the PR branch as a fast-forward, retarget the PR, read it all back |
| `bun ~/.claude/skills/ship-tag/Tools/ReleasePublish.ts --version X.Y.Z --pr <id> --feed <feed>` | Refuse unless the PR completed, tag its merge commit, build the sdist reproducibly, publish a Universal Package, read it back, download and compare sha256, optionally install-test |
| `bun ~/.claude/skills/ship-tag/Tools/ReleaseLocal.ts --version X.Y.Z [--push]` | No remote or PR flow: one release commit (version files + changelog) and an annotated tag with intact notes on it; optionally push and read back |

Compare links come from `--repo-url`, then origin, then the links a CHANGELOG already has. The release tools take `--dry-run` (guards and plan, nothing written). Exit code 3 always means "refused by a guard, nothing written". Results are `key=value` lines on stdout; progress goes to stderr. Tests: `bun test ~/.claude/skills/ship-tag/Tools/` runs the unit tests plus integration tests that drive the Azure DevOps path against a bare-repo origin and a stub `az`.

## References

- `References/KeepAChangelog.md`: the Keep a Changelog 1.1.0 spec as a local document, with principles, change types, heading grammar, link references, bad practices, FAQ and provenance.
- `References/ChangelogSamples.md`: a new file, a real entry reviewed and corrected, a full multi-release file, the spec's own example, and counter-examples.
- `References/Patterns.md`: release patterns, anti-patterns and best practices, each tied to what goes wrong without it.
- `References/ReleaseWalkthrough.md`: the whole flow on a sample project, from installing the tools to a consumer running the released CLI, including a generated feed Description and README.md.

## Gotchas

Each of these was hit in a real release run.

- **Tag and publish only after `status=completed`.** `mergeStatus=succeeded` means "no conflicts", not "merged". A PR shows it while still active.
- **Retarget and description are separate PATCHes.** Sending `targetRefName` and `description` in one Azure DevOps PR PATCH applies the retarget and silently drops the description.
- **Universal Package versions are immutable.** A wrong publish burns the number. Fix forward with the next patch and mark the bad one `[YANKED]` in CHANGELOG.md.
- **A package Description is capped at 256 characters.** Microsoft's docs don't say so; `artifacttool` rejects a longer one with return code 20 and the message "greater than the allowed maximum of 256 characters", after the tag has already been pushed. `ReleaseDocs.ts` budgets for it: the change summary is trimmed, while the short install command and the pointer to the packaged README always survive.
- **So is the package Description.** The Universal Packages "Update Package Version" API accepts only `views`, so a thin one-liner like `<pkg> X.Y.Z sdist (tag …, commit …)` is permanent for that version. `ReleasePublish.ts` generates the Description from the CHANGELOG section and reports `description_readback`.
- **`az artifacts universal publish -o json` has no name or version fields** (a successful publish printed `null null`). Confirm through the feed's packages API, then download and compare sha256.
- **`az repos pr show` omits PR labels.** Read them through the labels endpoint (`ship`'s `ship-tag.ts --list`).
- **`uv build --out-dir` drops a `.gitignore` into the directory.** Publishing that directory ships it too; stage, then delete it.
- **A plain sdist ships every tracked file**: dev scaffolding, coverage data, tests. Decide the contents (`[tool.hatch.build.targets.sdist]` include/exclude) before the first publish, because a published version can't be replaced.
- **`git tag -m` strips lines that start with `#`** under the default cleanup mode, which deletes `### Added` headings from release notes. Tag with `--cleanup=verbatim`.
- **A dirty main checkout blocks fast-forward and rebase.** Do release surgery in a detached temp worktree, and merge the base into the PR branch instead of rebasing, so the push is a fast-forward and nothing is forced.
- **Neither policy query answers "what blocks this PR" on its own.** `az repos policy list --branch <ref>` returned `[]` for a branch that a repo-wide policy did cover, and `policy/configurations?refName=…` returns the repo's policies whatever ref you pass, including one scoped `Exact` to `main`. `ReleaseCut.ts` therefore matches scopes itself (no refName means repo-wide) and reports `enabled_policies_on_release_branch` plus `blocking_policies`. For a live PR, the authority is `policy/evaluations?artifactId=vstfs:///CodeReview/CodeReviewId/<projectId>/<prId>`, with the artifactId URL-encoded and `api-version=7.1-preview.1` (plain `7.1` is rejected as "under preview"); an empty `value` means nothing blocks completion. Approvals only gate a merge when a minimum-approvers policy exists.
- **Shell probes lie in two known ways.** zsh has no `PIPESTATUS`, and `rg -q` under `set -o pipefail` kills the upstream command with SIGPIPE, so a found match reports as missing. The tools avoid shells; for ad-hoc checks use `/usr/bin/env bash` and don't pipe into `rg -q`.
- **An exit code is not a result.** A write probe against a non-existent item "failed fast" with rc=1 on `not found`, before the code path under test ever ran. Read the error text of every negative probe.
- **A branch and a tag with the same name** (`v1.2.3` for both) make `git checkout v1.2.3` ambiguous. Branch `release/vX.Y.Z`, tag `vX.Y.Z`.

## Examples

**Example 1: target a release branch instead of main**
```
User: "PR 123 shouldn't merge into main, it needs its own v2.3.0 release branch"
→ Workflows/CutRelease.md
→ ReleaseCut.ts --version 2.3.0 --pr 123 --bump --dry-run, then without --dry-run
→ reports release_branch, target, bump_files, enabled_policies_on_release_branch
```

**Example 2: publish after review**
```
User: "123 merged, tag and publish v2.3.0"
→ Workflows/TagAndPublish.md
→ ReleasePublish.ts --version 2.3.0 --pr 123 --feed <feed> --install-test
→ reports tag, sha256, published, download_sha256_match, install_version
```

**Example 4: how do I install a release?**
```
User: "how does someone install and use 1.4.0?"
→ References/ReleaseWalkthrough.md sections 6-7, or the README.md inside the package
→ az artifacts universal download … --version 1.4.0, sha256sum -c, uv pip install, <script> --help
```

**Example 3: changelog upkeep**
```
User: "we fixed the export timeout, put it in the changelog"
→ Workflows/Changelog.md
→ Changelog.ts add Fixed "Exports of large reports no longer time out." then lint
```
