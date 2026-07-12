# External-DNS Cloudflare Configuration Reference

Complete guide for configuring External-DNS with Cloudflare DNS, including proxy settings, API optimization, and production best practices.

## Authentication Methods

| Method | Security | Recommended |
|--------|----------|-------------|
| **API Token** | High (scoped permissions) | Production |
| **API Key** | Lower (global access) | Not recommended |

## API Token Configuration (Recommended)

### Step 1: Create API Token in Cloudflare

1. Go to Cloudflare Dashboard > My Profile > API Tokens
2. Click "Create Token"
3. Use "Custom token" template
4. Configure permissions:

| Permission | Access Level | Required |
|------------|--------------|----------|
| Zone > Zone | Read | Yes |
| Zone > DNS | Edit | Yes |

5. Zone Resources: Select "All zones" or specific zones
6. Click "Continue to summary" > "Create Token"
7. **Save the token immediately** - it won't be shown again

### Step 2: Create Kubernetes Secret

```bash
kubectl create namespace external-dns

kubectl create secret generic cloudflare-api-token \
  --namespace external-dns \
  --from-literal=cloudflare_api_token=<YOUR_API_TOKEN>
```

### Step 3: Helm Values Configuration

```yaml
# values.yaml for Cloudflare
fullnameOverride: external-dns

provider:
  name: cloudflare

# Authentication via secret
env:
  - name: CF_API_TOKEN
    valueFrom:
      secretKeyRef:
        name: cloudflare-api-token
        key: cloudflare_api_token

# Cloudflare-specific configuration
extraArgs:
  cloudflare-proxied: true  # Enable Cloudflare proxy (CDN/DDoS)
  cloudflare-dns-records-per-page: 5000  # API pagination optimization

# Source configuration
sources:
  - service
  - ingress

# Domain filter - restrict to your domains
domainFilters:
  - example.com
  - subdomain.example.com

# TXT record ownership (must be unique per cluster)
txtOwnerId: "aks-cluster-name"
txtPrefix: "_externaldns."

# Policy
policy: upsert-only  # Production: upsert-only, Dev: sync

# Sync interval
interval: "5m"

# Logging
logLevel: info
logFormat: json

# Resources
resources:
  requests:
    memory: "64Mi"
    cpu: "25m"
  limits:
    memory: "128Mi"
```

## Cloudflare Proxy Feature

### Proxied vs DNS-Only Records

| Setting | Proxied (`true`) | DNS-Only (`false`) |
|---------|------------------|---------------------|
| Traffic routing | Through Cloudflare edge | Direct to origin |
| DDoS protection | Yes | No |
| CDN caching | Yes | No |
| SSL termination | At Cloudflare edge | At origin |
| Origin IP | Hidden | Exposed |
| Supported protocols | HTTP/HTTPS only | All (TCP, UDP) |

### Global Proxy Configuration

```yaml
# Enable proxy globally (recommended for web traffic)
extraArgs:
  cloudflare-proxied: true
```

### Per-Record Proxy Override

Override the global setting using annotations:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api
  annotations:
    # Disable proxy for this specific record
    external-dns.alpha.kubernetes.io/cloudflare-proxied: "false"
spec:
  rules:
    - host: api.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: api
                port:
                  number: 80
```

### When to Disable Proxy

- WebSocket connections (if not using Cloudflare Websocket support)
- Non-HTTP protocols (MQTT, custom TCP)
- Services requiring direct IP access
- SSH access endpoints
- Mail servers (MX records)

## API Optimization

### Records Per Page

```yaml
extraArgs:
  cloudflare-dns-records-per-page: 5000  # Default: 100, Max: 5000
```

**Benefits**:

- Fewer API calls for zones with many records
- Reduced risk of rate limiting
- Faster sync cycles

### Sync Interval Tuning

```yaml
# Development: Fast feedback
interval: "1m"

# Staging: Balanced
interval: "5m"

# Production: Conservative
interval: "10m"
```

### Zone ID Filter

For accounts with many zones, filter to specific zone IDs:

```yaml
extraArgs:
  zone-id-filter: "zone_id_1,zone_id_2"
