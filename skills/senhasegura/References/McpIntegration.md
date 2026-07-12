# MCP Integration

The senhasegura MCP server lets Claude Code call PAM Core and DSM operations as tools. The runnable server is `Tools/SenhaseguraMcpServer.ts`.

## Configure Claude Code

Add to `~/.claude/claude_desktop_config.json` (Claude Desktop) or `.claude/settings.json` (Claude Code), pointing at the absolute path of the server:

```json
{
  "mcpServers": {
    "senhasegura": {
      "command": "bun",
      "args": [
        "run",
        "/absolute/path/to/skills/senhasegura/Tools/SenhaseguraMcpServer.ts"
      ],
      "env": {
        "SENHASEGURA_URL": "https://senhasegura.example.com",
        "SENHASEGURA_CLIENT_ID": "your-client-id",
        "SENHASEGURA_CLIENT_SECRET": "your-client-secret"
      }
    }
  }
}
```

PAI uses Bun by convention. If you must run with Node, install `tsx` and switch the command — but Bun is the standard.

## Available tools

### Credential management

| Tool | Description | Parameters |
|------|-------------|------------|
| `senhasegura_list_credentials` | List credentials visible to this authorization | — |
| `senhasegura_get_credential` | Get credential metadata | `id`: string |
| `senhasegura_get_password` | Retrieve password (auto-releases custody) | `credentialId`: string |

### SSH key management

| Tool | Description | Parameters |
|------|-------------|------------|
| `senhasegura_list_ssh_keys` | List all SSH keys | — |
| `senhasegura_get_ssh_key` | Get SSH key (includes private key) | `id`: string |
| `senhasegura_rotate_ssh_key` | Trigger key rotation | `id`: string |

### DevOps Secret Manager

| Tool | Description | Parameters |
|------|-------------|------------|
| `senhasegura_dsm_list_secrets` | List DSM secrets | `application?`: string |
| `senhasegura_dsm_get_secret` | Get a DSM secret | `identifier`: string |

## Usage in Claude Code

```
You: List all credentials in senhasegura
Claude: [calls senhasegura_list_credentials]
        Found 15 credentials:
        - db-admin-prod (admin@db.example.com)
        - api-service-account (svc_api@api.example.com)
        ...
```

```
You: Get the password for the production database credential
Claude: [calls senhasegura_list_credentials → finds db-admin-prod]
        [calls senhasegura_get_password with credentialId]
        The password for db-admin-prod has been retrieved.
        Custody released automatically.
```

```
You: What secrets are available for the payment-service application?
Claude: [calls senhasegura_dsm_list_secrets with application="payment-service"]
        Found 4 secrets:
        - stripe-api-keys (prod)
        - database-credentials (prod)
        - jwt-signing-key (prod)
        - encryption-keys (prod)
```

## Security considerations

- **Token caching.** Tokens cache in-process and refresh at expiry minus 60s — no 401 retry storms.
- **Custody.** `senhasegura_get_password` auto-releases custody in `finally`. If the release fails, the primary call still returns the secret; operators should monitor senhasegura's audit reports for orphaned custody.
- **Audit.** Every API call is logged in senhasegura's audit logs. Set a meaningful A2A application name so operations are traceable.
- **Least privilege.** Restrict the A2A authorization to the credentials/secrets the MCP user should reach. Don't share authorizations across humans and machine workloads.
- **IP restriction.** The IP senhasegura sees is the egress of the host running this MCP server (your laptop, a bastion, the dev container). Whitelist accordingly. (SKILL.md Gotcha #4.)

## Debugging

```bash
# Quick auth + list test
curl -s -X POST "$SENHASEGURA_URL/iso/oauth2/token" \
  -d "grant_type=client_credentials" \
  -d "client_id=$SENHASEGURA_CLIENT_ID" \
  -d "client_secret=$SENHASEGURA_CLIENT_SECRET"

curl -H "Authorization: Bearer $TOKEN" "$SENHASEGURA_URL/api/pam/credential"
```

If the MCP server fails to start, run it directly to see stderr:

```bash
SENHASEGURA_URL=... SENHASEGURA_CLIENT_ID=... SENHASEGURA_CLIENT_SECRET=... \
  bun run Tools/SenhaseguraMcpServer.ts
```

The server speaks stdio MCP — useful errors land on stderr and won't disturb the protocol on stdout.
