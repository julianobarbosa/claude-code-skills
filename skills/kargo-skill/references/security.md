# Kargo Security Reference

Comprehensive guide to Kargo security configuration, access controls, and credential management.

## Authentication Overview

Kargo implements a two-tier security model:

1. **IDP Authentication:** External identity providers via OpenID Connect (OIDC)
2. **Kubernetes RBAC Authorization:** Users mapped to ServiceAccounts for access control

## OpenID Connect (OIDC) Configuration

### Basic OIDC Setup

```yaml
# Helm values
api:
  oidc:
    enabled: true
    issuerURL: https://idp.example.com
    clientID: kargo-ui
    cliClientID: kargo-cli  # Optional, if different client
    additionalScopes:
      - groups
```

### IDP Callback URLs

**For OIDC + PKCE compatible IDPs:**

```
https://<api-server>/login           # UI
http://localhost/auth/callback       # CLI
```

**For IDPs requiring Dex:**

```
https://<api-server>/dex/callback    # Both UI and CLI
```

### Dex Integration (for incompatible IDPs)

```yaml
api:
  oidc:
    enabled: true
    dex:
      enabled: true
      connectors:
        - type: github
          id: github
          name: GitHub
          config:
            clientID: <github-client-id>
            clientSecret: $CLIENT_SECRET
            redirectURI: https://<api-server>/dex/callback
            orgs:
              - name: my-org
                teams:
                  - devops
      env:
        - name: CLIENT_SECRET
          valueFrom:
            secretKeyRef:
              name: github-dex
              key: clientSecret
```

### System Role Configuration

```yaml
api:
  oidc:
    admins:
      claims:
        email:
          - alice@example.com
          - bob@example.com
        groups:
          - kargo-admins
    projectCreators:
      claims:
        groups:
          - leads
    viewers:
      claims:
        groups:
          - devops
    users:
      claims:
        groups:
          - developers
```

**System Roles:**

| ServiceAccount | Config Key | Permissions |
|---------------|------------|-------------|
| `kargo-admin` | `api.oidc.admins` | Cluster-wide access to all resources |
| `kargo-viewer` | `api.oidc.viewers` | Read-only cluster-wide (no Secrets) |
| `kargo-user` | `api.oidc.users` | List projects, view config |
| `kargo-project-creator` | `api.oidc.projectCreators` | User + project creation |

## User-to-ServiceAccount Mapping

### Annotation-Based Mapping

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: admin
  namespace: my-project
  annotations:
    rbac.kargo.akuity.io/claims: |
      {
        "sub": ["alice", "bob"],
        "email": "carl@example.com",
        "groups": ["devops", "kargo-admin"]
      }
```

### Alternative Format (Backward Compatible)

```yaml
annotations:
  rbac.kargo.akuity.io/claim.sub: alice,bob
  rbac.kargo.akuity.io/claim.email: carl@example.com
  rbac.kargo.akuity.io/claim.groups: devops,kargo-admin
```

### Multi-ServiceAccount Binding

Users mapped to multiple ServiceAccounts get the **union** of all permissions:

```yaml
# Developer ServiceAccount
apiVersion: v1
kind: ServiceAccount
metadata:
  name: developer
  annotations:
    rbac.kargo.akuity.io/claims: '{"groups":["developers"]}'
---
# Promoter ServiceAccount
apiVersion: v1
kind: ServiceAccount
metadata:
  name: promoter
  annotations:
    rbac.kargo.akuity.io/claims: '{"groups":["devops"]}'
```

## Project-Level RBAC

### Pre-defined Roles

| Role | Description |
|------|-------------|
| `default` | Kubernetes-managed, non-modifiable |
| `kargo-admin` | Full project management |
| `kargo-viewer` | Read-only project access |

### Custom Role with Permissions

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: promoter
  namespace: my-project
  annotations:
    rbac.kargo.akuity.io/claims: '{"groups":["devops"]}'
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: promoter
  namespace: my-project
rules:
- apiGroups: [kargo.akuity.io]
  resources: [promotions]
  verbs: [create, patch, update]
- apiGroups: [kargo.akuity.io]
  resources: [stages]
  verbs: [promote]  # Custom Kargo verb
  resourceNames: [dev, staging]  # Specific stages only
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: promoter
  namespace: my-project
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: promoter
subjects:
- kind: ServiceAccount
  name: promoter
  namespace: my-project
```

### Custom Kargo RBAC Verbs

Kargo extends standard Kubernetes verbs:

| Verb | Description |
|------|-------------|
| `promote` | Authorize stage promotion initiation |

### Cross-Namespace RoleBinding

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: global-developer
  namespace: my-project
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: kargo-admin
subjects:
- kind: ServiceAccount
  name: team-x-developers
  namespace: kargo-global-service-accounts
```

### Global ServiceAccount Namespaces

```yaml
api:
  oidc:
    globalServiceAccounts:
      namespaces:
        - kargo-global-service-accounts
```

## CLI Role Management

```bash
# List roles
kargo get roles --project my-project

# Create role
kargo create role developer --project my-project

# Grant OIDC claims
kargo grant --role developer \
  --claim groups=developer \
  --project my-project

# Grant resource permissions
kargo grant --role developer \
  --verb '*' --resource-type stages \
  --project my-project

# View as Kubernetes resources
kargo get role developer --as-kubernetes-resources --project my-project

