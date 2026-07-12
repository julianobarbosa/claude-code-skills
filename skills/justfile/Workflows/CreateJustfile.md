# Workflow: CreateJustfile

Create a new Justfile (and its `.just` modules) for a project, following the house conventions.

## Steps

1. **Identify the concerns.** List the task domains the project needs (dev, test, docker, ci, db,
   infra, k8s, docs). Map each to a module from the namespacing table in `SKILL.md`. Single-concern
   projects use one `dev.just`.

2. **Pick the standard recipes.** From the vocabulary table in `SKILL.md`, select the public API
   (`dev`, `test`, `build`, `lint`, `fmt`, `check`, `clean`) — include only those that apply. Skip
   `build` for a project with no build step; skip `test` for a static site with no tests.

3. **Scaffold the root `Justfile`** from the root template in `Templates.md`:
   - Three-line header (`set dotenv-load := true` unless the project has no `.env`).
   - Project-wide variables via `env_var_or_default(...)`.
   - One `mod name '.justfiles/name.just'` per concern.
   - `_default` first, using `@just --list --unsorted --list-submodules` (root with modules).
   - Shortcut recipes delegating to modules (`build: docker-build`), plus `check: lint test`.

4. **Scaffold each module** at `.justfiles/<name>.just` from the module template in `Templates.md`:
   - Same three-line header, own `_default` with `@just --list --unsorted` (no `--list-submodules`).
   - Section order: variables → (mods, rare in modules) → recipes.
   - `root := source_directory() / ".."` for any path to a project file.
   - Doc comment above every recipe; `# param - desc (default: val)` for parameters.
   - `[confirm(...)]` or an inline prompt on destructive recipes; note "DESTRUCTIVE, prompts for
     confirmation" in the doc comment.

5. **Pull recipe content** from `References/Patterns.md` for the project's stack (Terraform, Go,
   Python, Docker, Azure, Ansible), adapting each fragment into the house structure.

6. **Lint and fix.**
   ```bash
   bun Tools/lint.ts <project-dir>
   ```
   Fix every `FAIL` and re-run until clean.

7. **Verify expansion** of a couple of recipes without executing them:
   ```bash
   just --justfile <project-dir>/Justfile --dry-run <recipe>
   ```

8. **Manual checklist** (judgment calls the linter can't make) — run `Workflows/CheckJustfile.md`.
