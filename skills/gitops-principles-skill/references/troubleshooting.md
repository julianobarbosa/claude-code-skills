# GitOps Troubleshooting Guide

Comprehensive debugging guide for common GitOps issues with ArgoCD, Flux, and Kubernetes.

## Quick Diagnostic Commands

### ArgoCD Quick Checks

```bash
# Application status overview
argocd app list

# Detailed app info
argocd app get myapp

# Show diff between Git and cluster
argocd app diff myapp

# Force refresh from Git
argocd app get myapp --refresh

# View sync history
argocd app history myapp

# Check ArgoCD components health
kubectl get pods -n argocd
```

### Flux Quick Checks

```bash
# Overall Flux status
flux check

# Kustomization status
flux get kustomizations -A

# Source status
flux get sources git -A

# Reconcile immediately
flux reconcile kustomization myapp --with-source

# View logs
flux logs --kind=Kustomization --name=myapp
```

### Kubernetes Quick Checks

```bash
# Pod status
kubectl get pods -n myapp

# Recent events
kubectl get events -n myapp --sort-by='.lastTimestamp'

# Describe problematic resource
kubectl describe deployment myapp -n myapp

# Pod logs
kubectl logs -l app=myapp -n myapp --tail=100
```

---

## Common Issues and Solutions

### Issue 1: Application Stuck in "OutOfSync"

**Symptoms:**

- Application shows `OutOfSync` status
- Sync button doesn't resolve the issue
- Diff shows unexpected differences

**Diagnostic Steps:**

```bash
# Step 1: View the diff
argocd app diff myapp

# Step 2: Check for ignored differences
argocd app get myapp -o yaml | grep -A 20 ignoreDifferences

# Step 3: Force a hard refresh
argocd app get myapp --hard-refresh
```

**Common Causes and Fixes:**

**Cause A: Server-side modifications (mutating webhooks, controllers)**

```yaml
# Fix: Add ignoreDifferences to Application
spec:
  ignoreDifferences:
    - group: apps
      kind: Deployment
      jsonPointers:
        - /spec/replicas  # Ignored by HPA
    - group: ""
      kind: Service
      jsonPointers:
        - /spec/clusterIP  # Auto-assigned
```

**Cause B: Defaulting by Kubernetes API**

```yaml
# Fix: Use Server-Side Apply
spec:
  syncPolicy:
    syncOptions:
      - ServerSideApply=true
```

**Cause C: Resource created outside Git**

```bash
# Identify extra resources
argocd app resources myapp

# Either:
# 1. Add to Git
# 2. Enable pruning
# 3. Add to exclude patterns
```

---

### Issue 2: Sync Failed

**Symptoms:**

- Application shows `Sync Failed`
- Error message in sync operation

**Diagnostic Steps:**

```bash
# Step 1: Get sync status details
argocd app get myapp

# Step 2: View sync operation result
argocd app sync myapp --dry-run

# Step 3: Check ArgoCD controller logs
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-application-controller
```

**Common Causes and Fixes:**

**Cause A: Invalid YAML/Manifest**

```bash
# Validate manifests locally
kustomize build ./overlays/prod | kubectl apply --dry-run=client -f -

# Or for Helm
helm template myrelease ./chart --validate
```

**Cause B: RBAC Permissions**

```bash
# Check ArgoCD service account permissions
kubectl auth can-i create deployments --as=system:serviceaccount:argocd:argocd-application-controller -n myapp
```

```yaml
# Fix: Add namespace to AppProject destinations
spec:
  destinations:
    - namespace: myapp
      server: https://kubernetes.default.svc
```

**Cause C: Resource Conflict**

```bash
# Check if resource exists with different manager
kubectl get deployment myapp -n myapp -o yaml | grep -A 5 managedFields
```

```yaml
# Fix: Force replace
spec:
  syncPolicy:
    syncOptions:
      - Replace=true
```

---

### Issue 3: Application Degraded

