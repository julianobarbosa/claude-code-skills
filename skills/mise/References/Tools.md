# Reference: Tools & Versions

## install vs use

| Command | Installs? | Edits config? |
|---------|-----------|---------------|
| `mise install node@20.11.0` | ✅ | ❌ (activates only if already in config) |
| `mise use node@20.11.0` | ✅ | ✅ (adds pin to `mise.toml`, activates on `cd`) |

```sh
mise use node@20.11.0     # install + pin (./mise.toml)
mise use -g node@lts      # global default
mise install node@20.11.0 # install only
mise install              # install everything in the active config
```

## Version strings

```toml
[tools]
node = '24'         # partial/fuzzy pin — latest 24.x
ruby = 'latest'     # newest stable (avoid in committed config)
go = '1.22.5'       # exact pin
python = ['3.12', '3.11']   # multiple; first is default, both installed
```

Accepted forms: exact (`20.11.0`), partial/fuzzy (`24`, `3.12`), `latest`, `lts` (where defined),
lists, and backend-specific prefixes like `ref:main` / `prefix:1.2`.

**House rule:** pin real versions in committed `mise.toml`. `latest`/`lts` belong only in personal
global config or throwaway `mise x`.

## Listing & inspecting

```sh
mise ls                 # installed tools + active version + source
mise ls node            # versions of one tool
mise ls-remote node     # all installable versions
mise ls-remote node@22  # available 22.x
mise current [tool]     # active versions here
mise outdated           # tools with newer versions available
mise which node         # path to the active binary
mise where node@24      # install dir of a version
```

## Upgrading & removing

```sh
mise upgrade            # upgrade all within config constraints
mise upgrade node       # one tool
mise upgrade --bump     # also rewrite the version pins in mise.toml
mise uninstall node@20.11.0
mise prune              # remove versions no config references
mise prune --dry-run
```

## Backends

mise installs from many ecosystems. Reference a backend with `backend:name`.

| Backend | Prefix | Example |
|---------|--------|---------|
| Core (built-in) | *(none)* | `node`, `python`, `go`, `ruby`, `java` |
| aqua | `aqua:` | `aqua:BurntSushi/ripgrep` |
| GitHub releases (ubi) | `ubi:` | `ubi:cli/cli` |
| npm | `npm:` | `npm:prettier` |
| PyPI (pipx) | `pipx:` | `pipx:black` |
| Cargo | `cargo:` | `cargo:cargo-edit` |
| Go modules | `go:` | `go:github.com/goreleaser/goreleaser` |
| asdf plugins | `asdf:` | `asdf:someplugin` |
| vfox plugins | `vfox:` | `vfox:someplugin` |

Usage is identical across backends:

```sh
mise use npm:prettier@latest
mise use ubi:BurntSushi/ripgrep
```

```toml
[tools]
node = '24'
"npm:prettier" = 'latest'
"ubi:BurntSushi/ripgrep" = 'latest'
"pipx:black" = 'latest'
```

`mise registry` shows the tool → backend mapping (e.g. what `ripgrep` resolves to by default).

## One-off under a specific version

```sh
mise exec node@22 -- node -v     # `x` is the alias
mise x node@22 -- npm ci
```

## Which backend should I pick?

- A **language/runtime** (node, python, go, ruby, java) → core backend, bare name.
- A **CLI tool** that has a core/aqua entry → prefer `aqua:` or the bare registry name (signed,
  cross-platform, no compile).
- A **GitHub-release binary** with no registry entry → `ubi:owner/repo`.
- An **ecosystem package** (a formatter, linter) → the matching `npm:` / `pipx:` / `cargo:` backend so
  the version is pinned alongside everything else instead of installed globally out-of-band.
