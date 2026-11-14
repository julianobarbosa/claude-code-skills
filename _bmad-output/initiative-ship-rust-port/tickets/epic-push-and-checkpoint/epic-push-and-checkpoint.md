---
tracker_id: ""
type: epic
title: "The binary pushes branches and cuts checkpoints"
parent: initiative-ship-rust-port
covers: ["R3", "R12"]
sources: ["_bmad-output/initiative-ship-rust-port/archive-v6/epics.md"]
companions: []
after: []
status: done
risk: high
---

# The binary pushes branches and cuts checkpoints

## Description

The operator pushes branches and cuts snapshot tags from the binary, with Azure Bearer auth and the stored-credential fallback, so a stale stored credential never blocks delivery.

## Outcome

Delivery writes come from the binary, authenticated the same way the TS scripts authenticated, with no token ever reaching output or a remote URL.

## Requirements

R1 (parent R3): `ship push` pushes the current branch and sets upstream; on Azure it uses an `az` Bearer token with `credential.helper` emptied and falls back to the stored credential when `az` is logged out; reports `push_ok=oauth-bearer|normal`; never force-pushes.
R2 (parent R12): `ship snapshot` creates an annotated tag on HEAD named `v<YYYY.MM.DD-HHMM>`, refuses an existing tag with exit 3, and `--push` pushes it with the same auth as R1.

## Constraints

- Tokens appear only in `Authorization` headers and are never printed, logged or put in URLs.
- Azure auth order is `az account get-access-token` first; the PAT variables only after a 401/403 or with `az` logged out.

## Done when

- A push on Azure with `az` logged in prints `push_ok=oauth-bearer`, and with `az` logged out prints `push_ok=normal`.
- A rejected push exits non-zero and never retries with force.
- `ship snapshot` tags, refuses a duplicate with exit 3, and pushes with the same auth order.

## Boundaries

- PR creation belongs to epic 3.
- Must not change: the refusal semantics of an existing tag.

## References

- parent — _bmad-output/initiative-ship-rust-port/initiative-ship-rust-port.md, section Requirements
- contract — _bmad-output/initiative-ship-rust-port/spec-ship-rust-port/cli-contract.md