**Symptoms:**

- Application shows `Degraded` health status
- Pods not running correctly

**Diagnostic Steps:**

```bash
# Step 1: Get health details
argocd app get myapp

# Step 2: Check pod status
kubectl get pods -n myapp
kubectl describe pod <pod-name> -n myapp

# Step 3: Check pod logs
kubectl logs <pod-name> -n myapp --previous  # For crashed containers
```

**Common Causes and Fixes:**

**Cause A: Image Pull Failure**

```bash
# Check events
kubectl get events -n myapp | grep -i pull

# Verify image exists
docker pull myregistry/myapp:v1.0.0

# Check imagePullSecrets
kubectl get deployment myapp -n myapp -o yaml | grep -A 5 imagePullSecrets
```

**Cause B: Resource Limits**

```bash
# Check for OOMKilled
kubectl get pods -n myapp -o jsonpath='{.items[*].status.containerStatuses[*].lastState.terminated.reason}'

# Check resource usage
kubectl top pods -n myapp
```

**Cause C: Readiness Probe Failure**

```bash
# Check probe configuration
kubectl get deployment myapp -n myapp -o yaml | grep -A 10 readinessProbe

# Test endpoint manually
kubectl exec -it <pod-name> -n myapp -- curl localhost:8080/health
```

---

### Issue 4: Repository Connection Failed

**Symptoms:**

- ArgoCD can't connect to Git repository
- `ComparisonError` or `Unable to fetch repository`

**Diagnostic Steps:**

```bash
# Step 1: Check repository status
argocd repo list

# Step 2: Test connection
argocd repo get https://github.com/org/repo.git

# Step 3: Check repo-server logs
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-repo-server
```

**Common Causes and Fixes:**

**Cause A: Authentication Failure**

```bash
# Update credentials
argocd repo add https://github.com/org/repo.git \
  --username git \
  --password $GITHUB_TOKEN \
  --upsert
```

**Cause B: SSH Key Issues**

```bash
# Check known hosts
argocd cert list

# Add SSH key
argocd repo add git@github.com:org/repo.git \
  --ssh-private-key-path ~/.ssh/id_rsa
```

**Cause C: Network/Firewall**

```bash
# Test from repo-server pod
kubectl exec -it -n argocd <repo-server-pod> -- \
  git ls-remote https://github.com/org/repo.git
```

---

### Issue 5: Webhook Not Triggering

**Symptoms:**

- Changes pushed to Git but no sync
- Waiting for poll interval

**Diagnostic Steps:**

```bash
# Step 1: Check webhook configuration in Git provider

# Step 2: Verify ArgoCD webhook endpoint
curl -X POST https://argocd.example.com/api/webhook

# Step 3: Check API server logs
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-server | grep webhook
```

**Common Causes and Fixes:**

**Cause A: Wrong Webhook URL**

```
# Correct URL format
https://argocd.example.com/api/webhook

# NOT
https://argocd.example.com/webhook
https://argocd.example.com/api/v1/webhook
```

**Cause B: Secret Mismatch**

```yaml
# Verify webhook secret in argocd-secret
kubectl get secret argocd-secret -n argocd -o yaml | grep webhook
```

**Cause C: Ingress/Load Balancer Issue**

```bash
# Check if webhook endpoint is reachable
curl -v https://argocd.example.com/api/webhook
```

---

### Issue 6: Slow Sync Performance

**Symptoms:**

- Syncs take a long time
- Timeouts during sync
- High resource usage on ArgoCD

**Diagnostic Steps:**

```bash
# Step 1: Check resource usage
kubectl top pods -n argocd

# Step 2: Check number of resources
argocd app resources myapp | wc -l

# Step 3: Check controller metrics
kubectl port-forward -n argocd svc/argocd-metrics 8082:8082
curl localhost:8082/metrics | grep argocd_app
```

**Optimization Steps:**

**1. Increase Controller Resources:**

