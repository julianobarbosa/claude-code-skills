# Workflow: Set up mise for a project

Goal: a committed `mise.toml` that makes the repo's toolchain, env, and common commands reproducible
for anyone who clones it.

## 1. Confirm mise is present and wired

```sh
mise --version   # is it installed?
mise doctor      # is the shell activated? are shims on PATH?
```

If mise isn't installed, install it (`curl https://mise.run | sh`) and add the activation line to the
user's shell rc — see `References/Configuration.md` § Activation. Don't proceed to write config the
user can't actually use.

## 2. Discover what the repo needs

Look before writing. Infer the toolchain from what's already in the repo:

- `package.json` (+ `engines`), `.nvmrc` → node, package manager (npm/pnpm/yarn/bun)
- `pyproject.toml` / `requirements.txt` / `.python-version` → python + tooling
- `go.mod` → go; `Cargo.toml` → rust; `Gemfile` / `.ruby-version` → ruby
- `*.tf` → terraform; `Dockerfile`/CI files → other CLIs the project assumes
- Existing `.tool-versions` (asdf) → import those pins directly

Pick the closest starting point from `Templates.md` rather than a blank file.

## 3. Write `mise.toml`

Follow the house style (see `SKILL.md` § House style):

- **Pin real versions**, not `latest`. Match whatever the repo already targets; if unknown, use the
  current stable major (`node = '24'`) and say so.
- Order `[tools]` → `[env]` → `[tasks.*]` → `[settings]`.
- Add `[env]` only for values that are genuinely per-project and safe to commit. Machine-local values
  and secrets go through a git-ignored `_.file = '.env'` — never inline secrets.
- Add tasks for the commands a newcomer would need on day one (dev/build/test/lint), each with a
  one-line `description`. Give the build task `sources`/`outputs` if it produces artifacts.

## 4. Handle git hygiene

- Commit `mise.toml`.
- Add to `.gitignore` if not already there: `mise.local.toml`, and whatever dotenv you referenced
  (`.env`, `.secrets.*`).

## 5. Validate — don't assume

```sh
bun <skill-dir>/Tools/lint.ts mise.toml --strict     # house-style + safety (<skill-dir> = this skill's directory)
mise trust                                           # trust the new config
mise install                                         # resolve + install all tools
mise ls                                              # confirm expected versions are active
mise tasks                                           # confirm tasks list with descriptions
mise run test                                        # smoke-test a task actually runs
```

## 6. Retire the redundant docs

Once `mise.toml` owns the toolchain, replace the "install node X, python Y…" prose in the README with
a short "run `mise install`" note. Two sources of truth drift; the config is now the one that matters.
