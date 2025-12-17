# GitOps Anti-Patterns

Common mistakes and pitfalls to avoid when implementing GitOps, with guidance on proper practices.

## Configuration Anti-Patterns

### Anti-Pattern 1: Imperative Commands in Production

**The Problem:**

```bash
# DON'T DO THIS
kubectl scale deployment nginx --replicas=5
kubectl set image deployment/nginx nginx=nginx:1.22
kubectl edit configmap app-config
```

**Why It's Bad:**

- Changes are not tracked in Git
- Drift occurs between Git and cluster
- No audit trail
- Changes lost on next sync

**The Fix:**

```yaml
# DO THIS: Update Git, let GitOps sync
# manifests/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx
spec:
  replicas: 5  # Changed from 3
  template:
    spec:
      containers:
      - name: nginx
        image: nginx:1.22  # Updated version
```

---

### Anti-Pattern 2: Mutable Image Tags

**The Problem:**

```yaml
# DON'T DO THIS
containers:
- name: app
  image: myapp:latest
  # or
  image: myapp:dev
  # or
  image: myapp:stable
```

**Why It's Bad:**

- Same tag, different content over time
- No way to track what's actually deployed
- Rollback doesn't work (`:latest` changed)
- Cache issues across nodes

**The Fix:**

```yaml
# DO THIS: Use immutable tags or digests
containers:
- name: app
  image: myapp:v1.2.3
  # or even better
  image: myapp@sha256:abc123def456...
```

**Automated Fix with Kargo/Flux:**

```yaml
# Warehouse subscription
subscriptions:
  - image:
      repoURL: myregistry/myapp
      imageSelectionStrategy: SemVer
      constraint: ^1.0.0
```

---

### Anti-Pattern 3: Secrets in Git

**The Problem:**

```yaml
# DON'T DO THIS - NEVER COMMIT SECRETS
apiVersion: v1
kind: Secret
metadata:
  name: db-credentials
type: Opaque
data:
  password: bXlzZWNyZXRwYXNzd29yZA==  # base64 != encryption!
```

**Why It's Bad:**

- Git history is forever
- base64 is encoding, not encryption
- Secrets exposed to anyone with repo access
- Compliance violations

**The Fix:**

Option 1: External Secrets Operator

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: db-credentials
spec:
  refreshInterval: 1h
  secretStoreRef:
    kind: ClusterSecretStore
    name: azure-keyvault
  target:
    name: db-credentials
  data:
    - secretKey: password
      remoteRef:
        key: database-password
```

Option 2: Sealed Secrets

```yaml
apiVersion: bitnami.com/v1alpha1
kind: SealedSecret
metadata:
  name: db-credentials
spec:
  encryptedData:
    password: AgBy8hCi...  # Actually encrypted
```

Option 3: SOPS

```yaml
# Encrypted with SOPS - safe to commit
password: ENC[AES256_GCM,data:xxx,iv:yyy,tag:zzz,type:str]
```

---

### Anti-Pattern 4: Hardcoded Environment Values

**The Problem:**

```yaml
# DON'T DO THIS - Hardcoded for each environment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app
spec:
  replicas: 3  # What about dev? staging?
  template:
    spec:
      containers:
      - name: app
        env:
        - name: DATABASE_URL
          value: "postgres://prod-db:5432/app"  # Hardcoded!
        resources:
          limits:
            memory: "2Gi"  # Same for all envs?
```

**The Fix:**

```yaml
# base/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app
spec:
  replicas: 1  # Overridden per environment
  template:
    spec:
      containers:
      - name: app
        envFrom:
        - configMapRef:
            name: app-config

# overlays/production/kustomization.yaml
replicas:
  - name: app
    count: 3

# overlays/production/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: app-config
data:
  DATABASE_URL: "postgres://prod-db:5432/app"
```

---

## Workflow Anti-Patterns

### Anti-Pattern 5: Bypassing Git for "Quick Fixes"

**The Problem:**

```bash
# "It's just a quick fix, I'll update Git later"
kubectl apply -f hotfix.yaml
# ... 3 months later, no Git update, forgotten
```

**Why It's Bad:**

- "Later" never comes
- Creates undocumented drift
- Next sync overwrites the fix
- Knowledge lost

**The Fix:**

1. **Disable direct kubectl access** to production
2. **Enable self-heal** in ArgoCD:

   ```yaml
   syncPolicy:
     automated:
       selfHeal: true
   ```

3. **Fast-track PR process** for hotfixes
4. **Emergency runbook** that includes Git steps

---

### Anti-Pattern 6: No Sync Windows

**The Problem:**

```yaml
# Automated sync with no restrictions
syncPolicy:
  automated:
    prune: true
    selfHeal: true
# Deploys at 3 AM on Friday before a holiday...
```

**Why It's Bad:**

- Deployments during low-staffing periods
- No change control
- Compliance issues
- Incidents during off-hours

**The Fix:**

```yaml
# ArgoCD Project with sync windows
apiVersion: argoproj.io/v1alpha1
kind: AppProject
metadata:
  name: production
