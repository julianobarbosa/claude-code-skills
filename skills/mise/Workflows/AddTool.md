# Workflow: Add or pin a tool

Goal: add a tool to the project at a pinned version, via the right backend, in one reviewable step.

## 1. Decide: runtime or CLI, and which backend

- **Language/runtime** (node, python, go, ruby, java) → core backend, bare name.
- **CLI tool** → check the registry first: `mise registry | rg <name>`. If it's there, use the bare
  name or `aqua:` entry (signed, cross-platform, no compile).
- **GitHub-release binary** not in the registry → `ubi:owner/repo`.
- **Ecosystem package** (formatter/linter from npm/PyPI/cargo) → `npm:` / `pipx:` / `cargo:` so its
  version is pinned in `mise.toml` alongside everything else, not installed globally out-of-band.

See `References/Tools.md` § Backends for the full table.

## 2. Find the version to pin

```sh
mise ls-remote <tool>          # what versions exist
mise ls-remote <tool>@<major>  # narrow to a major line
```

Pin a **real** version in committed config — an exact version or a stable partial (`24`, `3.12`), not
`latest`. `latest` breaks reproducibility, which is the reason mise exists.

## 3. Add it — prefer `mise use`

`mise use` installs *and* writes the pin in one step, which is easier to review than hand-editing:

```sh
mise use node@24
mise use "npm:prettier@latest"     # dev CLI; latest acceptable for lint tooling, not runtimes
mise use -g <tool>@<ver>           # only if it's a personal global default, not project scope
```

Hand-editing `[tools]` is fine too — just run `mise install` afterward.

## 4. Verify

```sh
mise ls <tool>       # installed + active + which config pinned it
mise which <tool>    # resolves to the mise-managed binary, not a system one
<tool> --version     # actually runs
```

If `mise which` points at a system path instead of a shim, activation/shims aren't wired for this
context — see `Workflows/Troubleshoot.md`.

## 5. Lint

```sh
bun <skill-dir>/Tools/lint.ts mise.toml --strict   # <skill-dir> = this skill's directory
```

The linter flags an unpinned `latest` on a runtime; `--strict` makes that fail the exit code, so
fix it before committing.
