---
name: k8s-clusters
description: Hypera Azure AKS infrastructure reference. Use when user mentions cluster names (cafehyna, loyalty, sonora, painelclientes), needs kubeconfig paths, asks about spot tolerations, cert-manager issuers, or resource definition policies. Critical: Hub cluster Azure name differs from developer name.
---

# Kubernetes Clusters Skill

## Critical: Hub Cluster Naming

| Context | cafehyna-hub | painelclientes-hub |
|---------|--------------|-------------------|
| Developer/Docs | `cafehyna-hub` | `painelclientes-hub` |
| Azure CLI | `aks-cafehyna-default` | `akspainelclienteshub` |

Always use Azure name in `az` commands.

## Cluster Lookup

Format: `developer-name` → Azure: `azure-name`, RG: `resource-group`, Config: `kubeconfig`

**Cafehyna**

- `cafehyna-dev` → Azure: `aks-cafehyna-dev-hlg`, RG: `RS_Hypera_Cafehyna_Dev`, Config: `aks-rg-hypera-cafehyna-dev-config`, Spot: Yes
- `cafehyna-hub` → Azure: `aks-cafehyna-default`, RG: `rs_hypera_cafehyna`, Config: `aks-rg-hypera-cafehyna-hub-config`, Spot: No
- `cafehyna-prd` → Azure: `aks-cafehyna-prd`, RG: `rs_hypera_cafehyna_prd`, Config: `aks-rg-hypera-cafehyna-prd-config`, Spot: No

**Loyalty**

- `loyalty-dev` → Azure: `Loyalty_AKS-QAS`, RG: `RS_Hypera_Loyalty_AKS_QAS`, Config: `aks-rg-hypera-loyalty-dev-config`, Spot: Yes
- `loyalty-prd` → Azure: `Loyalty_AKS-PRD`, RG: `RS_Hypera_Loyalty_AKS_PRD`, Config: `aks-rg-hypera-loyalty-prd-config`, Spot: No

**Other**

- `sonora-dev` → Azure: `AKS-Hypera-Sonora-Dev-Hlg`, RG: `rg-hypera-sonora-dev`, Config: `aks-rg-hypera-sonora-dev-config`, Spot: Yes
- `painelclientes-dev` → Azure: `akspainelclientedev`, RG: `rg-hypera-painelclientes-dev`, Config: `aks-rg-hypera-painelclientes-dev-config`, Spot: Yes, Region: East US2

All kubeconfigs at `~/.kube/<config-name>`.

## Mandatory Policies

### 1. Spot Tolerations & Node Affinity (dev clusters only)

Required toleration for ALL pods on spot clusters:

```yaml
tolerations:
  - key: kubernetes.azure.com/scalesetpriority
    operator: Equal
    value: "spot"
    effect: NoSchedule
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
        - matchExpressions:
            - key: agentpool
              operator: In
              values: ["cafedevspot"]  # cafehyna-dev: only use cafedevspot, NOT cafedev
```

**Important**: The `cafedev` nodepool has `CriticalAddonsOnly` taint and should NOT be used for workloads. Always use the spot nodepool (e.g., `cafedevspot`, `pcdevspot`).

Without this → pods stuck `Pending`. Use `scripts/patch-tolerations.sh` to fix.

### 2. Resource Definitions (all clusters)

| Resource | Requirement |
|----------|-------------|
| CPU requests | ✅ Required |
| CPU limits | ❌ Forbidden (causes throttling) |
| Memory requests | ✅ Required |
| Memory limits | ✅ Required, must equal requests |

### 3. cert-manager ClusterIssuers

| Environment | Issuer |
|-------------|--------|
| prd, hub | `letsencrypt-prod-cloudflare` |
| dev | `letsencrypt-staging-cloudflare` |

❌ Never use issuers without `-cloudflare` suffix.

### 4. Storage Class Policy (CRITICAL - ALL WORKLOADS)

**MANDATORY for ALL stateful workloads across ALL clusters:**

| Access Mode | StorageClass | Use Case |
|-------------|--------------|----------|
| ReadWriteOnce (RWO) | `managed-premium-zrs` | Databases, caches, single-pod storage |
| ReadWriteMany (RWX) | `azurefile-csi-premium` | Shared storage, media files, multi-pod access |

**Rules:**

| Rule | Requirement |
|------|-------------|
| Helm values `storageClass` | ✅ MUST be explicitly set (never omit or use null) |
| `storageClass: null` or omitted | ❌ FORBIDDEN - causes zone affinity conflicts |
| Default StorageClass reliance | ❌ FORBIDDEN - not guaranteed across clusters |

