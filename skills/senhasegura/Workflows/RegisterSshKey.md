# Workflow: Register and Rotate SSH Keys

Register an SSH key pair in senhasegura, configure automatic rotation, and consume the key from a CI/CD or operations workflow.

## Prerequisites
- Senhasegura console access with PAM Core / SSH Keys permissions
- Target devices (the systems whose `authorized_keys` will be updated) reachable from senhasegura
- A2A OAuth 2.0 credentials if you'll fetch via API (`Workflows/SetupA2A.md`)

## Steps

### 1. Generate the SSH key pair (if you don't already have one)

```bash
ssh-keygen -t ed25519 -C "deploy@example.com" -f ~/.ssh/deploy_key
# Output:
#   ~/.ssh/deploy_key       (private)
#   ~/.ssh/deploy_key.pub   (public)
```

Prefer Ed25519 over RSA. Use a strong passphrase or none — the key will be stored encrypted in senhasegura either way.

### 2. Register in senhasegura

**Console:** PAM Core → Credentials → SSH Keys → New

- **Identifier:** `deploy-key-prod`
- **Username:** `deploy`
- **Device:** `*.prod.example.com` (host pattern)
- **Private key:** paste contents of `deploy_key`
- **Public key:** paste contents of `deploy_key.pub`
- **Passphrase:** if applicable

**Rotation settings:**

- **Enable automatic renewal:** Yes
- **Renewal period:** 90 days
- **Key type:** Ed25519

### 3. Configure target devices

**Console:** PAM Core → Credentials → SSH Keys → `deploy-key-prod` → Devices tab

Add each host that should receive the new public key on rotation. Ensure for each:

- Reachable from senhasegura on TCP/22 (or your chosen SSH port)
- SSH service running
- `authorized_keys` path correct (default `~deploy/.ssh/authorized_keys`)
- The current key is already trusted so senhasegura can SSH in to install the next one

### 4. Retrieve the key via API

```bash
TOKEN=$(curl -s -X POST "$SENHASEGURA_URL/iso/oauth2/token" \
  -d "grant_type=client_credentials" \
  -d "client_id=$SENHASEGURA_CLIENT_ID" \
  -d "client_secret=$SENHASEGURA_CLIENT_SECRET" | jq -r '.access_token')

# List SSH keys
curl -H "Authorization: Bearer $TOKEN" "$SENHASEGURA_URL/api/pam/sshkey"

# Get a specific key
curl -H "Authorization: Bearer $TOKEN" "$SENHASEGURA_URL/api/pam/sshkey/456"

# Use it
curl -s -H "Authorization: Bearer $TOKEN" \
  "$SENHASEGURA_URL/api/pam/sshkey/456" \
  | jq -r '.private_key' > /tmp/deploy_key

chmod 600 /tmp/deploy_key
ssh -i /tmp/deploy_key deploy@target.prod.example.com
rm -f /tmp/deploy_key   # clean up
```

### 5. Trigger rotation manually (if needed)

**Console:** SSH Keys → `deploy-key-prod` → Actions → Rotate.

**API:**

```bash
curl -X POST "$SENHASEGURA_URL/api/pam/sshkey/456/rotate" \
  -H "Authorization: Bearer $TOKEN"
```

On rotation senhasegura:

1. Generates a new key pair.
2. Connects to each target device with the **current** key and appends the new public key.
3. Stores the new private key.
4. Records the operation in audit logs.
5. After verification, removes the old key from the targets.

If step 2 fails on any device, the rotation is aborted — the existing key stays valid.

## Common failures

| Symptom | Cause |
|---------|-------|
| Rotation aborts on one host | Senhasegura can't SSH there with the current key — check network, sshd config, key trust |
| New key doesn't work post-rotation | Wrong `authorized_keys` path, or sshd has `AuthorizedKeysCommand` overriding the file |
| `Permission denied (publickey)` after retrieving via API | Forgot `chmod 600`, OR file owner mismatch in containers |

## Next workflows

- Embed retrieval in a deploy pipeline → `Workflows/InjectCiCdSecrets.md`
- Use the MCP server to expose key retrieval to Claude Code → `References/McpIntegration.md`
