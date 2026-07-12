# Workflow: Setup A2A Application

Configure a new A2A application for API integration with OAuth 2.0 authentication.

## Prerequisites
- Senhasegura console access with admin privileges
- Target application/system identified
- Source IP range you'll call from (for IP restriction)

## Steps

### 1. Create A2A application

In the senhasegura console: **A2A → Applications → New**

- **Name:** `my-app-integration`
- **Authentication method:** OAuth 2.0
- **Status:** Enabled
- **Description:** Integration for production workloads
- Save.

### 2. Retrieve OAuth credentials

**A2A → Applications → my-app-integration → Authorization**

Copy and store:

- `client_id` — UUID format
- `client_secret` — long secret string

Store in a secure location (1Password, Vault, encrypted env file). Never commit.

### 3. Configure authorization rules

**A2A → Authorizations → New**

- **Application:** `my-app-integration`
- **Module:** `PAM Core` (or `DSM` for DevOps secrets)
- **Permission:** Read and Write
- **IP Restriction:** `10.0.0.0/8` (the actual source IP senhasegura sees — see SKILL.md Gotcha #4)
- **Credential filter:** `tag:production` (optional but recommended — least privilege)

**Best practice:** one A2A authorization per application. Don't share authorizations across services.

### 4. Test authentication

```bash
export SENHASEGURA_URL="https://senhasegura.example.com"
export SENHASEGURA_CLIENT_ID="..."
export SENHASEGURA_CLIENT_SECRET="..."

curl -s -X POST "$SENHASEGURA_URL/iso/oauth2/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=$SENHASEGURA_CLIENT_ID" \
  -d "client_secret=$SENHASEGURA_CLIENT_SECRET"
```

Expected response:

```json
{
  "access_token": "eyJhbGci...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

### 5. Verify API access

```bash
TOKEN=$(curl -s -X POST "$SENHASEGURA_URL/iso/oauth2/token" \
  -d "grant_type=client_credentials" \
  -d "client_id=$SENHASEGURA_CLIENT_ID" \
  -d "client_secret=$SENHASEGURA_CLIENT_SECRET" | jq -r '.access_token')

curl -H "Authorization: Bearer $TOKEN" "$SENHASEGURA_URL/api/pam/credential"
```

Expected: JSON list of credentials this authorization can see.

## Common failures

| Symptom | Likely cause |
|---------|--------------|
| `invalid_client` | Wrong client_id or client_secret — re-copy from console |
| `IP not allowed` | Source IP doesn't match restriction (Gotcha #4 — check egress NAT for Kubernetes) |
| Empty credentials list | Authorization filter too restrictive, or no credentials match the tag |
| `404` on `/iso/oauth2/token` | Note `/iso/`, not `/api/` (Gotcha #9) |

## Next workflows

- Add the credentials to a CI/CD pipeline → `Workflows/InjectCiCdSecrets.md`
- Sync them into Kubernetes via ESO → `Workflows/SyncKubernetesSecrets.md`
- Wire up to Claude Code via the MCP server → `References/McpIntegration.md`
