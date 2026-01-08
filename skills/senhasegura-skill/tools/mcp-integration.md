# Senhasegura MCP Tools Integration

Guide for integrating senhasegura with Claude Code using MCP (Model Context Protocol) tools.

---

## MCP Server Configuration

### Option 1: Custom MCP Server (TypeScript)

Create a senhasegura MCP server to expose PAM operations as tools:

```typescript
// senhasegura-mcp-server.ts
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

interface SenhaseguraConfig {
  baseUrl: string;
  clientId: string;
  clientSecret: string;
}

class SenhaseguraClient {
  private config: SenhaseguraConfig;
  private accessToken: string | null = null;
  private tokenExpiry: Date | null = null;

  constructor(config: SenhaseguraConfig) {
    this.config = config;
  }

  async authenticate(): Promise<void> {
    const response = await fetch(`${this.config.baseUrl}/iso/oauth2/token`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        grant_type: "client_credentials",
        client_id: this.config.clientId,
        client_secret: this.config.clientSecret,
      }),
    });
    const data = await response.json();
    this.accessToken = data.access_token;
    this.tokenExpiry = new Date(Date.now() + data.expires_in * 1000 - 60000);
  }

  private async ensureAuth(): Promise<void> {
    if (!this.accessToken || !this.tokenExpiry || this.tokenExpiry < new Date()) {
      await this.authenticate();
    }
  }

  async request(method: string, endpoint: string, body?: unknown): Promise<unknown> {
    await this.ensureAuth();
    const response = await fetch(`${this.config.baseUrl}${endpoint}`, {
      method,
      headers: {
        Authorization: `Bearer ${this.accessToken}`,
        "Content-Type": "application/json",
      },
      body: body ? JSON.stringify(body) : undefined,
    });
    return response.json();
  }
}

const server = new Server(
  { name: "senhasegura-mcp", version: "1.0.0" },
  { capabilities: { tools: {} } }
);

const client = new SenhaseguraClient({
  baseUrl: process.env.SENHASEGURA_URL!,
  clientId: process.env.SENHASEGURA_CLIENT_ID!,
  clientSecret: process.env.SENHASEGURA_CLIENT_SECRET!,
});

// Define available tools
server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: [
    {
      name: "senhasegura_list_credentials",
      description: "List all credentials from senhasegura PAM",
      inputSchema: {
        type: "object",
        properties: {
          filter: {
            type: "string",
            description: "Optional filter for credential identifier",
          },
        },
      },
    },
    {
      name: "senhasegura_get_password",
      description: "Get password for a specific credential (use with caution)",
      inputSchema: {
        type: "object",
        properties: {
          credentialId: {
            type: "string",
            description: "The credential ID",
          },
        },
        required: ["credentialId"],
      },
    },
    {
      name: "senhasegura_list_ssh_keys",
      description: "List all SSH keys registered in senhasegura",
      inputSchema: {
        type: "object",
        properties: {},
      },
    },
    {
      name: "senhasegura_dsm_list_secrets",
      description: "List secrets from DevOps Secret Manager",
      inputSchema: {
        type: "object",
        properties: {
          application: {
            type: "string",
            description: "Filter by application name",
          },
        },
      },
    },
    {
      name: "senhasegura_dsm_get_secret",
      description: "Get a specific secret from DSM",
      inputSchema: {
        type: "object",
        properties: {
          identifier: {
            type: "string",
            description: "Secret identifier",
          },
        },
        required: ["identifier"],
      },
    },
  ],
}));

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  switch (name) {
    case "senhasegura_list_credentials": {
      const data = await client.request("GET", "/api/pam/credential");
      return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
    }

    case "senhasegura_get_password": {
      const credentialId = (args as { credentialId: string }).credentialId;
      const data = await client.request(
        "GET",
        `/iso/coe/senha?credentialId=${credentialId}`
      );
      // Release custody immediately
      await client.request("DELETE", `/iso/pam/credential/custody/${credentialId}`);
      return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
    }

    case "senhasegura_list_ssh_keys": {
      const data = await client.request("GET", "/api/pam/sshkey");
      return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
    }

    case "senhasegura_dsm_list_secrets": {
      const application = (args as { application?: string }).application;
      const endpoint = application
        ? `/api/dsm/secret?application=${application}`
        : "/api/dsm/secret";
      const data = await client.request("GET", endpoint);
      return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
    }

    case "senhasegura_dsm_get_secret": {
      const identifier = (args as { identifier: string }).identifier;
      const data = await client.request("GET", `/api/dsm/secret/${identifier}`);
      return { content: [{ type: "text", text: JSON.stringify(data, null, 2) }] };
    }

    default:
      throw new Error(`Unknown tool: ${name}`);
  }
});

// Start server
const transport = new StdioServerTransport();
await server.connect(transport);
```

