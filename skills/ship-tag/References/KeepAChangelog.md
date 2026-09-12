# Keep a Changelog 1.1.0

> **Status:** current published version of the spec at keepachangelog.com/en/1.1.0 · **Applies to:** any project's `CHANGELOG.md`
> **Retrieved:** 2026-09-11 from the spec page and its source repository; see [Sources](#sources)

Keep a Changelog is a convention, not a tool: a human-written file listing the notable changes in each released version, newest first, grouped by the kind of change. Its motto is "Don't let your friends dump git logs into changelogs." It pairs with Semantic Versioning, so a reader can tell from the version number and the changelog together whether an upgrade is safe.

---

## What a changelog is, and who it's for

- **What:** "a file which contains a curated, chronologically ordered list of notable changes for each version of a project."
- **Why:** "To make it easier for users and contributors to see precisely what notable changes have been made between each release (or version) of the project."
- **Who:** "People do. Whether consumers or developers, the end users of software are human beings who care about what's in the software. When the software changes, people want to know why and how."

## Guiding principles

| # | Principle | How `Changelog.ts lint` checks it |
|---|---|---|
| 1 | Changelogs are for humans, not machines | W040 flags entries that read like commit messages |
| 2 | There should be an entry for every single version | W029 flags a version with no entries |
| 3 | The same types of changes should be grouped | E030 unknown type, E032 duplicate group, W034 entry outside a group |
| 4 | Versions and sections should be linkable | W022 unbracketed version, W050 missing link reference |
| 5 | The latest version comes first | E027 versions out of order, E012 `[Unreleased]` not first |
| 6 | The release date of each version is displayed | E023 missing date, E024 non-ISO date |
| 7 | Mention whether you follow Semantic Versioning | W002 no SemVer statement in the preamble |

## Types of changes

| Type | Use it for |
|---|---|
| `Added` | new features |
| `Changed` | changes in existing functionality |
| `Deprecated` | soon-to-be removed features |
| `Removed` | now removed features |
| `Fixed` | any bug fixes |
| `Security` | in case of vulnerabilities |

The spec lists the six types but does not fix their order: its own example puts `Fixed` before `Changed` in 1.1.1. The tool inserts new groups in the order above and does not lint order.

## The Unreleased section

"Keep an Unreleased section at the top to track upcoming changes." It does two jobs: people can see what's coming, and at release time you move its contents into a new version section instead of writing one from memory (`Changelog.ts release X.Y.Z`).

## File shape

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.2] - 2024-09-27

### Added
- v1.1 German translation

### Fixed
- Improve French translation

[unreleased]: https://github.com/olivierlacan/keep-a-changelog/compare/v1.1.2...HEAD
[1.1.2]: https://github.com/olivierlacan/keep-a-changelog/compare/v1.1.1...v1.1.2
```

## Heading grammar the tool enforces

```
## [Unreleased]
## [X.Y.Z] - YYYY-MM-DD
## [X.Y.Z] - YYYY-MM-DD [YANKED]
### Added | Changed | Deprecated | Removed | Fixed | Security
- one entry per line
```

- `X.Y.Z` is SemVer 2.0.0 (pre-releases like `2.0.0-rc.1` allowed). A leading `v` in the heading is tolerated; tags carry the `v`.
- The separator is an ASCII hyphen with spaces, as in every example in the spec. An em dash (`—`) or en dash (`–`) parses but is flagged (W025), because tools that split headings on ` - ` break on it. `lint --fix` rewrites it.
- The date is ISO 8601 `YYYY-MM-DD` and must be a real calendar date.

## Link references

Brackets make a heading a Markdown reference link; the definitions live at the bottom of the file. The spec's source repository uses exactly this pattern:

| Link | GitHub | Azure DevOps (see open questions) |
|---|---|---|
| `[unreleased]` | `https://github.com/<owner>/<repo>/compare/vX.Y.Z...HEAD` | `https://dev.azure.com/<org>/<project>/_git/<repo>/branchCompare?baseVersion=GTvX.Y.Z&targetVersion=GB<base>` |
| `[X.Y.Z]` | `.../compare/vPREV...vX.Y.Z` | `.../branchCompare?baseVersion=GTvPREV&targetVersion=GTvX.Y.Z` |
| first release | `.../releases/tag/vX.Y.Z` | `.../_git/<repo>?version=GTvX.Y.Z` |

Reference labels are case-insensitive, so `[unreleased]:` resolves `## [Unreleased]`. `Changelog.ts release` writes both links for the new version.

## Can changelogs be bad? Yes: four ways