```

Get zone IDs:

```bash
curl -X GET "https://api.cloudflare.com/client/v4/zones" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -H "Content-Type: application/json" | jq '.result[] | {name, id}'
```

## Cloudflare-Specific Annotations

### Basic Annotations

```yaml
# Custom hostname
external-dns.alpha.kubernetes.io/hostname: "app.example.com"

# Custom TTL (seconds, minimum: 60 for proxied, 1 for non-proxied)
external-dns.alpha.kubernetes.io/ttl: "300"

# Proxy override
external-dns.alpha.kubernetes.io/cloudflare-proxied: "false"
```

### Advanced Annotations

```yaml
# Multiple hostnames
external-dns.alpha.kubernetes.io/hostname: "app.example.com,www.example.com"

# Target IP override
external-dns.alpha.kubernetes.io/target: "203.0.113.10"

# Record comment (visible in Cloudflare dashboard)
# Added automatically by external-dns
```

## Multi-Domain Configuration

### Same Cloudflare Account

```yaml
domainFilters:
  - domain1.com
  - domain2.com
  - subdomain.domain3.com

# All domains managed by the same API token
env:
  - name: CF_API_TOKEN
    valueFrom:
      secretKeyRef:
        name: cloudflare-api-token
        key: cloudflare_api_token
```

### Different Cloudflare Accounts

Deploy separate External-DNS instances per account:

```yaml
# Instance 1: domain1.com
fullnameOverride: external-dns-domain1
env:
  - name: CF_API_TOKEN
    valueFrom:
      secretKeyRef:
        name: cloudflare-token-domain1
        key: token
domainFilters:
  - domain1.com
txtOwnerId: "aks-cluster-domain1"

# Instance 2: domain2.com (separate deployment)
fullnameOverride: external-dns-domain2
env:
  - name: CF_API_TOKEN
    valueFrom:
      secretKeyRef:
        name: cloudflare-token-domain2
        key: token
domainFilters:
  - domain2.com
txtOwnerId: "aks-cluster-domain2"
```

## Validation Commands

### Test API Token

```bash
# Verify token permissions
curl -X GET "https://api.cloudflare.com/client/v4/user/tokens/verify" \
  -H "Authorization: Bearer $CF_API_TOKEN" \
  -H "Content-Type: application/json"

# List zones accessible to token
curl -X GET "https://api.cloudflare.com/client/v4/zones" \
  -H "Authorization: Bearer $CF_API_TOKEN" | jq '.result[] | {name, id}'
```

### Check External-DNS Logs

```bash
# Watch logs
kubectl logs -n external-dns deployment/external-dns -f

# Check for Cloudflare-specific messages
kubectl logs -n external-dns deployment/external-dns | grep -i cloudflare

# Check for errors
kubectl logs -n external-dns deployment/external-dns | grep -i error
```

### Verify DNS Records

```bash
# Query Cloudflare DNS directly
dig @1.1.1.1 app.example.com

# Check TXT ownership records
dig @1.1.1.1 TXT _externaldns.app.example.com

# Full trace
dig +trace app.example.com
```

### List Records via Cloudflare API

```bash
ZONE_ID="your-zone-id"

# List all DNS records
curl -X GET "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
  -H "Authorization: Bearer $CF_API_TOKEN" | jq '.result[] | {name, type, content, proxied}'

# List TXT records only
curl -X GET "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records?type=TXT" \
  -H "Authorization: Bearer $CF_API_TOKEN" | jq '.result[] | {name, content}'
```

## Common Issues and Solutions

### Issue: Authentication Failed

**Symptoms**: `401 Unauthorized` or `403 Forbidden` in logs

**Solutions**:

1. Verify API token is correct in secret
2. Check token has Zone:Read and DNS:Edit permissions
3. Verify zone is accessible to the token (Zone Resources setting)
4. Regenerate token if expired

```bash
# Test token
curl "https://api.cloudflare.com/client/v4/user/tokens/verify" \
  -H "Authorization: Bearer $CF_API_TOKEN"
