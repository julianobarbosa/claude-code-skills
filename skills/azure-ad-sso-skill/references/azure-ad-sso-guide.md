# Azure AD SSO Integration - Complete Reference Guide

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Azure AD App Registration](#azure-ad-app-registration)
3. [Access Restriction by Group](#access-restriction-by-group)
4. [Secrets Management with Key Vault](#secrets-management-with-key-vault)
5. [Kubernetes Manifest Examples](#kubernetes-manifest-examples)
6. [Environment Configuration Matrix](#environment-configuration-matrix)
7. [Security Checklist](#security-checklist)

---

## Architecture Overview

### OAuth2 Authorization Code Flow

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│   Browser   │     │  Application │     │    Azure AD     │
│             │     │  (K8s Pod)   │     │  (Entra ID)     │
└──────┬──────┘     └──────┬───────┘     └────────┬────────┘
       │                   │                      │
       │  1. Click Login   │                      │
       │──────────────────>│                      │
       │                   │                      │
       │  2. Redirect      │                      │
       │<──────────────────│                      │
       │                   │                      │
       │  3. Azure Login   │                      │
       │─────────────────────────────────────────>│
       │                   │                      │
       │  4. MFA/Consent   │                      │
       │<─────────────────────────────────────────│
       │                   │                      │
       │  5. Auth Code     │                      │
       │──────────────────>│                      │
       │                   │                      │
       │                   │  6. Exchange Code    │
       │                   │─────────────────────>│
       │                   │                      │
       │                   │  7. Access + ID      │
       │                   │     Token + Groups   │
       │                   │<─────────────────────│
       │                   │                      │
       │  8. Session       │                      │
       │<──────────────────│                      │
       │                   │                      │
```

### Access Control Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Access Control Layers                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Layer 1: Azure AD Enterprise App                               │
│  ├─ appRoleAssignmentRequired = true                            │
│  └─ Only assigned users/groups can authenticate                 │
│                                                                  │
│  Layer 2: Application Group Filtering                           │
│  ├─ DD_SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_GROUPS_FILTER         │
│  └─ Only import matching groups to application                  │
│                                                                  │
│  Layer 3: Application RBAC                                      │
│  ├─ Map Azure AD groups to application roles                    │
│  └─ DefectDojo: Superuser, Staff, User                         │
│  └─ Grafana: Admin, Editor, Viewer                             │
│  └─ ArgoCD: admin, readonly, developer                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Component Interaction

| Component | Role | Configuration Location |
|-----------|------|----------------------|
| Azure AD App Registration | Identity Provider | Azure Portal / CLI |
| Enterprise Application | Access Control | Azure Portal / CLI |
| Azure Key Vault | Secret Storage | Azure |
| Secrets Store CSI Driver | Secret Sync | AKS Add-on |
| SecretProviderClass | Secret Mapping | Kubernetes Manifest |
| Application | Authentication Consumer | Helm Values |

---

## Azure AD App Registration

### Complete CLI Workflow

```bash
#!/bin/bash
# Azure AD SSO Setup Script

# Configuration
APP_NAME="<application>-<environment>"
REDIRECT_URI="https://<app-domain>/complete/<provider>/"
ADMIN_GROUP_NAME="G-Usuarios-<App>-Admin"
KEYVAULT_NAME="<keyvault-name>"

# Step 1: Create App Registration
echo "Creating App Registration..."
APP_ID=$(az ad app create \
  --display-name "$APP_NAME" \
  --sign-in-audience "AzureADMyOrg" \
  --web-redirect-uris "$REDIRECT_URI" \
  --query appId -o tsv)

echo "Application (client) ID: $APP_ID"

# Step 2: Get Tenant ID
TENANT_ID=$(az account show --query tenantId -o tsv)
echo "Directory (tenant) ID: $TENANT_ID"

# Step 3: Create Client Secret
echo "Creating client secret..."
SECRET=$(az ad app credential reset \
  --id $APP_ID \
  --append \
  --years 1 \
  --query password -o tsv)

echo "Client Secret: $SECRET"
echo "⚠️  SAVE THIS SECRET NOW - It cannot be retrieved later!"

# Step 4: Enable Group Claims
echo "Enabling group claims..."
az ad app update --id $APP_ID --set groupMembershipClaims=SecurityGroup

# Step 5: Add API Permissions
echo "Adding API permissions..."
# Microsoft Graph API ID
GRAPH_API="00000003-0000-0000-c000-000000000000"

# Group.Read.All (delegated)
az ad app permission add \
  --id $APP_ID \
  --api $GRAPH_API \
  --api-permissions 5f8c59db-677d-491f-a6b8-5f174b11ec1d=Scope

# Grant admin consent
echo "Granting admin consent..."
az ad app permission admin-consent --id $APP_ID

# Step 6: Store Secret in Key Vault
echo "Storing secret in Key Vault..."
az keyvault secret set \
  --vault-name "$KEYVAULT_NAME" \
  --name "${APP_NAME}-azuread-client-secret" \
  --value "$SECRET"

# Step 7: Enable User Assignment (Access Restriction)
echo "Enabling user assignment requirement..."
# Wait for Service Principal to be created
sleep 10

SP_ID=$(az ad sp list --filter "appId eq '$APP_ID'" --query "[0].id" -o tsv)
az ad sp update --id $SP_ID --set appRoleAssignmentRequired=true

# Step 8: Assign Admin Group
echo "Assigning admin group..."
GROUP_ID=$(az ad group show --group "$ADMIN_GROUP_NAME" --query id -o tsv)

az rest --method POST \
  --uri "https://graph.microsoft.com/v1.0/servicePrincipals/$SP_ID/appRoleAssignments" \
  --headers "Content-Type=application/json" \
  --body "{
    \"principalId\": \"$GROUP_ID\",
    \"principalType\": \"Group\",
    \"appRoleId\": \"00000000-0000-0000-0000-000000000000\",
    \"resourceId\": \"$SP_ID\"
  }"

# Summary
echo ""
echo "========================================="
echo "Azure AD SSO Setup Complete!"
echo "========================================="
echo "Application (client) ID: $APP_ID"
echo "Directory (tenant) ID: $TENANT_ID"
echo "Redirect URI: $REDIRECT_URI"
echo "Key Vault Secret: ${APP_NAME}-azuread-client-secret"
echo "Assigned Group: $ADMIN_GROUP_NAME"
echo "========================================="
```

### Redirect URI Reference

| Application | OAuth Provider | Redirect URI Pattern |
|-------------|---------------|---------------------|
| DefectDojo | `azuread-tenant-oauth2` | `https://<domain>/complete/azuread-tenant-oauth2/` |
| Grafana | `azuread` | `https://<domain>/login/azuread` |
| ArgoCD | `microsoft` (Dex) | `https://<domain>/api/dex/callback` |
| Harbor | `oidc` | `https://<domain>/c/oidc/callback` |
| SonarQube | `oidc` | `https://<domain>/oauth2/callback/oidc` |
| OAuth2 Proxy | `azure` | `https://<domain>/oauth2/callback` |
| Vault | `oidc` | `https://<domain>/ui/vault/auth/oidc/oidc/callback` |
| Keycloak | `oidc` | `https://<domain>/realms/<realm>/broker/azure/endpoint` |

---

## Access Restriction by Group

### Overview

Azure AD provides two levels of access control:

1. **Enterprise App Assignment**: Controls WHO can authenticate
2. **Application Role Mapping**: Controls WHAT they can do after authentication

### Enable User Assignment Requirement

This restricts login to only users/groups explicitly assigned to the application:

```bash
# Get Service Principal ID (not App ID!)
SP_ID=$(az ad sp list --filter "appId eq '<app-id>'" --query "[0].id" -o tsv)

# Enable assignment requirement
az ad sp update --id $SP_ID --set appRoleAssignmentRequired=true

# Verify
az ad sp show --id $SP_ID --query "appRoleAssignmentRequired"
# Should return: true
```

### Assign Groups to Application

```bash
# Get group ID
GROUP_ID=$(az ad group show --group "G-Usuarios-<App>-Admin" --query id -o tsv)

# Assign group (default app role)
az rest --method POST \
  --uri "https://graph.microsoft.com/v1.0/servicePrincipals/$SP_ID/appRoleAssignments" \
  --headers "Content-Type=application/json" \
  --body "{
    \"principalId\": \"$GROUP_ID\",
    \"principalType\": \"Group\",
    \"appRoleId\": \"00000000-0000-0000-0000-000000000000\",
    \"resourceId\": \"$SP_ID\"
  }"

# List current assignments
az rest --method GET \
  --uri "https://graph.microsoft.com/v1.0/servicePrincipals/$SP_ID/appRoleAssignments" \
  --query "value[].{group:principalDisplayName, type:principalType}"
```

### Remove Group Assignment

```bash
# List assignments to get ID
ASSIGNMENTS=$(az rest --method GET \
  --uri "https://graph.microsoft.com/v1.0/servicePrincipals/$SP_ID/appRoleAssignments")

# Delete specific assignment
ASSIGNMENT_ID="<assignment-id-from-list>"
az rest --method DELETE \
  --uri "https://graph.microsoft.com/v1.0/servicePrincipals/$SP_ID/appRoleAssignments/$ASSIGNMENT_ID"
```

### Application-Level Group Filtering

In addition to Azure AD assignment, applications can filter which groups are imported:

```yaml
# DefectDojo: Only import groups matching pattern
- name: DD_SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_GROUPS_FILTER
  value: "^G-Usuarios-DefectDojo-.*"

# Grafana: Only allow specific groups
grafana.ini:
  auth.azuread:
    allowed_groups: "<admin-group-id> <viewer-group-id>"

# ArgoCD: Only sync specific groups in Dex
dex.config:
  connectors:
    - type: microsoft
      config:
        groups:
          - <admin-group-id>
          - <developer-group-id>
```

---

## Secrets Management with Key Vault

### Store Secret

```bash
az keyvault secret set \
  --vault-name "<keyvault-name>" \
  --name "<app>-azuread-client-secret" \
  --value "<client-secret>"
```

### Grant AKS Access

```bash
# Get managed identity client ID
IDENTITY_ID=$(az aks show \
  --resource-group <rg> \
  --name <aks-name> \
  --query addonProfiles.azureKeyvaultSecretsProvider.identity.clientId -o tsv)

# Grant Key Vault access
az keyvault set-policy \
  --name "<keyvault-name>" \
  --spn $IDENTITY_ID \
  --secret-permissions get list
```

### SecretProviderClass Template

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
          objectName: "<app>-azuread-client-secret"
          objectType: "secret"
          objectAlias: "AZURE_AD_CLIENT_SECRET"
  secretObjects:
    - secretName: <app>-azure-ad
      type: Opaque
      data:
        - objectName: "AZURE_AD_CLIENT_SECRET"
          key: "client-secret"
```

### Bootstrap Secret (for CSI chicken-and-egg)

When CSI driver needs the pod to run to sync secrets, but pod needs secrets:

```bash
# Create bootstrap secret manually
kubectl create secret generic <app>-bootstrap \
  --namespace <namespace> \
  --from-literal=client-secret="$(az keyvault secret show \
    --vault-name <vault> \
    --name <secret-name> \
    --query value -o tsv)" \
  --from-literal=admin-password="$(az keyvault secret show \
    --vault-name <vault> \
    --name <app>-admin-password \
    --query value -o tsv)"
```

---

## Kubernetes Manifest Examples

### Complete DefectDojo SecretProviderClass

```yaml
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: defectdojo-secrets
  namespace: monitoring
  labels:
    app.kubernetes.io/name: defectdojo
    app.kubernetes.io/component: secrets
spec:
  provider: azure
  parameters:
    usePodIdentity: "false"
    useVMManagedIdentity: "true"
    userAssignedIdentityID: "f1a14a8f-6d38-40a0-a935-3cdd91a25f47"
    keyvaultName: "kv-cafehyna-dev-hlg"
    cloudName: "AzurePublicCloud"
    tenantId: "3f7a3df4-f85b-4ca8-98d0-08b1034e6567"
    objects: |
      array:
        - |
          objectName: "defectdojo-admin-password"
          objectType: "secret"
          objectAlias: "DD_ADMIN_PASSWORD"
        - |
          objectName: "defectdojo-secret-key"
          objectType: "secret"
          objectAlias: "DD_SECRET_KEY"
        - |
          objectName: "defectdojo-credential-aes-key"
          objectType: "secret"
          objectAlias: "DD_CREDENTIAL_AES_256_KEY"
        - |
          objectName: "defectdojo-azuread-client-secret"
          objectType: "secret"
          objectAlias: "DD_SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_SECRET"
  secretObjects:
    - secretName: defectdojo
      type: Opaque
      data:
        - objectName: "DD_ADMIN_PASSWORD"
          key: "DD_ADMIN_PASSWORD"
        - objectName: "DD_SECRET_KEY"
          key: "DD_SECRET_KEY"
        - objectName: "DD_CREDENTIAL_AES_256_KEY"
          key: "DD_CREDENTIAL_AES_256_KEY"
        - objectName: "DD_SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_SECRET"
          key: "DD_SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_SECRET"
```

---

## Environment Configuration Matrix

### Cluster Resources

| Environment | Key Vault | Managed Identity | AKS Cluster |
|-------------|-----------|------------------|-------------|
| cafehyna-dev | `kv-cafehyna-dev-hlg` | `f1a14a8f-6d38-40a0-a935-3cdd91a25f47` | `aks-cafehyna-dev-hlg` |
| cafehyna-hub | `kv-cafehyna-default` | `f1a14a8f-6d38-40a0-a935-3cdd91a25f47` | `aks-cafehyna-default` |
| cafehyna-prd | `kv-cafehyna-prd` | `f1a14a8f-6d38-40a0-a935-3cdd91a25f47` | `aks-cafehyna-prd` |

### Common Settings

| Setting | Value | Notes |
|---------|-------|-------|
| Tenant ID | `3f7a3df4-f85b-4ca8-98d0-08b1034e6567` | Same for all environments |
| Sign-in Audience | `AzureADMyOrg` | Single tenant only |
| Token Lifetime | Default (1h) | Don't modify unless required |
| Secret Expiration | 1 year | Set calendar reminder |

### Naming Conventions

| Resource | Pattern | Example |
|----------|---------|---------|
| App Registration | `<app>-<env>` | `defectdojo-dev` |
| Key Vault Secret | `<app>-azuread-client-secret` | `defectdojo-azuread-client-secret` |
| Azure AD Group | `G-Usuarios-<App>-<Role>` | `G-Usuarios-DefectDojo-Admin` |
| K8s Secret | `<app>` or `<app>-azure-ad` | `defectdojo` |
| SecretProviderClass | `<app>-secrets` | `defectdojo-secrets` |

---

## Security Checklist

### Azure AD Configuration

- [ ] Single tenant authentication (AzureADMyOrg)
- [ ] Client secret stored in Key Vault (never in code)
- [ ] Client secret expiration tracked (calendar reminder set)
- [ ] Only required redirect URIs configured
- [ ] User assignment enabled for restricted access
- [ ] Admin consent granted for API permissions
- [ ] Group claims enabled (SecurityGroup)

### Kubernetes Configuration

- [ ] Managed identity used for Key Vault access
- [ ] SecretProviderClass configured correctly
- [ ] CSI volume mounted in pods
- [ ] Environment variables reference K8s secrets
- [ ] No secrets hardcoded in Helm values

### Application Configuration

- [ ] HTTPS enforced for all redirect URIs
- [ ] Proxy SSL header configured (for reverse proxy)
- [ ] CSRF trusted origins configured
- [ ] Group filtering enabled (if applicable)
- [ ] Role mapping configured for authorization

### Operational

- [ ] Azure AD sign-in logs enabled
- [ ] Application login tested end-to-end
- [ ] Group sync verified
- [ ] Role mapping verified
- [ ] Fallback login method available (local admin)
- [ ] Secret rotation procedure documented
