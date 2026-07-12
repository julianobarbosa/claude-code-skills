# Workflow: MigrateFromMake

Convert an existing `Makefile` into a Justfile that follows the house conventions.

Full translation table and per-feature notes: `References/MakeMigration.md`. This workflow is the
procedure; that reference is the lookup.

## Steps

1. **Read the Makefile.** Understand every target, variable, dependency, and `.PHONY` declaration.

2. **Group targets into concerns.** Don't translate 1:1 into a flat file. Map targets onto modules
   by domain (see the namespacing table in `SKILL.md`): build/test/lint/fmt → `dev.just` or
   `test.just`, container targets → `docker.just`, deploy/release → `ci.just`, etc.

3. **Create the root `Justfile`** from `Templates.md` with the three-line header, `mod` imports, and
   shortcut recipes. Translate `.DEFAULT_GOAL` / first-target-is-default into `_default`.

4. **Translate each target** into a module recipe, applying the table in `References/MakeMigration.md`:
   - Drop `.PHONY` (just doesn't track files).
   - `$(VAR)` / `${VAR}` → `{{var}}`; `$$VAR` → `$VAR` (no double-dollar escaping).
   - `VAR := value` → `var := "value"` (quote strings); `VAR ?= def` → `var := env_var_or_default("VAR", "def")`.
   - `$(shell cmd)` → `` `cmd` `` (but mind the parse-time gotcha — see `SKILL.md`).
   - `include file.mk` → `import 'file.just'` or a `mod`.
   - Multi-line `\`-continued shell blocks → shebang recipes.

5. **Rename to the standard vocabulary.** Map ad-hoc target names to `dev`/`test`/`build`/`lint`/
   `fmt`/`check`/`clean` where they match. Add `check: lint test`.

6. **Add a doc comment** above every recipe (Make's grep/awk help hack is replaced by
   `just --list`), and `[confirm(...)]` on destructive recipes.

7. **Lint and fix.**
   ```bash
   bun Tools/lint.ts <project-dir>
   ```

8. **Verify each recipe** with `just --dry-run <recipe>` before deleting the Makefile. During
   migration both files can coexist (`Makefile` vs `Justfile` don't conflict) — migrate and verify
   one concern at a time, then remove the Makefile.