**Why Zone-Redundant Storage (ZRS)?**

- **High Availability**: Synchronous replication across 3 availability zones
- **Zero RPO**: No data loss during zone failures
- **12 nines durability**: 99.9999999999% data durability
- **No zone conflicts**: Prevents "volume node affinity conflict" errors
- **Proper binding**: Works with `WaitForFirstConsumer` binding mode

**This applies to ALL workloads including:**

- Observability: Loki, Tempo, Mimir, Prometheus, Grafana
- Security: DefectDojo, SonarQube, Vault
- Databases: PostgreSQL, MySQL, MongoDB, Redis
- Message Queues: RabbitMQ, Kafka
- Any Helm chart with persistence enabled
- Any StatefulSet, any PersistentVolumeClaim

**Creating managed-premium-zrs StorageClass**

Run on each cluster that doesn't have it:

```bash
# Quick check and create
.claude/skills/k8s-clusters/scripts/create-storageclass.sh <cluster-name>

# Or manually:
KUBECONFIG=~/.kube/<config> kubectl apply -f - <<EOF
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: managed-premium-zrs
provisioner: disk.csi.azure.com
parameters:
  skuName: Premium_ZRS
  kind: Managed
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
EOF
```

**Example Helm values pattern:**

```yaml
# For databases, caches (RWO)
persistence:
  storageClass: managed-premium-zrs  # NEVER omit this

# For shared/media storage (RWX)
persistence:
  storageClass: azurefile-csi-premium
  accessMode: ReadWriteMany
```

## Quick Troubleshooting

| Symptom | Fix |
|---------|-----|
| Pod Pending on dev | Add spot toleration + nodeAffinity to `cafedevspot` |
| Volume node affinity conflict | Set explicit `storageClass: managed-premium-zrs`, delete stuck PVC |
| PVC stuck Pending | 1) Check StorageClass exists 2) Run `create-storageclass.sh` 3) Delete and recreate PVC |
| StorageClass not found | Run `scripts/create-storageclass.sh <cluster>` |
| Certificate stuck | Change to `*-cloudflare` issuer |
| Connection timeout | Check VPN, run `scripts/diagnose.sh` |
| Auth failed | `az login` then re-get credentials |
| ArgoCD sync error: `podReplacementPolicy: field not declared in schema` | See ArgoCD SSA troubleshooting below |

## ArgoCD Server-Side Apply (SSA) Troubleshooting

### Issue: `podReplacementPolicy` / `status.terminating` Schema Error

**Error message:**

```
ComparisonError: error calculating structured merge diff: error building typed value from live resource:
errors: .spec.podReplacementPolicy: field not declared in schema .status.terminating: field not declared in schema
```

**Root Cause:** ArgoCD issue [#18778](https://github.com/argoproj/argo-cd/issues/18778). Kubernetes 1.29+ Job resources have new fields (`podReplacementPolicy`, `status.terminating`) that ArgoCD's embedded schema doesn't recognize when using Server-Side Diff.

**Important:** `ignoreDifferences` does NOT work for this issue because the error occurs during schema validation before diff comparison.

**Solution:** Disable Server-Side Diff at the Application level:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application  # or ApplicationSet template
metadata:
  annotations:
    # Workaround for ArgoCD issue #18778
    argocd.argoproj.io/compare-options: ServerSideDiff=false
```

**For ApplicationSets:**

```yaml
spec:
  template:
    metadata:
      annotations:
        argocd.argoproj.io/compare-options: ServerSideDiff=false
```

**Affected resources:** Any application deploying Jobs, CronJobs, or Helm charts that create Jobs (e.g., DefectDojo initializer, database migrations).

**References:**

- [ArgoCD Issue #18778](https://github.com/argoproj/argo-cd/issues/18778)
- [ArgoCD Diff Strategies](https://argo-cd.readthedocs.io/en/stable/user-guide/diff-strategies/)

## Scripts

- `scripts/patch-tolerations.sh <cluster> <deployment> <namespace>` - Add spot tolerations
- `scripts/diagnose.sh <cluster>` - Connection diagnostics
- `scripts/get-creds.sh <cluster>` - Refresh kubeconfig
- `scripts/create-storageclass.sh <cluster>` - Create managed-premium-zrs StorageClass

## Detailed Reference

For API endpoints, Key Vaults, nodepool details, and extended troubleshooting:

- **[references/clusters-detail.md](references/clusters-detail.md)**
