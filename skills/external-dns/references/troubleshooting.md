# External-DNS Troubleshooting Guide

Comprehensive troubleshooting guide for External-DNS across all supported DNS providers.

## Quick Diagnostic Commands

```bash
# 1. Check if External-DNS is running
kubectl get pods -n external-dns -l app.kubernetes.io/name=external-dns

# 2. Check recent logs
kubectl logs -n external-dns deployment/external-dns --tail=100

# 3. Check for errors in logs
kubectl logs -n external-dns deployment/external-dns | grep -i "error\|warn\|fail"

# 4. Describe pod for events
kubectl describe pod -n external-dns -l app.kubernetes.io/name=external-dns

# 5. Check configuration
kubectl get deployment external-dns -n external-dns -o yaml | grep -A 30 args

# 6. Check service account
kubectl get sa external-dns -n external-dns -o yaml

# 7. Restart external-dns
kubectl rollout restart deployment external-dns -n external-dns
```

## Issue Categories

## 1. DNS Records Not Created

### Symptoms

- Ingress/Service deployed but no DNS record in provider
- Logs show "no endpoints generated"

### Diagnostic Steps

```bash
# Check if external-dns is detecting the resource
kubectl logs -n external-dns deployment/external-dns | grep "Desired change"

# Verify the Ingress/Service exists and has correct annotations
kubectl get ingress <name> -o yaml
kubectl get service <name> -o yaml

# Check domain filters
kubectl get deployment external-dns -n external-dns -o yaml | grep domain-filter
```

### Common Causes and Solutions

#### Domain Not in Filter

**Problem**: Hostname doesn't match `domainFilters`

```yaml
# Values has:
domainFilters:
  - example.com

# But Ingress uses:
host: app.other-domain.com  # Won't be managed
```

**Solution**: Add domain to filter or remove filter to manage all domains:

```yaml
domainFilters:
  - example.com
  - other-domain.com
```

#### Source Type Not Configured

**Problem**: Watching wrong source type

```yaml
# Values has:
sources:
  - service  # Only watching services

# But using:
kind: Ingress  # Won't be detected
```

**Solution**: Add correct source type:

```yaml
sources:
  - service
  - ingress
```

#### Missing Hostname

**Problem**: Ingress without explicit host

```yaml
# Missing host or annotation
spec:
  rules:
    - http:  # No host specified
```

**Solution**: Add hostname:

```yaml
spec:
  rules:
    - host: app.example.com
      http:
        paths: [...]
```

#### Service Not LoadBalancer

**Problem**: Service type doesn't expose external IP

```yaml
spec:
  type: ClusterIP  # No external IP
```

**Solution**: Use LoadBalancer or add annotation:

```yaml
spec:
  type: LoadBalancer

# Or for ClusterIP with annotation:
metadata:
  annotations:
    external-dns.alpha.kubernetes.io/hostname: app.example.com
```

## 2. Authentication Failures

### Symptoms

- `401 Unauthorized` or `403 Forbidden` in logs
- `authorization failed` messages

### Provider-Specific Solutions

#### Azure DNS

```bash
# Check environment variables
kubectl exec -n external-dns deployment/external-dns -- env | grep AZURE

# Verify Workload Identity labels
kubectl get pod -n external-dns -l app.kubernetes.io/name=external-dns -o yaml | grep "azure.workload.identity"

# Check service account annotations
kubectl get sa external-dns -n external-dns -o yaml | grep azure

# Verify role assignment
az role assignment list --assignee <IDENTITY_OBJECT_ID> --scope <DNS_ZONE_ID> -o table
```

**Solutions**:

1. Verify AZURE_TENANT_ID, AZURE_SUBSCRIPTION_ID, AZURE_RESOURCE_GROUP are correct
2. Ensure Workload Identity labels are on both ServiceAccount AND Pod
3. Check federated credential subject: `system:serviceaccount:external-dns:external-dns`
4. Verify DNS Zone Contributor role is assigned to the managed identity

#### Cloudflare

```bash
# Test API token
curl "https://api.cloudflare.com/client/v4/user/tokens/verify" \
  -H "Authorization: Bearer $(kubectl get secret cloudflare-api-token -n external-dns -o jsonpath='{.data.cloudflare_api_token}' | base64 -d)"

# List accessible zones
curl "https://api.cloudflare.com/client/v4/zones" \
  -H "Authorization: Bearer $CF_API_TOKEN" | jq '.result[].name'
```

