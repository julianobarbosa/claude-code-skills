---
name: justfile
description: |
  Create, edit, refactor, lint, and maintain Justfiles and `.just` module files using the `just`
  command runner. ALWAYS use this skill when the user mentions justfile, Justfile, just recipes,
  just modules, `.just` files, or asks to set up task automation with just. Also trigger when
  migrating a Makefile to just, adding recipes or modules to an existing Justfile, or organizing
  and documenting project commands. Covers house conventions, templates, namespacing by domain,
  dotenv, cross-platform support, and a structural lint. NOT FOR file-based build dependency
  graphs that need timestamp tracking (use make).
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
---

# Justfile Skill

`just` is a command runner (not a build system) that saves and runs project-specific commands in a
file called `Justfile`. It uses make-inspired syntax but is simpler and more portable, with none of
make's idiosyncrasies (`.PHONY`, tab sensitivity, implicit rules, timestamp tracking).

This skill enforces a consistent **house style** so every Justfile looks the same across projects.
The rules below are the authoritative convention; `Tools/lint.ts` validates the deterministic ones.

## Workflow Routing

| Trigger | Workflow |
|---------|----------|
| "create a justfile", "set up just", "add a recipe/module" | `Workflows/CreateJustfile.md` |
| "migrate Makefile to just", "convert make to just" | `Workflows/MigrateFromMake.md` |
| "check/lint this justfile", "is this justfile correct" | `Workflows/CheckJustfile.md` |

## When to Use Just vs Make

| Scenario | Tool |
|----------|------|
| Project task automation (build, test, deploy, lint) | **just** |
| Cross-platform command runner | **just** |
| Actual file-based build dependencies (compile `.c` → `.o`) | **make** |
| Legacy projects already deep in make | **make** (or migrate) |

## Common Mistakes — do NOT do these

Patterns the model often generates incorrectly. Check output against this list.

| WRONG | RIGHT |
|-------|-------|
| `justfile` (lowercase) | `Justfile` (capital J) |
| `mod docker` (bare) | `mod docker '.justfiles/docker.just'` |
| Module at `docker.just` or `just/docker.just` | Module at `.justfiles/docker.just` |
| `default:` | `_default:` (underscore required) |
| `@just --list` | `@just --list --unsorted` (module) or `--unsorted --list-submodules` (root with modules) |
| `env("NAME", "val")` | `env_var_or_default("NAME", "val")` |
| Module file without the three-line header | Every file gets the full header |
| Module file without its own `_default` recipe | Every file gets its own `_default` |
| Module named after a tool (`psql.just`) | Module named after a concern (`db.just`) |
| Tests in `docker.just` because they run in a container | Tests in `test.just` — classify by purpose, not implementation |
| Root recipe duplicates module logic | Root shortcut delegates: `build: docker-build` |
| Ad-hoc names (`run-tests`, `do-lint`) | Standard names: `test`, `lint`, `build`, `dev`, `fmt`, `check` |
| Relative paths in module recipes (`bash tests/run.sh`) | Use `source_directory()` for absolute paths |

## Mandatory Rules — apply to EVERY file you create or edit

1. The root file MUST be named `Justfile` (capital J).
2. EVERY file (root and every `.just` module) MUST start with this three-line header:
   ```just
   #!/usr/bin/env just --justfile
   set shell := ["bash", "-euo", "pipefail", "-c"]
   set dotenv-load := true
   ```
   Use `set dotenv-load := false` where appropriate, but the line must always be present.
3. EVERY file MUST have `_default` as its first recipe:
   ```just
   # List all available recipes
   _default:
       @just --list --unsorted
   ```
   The **root** Justfile with modules uses `@just --list --unsorted --list-submodules`. Module
   files use `@just --list --unsorted` (no `--list-submodules`).
4. Section order in every file: **variables → mod imports → recipes**.
5. Module files MUST live at `.justfiles/<name>.just` — never `just/`, never beside the root.
6. Import modules with explicit paths: `mod name '.justfiles/name.just'` — never bare `mod name`.
7. Use `env_var_or_default("NAME", "value")` for variable defaults — never `env()`.
8. Every recipe gets a `#` doc comment on the line directly above it.
9. Parameterized recipes document each param: `# param - description (default: value)`.
10. Private/helper recipes start with `_`.
11. Dependencies go on the definition line: `build: _lint test`.
12. Destructive recipes prompt for confirmation; the doc comment says "DESTRUCTIVE, prompts for confirmation".
13. Extract modules by **domain concern**, named after the concern (`db.just`) not the tool (`psql.just`). The root Justfile is a thin orchestrator: `_default`, shortcut recipes, and project-wide recipes like `check`/`clean`.
14. The root provides shortcut recipes for common workflows that delegate to modules, giving developers a flat namespace for everyday tasks.
15. Use the standard recipe vocabulary below as the public API. Never invent `run-tests`, `do-lint`, `compile`, `format`.
16. In modules, never use bare relative paths — module recipes run with the module's directory as CWD. Define `root := source_directory() / ".."` and reference files as `{{root}}/tests/run.sh`.

