---
type: migration
title: 'Move v6 planning and implementation artifacts into the v7 initiative layout'
status: draft
created: '2026-11-14'
---

# Migration v6 to v7 — plan

Module `method`, migration-1, from `6` to `7`. Nothing below has been applied.
The only write made so far is the backup. This plan waits for approval.

## 1. Answers

| Question | Answer | Confirmed? |
|---|---|---|
| Planning content is `_bmad-output/planning-artifacts` (epics.md, implementation-readiness.md) and implementation content is `_bmad-output/implementation-artifacts` (15 build records, 5 epic context caches, 1 retro, deferred-work.md, sprint-status.yaml). Right, and anything elsewhere? | Yes; plus `_bmad-output/specs/spec-ship-rust-port/`, which belongs to the same initiative | **default taken, needs your word** |
| Will this touch other repositories, or should the planning files keep their own git history apart from the code? (`workspace`) | No. Store stays in this repo, no `git init`, no workspace move | **default taken, needs your word** |
| Fold unstarted stories' files into their entries? | Yes (default). No effect here: the only unstarted story, 5.2, has no build record | **default taken** |

### Decisions I could not take for you

1. **Initiative slug.** The guide says name it after `core.project_name`, which gives
   `initiative-claude-code-skills`. The content is actually the ship Rust port, so
   `initiative-ship-rust-port` reads better. Pick one.
2. **Status of story 5.1.** Its v6 status is `awaiting-operator`, which is not in the
   migration's mapping table. Closest v7 value is `in-review` (agent-complete, waiting on
   a human), not `blocked`. Proposed: `in-review`.
3. **No PRD exists.** The initiative envelope is supposed to draw its Description, Outcome,
   Requirements and Done-when from a PRD. There is none, so they come from `epics.md`
   (Overview, Requirements Inventory, FR Coverage Map). Flagging it rather than inventing one.

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

`<slug>` is the initiative slug chosen in decision 1.

| From | To | Note |
|---|---|---|
| `planning-artifacts/` (the folder) | `initiative-<slug>/` | renamed, everything goes along |
| `planning-artifacts/implementation-readiness.md` | `initiative-<slug>/implementation-readiness/implementation-readiness.md` | flat file into a folder named after its stem |
| `planning-artifacts/epics.md` | `initiative-<slug>/archive-v6/epics.md` | tracking source, unchanged |
| `implementation-artifacts/sprint-status.yaml` | `initiative-<slug>/archive-v6/sprint-status.yaml` | tracking source, unchanged |
| `implementation-artifacts/epic-{1..5}-context.md` | `initiative-<slug>/archive-v6/` | v6 caches, unchanged |
| `implementation-artifacts/deferred-work.md` | `initiative-<slug>/deferred-work.md` | unchanged, per the guide |
| `implementation-artifacts/epic-4-retro-2026-11-12.md` | `initiative-<slug>/tickets/epic-open-a-pr-in-the-right-browser-profile/epic-open-a-pr-in-the-right-browser-profile-retrospective.md` | the name `bmad-retrospective` reads |
| 15 `implementation-artifacts/spec-N-M-<slug>.md` | `initiative-<slug>/tickets/epic-<slug>/tickets/story-<slug>-plan.md` | build records, criteria from `epics.md` merged in |
| `specs/spec-ship-rust-port/` | `initiative-<slug>/spec-ship-rust-port/` | document folder; `SPEC.md` renamed `spec-ship-rust-port.md`; `cli-contract.md` and `.memlog.md` ride along |

Every move is a `git mv`: all 28 files are tracked, so history follows them.

## 5. Ticket tree

`initiative-<slug>/tickets/tickets.toml`, one `[[epic]]` per `## Epic N:` in `epics.md`, in order:

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

- `_bmad/custom/config.user.toml` gains `active_initiative = "initiative-<slug>"` under `[core]` (file does not exist yet, so it is created)
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
