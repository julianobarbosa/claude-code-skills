# Cloudflare DNS - Azure Integration Reference

Patterns and configurations for using Cloudflare DNS with Azure workloads.

## Architecture Patterns

### Pattern 1: AKS + Ingress-NGINX + Cloudflare

```
Internet
    │
    ▼
Cloudflare (Proxy/CDN)
    │
    ▼
Azure Load Balancer (Public IP)
    │
    ▼
Ingress-NGINX Controller
    │
    ▼
Kubernetes Services
    │
    ▼
Pods
```

**DNS Configuration:**

- Type: A Record
- Name: app.example.com
- Content: Azure Load Balancer IP
- Proxy: Enabled (orange cloud)

### Pattern 2: Azure App Service + Cloudflare

```
Internet
    │
    ▼
Cloudflare (Proxy/CDN)
    │
    ▼
Azure App Service
(myapp.azurewebsites.net)
```

**DNS Configuration:**

- Type: CNAME
- Name: app
- Content: myapp.azurewebsites.net
- Proxy: Enabled (orange cloud)

### Pattern 3: Azure Static Web Apps + Cloudflare

```
Internet
    │
    ▼
Cloudflare (DNS Only)
    │
    ▼
Azure Static Web Apps CDN
```

**DNS Configuration:**

- Type: CNAME
- Name: www
- Content: nice-beach-123.azurestaticapps.net
- Proxy: Disabled (gray cloud) - Azure handles CDN

### Pattern 4: Azure Front Door (Not Recommended)

Avoid combining Cloudflare proxy with Azure Front Door - use one or the other.

If required:

- Type: CNAME
- Proxy: Disabled (gray cloud)
- Let Azure Front Door handle CDN/WAF

## External-DNS Configuration

### Complete Helm Values for AKS

```yaml
# values.yaml - External-DNS with Cloudflare for AKS
fullnameOverride: external-dns

provider:
  name: cloudflare

env:
  - name: CF_API_TOKEN
    valueFrom:
      secretKeyRef:
        name: cloudflare-api-token
        key: cloudflare_api_token

# Cloudflare optimizations
extraArgs:
  cloudflare-proxied: "true"
  cloudflare-dns-records-per-page: "5000"

# Sources
sources:
  - service
  - ingress

# Domain restrictions
domainFilters:
  - example.com

# Ownership tracking
registry: txt
txtOwnerId: "aks-prod-eastus"  # UNIQUE per cluster
txtPrefix: "_externaldns."

# Policy
policy: upsert-only  # NEVER sync in production

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

# Pod security
securityContext:
  runAsNonRoot: true
  runAsUser: 65534
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities:
    drop: ["ALL"]

# Monitoring
serviceMonitor:
  enabled: true
  interval: 30s
  namespace: monitoring

# High availability (optional)
affinity:
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 100
        podAffinityTerm:
          labelSelector:
            matchExpressions:
              - key: app.kubernetes.io/name
                operator: In
                values:
                  - external-dns
          topologyKey: kubernetes.io/hostname
```

### Kubernetes Secret Setup

```bash
# Create namespace
kubectl create namespace external-dns

# Create secret from Azure Key Vault
CF_TOKEN=$(az keyvault secret show \
  --vault-name "your-keyvault" \
  --name "cloudflare-api-token" \
  --query value -o tsv)

kubectl create secret generic cloudflare-api-token \
  --namespace external-dns \
  --from-literal=cloudflare_api_token="$CF_TOKEN"
```

## cert-manager Integration

### DNS-01 Challenge with Cloudflare

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-cloudflare
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@example.com
    privateKeySecretRef:
      name: letsencrypt-cloudflare-key
    solvers:
      - dns01:
          cloudflare:
            apiTokenSecretRef:
              name: cloudflare-api-token
              key: api-token
        selector:
          dnsZones:
            - example.com
```

### cert-manager Secret

```bash
# cert-manager uses different key name
kubectl create secret generic cloudflare-api-token \
  --namespace cert-manager \
  --from-literal=api-token="$CF_TOKEN"
```

### Complete Ingress with TLS

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: myapp
  annotations:
    # cert-manager
    cert-manager.io/cluster-issuer: letsencrypt-cloudflare

    # External-DNS
    external-dns.alpha.kubernetes.io/hostname: app.example.com
    external-dns.alpha.kubernetes.io/cloudflare-proxied: "true"
    external-dns.alpha.kubernetes.io/ttl: "300"

    # NGINX
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
    - hosts:
        - app.example.com
      secretName: app-tls
  rules:
    - host: app.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: myapp
                port:
                  number: 80
```

## Origin Protection

### Ingress-NGINX: Allow Only Cloudflare IPs

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: ingress-nginx-controller
  namespace: ingress-nginx
data:
  # Cloudflare IP ranges
  # Source: https://www.cloudflare.com/ips/
  whitelist-source-range: |
    173.245.48.0/20,
    103.21.244.0/22,
    103.22.200.0/22,
    103.31.4.0/22,
    141.101.64.0/18,
    108.162.192.0/18,
    190.93.240.0/20,
    188.114.96.0/20,
    197.234.240.0/22,
    198.41.128.0/17,
    162.158.0.0/15,
    104.16.0.0/13,
    104.24.0.0/14,
    172.64.0.0/13,
    131.0.72.0/22,
    2400:cb00::/32,
    2606:4700::/32,
    2803:f800::/32,
    2405:b500::/32,
    2405:8100::/32,
    2a06:98c0::/29,
    2c0f:f248::/32
