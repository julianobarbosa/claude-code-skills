# Authentication

Senhasegura supports OAuth 2.0 (recommended), OAuth 1.0 (legacy — see `References/OAuth1Legacy.md`), and AWS Signature for AWS workloads.

## OAuth 2.0 (recommended)

### Token endpoint

`POST {SENHASEGURA_URL}/iso/oauth2/token` — note `/iso/`, not `/api/` (SKILL.md Gotcha #9).

### Request

```bash
curl -X POST "$SENHASEGURA_URL/iso/oauth2/token" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -d "client_id=$SENHASEGURA_CLIENT_ID" \
  -d "client_secret=$SENHASEGURA_CLIENT_SECRET"
```

### Response

```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIs...",
  "token_type": "Bearer",
  "expires_in": 3600
}
```

### Using the token

```bash
curl -H "Authorization: Bearer $TOKEN" \
     -H "Content-Type: application/json" \
     "$SENHASEGURA_URL/api/pam/credential"
```

### Token caching pattern (correct)

Cache the token in memory and refresh **at expiry minus 60 seconds**, not on 401. The TypeScript and Python clients in `References/` implement this; copy that pattern when writing your own.

```typescript
this.tokenExpiry = new Date(Date.now() + data.expires_in * 1000 - 60_000);
```

```python
self.token_expiry = datetime.now() + timedelta(seconds=data["expires_in"] - 60)
```

## A2A application creation

Walk through `Workflows/SetupA2A.md` for the console steps. Summary:

1. **A2A → Applications → New** — create the app, set OAuth 2.0, Enabled.
2. **A2A → Authorizations → New** — bind the app to a module (PAM Core, DSM, etc.) with permission, IP restriction, and optional credential filter.
3. Copy `client_id` and `client_secret` from the application's Authorization view.

**One A2A authorization per application.** Don't share credentials across services — least privilege and audit clarity both depend on it.

## IP restriction — what senhasegura actually sees

The IP restriction matches the source IP from the HTTP request as seen by senhasegura. In practice:

| Caller | What senhasegura sees |
|--------|------------------------|
| Bare bash on a VM | The VM's public/egress IP |
| Pod in Kubernetes | The cluster's egress NAT (NOT the pod IP) |
| GitHub Actions | The runner's egress (broad GitHub IP ranges) |
| Self-hosted runner / on-prem | Your egress firewall |

Whitelist the egress, not the source. Failures from this surface as "could not get provider client" in ESO logs and as `IP not allowed` in direct API calls.

## AWS Signature

Used when calling senhasegura from AWS workloads with IAM-based identity. Configure in the A2A authorization dialog. Most users should pick OAuth 2.0 unless they have a specific AWS-side requirement.

## OAuth 1.0 (legacy)

Still supported, no longer recommended for new integrations. See `References/OAuth1Legacy.md` if you must.