- **Commit log diffs.** "Using commit log diffs as changelogs is a bad idea: they're full of noise." A commit documents "a step in the evolution of the source code"; a changelog entry documents "the noteworthy difference, often across multiple commits, to communicate them clearly to end users."
- **Ignoring deprecations.** "When people upgrade from one version to another, it should be painfully clear when something will break." Users should be able to upgrade to the version that lists deprecations, fix them, then upgrade to the one where they become removals. "If you do nothing else, list deprecations, removals, and any breaking changes in your changelog."
- **Confusing dates.** Regional formats swap month and day. Use ISO 8601 (`2012-06-02`): largest to smallest unit, and it doesn't overlap ambiguously with other formats.
- **Inconsistent changes.** "A changelog which only mentions some of the changes can be as dangerous as not having a changelog." Not every change needs an entry, but every important one does, or readers will wrongly treat the file as the single source of truth.

## FAQ, condensed

| Question | The spec's answer |
|---|---|
| Is there a standard format? | "Not really." The GNU changelog style guide and GNU NEWS guideline are "inadequate or insufficient"; this project aims for a better convention from open source practice. |
| What should the file be called? | `CHANGELOG.md`. Some projects use `HISTORY`, `NEWS` or `RELEASES`, but a consistent name is easier for users to find. |
| What about GitHub Releases? | "A great initiative," but it creates "a non-portable changelog that can only be displayed to users within the context of GitHub," is less discoverable than uppercase files like README, and doesn't link commit logs between releases. |
| Can changelogs be parsed automatically? | "It's difficult, because people follow wildly different formats and file names." The Ruby gem Vandamme parses many, not all. |
| What about yanked releases? | Versions pulled for a serious bug or security issue "should" appear, marked `## [0.0.5] - 2014-12-13 [YANKED]`. "The [YANKED] tag is loud for a reason." Brackets also make it easy to parse. |
| Should you ever rewrite a changelog? | "Sure." Adding missing releases or undocumented breaking changes are good reasons. |
| How can I contribute? | The document is its author's "carefully considered opinion"; the discussion matters as much as the result. |

## Not covered / open questions

- **Keep a Changelog 2.0.0.** The spec's source repository now declares `The format is based on [Keep a Changelog](https://keepachangelog.com/en/2.0.0/)` in its own CHANGELOG. This document covers 1.1.0 as requested; 2.0.0 was not reviewed.
- **Azure DevOps compare URLs.** Microsoft Learn documents branch comparison only as a UI flow ("Compare branches"), not a URL format. The `branchCompare?baseVersion=GT…&targetVersion=GT…` form (`GT` = tag, `GB` = branch) is what the web UI produces, but it is undocumented. Verify one generated link in a browser before relying on it.
- **Markdown style inside sections.** The 1.1.0 page example has no blank line between `### Added` and its first entry; the source repository's current CHANGELOG has one. Both render the same; the tool preserves whichever the file already uses.

---

## Sources

Retrieved 2026-09-11. Re-verify version-sensitive claims before acting on them.

| Source | Type | URL |
|---|---|---|
| Keep a Changelog 1.1.0 | canonical spec | https://keepachangelog.com/en/1.1.0/ |
| keep-a-changelog `CHANGELOG.md` | the spec's own changelog (link-reference pattern) | https://raw.githubusercontent.com/olivierlacan/keep-a-changelog/main/CHANGELOG.md |
| Semantic Versioning 2.0.0 | referenced standard | https://semver.org/spec/v2.0.0.html |
| Review history: Compare branches | Azure DevOps (UI only, no URL format) | https://learn.microsoft.com/azure/devops/repos/git/review-history |

**Verified locally** (2026-09-11, bun 1.3.14, git 2.53.0):

`bun test ~/.claude/skills/ship-tag/Tools/Changelog.test.ts`

```
 21 pass
 0 fail
 49 expect() calls
Ran 21 tests across 1 file. [136.00ms]
```

Confirms: the spec's example above (first three releases, verbatim) parses and re-renders byte for byte and lints with zero findings; `release` writes `## [X.Y.Z] - YYYY-MM-DD` with GitHub and Azure DevOps compare links; `yank` produces the `[YANKED]` form the FAQ specifies, and lint accepts it.

License: Keep a Changelog is MIT licensed, created and maintained by Olivier Lacan, designed by Tyler Fortune. Quoted passages and the example above come from it.

**Source discrepancies:**

- The spec page is 1.1.0; the spec's source repository now points at 2.0.0 (see open questions). This document follows the page, which is what was requested.
- The spec's source repository defines `[0.1.0]: .../compare/v0.0.8...v0.0.1`, which runs backwards (it should compare `v0.0.8...v0.1.0`). Hand-maintained link references drift; that's why `Changelog.ts release` writes them.
