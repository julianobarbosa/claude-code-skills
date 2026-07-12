# Workflow: CheckJustfile

Validate an existing Justfile against the house conventions — automated structural lint plus the
judgment-call checklist the linter cannot cover.

## 1. Structural lint (automated)

```bash
bun Tools/lint.ts <project-dir>
```

Checks: file naming (`Justfile` capital J, no root-level `.just`, no `just/` dir), the three-line
header, `_default` as the first recipe, `--unsorted` (and `--list-submodules` only on the root with
modules), `env_var_or_default()` (no bare `env()`), doc comments on every recipe, explicit module
import paths, and section order. Every `FAIL` is a bug — fix and re-run until the summary reports
`0 errors`.

> Requires `bun`. The validator reads the directory listing to check the exact filename, so the
> capital-`J` (`Justfile` vs `justfile`) check is reliable on every platform, including
> case-insensitive macOS filesystems.

## 2. Parse check (automated)

Confirm the root and every module parse:

```bash
just --justfile <project-dir>/Justfile --summary >/dev/null && echo "root OK"
```

## 3. Manual checklist (judgment calls)

The linter validates structure, not intent. Verify by inspection:

- [ ] Recipes organized into modules by **domain concern** (purpose, not implementation tool).
- [ ] Modules named after concerns, not tools (tests-in-Docker → `test.just`, not `docker.just`).
- [ ] Root with modules has shortcut recipes for common workflows (flat namespace for daily tasks).
- [ ] Modules are self-contained — no cross-module recipe dependencies.
- [ ] Module recipes use `source_directory()` paths, not bare relative paths.
- [ ] Standard recipe names used where applicable (`dev`, `test`, `build`, `lint`, `fmt`, `check`, `clean`).
- [ ] Param docs present: `# param - desc (default: val)` on parameterized recipes.
- [ ] Destructive recipes prompt for confirmation and the doc comment says "DESTRUCTIVE, prompts for confirmation".
- [ ] Dependencies on the recipe definition line, not buried in the body.

## 4. Behavior spot-check (optional)

A recipe can pass every structural check and still run the wrong command. For risky recipes,
confirm the expansion without executing:

```bash
just --justfile <project-dir>/Justfile --dry-run <recipe>
```
