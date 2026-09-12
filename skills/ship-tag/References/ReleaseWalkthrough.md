# Release walkthrough: from an open PR to an installed package

A complete run of the release flow on a sample Python project called `widget`, from a maintainer machine with nothing installed to a consumer running the released CLI. Placeholders in angle brackets (`<org>`, `<project>`, `<feed>`) stand for your own values.

What you end up with, for version `1.4.0`:

| Where | What |
|---|---|
| git | branch `release/v1.4.0`, annotated tag `v1.4.0` on the reviewed merge commit |
| repo files | `pyproject.toml` says `1.4.0`; CHANGELOG.md has `## [1.4.0] - <date>` with compare links |
| Azure Artifacts | Universal Package `widget` `1.4.0` holding `widget-1.4.0.tar.gz` and a generated `README.md`, with a Description that says what changed and how to install it |

## 1. One-time setup: the maintainer machine

| Tool | Why | Install |
|---|---|---|
| bun | runs the ship-tag tools | `curl -fsSL https://bun.sh/install \| bash` |
| git | branches, tags, worktrees | your OS package manager |
| Azure CLI + `azure-devops` extension | PR API, feed publish and download | install the CLI from Microsoft, then `az extension add --name azure-devops` |
| uv | builds the sdist, runs the install test | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |

```bash
az login                                   # as an org member who can contribute to the repo
export SHIP_TAG_FEED=<feed>                # default feed for ReleasePublish.ts
bun test ~/.claude/skills/ship-tag/Tools/  # unit + integration tests; all must pass
```

Permissions: **Contribute** and **Create tag** on the repository, and **Feed Publisher (Contributor)** on the feed.

## 2. One-time setup: the repository

```bash
bun ~/.claude/skills/ship-tag/Tools/Changelog.ts init     # CHANGELOG.md with [Unreleased]
```

In `pyproject.toml`, keep a literal `version = "X.Y.Z"` under `[project]`. Declare console scripts too, because the generated README and Description tell consumers how to run them:

```toml
[project]
name = "widget"
version = "1.3.0"
requires-python = ">=3.10"

[project.scripts]
widget = "widget.cli:main"

# The sdist ships every tracked file unless you say otherwise, and a published
# version can never be replaced, so decide this before the first release.
[tool.hatch.build.targets.sdist]
exclude = ["tests/", ".coverage", "_bmad/", "_bmad-output/"]
```

## 3. During development: one changelog entry per user-visible change

```bash
bun ~/.claude/skills/ship-tag/Tools/Changelog.ts add Added "Scheduled exports from the Reports page."
bun ~/.claude/skills/ship-tag/Tools/Changelog.ts add Fixed "Exports of reports over 10,000 rows no longer time out."
bun ~/.claude/skills/ship-tag/Tools/Changelog.ts lint
```

The entries go in the same PR as the change. Open the PR with `ship`.

## 4. Cut the release: PR 123 targets `release/v1.4.0` instead of `main`

```bash
T=~/.claude/skills/ship-tag/Tools
bun $T/ReleaseCut.ts --version 1.4.0 --pr 123 --bump --dry-run    # every guard, nothing written
bun $T/ReleaseCut.ts --version 1.4.0 --pr 123 --bump --description-file pr.md
```

Check `target=release/v1.4.0`, `bump_files=pyproject.toml,CHANGELOG.md` and `enabled_policies_on_release_branch`. If that last one is `0`, review isn't enforced on the release branch; say so to the reviewers. Then review and complete PR 123 in Azure DevOps as usual.

## 5. Tag and publish, after the PR completes

```bash
bun $T/ReleasePublish.ts --version 1.4.0 --pr 123 --feed $SHIP_TAG_FEED --dry-run
bun $T/ReleasePublish.ts --version 1.4.0 --pr 123 --feed $SHIP_TAG_FEED --install-test
```

The run refuses (exit 3) unless the PR API says `status=completed`. It tags the merge commit, builds the sdist in a clean worktree, stages it with a generated README.md, publishes, reads the Description back, downloads everything again, compares sha256, and installs the download into a fresh venv. The lines to check are `tag=v1.4.0`, `readme=README.md`, `published=true`, `description_readback=true`, `download_sha256_match=true` and `install_version=1.4.0`.

## 6. What consumers see