```

### Issue: Rate Limiting

**Symptoms**: `429 Too Many Requests` in logs

**Solutions**:

1. Increase sync interval:

   ```yaml
   interval: "10m"  # Increase from default
   ```

2. Increase records per page:

   ```yaml
   extraArgs:
     cloudflare-dns-records-per-page: 5000
   ```

3. Use zone ID filter to reduce API calls:

   ```yaml
   extraArgs:
     zone-id-filter: "<specific-zone-id>"
   ```

### Issue: Proxy Not Working

**Symptoms**: Records created but not proxied

**Solutions**:

1. Verify `cloudflare-proxied: true` in extraArgs
2. Check per-record annotations aren't overriding
3. Note: Some record types cannot be proxied (MX, TXT, etc.)

### Issue: TXT Record Conflicts

**Symptoms**: `TXT record ownership conflict` in logs

**Solutions**:

1. Ensure unique `txtOwnerId` per cluster
2. Delete orphaned TXT records manually
3. Use different `txtPrefix` if migrating

```bash
# Find and delete orphaned TXT records
curl -X GET "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records?type=TXT&name=_externaldns" \
  -H "Authorization: Bearer $CF_API_TOKEN" | jq '.result[] | {id, name, content}'
```

### Issue: Records Not Created

**Symptoms**: Ingress/Service deployed but no DNS record

**Solutions**:

1. Check `domainFilters` includes your domain
2. Verify source type (service/ingress) is in `sources`
3. Check dry-run is not enabled
4. Verify Ingress has a host defined

## High Availability Configuration

```yaml
# Production HA configuration
replicaCount: 2

affinity:
  podAntiAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchExpressions:
            - key: app.kubernetes.io/name
              operator: In
              values:
                - external-dns
        topologyKey: kubernetes.io/hostname

podDisruptionBudget:
  enabled: true
  minAvailable: 1
```

## Security Best Practices

### API Token Rotation

```bash
# Create new token in Cloudflare dashboard
# Update Kubernetes secret
kubectl create secret generic cloudflare-api-token \
  --namespace external-dns \
  --from-literal=cloudflare_api_token=<NEW_TOKEN> \
  --dry-run=client -o yaml | kubectl apply -f -

# Restart external-dns to pick up new secret
kubectl rollout restart deployment external-dns -n external-dns

# Delete old token in Cloudflare dashboard
```

### Minimal Permissions Token

Create token with minimal required permissions:

1. **Zone > Zone > Read** - List zones
2. **Zone > DNS > Edit** - Manage DNS records
3. **Zone Resources** - Include only required zones

### Network Policy

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: external-dns
  namespace: external-dns
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: external-dns
  policyTypes:
    - Egress
  egress:
    # Allow DNS resolution
    - to: []
      ports:
        - protocol: UDP
          port: 53
    # Allow Cloudflare API
    - to:
        - ipBlock:
            cidr: 104.16.0.0/12  # Cloudflare IPs
      ports:
        - protocol: TCP
          port: 443
    # Allow Kubernetes API
    - to:
        - namespaceSelector: {}
          podSelector:
            matchLabels:
              component: kube-apiserver
      ports:
        - protocol: TCP
          port: 443
```

## Monitoring

### Prometheus Metrics

```promql
# Sync errors
rate(external_dns_controller_sync_errors_total[5m])

# Records managed
external_dns_registry_endpoints_total

# Last sync time
time() - external_dns_controller_last_sync_timestamp_seconds
```

### Alert Rules

```yaml
groups:
  - name: external-dns-cloudflare
    rules:
      - alert: CloudflareRateLimited
        expr: increase(external_dns_controller_sync_errors_total{error="rate_limited"}[5m]) > 0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: External-DNS is being rate limited by Cloudflare

      - alert: CloudflareAuthFailure
        expr: increase(external_dns_controller_sync_errors_total{error="unauthorized"}[5m]) > 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: External-DNS Cloudflare authentication failure
```

## References

- [Cloudflare Tutorial](https://kubernetes-sigs.github.io/external-dns/latest/tutorials/cloudflare/)
- [Cloudflare API Documentation](https://developers.cloudflare.com/api/)
- [Cloudflare API Tokens](https://developers.cloudflare.com/fundamentals/api/get-started/create-token/)
- [Cloudflare Proxy Mode](https://developers.cloudflare.com/dns/manage-dns-records/reference/proxied-dns-records/)
