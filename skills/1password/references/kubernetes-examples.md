# 1Password Kubernetes Integration Examples

Complete Kubernetes manifest examples for integrating 1Password with Kubernetes using either External Secrets Operator or the native 1Password Kubernetes Operator.

## External Secrets Operator Integration

### Connect Server Deployment

Deploy the 1Password Connect Server that ESO will communicate with.

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: onepassword-system
---
apiVersion: v1
kind: Secret
metadata:
  name: onepassword-credentials
  namespace: onepassword-system
type: Opaque
data:
  # Base64 encoded 1password-credentials.json
  1password-credentials.json: <base64-encoded-credentials>
---
apiVersion: v1
kind: Secret
metadata:
  name: onepassword-token
  namespace: onepassword-system
type: Opaque
stringData:
  token: <your-connect-access-token>
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: onepassword-connect
  namespace: onepassword-system
spec:
  replicas: 1
  selector:
    matchLabels:
      app: onepassword-connect
  template:
    metadata:
      labels:
        app: onepassword-connect
    spec:
      containers:
        - name: connect-api
          image: 1password/connect-api:1.7.2
          ports:
            - containerPort: 8080
              name: http
          env:
            - name: OP_SESSION
              valueFrom:
                secretKeyRef:
                  name: onepassword-credentials
                  key: 1password-credentials.json
          resources:
            requests:
              memory: "64Mi"
              cpu: "100m"
            limits:
              memory: "256Mi"
              cpu: "500m"
          livenessProbe:
            httpGet:
              path: /heartbeat
              port: http
            initialDelaySeconds: 15
            periodSeconds: 30
          readinessProbe:
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 15
        - name: connect-sync
          image: 1password/connect-sync:1.7.2
          env:
            - name: OP_SESSION
              valueFrom:
                secretKeyRef:
                  name: onepassword-credentials
                  key: 1password-credentials.json
          resources:
            requests:
              memory: "64Mi"
              cpu: "100m"
            limits:
              memory: "256Mi"
              cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: onepassword-connect
  namespace: onepassword-system
spec:
  selector:
    app: onepassword-connect
  ports:
    - port: 8080
      targetPort: 8080
      name: http
```

### ClusterSecretStore Configuration

Define cluster-wide access to 1Password vaults.

```yaml
apiVersion: external-secrets.io/v1
kind: ClusterSecretStore
metadata:
  name: onepassword
spec:
  provider:
    onepassword:
      connectHost: http://onepassword-connect.onepassword-system:8080
      vaults:
        production: 1    # Priority ordering
        staging: 2
        development: 3
      auth:
        secretRef:
          connectTokenSecretRef:
            name: onepassword-token
            namespace: onepassword-system
            key: token
```

### Namespace-Scoped SecretStore

For namespace-specific vault access.

```yaml
apiVersion: external-secrets.io/v1
kind: SecretStore
metadata:
  name: onepassword-staging
  namespace: staging
spec:
  provider:
    onepassword:
      connectHost: http://onepassword-connect.onepassword-system:8080
      vaults:
        staging: 1
      auth:
        secretRef:
          connectTokenSecretRef:
            name: onepassword-token
            key: token
```

### ExternalSecret Examples

#### Basic Secret Retrieval

```yaml
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata:
  name: database-credentials
  namespace: production
spec:
  refreshInterval: 1h
  secretStoreRef:
    kind: ClusterSecretStore
    name: onepassword
  target:
    name: database-credentials
    creationPolicy: Owner
    deletionPolicy: Retain
  data:
    - secretKey: DB_HOST
      remoteRef:
        key: production-database    # Item title in 1Password
        property: host              # Field label
    - secretKey: DB_PORT
      remoteRef:
        key: production-database
        property: port
    - secretKey: DB_USERNAME
      remoteRef:
        key: production-database
        property: username
    - secretKey: DB_PASSWORD
      remoteRef:
        key: production-database
        property: password
```

#### TLS Certificate Secret

```yaml
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata:
  name: tls-certificate
  namespace: production
spec:
  refreshInterval: 24h
  secretStoreRef:
    kind: ClusterSecretStore
    name: onepassword
  target:
    name: app-tls
    creationPolicy: Owner
    template:
      type: kubernetes.io/tls
  data:
    - secretKey: tls.crt
      remoteRef:
        key: wildcard-certificate
        property: certificate
    - secretKey: tls.key
      remoteRef:
        key: wildcard-certificate
        property: private-key
```

#### Docker Registry Secret

```yaml
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata:
  name: registry-credentials
  namespace: production
