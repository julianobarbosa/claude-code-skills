---
tracker_id: ""
type: epic
title: "The skill runs the binary and the scripts are gone"
parent: initiative-ship-rust-port
covers: ["R13", "R22"]
sources: ["_bmad-output/initiative-ship-rust-port/archive-v6/epics.md"]
companions: []
after: []
risk: high
---

# The skill runs the binary and the scripts are gone

## Description

`SKILL.md` drives the binary, the TypeScript scripts are retired, and parity plus startup speed are proven side by side on one Azure and one GitHub repo before anything is deleted.

## Outcome

The ship skill works on a machine with no bun, and the evidence for that claim is a recorded parity run rather than trust.

## Requirements

R1 (parent R13): A prebuilt binary runs all seven subcommands on a clean Linux/WSL2 and a clean macOS host with no bun installed, driven by `SKILL.md`.
R2 (parent R22): Startup per subcommand is faster than the bun script it replaces, with a median under 50 ms for `detect` and `preflight` on Linux/WSL2.

## Constraints

- The parity check itself needs no npm, npx or Python.
- The 50 ms median is a default from Barbosa's 2026-11-08 answer and is to be changed before story 5.1 runs if it is wrong.

## Done when

- A parity run reports no difference in `key=value` lines or exit codes across every subcommand on both platforms.
- Median startup is recorded per subcommand for both implementations and the binary is faster for each.
- Every `bun scripts/ship-*.ts` invocation in `SKILL.md` becomes `ship <subcommand>`, and `scripts/*.ts`, `package.json`, `tsconfig.json` and `node_modules` are removed.

## Boundaries

- Building the binary belongs to epic 1; this epic proves and cuts over.
- Must not change: any flag or output key during cutover; a difference is a defect, not a migration.

## References

- parent — _bmad-output/initiative-ship-rust-port/initiative-ship-rust-port.md, section Requirements
- contract — _bmad-output/initiative-ship-rust-port/spec-ship-rust-port/cli-contract.md
