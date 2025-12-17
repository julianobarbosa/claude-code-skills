# GitOps Core Principles

Deep dive into the four foundational principles of GitOps as defined by the OpenGitOps project (CNCF).

## The Four Pillars of GitOps

### Principle 1: Declarative

> "A system managed by GitOps must have its desired state expressed declaratively."

#### What This Means

- **Declarative**: Describe WHAT you want, not HOW to achieve it
- **Imperative (opposite)**: Step-by-step instructions to reach a state

#### Examples

**Declarative (GitOps):**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nginx
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nginx
  template:
    spec:
      containers:
      - name: nginx
        image: nginx:1.21
        resources:
          limits:
            memory: "128Mi"
            cpu: "500m"
```

**Imperative (NOT GitOps):**

```bash
kubectl run nginx --image=nginx:1.21
kubectl scale deployment nginx --replicas=3
kubectl set resources deployment nginx -c=nginx --limits=memory=128Mi,cpu=500m
```

#### Why Declarative Matters

| Benefit | Description |
|---------|-------------|
| Reproducibility | Same manifest = same result |
| Auditability | Changes tracked in Git |
| Comparison | Easy diff between desired and actual |
| Recovery | Reapply manifest to restore state |

#### Declarative Tools

| Tool | Purpose |
|------|---------|
| Kubernetes YAML | Native resource definitions |
| Kustomize | Overlay-based customization |
| Helm | Templated charts |
| Jsonnet | Data templating language |
| CUE | Configuration unification |
| Terraform | Infrastructure as Code |

---

### Principle 2: Versioned and Immutable

> "Desired state is stored in a way that enforces immutability, versioning, and retains a complete version history."

#### Git as the Version Control System

Git provides:

- **Immutability**: Commits are content-addressed (SHA)
- **Versioning**: Full history of changes
- **Branching**: Parallel development streams
- **Audit trail**: Who changed what, when, why

#### Version Control Best Practices

```bash
# Good commit message structure
git commit -m "feat(nginx): increase replicas to 3 for high availability

- Scaling nginx deployment from 1 to 3 replicas
- Adding pod anti-affinity for distribution
- Tested in staging environment

Relates to: TICKET-123"
```

#### Immutability Patterns

**Container Images:**

```yaml
# GOOD: Immutable tag
image: nginx:1.21.6

# BAD: Mutable tag
image: nginx:latest
```

**Git References:**

```yaml
# GOOD: Specific commit or tag
targetRevision: v1.2.3
targetRevision: abc123def

# RISKY: Branch (mutable)
targetRevision: main
```

#### Version History Benefits

```bash
# View deployment history
git log --oneline manifests/

# Compare versions
git diff v1.0.0..v1.1.0 -- manifests/

# Find when change was introduced
git bisect start
git bisect bad HEAD
git bisect good v1.0.0
```

---

### Principle 3: Pulled Automatically

> "Software agents automatically pull the desired state declarations from the source."

#### Pull vs Push Model

```
┌──────────────────────────────────────────────────────────────────┐
│                     PUSH MODEL (Traditional)                      │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│   CI/CD Server                                                   │
│       │                                                          │
│       │ kubectl apply                                            │
│       │ (requires cluster credentials)                           │
│       ▼                                                          │
│   Kubernetes Cluster                                             │
│                                                                  │
│   Issues:                                                        │
│   - Credentials exposed in CI                                    │
│   - No continuous reconciliation                                 │
│   - Drift goes undetected                                        │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                     PULL MODEL (GitOps)                           │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Git Repository ◄──────────────┐                                │
│       │                         │                                │
│       │ (pull/watch)            │ Developer pushes               │
│       ▼                         │                                │
│   GitOps Controller ────────────┘                                │
│   (inside cluster)                                               │
│       │                                                          │
│       │ kubectl apply                                            │
│       │ (internal credentials)                                   │
│       ▼                                                          │
│   Kubernetes Cluster                                             │
│                                                                  │
│   Benefits:                                                      │
│   - Credentials stay in cluster                                  │
│   - Continuous reconciliation                                    │
│   - Automatic drift detection                                    │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

#### Automatic Pull Mechanisms

**Polling (Default):**

```yaml
# ArgoCD application controller settings
spec:
  syncPolicy:
    automated: {}
# Default poll interval: 3 minutes
```

**Webhook (Recommended for Production):**

