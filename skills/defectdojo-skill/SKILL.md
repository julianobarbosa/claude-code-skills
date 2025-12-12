---
name: defectdojo
description: DefectDojo vulnerability management platform configuration and troubleshooting. Use when configuring Azure AD SSO, group synchronization, Helm chart values, API integration, or troubleshooting login/permission issues.
---

# DefectDojo Skill

## Overview

DefectDojo is an Application Security Pipeline Platform for vulnerability management. This skill covers configuration for Kubernetes deployments using Helm, Azure AD SSO integration, and troubleshooting common issues.

## Quick Reference

### Project File Locations

| File Type | Path |
|-----------|------|
| ApplicationSet | `infra-team/applicationset/defectdojo.yaml` |
| Helm Values | `argo-cd-helm-values/kube-addons/defectdojo/<cluster>/values.yaml` |
| SecretProviderClass | `argo-cd-helm-values/kube-addons/defectdojo/<cluster>/secretproviderclass.yaml` |

### Environment Configuration

| Cluster | Key Vault | Azure AD Tenant ID |
|---------|-----------|-------------------|
| cafehyna-dev | `kv-cafehyna-dev-hlg` | `3f7a3df4-f85b-4ca8-98d0-08b1034e6567` |

### Azure AD App Registration

| Setting | Value |
|---------|-------|
| Application (Client) ID | `79ada8c7-4270-41e8-9ea0-1e1e62afff3d` |
| Tenant ID | `3f7a3df4-f85b-4ca8-98d0-08b1034e6567` |
| Redirect URI | `https://defectdojo.dev.cafehyna.com.br/complete/azuread-tenant-oauth2/` |

## Azure AD SSO Configuration

### Required Environment Variables

```yaml
extraEnv:
  # Enable Azure AD OAuth2
  - name: DD_SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_ENABLED
    value: "True"
  # Application (Client) ID
  - name: DD_SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_KEY
    value: "<client-id>"
  # Directory (Tenant) ID
  - name: DD_SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_TENANT_ID
    value: "<tenant-id>"
  # Client Secret (from Key Vault)
  - name: DD_SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_SECRET
    valueFrom:
      secretKeyRef:
        name: defectdojo
        key: DD_SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_SECRET
```

### Group Synchronization

Enable automatic group sync from Azure AD:

```yaml
extraEnv:
  # Sync groups from Azure AD token
  - name: DD_SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_GET_GROUPS
    value: "True"
  # Remove users from groups when removed in Azure AD
  - name: DD_SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_CLEANUP_GROUPS
    value: "True"
  # Filter to only sync DefectDojo groups
  - name: DD_SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_GROUPS_FILTER
    value: "^G-Usuarios-DefectDojo-.*"
```

**Required Azure AD Permissions (Application type, Admin consent required):**

- `Group.Read.All`
- `GroupMember.Read.All`
- `User.Read.All`

**Azure AD Token Configuration:**

- Add Groups claim (select "All Groups")
- Do NOT enable "Emit groups as role claims"

For complete Azure AD SSO details, see [references/azure-ad-sso.md](references/azure-ad-sso.md).

## DefectDojo Roles

| Role | Permissions |
|------|-------------|
| **Superuser** | Full system access, manage users, system settings |
| **Owner** | Delete products, designate other owners |
| **Maintainer** | Edit products, add members, delete findings |
| **Writer** | Add/edit engagements, tests, findings |
| **Reader** | View-only, add comments |
| **API Importer** | Limited API access for CI/CD pipelines |

### Azure AD Groups for Role Mapping

| Azure AD Group | DefectDojo Role |
|----------------|-----------------|
| `G-Usuarios-DefectDojo-Superuser` | Superuser |
| `G-Usuarios-DefectDojo-Owner` | Owner |
| `G-Usuarios-DefectDojo-Maintainer` | Maintainer |
| `G-Usuarios-DefectDojo-Writer` | Writer |
| `G-Usuarios-DefectDojo-Reader` | Reader |

**Setup Steps:**

