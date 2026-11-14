---
tracker_id: ""
type: epic
title: "The binary opens and manages pull requests"
parent: initiative-ship-rust-port
covers: ["R4", "R5", "R6", "R7", "R8", "R9", "R10"]
sources: ["_bmad-output/initiative-ship-rust-port/archive-v6/epics.md"]
companions: []
after: []
status: done
risk: high
---

# The binary opens and manages pull requests

## Description

The operator opens PRs on GitHub and Azure Repos from the binary with work items, related links, transitions, tags and reviewers, and edits PR tags after review starts.

## Outcome

A PR reaches review with a real Board item, the right reviewers and a truthful triage tag, without anyone opening a web UI.

## Requirements

R1 (parent R4): `ship pr` opens a PR on the detected platform; on Azure it verifies the work item or creates one per task assigned to `SHIP_ADO_ASSIGNEE`, and links it.
R2 (parent R5): `ship pr --related` verifies each id and links it Related to the PR's own work item, never to the PR.
R3 (parent R6): `ship pr --transition` moves each linked or created item after the PR opens; `completionOptions.transitionWorkItems` is set by a post-create update and read back from that response.
R4 (parent R7): `ship pr` applies tags from `--tag`, else the Conventional-Commit title, else the branch prefix, else `needs-review` with a warning; `--no-tag` disables.
R5 (parent R8): `ship pr` adds optional and required reviewers, resolving Azure UPNs and skipping unresolvable ones with `reviewer_skipped`; `SHIP_ADO_DEFAULT_REVIEWER` applies on Azure when none is given.
R6 (parent R9): On GitHub, `ship pr` creates the PR, then attaches labels and reviewers in follow-up calls.
R7 (parent R10): `ship tag <pr-id>` adds, removes and lists PR tags (Azure) or labels (GitHub).

## Constraints

- `createPullRequest` drops `completionOptions`, so the completion flag is set by an update after create and read back from that response, never from the flag.
- Titles are passed literally so `&` is never escaped, and nothing in a title or body carries AI attribution.

## Done when

- A GitHub PR opens with labels and reviewers attached in follow-up calls.
- An Azure PR opens in one call carrying a verified work-item link, tags and draft state, or with items created one per task.
- Related ids link to the PR's own item and never to the PR, and transitions move items after open.
- `ship tag` adds, removes and lists on both platforms, and re-adding an existing tag succeeds.

## Boundaries

- Opening the PR in a browser belongs to epic 4.
- Must not change: the work-item verification step that keeps an unverified id from being linked.

## References

- parent — _bmad-output/initiative-ship-rust-port/initiative-ship-rust-port.md, section Requirements
- contract — _bmad-output/initiative-ship-rust-port/spec-ship-rust-port/cli-contract.md
