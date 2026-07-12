# mise.toml Templates (samples)

Copy the closest sample and delete what doesn't apply. Starting from a working shape beats writing
from a blank file — the structure encodes the house style (pinned versions, described tasks, redacted
secrets, section order).

---

## Minimal — pin a toolchain

The smallest useful config: reproducible tool versions, nothing else.

```toml
[tools]
node = '24'
python = '3.12'
```

---

## Standard project — tools + env + tasks

The everyday shape for an app repo.

```toml
[tools]
node = '24'
pnpm = '9'
"npm:prettier" = 'latest'   # dev CLI from a backend; latest is OK for lint tooling, not runtimes

[env]
NODE_ENV = 'development'
_.file = '.env'             # git-ignored dotenv for machine-local values
_.path = ['./node_modules/.bin']

[tasks.dev]
description = 'Run the app in watch mode'
run = 'pnpm dev'

[tasks.build]
description = 'Build the production bundle'
run = 'pnpm build'
sources = ['src/**/*', 'package.json', 'tsconfig.json']
outputs = ['dist/**/*']

[tasks.test]
description = 'Run the test suite'
run = 'pnpm test'

[tasks.lint]
description = 'Lint and format-check'
run = ['prettier --check .', 'pnpm lint']

[tasks.ci]
description = 'Everything CI runs'
depends = ['lint', 'build', 'test']
```

---

## Polyglot / infra repo — multiple backends

For a repo that mixes a runtime with CLI tools pulled from different ecosystems.

```toml
[tools]
python = '3.12'
terraform = '1.9'
"aqua:hashicorp/terraform-ls" = 'latest'
"ubi:BurntSushi/ripgrep" = 'latest'
"pipx:black" = 'latest'
"cargo:cargo-edit" = 'latest'

[env]
AWS_REGION = 'us-east-1'
_.file = { path = '.secrets.json', redact = true }   # values hidden from task output

[tasks."fmt:py"]
description = 'Format Python with black'
run = 'black .'

[tasks."tf:plan"]
description = 'Terraform plan for the dev workspace'
dir = 'infra'
run = 'terraform plan -out tfplan'

[settings]
jobs = 8   # this repo installs/builds a lot in parallel
```

---

## Global config sample

`~/.config/mise/config.toml` — personal defaults across every project. This is the one place `lts`/
`latest` is acceptable, because it's yours and not a shared contract.

```toml
[tools]
node = 'lts'
python = ['3.12', '3.11']   # first is the default; both installed

[settings]
idiomatic_version_file_enable_tools = ['node']   # allow reading .nvmrc for node
trusted_config_paths = ['~/code', '~/work']      # auto-trust your own trees
jobs = 8

[settings.status]
show_tools = false   # quiet the per-cd status line
show_env = false
```

---

## Task-heavy repo — mise as a `make`/`just` replacement

When the draw is the task runner more than version management.

```toml
[tools]
node = '24'

[tasks."db:migrate"]
description = 'Apply pending database migrations'
run = './scripts/migrate.sh'

[tasks."db:reset"]
description = 'Drop and recreate the local database'
confirm = 'This wipes the local DB. Continue?'   # prompts before running
run = './scripts/db-reset.sh'

[tasks.deploy]
description = 'Deploy to an environment'
usage = '''
arg "<environment>" {
  help "Target environment"
  choices "staging" "prod"
}
flag "--dry-run" help="Show what would happen without doing it"
'''
run = '''
#!/usr/bin/env bash
set -euo pipefail
echo "Deploying to ${usage_environment?}"
[ "${usage_dry_run:-false}" = "true" ] && { echo "(dry run)"; exit 0; }
./scripts/deploy.sh "${usage_environment?}"
'''
```

Run it: `mise run deploy prod --dry-run`.
