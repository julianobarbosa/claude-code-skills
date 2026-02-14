# 1Password Python SDK Reference

## Overview

The [onepassword-sdk](https://pypi.org/project/onepassword-sdk/) Python package provides native SDK access to 1Password without shelling out to the `op` CLI. It offers async operations for secret resolution, item CRUD, and vault management.

## System Requirements

- **Python:** 3.9+
- **libssl:** 3.x (OpenSSL 3)
- **glibc:** 2.32+ (Linux)
- **macOS:** 12+ (Monterey)

## Installation

```bash
# With uv (recommended)
uv add onepassword-sdk

# With pip
pip install onepassword-sdk
```

## Authentication

### Service Account Token (recommended for automation)

```python
import os
from onepassword import Client

client = await Client.authenticate(
    auth=os.environ["OP_SERVICE_ACCOUNT_TOKEN"],
    integration_name="my-app",
    integration_version="1.0.0",
)
```

### Environment Variable

Set `OP_SERVICE_ACCOUNT_TOKEN` in your environment:

```bash
export OP_SERVICE_ACCOUNT_TOKEN="ops_..."
```

## API Reference

### client.secrets

Resolve secret references without fetching full items.

```python
# Single secret
value = await client.secrets.resolve("op://Vault/Item/Field")

# Batch resolve (more efficient for multiple secrets)
values = await client.secrets.resolve_all([
    "op://Vault/Item/Field1",
    "op://Vault/Item/Field2",
])
# Returns list of strings in same order as input
```

### client.items

Full CRUD operations on 1Password items.

```python
# List items in a vault
items = await client.items.list_all(vault_id)
async for item in items:
    print(item.title, item.id)

# Get a specific item
item = await client.items.get(vault_id, item_id)

# Create an item
from onepassword.types import (
    ItemCategory, ItemCreateParams, ItemField, ItemFieldType, ItemSection,
)

params = ItemCreateParams(
    title="my-environment",
    category=ItemCategory.APICREDENTIALS,
    vault_id=vault_id,
    tags=["environment"],
    sections=[ItemSection(id="variables", title="variables")],
    fields=[
        ItemField(
            id="API_KEY",
            title="API_KEY",
            value="secret-value",
            field_type=ItemFieldType.CONCEALED,
            section_id="variables",
        ),
    ],
)
created = await client.items.create(params)

# Update an item (get, modify, put)
item = await client.items.get(vault_id, item_id)
# ... modify item fields ...
await client.items.put(vault_id, item)

# Delete an item
await client.items.delete(vault_id, item_id)

# Archive an item
await client.items.archive(vault_id, item_id)
```

### client.vaults

```python
# List all accessible vaults
vaults = await client.vaults.list_all()
async for vault in vaults:
    print(vault.title, vault.id)
```

## Item Creation Patterns

### Environment Item (API Credential with variables section)

This is the pattern used by the `op-env-*` tools:

```python
from onepassword.types import (
    ItemCategory, ItemCreateParams, ItemField, ItemFieldType, ItemSection,
)

variables = {"DB_HOST": "localhost", "DB_PORT": "5432", "API_KEY": "secret"}

params = ItemCreateParams(
    title="my-app-dev",
    category=ItemCategory.APICREDENTIALS,
    vault_id=vault_id,
    tags=["environment"],
    sections=[ItemSection(id="variables", title="variables")],
    fields=[
        ItemField(
            id=key,
            title=key,
            value=value,
            field_type=ItemFieldType.CONCEALED,
            section_id="variables",
        )
        for key, value in variables.items()
    ],
)

created = await client.items.create(params)
```

### Field Types

| SDK Type | CLI Equivalent | Use Case |
|----------|---------------|----------|
| `ItemFieldType.CONCEALED` | `[concealed]` | Secrets, passwords, API keys |
| `ItemFieldType.TEXT` | `[text]` | Non-sensitive values |
| `ItemFieldType.URL` | `[url]` | URLs |
| `ItemFieldType.EMAIL` | `[email]` | Email addresses |

## CLI-to-SDK Migration

| CLI Command | SDK Equivalent |
|-------------|---------------|
| `op item list --vault V` | `client.items.list_all(vault_id)` |
| `op item get ITEM --vault V` | `client.items.get(vault_id, item_id)` |
| `op item create ...` | `client.items.create(vault_id, item)` |
| `op item edit ITEM ...` | `client.items.get()` → modify → `client.items.put()` |
| `op item delete ITEM` | `client.items.delete(vault_id, item_id)` |
| `op item delete ITEM --archive` | `client.items.archive(vault_id, item_id)` |
| `op read "op://V/I/F"` | `client.secrets.resolve("op://V/I/F")` |
| `op vault list` | `client.vaults.list_all()` |
| `op item list --tags TAG` | No SDK equivalent (use CLI subprocess) |

## Key Differences from CLI

1. **Vault IDs required** — SDK uses vault IDs, not names. Use `resolve_vault_id()` helper.
2. **No tag filtering** — `items.list_all()` doesn't support tag filters. Use CLI subprocess fallback.
3. **No get-by-title** — Must iterate items to find by title. Use `find_item_by_title()` helper.
4. **Async throughout** — All SDK operations are async. Wrap with `asyncio.run()` for CLI tools.
5. **Item update is get+modify+put** — No atomic field edit; fetch the full item, modify, then save.

## Error Handling

```python
from onepassword import Client

try:
    client = await Client.authenticate(auth=token, ...)
except Exception as e:
    # Invalid token or network error
    print(f"Authentication failed: {e}")

try:
    value = await client.secrets.resolve("op://Vault/Item/Field")
except Exception as e:
    # Item not found, permission denied, etc.
    print(f"Secret resolution failed: {e}")
```

## SecretsManager Usage

The `SecretsManager` class provides a higher-level abstraction with caching:

```python
from op_env.secrets_manager import SecretsManager

async def main():
    sm = await SecretsManager.create()

    # Single secret (cached after first call)
    api_key = await sm.get("op://Production/API/key")

    # Batch resolve
    secrets = await sm.get_many([
        "op://Production/DB/password",
        "op://Production/DB/host",
    ])

    # Load all vars from a 1Password environment
    env = await sm.resolve_environment("my-app-prod", "Production")
    # Returns: {"DB_HOST": "...", "API_KEY": "...", ...}

    # List vaults
    vaults = await sm.list_vaults()

    # Clear cache when needed
    sm.clear_cache()
```

### FastAPI Integration

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from op_env.secrets_manager import SecretsManager

sm: SecretsManager

@asynccontextmanager
async def lifespan(app: FastAPI):
    global sm
    sm = await SecretsManager.create()
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/health")
async def health():
    db_url = await sm.get("op://Production/DB/url")
    return {"status": "ok"}
```

### Django Integration

```python
# settings.py
import asyncio
from op_env.secrets_manager import SecretsManager

def _load_secrets():
    async def _resolve():
        sm = await SecretsManager.create()
        return await sm.resolve_environment("my-app-prod", "Production")
    return asyncio.run(_resolve())

_secrets = _load_secrets()

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": _secrets["DB_HOST"],
        "PASSWORD": _secrets["DB_PASSWORD"],
    }
}
```
