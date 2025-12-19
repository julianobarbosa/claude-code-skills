# Azure Arc GitOps Integration with ArgoCD

Comprehensive guide for deploying and managing ArgoCD via Azure Arc-enabled
Kubernetes and Azure Kubernetes Service (AKS) using Azure's managed GitOps
extension.

## Overview

Azure provides a managed ArgoCD experience through the **Microsoft.ArgoCD**
cluster extension. This enables GitOps workflows on:

- **Azure Arc-enabled Kubernetes**: On-premises, multi-cloud, or edge
  Kubernetes clusters connected to Azure
- **Azure Kubernetes Service (AKS)**: Azure's managed Kubernetes offering

### Key Benefits

| Benefit | Description |
|---------|-------------|
| Managed Installation | Azure handles ArgoCD deployment and upgrades |
| Workload Identity | Native Azure AD integration without managing secrets |
| Multi-Cluster | Consistent GitOps across hybrid environments |
| Azure Integration | Works with Azure Key Vault, ACR, and Azure AD |
| High Availability | Built-in HA mode with 3-node support |

---

## Prerequisites

### Azure Arc-enabled Kubernetes

1. Kubernetes cluster connected to Azure Arc:

   ```bash
   # Connect cluster to Azure Arc
   az connectedk8s connect --name <cluster-name> \
     --resource-group <resource-group>
   ```

2. Required permissions:
   - `Microsoft.Kubernetes/connectedClusters` (read/write)
   - `Microsoft.KubernetesConfiguration/extensions` (read/write)

### Azure Kubernetes Service (AKS)

1. MSI-based AKS cluster (not SPN):

   ```bash
   # Create MSI-based AKS cluster
   az aks create --resource-group <rg> --name <cluster> \
     --enable-managed-identity

   # Convert existing SPN cluster to MSI
   az aks update -g <rg> -n <cluster> --enable-managed-identity
   ```

2. Required permissions:
   - `Microsoft.ContainerService/managedClusters` (read/write)
   - `Microsoft.KubernetesConfiguration/extensions` (read/write)

### Common Requirements

```bash
# Register Azure providers
az provider register --namespace Microsoft.Kubernetes
az provider register --namespace Microsoft.ContainerService
az provider register --namespace Microsoft.KubernetesConfiguration

# Install CLI extensions
az extension add -n k8s-configuration
az extension add -n k8s-extension

# Verify registration (wait for 'Registered' state)
az provider show -n Microsoft.KubernetesConfiguration -o table
```

---

## Network Requirements

The GitOps agents require outbound access to:

| Endpoint | Purpose |
|----------|---------|
| `management.azure.com` | Azure Resource Manager communication |
| `<region>.dp.kubernetesconfiguration.azure.com` | Configuration data plane |
| `login.microsoftonline.com` | Azure AD token refresh |
| `mcr.microsoft.com` | Container image pulls |
| Git repository (port 22 or 443) | Source code sync |

---

## Installation Methods

### Method 1: Simple Installation (Single Node)

For development or single-node clusters:

```bash
az k8s-extension create \
  --resource-group <resource-group> \
  --cluster-name <cluster-name> \
  --cluster-type managedClusters \
  --name argocd \
  --extension-type Microsoft.ArgoCD \
  --release-train preview \
  --config deployWithHighAvailability=false \
  --config namespaceInstall=false \
  --config "config-maps.argocd-cmd-params-cm.data.application\.namespaces=namespace1,namespace2"
```

**Parameters:**

| Parameter | Description |
|-----------|-------------|
| `deployWithHighAvailability=false` | Single-node deployment |
| `namespaceInstall=false` | Cluster-wide ArgoCD access |
| `application.namespaces` | Namespaces where ArgoCD can detect Applications |

### Method 2: High Availability Installation (Production)

For production with 3+ nodes:

```bash
az k8s-extension create \
  --resource-group <resource-group> \
  --cluster-name <cluster-name> \
  --cluster-type managedClusters \
  --name argocd \
  --extension-type Microsoft.ArgoCD \
  --release-train preview \
  --config namespaceInstall=false \
  --config "config-maps.argocd-cmd-params-cm.data.application\.namespaces=default,argocd"
```

### Method 3: Namespace-Scoped Installation

For multi-tenant clusters with isolated ArgoCD instances:

