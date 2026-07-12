# GitOps Tooling Ecosystem

Comprehensive comparison of GitOps tools, their architectures, and use cases.

## Tool Comparison Overview

| Feature | ArgoCD | Flux | Kargo |
|---------|--------|------|-------|
| **Primary Focus** | Application deployment | Full GitOps toolkit | Progressive delivery |
| **UI** | Built-in web UI | Third-party (Weave GitOps) | Built-in web UI |
| **Multi-tenancy** | Projects, RBAC | Namespaced controllers | Projects, RBAC |
| **Helm Support** | Native | Native | Via ArgoCD integration |
| **Kustomize Support** | Native | Native | Via ArgoCD integration |
| **Multi-Cluster** | Centralized hub | Agent per cluster | Centralized |
| **GitOps Model** | Pull | Pull | Pull + Promotion |
| **CNCF Status** | Graduated | Graduated | Incubating |
| **Best For** | Visibility, multi-cluster | Lightweight, automation | Environment promotion |

---

## ArgoCD

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        ArgoCD Components                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐    ┌──────────────────┐                  │
│  │   API Server     │◄──►│    Web UI        │                  │
│  │   (gRPC/REST)    │    │                  │                  │
│  └────────┬─────────┘    └──────────────────┘                  │
│           │                                                     │
│           ▼                                                     │
│  ┌──────────────────┐    ┌──────────────────┐                  │
│  │ Repo Server      │    │ Redis            │                  │
│  │ (Git operations) │    │ (Caching)        │                  │
│  └────────┬─────────┘    └──────────────────┘                  │
│           │                                                     │
│           ▼                                                     │
│  ┌──────────────────┐    ┌──────────────────┐                  │
│  │ Application      │    │ Dex              │                  │
│  │ Controller       │    │ (SSO/OIDC)       │                  │
│  │ (Reconciliation) │    │                  │                  │
│  └──────────────────┘    └──────────────────┘                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Key Features

**Application CRD:**

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: myapp
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/org/repo.git
    targetRevision: HEAD
    path: manifests
  destination:
    server: https://kubernetes.default.svc
    namespace: myapp
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

**ApplicationSet (Multi-App Generation):**

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: cluster-apps
spec:
  generators:
    - clusters: {}  # All registered clusters
  template:
    spec:
      destination:
        server: '{{server}}'
```

### Strengths

- Rich web UI with visualization
- Multi-cluster management from single control plane
- SSO integration (OIDC, SAML, LDAP)
- ApplicationSets for templated deployments
- Extensive sync options and hooks
- Large community and ecosystem

### Considerations

- Resource-intensive for large deployments
- Single point of failure (hub cluster)
- Requires dedicated namespace

### Installation

**Standard Installation:**

```bash
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

**Azure Arc / AKS Managed Extension:**

```bash
# Register providers
az provider register --namespace Microsoft.KubernetesConfiguration
az extension add -n k8s-extension

# Install ArgoCD as managed extension
az k8s-extension create \
  --resource-group <rg> --cluster-name <cluster> \
  --cluster-type managedClusters \
  --name argocd \
  --extension-type Microsoft.ArgoCD \
  --release-train preview \
  --config deployWithHighAvailability=false
```

Benefits of Azure managed extension:

- Managed upgrades and maintenance
- Native Azure AD workload identity integration
- Consistent multi-cluster management via Azure Arc
- See `azure-arc-integration.md` for complete guide

---

## Flux

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Flux Components                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐    ┌──────────────────┐                  │
│  │ Source Controller│    │ Kustomize        │                  │
│  │ (Git, Helm, OCI) │    │ Controller       │                  │
│  └────────┬─────────┘    └────────┬─────────┘                  │
│           │                       │                             │
│           └───────────┬───────────┘                             │
│                       ▼                                         │
│  ┌──────────────────┐    ┌──────────────────┐                  │
│  │ Helm Controller  │    │ Notification     │                  │
│  │                  │    │ Controller       │                  │
│  └──────────────────┘    └──────────────────┘                  │
│                                                                 │
│  ┌──────────────────┐    ┌──────────────────┐                  │
│  │ Image Automation │    │ Image Reflector  │                  │
│  │ Controller       │    │ Controller       │                  │
│  └──────────────────┘    └──────────────────┘                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Key Features

