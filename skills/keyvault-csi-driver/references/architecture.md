# CSI Driver Architecture Reference

## Component Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Secrets Store CSI Driver Stack                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                            Control Plane                                 ││
│  │  ┌──────────────────┐   ┌──────────────────┐   ┌──────────────────┐    ││
│  │  │ SecretProvider   │   │ K8s API Server   │   │  ArgoCD          │    ││
│  │  │ Class (CRD)      │   │ (Secret Sync)    │   │  (GitOps Deploy) │    ││
│  │  └────────┬─────────┘   └────────▲─────────┘   └──────────────────┘    ││
│  │           │                      │                                       ││
│  └───────────│──────────────────────│───────────────────────────────────────┘│
│              │                      │                                        │
│  ┌───────────▼──────────────────────│───────────────────────────────────────┐│
│  │                             Node Level                                    ││
│  │  ┌──────────────────────────────────────────────────────────────────┐   ││
│  │  │               secrets-store-csi-driver (DaemonSet)                │   ││
│  │  │  - Runs on every node                                             │   ││
│  │  │  - Handles CSI volume mount requests                              │   ││
│  │  │  - Syncs mounted secrets to K8s Secrets (if configured)           │   ││
│  │  │  - Manages secret rotation                                        │   ││
│  │  └────────────────────────────┬─────────────────────────────────────┘   ││
│  │                               │                                          ││
│  │  ┌────────────────────────────▼─────────────────────────────────────┐   ││
│  │  │          secrets-store-csi-driver-provider-azure (DaemonSet)      │   ││
│  │  │  - Runs on every node alongside CSI driver                        │   ││
│  │  │  - Communicates with Azure Key Vault                              │   ││
│  │  │  - Handles authentication via Managed Identity                    │   ││
│  │  │  - Retrieves secrets/keys/certificates                            │   ││
│  │  └────────────────────────────┬─────────────────────────────────────┘   ││
│  │                               │                                          ││
│  └───────────────────────────────│──────────────────────────────────────────┘│
│                                  │                                           │
│  ┌───────────────────────────────▼──────────────────────────────────────────┐│
│  │                           Azure Services                                  ││
│  │  ┌──────────────────┐                      ┌──────────────────────────┐  ││
│  │  │ Azure Key Vault  │◄────────────────────│ Azure Managed Identity   │  ││
│  │  │ - Secrets        │   Authentication    │ - User-Assigned          │  ││
│  │  │ - Keys           │                     │ - Or Workload Identity   │  ││
│  │  │ - Certificates   │                     │                          │  ││
│  │  └──────────────────┘                     └──────────────────────────┘  ││
│  └──────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Request Flow

### 1. Pod Creation with CSI Volume

```
┌──────────┐     ┌──────────┐     ┌──────────────┐     ┌──────────────┐     ┌─────────┐
│   User   │     │ Kubelet  │     │  CSI Driver  │     │ Azure        │     │  Azure  │
│ (Deploy) │     │          │     │              │     │ Provider     │     │  KeyVlt │
└────┬─────┘     └────┬─────┘     └──────┬───────┘     └──────┬───────┘     └────┬────┘
     │                │                   │                    │                  │
     │ Create Pod     │                   │                    │                  │
     │ with CSI Vol   │                   │                    │                  │
     │───────────────>│                   │                    │                  │
     │                │                   │                    │                  │
     │                │ NodeStageVolume   │                    │                  │
     │                │──────────────────>│                    │                  │
     │                │                   │                    │                  │
     │                │                   │ Get Secrets        │                  │
     │                │                   │───────────────────>│                  │
     │                │                   │                    │                  │
     │                │                   │                    │ Auth + Fetch     │
     │                │                   │                    │─────────────────>│
     │                │                   │                    │                  │
     │                │                   │                    │<─────────────────│
     │                │                   │                    │   Secrets        │
     │                │                   │<───────────────────│                  │
     │                │                   │   Secret Data      │                  │
     │                │                   │                    │                  │
     │                │                   │ Write to tmpfs     │                  │
     │                │                   │ at mount path      │                  │
     │                │<──────────────────│                    │                  │
     │                │   Volume Ready    │                    │                  │
     │                │                   │                    │                  │
     │                │ (Optional) Sync   │                    │                  │
     │                │ to K8s Secret     │                    │                  │
     │                │                   │                    │                  │
     │<───────────────│                   │                    │                  │
     │  Pod Running   │                   │                    │                  │
     │                │                   │                    │                  │
```

### 2. Secret Rotation Flow