spec:
  syncWindows:
    # Allow syncs Monday-Thursday, 9 AM - 5 PM
    - kind: allow
      schedule: "0 9 * * 1-4"
      duration: 8h
      applications: ["*"]
    # Deny all syncs on weekends
    - kind: deny
      schedule: "0 0 * * 0,6"
      duration: 24h
      applications: ["*"]
```

---

### Anti-Pattern 7: Monolithic Applications

**The Problem:**

```yaml
# Single Application for entire platform
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: everything
spec:
  source:
    path: manifests/  # 500+ resources!
```

**Why It's Bad:**

- Single failure affects everything
- Long sync times
- Difficult to track changes
- No granular rollback
- Complex RBAC

**The Fix:**

```yaml
# App of Apps pattern
# Root application
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: platform
spec:
  source:
    path: apps/
---
# Individual applications
# apps/frontend.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: frontend
spec:
  source:
    path: manifests/frontend/
---
# apps/backend.yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: backend
spec:
  source:
    path: manifests/backend/
```

---

### Anti-Pattern 8: Ignoring Drift Detection

**The Problem:**

```yaml
# "OutOfSync is normal, we ignore it"
syncPolicy:
  automated: null  # No auto-sync
  # No alerts configured
  # No regular reconciliation
```

**Why It's Bad:**

- Security vulnerabilities unpatched
- Configuration creep
- Disaster recovery compromised
- Git becomes stale

**The Fix:**

1. **Configure alerts** for OutOfSync status
2. **Schedule regular syncs** even if manual
3. **Use diff commands** in CI:

   ```bash
   argocd app diff myapp --exit-code
   if [ $? -ne 0 ]; then
     echo "Drift detected!"
     # Send alert
   fi
   ```

4. **Review OutOfSync apps** weekly

---

## Architecture Anti-Patterns

### Anti-Pattern 9: Single Repository for All Environments

**The Problem:**

```
monorepo/
├── prod-secrets.yaml    # Production secrets
├── dev-secrets.yaml     # Dev secrets
├── manifests/           # Same access for all
```

**Why It's Bad:**

- Everyone with repo access sees production secrets
- No separation of duties
- Compliance violations
- Accidental production changes

**The Fix:**

```
# Separate repositories with different access
infra-config/          # Platform team only
├── applications/
└── base-values/

prod-values/           # Production team + approvals
├── secrets/
└── values/

dev-values/            # Developers
├── secrets/
└── values/
```

---

### Anti-Pattern 10: No Health Checks

**The Problem:**

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
spec:
  # Syncs and reports "Healthy" immediately
  # Doesn't wait for pods to be ready
```

**Why It's Bad:**

- Deployment appears successful when it's not
- Rolling updates continue despite failures
- No automatic rollback trigger

**The Fix:**

```yaml
# Proper health checks in Deployment
spec:
  template:
    spec:
      containers:
      - name: app
        readinessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 10
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 15
          periodSeconds: 20
```

```yaml
# ArgoCD sync with health check
syncPolicy:
  automated:
    prune: true
    selfHeal: true
  syncOptions:
    - CreateNamespace=true
# ArgoCD will wait for resources to be healthy
```

---

### Anti-Pattern 11: No Rollback Strategy

**The Problem:**

```bash
# On deployment failure:
# "Let me just push another commit to fix it"
# ... 30 minutes of debugging while production is down
```

**Why It's Bad:**

- Extended downtime
- Panic-driven changes
- More errors from rushed fixes

**The Fix:**

**Immediate rollback via Git:**

```bash
# Option 1: Revert commit
git revert HEAD
git push

# Option 2: Reset to known good
git reset --hard v1.2.2
git push --force  # If protected, use revert

# Option 3: ArgoCD CLI
argocd app rollback myapp 2  # Rollback to revision 2
```

**Automated rollback with Argo Rollouts:**

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
spec:
  strategy:
    canary:
      steps:
        - setWeight: 10
        - pause: {duration: 5m}
        - analysis:
            templates:
              - templateName: success-rate
            args:
              - name: service-name
                value: myapp
      # Automatic rollback on analysis failure
```

---

## Anti-Pattern Checklist

Before deploying, verify:

- [ ] No `kubectl apply` to production
- [ ] No `:latest` or mutable tags
- [ ] No secrets in Git (plain or base64)
- [ ] Environment-specific values in overlays
- [ ] Sync windows configured for production
- [ ] Applications are granular (not monolithic)
- [ ] Drift alerts configured
- [ ] Health checks defined
- [ ] Rollback procedure documented
- [ ] Repository access properly scoped

## Summary

| Anti-Pattern | Impact | Prevention |
|--------------|--------|------------|
| Imperative commands | Drift, no audit | Self-heal, block kubectl |
| Mutable tags | Unknown state | SemVer, digests |
| Secrets in Git | Security breach | External secrets |
| Hardcoded values | Inflexibility | Kustomize overlays |
| Bypassing Git | Lost changes | Self-heal, RBAC |
| No sync windows | Risky deployments | Project policies |
| Monolithic apps | Blast radius | App of Apps |
| Ignoring drift | Security risk | Alerts, audits |
| Single repo | Access issues | Multi-repo pattern |
| No health checks | False success | Probes, sync health |
| No rollback plan | Extended outages | Documented runbook |
