---
name: keyvault-csi-driver
description: Azure Key Vault + CSI Driver integration for Kubernetes secrets management. Use when creating SecretProviderClass resources, mounting secrets from Key Vault, troubleshooting 403 errors, syncing secrets to K8s, or configuring applications to use Key Vault secrets.
---

# Azure Key Vault CSI Driver Skill

## Overview

This skill provides guidance for integrating Azure Key Vault with Kubernetes using the Secrets Store CSI Driver. All sensitive data in the your organization clusters is stored in Azure Key Vault and accessed via the CSI driver.

## Quick Reference

### Environment Configuration

| Cluster | Key Vault | Managed Identity (Client ID) | Tenant ID |
|---------|-----------|------------------------------|-----------|
| example-app-dev | `kv-example-dev-hlg` | `<WORKLOAD_IDENTITY_CLIENT_ID>` | `<TENANT_ID>` |
| example-app-hub | `kv-example-default` | `<WORKLOAD_IDENTITY_CLIENT_ID>` | `<TENANT_ID>` |
| example-app-prd | `kv-example-prd` | `<WORKLOAD_IDENTITY_CLIENT_ID>` | `<TENANT_ID>` |
| example-app2-dev | `kv-example2-dev` | Check cluster identity | `<TENANT_ID>` |
| example-app2-prd | `kv-example2-prd` | Check cluster identity | `<TENANT_ID>` |

## SecretProviderClass Template

```yaml
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: <app>-secrets
  namespace: <namespace>
  labels:
    app.kubernetes.io/name: <app>
    app.kubernetes.io/component: secrets
spec:
  provider: azure
  parameters:
    usePodIdentity: "false"
    useVMManagedIdentity: "true"
    userAssignedIdentityID: "<managed-identity-client-id>"
    keyvaultName: "<keyvault-name>"
    cloudName: "AzurePublicCloud"
    tenantId: "<tenant-id>"
    objects: |
      array:
        - |
          objectName: "<secret-name-in-keyvault>"
          objectType: "secret"
          objectAlias: "<ALIAS_FOR_MOUNT>"
  # Optional: Sync to Kubernetes Secret
  secretObjects:
    - secretName: <k8s-secret-name>
      type: Opaque
      data:
        - objectName: "<ALIAS_FOR_MOUNT>"
          key: "<key-in-k8s-secret>"
```

## Pod Volume Mount

```yaml
spec:
  containers:
    - name: app
      volumeMounts:
        - name: secrets-store
          mountPath: "/mnt/secrets-store"
          readOnly: true
  volumes:
    - name: secrets-store
      csi:
        driver: secrets-store.csi.k8s.io
        readOnly: true
        volumeAttributes:
          secretProviderClass: "<secretproviderclass-name>"
```

## Common Patterns

### Pattern 1: Simple API Token (e.g., Cloudflare)

```yaml
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: cloudflare-api-token-kv
  namespace: external-dns
spec:
  provider: azure
  secretObjects:
    - data:
        - key: cloudflare_api_token
          objectName: cloudflare-api-token
      secretName: cloudflare-api-token
      type: Opaque
  parameters:
    usePodIdentity: "false"
    useVMManagedIdentity: "true"
    userAssignedIdentityID: "<WORKLOAD_IDENTITY_CLIENT_ID>"
    keyvaultName: "kv-example-dev-hlg"
    objects: |
      array:
        - |
          objectName: cloudflare-api-token
          objectType: secret
    tenantId: "<TENANT_ID>"
```

### Pattern 2: Multiple Secrets to Multiple K8s Secrets

```yaml
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: app-secrets
spec:
  provider: azure
  parameters:
    usePodIdentity: "false"
    useVMManagedIdentity: "true"
    userAssignedIdentityID: "<identity>"
    keyvaultName: "<keyvault>"
    tenantId: "<tenant>"
    objects: |
      array:
        - |
          objectName: "app-db-password"
          objectType: "secret"
          objectAlias: "DB_PASSWORD"
        - |
          objectName: "app-redis-password"
          objectType: "secret"
          objectAlias: "REDIS_PASSWORD"
  secretObjects:
    - secretName: app-db-secret
      type: Opaque
      data:
        - objectName: "DB_PASSWORD"
          key: "password"
    - secretName: app-redis-secret
      type: Opaque
      data:
        - objectName: "REDIS_PASSWORD"
          key: "password"
```

### Pattern 3: TLS Certificate

```yaml
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: tls-cert-provider
spec:
  provider: azure
  secretObjects:
    - secretName: tls-secret
      type: kubernetes.io/tls
      data:
        - objectName: tls-cert
          key: tls.crt
        - objectName: tls-key
          key: tls.key
  parameters:
    usePodIdentity: "false"
    useVMManagedIdentity: "true"
    userAssignedIdentityID: "<identity>"
    keyvaultName: "<keyvault>"
    tenantId: "<tenant>"
    objects: |
      array:
        - |
          objectName: my-certificate
          objectType: cert
          objectAlias: tls-cert
        - |
          objectName: my-certificate
          objectType: secret
          objectAlias: tls-key
```