**GitRepository Source:**

```yaml
apiVersion: source.toolkit.fluxcd.io/v1
kind: GitRepository
metadata:
  name: myapp
  namespace: flux-system
spec:
  interval: 1m
  url: https://github.com/org/repo.git
  ref:
    branch: main
  secretRef:
    name: git-credentials
```

**Kustomization (Flux CRD, not Kustomize):**

```yaml
apiVersion: kustomize.toolkit.fluxcd.io/v1
kind: Kustomization
metadata:
  name: myapp
  namespace: flux-system
spec:
  interval: 10m
  sourceRef:
    kind: GitRepository
    name: myapp
  path: ./manifests
  prune: true
  healthChecks:
    - apiVersion: apps/v1
      kind: Deployment
      name: myapp
      namespace: default
```

**HelmRelease:**

```yaml
apiVersion: helm.toolkit.fluxcd.io/v2beta1
kind: HelmRelease
metadata:
  name: nginx
  namespace: default
spec:
  interval: 5m
  chart:
    spec:
      chart: nginx
      version: '15.x'
      sourceRef:
        kind: HelmRepository
        name: bitnami
        namespace: flux-system
  values:
    replicaCount: 2
```

### Strengths

- Lightweight, modular architecture
- No single point of failure
- Native image automation (update manifests on new image)
- OCI registry support for storing configs
- Multi-tenancy via namespaces
- Terraform Controller integration

### Considerations

- No built-in UI (requires Weave GitOps or similar)
- Steeper learning curve for CRD relationships
- Each cluster needs its own Flux instance

### Installation

```bash
flux bootstrap github \
  --owner=my-org \
  --repository=fleet-infra \
  --branch=main \
  --path=clusters/my-cluster \
  --personal
```

---

## Kargo

### Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Kargo Components                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────┐    ┌──────────────────┐                  │
│  │   Warehouse      │    │   Stages         │                  │
│  │   (Artifact      │    │   (Promotion     │                  │
│  │    Discovery)    │    │    Targets)      │                  │
│  └────────┬─────────┘    └────────┬─────────┘                  │
│           │                       │                             │
│           └───────────┬───────────┘                             │
│                       │                                         │
│                       ▼                                         │
│  ┌──────────────────────────────────────────┐                  │
│  │              Freight                      │                  │
│  │  (Versioned artifact collection)          │                  │
│  └──────────────────────────────────────────┘                  │
│                       │                                         │
│                       ▼                                         │
│  ┌──────────────────────────────────────────┐                  │
│  │           Promotions                      │                  │
│  │  (Move Freight through Stages)            │                  │
│  └──────────────────────────────────────────┘                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Key Features

**Warehouse (Artifact Discovery):**

```yaml
apiVersion: kargo.akuity.io/v1alpha1
kind: Warehouse
metadata:
  name: main-warehouse
  namespace: myproject
spec:
  subscriptions:
    - image:
        repoURL: ghcr.io/org/myapp
        imageSelectionStrategy: SemVer
    - git:
        repoURL: https://github.com/org/config.git
        branch: main
```

**Stage (Promotion Target):**

```yaml
apiVersion: kargo.akuity.io/v1alpha1
kind: Stage
metadata:
  name: staging
  namespace: myproject
spec:
  requestedFreight:
    - origin:
        kind: Warehouse
        name: main-warehouse
      sources:
        direct: true
  promotionTemplate:
    spec:
      steps:
        - uses: git-clone
        - uses: kustomize-set-image
        - uses: git-commit
        - uses: git-push
        - uses: argocd-update
```

