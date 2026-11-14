---
type: migration
title: 'Move v6 planning and implementation artifacts into the v7 initiative layout'
status: done
created: '2026-11-14'
---

# Migration v6 to v7 — plan

Module `method`, migration-1, from `6` to `7`. Nothing below has been applied.
The only write made so far is the backup. This plan waits for approval.

## 1. Answers

| Question | Answer | Confirmed? |
|---|---|---|
| Planning content is `_bmad-output/planning-artifacts` (epics.md, implementation-readiness.md) and implementation content is `_bmad-output/implementation-artifacts` (15 build records, 5 epic context caches, 1 retro, deferred-work.md, sprint-status.yaml). Right, and anything elsewhere? | Yes; plus `_bmad-output/specs/spec-ship-rust-port/`, which belongs to the same initiative | confirmed by Barbosa 2026-11-14 |
| Will this touch other repositories, or should the planning files keep their own git history apart from the code? (`workspace`) | No. Store stays in this repo, no `git init`, no workspace move | confirmed by Barbosa 2026-11-14 |
| Fold unstarted stories' files into their entries? | Yes (default). No effect here: the only unstarted story, 5.2, has no build record | **default taken** |

### Decisions I could not take for you

1. **Initiative slug.** The guide says name it after `core.project_name`, which gives
   **Answered: `initiative-ship-rust-port`.**
   `initiative-ship-rust-port` reads better. Pick one.
2. **Status of story 5.1.** Its v6 status is `awaiting-operator`, which is not in the
   migration's mapping table. Closest v7 value is `in-review` (agent-complete, waiting on
   a human), not `blocked`. **Answered: `in-review`.**
3. **No PRD exists.** The initiative envelope is supposed to draw its Description, Outcome,
   Requirements and Done-when from a PRD. There is none, so they come from `epics.md`
   (Overview, Requirements Inventory, FR Coverage Map). **Answered: ok.**

## 2. Backup

`.v6-v7-migration-backup-20261114-1235/` holds `_bmad/` (21 files) and `_bmad-output/`
(28 files), with a `.gitignore` of `*` so it is never committed. Counts verified equal
to the sources.

## 3. Inventory and detect signals

28 files under the source folders. All four v6 signals present:

- `planning-artifacts/epics.md` and `implementation-artifacts/sprint-status.yaml` (v6 for certain)
- 15 `spec-<epic>-<story>-<slug>.md` build records with `route:` and `status:` frontmatter
- `specs/spec-ship-rust-port/SPEC.md`
- No `active_initiative`, no `initiative-*/` folder, so nothing blocks the migration

## 4. What moves where

The initiative slug is `ship-rust-port`.

| From | To | Note |
|---|---|---|
| `planning-artifacts/` (the folder) | `initiative-ship-rust-port/` | renamed, everything goes along |
| `planning-artifacts/implementation-readiness.md` | `initiative-ship-rust-port/implementation-readiness/implementation-readiness.md` | flat file into a folder named after its stem |
| `planning-artifacts/epics.md` | `initiative-ship-rust-port/archive-v6/epics.md` | tracking source, unchanged |
| `implementation-artifacts/sprint-status.yaml` | `initiative-ship-rust-port/archive-v6/sprint-status.yaml` | tracking source, unchanged |
| `implementation-artifacts/epic-{1..5}-context.md` | `initiative-ship-rust-port/archive-v6/` | v6 caches, unchanged |
| `implementation-artifacts/deferred-work.md` | `initiative-ship-rust-port/deferred-work.md` | unchanged, per the guide |
| `implementation-artifacts/epic-4-retro-2026-11-12.md` | `initiative-ship-rust-port/tickets/epic-open-a-pr-in-the-right-browser-profile/epic-open-a-pr-in-the-right-browser-profile-retrospective.md` | the name `bmad-retrospective` reads |
| 15 `implementation-artifacts/spec-N-M-<slug>.md` | `initiative-ship-rust-port/tickets/epic-<slug>/tickets/story-<slug>-plan.md` | build records, criteria from `epics.md` merged in |
| `specs/spec-ship-rust-port/` | `initiative-ship-rust-port/spec-ship-rust-port/` | document folder; `SPEC.md` renamed `spec-ship-rust-port.md`; `cli-contract.md` and `.memlog.md` ride along |

Every move is a `git mv`: all 28 files are tracked, so history follows them.

## 5. Ticket tree

`initiative-ship-rust-port/tickets/tickets.toml`, one `[[epic]]` per `## Epic N:` in `epics.md`, in order:

| id | slug | title | v6 status | v7 status |
|---|---|---|---|---|
| 1 | `epic-first-binary-inspect-a-repo` | First binary: inspect a repo | done | `done` |
| 2 | `epic-push-and-checkpoint` | Push and checkpoint | done | `done` |
| 3 | `epic-open-and-manage-prs` | Open and manage PRs | done | `done` |
| 4 | `epic-open-a-pr-in-the-right-browser-profile` | Open a PR in the right browser profile | done | `done` |
| 5 | `epic-cut-over-ship-with-no-bun` | Cut over: ship with no bun | backlog | no `status` line |