```yaml
# argocd-application-controller deployment
resources:
  limits:
    cpu: "2"
    memory: "2Gi"
  requests:
    cpu: "500m"
    memory: "512Mi"
```

**2. Split Large Applications:**

```yaml
# Instead of one app with 500 resources
# Create multiple smaller apps
```

**3. Optimize Sync Options:**

```yaml
spec:
  syncPolicy:
    syncOptions:
      - ApplyOutOfSyncOnly=true  # Only sync changed resources
```

**4. Adjust Reconciliation Timeout:**

```yaml
# In argocd-cm ConfigMap
data:
  timeout.reconciliation: 300s
```

---

### Issue 7: Multi-Cluster Connection Issues

**Symptoms:**

- External cluster shows as disconnected
- Applications targeting external cluster fail

**Diagnostic Steps:**

```bash
# Step 1: List clusters
argocd cluster list

# Step 2: Check cluster status
argocd cluster get https://external-cluster:6443

# Step 3: Verify cluster secret
kubectl get secret -n argocd -l argocd.argoproj.io/secret-type=cluster
```

**Common Causes and Fixes:**

**Cause A: Expired Credentials**

```bash
# Rotate cluster credentials
argocd cluster rotate-auth https://external-cluster:6443
```

**Cause B: Network Connectivity**

```bash
# Test from ArgoCD pod
kubectl exec -it -n argocd <application-controller-pod> -- \
  curl -k https://external-cluster:6443/healthz
```

**Cause C: Certificate Issues**

```bash
# Re-add cluster with updated certs
argocd cluster add external-context --name external-cluster
```

---

## Debugging Checklist

### Pre-Sync Checklist

- [ ] Manifests are valid YAML
- [ ] Image tags exist and are pullable
- [ ] Secrets/ConfigMaps referenced exist
- [ ] Namespace exists or `CreateNamespace=true`
- [ ] RBAC allows ArgoCD to create resources
- [ ] Resource quotas won't block creation

### Post-Failure Checklist

- [ ] Check ArgoCD UI for error messages
- [ ] Review `argocd app diff` output
- [ ] Check Kubernetes events in target namespace
- [ ] Review ArgoCD controller logs
- [ ] Verify Git repository is accessible
- [ ] Check for webhook delivery failures

### Performance Checklist

- [ ] Applications are appropriately sized
- [ ] `ApplyOutOfSyncOnly` enabled where appropriate
- [ ] Controller resources adequate
- [ ] Redis cache functioning
- [ ] Repository server not overloaded

---

## Log Locations

| Component | How to Access |
|-----------|---------------|
| ArgoCD API Server | `kubectl logs -n argocd -l app.kubernetes.io/name=argocd-server` |
| ArgoCD Controller | `kubectl logs -n argocd -l app.kubernetes.io/name=argocd-application-controller` |
| ArgoCD Repo Server | `kubectl logs -n argocd -l app.kubernetes.io/name=argocd-repo-server` |
| Flux Source Controller | `kubectl logs -n flux-system -l app=source-controller` |
| Flux Kustomize Controller | `kubectl logs -n flux-system -l app=kustomize-controller` |

---

## Emergency Procedures

### Force Sync (Override Errors)

```bash
# ArgoCD
argocd app sync myapp --force --prune

# Flux
flux reconcile kustomization myapp --force
```

### Disable Auto-Sync (Stop Reconciliation)

```bash
# ArgoCD - patch application
argocd app set myapp --sync-policy none

# Flux - suspend kustomization
flux suspend kustomization myapp
```

### Emergency Rollback

```bash
# ArgoCD
argocd app rollback myapp <revision>

# Git-based (works for any tool)
git revert HEAD
git push
```

### Nuclear Option (Delete and Recreate)

```bash
# WARNING: Causes downtime
argocd app delete myapp --cascade=false  # Keep resources
# Fix configuration
argocd app create myapp ...  # Recreate application
```
