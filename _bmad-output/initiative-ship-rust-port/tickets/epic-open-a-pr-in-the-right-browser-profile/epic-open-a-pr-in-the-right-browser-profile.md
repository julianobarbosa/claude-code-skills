---
tracker_id: ""
type: epic
title: "A PR opens in the browser profile that can review it"
parent: initiative-ship-rust-port
covers: ["R11"]
sources: ["_bmad-output/initiative-ship-rust-port/archive-v6/epics.md"]
companions: []
after: []
status: done
risk: medium
---

# A PR opens in the browser profile that can review it

## Description

The operator opens any PR URL in the browser profile signed in with a chosen email, from WSL or macOS, so review happens with the right permissions instead of the wrong account's 404.

## Outcome

One command puts the PR in front of the operator under the account that can actually read it.

## Requirements

R1 (parent R11): `ship open` lists browser profiles from `Local State`, resolves an email to a profile directory, opens a URL in it, and `--set-default` writes `~/.config/ship/open.json`; works from WSL (Windows Edge/Chrome) and macOS.

## Constraints

- Launch arguments are an array, never a shell string, so a URL with `&` opens intact.
- An unknown email falls back to the Default profile with a note on stderr rather than failing.

## Done when

- `--list-profiles` prints one line per account read from `Local State`, matching `ship-open.ts`.
- `--dry-run` resolves the profile directory without launching.
- A launch works through `cmd.exe start` on WSL and `open -a` on macOS, and the remembered default is used when no `--profile` is given.

## Boundaries

- Creating the PR belongs to epic 3.
- Must not change: the `~/.config/ship/open.json` format the TS script reads.

## References

- parent — _bmad-output/initiative-ship-rust-port/initiative-ship-rust-port.md, section Requirements
- contract — _bmad-output/initiative-ship-rust-port/spec-ship-rust-port/cli-contract.md
- retrospective — epic-open-a-pr-in-the-right-browser-profile-retrospective.md

## Notes

- Retrospective: epic-open-a-pr-in-the-right-browser-profile-retrospective.md, 2026-11-12; its six action items are on the initiative.
