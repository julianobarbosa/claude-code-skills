# Reference: CLI

Commands grouped by purpose. Run `mise <cmd> --help` for full flags; short aliases in parentheses.

## Tools & versions

| Command | Does |
|---------|------|
| `mise use <tool>@<ver>` | Install + pin to `mise.toml` (`-g` = global). |
| `mise install [<tool>@<ver>]` | Install without editing config; bare = everything in config. |
| `mise ls [tool]` | List installed tools/versions + source. |
| `mise ls-remote <tool>` | List installable versions. |
| `mise current [tool]` | Active version(s) here. |
| `mise outdated` | Tools with newer versions available. |
| `mise upgrade [tool]` | Upgrade tools (`--bump` also rewrites config pins). |
| `mise uninstall <tool>@<ver>` | Remove an installed version. |
| `mise prune` | Remove versions no config references. |
| `mise which <tool>` | Path to the active binary. |
| `mise where <tool>@<ver>` | Install directory of a version. |

## Running

| Command | Does |
|---------|------|
| `mise exec <tool>@<ver> -- <cmd>` (`x`) | Run a command under specific versions. |
| `mise run [task...]` (`r`) | Run task(s); bare = interactive/default. |
| `mise tasks` | List defined tasks. |
| `mise watch <task>` | Re-run a task on file changes. |
| `mise shell <tool>@<ver>` (`sh`) | Set a tool version for the current shell session. |

## Environment

| Command | Does |
|---------|------|
| `mise env` | Print exported env (`-s <shell>` for a syntax). |
| `mise set [KEY=VAL]` | List or set `[env]` vars. |
| `mise unset <KEY>` | Remove an `[env]` var. |
| `mise activate <shell>` | Emit shell activation hook (for rc file). |
| `mise hook-env` | Re-evaluate env for the current dir (scripts/internal). |

## Config

| Command | Does |
|---------|------|
| `mise config` (`cfg`) | Show config load order / resolved config. |
| `mise config ls` | List active config files + their tools. |
| `mise config get/set <key> [val]` | Read/write config values. |
| `mise trust` | Trust the current dir's config (`--untrust` to revoke). |

## Settings

| Command | Does |
|---------|------|
| `mise settings` | List all settings. |
| `mise settings get <key>` | Read one. |
| `mise settings set <key> <val>` | Write one (e.g. `jobs 8`). |
| `mise settings unset <key>` | Reset to default. |

## Plugins & backends

| Command | Does |
|---------|------|
| `mise plugin ls` | List installed plugins. |
| `mise plugin install <name>` | Install an asdf/vfox plugin. |
| `mise plugin update [name]` | Update plugin(s). |
| `mise registry` | Show tool → backend registry. |
| `mise link <tool>@<ver> <path>` | Symlink an externally-managed install into mise. |

## Maintenance & diagnostics

| Command | Does |
|---------|------|
| `mise doctor` | Health check: activation, PATH, config, plugins. |
| `mise self-update` | Update mise itself (disabled if installed via a package manager). |
| `mise reshim` | Rebuild shims (after installing new global binaries). |
| `mise cache clear` | Clear cached data. |
| `mise completion <shell>` | Generate shell completion script. |
| `mise generate <asset>` | Generate project assets (git hooks, CI configs). |
| `mise --version` | Show mise version. |

## Handy one-liners

```sh
mise use node@lts python@3.12          # pin several at once
mise x node@22 -- npm ci               # one-off under a version
mise run 'test:*' --jobs 8             # run a task group in parallel
mise ls --current                      # only what's active here
mise upgrade --bump                    # upgrade + rewrite config pins
MISE_DEBUG=1 mise install              # verbose install for debugging
```
