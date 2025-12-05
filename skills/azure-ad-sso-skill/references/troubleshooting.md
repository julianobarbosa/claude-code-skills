# Azure AD SSO Troubleshooting Guide

Comprehensive troubleshooting guide for Azure AD OAuth2/OIDC integration issues.

## Table of Contents

1. [Error Code Reference](#error-code-reference)
2. [Common Issues and Solutions](#common-issues-and-solutions)
3. [Diagnostic Commands](#diagnostic-commands)
4. [Application-Specific Issues](#application-specific-issues)
5. [CSI Driver and Secrets Issues](#csi-driver-and-secrets-issues)
6. [Network and Proxy Issues](#network-and-proxy-issues)

---

## Error Code Reference

### Azure AD Error Codes (AADSTS)

| Error Code | Error Name | Description | Solution |
|------------|------------|-------------|----------|
| AADSTS50011 | InvalidReplyTo | Reply URL doesn't match | Verify exact redirect URI in App Registration (including trailing slash) |
| AADSTS50105 | NotAssigned | User not assigned to application | Enable `appRoleAssignmentRequired` and assign user/group |
| AADSTS65001 | ConsentRequired | Consent not granted for permissions | Run `az ad app permission admin-consent` |
| AADSTS700016 | ApplicationNotFound | App not found in tenant | Verify client ID and tenant ID |
| AADSTS7000218 | InvalidClientSecret | Client secret expired or invalid | Rotate secret in Key Vault, restart pods |
| AADSTS90102 | InvalidRedirectUri | Malformed redirect_uri | Check SSL proxy header configuration |
| AADSTS90014 | MissingRequiredField | Required field missing in request | Verify all required OAuth parameters |
| AADSTS500011 | InvalidResourceServicePrincipal | Resource app doesn't exist in tenant | Create Service Principal for the app |
| AADSTS50058 | SessionExpired | User session expired | Re-authenticate |
| AADSTS50076 | MFARequired | MFA required but not completed | Complete MFA challenge |
| AADSTS530003 | BlockedByCAPolicy | Blocked by Conditional Access | Review CA policies for the app |

---

## Common Issues and Solutions

### 1. Redirect URI Mismatch (AADSTS50011)

**Symptoms:**

- Error: "The reply URL specified in the request does not match"
- Login redirects to Azure AD but fails to return

**Diagnosis:**

```bash
# Check configured redirect URIs
az ad app show --id <app-id> --query "web.redirectUris" -o json

# Common patterns to check
# DefectDojo: https://domain/complete/azuread-tenant-oauth2/
# Grafana: https://domain/login/azuread
# ArgoCD: https://domain/api/dex/callback
```

**Solutions:**

```bash
# Add missing redirect URI
az ad app update --id <app-id> \
  --web-redirect-uris "https://<domain>/complete/<provider>/"

# Verify (note trailing slash matters!)
curl -sS -k -D - -o /dev/null "https://<app>/login/<provider>/" 2>&1 | grep -i location
```

**Checklist:**

- [ ] Trailing slash matches exactly
- [ ] Protocol is HTTPS (not HTTP)
- [ ] Domain matches exactly (no www vs non-www mismatch)
- [ ] Path matches provider expectation

---

### 2. Malformed redirect_uri (AADSTS90102)

**Symptoms:**

- Error: "'redirect_uri' value must be a valid absolute URI"
- redirect_uri appears as `https,%20https://...` or has duplicated scheme

**Root Cause:**
Django apps behind a reverse proxy incorrectly building the redirect URI because `SECURE_PROXY_SSL_HEADER` is misconfigured.

**Diagnosis:**

```bash
# Check what redirect_uri is being sent
curl -sS -k -D - -o /dev/null "https://<app>/login/<provider>/" 2>&1 | grep -i location

# Look for malformed URI like:
# redirect_uri=https,%20https://domain/complete/...
```

**Solution:**

```yaml
# WRONG - causes malformed URI
- name: DD_SECURE_PROXY_SSL_HEADER
  value: "HTTP_X_FORWARDED_PROTO,https"

# CORRECT - just enable the feature
- name: DD_SECURE_PROXY_SSL_HEADER
  value: "True"
```

```bash
# Restart pods after fix
kubectl rollout restart deployment/<app> -n <namespace>
```

---

### 3. User Not Assigned to Application (AADSTS50105)

**Symptoms:**

- Error: "User is not assigned to a role for the application"
- Only affects certain users

**Diagnosis:**

```bash
# Check if user assignment is required
az ad sp show --id <sp-id> --query "appRoleAssignmentRequired"

# List current assignments
az rest --method GET \
  --uri "https://graph.microsoft.com/v1.0/servicePrincipals/<sp-id>/appRoleAssignments"
```

**Solution:**

```bash
# Get Service Principal ID
SP_ID=$(az ad sp list --filter "appId eq '<app-id>'" --query "[0].id" -o tsv)

# Get group ID
GROUP_ID=$(az ad group show --group "G-Usuarios-<App>-Admin" --query id -o tsv)

# Assign group
az rest --method POST \
  --uri "https://graph.microsoft.com/v1.0/servicePrincipals/$SP_ID/appRoleAssignments" \
  --body "{
    \"principalId\": \"$GROUP_ID\",
    \"principalType\": \"Group\",
    \"appRoleId\": \"00000000-0000-0000-0000-000000000000\",
    \"resourceId\": \"$SP_ID\"
  }"
```

---

### 4. Groups Not Appearing in Token

**Symptoms:**

- User can login but has no group membership
- Group-based authorization fails
- DefectDojo shows user in no groups

**Diagnosis:**

```bash
# Check group claims configuration
az ad app show --id <app-id> --query "groupMembershipClaims"
# Should return: "SecurityGroup" or "All"

# Check API permissions
az ad app permission list --id <app-id> --query "[].resourceAccess[].id"
# Should include Group.Read.All: 5f8c59db-677d-491f-a6b8-5f174b11ec1d

# Verify user is member of expected group
az ad group member check --group "<group-name>" --member-id "<user-object-id>"
```

**Solution:**

```bash
# Enable group claims
az ad app update --id <app-id> --set groupMembershipClaims=SecurityGroup

# Add Group.Read.All permission
az ad app permission add --id <app-id> \
  --api 00000003-0000-0000-c000-000000000000 \
  --api-permissions 5f8c59db-677d-491f-a6b8-5f174b11ec1d=Scope

# Grant admin consent
az ad app permission admin-consent --id <app-id>
```

**Token Verification:**

1. Login to application
2. Open browser DevTools > Application > Cookies
3. Find session/token cookie
4. Decode at <https://jwt.io>
5. Check for `groups` claim in payload

---

### 5. Client Secret Expired (AADSTS7000218)

**Symptoms:**

- Error: "The request body must contain 'client_secret'"
- Suddenly stopped working after secret expiration

**Diagnosis:**

```bash
# Check secret expiration dates
az ad app credential list --id <app-id> --query "[].{keyId:keyId,endDateTime:endDateTime}"

# Check Key Vault secret
az keyvault secret show --vault-name <vault> --name <secret-name> --query "attributes.expires"
```

**Solution:**

```bash
# Create new secret
NEW_SECRET=$(az ad app credential reset \
  --id <app-id> \
  --append \
  --years 1 \
  --query password -o tsv)

# Update Key Vault
az keyvault secret set \
  --vault-name <vault> \
  --name <secret-name> \
  --value "$NEW_SECRET"

# Restart pods to pick up new secret
kubectl rollout restart deployment/<app> -n <namespace>
```

---

### 6. Consent Required (AADSTS65001)

**Symptoms:**

- Error: "The user or administrator has not consented to use the application"

**Solution:**

```bash
# Grant admin consent
az ad app permission admin-consent --id <app-id>

# If that fails, grant via Azure Portal:
# 1. Azure Portal > App registrations > <app>
# 2. API permissions > Grant admin consent for <tenant>
```

---

## Diagnostic Commands

### Check OAuth Flow

```bash
# 1. Get the authorization redirect URL
curl -sS -k -D - -o /dev/null "https://<app>/login/<provider>/" 2>&1

# 2. Verify redirect_uri format
curl -sS -k -D - -o /dev/null "https://<app>/login/<provider>/" 2>&1 | grep -i location | sed 's/.*redirect_uri=//' | cut -d'&' -f1

# 3. Check for SSL issues
curl -sS -I "https://<app>/login/<provider>/" 2>&1 | head -20
```

### Check Application Configuration

```bash
# Check environment variables in pod
kubectl exec -n <namespace> deploy/<app> -c <container> -- env | grep -i "AZURE\|OAUTH\|SSO\|SOCIAL"

# Check if secrets are mounted
kubectl exec -n <namespace> deploy/<app> -c <container> -- ls -la /mnt/secrets-store/

# Check logs for auth errors
kubectl logs -n <namespace> deploy/<app> -c <container> --tail=100 | grep -i "auth\|oauth\|azure\|sso"
```

### Check Azure AD App Registration

```bash
# Full app details
az ad app show --id <app-id>

# Redirect URIs
az ad app show --id <app-id> --query "web.redirectUris"

# API permissions
az ad app permission list --id <app-id>

# Group claims
az ad app show --id <app-id> --query "groupMembershipClaims"

# Secret expiration
az ad app credential list --id <app-id>
```

### Check Service Principal

```bash
# Get SP details
az ad sp show --id <sp-id>

# Check user assignment requirement
az ad sp show --id <sp-id> --query "appRoleAssignmentRequired"

# List app role assignments
az rest --method GET \
  --uri "https://graph.microsoft.com/v1.0/servicePrincipals/<sp-id>/appRoleAssignments"
```

---

## Application-Specific Issues

### DefectDojo

**Issue: DD_SITE_URL is localhost**

```bash
# Check current value
kubectl exec -n monitoring deploy/defectdojo-django -c uwsgi -- env | grep DD_SITE_URL

# Fix: Use siteUrl (camelCase) in Helm values, not site_url
```

**Issue: Groups not syncing**

```yaml
# Required environment variables
- name: DD_SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_GET_GROUPS
  value: "True"
- name: DD_SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_CLEANUP_GROUPS
  value: "True"
```

### Grafana

**Issue: Role mapping not working**

```yaml
# Check JMESPath expression syntax
role_attribute_path: contains(groups[*], '<group-id>') && 'Admin' || 'Viewer'

# Debug: Check Grafana logs
kubectl logs -n monitoring deploy/grafana | grep -i "azure\|oauth\|groups"
```

### ArgoCD

**Issue: Groups not passed to RBAC**

```yaml
# Ensure groups are in scope
configs:
  rbac:
    scopes: "[groups, email]"
```

---

## CSI Driver and Secrets Issues

### Secret Not Syncing from Key Vault

**Diagnosis:**

```bash
# Check SecretProviderClass
kubectl describe secretproviderclass <name> -n <namespace>

# Check CSI driver pods
kubectl get pods -n kube-system | grep secrets-store

# Check for mount errors
kubectl describe pod <pod> -n <namespace> | grep -A 20 Events

# Check managed identity
az aks show --resource-group <rg> --name <aks> \
  --query addonProfiles.azureKeyvaultSecretsProvider.identity
```

**Common Issues:**

1. **Managed identity lacks Key Vault access**

```bash
az keyvault set-policy \
  --name <vault> \
  --spn <identity-client-id> \
  --secret-permissions get list
```

2. **Secret name mismatch**

```bash
# Verify secret exists in Key Vault
az keyvault secret list --vault-name <vault> --query "[].name"
```

3. **CSI volume not mounted**

```yaml
# Ensure pod has volume mount
extraVolumes:
  - name: secrets-store
    csi:
      driver: secrets-store.csi.k8s.io
      readOnly: true
      volumeAttributes:
        secretProviderClass: "<name>"
```

### Chicken-and-Egg Problem

**Issue:** CSI driver needs pod to mount volume to sync secret, but pod needs secret to start.

**Solution:** Create bootstrap secret manually:

```bash
# Fetch secret from Key Vault and create K8s secret
kubectl create secret generic <app>-bootstrap \
  --namespace <namespace> \
  --from-literal=client-secret="$(az keyvault secret show \
    --vault-name <vault> \
    --name <secret-name> \
    --query value -o tsv)"
```

---

## Network and Proxy Issues

### Infinite Redirect Loop

**Symptoms:**

- ERR_TOO_MANY_REDIRECTS
- Browser shows redirect loop error

**Cause:** `SECURE_SSL_REDIRECT` is True while behind a TLS-terminating proxy.

**Solution:**

```yaml
# Disable Django SSL redirect (proxy handles it)
- name: DD_SECURE_SSL_REDIRECT
  value: "False"

# Enable proxy SSL header detection
- name: DD_SECURE_PROXY_SSL_HEADER
  value: "True"
```

### CSRF Errors

**Symptoms:**

- 403 Forbidden on POST requests
- "CSRF verification failed" error

**Solution:**

```yaml
# Add trusted origins
- name: DD_CSRF_TRUSTED_ORIGINS
  value: "https://<domain>"
```

### Timeout Connecting to Azure AD

**Symptoms:**

- Connection timeout to login.microsoftonline.com
- "Could not connect to identity provider"

**Solutions:**

1. Check egress network policies
2. Verify DNS resolution
3. Check proxy configuration
4. Test connectivity from pod:

```bash
kubectl exec -n <namespace> deploy/<app> -c <container> -- \
  curl -I https://login.microsoftonline.com/<tenant-id>/.well-known/openid-configuration
```

---

## Quick Troubleshooting Checklist

### Before Login Attempt

- [ ] App Registration exists with correct redirect URI
- [ ] Client secret is valid (not expired)
- [ ] Secret is in Key Vault
- [ ] SecretProviderClass is configured
- [ ] K8s secret is created
- [ ] Pod has CSI volume mounted
- [ ] Environment variables are set correctly

### During Login

- [ ] Redirect to Azure AD works
- [ ] redirect_uri is properly formed
- [ ] User is member of allowed group (if restricted)
- [ ] MFA/Conditional Access policies pass

### After Login

- [ ] Groups appear in token
- [ ] Groups sync to application
- [ ] Role mapping works correctly
- [ ] Session is created properly

### Azure CLI Quick Checks

```bash
# Full diagnostic in one command
APP_ID="<your-app-id>"

echo "=== App Registration ==="
az ad app show --id $APP_ID --query "{name:displayName, appId:appId, redirectUris:web.redirectUris, groupClaims:groupMembershipClaims}"

echo "=== Service Principal ==="
SP_ID=$(az ad sp list --filter "appId eq '$APP_ID'" --query "[0].id" -o tsv)
az ad sp show --id $SP_ID --query "{assignmentRequired:appRoleAssignmentRequired}"

echo "=== Credentials ==="
az ad app credential list --id $APP_ID --query "[].{keyId:keyId,expires:endDateTime}"

echo "=== API Permissions ==="
az ad app permission list --id $APP_ID
```