# Delete role
kargo delete role developer --project my-project
```

## Credential Management

### Credential Secret Format

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: my-credentials
  namespace: my-project
  labels:
    kargo.akuity.io/cred-type: git  # git, helm, image, generic
type: Opaque
stringData:
  repoURL: https://github.com/example/repo.git
  username: my-username
  password: my-token
```

### Git Credentials

**HTTPS with Token:**

```yaml
stringData:
  repoURL: https://github.com/example/repo.git
  username: my-username
  password: my-personal-access-token
```

**SSH Key:**

```yaml
stringData:
  repoURL: git@github.com:example/repo.git
  sshPrivateKey: <base64-encoded-ssh-key>
```

**GitHub App:**

```yaml
stringData:
  repoURL: https://github.com/example/repo.git
  githubAppClientID: "1234567"
  githubAppPrivateKey: <base64-encoded-app-key>
  githubAppInstallationID: "98765432"
```

### Container Registry Credentials

**Basic Auth:**

```yaml
metadata:
  labels:
    kargo.akuity.io/cred-type: image
stringData:
  repoURL: registry.example.com
  username: my-user
  password: my-password
```

**AWS ECR (Long-lived):**

```yaml
stringData:
  repoURL: 123456789.dkr.ecr.us-west-2.amazonaws.com
  awsRegion: us-west-2
  awsAccessKeyID: AKIA...
  awsSecretAccessKey: ...
```

**AWS ECR via IRSA (Operator Setup):**

```yaml
# Helm values
controller:
  serviceAccount:
    iamRole: arn:aws:iam::ACCOUNT_ID:role/kargo-controller-role
```

Token cached for 10 hours.

**Google Artifact Registry:**

```yaml
stringData:
  repoURL: us-central1-docker.pkg.dev/my-project/my-repo
  gcpServiceAccountKey: |
    {
      "type": "service_account",
      "project_id": "my-project",
      ...
    }
```

Token cached for 40 minutes.

**Azure ACR:**

```yaml
stringData:
  repoURL: myregistry.azurecr.io
  username: <repository-scoped-token-username>
  password: <repository-scoped-token-password>
```

### Helm Repository Credentials

```yaml
metadata:
  labels:
    kargo.akuity.io/cred-type: helm
stringData:
  repoURL: https://charts.example.com
  username: my-user
  password: my-token
```

### Regex Pattern Matching

Match multiple repositories with one credential:

```yaml
stringData:
  repoURL: '^https://github\.com/myorg/.*\.git$'
  repoURLIsRegex: 'true'
  username: my-username
  password: my-pat
```

### CLI Credential Management

```bash
# Create
kargo create credentials \
  --project my-project my-creds \
  --git \
  --repo-url https://github.com/example/repo.git \
  --username my-username \
  --password my-pat

# List
kargo get credentials --project my-project

# View
kargo get credentials --project my-project my-creds

# Update
kargo update credentials \
  --project my-project my-creds \
  --password new-token

# Update with regex
kargo update credentials \
  --project my-project my-creds \
  --repo-url '^https://github.com/' \
  --regex

# Delete
kargo delete credentials --project my-project my-creds
```

### Credential Precedence

1. Exact `repoURL` matches in project namespace (lexical order)
2. Regex pattern matches in project namespace (lexical order)
3. Global credentials from operator-designated namespaces

### Global Credentials (Operator Setup)

```yaml
# Helm values
controller:
  globalCredentials:
    namespaces:
      - kargo-global-creds
```

Required RBAC:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: kargo-controller-read-secrets
  namespace: kargo-global-creds
subjects:
- kind: ServiceAccount
  name: kargo-controller
  namespace: kargo
roleRef:
  kind: ClusterRole
  name: kargo-controller-read-secrets
  apiGroup: rbac.authorization.k8s.io
```

## Secure Configuration (Production)

### Disable Admin Account

```yaml
api:
  adminAccount:
    enabled: false  # Requires SSO
```

### TLS Configuration

```yaml
# Production - use proper certificates
api:
  tls:
    selfSignedCert: false
# Create Secret: kargo-api-cert (TLS type)
```

### Secret Access Controls

```yaml
# Disable API server secret management
api:
  secretManagementEnabled: false

# Restrict controller secret reading
controller:
  serviceAccount:
    clusterWideSecretReadingEnabled: false  # Default
```

## ArgoCD Authorization

Applications must explicitly authorize Kargo:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  annotations:
    kargo.akuity.io/authorized-stage: "my-project:my-stage"
```

Multiple stages:

```yaml
annotations:
  kargo.akuity.io/authorized-stage: "my-project:test,my-project:uat,my-project:prod"
```

## Security Best Practices

1. **Use OIDC:** Always integrate with external identity providers
2. **Principle of Least Privilege:** Grant minimal required permissions
3. **Group-Based Access:** Use IDP groups for scalable access control
4. **Separate Global and Project Roles:** Use global namespaces for infrastructure ServiceAccounts
5. **Credential Rotation:** Regularly rotate repository credentials and API keys
6. **Regex Patterns:** Use patterns for broad credential coverage
7. **Ambient Credentials:** Prefer IRSA/Workload Identity over long-lived keys
8. **Monitor RBAC:** Regularly audit ServiceAccount mappings
9. **Disable Admin in Production:** Force SSO authentication
10. **Use TLS:** Never skip TLS in production environments
11. **GitOps for Credentials:** Use Sealed Secrets or External Secrets Operator