Both texts below are real output of `Tools/ReleaseDocs.ts` for this example; only the org, project, feed and hashes are placeholders.

**The feed Description** (Artifacts → feed → widget → 1.4.0). Azure Artifacts caps this at 256 characters, so it carries the change summary and a short install command; the full command, checksum and notes are in the README:

```text
widget 1.4.0 (2026-09-11). Added: Scheduled exports from the Reports page. Fixed: Ex… Install: az artifacts universal download --feed <feed> --name widget --version 1.4.0 --path . && uv pip install ./widget-1.4.0.tar.gz. Details: README.md in this package.
```

**README.md**, shipped inside the package next to the tarball:

````markdown
# widget 1.4.0

Released 2026-09-11 from tag `v1.4.0` (commit `9f3c2a1`) of https://dev.azure.com/<org>/<project>/_git/widget.

## What's in this package

| File | What it is |
|---|---|
| `widget-1.4.0.tar.gz` | Python source distribution. sha256 `4b2c7e1f0a9d8c6b5e4f3a2d1c0b9a8f7e6d5c4b3a2f1e0d9c8b7a6f5e4d3c2b` |
| `README.md` | This file |

## Install

You need the Azure CLI with the `azure-devops` extension (after `az login`), and Python >=3.10 with `uv` or `pip`.

```bash
az artifacts universal download --organization https://dev.azure.com/<org> --feed <feed> --name widget --version 1.4.0 --path ./widget-1.4.0
cd ./widget-1.4.0
echo "4b2c7e1f0a9d8c6b5e4f3a2d1c0b9a8f7e6d5c4b3a2f1e0d9c8b7a6f5e4d3c2b  widget-1.4.0.tar.gz" | sha256sum -c -
uv pip install ./widget-1.4.0.tar.gz        # or: pip install ./widget-1.4.0.tar.gz
```

For the full source tree instead (scripts, docs, CHANGELOG.md):

```bash
tar -xzf widget-1.4.0.tar.gz
```

## Use it

```bash
widget --help
```

In automation, pin the exact version (`--version 1.4.0`) instead of a wildcard, so every run installs the bytes that were verified at release.

## What changed in 1.4.0

### Added
- Scheduled exports from the Reports page.

### Fixed
- Exports of reports over 10,000 rows no longer time out.

Full diff: https://dev.azure.com/<org>/<project>/_git/widget/branchCompare?baseVersion=GTv1.3.0&targetVersion=GTv1.4.0
````

## 7. Install and use it (consumer side)

```bash
az artifacts universal download --organization https://dev.azure.com/<org> --feed <feed> \
  --name widget --version 1.4.0 --path ./widget-1.4.0
cd ./widget-1.4.0
cat README.md                                   # install steps, checksum, what changed
echo "<sha256 from README>  widget-1.4.0.tar.gz" | sha256sum -c -
uv pip install ./widget-1.4.0.tar.gz
widget --help
```

In a pipeline, pin `--version 1.4.0`. A wildcard installs whatever was published last, not what you tested.

## 8. Close the loop

Open a PR from `release/v1.4.0` into `main` with `ship`, so the base branch carries the release. A release branch that never merges back leaves `main` without the fix.

## 9. No PR platform?

```bash
bun $T/ReleaseLocal.ts --version 1.4.0 --dry-run
bun $T/ReleaseLocal.ts --version 1.4.0            # one release commit + annotated tag, local
bun $T/ReleaseLocal.ts --version 1.4.0 --push     # also push branch and tag, read the tag back
```

## When a step refuses

| Message | Meaning | Do |
|---|---|---|
| `PR … is active …; tag only after it completes` | the PR hasn't merged | complete the PR, rerun |
| `… is already in feed …; versions are immutable` | that version was published | cut the next patch; `Changelog.ts yank` the bad one if needed |
| `tag vX.Y.Z already exists at …, not …` | the tag points elsewhere | investigate before anything else; never move a published tag |
| `pyproject.toml at … says version …` | the bump didn't land in the merged code | rerun ReleaseCut with `--bump` before merging |
| `[Unreleased] has no entries` | nothing to release | add changelog entries first |
| wrong or thin feed Description | it can't be edited after publish (the update API only accepts `views`) | fix CHANGELOG.md; the next version gets the right text |