```bash
az k8s-extension create \
  --resource-group <resource-group> \
  --cluster-name <cluster-name> \
  --cluster-type managedClusters \
  --name argocd-team-a \
  --extension-type Microsoft.ArgoCD \
  --release-train preview \
  --config namespaceInstall=true \
  --target-namespace team-a-argocd
```

---

## Workload Identity Integration (Recommended for Production)

Workload identity enables Azure AD authentication without managing secrets.

### Bicep Template

```bicep
var clusterName = '<aks-or-arc-cluster-name>'
var workloadIdentityClientId = '<managed-identity-client-id>'
var ssoWorkloadIdentityClientId = '<sso-managed-identity-client-id>'
var url = 'https://<public-ip-for-argocd-ui>/'

var oidcConfig = '''
name: Azure
issuer: https://login.microsoftonline.com/<your-tenant-id>/v2.0
clientID: <sso-client-id>
azure:
  useWorkloadIdentity: true
requestedIDTokenClaims:
  groups:
    essential: true
requestedScopes:
  - openid
  - profile
  - email
'''

var defaultPolicy = 'role:readonly'
var policy = '''
p, role:org-admin, applications, *, */*, allow
p, role:org-admin, clusters, get, *, allow
p, role:org-admin, repositories, get, *, allow
p, role:org-admin, repositories, create, *, allow
p, role:org-admin, repositories, update, *, allow
p, role:org-admin, repositories, delete, *, allow
g, <entra-group-id>, role:org-admin
'''

resource cluster 'Microsoft.ContainerService/managedClusters@2024-10-01' existing = {
  name: clusterName
}

resource extension 'Microsoft.KubernetesConfiguration/extensions@2023-05-01' = {
  name: 'argocd'
  scope: cluster
  properties: {
    extensionType: 'Microsoft.ArgoCD'
    releaseTrain: 'preview'
    configurationSettings: {
      'workloadIdentity.enable': 'true'
      'workloadIdentity.clientId': workloadIdentityClientId
      'workloadIdentity.entraSSOClientId': ssoWorkloadIdentityClientId
      'config-maps.argocd-cm.data.oidc\\.config': oidcConfig
      'config-maps.argocd-cm.data.url': url
      'config-maps.argocd-rbac-cm.data.policy\\.default': defaultPolicy
      'config-maps.argocd-rbac-cm.data.policy\\.csv': policy
      'config-maps.argocd-cmd-params-cm.data.application\\.namespaces': 'default, argocd'
    }
  }
}
```

### Deploy with Bicep

```bash
az deployment group create \
  --resource-group <resource-group> \
  --template-file argocd-extension.bicep
```

### Setup Workload Identity Credentials

1. **Retrieve OIDC issuer URL:**

   ```bash
   # For AKS
   az aks show -n <cluster> -g <rg> --query "oidcIssuerProfile.issuerUrl" -o tsv

   # For Arc-enabled Kubernetes
   az connectedk8s show -n <cluster> -g <rg> --query "oidcIssuerProfile.issuerUrl" -o tsv
   ```

2. **Create managed identity:**

   ```bash
   az identity create --name argocd-identity --resource-group <rg>
   ```

3. **Create federated credential:**

   ```bash
   az identity federated-credential create \
     --name argocd-federated \
     --identity-name argocd-identity \
     --resource-group <rg> \
     --issuer <oidc-issuer-url> \
     --subject system:serviceaccount:argocd:source-controller \
     --audience api://AzureADTokenExchange
   ```

4. **Grant ACR permissions (if using Azure Container Registry):**

   ```bash
   # For ABAC-enabled registries
   az role assignment create \
     --role "Container Registry Repository Reader" \
     --assignee <identity-client-id> \
     --scope /subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.ContainerRegistry/registries/<acr>

   # For non-ABAC registries
   az role assignment create \
     --role "AcrPull" \
     --assignee <identity-client-id> \
     --scope /subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.ContainerRegistry/registries/<acr>
   ```

---

## Accessing ArgoCD UI

### Option 1: LoadBalancer Service

```bash
kubectl -n argocd expose service argocd-server \
  --type LoadBalancer \
  --name argocd-server-lb \
  --port 80 \
  --target-port 8080
```

### Option 2: Ingress Controller

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: argocd-server
  namespace: argocd
  annotations:
    nginx.ingress.kubernetes.io/ssl-passthrough: "true"
    nginx.ingress.kubernetes.io/backend-protocol: "HTTPS"