**Solutions**:

1. Regenerate API token with correct permissions (Zone:Read, DNS:Edit)
2. Verify Zone Resources includes your zones
3. Update Kubernetes secret with new token

#### AWS Route53

```bash
# Check IAM role annotation
kubectl get sa external-dns -n external-dns -o yaml | grep eks.amazonaws.com/role-arn

# Test assume role (from cluster)
kubectl exec -n external-dns deployment/external-dns -- aws sts get-caller-identity
```

**Solutions**:

1. Verify IRSA role annotation on ServiceAccount
2. Check IAM policy has route53 permissions
3. Ensure OIDC provider is configured for cluster

## 3. TXT Record Conflicts

### Symptoms

- `TXT record ownership conflict` in logs
- Records not being updated
- `another external-dns instance owns this record`

### Diagnostic Steps

```bash
# Check current TXT ownership records
dig TXT _externaldns.app.example.com

# For Azure
az network dns record-set txt list -g <RG> -z <ZONE> | grep external-dns

# For Cloudflare
curl "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records?type=TXT" \
  -H "Authorization: Bearer $CF_API_TOKEN" | jq '.result[] | select(.name | contains("externaldns"))'
```

### Solutions

#### Different txtOwnerId per Cluster

```yaml
# Cluster 1
txtOwnerId: "aks-cluster-1-eastus"

# Cluster 2
txtOwnerId: "aks-cluster-2-westus"
```

#### Clean Up Orphaned TXT Records

```bash
# For Azure - delete orphaned TXT record
az network dns record-set txt delete -g <RG> -z <ZONE> -n _externaldns.app --yes

# For Cloudflare
RECORD_ID="<record-id-from-list>"
curl -X DELETE "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/$RECORD_ID" \
  -H "Authorization: Bearer $CF_API_TOKEN"
```

#### Change TXT Prefix

```yaml
# If migrating from another txtOwnerId
txtPrefix: "_externaldns2."  # Use different prefix temporarily
```

## 4. Rate Limiting

### Symptoms

- `429 Too Many Requests` in logs
- DNS updates delayed
- Intermittent sync failures

### Solutions

#### Increase Sync Interval

```yaml
# Development
interval: "1m"

# Production (recommended)
interval: "10m"
```

#### Optimize API Calls

```yaml
extraArgs:
  # Cloudflare - reduce API calls
  cloudflare-dns-records-per-page: 5000

  # AWS - batch changes
  aws-batch-change-size: 4000
  aws-zones-cache-duration: 3h
```

#### Filter Zones

```yaml
# Cloudflare - specific zone IDs
extraArgs:
  zone-id-filter: "zone-id-1,zone-id-2"

# AWS - specific hosted zones
extraArgs:
  aws-zone-match-parent: true
```

## 5. High Memory/CPU Usage

### Symptoms

- Pods OOMKilled
- Slow sync cycles
- CPU throttling

### Solutions

#### Increase Resource Limits

```yaml
resources:
  requests:
    memory: "128Mi"
    cpu: "50m"
  limits:
    memory: "256Mi"
    # No CPU limit recommended
```

#### Reduce Scope

```yaml
# Limit to specific namespaces
extraArgs:
  namespace: "app-namespace"

# Or exclude namespaces
extraArgs:
  ignore-hostname-annotation: true
```

#### Increase Interval

```yaml
interval: "15m"  # Reduce sync frequency
```

## 6. Records Not Deleted (Expected Behavior)

### Symptoms

- Old DNS records remain after Ingress/Service deletion
- Records accumulate over time

### Explanation

This is **expected** when using `policy: upsert-only` (recommended for production).

| Policy | Creates | Updates | Deletes |
|--------|---------|---------|---------|
| `sync` | Yes | Yes | Yes |
| `upsert-only` | Yes | Yes | No |

### Solutions

For **production**: Manually delete records via DNS provider dashboard

For **development**: Use sync policy:

```yaml
policy: sync  # Only in dev environments
```

## 7. SSL/TLS Issues

### Symptoms

- Connection refused to provider API
- Certificate verification errors

### Solutions

#### Skip TLS Verification (Not Recommended)

```yaml
extraArgs:
  tls-verify: false  # Only for testing
```