```
┌──────────────┐     ┌──────────────┐     ┌─────────┐
│  CSI Driver  │     │ Azure        │     │  Azure  │
│  (Rotation   │     │ Provider     │     │  KeyVlt │
│   Reconciler)│     │              │     │         │
└──────┬───────┘     └──────┬───────┘     └────┬────┘
       │                    │                   │
       │ Poll Interval      │                   │
       │ (default: 2m)      │                   │
       │                    │                   │
       │ Check for Updates  │                   │
       │───────────────────>│                   │
       │                    │                   │
       │                    │ Fetch Latest      │
       │                    │──────────────────>│
       │                    │                   │
       │                    │<──────────────────│
       │                    │  Secret (v2)      │
       │<───────────────────│                   │
       │   New Version      │                   │
       │                    │                   │
       │ Update mounted     │                   │
       │ files in-place     │                   │
       │                    │                   │
       │ (If secretObjects) │                   │
       │ Update K8s Secret  │                   │
       │                    │                   │
```

## CRD Structure: SecretProviderClass

```yaml
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: example             # Referenced by pod volume
  namespace: default        # Must match pod namespace
spec:
  provider: azure           # Provider type

  parameters:               # Provider-specific configuration
    # Authentication
    usePodIdentity: "false"
    useVMManagedIdentity: "true"
    userAssignedIdentityID: "client-id-of-managed-identity"

    # Key Vault Configuration
    keyvaultName: "vault-name"
    cloudName: "AzurePublicCloud"  # Or AzureUSGovernment, AzureChinaCloud
    tenantId: "tenant-id"

    # Objects to retrieve
    objects: |
      array:
        - |
          objectName: "secret-name"      # Name in Key Vault
          objectType: "secret"           # secret, key, or cert
          objectAlias: "MOUNT_NAME"      # Optional: filename when mounted
          objectVersion: ""              # Optional: specific version
          objectEncoding: "utf-8"        # Optional: base64, hex, utf-8
          filePermission: "0644"         # Optional: file permissions

  # Optional: Create K8s Secrets from mounted content
  secretObjects:
    - secretName: k8s-secret-name       # Name of K8s Secret to create
      type: Opaque                       # Secret type
      data:
        - objectName: "MOUNT_NAME"       # Must match objectAlias above
          key: "key-in-secret"           # Key name in K8s Secret
```

## Authentication Methods

### User-Assigned Managed Identity (Recommended)

```yaml
parameters:
  usePodIdentity: "false"
  useVMManagedIdentity: "true"
  userAssignedIdentityID: "<client-id>"  # NOT object-id
```

**How it works:**

1. AKS cluster has a user-assigned managed identity attached to node VMSS
2. Provider uses this identity to authenticate to Key Vault
3. Identity must have Key Vault access policies or RBAC role

### Workload Identity (Modern Alternative)

```yaml
parameters:
  usePodIdentity: "false"
  clientID: "<managed-identity-client-id>"
```

**Requirements:**

- AKS cluster with OIDC issuer enabled
- Workload identity enabled
- Federated credential configured
- Service account annotated

### Pod Identity (Deprecated)

```yaml
parameters:
  usePodIdentity: "true"
```

**Note:** Pod Identity is deprecated as of October 2022. Use Workload Identity instead.

## Resource Requirements

### CSI Driver DaemonSet

```yaml
resources:
  requests:
    cpu: 50m
    memory: 100Mi
  limits:
    cpu: 200m
    memory: 200Mi
```

### Azure Provider DaemonSet

```yaml
resources:
  requests:
    cpu: 50m
    memory: 100Mi
  limits:
    cpu: 200m
    memory: 200Mi
```

## Ports and Endpoints

| Component | Port | Purpose |
|-----------|------|---------|
| CSI Driver | 9808 | Liveness probe |
| CSI Driver | 8095 | Metrics |
| Azure Provider | 8989 | Health probe |
| Azure Provider | 8898 | Metrics |

## Metrics Available

### CSI Driver Metrics (port 8095)

- `csi_operations_seconds` - CSI operation latency
- `total_node_publish` - Volume publish operations
- `total_node_unpublish` - Volume unpublish operations
- `total_sync_k8s_secret` - K8s secret sync operations

### Azure Provider Metrics (port 8898)

- `keyvault_request` - Key Vault request count
- `keyvault_request_duration_seconds` - Request latency
- `total_rotation_reconcile` - Rotation reconciliation count
- `total_rotation_reconcile_error` - Rotation errors
