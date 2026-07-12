# 1Password Python SDK Tools

Python CLI tools for managing 1Password Developer Environments using the official `onepassword-sdk` package. Drop-in replacement for the TypeScript/Bun tools with identical CLI interfaces.

## Prerequisites

- Python 3.9+
- [uv](https://docs.astral.sh/uv/) package manager
- `OP_SERVICE_ACCOUNT_TOKEN` environment variable set

## Setup

```bash
cd tools-python
uv sync
```

## CLI Tools

All tools accept the same arguments as their TypeScript counterparts.

### Create Environment

```bash
# Inline variables
uv run op-env-create my-app-dev Personal API_KEY=secret DB_HOST=localhost

# From .env file
uv run op-env-create my-app-prod Production --from-file .env.prod

# Combine file + inline (inline overrides)
uv run op-env-create azure-config Shared --from-file .env EXTRA=value
```

### List Environments

```bash
uv run op-env-list
uv run op-env-list --vault Personal
uv run op-env-list --json
```

### Show Environment

```bash
uv run op-env-show my-app-dev Personal
uv run op-env-show my-app-dev Personal --reveal
uv run op-env-show my-app-dev Personal --json
uv run op-env-show my-app-dev Personal --keys
```

### Update Environment

```bash
uv run op-env-update my-app-dev Personal API_KEY=new-key
uv run op-env-update my-app-dev Personal --from-file .env.local
uv run op-env-update my-app-dev Personal --remove OLD_KEY,DEPRECATED
```

### Export Environment

```bash
uv run op-env-export my-app-dev Personal > .env
uv run op-env-export my-app-dev Personal --format docker > .env
uv run op-env-export my-app-dev Personal --format op-refs > .env.tpl
uv run op-env-export my-app-dev Personal --format json
uv run op-env-export azure Shared --prefix AZURE_ > .env
```

### Delete Environment

```bash
uv run op-env-delete my-app-dev Personal
uv run op-env-delete old-config Shared --force
uv run op-env-delete deprecated Production --archive
```

## SecretsManager (for application integration)

```python
from op_env.secrets_manager import SecretsManager

async def main():
    sm = await SecretsManager.create()

    # Single secret (with caching)
    api_key = await sm.get("op://Production/API/key")

    # Batch resolve
    secrets = await sm.get_many([
        "op://Production/DB/password",
        "op://Production/DB/host",
    ])

    # Load all vars from an environment item
    env = await sm.resolve_environment("my-app-prod", "Production")
```

## SDK vs CLI

| Feature | Python SDK (`tools-python/`) | TypeScript CLI (`tools/`) |
|---------|-----|-----|
| Runtime | Python 3.9+ / uv | Bun |
| Auth | Service account token | op CLI signin or token |
| Performance | Native SDK (no subprocess) | Shells out to `op` CLI |
| Tag filtering | Falls back to CLI | Native CLI support |
| Best for | Python apps, FastAPI/Django | Scripts, CI/CD, shell |

## Development

```bash
# Lint
uv run ruff check src/

# Type check
uv run mypy src/

# Run tests
uv run pytest
```
