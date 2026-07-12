# Integrations

Where senhasegura plugs into the rest of your stack: language clients, CI/CD pipelines, and the MySafe end-user surface.

## TypeScript / Bun client (PAI standard)

Drop-in client at `References/TypescriptClient.ts`. Run with Bun:

```bash
bun run References/TypescriptClient.ts
```

Highlights:

- `authenticate()` caches the token and refreshes at expiry minus 60s
- `withPassword(credentialId, callback)` retrieves the password and **always** releases custody in `finally` — use this instead of raw `getPassword`
- Strongly typed `Credential`, `CredentialPassword`, and `ApiResponse<T>` shapes

```typescript
const client = new SenhaseguraClient({
  baseUrl: process.env.SENHASEGURA_URL!,
  clientId: process.env.SENHASEGURA_CLIENT_ID!,
  clientSecret: process.env.SENHASEGURA_CLIENT_SECRET!,
});

const credentials = await client.listCredentials();

await client.withPassword("123", async (password) => {
  // password is valid here
});
// Custody released automatically
```

## Python client

`References/PythonClient.py` — full `SenhaseguraClient` and `DSMClient`. Key pattern:

```python
client = SenhaseguraClient()  # reads SENHASEGURA_* env vars

with client.password_context("123") as password:
    # use password
    pass
# Custody released automatically
```

For broader Python guidance (including a discussion of the `senhasegura` PyPI package and OAuth 1.0 fallback), see `References/PythonSdk.md`.

## CI/CD pipelines

End-to-end workflow: `Workflows/InjectCiCdSecrets.md`.

Per-platform templates:

| Platform | File |
|----------|------|
| GitHub Actions | `References/GithubActionsExample.yaml` |
| Azure DevOps | `References/AzurePipelinesExample.yaml` |
| GitLab CI | `References/GitlabCiExample.yaml` |

The same shape repeats across all three:

1. Install DSM CLI in the runner
2. Export `SENHASEGURA_*` env vars from the platform's secret store
3. `dsm runb --tool-name <github|azure-devops|gitlab> ...` from a tmpdir
4. `source .runb.vars`
5. Use secrets
6. Cleanup `rm -f .runb.vars` in an always-run step

## MySafe

End-user vault for personal/team credentials, separate from machine A2A flows.

**Web access:** `https://senhasegura.example.com/mysafe`

Features:

- **Passwords** — store and share login credentials
- **Notes** — secure text notes
- **Files** — encrypted file storage
- **API Secrets** — API keys, tokens, client credentials

### Browser extension

Chrome — *Segura MySafe Extension*. Auto-fill, quick credential creation, vault search.

### Sharing

| Mode | Use case | Notes |
|------|----------|-------|
| Internal | Share with MySafe users / groups | Permission: view or edit |
| External (link) | Share with non-users | Set expiration, view limit, can revoke anytime |

External-link sharing is the right tool when you need to send a one-off password to someone outside the org. Don't paste credentials into chat.

## MCP server (Claude Code)

Opt-in: a runnable MCP server at `Tools/SenhaseguraMcpServer.ts` exposes core PAM operations as Claude Code tools.

See `References/McpIntegration.md` for the configuration and full tool catalog.

## SCIM provisioning

Senhasegura supports SCIM for user/group sync from an IdP (Azure AD, Okta, Google). Configure under **Settings → SCIM** in the console; the IdP-side configuration varies. Out of scope for this skill — see vendor docs.
