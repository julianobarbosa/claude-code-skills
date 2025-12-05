# Application-Specific Azure AD SSO Configurations

This document provides complete, production-ready configurations for integrating various applications with Azure AD SSO.

## Table of Contents

1. [DefectDojo](#defectdojo)
2. [Grafana](#grafana)
3. [ArgoCD](#argocd)
4. [Harbor](#harbor)
5. [SonarQube](#sonarqube)
6. [Keycloak](#keycloak)
7. [OAuth2 Proxy](#oauth2-proxy)
8. [Vault (HashiCorp)](#vault-hashicorp)

---

## DefectDojo

### Azure AD App Registration

| Setting | Value |
|---------|-------|
| Redirect URI | `https://<domain>/complete/azuread-tenant-oauth2/` |
| API Permissions | `User.Read`, `Group.Read.All` (delegated) |
| Token Claims | Security groups (Group ID) |
| Provider | `azuread-tenant-oauth2` |

### Helm Values Configuration

```yaml
# values.yaml for DefectDojo

# Disable Helm secret creation - use CSI Driver instead
createSecret: false

# Site URL for OAuth redirects
siteUrl: https://defectdojo.<domain>

# Environment variables for Azure AD SSO
extraEnv:
  # -------------------------------------------------------------------------
  # Azure AD SSO Configuration
  # -------------------------------------------------------------------------
  - name: DD_SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_ENABLED
    value: "True"

  # Application (client) ID from Azure AD App Registration
  - name: DD_SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_KEY
    value: "<client-id>"

  # Directory (tenant) ID
  - name: DD_SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_TENANT_ID
    value: "<tenant-id>"

  # Client Secret from Kubernetes secret (synced from Key Vault)
  - name: DD_SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_SECRET
    valueFrom:
      secretKeyRef:
        name: defectdojo
        key: DD_SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_SECRET

  # -------------------------------------------------------------------------
  # Group Synchronization
  # -------------------------------------------------------------------------
  - name: DD_SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_GET_GROUPS
    value: "True"

  - name: DD_SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_CLEANUP_GROUPS
    value: "True"

  # Filter groups by regex pattern
  - name: DD_SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_GROUPS_FILTER
    value: "^G-Usuarios-DefectDojo-.*"

  # -------------------------------------------------------------------------
  # Proxy/SSL Configuration (CRITICAL for apps behind Ingress)
  # -------------------------------------------------------------------------
  # Trust X-Forwarded-Proto header from reverse proxy
  - name: DD_SECURE_PROXY_SSL_HEADER
    value: "True"

  # Disable Django SSL redirect (handled by Ingress)
  - name: DD_SECURE_SSL_REDIRECT
    value: "False"

  # CSRF trusted origins
  - name: DD_CSRF_TRUSTED_ORIGINS
    value: "https://defectdojo.<domain>"

  # -------------------------------------------------------------------------
  # Optional: Auto-redirect to SSO (after confirming SSO works)
  # -------------------------------------------------------------------------
  # - name: DD_SOCIAL_LOGIN_AUTO_REDIRECT
  #   value: "True"
  # - name: DD_SOCIAL_AUTH_SHOW_LOGIN_FORM
  #   value: "False"

# CSI Driver volume mount for secrets
extraVolumes:
  - name: secrets-store
    csi:
      driver: secrets-store.csi.k8s.io
      readOnly: true
      volumeAttributes:
        secretProviderClass: "defectdojo-secrets"

extraVolumeMounts:
  - name: secrets-store
    mountPath: "/mnt/secrets-store"
    readOnly: true
```

### SecretProviderClass

```yaml
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: defectdojo-secrets
  namespace: monitoring
spec:
  provider: azure
  parameters:
    usePodIdentity: "false"
    useVMManagedIdentity: "true"
    userAssignedIdentityID: "<managed-identity-client-id>"
    keyvaultName: "<keyvault-name>"
    tenantId: "<tenant-id>"
    objects: |
      array:
        - |
          objectName: defectdojo-azuread-client-secret
          objectType: secret
          objectAlias: DD_SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_SECRET
        - |
          objectName: defectdojo-admin-password
          objectType: secret
          objectAlias: DD_ADMIN_PASSWORD
        - |
          objectName: defectdojo-secret-key
          objectType: secret
          objectAlias: DD_SECRET_KEY
        - |
          objectName: defectdojo-credential-aes-key
          objectType: secret
          objectAlias: DD_CREDENTIAL_AES_256_KEY
  secretObjects:
    - secretName: defectdojo
      type: Opaque
      data:
        - objectName: DD_SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_SECRET
          key: DD_SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_SECRET
        - objectName: DD_ADMIN_PASSWORD
          key: DD_ADMIN_PASSWORD
        - objectName: DD_SECRET_KEY
          key: DD_SECRET_KEY
        - objectName: DD_CREDENTIAL_AES_256_KEY
          key: DD_CREDENTIAL_AES_256_KEY
```

---

## Grafana

### Azure AD App Registration

| Setting | Value |
|---------|-------|
| Redirect URI | `https://<domain>/login/azuread` |
| API Permissions | `User.Read`, `Group.Read.All` (delegated) |
| Token Claims | Security groups (Group ID) |
| Provider | `azuread` |

### Helm Values Configuration

```yaml
# values.yaml for Grafana (kube-prometheus-stack or standalone)

grafana:
  grafana.ini:
    server:
      root_url: https://grafana.<domain>

    auth:
      disable_login_form: false  # Set true after SSO verified
      disable_signout_menu: false

    auth.azuread:
      enabled: true
      name: Azure AD
      allow_sign_up: true
      auto_login: false  # Set true after SSO verified

      # Azure AD credentials
      client_id: "<client-id>"
      client_secret: "${GF_AUTH_AZUREAD_CLIENT_SECRET}"

      # OAuth2 endpoints
      scopes: openid email profile
      auth_url: https://login.microsoftonline.com/<tenant-id>/oauth2/v2.0/authorize
      token_url: https://login.microsoftonline.com/<tenant-id>/oauth2/v2.0/token

      # Domain restriction
      allowed_domains: <your-domain.com>

      # Group-based access control
      allowed_groups: "<admin-group-id> <editor-group-id> <viewer-group-id>"

      # Role mapping based on group membership
      # JMESPath expression to map Azure AD groups to Grafana roles
      role_attribute_path: >-
        contains(groups[*], '<admin-group-id>') && 'Admin' ||
        contains(groups[*], '<editor-group-id>') && 'Editor' ||
        'Viewer'

      # Skip org role sync if managing via API
      skip_org_role_sync: false

  # Environment variables for secrets
  envFromSecret: grafana-azure-ad-secret

  # Or use envValueFrom for specific values
  envValueFrom:
    GF_AUTH_AZUREAD_CLIENT_SECRET:
      secretKeyRef:
        name: grafana-azure-ad
        key: client-secret
```

### Secret for Grafana

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: grafana-azure-ad
  namespace: monitoring
type: Opaque
stringData:
  client-secret: "<azure-ad-client-secret>"
```

---

## ArgoCD

### Azure AD App Registration

| Setting | Value |
|---------|-------|
| Redirect URI | `https://<domain>/api/dex/callback` |
| API Permissions | `User.Read`, `Group.Read.All` (delegated) |
| Token Claims | Security groups (Group ID) |
| Provider | `microsoft` (via Dex) |

### Helm Values Configuration

```yaml
# values.yaml for ArgoCD

configs:
  cm:
    url: https://argocd.<domain>

    # Dex configuration for Azure AD
    dex.config: |
      connectors:
        - type: microsoft
          id: microsoft
          name: Microsoft Azure AD
          config:
            clientID: "<client-id>"
            clientSecret: $dex.azure.clientSecret
            tenant: "<tenant-id>"
            redirectURI: https://argocd.<domain>/api/dex/callback

            # Restrict to specific groups
            groups:
              - <argocd-admins-group-id>
              - <argocd-readonly-group-id>

            # Include group IDs in claims
            groupsClaimType: "groups"

            # Optional: Use group names instead of IDs
            # useGroupsAsWhitelist: true

  # RBAC configuration
  rbac:
    # Policy CSV for group-based authorization
    policy.csv: |
      # Admin role for Azure AD admin group
      g, <argocd-admins-group-id>, role:admin

      # Read-only role for viewer group
      g, <argocd-readonly-group-id>, role:readonly

      # Custom policies
      p, role:developer, applications, get, */*, allow
      p, role:developer, applications, sync, */*, allow
      p, role:developer, logs, get, */*, allow
      g, <developer-group-id>, role:developer

    # Default policy for authenticated users
    policy.default: role:readonly

    # Map SSO groups to ArgoCD roles
    scopes: "[groups, email]"

  # Secret for Dex
  secret:
    extra:
      dex.azure.clientSecret: "<client-secret>"
```

---

## Harbor

### Azure AD App Registration

| Setting | Value |
|---------|-------|
| Redirect URI | `https://<domain>/c/oidc/callback` |
| API Permissions | `User.Read`, `Group.Read.All` (delegated) |
| Token Claims | Security groups (Group ID) |
| Provider | `oidc` |

### Helm Values Configuration

```yaml
# values.yaml for Harbor

externalURL: https://harbor.<domain>

expose:
  type: ingress
  ingress:
    hosts:
      core: harbor.<domain>
    className: nginx
    annotations:
      cert-manager.io/cluster-issuer: letsencrypt-prod-cloudflare

# OIDC configuration for Azure AD
core:
  # Configure OIDC via values (alternative to UI configuration)
  configOverwriteJson: |
    {
      "auth_mode": "oidc_auth",
      "oidc_name": "azure",
      "oidc_endpoint": "https://login.microsoftonline.com/<tenant-id>/v2.0",
      "oidc_client_id": "<client-id>",
      "oidc_client_secret": "<from-secret>",
      "oidc_scope": "openid,profile,email,offline_access",
      "oidc_groups_claim": "groups",
      "oidc_admin_group": "<admin-group-id>",
      "oidc_verify_cert": true,
      "oidc_auto_onboard": true,
      "oidc_user_claim": "preferred_username"
    }

# Secret reference for OIDC client secret
core:
  secretName: harbor-oidc-secret
```

### Secret for Harbor OIDC

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: harbor-oidc-secret
  namespace: harbor
type: Opaque
stringData:
  OIDC_CLIENT_SECRET: "<azure-ad-client-secret>"
```

---

## SonarQube

### Azure AD App Registration

| Setting | Value |
|---------|-------|
| Redirect URI | `https://<domain>/oauth2/callback/saml` (SAML) or `https://<domain>/oauth2/callback/oidc` (OIDC) |
| API Permissions | `User.Read`, `Group.Read.All` (delegated) |
| Token Claims | Security groups (Group ID) |

### Helm Values Configuration (OIDC)

```yaml
# values.yaml for SonarQube

sonarProperties:
  # OIDC Authentication
  sonar.auth.oidc.enabled: true
  sonar.auth.oidc.issuerUri: https://login.microsoftonline.com/<tenant-id>/v2.0
  sonar.auth.oidc.clientId.secured: "<client-id>"
  sonar.auth.oidc.clientSecret.secured: "${SONAR_AUTH_OIDC_CLIENT_SECRET}"
  sonar.auth.oidc.scopes: openid profile email
  sonar.auth.oidc.groupsSync: true
  sonar.auth.oidc.groupsSync.claimName: groups

  # Group mapping
  sonar.auth.oidc.allowedGroups: "<admin-group-id>,<developer-group-id>"

  # Admin group
  sonar.auth.oidc.adminGroup: "<admin-group-id>"

# Environment variables
extraEnv:
  - name: SONAR_AUTH_OIDC_CLIENT_SECRET
    valueFrom:
      secretKeyRef:
        name: sonarqube-oidc
        key: client-secret
```

---

## Keycloak

### Azure AD App Registration

| Setting | Value |
|---------|-------|
| Redirect URI | `https://<domain>/realms/<realm>/broker/azure/endpoint` |
| API Permissions | `User.Read`, `Group.Read.All` (delegated) |
| Token Claims | Security groups (Group ID) |

### Identity Provider Configuration (via CRD or Admin Console)

```yaml
# KeycloakRealmImport CRD for Azure AD Identity Provider
apiVersion: k8s.keycloak.org/v2alpha1
kind: KeycloakRealmImport
metadata:
  name: azure-ad-idp
  namespace: keycloak
spec:
  keycloakCRName: keycloak
  realm:
    realm: <realm-name>
    identityProviders:
      - alias: azure
        providerId: oidc
        enabled: true
        trustEmail: true
        storeToken: true
        firstBrokerLoginFlowAlias: first broker login
        config:
          clientId: "<client-id>"
          clientSecret: "<client-secret>"
          tokenUrl: "https://login.microsoftonline.com/<tenant-id>/oauth2/v2.0/token"
          authorizationUrl: "https://login.microsoftonline.com/<tenant-id>/oauth2/v2.0/authorize"
          logoutUrl: "https://login.microsoftonline.com/<tenant-id>/oauth2/v2.0/logout"
          userInfoUrl: "https://graph.microsoft.com/oidc/userinfo"
          issuer: "https://login.microsoftonline.com/<tenant-id>/v2.0"
          defaultScope: "openid profile email"
          syncMode: INHERIT
```

---

## OAuth2 Proxy

### Azure AD App Registration

| Setting | Value |
|---------|-------|
| Redirect URI | `https://<domain>/oauth2/callback` |
| API Permissions | `User.Read`, `Group.Read.All` (delegated) |
| Token Claims | Security groups (Group ID) |
| Provider | `azure` |

### Helm Values Configuration

```yaml
# values.yaml for OAuth2 Proxy

config:
  clientID: "<client-id>"
  clientSecret: "<client-secret>"
  cookieSecret: "<random-32-byte-base64>"

extraArgs:
  provider: azure
  azure-tenant: "<tenant-id>"
  oidc-issuer-url: "https://login.microsoftonline.com/<tenant-id>/v2.0"

  # Access control
  allowed-group: "<allowed-group-id>"

  # Email domain restriction
  email-domain: "<your-domain.com>"

  # Cookie settings
  cookie-secure: true
  cookie-httponly: true
  cookie-samesite: lax

  # Upstream configuration
  upstream: "http://<backend-service>.<namespace>.svc.cluster.local"

  # Pass headers to upstream
  pass-access-token: true
  pass-authorization-header: true
  set-xauthrequest: true

ingress:
  enabled: true
  className: nginx
  hosts:
    - <domain>
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod-cloudflare
```

---

## Vault (HashiCorp)

### Azure AD App Registration

| Setting | Value |
|---------|-------|
| Redirect URI | `https://<domain>/ui/vault/auth/oidc/oidc/callback` |
| API Permissions | `User.Read`, `Group.Read.All` (delegated) |
| Token Claims | Security groups (Group ID) |

### Vault OIDC Configuration

```bash
# Enable OIDC auth method
vault auth enable oidc

# Configure OIDC
vault write auth/oidc/config \
  oidc_discovery_url="https://login.microsoftonline.com/<tenant-id>/v2.0" \
  oidc_client_id="<client-id>" \
  oidc_client_secret="<client-secret>" \
  default_role="reader"

# Create role for admin group
vault write auth/oidc/role/admin \
  bound_audiences="<client-id>" \
  allowed_redirect_uris="https://<domain>/ui/vault/auth/oidc/oidc/callback" \
  allowed_redirect_uris="https://<domain>/oidc/callback" \
  user_claim="email" \
  groups_claim="groups" \
  bound_claims_type="string" \
  bound_claims='{"groups":"<admin-group-id>"}' \
  token_policies="admin"

# Create role for reader group
vault write auth/oidc/role/reader \
  bound_audiences="<client-id>" \
  allowed_redirect_uris="https://<domain>/ui/vault/auth/oidc/oidc/callback" \
  allowed_redirect_uris="https://<domain>/oidc/callback" \
  user_claim="email" \
  groups_claim="groups" \
  token_policies="reader"
```

### Helm Values Configuration

```yaml
# values.yaml for Vault

server:
  extraEnvironmentVars:
    VAULT_ADDR: https://vault.<domain>

  # HA configuration with OIDC
  ha:
    enabled: true
    raft:
      enabled: true
      config: |
        ui = true
        listener "tcp" {
          address = "[::]:8200"
          cluster_address = "[::]:8201"
          tls_disable = 1
        }

        storage "raft" {
          path = "/vault/data"
        }

        service_registration "kubernetes" {}

ui:
  enabled: true

ingress:
  enabled: true
  hosts:
    - host: vault.<domain>
```

---

## Common Patterns

### Bootstrap Secret for CSI Driver

When using CSI Driver, a bootstrap secret may be needed to break the chicken-and-egg cycle:

```bash
# Create bootstrap secret from Key Vault
kubectl create secret generic <app>-bootstrap \
  --namespace <namespace> \
  --from-literal=client-secret="$(az keyvault secret show \
    --vault-name <vault> \
    --name <secret-name> \
    --query value -o tsv)"
```

### Ingress Annotations for OAuth2 Proxy

```yaml
annotations:
  nginx.ingress.kubernetes.io/auth-url: "https://oauth2-proxy.<domain>/oauth2/auth"
  nginx.ingress.kubernetes.io/auth-signin: "https://oauth2-proxy.<domain>/oauth2/start?rd=$scheme://$host$escaped_request_uri"
  nginx.ingress.kubernetes.io/auth-response-headers: "X-Auth-Request-User,X-Auth-Request-Email,X-Auth-Request-Groups"
```

### Testing OAuth Flow

```bash
# Get authorization URL
curl -sS -k -D - -o /dev/null "https://<app>/login/<provider>/" 2>&1 | grep -i location

# Verify redirect_uri format
# Should be: redirect_uri=https://<domain>/complete/<provider>/
# NOT: redirect_uri=https,%20https://...
```
