# CHANGELOG samples

Every sample here can be checked with `bun ~/.claude/skills/ship-tag/Tools/Changelog.ts lint --file <file>`.

## 1. A new file

What `Changelog.ts init` writes. It lints clean.

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
```

## 2. A real entry, reviewed and corrected

As handed in:

```markdown
# Changelog
All notable changes to this project are documented here.

## [Unreleased]
### Added
- Bulk export to CSV.

## [1.4.0] — 2026-07-05
### Added
- Slack integration: auto‑post on publish.
### Changed
- Dashboard loads 60% faster.
### Fixed
- SSL verification now completes within 60 seconds.
```

The structure is right: `[Unreleased]` on top, bracketed version, ISO date, and entries written for users ("loads 60% faster", not "optimized queries"). What the linter reports is in section 7. In short: the separator is an em dash (U+2014), "auto‑post" contains a non-breaking hyphen (U+2011) that a search for `auto-post` won't find, the preamble doesn't say whether the project follows SemVer, and neither heading has a link reference.

Corrected: the separator and hyphen via `lint --fix`, the links via `links --repo-url <url>`, and the SemVer sentence by hand.

```markdown
# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Bulk export to CSV.

## [1.4.0] - 2026-07-05

### Added
- Slack integration: auto-post on publish.

### Changed
- Dashboard loads 60% faster.

### Fixed
- SSL verification now completes within 60 seconds.

[unreleased]: https://github.com/<owner>/<repo>/compare/v1.4.0...HEAD
[1.4.0]: https://github.com/<owner>/<repo>/compare/v1.3.0...v1.4.0
```

(`v1.3.0` stands in for whatever the previous tag was.)

## 3. A full multi-release file

A service with an Azure DevOps remote, showing all six change types, a deprecation that turns into a removal, a security fix with its advisory, and a yanked release.

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `--format yaml` on every read command.

## [2.0.0] - 2026-08-20

### Removed
- The `/v1/export` endpoint, deprecated in 1.6.0. Use `/v2/export`; the payload is identical apart from ISO dates.

### Changed
- Configuration moves from `settings.ini` to `config.yaml`. Run `widget migrate-config` once; it keeps a backup.

## [1.6.1] - 2026-07-30

### Security
- Session tokens no longer appear in debug logs (advisory WID-2026-004). Rotate tokens issued before this release.

### Fixed
- Exports of large reports no longer time out after 60 seconds.

## [1.6.0] - 2026-07-10 [YANKED]

### Added
- Scheduled exports.

### Deprecated
- The `/v1/export` endpoint. It will be removed in 2.0.0.

## [1.5.0] - 2026-06-02

### Added
- Bulk export to CSV.

[unreleased]: https://dev.azure.com/<org>/<project>/_git/<repo>/branchCompare?baseVersion=GTv2.0.0&targetVersion=GBmain
[2.0.0]: https://dev.azure.com/<org>/<project>/_git/<repo>/branchCompare?baseVersion=GTv1.6.1&targetVersion=GTv2.0.0
[1.6.1]: https://dev.azure.com/<org>/<project>/_git/<repo>/branchCompare?baseVersion=GTv1.6.0&targetVersion=GTv1.6.1
[1.6.0]: https://dev.azure.com/<org>/<project>/_git/<repo>/branchCompare?baseVersion=GTv1.5.0&targetVersion=GTv1.6.0
[1.5.0]: https://dev.azure.com/<org>/<project>/_git/<repo>?version=GTv1.5.0
```

Things to notice:

- 1.6.0 was yanked, not deleted: someone running it needs to know.
- The deprecation appeared a full release before the removal, and the removal says what to use instead.
- The breaking change in 2.0.0 comes with the one command to run.
- The security entry names the advisory and tells users what to do.

## 4. The spec's own example (abridged)

From Keep a Changelog 1.1.0 (MIT, Olivier Lacan); the first three releases, lists shortened. It lints with zero findings, which the tool's tests assert.

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.2] - 2024-09-27

### Added
- v1.1 German translation
- v1.1 Italian translation

### Fixed
- Improve French translation
- Improve Dutch translation

## [1.1.1] - 2023-03-05

### Added
- Default to most recent versions available for each languages
- Centralize all links into `/data/links.json` for easy updates

### Fixed
- Missing periods at end of each change

### Changed
- Upgrade dependencies: Ruby 3.2.1, Middleman, etc.

### Removed
- Unused normalize.css file

## [1.1.0] - 2019-02-15

### Added
- Danish translation
- Georgian translation
- Changelog inconsistency section in Bad Practices

