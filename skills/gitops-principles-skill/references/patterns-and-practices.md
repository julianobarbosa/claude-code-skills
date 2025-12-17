# GitOps Patterns and Practices

Comprehensive guide to repository structures, branching strategies, and deployment patterns for GitOps implementations.

## Repository Structure Patterns

### Pattern 1: Monorepo

All applications and environments in a single repository.

```
gitops-monorepo/
├── apps/
│   ├── frontend/
│   │   ├── base/
│   │   │   ├── deployment.yaml
│   │   │   ├── service.yaml
│   │   │   └── kustomization.yaml
│   │   └── overlays/
│   │       ├── dev/
│   │       │   ├── kustomization.yaml
│   │       │   └── replica-patch.yaml
│   │       ├── staging/
│   │       └── production/
│   ├── backend/
│   └── database/
├── infrastructure/
│   ├── cert-manager/
│   ├── ingress-nginx/
│   └── monitoring/
├── clusters/
│   ├── dev/
│   ├── staging/
│   └── production/
└── README.md
```

**Pros:**

- Single source of truth
- Easy cross-application changes
- Atomic multi-app deployments
- Simplified tooling

**Cons:**

- Large repository over time
- Broad access permissions needed
- CI/CD triggers for all changes
- Potential merge conflicts

**Best For:** Small-medium teams, tightly coupled applications

---

### Pattern 2: Polyrepo (Multi-Repository)

Separate repositories per application or concern.

```
# Application repositories
app-frontend/
├── src/
├── Dockerfile
└── k8s/
    ├── base/
    └── overlays/

app-backend/
├── src/
├── Dockerfile
└── k8s/

# Infrastructure repository
platform-infrastructure/
├── cert-manager/
├── ingress/
└── monitoring/

# Cluster configuration
cluster-config/
├── dev/
├── staging/
└── production/
```

**Pros:**

- Fine-grained access control
- Independent release cycles
- Smaller, focused repositories
- Team autonomy

**Cons:**

- Harder to coordinate changes
- More repositories to manage
- Complex dependency tracking
- Potential version drift

**Best For:** Large organizations, microservices, multiple teams

---

### Pattern 3: App of Apps (Umbrella Pattern)

A parent Application manages child Applications.

```yaml
# Root Application (apps/root-app.yaml)
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: root-app
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/org/gitops-config.git
    targetRevision: HEAD
    path: apps
  destination:
    server: https://kubernetes.default.svc
    namespace: argocd
```

```
gitops-config/
├── apps/
│   ├── frontend.yaml      # Application CR
│   ├── backend.yaml       # Application CR
│   ├── monitoring.yaml    # Application CR
│   └── kustomization.yaml
└── manifests/
    ├── frontend/
    ├── backend/
    └── monitoring/
```

**Benefits:**

- Hierarchical organization
- Single sync point
- Environment-specific app sets
- Easy to add/remove apps

---

### Pattern 4: Multi-Repository with Values Separation

Separates infrastructure definitions from environment-specific values.

```
# Repository 1: Infrastructure (infra-team/)
infra-team/
├── applications/
│   ├── nginx/
│   │   ├── applicationset.yaml
│   │   └── base-values.yaml
│   └── prometheus/
└── applicationsets/

# Repository 2: Values (argo-cd-helm-values/)
argo-cd-helm-values/
├── dev/
│   ├── nginx/
│   │   └── values.yaml
│   └── prometheus/
├── staging/
└── production/
```

**ApplicationSet with Multi-Source:**

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: nginx
spec:
  generators:
    - list:
        elements:
          - cluster: dev
            url: https://dev-cluster
          - cluster: prod
            url: https://prod-cluster
  template:
    spec:
      sources:
        - repoURL: https://charts.bitnami.com/bitnami
          chart: nginx
          targetRevision: 15.0.0
          helm:
            valueFiles:
              - $values/{{cluster}}/nginx/values.yaml
        - repoURL: https://github.com/org/argo-cd-helm-values.git
          targetRevision: main
          ref: values
```

**Benefits:**

- Security boundary between repos
- Different RBAC per environment
- Separation of concerns
- Easier secret management

---

## Branching Strategies

### Strategy 1: Environment Branches

```
main ──────────────────────────────────────► Production
  │
  └── staging ─────────────────────────────► Staging
        │
        └── develop ───────────────────────► Development
```

**Workflow:**

1. Develop on `develop` branch
2. Merge to `staging` for testing
3. Merge to `main` for production

**Pros:** Clear environment mapping
**Cons:** Merge conflicts, branch maintenance

---

### Strategy 2: Trunk-Based with Directory Overlays

```
main (single branch)
├── base/                 # Shared configuration
├── overlays/
│   ├── dev/             # Dev-specific patches
│   ├── staging/         # Staging-specific patches
│   └── production/      # Prod-specific patches
```

**Workflow:**

1. All changes go to `main`
2. Kustomize overlays handle environment differences
3. GitOps controller watches specific paths

**Pros:** Simple, fewer branches, atomic changes
**Cons:** Requires good overlay discipline

---

### Strategy 3: Release Branches

```
main
  │
  ├── release/v1.0.0 ──► Production (v1.0)
  ├── release/v1.1.0 ──► Production (v1.1)
  └── release/v2.0.0 ──► Production (v2.0)
