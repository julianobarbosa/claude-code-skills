# Changelog

Keep CHANGELOG.md so a user can answer "what changed for me between the version I run and this one?" without reading commits.

## Done looks like

- `CHANGELOG.md` at the repo root, in Keep a Changelog 1.1.0 shape (`References/KeepAChangelog.md`).
- `## [Unreleased]` is first and always present. It holds every merged, unreleased, user-visible change.
- Each release is `## [X.Y.Z] - YYYY-MM-DD`, newest first, with entries under `### Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security` (in that order), and no empty groups.
- Every version heading resolves through a link reference at the bottom: a compare view from the previous tag, and `[unreleased]` from the latest tag to the base branch.
- The preamble says whether the project follows Semantic Versioning.
- `bun ~/.claude/skills/ship-tag/Tools/Changelog.ts lint --strict` exits 0 at release time.

## When entries get written

In the same PR as the change, under `[Unreleased]`. At release time the section *moves*; it is never written from scratch. That's what keeps entries accurate and cheap. `ReleaseCut.ts --bump` runs the move on the PR branch.

## Writing an entry

One line about the effect on the user, specific enough to act on: "Export reports to CSV from the Reports page", not "Refactored exporter". Say what breaks and what to do about it. Link an issue or PR when a reader would want to dig.

Commits are raw material, never a copy:

| Commit type | Category | Keep? |
|---|---|---|
| `feat` | Added, or Changed when it alters existing behaviour | yes |
| `fix` | Fixed | when a user could have hit it |
| `perf` | Changed | when it's measurable ("loads 60% faster") |
| `refactor`, `style`, `test`, `ci`, `build`, `chore` | none | usually omit: steps, not changes |
| `docs` | Changed | only user-facing documentation |
| `revert` | Removed or Fixed | describe the net effect |
| `BREAKING CHANGE` | Changed or Removed, plus the migration | always |
| deprecation | Deprecated | always, at least one release before the removal |
| security fix | Security | always, with the advisory or CVE id when public |

## Tool contract

```bash
T=~/.claude/skills/ship-tag/Tools/Changelog.ts
bun $T init                                   # new file; refuses to overwrite
bun $T add Fixed "Exports no longer time out on 10k-row reports."
bun $T release 1.4.0 [--date 2026-07-05]      # [Unreleased] -> [1.4.0], links rewritten
bun $T yank 1.3.2                             # heading gets [YANKED]; nothing deleted
bun $T notes 1.4.0                            # section body: tag message, PR text, package description
bun $T links [--rewrite]                       # write missing compare links; --rewrite fixes wrong ones (not the oldest)
bun $T lint [--strict]                        # errors exit 1; --strict also fails on warnings
```

Every command takes `--file <path>` (default `CHANGELOG.md`). `release` and `links` build compare links from `--repo-url <url>`, then `origin`'s URL, then the repository the file already links to (GitHub or Azure DevOps), with `--base <branch>` (default `main`) for `[Unreleased]`. `add` matches the file's existing spacing, so it never reflows someone's layout.

## Backfilling a repo that has tags but no changelog

One section per existing SemVer tag, newest first, dated from the tag:

```bash
git for-each-ref refs/tags --sort=-creatordate --format='%(refname:short) %(creatordate:short)'
git log --no-merges --format='%s' vPREV..vX.Y.Z
```

Summarize each range into entries. Where the history is too thin to say what changed, say so ("Initial tagged release") rather than inventing detail. Tags that aren't SemVer (date tags) stay out of version headings.

## Patterns and anti-patterns

| Do | Don't | Why |
|---|---|---|
| Curate entries in the PR | Generate them from `git log` at release | commit logs are noise to users |
| List a deprecation one release before the removal | Remove without warning | users need an upgrade path |
| ISO dates, `2026-07-05` | `07/05/2026`, `5 Jul` | unambiguous in every locale |
| ASCII ` - ` between version and date | em dash `—` or en dash `–` | tools that parse headings split on the hyphen |
| Keep yanked versions, marked `[YANKED]` | Delete the section | users on that version need to know |
| Mention every notable change | Pick a few highlights | a partial changelog gets trusted as complete |

Full samples and counter-examples: `References/ChangelogSamples.md`.
