# OAuth 1.0 (Legacy)

> **Use OAuth 2.0 for any new integration.** OAuth 1.0 remains supported for backward compatibility with older A2A applications. This document exists so you can keep an existing OAuth 1.0 path running while migrating.

## When you'll see OAuth 1.0

- A2A application created before OAuth 2.0 was the default
- Vendor integrations that haven't been updated
- On-prem systems with strict change-control where rotating to OAuth 2.0 hasn't been approved

## Credentials

OAuth 1.0 uses four secrets per client:

- `consumer_key`
- `consumer_secret`
- `token_key`
- `token_secret`

All four come from **A2A → Applications → `<app>` → Authorization** (the same screen as OAuth 2.0, but the app must be configured with `Authentication method: OAuth 1.0`).

## Python example

```python
from senhasegura import A2A

client = A2A(
    base_url="https://senhasegura.example.com",
    consumer_key="your-consumer-key",
    consumer_secret="your-consumer-secret",
    token_key="your-token-key",
    token_secret="your-token-secret",
    auth_method="oauth1",
)

response = client.get("/iso/coe/senha", params={"credentialId": 123})
```

## Migration to OAuth 2.0

1. Create a **new** A2A application configured for OAuth 2.0 — don't try to flip the existing one.
2. Authorize the new application against the same modules and credentials as the old one (or a tighter subset — migration is a good time to scope down).
3. Update one consumer at a time to point at the new `client_id` / `client_secret`.
4. Once all consumers are migrated, disable the old OAuth 1.0 application and remove its authorizations.

Don't run both side-by-side longer than a release cycle — each authorization is a credential surface.

## Security notes

- The four-token shape doesn't expire by itself; rotate it on the same cadence as your OAuth 2.0 secrets.
- Audit logs do distinguish OAuth 1.0 vs OAuth 2.0 traffic — useful when verifying migrations.
- HMAC signing in OAuth 1.0 means clock skew matters: keep client clocks within ~5 minutes of the senhasegura server.
