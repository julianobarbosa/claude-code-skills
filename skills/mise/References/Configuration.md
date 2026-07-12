# Reference: Configuration

## `mise.toml` structure

A single file holds tools, env, tasks, and settings:

```toml
[tools]
node = '24'
python = '3.12'

[env]
NODE_ENV = 'development'

[tasks.dev]
run = 'npm run dev'

[settings]
jobs = 8
```

## Config file locations & precedence

mise merges multiple files. **Closer to `cwd` wins**, and within a directory, later-loaded wins.

| File | Scope |
|------|-------|
| `~/.config/mise/config.toml` | Global (all projects). Written by `mise use -g`. |
| `./mise.toml` | Project-local, committed. Written by `mise use`. |
| `./mise.local.toml` | Project-local, **git-ignored** — personal overrides. |
| `./mise.<env>.toml` | Environment-specific, active when `MISE_ENV=<env>` (e.g. `mise.production.toml`). |
| `.tool-versions` | asdf-compatible tool list (tools only, no env/tasks). |
| Idiomatic files | `.node-version`, `.nvmrc`, `.ruby-version`, `.python-version`, … |

Within the same directory, `mise.toml` **outranks** idiomatic files like `.nvmrc`.

Inspect what's actually loaded:

```sh
mise config ls     # active config files + the tools each defines
mise config        # resolved config / load order
```

### Idiomatic version files

Reading `.nvmrc`-style files is opt-in per tool, to avoid surprises:

```toml
[settings]
idiomatic_version_file_enable_tools = ['node', 'ruby']
```

## `[settings]`

Controls mise's own behavior. Manage from the CLI or edit directly:

```sh
mise settings                    # list
mise settings get <key>
mise settings set jobs 8
mise settings unset <key>
```

Frequently used:

| Setting | Purpose |
|---------|---------|
| `jobs` | Parallel install/task jobs (default 4). Also `MISE_JOBS`. |
| `trusted_config_paths` | Directories whose configs are auto-trusted. |
| `idiomatic_version_file_enable_tools` | Which tools may read `.nvmrc`-style files. |
| `experimental` | Enable experimental features. |
| `env_file` | Default dotenv file to auto-load. |
| `status.show_tools` / `status.show_env` | Toggle the per-`cd` status line. |

Any setting is also settable via `MISE_<UPPER_SNAKE>` env var (`MISE_JOBS=8`, `MISE_EXPERIMENTAL=1`).

The `[_]` table is a scratch space mise never parses — use it for arbitrary metadata.

## Trust

mise won't evaluate a `mise.toml` (it can run code) until the directory is trusted:

```sh
mise trust              # trust current dir
mise trust --untrust    # revoke
```

Or pre-trust trees:

```toml
[settings]
trusted_config_paths = ['~/work/my-trusted-projects']
```

## Activation vs shims — the core mental model

| Mechanism | How it works | Best for |
|-----------|--------------|----------|
| `mise activate <shell>` | Hooks the shell prompt; updates `PATH`/env **at the next prompt**. | Interactive shells. |
| Shims | Real files in `~/.local/share/mise/shims/` that dispatch to the right version. | Non-interactive: scripts, IDEs, cron, CI. |

Activation only refreshes on a new prompt, so a tool installed *inside* a running script isn't on
`PATH` in that same script. Fixes: `mise exec -- <cmd>`, `eval "$(mise hook-env)"`, or put the shim
dir on `PATH`. To enable shims in-shell (fish example):

```fish
mise activate fish --shims | source
mise activate fish | source
```

Activation lines by shell:

```sh
eval "$(mise activate bash)"          # ~/.bashrc
eval "$(mise activate zsh)"           # ${ZDOTDIR-$HOME}/.zshrc
mise activate fish | source           # ~/.config/fish/config.fish
```
