# Workflow: Create and wire tasks

Goal: turn the project's common commands into discoverable, composable mise tasks — a `make`/`just`
replacement that lives in the same config as the tools.

## 1. Inventory the real commands

Find what people actually run. Look in `package.json` scripts, a `Makefile`/`Justfile`, CI workflow
files, and README "how to build/test/run" prose. Those are your task candidates. Don't invent tasks
nobody uses.

## 2. Choose TOML tasks vs file tasks

- **TOML tasks** (in `mise.toml`) — the default. Best for short commands and anything a reader benefits
  from seeing inline.
- **File tasks** (executable scripts in `mise-tasks/`) — better for long/complex scripts, or when the
  script already exists. Add `#MISE description=...` / `#MISE depends=[...]` header comments.

See `References/Tasks.md` for both forms.

## 3. Write them to house style

- **Every task gets a one-line `description`** — `mise tasks` is the project's command menu, and an
  undescribed entry is dead weight.
- **Namespace related tasks** with colons: `test:unit`, `test:e2e`, `db:migrate`. Run a group with
  `mise run 'test:*'`.
- **Compose, don't duplicate.** A `ci` task should be `depends = ['lint', 'build', 'test']`, not a
  copy-paste of their commands.
- **Give build-like tasks `sources`/`outputs`** so mise skips them when nothing changed — free
  incremental builds.
- **Guard destructive tasks** with `confirm = '...'` (db resets, deploys, releases).
- **Parameterize** with a `usage` block when a task takes an environment/flag, rather than making three
  near-identical tasks. Access args as `${usage_*}`.

## 4. Verify each task runs

```sh
mise tasks                 # all listed, all described?
mise run <task>            # it actually executes in the mise env
mise run 'group:*'         # wildcard resolves the group
mise run ci --dry-run 2>/dev/null || mise run ci   # orchestrator runs deps in order
```

Tasks run with the project's `[tools]` and `[env]` loaded, so a task can assume the pinned toolchain
is on `PATH` — that's the point of keeping tasks in mise rather than a bare shell script.

## 5. Lint

```sh
bun <skill-dir>/Tools/lint.ts mise.toml --strict   # <skill-dir> = this skill's directory
```

The linter flags tasks missing a `description` (hidden tasks with `hide = true` are exempt);
`--strict` makes those warnings fail the exit code.
