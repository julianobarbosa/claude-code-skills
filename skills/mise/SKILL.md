---
name: mise
description: |
  Set up, configure, and maintain development environments with `mise` (mise-en-place) — the
  polyglot tool/version manager, per-directory environment switcher, and task runner. ALWAYS use
  this skill when the user mentions mise, `mise.toml`, `.mise.toml`, `mise use`, `mise run`, pinning
  tool/language versions per project, an asdf / nvm / rbenv / pyenv / direnv replacement, a
  `.tool-versions` file, or wants project-scoped env vars and task automation in one config. Also
  trigger when scaffolding a dev environment for a repo, migrating from asdf/nvm/direnv/make to
  mise, adding a tool from a backend (npm, cargo, pipx, aqua, ubi/GitHub), or diagnosing "tool not
  found" / activation / shim problems. Covers house conventions, a sample-driven config template,
  workflows, a `mise.toml` best-practice linter, and a full CLI reference. NOT FOR system package
  management (apt/brew for OS libraries), Nix flakes, or make-style file-timestamp build graphs
  with complex dependency trees.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
---

# mise Skill

`mise` (pronounced "meez", short for *mise-en-place*) is a single static binary that does three jobs
that usually take three tools:

| Job | Tools it replaces | Where it lives in config |
|-----|-------------------|--------------------------|
| Manage tool/language versions per project | asdf, nvm, rbenv, pyenv | `[tools]` |
| Switch environment variables per directory | direnv, dotenv | `[env]` |
| Run project tasks | make, npm scripts, just | `[tasks.*]` + `mise run` |

Everything lives in one committed `mise.toml`. This skill enforces a consistent **house style** so
every project's mise config reads the same way, and treats `mise.toml` as source-controlled infra:
pinned, reviewable, reproducible.

## Before you touch anything

`mise.toml` can execute code (via `[tasks]`, `env._.source`, `env._.file`). Two habits keep that safe
and predictable:

1. **Verify mise is present and how it's wired**: run `mise --version` and `mise doctor`. `doctor`
   tells you whether the shell is activated, whether shims are on `PATH`, and which config files load.
   Never assume — the #1 class of mise bugs is "tool installed but not found", and it's almost always
   an activation/shim issue, not a version issue.
2. **Trust before you run**: mise refuses to evaluate a config in an untrusted directory. After
   creating or editing a `mise.toml`, `mise trust` in that directory (or add the path to
   `trusted_config_paths`).

Per the operating rules here: any executable helper you add to a project ships as **TypeScript run
with `bun`**, never Python or npm/npx.

## Choose a workflow

Route to the workflow file that matches the request. Each is a self-contained recipe — read it, then
follow it.

| The user wants to… | Workflow |
|--------------------|----------|
| Stand up mise for a repo (tools + env + tasks from scratch) | `Workflows/SetupProject.md` |
| Add or pin a tool, pick the right backend | `Workflows/AddTool.md` |
| Define, wire, and run tasks | `Workflows/CreateTasks.md` |
| Move an existing repo off asdf / nvm / direnv / make | `Workflows/MigrateToMise.md` |
| Fix "tool not found" / wrong version / activation / trust | `Workflows/Troubleshoot.md` |

Reach for `Templates.md` whenever you need a concrete starting `mise.toml` — copy the closest sample
and delete what doesn't apply rather than writing one from a blank page.

## House style

These conventions are what the linter (`Tools/lint.ts`) checks. They exist because a `mise.toml` is a
contract the whole team (and CI, and future-you) reads — surprises in it are expensive.

- **Pin real versions in committed config.** `node = '24'` or `node = '24.3.0'`, not `node = 'latest'`.
  `latest` means "whatever exists the day someone runs `mise install`" — it silently breaks
  reproducibility, which is the entire reason to use mise. `latest` is fine for a throwaway
  `mise x`, never for `mise.toml`. Global `~/.config/mise/config.toml` is the one place `lts`/`latest`
  is acceptable, because it's personal, not shared.
- **Order sections top-down as a reader would want them:** `[tools]`, then `[env]`, then `[tasks.*]`,
  then `[settings]`. Tools define the world, env configures it, tasks act in it.
- **Every task gets a `description`.** `mise tasks` is the project's command menu; an undescribed task
  is a dead entry. One line, imperative ("Build the release binary").
- **Secrets are redacted, never inlined.** Load them from a git-ignored `.env`/`.env.json` via
  `env._.file`, or mark them `redact = true`. A literal token in a committed `mise.toml` is a leak.
- **Personal overrides go in `mise.local.toml`** (git-ignored), not in the committed file. Keep the
  shared config clean.
- **Prefer `mise use` over hand-editing** for tools, because it installs *and* writes the pin in one
  reviewable step — but hand-editing is fine and expected for env and tasks.

## Best practices worth stating out loud

- **Reproducibility is the point.** If two teammates run `mise install` and get different tool
  versions, the config has failed at its one job. Pinning is not pedantry; it's the deliverable.
- **Activation vs shims is the mental model that prevents most pain.** `mise activate` updates `PATH`
  at your shell prompt — great interactively, invisible to scripts/IDEs/cron because they never hit a
  new prompt. Shims (`~/.local/share/mise/shims`) are real files that work everywhere. When something
  can't find a tool outside an interactive shell, the fix is shims or `mise exec`, not reinstalling.
  See `References/Configuration.md` and `Workflows/Troubleshoot.md`.
- **`sources`/`outputs` turn tasks into a cheap build cache.** A task that declares what it reads and
  writes is skipped when nothing changed — make-style incrementality without make's footguns.
- **Let mise own the versions, not the READMEs.** Once `mise.toml` pins the toolchain, delete the
  "install node 24, python 3.12…" prose from onboarding docs and point at `mise install`. The config
  is now the single source of truth; two sources drift.

## Validate before you call it done

After writing or editing a `mise.toml`, lint it and prove it loads:

```bash
bun <skill-dir>/Tools/lint.ts path/to/mise.toml --strict   # house-style + safety check
mise trust path/to/                                        # trust the dir if new
mise install                                               # resolves + installs everything
mise ls                                                    # confirm the versions you expect are active
mise tasks                                                 # confirm tasks are listed with descriptions
```

`<skill-dir>` is this skill's directory (wherever this SKILL.md lives — never assume a fixed
install path). `--strict` makes warnings fail the exit code too, so the lint works as a real gate.

A change isn't finished because the file parses — it's finished when `mise install` succeeds and the
tools/tasks you intended actually show up. Verify, don't assume.

## Reference material

Load the reference that matches the depth you need — these hold the exhaustive detail so this file
stays scannable.

- `References/Configuration.md` — `mise.toml` structure, config resolution & precedence, `[settings]`,
  trust, activation vs shims.
- `References/Tools.md` — version strings, `use`/`install`/`ls`/`upgrade`/`prune`, backends (npm,
  cargo, pipx, aqua, ubi, go, asdf/vfox).
- `References/Tasks.md` — TOML & file tasks, `depends`, `sources`/`outputs`, `usage` argument specs,
  parallelism.
- `References/Environments.md` — `[env]`, `_.file`/`_.source`/`_.path`, secrets & redaction, templates.
- `References/CliReference.md` — every command you reach for, grouped by purpose.
