# Azure AD SSO Configuration for DefectDojo

## Azure AD App Registration Setup

### Step 1: Create App Registration

1. Go to Azure Portal > Azure Active Directory > App registrations
2. Click "New registration"
3. Configure:
   - Name: `DefectDojo`
   - Supported account types: "Accounts in this organizational directory only"
   - Redirect URI: Web - `https://defectdojo.dev.cafehyna.com.br/complete/azuread-tenant-oauth2/`

### Step 2: Configure API Permissions

Add these **Application** permissions (not Delegated):

| Permission | Type | Purpose |
|------------|------|---------|
| `Group.Read.All` | Application | Read all groups |
| `GroupMember.Read.All` | Application | Read group memberships |
| `User.Read.All` | Application | Read user profiles |

**Grant admin consent** after adding permissions.

### Step 3: Configure Token Claims

1. Go to App Registration > Token configuration
2. Add Groups claim:
   - Click "Add groups claim"
   - Select "All groups"
   - **Important:** Do NOT check "Emit groups as role claims"

### Step 4: Create Client Secret

1. Go to Certificates & secrets
2. Create new client secret
3. Store in Azure Key Vault as `defectdojo-azuread-client-secret`

## DefectDojo Environment Variables

### Required Variables

```yaml
extraEnv:
  # Enable Azure AD OAuth2 authentication
  - name: DD_SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_ENABLED
    value: "True"

  # Azure AD Application (client) ID
  - name: DD_SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_KEY
    value: "79ada8c7-4270-41e8-9ea0-1e1e62afff3d"

  # Azure AD Directory (tenant) ID
  - name: DD_SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_TENANT_ID
    value: "3f7a3df4-f85b-4ca8-98d0-08b1034e6567"

  # Azure AD Client Secret (from Key Vault)
  - name: DD_SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_SECRET
    valueFrom:
      secretKeyRef:
        name: defectdojo
        key: DD_SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_SECRET
```

### Group Synchronization Variables

```yaml
extraEnv:
  # Enable group sync from Azure AD
  - name: DD_SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_GET_GROUPS
    value: "True"

  # Clean up empty groups
  - name: DD_SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_CLEANUP_GROUPS
    value: "True"

  # Filter groups by regex pattern
  - name: DD_SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_GROUPS_FILTER
    value: "^G-Usuarios-DefectDojo-.*"
```

### SSL/Security Variables

Required when behind a TLS-terminating proxy:

```yaml
extraEnv:
  # Secure cookies
  - name: DD_SESSION_COOKIE_SECURE
    value: "True"
  - name: DD_CSRF_COOKIE_SECURE
    value: "True"

  # Trust proxy headers
  - name: DD_SECURE_PROXY_SSL_HEADER
    value: "True"

  # IMPORTANT: Set to False behind NGINX Ingress to avoid redirect loops
  - name: DD_SECURE_SSL_REDIRECT
    value: "False"
```

### Optional SSO Behavior Variables

```yaml
extraEnv:
  # Auto-redirect to Azure AD login (skip username/password form)
  - name: DD_SOCIAL_LOGIN_AUTO_REDIRECT
    value: "True"

  # Hide traditional login form
  - name: DD_SOCIAL_AUTH_SHOW_LOGIN_FORM
    value: "False"
```

## Azure AD Groups for DefectDojo Roles

### Recommended Group Structure

| Azure AD Group Name | DefectDojo Role | Description |
|---------------------|-----------------|-------------|
| `G-Usuarios-DefectDojo-Superuser` | Superuser | Full admin access (is_superuser=true) |
| `G-Usuarios-DefectDojo-Owner` | Owner | Can delete products, manage members |
| `G-Usuarios-DefectDojo-Maintainer` | Maintainer | Edit settings, delete findings |
| `G-Usuarios-DefectDojo-Writer` | Writer | Add/edit engagements, tests, findings |
| `G-Usuarios-DefectDojo-Reader` | Reader | View-only, add comments |
| `G-Usuarios-DefectDojo-APIImporter` | API Importer | CI/CD pipeline scan imports |

### Setting Up Group-Role Mapping

1. **Create Azure AD Groups:**
   - Go to Azure Portal > Azure Active Directory > Groups
   - Create groups matching the naming pattern above
   - Add users to appropriate groups

2. **Enable Group Sync in DefectDojo:**

   ```yaml
   - name: DD_SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_GET_GROUPS
     value: "True"
   - name: DD_SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_GROUPS_FILTER
     value: "^G-Usuarios-DefectDojo-.*"
   ```

3. **Create Matching Groups in DefectDojo:**
   - Go to DefectDojo > Configuration > Groups
   - Create groups with exact same names as Azure AD groups
   - Assign appropriate Global Role to each group

4. **User Login:**
   - Users log in via Azure AD SSO
   - Groups are synced during login
   - Users inherit roles from their group memberships

## Troubleshooting SSO Issues

### Error: ADSTS50011 - Redirect URI Mismatch

**Cause:** Azure AD requires HTTPS, but DefectDojo sending HTTP redirect

**Solution:**

1. Verify redirect URI in Azure AD is exactly:
   `https://defectdojo.dev.cafehyna.com.br/complete/azuread-tenant-oauth2/`
2. Set SSL environment variables:

   ```yaml
   - name: DD_SESSION_COOKIE_SECURE
     value: "True"
   - name: DD_CSRF_COOKIE_SECURE
     value: "True"
   - name: DD_SECURE_PROXY_SSL_HEADER
     value: "True"
   ```

### Error: Groups Not Syncing

**Symptoms:** User logged in but shows "No group members found"

**Checklist:**

- [ ] `DD_SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_GET_GROUPS=True`
- [ ] Azure AD App has `Group.Read.All` permission (Application type)
- [ ] Admin consent granted for API permissions
- [ ] Token configuration has Groups claim (not role claims)
- [ ] "Emit groups as role claims" is NOT enabled
- [ ] User logged out and back in after configuration change
- [ ] Matching groups exist in DefectDojo UI

### Error: 403 Forbidden from Graph API

**Cause:** Missing or incorrect API permissions

**Solution:**

1. Go to Azure AD > App Registration > API Permissions
2. Add `Group.Read.All` as Application permission
3. Click "Grant admin consent"
4. Restart DefectDojo pods

### Emergency Access

If SSO is broken and you're locked out:

```
https://defectdojo.dev.cafehyna.com.br/login?force_login_form
```

This bypasses SSO redirect and shows the standard login form.
