---
name: senhasegura
description: Senhasegura PAM platform integration — A2A OAuth 2.0, PAM Core credentials, SSH key rotation, DSM CLI for CI/CD, External Secrets Operator (Kubernetes), MySafe, and a runnable MCP server. USE WHEN senhasegura, segura, A2A application, DSM CLI, runb, MySafe, ExternalSecret + senhasegura, OAuth client_credentials for PAM, credential custody release, /iso/coe/senha endpoint, SCIM provisioning. NOT FOR HashiCorp Vault, AWS Secrets Manager, Azure Key Vault, GCP Secret Manager, 1Password, or generic OAuth 2.0 flows (use those directly).
---

# Senhasegura

**Skill Type:** Library/API Reference (Type 1) + Data Fetching (Type 3).

Practical integration guide for the senhasegura (Segura) Privileged Access Management platform. Covers A2A OAuth 2.0 auth, PAM Core credential and SSH key APIs, DevOps Secret Manager (DSM) for CI/CD, External Secrets Operator for Kubernetes, MySafe, and an opt-in MCP server.

## Voice Notification (on invocation)

```bash
curl -s -X POST http://localhost:31337/notify \
  -H "Content-Type: application/json" \
  -d '{"message": "Running the Senhasegura skill"}' \
  > /dev/null 2>&1 &
```

## Workflow Routing

| Trigger | Workflow |
|---------|----------|
| "set up A2A", "create senhasegura application", first-time OAuth client | `Workflows/SetupA2A.md` |
| "sync secrets to Kubernetes", ESO + senhasegura DSM | `Workflows/SyncKubernetesSecrets.md` |
| "rotate password", schedule rotation, Executions module | `Workflows/RotatePasswords.md` |
| "fetch secrets in pipeline", DSM `runb` in CI/CD | `Workflows/InjectCiCdSecrets.md` |
| "register SSH key", manage SSH key rotation | `Workflows/RegisterSshKey.md` |

## Reference Routing

| Topic | File |
|-------|------|
| OAuth 2.0 flow, A2A application creation, token caching | `Authentication.md` |
| PAM Core endpoints — credentials, custody, SSH keys | `PamApi.md` |
| DSM CLI, runb, mapping.json, External Secrets Operator | `Dsm.md` |
| MySafe, Python/TypeScript clients, CI/CD pipeline templates | `Integrations.md` |
| Errors, debug mode, rate limits, common failure modes | `Troubleshooting.md` |
| MCP server (opt-in Claude Code integration) | `References/McpIntegration.md` + `Tools/SenhaseguraMcpServer.ts` |
| Legacy OAuth 1.0 reference | `References/OAuth1Legacy.md` |
| Python SDK reference (PAI standard is TypeScript+Bun) | `References/PythonSdk.md` |

## Gotchas

These are non-obvious senhasegura behaviors that bite users. Add new entries as they're discovered.