[unreleased]: https://github.com/olivierlacan/keep-a-changelog/compare/v1.1.2...HEAD
[1.1.2]: https://github.com/olivierlacan/keep-a-changelog/compare/v1.1.1...v1.1.2
[1.1.1]: https://github.com/olivierlacan/keep-a-changelog/compare/v1.1.0...v1.1.1
[1.1.0]: https://github.com/olivierlacan/keep-a-changelog/compare/v1.0.0...v1.1.0
```

## 5. Counter-examples

Each block triggers the lint code in its title (plus W001/W002/W010, because a fragment has no preamble).

**Commit-log dump (W040).** Noise to a user, and it hides the one line that matters.

```markdown
## [1.2.0] - 2026-03-01
### Added
- feat(api): add export endpoint
- a1b2c3d fix typo in README
- Merged PR 42: feature/export
```

Better: `- Export any report to CSV from the Reports page.`

**Ambiguous or invalid date (E024).** `03/04/2026` means March in one country and April in another.

```markdown
## [1.2.0] - 03/04/2026
```

**Newest version not first (E027).**

```markdown
## [1.0.0] - 2026-01-10
## [1.1.0] - 2026-02-01
```

**Invented change type (E030).** Readers and tools know six groups.

```markdown
## [1.2.0] - 2026-03-01
### Improvements
- Faster startup.
```

Better: `### Changed`.

**Empty group left behind (W033).**

```markdown
## [1.2.0] - 2026-03-01
### Fixed

### Security
- Patched the session fixation issue.
```

**A removal nobody was warned about.** No lint code can catch this one; it's a review question. If `/v1/export` disappears in 2.0.0 with no `Deprecated` entry in an earlier release, users find out in production.

## 6. Turning commits into entries

| Commits in the range | Entry |
|---|---|
| `feat(export): csv writer`, `feat(export): wire button`, `test(export): fixtures` | `### Added` `- Export any report to CSV from the Reports page.` |
| `fix(auth): refresh loop on expired token` | `### Fixed` `- Signing in with an expired session no longer loops back to the login page.` |
| `perf(dashboard): cache tiles` | `### Changed` `- Dashboard loads 60% faster.` |
| `chore(deps): bump lodash`, `ci: cache bun install` | nothing (unless the bump fixed a vulnerability: then `### Security`) |
| `refactor!: drop settings.ini` | `### Changed` `- Configuration moves to config.yaml; run widget migrate-config once.` |

## 7. What the linter says about sample 2

Run on the sample exactly as handed in, then fixed, extended and released. Output pasted unedited.

```
$ bun Changelog.ts lint
CHANGELOG.md:1: warning W002 the preamble doesn't say whether the project follows Semantic Versioning
CHANGELOG.md:4: warning W050 [Unreleased] has no link reference at the bottom
CHANGELOG.md:8: warning W025 separator '—' (U+2014) between version and date; use an ASCII hyphen ' - ' (lint --fix)
CHANGELOG.md:8: warning W050 [1.4.0] has no link reference at the bottom
CHANGELOG.md:10: warning W041 contains U+2011 (non-breaking hyphen); searches for a plain '-' won't match (lint --fix)
errors=0
warnings=5

$ bun Changelog.ts lint --fix
fixed=2
CHANGELOG.md:1: warning W002 the preamble doesn't say whether the project follows Semantic Versioning
CHANGELOG.md:4: warning W050 [Unreleased] has no link reference at the bottom
CHANGELOG.md:8: warning W050 [1.4.0] has no link reference at the bottom
errors=0
warnings=3

$ bun Changelog.ts add Added "Scheduled exports."
added=true
category=Added

$ bun Changelog.ts release 1.5.0 --date 2026-09-11 --repo-url https://github.com/acme/widget
released=1.5.0
date=2026-09-11
links=github

$ bun Changelog.ts release 1.5.0 --date 2026-09-11   # again
ERROR: [Unreleased] has no entries; add them before releasing      (exit 3)

$ bun Changelog.ts notes 1.5.0
### Added
- Bulk export to CSV.
- Scheduled exports.
```

The file after `release`. The existing layout (no blank line under `###` headings) is kept, the empty `[Unreleased]` stays on top, and both links are written. The remaining warnings are the SemVer statement and `[1.4.0]`'s link, which predate the tool and need a human.

```markdown
# Changelog
All notable changes to this project are documented here.

## [Unreleased]

## [1.5.0] - 2026-09-11
### Added
- Bulk export to CSV.
- Scheduled exports.

## [1.4.0] - 2026-07-05
### Added
- Slack integration: auto-post on publish.
### Changed
- Dashboard loads 60% faster.
### Fixed
- SSL verification now completes within 60 seconds.

[unreleased]: https://github.com/acme/widget/compare/v1.5.0...HEAD
[1.5.0]: https://github.com/acme/widget/compare/v1.4.0...v1.5.0
```
