# Reference: Environments (env vars)

mise sets env vars per directory — a built-in `direnv`. Vars apply when you `cd` in (with
`mise activate`) or via `mise exec`/shims.

## Basic variables

```toml
[env]
NODE_ENV = 'development'
DATABASE_URL = 'postgres://localhost/dev'
```

Values can be templates:

```toml
[env]
LD_LIBRARY_PATH = "/some/path:{{env.LD_LIBRARY_PATH}}"
PROJECT_ROOT = "{{config_root}}"
```

## The special `_` directives

Keys under `_` are directives, not literal variables.

### `_.file` — load a dotenv file

```toml
[env]
_.file = '.env'                 # .env / .json / .yaml / .toml supported
```

Multiple, mixed relative/absolute, redacted, or loaded **after** tool env with `tools = true`:

```toml
[env]
_.file = [
    '.env.json',
    '/home/bob/.env',
    { path = '.secrets.yaml', redact = true },
    { path = '.env', tools = true },
]
```

### `_.source` — source a shell script

Runs a bash script and captures exported vars (sourced; shebang ignored):

```toml
[env]
_.source = './script.sh'
```

```toml
[env]
_.source = [
    './scripts/base.sh',
    { path = '.secrets.sh', redact = true },
    { path = 'my/env.sh', tools = true },
]
```

### `_.path` — prepend to PATH

```toml
[env]
_.path = ['./node_modules/.bin', '{{config_root}}/bin']
```

### `[[env]]` — multiple env blocks

TOML forbids duplicate keys, so to use a `_` directive more than once, use an array of tables:

```toml
[[env]]
_.source = './script_1.sh'
[[env]]
_.source = './script_2.sh'
```

## Secrets & redaction

Keep sensitive values out of task output/logs.

Per-variable or per-file:

```toml
[env]
SECRET = { value = 'my_secret', redact = true }
_.file = { path = '.env.json', redact = true }
```

Globally by pattern (top-level `redactions`, not under `[env]`):

```toml
redactions = ['SECRET_*', '*_TOKEN', 'PASSWORD']

[env]
SECRET_KEY = 'sensitive_value'
API_TOKEN = 'token_123'
```

**House rule:** never inline a real secret in a committed `mise.toml`. Load it from a git-ignored
file via `_.file`, and redact. mise also supports encrypted secrets (sops/age) via `_.file` on an
appropriately-typed file — see upstream "Secrets" docs.

## Inspecting

```sh
mise env               # print the env mise would export (sh format)
mise env -s fish       # fish syntax
mise set FOO=bar       # write a var into [env]
mise set               # list managed vars
mise unset FOO         # remove one
```

## vs direnv

Both set per-directory env. mise keeps it in the same `mise.toml` as tools/tasks, needs no separate
`.envrc`, and applies via activation or shims. If you already use direnv, mise has a `direnv`
integration so both can coexist during a migration.
