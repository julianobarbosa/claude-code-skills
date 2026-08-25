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
| GitHub releases | `github:` | `github:cli/cli` (`ubi:` is the deprecated spelling, removed in mise 2027.1.0) |
| npm | `npm:` | `npm:prettier` |
| PyPI (pipx) | `pipx:` | `pipx:black` |
| Cargo | `cargo:` | `cargo:cargo-edit` |
| Go modules | `go:` | `go:github.com/goreleaser/goreleaser` |
| asdf plugins | `asdf:` | `asdf:someplugin` |
| vfox plugins | `vfox:` | `vfox:someplugin` |

Usage is identical across backends:

```sh
mise use npm:prettier@latest
mise use github:BurntSushi/ripgrep
```

```toml
[tools]
node = '24'
"npm:prettier" = 'latest'
"github:BurntSushi/ripgrep" = 'latest'
"pipx:black" = 'latest'
```

`mise registry` shows the tool → backend mapping (e.g. what `ripgrep` resolves to by default).

### GitHub-release gotcha: the binary name is not the repo name

The `github:`/`ubi:` backend looks for an executable matching the **repo** name inside the release
archive. When they differ the install fails at the extract step with `could not find any files
matching [<repo>*] in the downloaded archive file` — download and asset-matching both succeeded, so
the debug log reads healthy right up to that line. Fix it with the `exe` tool option, not a
different version:

```sh
mise use -g "github:microsoft/go-sqlcmd[exe=sqlcmd]@1.10.0"   # archive ships sqlcmd, repo is go-sqlcmd
```

```toml
"github:microsoft/go-sqlcmd" = { version = "1.10.0", exe = "sqlcmd" }
```

Under `MISE_VERBOSE=1` the lines that name the real contents are `found tarball entry with path
'<name>'` — read those to pick the right `exe` value.

## One-off under a specific version

```sh
mise exec node@22 -- node -v     # `x` is the alias
mise x node@22 -- npm ci
```

## Which backend should I pick?

- A **language/runtime** (node, python, go, ruby, java) → core backend, bare name.
- A **CLI tool** that has a core/aqua entry → prefer `aqua:` or the bare registry name (signed,
  cross-platform, no compile).
- A **GitHub-release binary** with no registry entry → `github:owner/repo`.
- An **ecosystem package** (a formatter, linter) → the matching `npm:` / `pipx:` / `cargo:` backend so
  the version is pinned alongside everything else instead of installed globally out-of-band.