## File Locations

SecretProviderClass files are stored in:

```
argo-cd-helm-values/kube-addons/<application>/<cluster>/secretproviderclass.yaml
```

Examples:

- `argo-cd-helm-values/kube-addons/defectdojo/example-app-dev/secretproviderclass.yaml`
- `argo-cd-helm-values/kube-addons/external-dns/example-app-dev/secretproviderclass.yaml`
- `argo-cd-helm-values/kube-addons/cert-manager/example-app-dev/csi-cloudflare-api-key.yaml`

## Troubleshooting

### Error: 403 Forbidden

**Cause:** Managed identity lacks Key Vault permissions.

**Solution:**

```bash
# Get identity info from error message, then:
az keyvault set-policy \
  --name "<keyvault-name>" \
  --object-id "<object-id-from-error>" \
  --secret-permissions get list

# Or for RBAC-enabled Key Vaults:
az role assignment create \
  --role "Key Vault Secrets User" \
  --assignee-object-id "<object-id>" \
  --assignee-principal-type ServicePrincipal \
  --scope "/subscriptions/.../Microsoft.KeyVault/vaults/<kv-name>"
```

### Error: Secret Not Found

**Cause:** Secret name doesn't exist or case mismatch.

**Solution:**

```bash
# List secrets (names are case-sensitive)
az keyvault secret list --vault-name "<kv-name>" --query "[].name" -o tsv
```

### Error: K8s Secret Not Created

**Cause:** No pod has mounted the CSI volume yet.

**Solution:** Deploy a pod that mounts the volume. K8s secrets are only created when at least one pod uses the SecretProviderClass.

### Error: Pod Stuck in ContainerCreating

**Diagnostic:**

```bash
kubectl describe pod <pod-name> -n <namespace>
kubectl get pods -n kube-system | grep secrets-store
kubectl logs -n kube-system -l app=secrets-store-provider-azure
```

## Scripts

### Grant Key Vault Permissions

```bash
# Use the helper script
./scripts/grant-keyvault-permissions.sh

# Or quick manual command
az keyvault set-policy \
  --name "kv-example-dev-hlg" \
  --object-id "<object-id>" \
  --secret-permissions get list
```

### Create Secret in Key Vault

```bash
az keyvault secret set \
  --vault-name "kv-example-dev-hlg" \
  --name "my-app-secret" \
  --value "secret-value"
```

### List All SecretProviderClasses

```bash
kubectl get secretproviderclass -A
```

### Check CSI Driver Status

```bash
kubectl get pods -n kube-system | grep secrets-store
```

## Important Notes

1. **CSI Volume Required**: Even if using `secretObjects` to sync to K8s secrets, the pod MUST mount the CSI volume.

2. **Secret Names**: Key Vault secret names are case-sensitive. Use exact match.

3. **Object Alias**: Use `objectAlias` for filesystem-safe names when mounting.

4. **Namespace Scope**: SecretProviderClass is namespace-scoped. Create one per namespace that needs it.

5. **RBAC vs Access Policies**: Check Key Vault authorization model:

   ```bash
   az keyvault show --name "<kv>" --query "properties.enableRbacAuthorization"
   ```

## Detailed Reference

For complete implementation examples and architecture:

- **[references/architecture.md](references/architecture.md)** - CSI driver architecture
- **[references/examples.md](references/examples.md)** - Real-world examples
- **[references/troubleshooting.md](references/troubleshooting.md)** - Extended troubleshooting

---

## Gotchas

- **K8s Secret doesn't exist until a pod mounts the CSI volume:** `secretObjects:` syncing is lazy — no pod, no Secret. Apps that consume the Secret directly (without mounting the CSI volume themselves) will fail on first deploy until a sibling pod mounts first.
- **Workload Identity vs VM Managed Identity are different code paths:** `useVMManagedIdentity: "true"` reads from IMDS; Workload Identity needs `usePodIdentity: "false"` + `useVMManagedIdentity: "false"` + serviceAccount annotations. Mixing flags silently falls back to wrong identity.
- **Key Vault names are case-sensitive in `objects:`, K8s keys are not:** Secret named `MyToken` in KV won't be found if you write `mytoken` in the SPC. The CSI logs say "secret not found" with no hint about casing.
- **RBAC vs Access Policy is per-vault, not per-tenant:** Some vaults use access policies (`az keyvault set-policy`), others use Azure RBAC (`Key Vault Secrets User` role). Check `properties.enableRbacAuthorization` first — granting the wrong type returns 403 with identical error text.
- **TLS certs need two `objectType` entries:** Mounting a cert as `tls.crt`+`tls.key` requires `objectType: cert` (public) AND `objectType: secret` (full PEM with private key) — both pointing to the same KV cert name. Missing one breaks Ingress TLS silently.
- **CSI rotation is opt-in and deploy-only by default:** Secrets mounted into pods don't refresh when the KV value changes unless `--enable-secret-rotation=true` is set on the driver AND the pod is restarted. Long-lived pods serve stale secrets.
