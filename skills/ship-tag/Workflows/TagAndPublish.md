# Tag and publish

## Done looks like

- The PR API shows the release PR with `status=completed`. Its `lastMergeCommit` is the release commit.
- An annotated tag `vX.Y.Z` points at that commit and is pushed; `git ls-remote --tags origin vX.Y.Z` peels to it. The message is `<package> X.Y.Z` followed by the CHANGELOG section for X.Y.Z.
- `<package>@X.Y.Z` exists in the feed and holds exactly two files: `<package>-X.Y.Z.tar.gz`, built from the tagged commit in a clean worktree with `SOURCE_DATE_EPOCH` set to the commit time, and a generated `README.md` with install, checksum, usage and the release notes.
- The feed Description says what changed and how to download and install the package, within the 256-character limit Azure Artifacts enforces, and reads back identical to what was sent (`description_readback=true`). It can't be edited after publish, so it's generated, never typed; the full command, checksum and notes live in the packaged README.md.
- A fresh download matches every staged file's sha256. With `--install-test`, it installs into a new venv and reports `X.Y.Z`.
- Scratch builds, downloads and worktrees are gone.

## Tool contract

```bash
T=~/.claude/skills/ship-tag/Tools/ReleasePublish.ts
bun $T --version 1.4.0 --pr 123 --feed <feed> --dry-run            # guards and plan
bun $T --version 1.4.0 --pr 123 --feed <feed> --install-test
bun $T --version 1.4.0 --commit <sha> --feed <feed> --no-publish   # tag, build and verify only
```

`--feed` defaults to `$SHIP_TAG_FEED`. For a project-scoped feed add `--feed-project <project>`. To publish artifacts you built yourself, pass `--stage-dir <dir>`; it's published as-is.

Output keys: `version`, `commit`, `package`, `feed`, `tag_exists`, `tag`, `artifact`, `sha256`, `pkg_info_version`, `readme`, `description_chars`, `published`, `description_readback`, `download_sha256_match`, `install_version`.

With `--stage-dir`, no README.md is added, because you own that directory's contents. The Description is still generated.

Exit 3 means a guard refused and nothing was written: the PR isn't completed, the tag exists on a different commit, the version is already in the feed, or the version file at the commit disagrees.

## Consumers install it with

The generated `README.md` inside the package carries these steps with the real org, feed and checksum filled in. A full sample, with a generated Description and README, is in `References/ReleaseWalkthrough.md`.

```bash
az artifacts universal download --organization https://dev.azure.com/<org> \
  --feed <feed> --name <package> --version 1.4.0 --path .
uv pip install ./<package>-1.4.0.tar.gz      # or extract it and use the scripts inside
```

## Doing it by hand (same contract)

```bash
C=<merge commit>
git tag -a v1.4.0 "$C" --cleanup=verbatim -m "<package> 1.4.0" -m "$(bun .../Changelog.ts notes 1.4.0)"
git push origin refs/tags/v1.4.0
git ls-remote --tags origin 'v1.4.0*'                     # the ^{} line must be $C

git worktree add --detach /tmp/rel "$C"
SOURCE_DATE_EPOCH=$(git log -1 --format=%ct "$C") uv --directory /tmp/rel build --sdist --out-dir /tmp/stage
rm /tmp/stage/.gitignore                                  # uv writes one; the package must hold only the tarball
az artifacts universal publish --organization https://dev.azure.com/<org> --feed <feed> \
  --name <package> --version 1.4.0 --path /tmp/stage
# Read back from the feed, not from publish's output:
az rest --method get --resource 499b84ac-1321-427f-aa17-267ca6975798 \
  --uri "https://feeds.dev.azure.com/<org>/_apis/packaging/feeds/<feed>/packages?packageNameQuery=<package>&includeAllVersions=true&api-version=7.1"
```

Then download into an empty directory, compare `sha256sum`, and remove the worktree.

## GitHub instead of Azure DevOps

Not tooled here, same contract: `gh release create v1.4.0 dist/<package>-1.4.0.tar.gz --verify-tag --title v1.4.0 --notes "$(bun .../Changelog.ts notes 1.4.0)"`, then `gh release download v1.4.0` into an empty directory and compare sha256.

## When a published version is wrong

Never delete and re-publish the same number: consumers may already have it, and the feed refuses a duplicate version. Fix forward with the next patch, then `Changelog.ts yank X.Y.Z` so the bad version is marked rather than hidden.
