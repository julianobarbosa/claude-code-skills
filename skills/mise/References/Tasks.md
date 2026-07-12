# Reference: Tasks

Tasks run inside the mise environment, so all `[tools]` and `[env]` are available. Define them inline
(TOML tasks) or as script files (file tasks).

## TOML tasks

```toml
[tasks.build]
description = 'Build the CLI'
run = 'cargo build'
alias = 'b'                 # `mise run b`

[tasks.test]
description = 'Run automated tests'
run = ['cargo test', './scripts/test-e2e.sh']   # list = run in series
dir = '{{cwd}}'             # working dir; default is project root

[tasks.lint]
description = 'Lint with clippy'
env = { RUST_BACKTRACE = '1' }   # task-scoped env
run = '''
#!/usr/bin/env bash
cargo clippy
'''

[tasks.clean]
depends = ['cleancache']   # run dependency first
run = 'cargo clean'

[tasks.cleancache]
run = 'rm -rf .cache'
hide = true                # hidden from `mise tasks`

[tasks.ci]
description = 'Run CI tasks'
depends = ['build', 'lint', 'test']   # a pure orchestrator

[tasks.release]
description = 'Cut a new release'
confirm = 'Are you sure?'  # prompt before running
file = 'scripts/release.sh' # external script instead of inline run
```

### Task properties

| Property | Meaning |
|----------|---------|
| `run` | Command string, multiline script, or list (list runs in series). |
| `depends` | Tasks that must run first. |
| `description` | Shown in `mise tasks`. House rule: always set it. |
| `alias` | Short name(s). |
| `dir` | Working directory (`{{cwd}}` = caller's dir). |
| `env` | Task-scoped env vars. |
| `hide` | Hide from listings. |
| `confirm` | Prompt string before executing. |
| `file` | External script to execute. |
| `sources` / `outputs` | Incremental-build fingerprinting. |
| `usage` | Argument/flag spec. |

### Namespaced tasks

Quote keys to use colons:

```toml
[tasks."test:unit"]
run = 'cargo test --lib'
```

Run a group by wildcard: `mise run 'test:*'`.

## Incremental tasks: sources & outputs

mise skips the task if no `source` is newer than the newest `output` — make-style caching without
make's footguns.

```toml
[tasks.build]
run = 'cargo build'
sources = ['Cargo.toml', 'src/**/*.rs']
outputs = ['target/debug/mycli']
```

## File tasks

Any executable script under `mise-tasks/` (also `.mise/tasks/`, `.config/mise/tasks/`) becomes a task
named after the file. Add metadata via comment directives:

```bash
#!/usr/bin/env bash
#MISE description="Deploy the app"
#MISE depends=["build"]
set -euo pipefail
./deploy.sh
```

Then `mise run deploy`.

## Arguments (usage spec)

Declare positional args and flags; access them as `usage_*` env vars.

```toml
[tasks.deploy]
description = 'Deploy application'
usage = '''
arg "<environment>" {
  help "Deployment environment"
  choices "dev" "staging" "prod"
}
flag "--region <region>" {
  help "Cloud region"
  default "us-east-1"
}
flag "--dry-run" help="Show what would be deployed"
'''
run = '''
#!/usr/bin/env bash
set -euo pipefail
echo "Deploying to ${usage_environment?} in ${usage_region?}"
[ "${usage_dry_run:-false}" = "true" ] && echo "(dry run)"
'''
```

```sh
mise run deploy prod --region us-west-2 --dry-run
```

## Running

```sh
mise tasks               # list tasks
mise run                 # pick interactively / run default
mise run test            # run one
mise run build test      # several
mise run 'test:*'        # a group
mise run test -- --nocapture   # args after -- go to the task command
mise watch test          # re-run on file changes (needs watchexec)
```

### Parallelism

Independent tasks run in parallel; `depends` ordering is respected. Control the degree with
`--jobs N`, the `jobs` setting, or `MISE_JOBS`. Default is **4**.