1. Create Azure AD groups matching the pattern above
2. Enable group sync in DefectDojo (`DD_SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_GET_GROUPS=True`)
3. Create matching groups in DefectDojo (Configuration > Groups)
4. Assign Global Roles to each DefectDojo group
5. Users inherit roles when they log in via SSO

## Common Troubleshooting

### User Not in Groups After SSO Login

**Symptoms:** User logged in via Azure AD but shows "No group members found"

**Solutions:**

1. Verify `DD_SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_GET_GROUPS=True`
2. Check Azure AD API permissions (Group.Read.All with admin consent)
3. Verify Azure AD token includes group claim (not role claims)
4. User must log out and log back in to sync groups
5. Create matching groups in DefectDojo UI

### HTTPS Redirect URI Mismatch (ADSTS50011)

**Error:** "The redirect URI specified in the request does not match"

**Solution:** Ensure these are set:

```yaml
- name: DD_SESSION_COOKIE_SECURE
  value: "True"
- name: DD_CSRF_COOKIE_SECURE
  value: "True"
- name: DD_SECURE_PROXY_SSL_HEADER
  value: "True"
```

### ERR_TOO_MANY_REDIRECTS

**Cause:** `DD_SECURE_SSL_REDIRECT=True` with TLS-terminating proxy

**Solution:** Set `DD_SECURE_SSL_REDIRECT=False` when behind NGINX Ingress

### Emergency Login Access

If SSO breaks, access standard login form:

```
https://defectdojo.dev.cafehyna.com.br/login?force_login_form
```

For complete troubleshooting guide, see [references/troubleshooting.md](references/troubleshooting.md).

## Helm Chart Quick Reference

### Key Values

```yaml
# Host configuration
host: defectdojo.dev.cafehyna.com.br
siteUrl: https://defectdojo.dev.cafehyna.com.br

# Secrets (use CSI driver)
createSecret: false
disableHooks: true

# Django
django:
  replicas: 1
  ingress:
    enabled: true
    activateTLS: true
    className: nginx

# Celery (keep beat at 1 replica)
celery:
  beat:
    enabled: true
    replicas: 1
  worker:
    enabled: true
    replicas: 1

# Database
postgresql:
  enabled: true

# Cache
redis:
  enabled: true
```

For complete Helm values reference, see [references/helm-values.md](references/helm-values.md).

## Secrets Management

Secrets are managed via Azure Key Vault CSI Driver:

| Key Vault Secret | K8s Secret Key | Purpose |
|------------------|----------------|---------|
| `defectdojo-admin-password` | `DD_ADMIN_PASSWORD` | Admin user password |
| `defectdojo-secret-key` | `DD_SECRET_KEY` | Django secret key |
| `defectdojo-credential-aes-key` | `DD_CREDENTIAL_AES_256_KEY` | Credential encryption |
| `defectdojo-azuread-client-secret` | `DD_SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_SECRET` | Azure AD client secret |

## API Integration

### Get API Token

User Profile > API v2 Key

### Import Scan Results

```bash
curl -X POST "https://defectdojo.dev.cafehyna.com.br/api/v2/import-scan/" \
  -H "Authorization: Token <api-token>" \
  -F "scan_type=<scanner-type>" \
  -F "file=@results.json" \
  -F "engagement=<engagement-id>"
```

## Useful Commands

### Check Pod Status

```bash
KUBECONFIG=~/.kube/aks-rg-hypera-cafehyna-dev-config kubectl get pods -n defectdojo
```

### View Logs

```bash
KUBECONFIG=~/.kube/aks-rg-hypera-cafehyna-dev-config kubectl logs -n defectdojo -l app.kubernetes.io/name=defectdojo -c uwsgi
```

### Restart Deployment

```bash
KUBECONFIG=~/.kube/aks-rg-hypera-cafehyna-dev-config kubectl rollout restart deployment/defectdojo-django -n defectdojo
```

## Additional References

- [Azure AD SSO Configuration](references/azure-ad-sso.md) - Complete SSO setup guide
- [Helm Values Reference](references/helm-values.md) - Full Helm chart configuration
- [Troubleshooting Guide](references/troubleshooting.md) - Common issues and solutions
- [Official Documentation](https://documentation.defectdojo.com/)
