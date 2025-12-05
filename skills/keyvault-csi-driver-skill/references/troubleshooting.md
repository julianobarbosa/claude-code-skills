# Troubleshooting Reference

## Quick Diagnostic Commands

```bash
# Check CSI driver pods
kubectl get pods -n kube-system -l app=secrets-store-csi-driver

# Check Azure provider pods
kubectl get pods -n kube-system -l app=secrets-store-provider-azure

# List all SecretProviderClasses
kubectl get secretproviderclass -A

# Check CSI driver logs
kubectl logs -n kube-system -l app=secrets-store-csi-driver --tail=100

# Check provider logs
kubectl logs -n kube-system -l app=secrets-store-provider-azure --tail=100

# Describe problematic pod
kubectl describe pod <pod-name> -n <namespace>

# Check synced secrets
kubectl get secret -n <namespace> | grep <expected-secret-name>
```

## Error Reference

### Error: 403 Forbidden / Access Denied

**Full Error:**

```
MountVolume.SetUp failed for volume "secrets-store"
rpc error: code = Unknown desc = failed to mount secrets store objects
for pod <namespace>/<pod-name>, err: rpc error: code = Unknown desc =
failed to process mount request, error: keyvault.BaseClient#GetSecret:
Failure responding to request: StatusCode=403 -- Original Error:
autorest/azure: Service returned an error. Status=403 Code="Forbidden"
Message="The user, group or application... does not have secrets get
permission on key vault..."
```

**Cause:** The managed identity doesn't have permission to access Key Vault secrets.

**Solution Steps:**

1. Extract identity info from error:

   ```bash
   # Look for object_id and client_id in the error message
   ```

2. Check Key Vault authorization model:

   ```bash
   az keyvault show --name "<kv-name>" \
     --query "properties.enableRbacAuthorization" -o tsv
   ```

3. Grant permissions:

   **For Access Policies (enableRbacAuthorization=false):**

   ```bash
   az keyvault set-policy \
     --name "<kv-name>" \
     --object-id "<object-id-from-error>" \
     --secret-permissions get list
   ```

   **For RBAC Authorization (enableRbacAuthorization=true):**

   ```bash
   az role assignment create \
     --role "Key Vault Secrets User" \
     --assignee-object-id "<object-id-from-error>" \
     --assignee-principal-type ServicePrincipal \
     --scope "/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.KeyVault/vaults/<kv-name>"
   ```

4. Restart the pod:

   ```bash
   kubectl delete pod <pod-name> -n <namespace>
   ```

---

### Error: Secret Not Found

**Full Error:**

```
failed to get objectType:secret, objectName:<secret-name>, objectVersion::
keyvault.BaseClient#GetSecret: Failure responding to request:
StatusCode=404 -- Original Error: autorest/azure: Service returned an error.
Status=404 Code="SecretNotFound" Message="A secret with (name/id) <name> was not found"
```

**Cause:** Secret doesn't exist in Key Vault or name is incorrect (case-sensitive).

**Solution Steps:**

1. List secrets in Key Vault:

   ```bash
   az keyvault secret list --vault-name "<kv-name>" \
     --query "[].name" -o tsv
   ```

2. Check exact name (case-sensitive):

   ```bash
   az keyvault secret show --vault-name "<kv-name>" \
     --name "<exact-secret-name>"
   ```

3. Create secret if missing:

   ```bash
   az keyvault secret set \
     --vault-name "<kv-name>" \
     --name "<secret-name>" \
     --value "<secret-value>"
   ```

4. Verify SecretProviderClass `objectName` matches exactly.

---

### Error: Kubernetes Secret Not Created

**Symptom:** Pod starts successfully but expected K8s Secret doesn't exist.

**Causes:**

1. No pod has mounted the CSI volume yet
2. `secretObjects` configuration is wrong
3. `objectName` in `secretObjects.data` doesn't match `objectAlias` (or `objectName` if no alias)

**Diagnostic:**

```bash
# Check if secret exists
kubectl get secret <expected-name> -n <namespace>

# Check SecretProviderClass configuration
kubectl get secretproviderclass <name> -n <namespace> -o yaml

# Verify pod has the CSI volume mounted
kubectl get pod <pod-name> -n <namespace> -o yaml | grep -A10 "volumes:"
```

**Solution:**

1. Ensure at least one pod mounts the CSI volume
2. Verify `objectName` in `secretObjects.data` matches the alias:

   ```yaml
   parameters:
     objects: |
       array:
         - |
           objectName: "kv-secret-name"
           objectAlias: "MY_ALIAS"  # <-- This name
   secretObjects:
     - secretName: k8s-secret
       data:
         - objectName: "MY_ALIAS"   # <-- Must match alias above
           key: "secret-key"
   ```

---

### Error: Pod Stuck in ContainerCreating

**Symptom:** Pod stays in `ContainerCreating` state indefinitely.

**Diagnostic:**

```bash
# Check pod events
kubectl describe pod <pod-name> -n <namespace>

# Check CSI driver logs
kubectl logs -n kube-system -l app=secrets-store-csi-driver --tail=50

# Check provider logs
kubectl logs -n kube-system -l app=secrets-store-provider-azure --tail=50
```

**Common Causes:**

1. **CSI driver not running:**

   ```bash
   kubectl get pods -n kube-system | grep secrets-store
   # Should see both driver and provider pods on each node
   ```