spec:
  ingressClassName: nginx
  rules:
    - host: argocd.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: argocd-server
                port:
                  number: 443
```

### Option 3: Port Forward (Development)

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

---

## Deploying Applications

### Example: AKS Store Demo

```bash
kubectl apply -f - <<EOF
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: aks-store-demo
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/Azure-Samples/aks-store-demo.git
    targetRevision: HEAD
    path: kustomize/overlays/dev
  syncPolicy:
    automated: {}
  destination:
    namespace: pets
    server: https://kubernetes.default.svc
EOF
```

### Multi-Source with Azure Container Registry

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: myapp
  namespace: argocd
spec:
  project: default
  sources:
    # Helm chart from ACR
    - repoURL: <acr-name>.azurecr.io/helm
      chart: myapp
      targetRevision: 1.0.0
      helm:
        valueFiles:
          - $values/overlays/prod/values.yaml
    # Values from Git
    - repoURL: https://github.com/org/config.git
      targetRevision: main
      ref: values
  destination:
    server: https://kubernetes.default.svc
    namespace: myapp
```

---

## Updating Configuration

Update ArgoCD configmaps through the extension (not directly via kubectl):

```bash
az k8s-extension update \
  --resource-group <resource-group> \
  --cluster-name <cluster-name> \
  --cluster-type managedClusters \
  --name argocd \
  --config "config-maps.argocd-cm.data.url=https://<new-public-ip>/auth/callback"
```

---

## Connecting to Private ACR

For private Azure Container Registry access with workload identity:

1. Use workload identity (configured above)
2. Add repository in ArgoCD:

   ```bash
   argocd repo add <acr-name>.azurecr.io \
     --type helm \
     --name azure-acr \
     --enable-oci
   ```

---

## Deleting the Extension

```bash
az k8s-extension delete \
  -g <resource-group> \
  -c <cluster-name> \
  -n argocd \
  -t managedClusters \
  --yes
```

---

## Comparison: Azure Extension vs Manual Installation

| Aspect | Azure Extension | Manual Installation |
|--------|-----------------|---------------------|
| Installation | `az k8s-extension create` | `kubectl apply` or Helm |
| Upgrades | Managed by Azure | Manual |
| Workload Identity | Built-in support | Manual configuration |
| Azure AD SSO | Simplified setup | Complex OIDC config |
| Support | Azure support included | Community support |
| Customization | Limited to extension params | Full control |
| Multi-cluster | Centralized Azure management | Per-cluster management |

---

## Troubleshooting

### Extension Installation Failed

```bash
# Check extension status
az k8s-extension show \
  -g <rg> -c <cluster> -t managedClusters \
  -n argocd

# Check ArgoCD pods
kubectl get pods -n argocd

# Check extension operator logs
kubectl logs -n azure-arc -l app.kubernetes.io/component=extension-manager
```

### Workload Identity Issues

```bash
# Verify federated credential
az identity federated-credential list \
  --identity-name argocd-identity \
  --resource-group <rg>

# Check service account annotation
kubectl get sa -n argocd source-controller -o yaml
```

### Sync Failures

```bash
# Check ArgoCD application status
argocd app get <app-name>

# Check repo server logs
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-repo-server
```

---

## Best Practices for Azure GitOps

1. **Use Workload Identity**: Avoid storing secrets; use Azure AD authentication
2. **Private Endpoints**: Use Azure Private Link for ACR and Key Vault
3. **Azure Policy**: Enforce GitOps compliance with Azure Policy
4. **Azure Monitor**: Integrate ArgoCD metrics with Azure Monitor
5. **Separate Environments**: Use different resource groups for dev/staging/prod
6. **RBAC**: Map Azure AD groups to ArgoCD roles

---

## References

- [Microsoft Learn: GitOps with ArgoCD Tutorial](https://learn.microsoft.com/en-us/azure/azure-arc/kubernetes/tutorial-use-gitops-argocd)
- [Azure Arc-enabled Kubernetes Documentation](https://learn.microsoft.com/en-us/azure/azure-arc/kubernetes/)
- [AKS Workload Identity](https://learn.microsoft.com/en-us/azure/aks/workload-identity-deploy-cluster)
- [ArgoCD Azure AD OIDC Configuration](https://github.com/argoproj/argo-cd/blob/master/docs/operator-manual/user-management/microsoft.md)
