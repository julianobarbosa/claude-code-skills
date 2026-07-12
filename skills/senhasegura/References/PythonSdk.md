# Python SDK Reference

PAI's standard runtime is **Bun + TypeScript** — reach for `References/TypescriptClient.ts` first. This file exists because senhasegura's official examples and many enterprise integrations are still Python.

## Available clients

### `References/PythonClient.py` (recommended)

A self-contained client that mirrors `TypescriptClient.ts`. No PyPI dependency beyond `requests`.

```python
from PythonClient import SenhaseguraClient, DSMClient

client = SenhaseguraClient()  # reads SENHASEGURA_* env vars

# List credentials
for cred in client.list_credentials():
    print(f"{cred.identifier}: {cred.username}@{cred.hostname}")

# Get password with automatic custody release (use this, not get_password directly)
with client.password_context("123") as password:
    # Use password
    pass
# Custody released by __exit__

# DSM
dsm = DSMClient()
for secret in dsm.list_secrets(application="my-app"):
    print(secret["identifier"])
```

### `senhasegura` PyPI package (vendor library)

```bash
pip install senhasegura
```

```python
from senhasegura import A2A

# OAuth 2.0 (recommended)
client = A2A(
    base_url="https://senhasegura.example.com",
    client_id="your-client-id",
    client_secret="your-client-secret",
    auth_method="oauth2",
)

response = client.get("/iso/coe/senha", params={"credentialId": 123})
password = response.json()["response"]["credential"]["password"]

# IMPORTANT — release custody after use (Gotcha #1)
client.delete(f"/iso/pam/credential/custody/{credential_id}")
```

## Custody safety pattern (mandatory)

Senhasegura's `GET /iso/coe/senha` auto-locks the credential. Wrap retrieval and release in `try/finally`:

```python
try:
    password = client.get_password(credential_id)
    # Use password
finally:
    client.release_custody(credential_id)
```

`PythonClient.py` provides `password_context(...)` that does this for you. **Use it.** Raw `get_password` is for cases where you need fine-grained control.

## Error handling

```python
from senhasegura import A2A
from senhasegura.exceptions import AuthenticationError, APIError

try:
    client = A2A(
        base_url=os.environ["SENHASEGURA_URL"],
        client_id=os.environ["SENHASEGURA_CLIENT_ID"],
        client_secret=os.environ["SENHASEGURA_CLIENT_SECRET"],
    )
    response = client.get("/api/pam/credential/999")
    response.raise_for_status()

except AuthenticationError as e:
    print(f"Authentication failed: {e}")
except APIError as e:
    print(f"API error: {e.status_code} - {e.message}")
```

## OAuth 1.0 (legacy)

If you must, see `References/OAuth1Legacy.md`.

## When NOT to use Python here

- Inside PAI hooks, skills, or tools — use TypeScript with Bun.
- Inside the MCP server (`Tools/SenhaseguraMcpServer.ts`) — TypeScript is the runtime.

This file is here so a Python team or vendor sample can be referenced without polluting the main skill body.