## Standard Recipe Vocabulary

A developer should be able to run `just test`, `just dev`, or `just check` in any project without guessing. Use these exact names; include only the ones that apply.

| Recipe | Purpose | Include when |
|--------|---------|--------------|
| `dev` | Start dev environment (server, watch, REPL) | Project has a dev loop |
| `test` | Run the test suite | Always |
| `build` | Build or compile | Project has a build step |
| `lint` | Run linters | Linters configured |
| `fmt` | Format code | Formatters configured |
| `check` | Run ALL quality gates (`check: lint test`) | Always |
| `clean` | Remove build artifacts, caches, generated files | Project produces output |

`check` is the meta-recipe — depend on the applicable gates and add format checks (`cargo fmt --check`, `ruff format --check`) as appropriate.

## Namespacing by Concern

Group by **domain**, not tool. Classify by purpose: a test that runs in Docker is a *testing* recipe (`test.just`), not a Docker recipe. A migration that uses kubectl is a *database* recipe (`db.just`).

| Concern | Module | Typical recipes |
|---------|--------|-----------------|
| Development | `dev.just` | build, test, lint, fmt, bench |
| Testing | `test.just` | run, list, watch, coverage |
| Containers | `docker.just` | build, push, run, compose-up |
| CI/CD | `ci.just` | lint, deploy, release |
| Database | `db.just` | migrate, seed, reset, dump, restore |
| Infrastructure | `infra.just` | plan, apply, destroy |
| Kubernetes | `k8s.just` | apply, diff, rollback, logs |
| Documentation | `docs.just` | build, serve, publish |

Single-concern projects (e.g. a Go/Rust project with only build/test/lint/fmt) use one `dev.just`; the root still stays thin. Modules are self-contained: own variables, own `_default`, no cross-module recipe dependencies.

## Templates & References

- **Templates** (root + module, copy-and-adapt): `Templates.md`
- **just language reference** (variables, args, deps, conditionals, attributes, functions, install): `References/Syntax.md`
- **Recipe fragments by project type** (Terraform, Go, Python, Docker, Azure, Ansible): `References/Patterns.md`
- **Makefile → just migration guide**: `References/MakeMigration.md`

## Linting

After creating or editing ANY Justfile or `.just` module, run the structural lint and fix every failure:

```bash
bun Tools/lint.ts <project-dir>
```

It checks file naming, the three-line header, `_default` as first recipe, the `--unsorted`/`--list-submodules` flags, `env_var_or_default()` usage, doc comments on all recipes, explicit module import paths, and section order. Any `FAIL` is a bug — fix and re-run until clean. The lint cannot judge concern-based naming, self-containment, or standard-vocabulary use — verify those by inspection (see `Workflows/CheckJustfile.md`).

## Gotchas

- **Each recipe line runs in a separate shell by default** — `cd foo` on one line and `ls` on the next runs `ls` in the original directory. Use a shebang recipe for multi-line scripts.
- **`set dotenv-load` loads `.env` from the justfile directory, not the invocation directory** — running `just` from a subdirectory loads the parent's `.env`. Use `set dotenv-path` to override.
- **Backtick variables evaluate at parse time, every invocation** — `git_hash := \`git rev-parse HEAD\`` runs git on every `just` call, even for unrelated recipes. Slow on large repos; move inside the recipe if not needed globally.
- **Recipe arguments don't shell-quote automatically** — `just deploy "my server"` passes two args. Use `set positional-arguments` with `"$@"`, or wrap as `{{quote(target)}}`.
- **`set shell := ["bash", "-c"]` breaks `set -euo pipefail` semantics** because each line is its own `-c` invocation — `pipefail` only applies within that line. Use shebang recipes for proper fail-fast scripts.
- **`just --list` hides `_`-prefixed and `[private]` recipes** but they're still callable — obscurity, not access control.
- **Cross-platform `[macos]`/`[linux]` attributes silently skip the recipe on other OSes** — running `just install` on Windows when only `[linux]`/`[macos]` variants exist exits 0 with no error, which looks like success.
- **The lint validates structure, not behavior** — a recipe can pass every check and still run the wrong command. Run `just --dry-run <recipe>` to verify expansion.