```yaml
# Configure webhook for instant updates
apiVersion: v1
kind: Secret
metadata:
  name: argocd-webhook
  namespace: argocd
data:
  github.secret: <base64-encoded-secret>
```

**Git Generators (ApplicationSets):**

```yaml
spec:
  generators:
    - git:
        repoURL: https://github.com/org/repo.git
        revision: HEAD
        directories:
          - path: apps/*
```

#### Security Benefits of Pull

| Aspect | Push Model | Pull Model |
|--------|------------|------------|
| Credential Location | CI server | Cluster only |
| Attack Surface | External access required | Internal only |
| Audit | CI logs | Git + controller logs |
| Blast Radius | CI compromise = cluster access | Limited to controller |

---

### Principle 4: Continuously Reconciled

> "Software agents continuously observe actual system state and attempt to apply the desired state."

#### The Reconciliation Loop

```
┌─────────────────────────────────────────────────────────────────┐
│                    CONTINUOUS RECONCILIATION                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│   ┌──────────────┐                                              │
│   │ Git (Desired)│                                              │
│   │    State     │                                              │
│   └──────┬───────┘                                              │
│          │                                                      │
│          ▼                                                      │
│   ┌──────────────┐     ┌──────────────┐                        │
│   │   Compare    │◄────│   Observe    │                        │
│   │    (Diff)    │     │    Actual    │                        │
│   └──────┬───────┘     └──────┬───────┘                        │
│          │                    │                                 │
│          │                    │                                 │
│          ▼                    │                                 │
│   ┌──────────────┐           │                                 │
│   │    Apply     │───────────┘                                  │
│   │   Changes    │     Repeat continuously                      │
│   └──────────────┘                                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### Self-Healing Capabilities

```yaml
spec:
  syncPolicy:
    automated:
      selfHeal: true    # Automatically revert manual changes
      prune: true       # Remove resources not in Git
```

**Self-Heal Scenarios:**

| Manual Change | GitOps Response |
|---------------|-----------------|
| `kubectl scale deploy --replicas=1` | Restored to Git-defined replicas |
| `kubectl delete pod` | Pod recreated (normal K8s) |
| `kubectl edit configmap` | Reverted to Git version |
| `kubectl delete deployment` | Deployment recreated |

#### Drift Detection

**Types of Drift:**

1. **Configuration Drift**: Resource spec differs from Git
2. **State Drift**: Resource status unhealthy
3. **Missing Resources**: Resources deleted manually
4. **Extra Resources**: Resources created outside Git

**Detecting Drift:**

```bash
# ArgoCD diff command
argocd app diff myapp

# Flux reconciliation
flux reconcile kustomization myapp --with-source
```

#### Reconciliation Intervals

| Tool | Default Interval | Configurable |
|------|------------------|--------------|
| ArgoCD | 3 minutes | Yes, via `timeout.reconciliation` |
| Flux | 10 minutes | Yes, per Kustomization/HelmRelease |
| Kargo | Event-driven | Webhook-based |

**Example Configuration:**

```yaml
# ArgoCD ConfigMap
apiVersion: v1
kind: ConfigMap
metadata:
  name: argocd-cm
data:
  timeout.reconciliation: 180s  # 3 minutes
```

```yaml
# Flux Kustomization
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
spec:
  interval: 5m  # Check every 5 minutes
```

---

## Putting It All Together

### The Complete GitOps Workflow

```
1. Developer creates PR with DECLARATIVE changes
                    │
                    ▼
2. Changes reviewed and VERSIONED in Git
                    │
                    ▼
3. GitOps controller PULLS changes automatically
                    │
                    ▼
4. Controller CONTINUOUSLY RECONCILES cluster state
                    │
                    ▼
5. Drift detected? → Auto-heal OR alert
```

### Compliance with Principles Checklist

- [ ] All configurations are YAML/HCL (declarative)
- [ ] All changes go through Git PR (versioned)
- [ ] No `kubectl apply` from laptops (pulled)
- [ ] Self-heal enabled (continuously reconciled)
- [ ] Drift alerts configured (continuously reconciled)

## References

- [OpenGitOps Principles](https://opengitops.dev/principles)
- [CNCF GitOps Working Group](https://github.com/cncf/tag-app-delivery/tree/main/gitops-wg)
- [GitOps Principles v1.0.0](https://github.com/open-gitops/documents/blob/main/PRINCIPLES.md)