spec:
  refreshInterval: 1h
  secretStoreRef:
    kind: ClusterSecretStore
    name: onepassword
  target:
    name: registry-secret
    creationPolicy: Owner
    template:
      type: kubernetes.io/dockerconfigjson
      data:
        .dockerconfigjson: |
          {
            "auths": {
              "{{ .registry }}": {
                "username": "{{ .username }}",
                "password": "{{ .password }}",
                "auth": "{{ printf "%s:%s" .username .password | b64enc }}"
              }
            }
          }
  data:
    - secretKey: registry
      remoteRef:
        key: docker-registry
        property: registry
    - secretKey: username
      remoteRef:
        key: docker-registry
        property: username
    - secretKey: password
      remoteRef:
        key: docker-registry
        property: password
```

#### SSH Key Secret

```yaml
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata:
  name: git-ssh-key
  namespace: argocd
spec:
  refreshInterval: 24h
  secretStoreRef:
    kind: ClusterSecretStore
    name: onepassword
  target:
    name: repo-ssh-key
    creationPolicy: Owner
    template:
      type: kubernetes.io/ssh-auth
  data:
    - secretKey: ssh-privatekey
      remoteRef:
        key: git-deploy-key
        property: private-key
```

#### Bulk Environment Variables with dataFrom

```yaml
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata:
  name: app-environment
  namespace: production
spec:
  refreshInterval: 30m
  secretStoreRef:
    kind: ClusterSecretStore
    name: onepassword
  target:
    name: app-env
    creationPolicy: Owner
  dataFrom:
    - find:
        path: app-config              # Item title
        name:
          regexp: "^[A-Z][A-Z0-9_]*$" # Match uppercase env vars
```

#### Multiple Items with dataFrom

```yaml
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata:
  name: combined-secrets
  namespace: production
spec:
  refreshInterval: 1h
  secretStoreRef:
    kind: ClusterSecretStore
    name: onepassword
  target:
    name: combined-secrets
  dataFrom:
    - extract:
        key: database-credentials
    - extract:
        key: cache-credentials
    - extract:
        key: api-keys
```

### PushSecret Examples

Push Kubernetes secrets to 1Password.

#### Basic PushSecret

```yaml
apiVersion: external-secrets.io/v1alpha1
kind: PushSecret
metadata:
  name: push-cert-manager-certs
  namespace: cert-manager
spec:
  refreshInterval: 1h
  secretStoreRefs:
    - name: onepassword
      kind: ClusterSecretStore
  selector:
    secret:
      name: letsencrypt-certificate
  data:
    - match:
        secretKey: tls.crt
        remoteRef:
          remoteKey: kubernetes-certificates
          property: certificate
      metadata:
        apiVersion: kubernetes.external-secrets.io/v1alpha1
        kind: PushSecretMetadata
        spec:
          vault: production
          tags:
            - kubernetes
            - certificate
    - match:
        secretKey: tls.key
        remoteRef:
          remoteKey: kubernetes-certificates
          property: private-key
      metadata:
        apiVersion: kubernetes.external-secrets.io/v1alpha1
        kind: PushSecretMetadata
        spec:
          vault: production
          tags:
            - kubernetes
            - certificate
```

#### PushSecret with Delete Policy

```yaml
apiVersion: external-secrets.io/v1alpha1
kind: PushSecret
metadata:
  name: push-dynamic-secret
spec:
  deletionPolicy: Delete    # Delete from 1Password when PushSecret is deleted
  refreshInterval: 30m
  secretStoreRefs:
    - name: onepassword
      kind: ClusterSecretStore
  selector:
    secret:
      name: generated-api-key
  data:
    - match:
        secretKey: api-key
        remoteRef:
          remoteKey: k8s-generated-api-key
          property: password
      metadata:
        apiVersion: kubernetes.external-secrets.io/v1alpha1
        kind: PushSecretMetadata
        spec:
          vault: staging
```

## Native 1Password Kubernetes Operator

### Helm Installation Values

```yaml
# values.yaml for 1password/connect chart
connect:
  create: true
  credentials: ""  # Set via --set-file

operator:
  create: true
  watchNamespace: []  # Empty = all namespaces
  autoRestart: true
  pollingInterval: 600

# Resource limits
resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 500m
    memory: 512Mi
```

Install command:

```bash
helm install connect 1password/connect \
  --namespace onepassword-system \
  --create-namespace \
  --set-file connect.credentials=1password-credentials.json \
  --set operator.token.value=<access-token> \
  -f values.yaml
```

### OnePasswordItem Examples

#### Basic Item

```yaml
apiVersion: onepassword.com/v1
kind: OnePasswordItem
metadata:
  name: database-secret
  namespace: production