```

**Workflow:**

1. Develop on `main`
2. Create release branch for deployment
3. Hotfixes on release branches
4. Cherry-pick to main

**Pros:** Clear versioning, rollback by switching branches
**Cons:** Branch proliferation, merge complexity

---

### Strategy 4: GitFlow for GitOps

```
main ────────────────────────────────────────► Production
  ▲
  │
  │ merge
  │
develop ─────────────────────────────────────► Development
  ▲     ▲
  │     │
feature/  release/
branches  branches
```

**Best For:** Complex release processes, multiple parallel versions

---

## Deployment Patterns

### Progressive Delivery Patterns

#### Blue-Green Deployment

```yaml
# Blue deployment (current production)
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: myapp-blue
spec:
  source:
    path: manifests/blue
  destination:
    namespace: myapp-blue

---
# Green deployment (new version)
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: myapp-green
spec:
  source:
    path: manifests/green
  destination:
    namespace: myapp-green
```

**Traffic Switch:**

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: myapp
spec:
  rules:
    - host: myapp.example.com
      http:
        paths:
          - path: /
            backend:
              service:
                name: myapp-green  # Switch from blue to green
                port:
                  number: 80
```

#### Canary Deployment

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: myapp
spec:
  replicas: 10
  strategy:
    canary:
      steps:
        - setWeight: 10        # 10% traffic to canary
        - pause: {duration: 5m}
        - setWeight: 30
        - pause: {duration: 10m}
        - setWeight: 50
        - pause: {duration: 10m}
      trafficRouting:
        nginx:
          stableIngress: myapp-stable
```

#### Wave-Based Deployment

```yaml
# Wave 1: Infrastructure
metadata:
  annotations:
    argocd.argoproj.io/sync-wave: "-1"

# Wave 2: Database migrations
metadata:
  annotations:
    argocd.argoproj.io/sync-wave: "0"

# Wave 3: Application
metadata:
  annotations:
    argocd.argoproj.io/sync-wave: "1"

# Wave 4: Post-deployment jobs
metadata:
  annotations:
    argocd.argoproj.io/sync-wave: "2"
```

---

### Multi-Cluster Patterns

#### Hub and Spoke

```
                    ┌─────────────────┐
                    │   Hub Cluster   │
                    │   (ArgoCD)      │
                    └────────┬────────┘
                             │
            ┌────────────────┼────────────────┐
            │                │                │
            ▼                ▼                ▼
    ┌───────────┐    ┌───────────┐    ┌───────────┐
    │  Spoke 1  │    │  Spoke 2  │    │  Spoke 3  │
    │  (Dev)    │    │  (Staging)│    │  (Prod)   │
    └───────────┘    └───────────┘    └───────────┘
```

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: myapp
  namespace: argocd
spec:
  generators:
    - clusters:
        selector:
          matchLabels:
            environment: production
  template:
    spec:
      destination:
        server: '{{server}}'
        namespace: myapp
```

#### Pull-Based Multi-Cluster

Each cluster has its own GitOps controller:

```
Git Repository
      │
      ├──────────────────┬──────────────────┐
      │                  │                  │
      ▼                  ▼                  ▼
┌───────────┐    ┌───────────┐    ┌───────────┐
│ Cluster 1 │    │ Cluster 2 │    │ Cluster 3 │
│ ArgoCD    │    │ Flux      │    │ ArgoCD    │
└───────────┘    └───────────┘    └───────────┘
```

---

### Environment Promotion Pattern

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│     Dev      │────►│   Staging    │────►│  Production  │
│              │     │              │     │              │
│ Auto-deploy  │     │ Auto-deploy  │     │ Manual gate  │
│ from main    │     │ after dev    │     │ approval     │
└──────────────┘     └──────────────┘     └──────────────┘
```

**Kargo Implementation:**

```yaml
apiVersion: kargo.akuity.io/v1alpha1
kind: Stage
metadata:
  name: production
spec:
  requestedFreight:
    - origin:
        kind: Warehouse
        name: main-warehouse
      sources:
        stages:
          - staging
        requiredSoakTime: 24h  # Must be stable in staging for 24h
```

---

## Best Practices Summary

### Repository Best Practices

| Practice | Description |
|----------|-------------|
| README in every directory | Document purpose and ownership |
| CODEOWNERS file | Define approval requirements |
| Branch protection | Require PR reviews |
| Semantic versioning | For releases and tags |
| Gitignore | Exclude generated files |

### Branching Best Practices

| Practice | Description |
|----------|-------------|
| Keep main deployable | Always production-ready |
| Short-lived branches | Reduce merge conflicts |
| Descriptive branch names | `feature/add-redis`, `fix/memory-leak` |
| Squash on merge | Clean history |

### Deployment Best Practices

| Practice | Description |
|----------|-------------|
| Progressive rollouts | Never deploy 100% immediately |
| Automated rollback | On health check failure |
| Sync windows | Control when deployments happen |
| Resource quotas | Prevent runaway deployments |

## Quick Reference

### Choose Your Pattern

| Scenario | Recommended Pattern |
|----------|-------------------|
| Small team, few apps | Monorepo + trunk-based |
| Large org, many teams | Polyrepo + App of Apps |
| Strict compliance | Multi-repo with values separation |
| Rapid iteration | Trunk-based + overlays |
| Complex releases | GitFlow or release branches |