### Option 2: MCP Configuration in Claude Code

Add to `~/.claude/claude_desktop_config.json` or `.claude/settings.json`:

```json
{
  "mcpServers": {
    "senhasegura": {
      "command": "bun",
      "args": ["run", "/path/to/senhasegura-mcp-server.ts"],
      "env": {
        "SENHASEGURA_URL": "https://senhasegura.example.com",
        "SENHASEGURA_CLIENT_ID": "your-client-id",
        "SENHASEGURA_CLIENT_SECRET": "your-client-secret"
      }
    }
  }
}
```

---

## Available MCP Tools

### Credential Management

| Tool | Description | Parameters |
|------|-------------|------------|
| `senhasegura_list_credentials` | List all PAM credentials | `filter?`: string |
| `senhasegura_get_credential` | Get credential details | `id`: string |
| `senhasegura_get_password` | Retrieve credential password | `credentialId`: string |
| `senhasegura_release_custody` | Release credential custody | `credentialId`: string |

### SSH Key Management

| Tool | Description | Parameters |
|------|-------------|------------|
| `senhasegura_list_ssh_keys` | List all SSH keys | - |
| `senhasegura_get_ssh_key` | Get SSH key details | `id`: string |
| `senhasegura_rotate_ssh_key` | Trigger key rotation | `id`: string |

### DevOps Secret Manager

| Tool | Description | Parameters |
|------|-------------|------------|
| `senhasegura_dsm_list_secrets` | List DSM secrets | `application?`: string |
| `senhasegura_dsm_get_secret` | Get secret by identifier | `identifier`: string |
| `senhasegura_dsm_create_secret` | Create new secret | `identifier`, `data`, `application`, `system`, `environment` |
| `senhasegura_dsm_update_secret` | Update existing secret | `identifier`, `data` |

---

## Usage Examples in Claude Code

### List Credentials

```
User: List all credentials in senhasegura

Claude: [Uses senhasegura_list_credentials tool]

Found 15 credentials:
- db-admin-prod (admin@db.example.com)
- api-service-account (svc_api@api.example.com)
...
```

### Get Database Password

```
User: Get the password for the production database credential

Claude: [Uses senhasegura_list_credentials to find credential]
[Uses senhasegura_get_password with credentialId]

The password for db-admin-prod has been retrieved.
Note: Custody has been automatically released.
```

### DSM Secret Lookup

```
User: What secrets are available for the payment-service application?

Claude: [Uses senhasegura_dsm_list_secrets with application="payment-service"]

Found 4 secrets for payment-service:
- stripe-api-keys (prod)
- database-credentials (prod)
- jwt-signing-key (prod)
- encryption-keys (prod)
```

---

## Security Considerations

### Token Management
- Access tokens are cached and refreshed automatically
- Tokens expire after 1 hour by default
- New token is requested before expiry

### Credential Custody
- When password is retrieved, credential goes into custody
- Always release custody after use
- MCP tools automatically release custody

### Audit Logging
- All API calls are logged in senhasegura
- Include application identifier for traceability
- Review access logs regularly

### Best Practices

1. **Least Privilege**: Only request credentials you need
2. **Short-lived Access**: Release custody immediately
3. **Audit Trail**: All operations are logged
4. **IP Restrictions**: Configure A2A with IP whitelist
5. **Rotate Regularly**: Enable automatic rotation

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid/expired token | Check credentials, request new token |
| `403 Forbidden` | Insufficient permissions | Verify A2A authorization |
| `Connection refused` | Network/firewall | Check connectivity to senhasegura |
| `SSL certificate error` | Invalid cert | Configure proper CA or skip verify |

### Debug Mode

Enable debug logging:

```bash
export DEBUG=senhasegura:*
bun run senhasegura-mcp-server.ts
```

### Test Connection

```bash
# Test OAuth token
curl -X POST "$SENHASEGURA_URL/iso/oauth2/token" \
  -d "grant_type=client_credentials" \
  -d "client_id=$CLIENT_ID" \
  -d "client_secret=$CLIENT_SECRET"

# Test API access
curl -H "Authorization: Bearer $TOKEN" "$SENHASEGURA_URL/api/pam/credential"
```