2. **SecretProviderClass not found:**

   ```bash
   kubectl get secretproviderclass <name> -n <namespace>
   ```

3. **Network connectivity to Key Vault:**
   - Check if VPN is connected
   - Verify private endpoint configuration (if used)

4. **Wrong namespace:**
   - SecretProviderClass must be in the same namespace as the pod

---

### Error: Wrong Managed Identity Used

**Symptom:** Getting 403 errors even after granting permissions.

**Cause:** Multiple managed identities exist, and the wrong one is being used.

**Diagnostic:**

```bash
# Get cluster's kubelet identity (used by CSI driver)
az aks show -g <rg> -n <cluster> \
  --query "identityProfile.kubeletidentity.clientId" -o tsv

# Compare with userAssignedIdentityID in SecretProviderClass
kubectl get secretproviderclass <name> -n <namespace> -o yaml | grep userAssignedIdentityID
```

**Solution:**
Update `userAssignedIdentityID` to match the cluster's kubelet identity, or grant permissions to the identity that's actually being used.

---

### Error: Secret Rotation Not Working

**Symptom:** Secrets in Key Vault were updated but pods still see old values.

**Diagnostic:**

```bash
# Check if rotation is enabled on cluster
az aks show -g <rg> -n <cluster> \
  --query "addonProfiles.azureKeyvaultSecretsProvider.config.enableSecretRotation"

# Check rotation poll interval
az aks show -g <rg> -n <cluster> \
  --query "addonProfiles.azureKeyvaultSecretsProvider.config.rotationPollInterval"

# Check provider logs for rotation activity
kubectl logs -n kube-system -l app=secrets-store-provider-azure | grep rotation
```

**Solution:**

1. Enable rotation on cluster:

   ```bash
   az aks addon update \
     --resource-group <rg> \
     --name <cluster> \
     --addon azure-keyvault-secrets-provider \
     --enable-secret-rotation \
     --rotation-poll-interval 2m
   ```

2. For environment variables from K8s Secrets, the pod must restart. Use Stakater Reloader:

   ```yaml
   metadata:
     annotations:
       reloader.stakater.com/auto: "true"
   ```

3. For volume mounts, the application must re-read the file.

---

### Error: Authentication Timeout

**Full Error:**

```
context deadline exceeded
```

**Cause:** Network connectivity issue to Azure.

**Solution:**

1. Check VPN connection (for private clusters)
2. Verify DNS resolution:

   ```bash
   kubectl run test --rm -it --image=busybox -- nslookup <keyvault-name>.vault.azure.net
   ```

3. Check if private endpoint is configured correctly

---

## Verification Checklist

### Before Deployment

- [ ] Key Vault secret exists with correct name
- [ ] Managed identity has Key Vault permissions
- [ ] CSI driver pods are running on all nodes
- [ ] SecretProviderClass uses correct parameters

### After Deployment

```bash
# 1. Check pod is running
kubectl get pod <name> -n <namespace>

# 2. Check secrets are mounted
kubectl exec <pod> -n <namespace> -- ls -la /mnt/secrets-store/

# 3. Check K8s secrets were created (if using secretObjects)
kubectl get secret -n <namespace>

# 4. Verify secret content (careful with sensitive data)
kubectl exec <pod> -n <namespace> -- cat /mnt/secrets-store/<alias>
```

## Scripts

### Quick Permission Grant Script

Save as `grant-kv-access.sh`:

```bash
#!/bin/bash
KV_NAME="${1:?Key Vault name required}"
OBJECT_ID="${2:?Object ID required}"

RBAC_ENABLED=$(az keyvault show -n "$KV_NAME" --query "properties.enableRbacAuthorization" -o tsv)

if [ "$RBAC_ENABLED" == "true" ]; then
    SCOPE=$(az keyvault show -n "$KV_NAME" --query "id" -o tsv)
    az role assignment create \
        --role "Key Vault Secrets User" \
        --assignee-object-id "$OBJECT_ID" \
        --assignee-principal-type ServicePrincipal \
        --scope "$SCOPE"
else
    az keyvault set-policy \
        --name "$KV_NAME" \
        --object-id "$OBJECT_ID" \
        --secret-permissions get list
fi

echo "Permissions granted for $OBJECT_ID on $KV_NAME"
```

Usage:

```bash
./grant-kv-access.sh "kv-cafehyna-dev-hlg" "b31833cc-acab-4afd-adb1-9004c3331359"
```

### Diagnose CSI Issues Script

```bash
#!/bin/bash
NS="${1:-default}"
SPC="${2:-}"

echo "=== CSI Driver Pods ==="
kubectl get pods -n kube-system | grep secrets-store

echo -e "\n=== SecretProviderClasses in $NS ==="
kubectl get secretproviderclass -n "$NS"

if [ -n "$SPC" ]; then
    echo -e "\n=== SecretProviderClass Details: $SPC ==="
    kubectl describe secretproviderclass "$SPC" -n "$NS"
fi

echo -e "\n=== Recent CSI Driver Logs ==="
kubectl logs -n kube-system -l app=secrets-store-csi-driver --tail=20

echo -e "\n=== Recent Provider Logs ==="
kubectl logs -n kube-system -l app=secrets-store-provider-azure --tail=20
```