spec:
  itemPath: "vaults/Production/items/Database Credentials"
```

Creates a Kubernetes Secret with all fields from the 1Password item.

#### Item with Specific Vault ID

```yaml
apiVersion: onepassword.com/v1
kind: OnePasswordItem
metadata:
  name: api-keys
  namespace: production
spec:
  itemPath: "vaults/abcd1234efgh5678/items/API Keys"
```

### Auto-Restart Configuration

#### Namespace-Level Auto-Restart

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: production
  annotations:
    operator.1password.io/auto-restart: "true"
```

#### Deployment with Auto-Restart

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
  namespace: production
  annotations:
    operator.1password.io/auto-restart: "true"
spec:
  replicas: 3
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
        - name: app
          image: my-app:latest
          envFrom:
            - secretRef:
                name: database-secret  # OnePasswordItem-created secret
```

#### Disable Auto-Restart for Specific Item

```yaml
apiVersion: onepassword.com/v1
kind: OnePasswordItem
metadata:
  name: static-config
  namespace: production
  annotations:
    operator.1password.io/auto-restart: "false"
spec:
  itemPath: "vaults/Production/items/Static Config"
```

### Operator Environment Configuration

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: onepassword-operator
spec:
  template:
    spec:
      containers:
        - name: operator
          env:
            - name: POLLING_INTERVAL
              value: "300"  # 5 minutes
            - name: AUTO_RESTART
              value: "true"
            - name: WATCH_NAMESPACE
              value: "production,staging"  # Specific namespaces
            - name: OP_CONNECT_HOST
              value: "http://onepassword-connect:8080"
```

## Kubernetes Secrets Injector

Alternative approach using init containers.

### Injector Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  template:
    spec:
      serviceAccountName: my-app
      initContainers:
        - name: secrets-injector
          image: 1password/kubernetes-secrets-injector:latest
          env:
            - name: OP_SERVICE_ACCOUNT_TOKEN
              valueFrom:
                secretKeyRef:
                  name: op-service-account
                  key: token
          volumeMounts:
            - name: secrets
              mountPath: /secrets
      containers:
        - name: app
          image: my-app:latest
          envFrom:
            - secretRef:
                name: injected-secrets
          volumeMounts:
            - name: secrets
              mountPath: /secrets
              readOnly: true
      volumes:
        - name: secrets
          emptyDir:
            medium: Memory
```

## Common Patterns

### Multi-Environment Setup

```yaml
# Development ClusterSecretStore
apiVersion: external-secrets.io/v1
kind: ClusterSecretStore
metadata:
  name: onepassword-dev
spec:
  provider:
    onepassword:
      connectHost: http://onepassword-connect.onepassword-system:8080
      vaults:
        development: 1
        shared: 2
      auth:
        secretRef:
          connectTokenSecretRef:
            name: onepassword-token-dev
            namespace: onepassword-system
            key: token
---
# Production ClusterSecretStore
apiVersion: external-secrets.io/v1
kind: ClusterSecretStore
metadata:
  name: onepassword-prod
spec:
  provider:
    onepassword:
      connectHost: http://onepassword-connect.onepassword-system:8080
      vaults:
        production: 1
      auth:
        secretRef:
          connectTokenSecretRef:
            name: onepassword-token-prod
            namespace: onepassword-system
            key: token
```

### Kustomize Integration

```yaml
# kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - external-secrets.yaml

patches:
  - target:
      kind: ExternalSecret
    patch: |
      - op: replace
        path: /spec/secretStoreRef/name
        value: onepassword-prod
```

### ArgoCD Application

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: app-secrets
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/org/secrets-repo
    targetRevision: HEAD
    path: external-secrets/production
  destination:
    server: https://kubernetes.default.svc
    namespace: production
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

## Troubleshooting Manifests

### Debug ExternalSecret

```yaml
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata:
  name: debug-secret
  annotations:
    external-secrets.io/debug: "true"
spec:
  refreshInterval: 1m  # Fast refresh for debugging
  secretStoreRef:
    kind: ClusterSecretStore
    name: onepassword
  target:
    name: debug-secret
    creationPolicy: Owner
  data:
    - secretKey: test
      remoteRef:
        key: test-item
        property: password
```

Check status:

```bash
kubectl describe externalsecret debug-secret
kubectl get externalsecret debug-secret -o yaml
kubectl logs -n onepassword-system -l app=onepassword-connect
```

### Verify SecretStore Connection

```bash
# Check SecretStore status
kubectl get secretstore,clustersecretstore -A

# Describe for detailed status
kubectl describe clustersecretstore onepassword

# Check for sync errors
kubectl get externalsecret -A -o wide
```
