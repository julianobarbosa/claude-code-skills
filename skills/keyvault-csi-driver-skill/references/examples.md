# Real-World Examples

## Example 1: External-DNS Cloudflare API Token

**Location:** `argo-cd-helm-values/kube-addons/external-dns/cafehyna-dev/secretproviderclass.yaml`

**Key Vault Secret:** `cloudflare-api-token`

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
    userAssignedIdentityID: "f1a14a8f-6d38-40a0-a935-3cdd91a25f47"
    keyvaultName: "kv-cafehyna-dev-hlg"
    objects: |
      array:
        - |
          objectName: cloudflare-api-token
          objectType: secret
    tenantId: "3f7a3df4-f85b-4ca8-98d0-08b1034e6567"
```

**Helm Values Usage:**

```yaml
# values.yaml
env:
  - name: CF_API_TOKEN
    valueFrom:
      secretKeyRef:
        name: cloudflare-api-token
        key: cloudflare_api_token

extraVolumes:
  - name: secrets-store
    csi:
      driver: secrets-store.csi.k8s.io
      readOnly: true
      volumeAttributes:
        secretProviderClass: cloudflare-api-token-kv

extraVolumeMounts:
  - name: secrets-store
    mountPath: /mnt/secrets-store
    readOnly: true
```

---

## Example 2: DefectDojo Multi-Secret Configuration

**Location:** `argo-cd-helm-values/kube-addons/defectdojo/cafehyna-dev/secretproviderclass.yaml`

**Key Vault Secrets:**

- `defectdojo-admin-password`
- `defectdojo-secret-key`
- `defectdojo-credential-aes-key`
- `defectdojo-metrics-password`
- `defectdojo-postgresql-password`
- `defectdojo-postgresql-postgres-password`
- `defectdojo-redis-password`
- `defectdojo-azuread-client-secret`

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
          objectName: "defectdojo-metrics-password"
          objectType: "secret"
          objectAlias: "METRICS_HTTP_AUTH_PASSWORD"
        - |
          objectName: "defectdojo-postgresql-password"
          objectType: "secret"
          objectAlias: "postgresql-password"
        - |
          objectName: "defectdojo-postgresql-postgres-password"
          objectType: "secret"
          objectAlias: "postgresql-postgres-password"
        - |
          objectName: "defectdojo-redis-password"
          objectType: "secret"
          objectAlias: "redis-password"
        - |
          objectName: "defectdojo-azuread-client-secret"
          objectType: "secret"
          objectAlias: "DD_SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_SECRET"
  secretObjects:
    # DefectDojo application secrets
    - secretName: defectdojo
      type: Opaque
      data:
        - objectName: "DD_ADMIN_PASSWORD"
          key: "DD_ADMIN_PASSWORD"
        - objectName: "DD_SECRET_KEY"
          key: "DD_SECRET_KEY"
        - objectName: "DD_CREDENTIAL_AES_256_KEY"
          key: "DD_CREDENTIAL_AES_256_KEY"
        - objectName: "METRICS_HTTP_AUTH_PASSWORD"
          key: "METRICS_HTTP_AUTH_PASSWORD"
        - objectName: "DD_SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_SECRET"
          key: "DD_SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_SECRET"
    # PostgreSQL secrets
    - secretName: defectdojo-postgresql-specific
      type: Opaque
      data:
        - objectName: "postgresql-password"
          key: "postgresql-password"
        - objectName: "postgresql-postgres-password"
          key: "postgresql-postgres-password"
    # Redis secrets
    - secretName: defectdojo-redis-specific
      type: Opaque
      data:
        - objectName: "redis-password"
          key: "redis-password"
```

**Key Points:**

- Uses `objectAlias` to provide clear names
- Creates 3 separate K8s secrets for different purposes
- Helm chart expects specific secret names (`defectdojo`, `defectdojo-postgresql-specific`, `defectdojo-redis-specific`)

---

## Example 3: Cert-Manager Cloudflare DNS01 Challenge

**Location:** `argo-cd-helm-values/kube-addons/cert-manager/loyalty-dev/csi-cloudflare-api-key.yaml`

```yaml
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: cloudflare-api-key-csi
  namespace: cert-manager
spec:
  provider: azure
  secretObjects:
    - secretName: cloudflare-api-key
      type: Opaque
      data:
        - objectName: api-token
          key: api-token
  parameters:
    usePodIdentity: "false"
    useVMManagedIdentity: "true"
    userAssignedIdentityID: "<cluster-managed-identity>"
    keyvaultName: "kv-loyalty-qas"
    tenantId: "3f7a3df4-f85b-4ca8-98d0-08b1034e6567"
    objects: |
      array:
        - |
          objectName: cloudflare-api-token
          objectType: secret
          objectAlias: api-token
```