#### Update CA Certificates

```yaml
# Mount custom CA bundle
volumes:
  - name: ca-bundle
    configMap:
      name: custom-ca-bundle
volumeMounts:
  - name: ca-bundle
    mountPath: /etc/ssl/certs
    readOnly: true
```

## 8. Pods Not Starting

### Symptoms

- Pods in CrashLoopBackOff
- Init container failures

### Diagnostic Steps

```bash
# Check pod events
kubectl describe pod -n external-dns -l app.kubernetes.io/name=external-dns

# Check for image pull errors
kubectl get events -n external-dns --sort-by='.lastTimestamp'

# Check resource constraints
kubectl top pods -n external-dns
```

### Solutions

#### Image Pull Errors

```yaml
# Verify image exists
image:
  repository: registry.k8s.io/external-dns/external-dns
  tag: v0.18.0

# Or use specific registry
image:
  repository: gcr.io/k8s-staging-external-dns/external-dns
```

#### Security Context Issues

```yaml
# Ensure compatible security context
securityContext:
  runAsNonRoot: true
  runAsUser: 65534
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities:
    drop: ["ALL"]
```

## Debug Mode

Enable debug logging for detailed troubleshooting:

```yaml
logLevel: debug
logFormat: json

# Or via args
extraArgs:
  log-level: debug
```

**Warning**: Debug logging is verbose. Return to `info` or `warning` after troubleshooting.

## Dry Run Mode

Test changes without applying:

```yaml
extraArgs:
  dry-run: true
```

Check logs to see what changes would be made:

```bash
kubectl logs -n external-dns deployment/external-dns | grep "would have"
```

## Validation Checklist

### Pre-deployment

- [ ] DNS provider credentials are valid
- [ ] Appropriate RBAC permissions assigned
- [ ] `txtOwnerId` is unique for this cluster
- [ ] `domainFilters` includes all target domains
- [ ] Source types (service/ingress) are configured
- [ ] Namespace is created

### Post-deployment

- [ ] Pods are Running
- [ ] No error logs
- [ ] Test record created successfully
- [ ] TXT ownership record exists
- [ ] DNS resolution works
- [ ] Metrics endpoint accessible (port 7979)

### Test Record

Deploy a test service:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: external-dns-test
  namespace: default
  annotations:
    external-dns.alpha.kubernetes.io/hostname: test.example.com
spec:
  type: LoadBalancer
  ports:
    - port: 80
      targetPort: 80
  selector:
    app: nginx
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx-test
  namespace: default
spec:
  replicas: 1
  selector:
    matchLabels:
      app: nginx
  template:
    metadata:
      labels:
        app: nginx
    spec:
      containers:
        - name: nginx
          image: nginx:alpine
          ports:
            - containerPort: 80
```

Verify:

```bash
# Wait for LoadBalancer IP
kubectl get svc external-dns-test -w

# Check external-dns logs
kubectl logs -n external-dns deployment/external-dns | grep test.example.com

# Verify DNS record
dig test.example.com
```

## Getting Help

### Logs to Collect

```bash
# External-DNS logs
kubectl logs -n external-dns deployment/external-dns --tail=500 > external-dns.log

# Pod description
kubectl describe pod -n external-dns -l app.kubernetes.io/name=external-dns > pod-describe.txt

# Configuration
kubectl get deployment external-dns -n external-dns -o yaml > deployment.yaml

# Events
kubectl get events -n external-dns --sort-by='.lastTimestamp' > events.txt
```

### Resources

- [GitHub Issues](https://github.com/kubernetes-sigs/external-dns/issues)
- [Official FAQ](https://kubernetes-sigs.github.io/external-dns/latest/docs/faq/)
- [Provider Tutorials](https://kubernetes-sigs.github.io/external-dns/latest/tutorials/)

## Quick Fixes Reference

| Problem | Quick Fix |
|---------|-----------|
| No records created | Check `domainFilters` and `sources` |
| Auth failure (Azure) | Verify Workload Identity labels and role assignment |
| Auth failure (Cloudflare) | Test API token with curl |
| Rate limited | Increase `interval` to 10m+ |
| TXT conflicts | Ensure unique `txtOwnerId` per cluster |
| Records not deleted | Expected with `policy: upsert-only` |
| Pods crashing | Check resource limits and security context |
