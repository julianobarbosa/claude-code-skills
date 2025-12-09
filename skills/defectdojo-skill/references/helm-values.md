# DefectDojo Helm Chart Values Reference

## Chart Information

| Property | Value |
|----------|-------|
| Chart Repository | `https://raw.githubusercontent.com/DefectDojo/django-DefectDojo/helm-charts` |
| Chart Name | `defectdojo` |
| Current Version | `1.8.3` |
| App Version | `2.52.3` |

## Core Configuration

### Host Configuration

```yaml
# Primary hostname
host: defectdojo.dev.cafehyna.com.br

# Full site URL (used for OAuth redirect URIs)
siteUrl: https://defectdojo.dev.cafehyna.com.br

# Alternative hostnames (internal access)
alternativeHosts:
  - defectdojo.cafehyna-dev.internal
```

### Secret Configuration

```yaml
# Disable Helm-managed secrets (use CSI driver instead)
createSecret: false

# Disable hooks for ArgoCD compatibility
disableHooks: true

# PostgreSQL secret
createPostgresqlSecret: true

# Redis secret
createRedisSecret: true
```

## Django Configuration

```yaml
django:
  # Number of replicas
  replicas: 1

  # Ingress configuration
  ingress:
    enabled: true
    activateTLS: true
    className: nginx
    secretName: defectdojo-tls
    annotations:
      external-dns.alpha.kubernetes.io/hostname: defectdojo.dev.cafehyna.com.br
      cert-manager.io/cluster-issuer: letsencrypt-staging-cloudflare
      nginx.ingress.kubernetes.io/ssl-redirect: "true"
      nginx.ingress.kubernetes.io/proxy-body-size: 100m
      nginx.ingress.kubernetes.io/proxy-read-timeout: "600"

  # uWSGI configuration
  uwsgi:
    enable: true
    livenessProbe:
      initialDelaySeconds: 120
      periodSeconds: 30
      timeoutSeconds: 10
      failureThreshold: 6
    readinessProbe:
      initialDelaySeconds: 60
      periodSeconds: 15
      timeoutSeconds: 10
    resources:
      requests:
        cpu: 250m
        memory: 1Gi
      limits:
        memory: 1Gi

  # Security context
  securityContext:
    enabled: true
    runAsUser: 1001
    runAsGroup: 1001
    fsGroup: 1001
    runAsNonRoot: true
    allowPrivilegeEscalation: false

  # Autoscaling (disabled for dev)
  autoscaling:
    enabled: false
    minReplicas: 1
    maxReplicas: 3

  # Spot node tolerations
  tolerations:
    - key: kubernetes.azure.com/scalesetpriority
      operator: Equal
      value: spot
      effect: NoSchedule

  # Node affinity
  affinity:
    nodeAffinity:
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
          - matchExpressions:
              - key: agentpool
                operator: In
                values:
                  - cafedevspot
```

## Celery Configuration

**Important:** Celery Beat must remain a singleton (replicas: 1) to prevent duplicate task execution.

```yaml
celery:
  beat:
    enabled: true
    replicas: 1  # MUST be 1 - do not scale
    resources:
      requests:
        cpu: 50m
        memory: 128Mi
      limits:
        memory: 256Mi
    tolerations:
      - key: kubernetes.azure.com/scalesetpriority
        operator: Equal
        value: spot
        effect: NoSchedule

  worker:
    enabled: true
    replicas: 1
    logLevel: INFO
    concurrency: 2
    resources:
      requests:
        cpu: 250m
        memory: 256Mi
      limits:
        memory: 512Mi
    autoscaling:
      enabled: false
    tolerations:
      - key: kubernetes.azure.com/scalesetpriority
        operator: Equal
        value: spot
        effect: NoSchedule
```

## PostgreSQL Configuration

```yaml
postgresql:
  enabled: true
  auth:
    username: defectdojo
    database: defectdojo
    existingSecret: defectdojo-postgresql-secret
    secretKeys:
      adminPasswordKey: postgres-password
      userPasswordKey: password
  primary:
    persistence:
      enabled: true
      size: 10Gi
      storageClass: managed-premium-zrs
    resources:
      requests:
        cpu: 100m
        memory: 256Mi
      limits:
        memory: 512Mi
    tolerations:
      - key: kubernetes.azure.com/scalesetpriority
        operator: Equal
        value: spot
        effect: NoSchedule
  metrics:
    enabled: true
    serviceMonitor:
      enabled: true
      namespace: defectdojo
      interval: 30s
```

## Redis Configuration

```yaml
redis:
  enabled: true
  architecture: standalone
  auth:
    enabled: true
    existingSecret: defectdojo-redis-secret
    existingSecretPasswordKey: redis-password
  master:
    persistence:
      enabled: true
      size: 4Gi
      storageClass: managed-premium-zrs
    resources:
      requests:
        cpu: 50m
        memory: 128Mi
      limits:
        memory: 256Mi
    tolerations:
      - key: kubernetes.azure.com/scalesetpriority
        operator: Equal
        value: spot
        effect: NoSchedule
  metrics:
    enabled: true
    serviceMonitor:
      enabled: true
```

## Persistent Volume Configuration

```yaml
persistentVolume:
  enabled: true
  size: 20Gi
  accessMode: ReadWriteMany
  storageClass: azurefile-csi-premium-zrs
```

## Environment Variables

### Core Django Settings

```yaml
extraEnv:
  - name: DD_DEBUG
    value: "False"
  - name: DD_TIME_ZONE
    value: America/Sao_Paulo
  - name: DD_LANGUAGE_CODE
    value: pt-br
  - name: DD_ALLOWED_HOSTS
    value: defectdojo.dev.cafehyna.com.br,defectdojo.cafehyna-dev.internal,localhost
  - name: DD_CSRF_TRUSTED_ORIGINS
    value: https://defectdojo.dev.cafehyna.com.br
```

### Security Settings

```yaml
extraEnv:
  - name: DD_SESSION_COOKIE_HTTPONLY
    value: "True"
  - name: DD_CSRF_COOKIE_HTTPONLY
    value: "True"
  - name: DD_SECURE_SSL_REDIRECT
    value: "False"  # False when behind TLS-terminating proxy
  - name: DD_SECURE_PROXY_SSL_HEADER
    value: "True"
  - name: DD_SECURE_BROWSER_XSS_FILTER
    value: "True"
```

### Metrics Settings

```yaml
extraEnv:
  - name: DD_DJANGO_METRICS_ENABLED
    value: "True"
  - name: DD_CELERY_METRICS_ENABLED
    value: "True"
```

## CSI Volume Mounts

```yaml
# Mount Azure Key Vault secrets
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

## High Availability Configuration

For production deployments:

```yaml
django:
  replicas: 3
  autoscaling:
    enabled: true
    minReplicas: 2
    maxReplicas: 5

celery:
  worker:
    replicas: 3
    autoscaling:
      enabled: true

postgresql:
  replication:
    enabled: true
    slaveReplicas: 2

redis:
  architecture: replication
  replicas: 3
```

## Service Account

```yaml
serviceAccount:
  create: true
  name: defectdojo
```

## Pod Disruption Budget

```yaml
podDisruptionBudget:
  enabled: true
  minAvailable: 1
```

## Monitoring

```yaml
monitoring:
  enabled: true

createServiceMonitor: true

metrics:
  enabled: true
  serviceMonitor:
    enabled: true
    interval: 30s
    scrapeTimeout: 10s
```