16 stories become `[[entry]]` rows in their epic's `tickets/tickets.toml`, each keeping
`v6_key = "N-M-<slug>"`. 15 carry a build record and get a `story-<slug>-plan.md`:

- Epic 1: 1.1, 1.2, 1.3 — all `done`
- Epic 2: 2.1, 2.2 — all `done`
- Epic 3: 3.1 through 3.7 — all `done`
- Epic 4: 4.1, 4.2 — all `done`
- Epic 5: 5.1 — `awaiting-operator` to map (decision 2); **5.2 has no build record**, so it
  stays an entry with no plan, its criteria kept in the entry description

## 6. Action items

Six `open` items from `sprint-status.yaml` become `Action item:` lines in the initiative's
Notes, each with owner (Barbosa) and epic (4), referencing the retro. None are `done`, so
none are dropped.

## 7. Files left in place

None. Every one of the 28 files lands in the initiative, its `archive-v6/`, or a document
folder. Nothing goes to `backlog/` or `archive/`; both are created with a `.gitkeep`.

## 8. Configuration

- `_bmad/custom/config.user.toml` gains `active_initiative = "initiative-ship-rust-port"` under `[core]` (file does not exist yet, so it is created)
- `output_folder` is not touched: the store is not moving
- `planning_artifacts` and `implementation_artifacts` are left alone, as the guide requires; `bmad setup`'s v6 cleanup owns those keys
- No `_bmad/custom/` override names a moved path, and no other module's config points inside the planning folder

## 9. Path rewrites

To be computed at run time: every live `inputDocuments:`, `sources:`, `companions:`,
References and prose link inside the store is rewritten to its new path. References from
outside the store are **listed, never edited** — the six action items in `sprint-status.yaml`
already point at `_bmad-output/implementation-artifacts/epic-4-retro-2026-11-12.md`, so that
path appears in the report for you to update.

## 10. Checklist

The migration's 14 checklist items run after the move; each result is recorded here.
No results yet: nothing has been applied.

## 11. Checklist results — all 14 green

1. Every v6 file is under the initiative, its `archive-v6/`, or a document folder. Nothing was left in place and nothing was deleted.
2. `spec-ship-rust-port/` and `implementation-readiness/` kept their v6 names and every file; each main file is named after its folder. `initiative-ship-rust-port/`, `backlog/` and `archive/` exist, the last two with a `.gitkeep`.
3. No dated or numbered duplicate documents existed.
4. `tickets.py status initiative-ship-rust-port` exits 0 and counts 16 total: 14 done, 1 review, 1 planned, matching the archived `sprint-status.yaml` exactly.
5. 16 stories are 16 entries; the 15 build records are 15 plans; story 5.2 has no record and keeps its criteria in its entry. No epic story files were written (`file: null` on every ticket).
6. Every plan carries a build `type`, a mapped `status` and a `baseline_revision`; all 15 baselines were recorded in v6, none inferred, none missing. The retrospective sits in epic 4 with `epic: 4` and a verdict, no ticket or leaf type.
7. Every epic `covers` id resolves to an initiative Requirements line, and every entry `covers` id to a line in its own epic. R14 to R21 (NFR1 to NFR8) are cross-cutting by the coverage map's own statement and are declared in the initiative's Boundaries.
8. `migrate_v6.py` reports no `legacy_leftovers`: the spec folder is a v6 document folder, not a 6.13 pre-release spec, and the detector leaves it alone. No `CAP-` id exists outside `archive-v6/`.
9. Live references were rewritten: 9 distinct `source_spec` paths in `deferred-work.md` now point at the plan files. `archive-v6/epics.md` and `archive-v6/sprint-status.yaml` keep their original paths, as archived files must. `implementation-readiness.md` quotes the `planning_artifacts` and `implementation_artifacts` config values, which were deliberately left unchanged, so its text stays accurate.
10. `_bmad/custom/config.user.toml` names `active_initiative = "initiative-ship-rust-port"` under `[core]`, and `core.output_folder` still resolves to `_bmad-output`.
11. No module config key pointed inside the renamed planning folder.
12. The store stays in this repository, as answered. No file is tracked twice.
13. `.v6-v7-migration-backup-20261114-1235/` holds all 49 pre-migration files and is excluded by its own `.gitignore`, so no commit includes it.
14. This plan records every question, its answer, the backup path and each item's result.

## 12. Not done, on purpose

`migrate_v6.py --clean` was **not** run. It would strip 7 stale v6 keys (`core.user_name`,
the two language keys and 4 `modules.bmm.*`) from `_bmad/config.toml`, which is tracked in
git and shared with the live v6 install in the main checkout. Removing them here would break
v6 the moment this branch merged. The keys are listed in the report and the call is Barbosa's.