**ClusterIssuer Reference:**

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-staging-cloudflare
spec:
  acme:
    solvers:
      - dns01:
          cloudflare:
            apiTokenSecretRef:
              name: cloudflare-api-key
              key: api-token
```

---

## Example 4: RabbitMQ Cluster Secrets

**Location:** `infra-team/argocd/addons/rabbitmq-cluster-operator/overlays/painelclientes-prd/secretproviderclass-rabbitmq.yaml`

```yaml
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: rabbitmq-secrets
  namespace: painelclientes-prd
spec:
  provider: azure
  secretObjects:
    - secretName: rabbitmq-default-user
      type: Opaque
      data:
        - objectName: username
          key: username
        - objectName: password
          key: password
  parameters:
    usePodIdentity: "false"
    useVMManagedIdentity: "true"
    userAssignedIdentityID: "<cluster-identity>"
    keyvaultName: "painel-clientes-prd"
    tenantId: "3f7a3df4-f85b-4ca8-98d0-08b1034e6567"
    objects: |
      array:
        - |
          objectName: rabbitmq-username
          objectType: secret
          objectAlias: username
        - |
          objectName: rabbitmq-password
          objectType: secret
          objectAlias: password
```

---

## Example 5: Robusta Monitoring Secrets

**Location:** `infra-team/argocd/addons/robusta/base/secret-provider-class.yaml`

```yaml
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: robusta-secrets
  namespace: robusta
spec:
  provider: azure
  secretObjects:
    - secretName: robusta-credentials
      type: Opaque
      data:
        - objectName: signing-key
          key: ROBUSTA_SIGNING_KEY
        - objectName: account-id
          key: ROBUSTA_ACCOUNT_ID
        - objectName: sink-token
          key: ROBUSTA_SINK_TOKEN
  parameters:
    usePodIdentity: "false"
    useVMManagedIdentity: "true"
    userAssignedIdentityID: "$(MANAGED_IDENTITY_CLIENT_ID)"
    keyvaultName: "$(KEY_VAULT_NAME)"
    tenantId: "$(TENANT_ID)"
    objects: |
      array:
        - |
          objectName: robusta-signing-key
          objectType: secret
          objectAlias: signing-key
        - |
          objectName: robusta-account-id
          objectType: secret
          objectAlias: account-id
        - |
          objectName: robusta-sink-token
          objectType: secret
          objectAlias: sink-token
```

**Kustomize Overlay (dev):**

```yaml
# overlays/dev/secret-provider-patch.yaml
apiVersion: secrets-store.csi.x-k8s.io/v1
kind: SecretProviderClass
metadata:
  name: robusta-secrets
spec:
  parameters:
    userAssignedIdentityID: "f1a14a8f-6d38-40a0-a935-3cdd91a25f47"
    keyvaultName: "kv-cafehyna-dev-hlg"
    tenantId: "3f7a3df4-f85b-4ca8-98d0-08b1034e6567"
```

---

## Common Patterns Summary

### Pattern: Helm Chart Without extraObjects Support

When a Helm chart doesn't support `extraObjects`, deploy SecretProviderClass as a separate manifest in the same directory:

```
argo-cd-helm-values/kube-addons/<app>/<cluster>/
├── values.yaml                 # Helm values
└── secretproviderclass.yaml    # CSI configuration
```

Configure ApplicationSet to include both:

```yaml
sources:
  - chart: <chart-name>
    helm:
      valueFiles:
        - $values/kube-addons/<app>/{{cluster}}/values.yaml
  - repoURL: <values-repo>
    path: kube-addons/<app>/{{cluster}}
    directory:
      include: "secretproviderclass.yaml"
```

### Pattern: Base + Overlay with Kustomize

For applications using Kustomize:

```
infra-team/argocd/addons/<app>/
├── base/
│   ├── kustomization.yaml
│   └── secret-provider-class.yaml
└── overlays/
    ├── dev/
    │   ├── kustomization.yaml
    │   └── secret-provider-patch.yaml
    └── prd/
        ├── kustomization.yaml
        └── secret-provider-patch.yaml
```

### Pattern: Secret Sync Pod

When secrets need to be created before the main application starts:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: secret-sync
  annotations:
    argocd.argoproj.io/hook: PreSync
spec:
  containers:
    - name: sync
      image: busybox
      command: ["sleep", "5"]
      volumeMounts:
        - name: secrets-store
          mountPath: /mnt/secrets-store
  volumes:
    - name: secrets-store
      csi:
        driver: secrets-store.csi.k8s.io
        volumeAttributes:
          secretProviderClass: <name>
  restartPolicy: Never
```