| # | Gotcha |
|---|--------|
| 1 | `GET /iso/coe/senha?credentialId=N` **auto-locks the credential into custody.** You MUST `DELETE /iso/pam/credential/custody/N` after, or the credential is held until manual release. Concurrent jobs deadlock on the second fetch. |
| 2 | OAuth 2.0 access token TTL is 3600s. Cache and refresh **at expiry minus 60s buffer**, not on 401 retry. 401 retry storms hammer the IDP and trigger rate limits. |
| 3 | `/iso/coe/senha` is the **legacy A2A v1 password retrieval path**; `/api/pam/credential/{id}` returns metadata only. The legacy path is current — do not refactor it away. |
| 4 | A2A authorization IP restriction is matched against the **HTTP source IP as seen by senhasegura** — for Kubernetes, that's the egress NAT, not the pod IP. Whitelist the cluster egress. ESO failures surface as a generic "could not get provider client". |
| 5 | DSM `runb` writes secrets to `.runb.vars` in the **current working directory**. If cwd is the repo root, it can be accidentally committed. Always run from a tmpdir or set `SENHASEGURA_SECRETS_FILE=/tmp/runb.$$.vars`. |
| 6 | External Secrets Operator provider key is `senhasegura` (lowercase) and module is `DSM` (uppercase). Mixed case = silent provider-not-found; ESO just fails to reconcile with no clear error. |
| 7 | `dsm runb --tool-name <X>` accepts `github`, `azure-devops`, `gitlab`, `linux`. Using `linux` outside Linux containers (Windows runners, unspecified) prevents masking of secret values in CI logs — secrets leak into log output. |
| 8 | The Python and TypeScript clients in `References/` do **not** auto-release custody on raw `getPassword`. Use the provided `withPassword(...)` / `password_context(...)` helpers, which wrap try/finally. |
| 9 | The token endpoint is `/iso/oauth2/token` — note `/iso/`, not `/api/`. Senhasegura's path scheme mixes `/iso/` (legacy/console) and `/api/` (newer REST) inconsistently. |
| 10 | Most enterprise installs use internal CAs. Reach for `ignoreSslCertificate: true` / `SENHASEGURA_INSECURE: true` only for local debugging. The proper path is mounting the CA bundle into ESO via the `ca` field. |

## Quick Reference

```bash
# 1. Get token (1h TTL)
TOKEN=$(curl -s -X POST "$SENHASEGURA_URL/iso/oauth2/token" \
  -d "grant_type=client_credentials" \
  -d "client_id=$SENHASEGURA_CLIENT_ID" \
  -d "client_secret=$SENHASEGURA_CLIENT_SECRET" | jq -r '.access_token')

# 2. List credentials
curl -H "Authorization: Bearer $TOKEN" "$SENHASEGURA_URL/api/pam/credential"

# 3. Get password (auto-locks custody — see Gotcha #1)
curl -H "Authorization: Bearer $TOKEN" \
  "$SENHASEGURA_URL/iso/coe/senha?credentialId=123"

# 4. Release custody (REQUIRED after step 3)
curl -X DELETE -H "Authorization: Bearer $TOKEN" \
  "$SENHASEGURA_URL/iso/pam/credential/custody/123"

# 5. DSM secret fetch via CLI
dsm runb --tool-name github \
  --application my-app --system production --environment prod
source .runb.vars && rm -f .runb.vars
```

## Environment Variables

```bash
SENHASEGURA_URL="https://senhasegura.example.com"
SENHASEGURA_CLIENT_ID="oauth2-client-id"
SENHASEGURA_CLIENT_SECRET="oauth2-client-secret"

# DSM CLI optionals
SENHASEGURA_CONFIG_FILE="/path/to/config.yaml"
SENHASEGURA_MAPPING_FILE="/path/to/mapping.json"
SENHASEGURA_SECRETS_FILE="/tmp/runb.$$.vars"   # don't write into repo root
SENHASEGURA_TIMEOUT="30"
# SENHASEGURA_INSECURE — local debug only; mount the CA bundle in prod
```

## Documentation Links

- [Official documentation](https://docs.senhasegura.io/docs)
- [A2A module](https://docs.senhasegura.io/docs/a2a)
- [DSM module](https://docs.senhasegura.io/docs/devops-secret-manager)
- [PAM Core API reference](https://docs.senhasegura.io/docs/api-a2a-pam-core)
- [DSM CLI on GitHub](https://github.com/senhasegura/dsmcli)
- [External Secrets Operator — senhasegura provider](https://external-secrets.io/latest/provider/senhasegura-dsm/)

## Execution Log

Append after every workflow run:

```bash
echo '{"ts":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","skill":"Senhasegura","workflow":"WORKFLOW_USED","input":"8_WORD_SUMMARY","status":"ok|error","duration_s":SECONDS}' \
  >> ~/.claude/PAI/MEMORY/SKILLS/execution.jsonl
```
