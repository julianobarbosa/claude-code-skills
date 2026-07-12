# PAM Core API

Endpoints for credentials, password retrieval, custody management, and SSH keys.

## Credentials

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/api/pam/credential` | List all credentials this authorization can see |
| `GET` | `/api/pam/credential/{id}` | Get credential metadata (no password) |
| `POST` | `/api/pam/credential` | Create a credential |
| `PUT` | `/api/pam/credential/{id}` | Update a credential |
| `DELETE` | `/api/pam/credential/{id}` | Disable a credential |
| `GET` | `/iso/coe/senha?credentialId={id}` | **Retrieve password (LEGACY path, current use)** — auto-locks custody |
| `DELETE` | `/iso/pam/credential/custody/{id}` | Release custody after password retrieval |
| `POST` | `/api/pam/credential/{id}/rotate` | Trigger immediate rotation |

### List credentials

```bash
curl -H "Authorization: Bearer $TOKEN" "$SENHASEGURA_URL/api/pam/credential"
```

```json
{
  "response": {
    "status": 200,
    "credentials": [
      {
        "id": "123",
        "identifier": "db-admin-prod",
        "username": "admin",
        "hostname": "db.example.com",
        "ip": "10.0.1.50",
        "type": "Local User"
      }
    ]
  }
}
```

### Retrieve password (custody lifecycle)

The two-step lifecycle is mandatory:

```bash
# 1. Fetch — auto-locks the credential into custody (SKILL.md Gotcha #1)
curl -H "Authorization: Bearer $TOKEN" \
  "$SENHASEGURA_URL/iso/coe/senha?credentialId=123"

# 2. Release custody — REQUIRED, even on error
curl -X DELETE -H "Authorization: Bearer $TOKEN" \
  "$SENHASEGURA_URL/iso/pam/credential/custody/123"
```

**Always wrap retrieval + release in try/finally** in any client. The TypeScript and Python clients in `References/` provide `withPassword(...)` and `password_context(...)` helpers for this. Use them. Don't roll your own without the `finally` block (Gotcha #8).

### Create credential

```bash
curl -X POST "$SENHASEGURA_URL/api/pam/credential" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "new-service-account",
    "username": "svc_app",
    "password": "InitialP@ss123",
    "hostname": "app-server.example.com",
    "ip": "10.0.2.100",
    "type": "Local User",
    "additional_info": "Service account for app",
    "tags": ["production", "critical"]
  }'
```

After creation, prefer enabling automatic rotation immediately so the bootstrap password isn't long-lived.

## SSH Keys

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/api/pam/sshkey` | List all SSH keys |
| `GET` | `/api/pam/sshkey/{id}` | Get key (private key included) |
| `POST` | `/api/pam/sshkey` | Register a new SSH key |
| `PUT` | `/api/pam/sshkey/{id}` | Update key metadata |
| `POST` | `/api/pam/sshkey/{id}/rotate` | Trigger key rotation |

See `Workflows/RegisterSshKey.md` for the end-to-end flow.

### Register key

```bash
curl -X POST "$SENHASEGURA_URL/api/pam/sshkey" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "identifier": "deploy-key-prod",
    "username": "deploy",
    "hostname": "*.prod.example.com",
    "public_key": "ssh-ed25519 AAAAC3Nza...",
    "private_key": "-----BEGIN OPENSSH PRIVATE KEY-----...",
    "passphrase": "optional-passphrase",
    "auto_rotate": true,
    "rotation_days": 90
  }'
```

### Trigger rotation

```bash
curl -X POST "$SENHASEGURA_URL/api/pam/sshkey/456/rotate" \
  -H "Authorization: Bearer $TOKEN"
```

## Response codes

| Code | Meaning | Action |
|------|---------|--------|
| `200` | Success | Process the response |
| `400` | Bad request | Check JSON shape and required fields |
| `401` | Unauthorized | Token expired or invalid — re-authenticate |
| `403` | Forbidden | Authorization doesn't grant access — check A2A permissions and credential filter |
| `404` | Not found | Wrong ID, or credential not visible to this authorization |
| `429` | Rate limited | Implement exponential backoff with jitter |
| `5xx` | Server error | Retry with backoff; persistent → contact senhasegura support |
