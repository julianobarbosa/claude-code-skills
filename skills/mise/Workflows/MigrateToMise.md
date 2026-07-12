# Workflow: Migrate to mise (from asdf / nvm / direnv / make)

Goal: consolidate an existing repo's version pins, env, and commands into one `mise.toml` without
breaking anyone mid-transition.

mise is intentionally backward-compatible — it reads `.tool-versions`, `.nvmrc`, and can coexist with
direnv — so migration can be incremental rather than a big-bang rewrite.

## From asdf (`.tool-versions`)

mise reads `.tool-versions` directly, so step one is zero-effort: `mise install` already works.

To move the pins into `mise.toml`:

1. Read `.tool-versions` — each line is `<tool> <version>`.
2. Translate to `[tools]` (same tool names for core tools; asdf plugins become `asdf:<plugin>` or,
   better, a native backend if one exists — check `mise registry`).
3. Verify parity: `mise ls` should show the same versions asdf did.
4. Once confirmed, delete `.tool-versions` (or keep it if other tooling still needs it — mise is fine
   either way).

asdf plugins work via `mise plugin install`, but prefer core/aqua/ubi backends where available — they
don't need a plugin and are faster.

## From nvm / rbenv / pyenv (idiomatic version files)

`.nvmrc`, `.ruby-version`, `.python-version` are read natively once enabled:

```toml
[settings]
idiomatic_version_file_enable_tools = ['node', 'ruby', 'python']
```

Then fold the version into `[tools]` and retire the idiomatic file. Remember: within a directory,
`mise.toml` outranks the idiomatic file, so add the pin before removing the old file to avoid a gap.

## From direnv (`.envrc`)

Move the exports into `[env]`:

- `export FOO=bar` → `FOO = 'bar'` under `[env]`
- `dotenv .env` → `_.file = '.env'`
- `PATH_add ./bin` → `_.path = ['./bin']`
- arbitrary shell logic → `_.source = './scripts/env.sh'`

mise ships a direnv integration if the two must run side by side during the move. See
`References/Environments.md`.

## From make / just / npm scripts

Translate each target/recipe/script into a task (`References/Tasks.md`):

- Makefile target → `[tasks.<name>]` with `run`. `.PHONY` targets map cleanly; file-producing targets
  become `sources`/`outputs`.
- `just` recipe → task; recipe params → a `usage` arg block.
- `package.json` scripts → tasks; `pre`/`post` hooks → `depends`.

Keep the old runner until the mise tasks are verified, then delete it so there's one source of truth.

## Verify the whole migration

```sh
bun <skill-dir>/Tools/lint.ts mise.toml --strict   # <skill-dir> = this skill's directory
mise trust
mise install     # same tools as before?
mise ls          # versions match the old pins
mise tasks       # every old command has a task
mise run ci      # the aggregate still passes
```

Migration is done when a fresh clone + `mise install` reproduces what the old three tools produced,
and the old config files are gone (or deliberately kept for a documented reason).