### Strengths

- Purpose-built for environment promotion
- Coordinates image + config updates
- Verification (testing) between stages
- Soak time requirements
- Works alongside ArgoCD
- Progressive delivery native

### Considerations

- Newer project (less mature)
- Requires ArgoCD or Flux for actual deployment
- Additional complexity layer

### Installation

```bash
helm install kargo \
  oci://ghcr.io/akuity/kargo-charts/kargo \
  --namespace kargo \
  --create-namespace
```

---

## Tool Selection Guide

### Decision Matrix

| Requirement | Best Tool |
|-------------|-----------|
| Need rich UI for developers | ArgoCD |
| Lightweight, minimal footprint | Flux |
| Multi-cluster from single pane | ArgoCD |
| Image automation (auto-update on new image) | Flux |
| Environment promotion workflows | Kargo |
| SSO/OIDC integration | ArgoCD |
| GitOps for Terraform | Flux (TF Controller) |
| Large enterprise with compliance | ArgoCD + Kargo |

### Architecture Recommendations

**Small Team (< 5 developers):**

```
Single cluster
    │
    └── Flux or ArgoCD (standalone)
```

**Medium Team (5-20 developers):**

```
ArgoCD (hub cluster)
    │
    ├── Dev cluster
    ├── Staging cluster
    └── Prod cluster
```

**Large Organization (20+ developers):**

```
Kargo + ArgoCD
    │
    ├── ArgoCD manages deployments
    └── Kargo manages promotions
        │
        ├── Dev stages
        ├── Staging stages (with verification)
        └── Prod stages (with approval gates)
```

---

## Complementary Tools

### Secrets Management

| Tool | Integration |
|------|-------------|
| External Secrets Operator | ArgoCD, Flux |
| Sealed Secrets | ArgoCD, Flux |
| SOPS | Flux native, ArgoCD plugin |
| HashiCorp Vault | Both via CSI or injector |

### Progressive Delivery

| Tool | Use Case |
|------|----------|
| Argo Rollouts | Canary, Blue-Green |
| Flagger | Works with Flux |
| Kargo | Multi-environment promotion |

### Policy Enforcement

| Tool | Purpose |
|------|---------|
| Kyverno | Kubernetes-native policies |
| OPA Gatekeeper | Rego-based policies |
| Datree | Pre-commit validation |

### Observability

| Tool | Purpose |
|------|---------|
| Prometheus | Metrics |
| Grafana | Dashboards |
| ArgoCD Notifications | Alerts |
| Flux Notification Controller | Alerts |

---

## Migration Paths

### From Helm/kubectl to ArgoCD

1. Export existing Helm releases as values files
2. Create ArgoCD Applications pointing to charts
3. Disable Helm Tiller/manual deployments
4. Enable automated sync

### From ArgoCD to Flux

1. Export Applications as Flux Kustomizations
2. Deploy Flux controllers
3. Migrate repo credentials
4. Decommission ArgoCD

### Adding Kargo to Existing ArgoCD

1. Install Kargo alongside ArgoCD
2. Create Warehouses for artifact sources
3. Create Stages matching your environments
4. Add `kargo.akuity.io/authorized-stage` annotations to ArgoCD Applications
5. Define promotion templates

---

## Quick CLI Reference

### ArgoCD

```bash
argocd app list
argocd app sync myapp
argocd app get myapp
argocd app diff myapp
argocd app history myapp
argocd app rollback myapp 2
```

### Flux

```bash
flux get kustomizations
flux reconcile kustomization myapp
flux get sources git
flux logs --kind=Kustomization --name=myapp
flux suspend kustomization myapp
flux resume kustomization myapp
```

### Kargo

```bash
kargo get stages --project myproject
kargo get freight --project myproject
kargo promote --project myproject --freight <id> --stage prod
kargo approve --project myproject --freight <id> --stage prod
```
