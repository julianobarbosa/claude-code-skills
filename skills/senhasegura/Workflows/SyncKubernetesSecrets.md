# Workflow: Sync Senhasegura DSM Secrets to Kubernetes

Pull secrets from senhasegura DSM into Kubernetes `Secret` objects via External Secrets Operator (ESO).

## Prerequisites
- Kubernetes cluster access with permissions to install controllers
- Helm 3.x
- A2A OAuth 2.0 credentials (`Workflows/SetupA2A.md`)
- Cluster egress IP whitelisted in the A2A authorization (SKILL.md Gotcha #4)

## Steps

### 1. Install External Secrets Operator

```bash
helm repo add external-secrets https://charts.external-secrets.io
helm install external-secrets external-secrets/external-secrets \
  -n external-secrets --create-namespace --wait

# Verify
kubectl get pods -n external-secrets
```

### 2. Create the auth Secret

```bash
kubectl create secret generic senhasegura-auth \
  -n external-secrets \
  --from-literal=clientId="$SENHASEGURA_CLIENT_ID" \
  --from-literal=clientSecret="$SENHASEGURA_CLIENT_SECRET"
```

### 3. Create a `SecretStore`

Apply `References/SecretStoreExample.yaml` (edit `url` and namespaces as needed):

```bash
kubectl apply -f References/SecretStoreExample.yaml
```

The minimum shape:

```yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: senhasegura-dsm
  namespace: default
spec:
  provider:
    senhasegura:           # lowercase — Gotcha #6
      url: "https://senhasegura.example.com"
      module: DSM          # uppercase — Gotcha #6
      auth:
        clientId:
          secretRef:
            name: senhasegura-auth
            key: clientId
            namespace: external-secrets
        clientSecretSecretRef:
          name: senhasegura-auth
          key: clientSecret
          namespace: external-secrets
      # In production, mount the CA bundle. Don't ignoreSslCertificate. (Gotcha #10)
```

For multi-namespace use a `ClusterSecretStore` instead — see `Dsm.md`.

### 4. Create an `ExternalSecret`

Apply `References/ExternalSecretExample.yaml`. Two patterns:

**Explicit keys:**

```yaml
apiVersion: external-secrets.io/v1beta1
kind: ExternalSecret
metadata:
  name: database-credentials
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: senhasegura-dsm
    kind: SecretStore
  target:
    name: db-secret
  data:
    - secretKey: password
      remoteRef:
        key: database-prod
        property: password
```

**Extract all fields:**

```yaml
spec:
  dataFrom:
    - extract:
        key: api-settings-prod
```

### 5. Verify synchronization

```bash
kubectl get externalsecret database-credentials
# Expected STATUS: SecretSynced

kubectl get secret db-secret -o yaml
# Expected: data.password is base64-encoded value from senhasegura

# If it's not syncing:
kubectl describe externalsecret database-credentials
kubectl logs -n external-secrets -l app.kubernetes.io/name=external-secrets
```

## Common failures

| Symptom | Likely cause |
|---------|--------------|
| `could not get provider client` | Auth secret wrong, OR cluster egress IP not whitelisted (Gotcha #4) |
| `provider not found` | Casing wrong — `senhasegura` lowercase, `DSM` uppercase (Gotcha #6) |
| `could not find secret` | Identifier in `remoteRef.key` doesn't match a DSM secret |
| TLS errors | Internal CA — mount the CA bundle into ESO pod via `ca` field, don't use `ignoreSslCertificate` (Gotcha #10) |

## Next workflows

- Set up automated rotation of source credentials → `Workflows/RotatePasswords.md`
- Wire pipelines that consume these secrets directly → `Workflows/InjectCiCdSecrets.md`