```

### Azure NSG Rules

```bash
# Get Cloudflare IPs
curl -s https://www.cloudflare.com/ips-v4 > cf-ipv4.txt
curl -s https://www.cloudflare.com/ips-v6 > cf-ipv6.txt

# Create NSG rule (example)
az network nsg rule create \
  --resource-group MC_rg-aks_aks-cluster_eastus \
  --nsg-name aks-agentpool-nsg \
  --name AllowCloudflareHTTPS \
  --priority 100 \
  --source-address-prefixes $(cat cf-ipv4.txt | tr '\n' ' ') \
  --destination-port-ranges 443 \
  --access Allow \
  --protocol Tcp
```

## SSL/TLS Configuration

### Recommended Zone Settings

| Setting | Value | Reason |
|---------|-------|--------|
| SSL Mode | Full (Strict) | Validates origin certificate |
| Always Use HTTPS | On | Force HTTPS |
| Min TLS Version | 1.2 | Security baseline |
| TLS 1.3 | On | Performance & security |
| HSTS | On | Strict transport security |

### Origin Certificates

**Option 1: Let's Encrypt via cert-manager**

- Works with Full (Strict) mode
- Auto-renewal
- Recommended for Kubernetes

**Option 2: Cloudflare Origin CA**

- 15-year validity
- Only trusted by Cloudflare
- Good for App Service

## Multi-Cluster Configuration

### Unique txtOwnerId per Cluster

| Cluster | Region | txtOwnerId |
|---------|--------|------------|
| aks-dev | East US | aks-dev-eastus |
| aks-stg | West Europe | aks-stg-westeurope |
| aks-prd | East US | aks-prd-eastus |

### ArgoCD ApplicationSet

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: external-dns
  namespace: argocd
spec:
  generators:
    - list:
        elements:
          - cluster: dev
            txtOwnerId: aks-dev-eastus
          - cluster: stg
            txtOwnerId: aks-stg-westeurope
          - cluster: prd
            txtOwnerId: aks-prd-eastus
  template:
    metadata:
      name: 'external-dns-{{cluster}}'
    spec:
      project: infrastructure
      sources:
        - chart: external-dns
          repoURL: https://kubernetes-sigs.github.io/external-dns/
          targetRevision: "1.18.0"
          helm:
            releaseName: external-dns
            valueFiles:
              - $values/argo-cd-helm-values/kube-addons/external-dns/{{cluster}}/values.yaml
        - repoURL: https://your-repo.git
          targetRevision: main
          ref: values
      destination:
        server: '{{url}}'
        namespace: external-dns
```

## Monitoring & Alerting

### Prometheus Metrics

```promql
# Sync errors
rate(external_dns_controller_sync_errors_total[5m])

# Records managed
external_dns_registry_endpoints_total

# Last sync time (staleness)
time() - external_dns_controller_last_sync_timestamp_seconds > 600
```

### Alert Rules

```yaml
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: external-dns-cloudflare
  namespace: monitoring
spec:
  groups:
    - name: external-dns
      rules:
        - alert: ExternalDNSSyncFailed
          expr: increase(external_dns_controller_sync_errors_total[5m]) > 0
          for: 5m
          labels:
            severity: warning
          annotations:
            summary: External-DNS sync errors detected
            description: External-DNS is experiencing sync errors with Cloudflare

        - alert: ExternalDNSStale
          expr: time() - external_dns_controller_last_sync_timestamp_seconds > 900
          for: 5m
          labels:
            severity: critical
          annotations:
            summary: External-DNS has not synced recently
            description: External-DNS last sync was over 15 minutes ago
```

## Troubleshooting

### Check External-DNS Status

```bash
# Pods running
kubectl get pods -n external-dns

# Logs
kubectl logs -n external-dns deployment/external-dns -f

# Check for Cloudflare errors
kubectl logs -n external-dns deployment/external-dns | grep -E "(error|cloudflare|401|403|429)"

# Check configuration
kubectl get deployment external-dns -n external-dns -o yaml | grep -A 30 args
```

### Verify DNS Records

```bash
# Query Cloudflare DNS
dig @1.1.1.1 app.example.com A

# Check if proxied (Cloudflare IP = proxied)
dig +short app.example.com
# 104.x.x.x = proxied
# Your actual IP = DNS-only

# Check TXT ownership
dig @1.1.1.1 TXT _externaldns.app.example.com
```

### Common Issues

| Issue | Symptom | Solution |
|-------|---------|----------|
| No records created | Ingress exists but no DNS | Check domainFilters, verify annotations |
| Auth failed | 401/403 in logs | Verify CF_API_TOKEN secret |
| Rate limited | 429 errors | Increase interval, use zone-id-filter |
| TXT conflicts | Ownership errors | Ensure unique txtOwnerId per cluster |
| Wrong IP | DNS returns incorrect IP | Check ingress controller external IP |
