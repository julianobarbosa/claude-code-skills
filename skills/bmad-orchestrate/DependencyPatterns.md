# Dependency Patterns

Common patterns for detecting independent vs. dependent BMAD stories. Used by the Analyze workflow.

## Infrastructure Domain Classification

Stories that operate on different infrastructure domains are typically independent:

| Domain | Indicators | Examples |
|--------|-----------|----------|
| **Azure DevOps** | Pipeline YAML, build definitions, branch policies | CI pipelines, PR workflows |
| **Kubernetes/Helm** | Helm charts, K8s manifests, CRDs | ArgoCD, monitoring stacks, operators |
| **Terraform Networking** | VNet, subnets, peering, DNS | Network infrastructure |
| **Terraform Compute** | AKS, node pools, VM scale sets | Cluster provisioning |
| **Terraform Security** | Key Vault, managed identities, RBAC | Secret management, access control |
| **Terraform CI** | Azure DevOps provider resources | Repo, pipeline, policy resources |
| **Container Images** | Dockerfiles, ACR, image builds | Base images, app images |
| **Observability** | Grafana, Prometheus, Loki, Tempo | Dashboards, alerts, log collection |

## Independence Signals

Stories are likely **independent** when they:

1. **Touch different Terraform modules** — e.g., `terraform/modules/ci/` vs `terraform/modules/monitoring/` (safe for parallelization if using per-module state; shared state requires serialized `terraform apply`)
2. **Use different Terraform providers** — e.g., `azuredevops` provider vs `helm` provider
3. **Create files in different directories** — e.g., `pipelines/` vs `k8s/argocd/`
4. **Have no "Given X from Story N" in acceptance criteria**
5. **Operate at different layers** — e.g., infrastructure provisioning vs application deployment

## Dependency Signals

Stories are likely **dependent** when they:

1. **Acceptance criteria reference another story's output** — "Given pipeline from Story 4-2..."
2. **Both modify the same Terraform module** — same `main.tf` or `variables.tf`
3. **One extends what the other creates** — "extend the CI pipeline to also..."
4. **Share a Terraform state file** — the default in most projects; both stories' resources live in the same state, causing lock contention on `terraform apply`
5. **Have explicit ordering in the epics doc** — "after Story N.M is complete"

## Common Parallel Patterns in BMAD Projects

### Pattern: CI Pipeline + GitOps Deployment
```
CI Pipeline (Azure DevOps)  ──┐
                               ├── Image Push (depends on CI)
GitOps (ArgoCD on K8s)     ──┘   (depends on both)
```
**CI and GitOps are independent** until the image push story connects them.

### Pattern: Monitoring + Security
```
Monitoring Stack (Helm)     ── independent ──  Security Policies (Terraform)
```
Both deploy to the same cluster but touch completely different resources.

### Pattern: Multiple Namespace Setups
```
Namespace A setup  ── independent ──  Namespace B setup
```
Each creates its own resources in its own namespace.

### Pattern: Dashboard + Alert Rules
```
Dashboard creation  ── independent ──  Alert rule configuration
```
Both use Grafana but configure different resource types.

## Conflict Hotspots

Files that commonly cause merge conflicts when stories run in parallel:

| File | Why | Resolution Strategy |
|------|-----|-------------------|
| `sprint-status.yaml` | Every story updates its status line | Accept all status changes (different lines) |
| `terraform/main.tf` (root) | Module wiring additions | Accept both module blocks (additive) |
| `terraform/variables.tf` (root) | New variable declarations | Accept both variable blocks (additive) |
| `terraform/environments/*.tfvars` | New variable values | Accept both value blocks (additive) |
| `terraform/providers.tf` | New provider declarations | Deduplicate, keep one copy |
| `terraform/backend.tf` | State configuration | Should NOT differ — flag if it does |

## Terraform State Considerations

Most projects use a **single shared state file** (`key = "terraform.tfstate"`). This means `terraform apply` from parallel worktrees will cause state lock contention — only one apply can run at a time.

### Shared State (Default)

Check the backend configuration:
```bash
grep "key" terraform/backend.tf
```

If `key = "terraform.tfstate"` (single key for all modules):

- **BMAD steps that DON'T run `terraform apply`** are always safe to parallelize:
  - Create Story (CS) — only writes markdown spec files
  - Code Review (CR) — read-only analysis
  - Retrospective (ER) — only writes markdown
- **BMAD steps that DO run `terraform apply`** (Dev Story for Terraform modules) must be **serialized** — schedule them in sequential phases
- **Stories touching non-Terraform domains** (Helm charts, K8s manifests, pipeline YAML) do not hit Terraform state and remain fully parallelizable even during Dev Story

### Per-Module State (Alternative)

If the project uses per-module state (`key = "module-name/terraform.tfstate"`):
- Parallel stories modifying **different modules** are safe to parallelize
- Parallel stories modifying the **same module** still require serialization
