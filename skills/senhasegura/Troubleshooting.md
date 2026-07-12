# Troubleshooting

Failure modes you'll hit, mapped to causes and fixes. The Gotchas in `SKILL.md` cover the most common ones — this file expands on them and adds debug procedures.

## Authentication errors

| Error | Cause | Fix |
|-------|-------|-----|
| `401 Unauthorized` | Token expired or invalid | Request a new token; verify token caching uses `expires_in − 60s` (Gotcha #2) |
| `403 Forbidden` | Authorization missing or filter excludes the resource | Check **A2A → Authorizations** in the console |
| `invalid_client` | Wrong `client_id` / `client_secret` | Re-copy from console; whitespace in env vars is a frequent cause |
| `IP not allowed` | Source IP doesn't match the authorization restriction (Gotcha #4) | Whitelist the actual egress IP — for K8s, that's the cluster NAT, not the pod |
| `404` on `/iso/oauth2/token` | Wrong path scheme (Gotcha #9) | Path is `/iso/oauth2/token`, not `/api/oauth2/token` |

## DSM CLI issues

### Debug mode

```bash
dsm runb --debug \
  --application myapp \
  --system prod \
  --environment prod
```

### Common fixes

| Symptom | Fix |
|---------|-----|
| Config file not found | `export SENHASEGURA_CONFIG_FILE=/absolute/path/to/config.yaml` |
| SSL certificate errors (corporate CA) | Mount the CA bundle into the runner; only set `SENHASEGURA_INSECURE: true` for local debugging (Gotcha #10) |
| Permission denied on config | `chmod 600 ~/.senhasegura/config.yaml` |
| `.runb.vars` accidentally committed | Run from a tmpdir or set `SENHASEGURA_SECRETS_FILE=/tmp/runb.$$.vars` (Gotcha #5); rotate any exposed secrets |
| Secrets visible in CI log output | Wrong `--tool-name` for the runner (Gotcha #7) |

## External Secrets Operator

```bash
# SecretStore status
kubectl describe secretstore senhasegura-dsm

# ExternalSecret status
kubectl describe externalsecret database-credentials

# ESO logs
kubectl logs -n external-secrets -l app.kubernetes.io/name=external-secrets
```

| ESO log message | Likely cause |
|-----------------|--------------|
| `could not get provider client` | Auth secret missing/wrong, OR cluster egress IP not in A2A IP whitelist (Gotcha #4) |
| `provider not found` | Casing wrong — `senhasegura` lowercase, `DSM` uppercase (Gotcha #6) |
| `could not find secret <X>` | `remoteRef.key` doesn't match a DSM secret identifier |
| `refresh failed` | Network/firewall to senhasegura, OR token endpoint unreachable |
| TLS verify error | Internal CA not trusted by the ESO pod — mount it via `ca` field |

## API response codes

| Code | Meaning | Action |
|------|---------|--------|
| `200` | Success | Process the response |
| `400` | Bad request | Validate JSON shape and required fields |
| `401` | Unauthorized | Re-authenticate; check token caching |
| `403` | Forbidden | Check A2A authorization permissions and credential filter |
| `404` | Not found | Verify resource ID; the authorization may not see it |
| `429` | Rate limited | Implement exponential backoff with jitter (see below) |
| `5xx` | Server error | Retry with backoff; persistent → contact senhasegura support |

## Rate limits

Senhasegura applies rate limits per A2A authorization. Limits are not published as a fixed number — they vary by deployment and license. Practical guidance:

- For batch enumerations (e.g. listing all credentials), **paginate** and add a 50–200 ms sleep between pages.
- On `429`, sleep `min(60, 2^attempt + random(0, 1))` seconds and retry up to 5 times.
- Token requests should be cached and reused across the whole job — every `dsm runb` invocation in a long pipeline burns one token call.
- For ESO, `refreshInterval: 1h` is typical; **do not** drop below 5m without an operational reason.
- Audit logs surface throttling events — review **Reports → API Audit** if you suspect throttling.

## Connection / network

| Symptom | Check |
|---------|-------|
| `Connection refused` | DNS resolution, firewall outbound rules, senhasegura listening ports |
| `Connection reset` | Mid-flight, often a stateful firewall idle timeout — shorten request payload or split work |
| Long tail latency | Senhasegura behind WAF/proxy with cold paths; warm with a periodic heartbeat call |

## Audit and observability

- **Reports → API Audit** in the console is the source of truth for what your A2A application called and what it received (200/4xx/5xx).
- **Reports → Access Logs** show password retrievals and custody events — useful when you suspect Gotcha #1 (forgotten custody release).
- Plumb request/response timing into your own observability — senhasegura latency is invisible to most apps until it isn't.
