# DevOps Secret Manager (DSM)

DSM is senhasegura's secret store for DevOps workflows. Two main consumers: the `dsm` CLI (for CI/CD pipelines) and the External Secrets Operator (for Kubernetes).

## DSM CLI

### Install

```bash
curl -LO https://github.com/senhasegura/dsmcli/releases/latest/download/dsm-linux-amd64
chmod +x dsm-linux-amd64
sudo mv dsm-linux-amd64 /usr/local/bin/dsm
dsm --version
```

### Configuration

Create `~/.senhasegura/config.yaml` (chmod 600):

```yaml
SENHASEGURA_URL: "https://senhasegura.example.com"
SENHASEGURA_CLIENT_ID: "your-client-id"
SENHASEGURA_CLIENT_SECRET: "your-client-secret"

# Optional
SENHASEGURA_MAPPING_FILE: "/path/to/mapping.json"
SENHASEGURA_SECRETS_FILE: "/tmp/runb.$$.vars"
SENHASEGURA_DISABLE_RUNB: 0
```

A full template is at `References/DsmConfigExample.yaml`.

Or use environment variables (preferred for CI):

```bash
export SENHASEGURA_URL="https://senhasegura.example.com"
export SENHASEGURA_CLIENT_ID="your-client-id"
export SENHASEGURA_CLIENT_SECRET="your-client-secret"
export SENHASEGURA_CONFIG_FILE="/path/to/config.yaml"   # optional
```

### `dsm runb` — fetch secrets at runtime

```bash
dsm runb \
  --tool-name github \
  --application my-app \
  --system production \
  --environment prod
source .runb.vars
# ... use secrets ...
rm -f .runb.vars   # always, even on failure
```

`--tool-name` controls log masking and must match the actual runner: `github`, `azure-devops`, `gitlab`, `linux`. See SKILL.md Gotcha #7.

Run from a tmpdir, not the repo root, so `.runb.vars` cannot be committed (Gotcha #5).

### Mapping file (write-back)

For pipelines that *register* or *update* secrets, configure a mapping file:

```json
{
  "access_keys": [
    {
      "name": "AWS_PROD_KEYS",
      "type": "aws",
      "fields": {
        "access_key_id": "AWS_ACCESS_KEY_ID",
        "secret_access_key": "AWS_SECRET_ACCESS_KEY"
      }
    }
  ],
  "credentials": [
    {
      "name": "DATABASE_CREDS",
      "fields": {
        "user": "DB_USER",
        "password": "DB_PASSWORD",
        "host": "DB_HOST"
      }
    }
  ],
  "key_value": [
    {
      "name": "API_TOKENS",
      "fields": ["API_KEY", "API_SECRET", "WEBHOOK_SECRET"]
    }
  ]
}
```

Set `SENHASEGURA_MAPPING_FILE=/path/to/mapping.json`. Full template: `References/MappingExample.json`.

## DSM API

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/api/dsm/secret` | List secrets |
| `GET` | `/api/dsm/secret/{identifier}` | Get a secret by identifier |
| `POST` | `/api/dsm/secret` | Create a secret |
| `PUT` | `/api/dsm/secret/{identifier}` | Update a secret |
| `DELETE` | `/api/dsm/secret/{identifier}` | Delete a secret |

The Python `DSMClient` and TypeScript clients in `References/` wrap these.

## Kubernetes — External Secrets Operator

ESO is the recommended way to project DSM secrets into Kubernetes `Secret` objects. Full step-by-step: `Workflows/SyncKubernetesSecrets.md`.

### Provider casing — critical

`senhasegura` (lowercase) and `DSM` (uppercase). Mixed case = silent provider-not-found (SKILL.md Gotcha #6).

### `SecretStore` (single namespace)

```yaml
apiVersion: external-secrets.io/v1beta1
kind: SecretStore
metadata:
  name: senhasegura-dsm
  namespace: default
spec:
  provider:
    senhasegura:
      url: "https://senhasegura.example.com"
      module: DSM
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
```

Full template: `References/SecretStoreExample.yaml`.

### `ClusterSecretStore` (multi-namespace)

Identical spec, `kind: ClusterSecretStore`, no `metadata.namespace`. Bind RBAC tightly — anything in the cluster can create an `ExternalSecret` against it.

### `ExternalSecret` patterns

**Explicit keys:**

```yaml
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: senhasegura-dsm
    kind: SecretStore
  target:
    name: db-secret
    creationPolicy: Owner
  data:
    - secretKey: username
      remoteRef:
        key: database-prod
        property: username
    - secretKey: password
      remoteRef:
        key: database-prod
        property: password
```

**Extract all fields:**

```yaml
spec:
  refreshInterval: 30m
  secretStoreRef:
    name: senhasegura-dsm
    kind: SecretStore
  target:
    name: api-config
    creationPolicy: Owner
  dataFrom:
    - extract:
        key: api-settings-prod
```

Full template: `References/ExternalSecretExample.yaml`.

### TLS

If your senhasegura uses an internal CA, mount the CA bundle into the ESO pod and reference it via the `ca` field. **Don't** use `ignoreSslCertificate: true` outside local debugging (SKILL.md Gotcha #10).

### RBAC for consuming pods

Restrict consumers to specific secret names:

```yaml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: secret-reader
  namespace: my-app
rules:
  - apiGroups: [""]
    resources: ["secrets"]
    resourceNames: ["db-secret", "api-secret"]
    verbs: ["get"]
```
