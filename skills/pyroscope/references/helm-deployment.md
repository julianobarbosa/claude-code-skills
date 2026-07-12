# Pyroscope Helm Deployment Reference

Complete reference for deploying Grafana Pyroscope on Kubernetes via Helm.

## Chart Information

| Property | Value |
|----------|-------|
| Repository | `https://grafana.github.io/helm-charts` |
| Chart Name | `pyroscope` |
| Current Version | 1.16.0 |
| Homepage | <https://grafana.com/oss/pyroscope/> |

## Installation

### Add Repository

```bash
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
```

### Single Binary Mode

```bash
kubectl create namespace pyroscope
helm install pyroscope grafana/pyroscope -n pyroscope
```

### Microservices Mode

```bash
curl -Lo values-micro-services.yaml \
  https://raw.githubusercontent.com/grafana/pyroscope/main/operations/pyroscope/helm/pyroscope/values-micro-services.yaml

helm install pyroscope grafana/pyroscope \
  -n pyroscope \
  --values values-micro-services.yaml
```

## Complete Values Reference

### Root Level Values

```yaml
# Replica count for single binary mode
replicaCount: 1

# Image configuration
image:
  repository: grafana/pyroscope
  pullPolicy: IfNotPresent
  tag: ""  # Defaults to chart.appVersion

# Image pull secrets
imagePullSecrets: []

# Pod service account
serviceAccount:
  create: true
  annotations: {}
  name: ""

# Pod annotations (profile scraping)
podAnnotations:
  profiles.grafana.com/cpu.scrape: "true"
  profiles.grafana.com/cpu.port: "4040"
  profiles.grafana.com/memory.scrape: "true"
  profiles.grafana.com/memory.port: "4040"
  profiles.grafana.com/goroutine.scrape: "true"
  profiles.grafana.com/goroutine.port: "4040"

# Pod security context
podSecurityContext:
  fsGroup: 10001
  runAsUser: 10001
  runAsNonRoot: true

# Container security context
securityContext:
  allowPrivilegeEscalation: false
  capabilities:
    drop:
      - ALL
  readOnlyRootFilesystem: true
```

### Architecture Configuration

```yaml
architecture:
  # Enable microservices mode
  microservices:
    enabled: false    # Set true for production

  # Deploy unified services (compatible endpoints)
  deployUnifiedServices: false

  # Storage architecture
  storage:
    v1: true          # Legacy storage layer
    v2: false         # Modern segment-writer storage
    migration:
      ingesterWeight: 0        # Traffic split (0-1)
      segmentWriterWeight: 0   # V2 write path
```

### Service Configuration

```yaml
service:
  type: ClusterIP
  port: 4040
  portName: http2
  annotations: {}

  # Additional ports
  grpc:
    port: 9095
  memberlist:
    port: 7946
  metastore:
    port: 9099
```

### Ingress Configuration

```yaml
ingress:
  enabled: false
  className: ""
  annotations: {}
  hosts:
    - host: pyroscope.local
      paths:
        - path: /
          pathType: Prefix
  tls: []
```

### Persistence Configuration

```yaml
pyroscope:
  persistence:
    enabled: false
    size: 10Gi
    accessModes:
      - ReadWriteOnce
    storageClassName: ""
    annotations: {}
    subPath: ""

  # Disable self-profiling
  disableSelfProfile: true

  # Cluster domain
  cluster_domain: .cluster.local

  # Custom config (merged with defaults)
  config: {}

  # Extra arguments
  extraArgs: []

  # Environment variables
  env: []

  # Volume mounts
  volumeMounts: []
```

### Resource Configuration

```yaml
resources:
  requests:
    cpu: 500m
    memory: 512Mi
  limits:
    cpu: 1
    memory: 2Gi
```

### Pod Disruption Budget

```yaml
podDisruptionBudget:
  enabled: true
  maxUnavailable: 1
```

### Autoscaling

```yaml
autoscaling:
  enabled: false
  minReplicas: 1
  maxReplicas: 10
```

### Node Scheduling

```yaml
nodeSelector: {}
affinity: {}
tolerations: []
topologySpreadConstraints: []
```

### Monitoring

```yaml
serviceMonitor:
  enabled: false
  interval: 15s
  scrapeTimeout: 10s

podMonitor:
  enabled: false
```

## Microservices Mode Values

### Querier

```yaml
querier:
  replicas: 3
  resources:
    requests:
      cpu: 100m
      memory: 256Mi
    limits:
      cpu: 1
      memory: 1Gi
```

### Query Frontend

```yaml
queryFrontend:
  replicas: 2
  resources:
    requests:
      cpu: 100m
      memory: 256Mi
    limits:
      cpu: 100m
      memory: 1Gi
```

### Query Scheduler

```yaml
queryScheduler:
  replicas: 2
  resources:
    requests:
      cpu: 100m
      memory: 256Mi
    limits:
      cpu: 100m
      memory: 1Gi
```

### Distributor

```yaml
distributor:
  replicas: 2
  resources:
    requests:
      cpu: 500m
      memory: 256Mi
    limits:
      cpu: 500m
      memory: 1Gi
```

### Ingester (StatefulSet)

```yaml
ingester:
  replicas: 3
  resources:
    requests:
      cpu: 1
      memory: 8Gi
    limits:
      cpu: 1
      memory: 16Gi
  terminationGracePeriodSeconds: 600  # 10 minutes
  persistence:
    enabled: true
    size: 50Gi
```

### Compactor (StatefulSet)

```yaml
compactor:
  replicas: 3
  resources:
    requests:
      cpu: 1
      memory: 8Gi
    limits:
      cpu: 1
      memory: 16Gi
  terminationGracePeriodSeconds: 1200  # 20 minutes
```

### Store Gateway (StatefulSet)

```yaml
storeGateway:
  replicas: 3
  shardSize: 3  # Replication factor
  resources:
    requests:
      cpu: 1
      memory: 8Gi
    limits:
      cpu: 1
      memory: 16Gi
  readinessProbe:
    initialDelaySeconds: 60
```

## Storage Backend Configuration

### AWS S3

```yaml
pyroscope:
  config:
    storage:
      backend: s3
      s3:
        bucket_name: pyroscope-data
        region: us-east-1
        endpoint: s3.us-east-1.amazonaws.com
        access_key_id: ${AWS_ACCESS_KEY_ID}
        secret_access_key: ${AWS_SECRET_ACCESS_KEY}
        # Optional
        s3ForcePathStyle: false
        insecure: false
```

### Azure Blob Storage

```yaml
pyroscope:
  config:
    storage:
      backend: azure
      azure:
        container_name: pyroscope-data
        account_name: mystorageaccount
        # Option 1: Account Key
        account_key: ${AZURE_ACCOUNT_KEY}
        # Option 2: Managed Identity
        # useManagedIdentity: true
        # userAssignedId: <client-id>
        request_timeout: 30s
```

### Google Cloud Storage

```yaml
pyroscope:
  config:
    storage:
      backend: gcs
      gcs:
        bucket_name: pyroscope-data
        # Uses GOOGLE_APPLICATION_CREDENTIALS
```

### MinIO (Development)

```yaml
minio:
  enabled: true
  rootUser: minioadmin
  rootPassword: minioadmin
  buckets:
    - name: grafana-pyroscope-data
  persistence:
    enabled: true
    size: 50Gi

pyroscope:
  config:
    storage:
      backend: s3
      s3:
        bucket_name: grafana-pyroscope-data
        endpoint: pyroscope-minio:9000
        access_key_id: minioadmin
        secret_access_key: minioadmin
        insecure: true
```

## Dependency Charts

### Grafana Alloy (Profile Collection)

```yaml
alloy:
  enabled: true
  controller:
    type: statefulset
    replicas: 1
  alloy:
    configMap:
      content: |
        pyroscope.scrape "default" {
          targets = discovery.kubernetes.pods.targets
          forward_to = [pyroscope.write.default.receiver]
        }
        pyroscope.write "default" {
          endpoint {
            url = "http://pyroscope:4040"
          }
        }
```

### Grafana Agent (Alternative)

```yaml
grafana-agent:
  enabled: false
```

## Production Values Example

```yaml
# values-production.yaml
architecture:
  microservices:
    enabled: true

# Object storage
pyroscope:
  config:
    storage:
      backend: s3
      s3:
        bucket_name: pyroscope-prod
        region: us-east-1

# High availability replicas
querier:
  replicas: 5
  resources:
    limits:
      cpu: 2
      memory: 2Gi

distributor:
  replicas: 3
  resources:
    limits:
      cpu: 1
      memory: 1Gi

ingester:
  replicas: 5
  resources:
    limits:
      cpu: 2
      memory: 16Gi
  persistence:
    enabled: true
    size: 100Gi
  terminationGracePeriodSeconds: 600

compactor:
  replicas: 3
  resources:
    limits:
      cpu: 2
      memory: 16Gi
  terminationGracePeriodSeconds: 1200

storeGateway:
  replicas: 3
  resources:
    limits:
      cpu: 2
      memory: 16Gi

queryFrontend:
  replicas: 2

queryScheduler:
  replicas: 2

# Pod disruption
podDisruptionBudget:
  enabled: true
  maxUnavailable: 1

# Topology spread
topologySpreadConstraints:
  - maxSkew: 1
    topologyKey: kubernetes.io/hostname
    whenUnsatisfiable: DoNotSchedule
    labelSelector:
      matchLabels:
        app.kubernetes.io/name: pyroscope

# Monitoring
serviceMonitor:
  enabled: true
  interval: 30s

# Alloy for collection
alloy:
  enabled: true
  controller:
    type: daemonset
```

## Development Values Example

```yaml
# values-dev.yaml
replicaCount: 1

image:
  tag: "1.16.0"

resources:
  requests:
    cpu: 500m
    memory: 512Mi
  limits:
    cpu: 1
    memory: 2Gi

pyroscope:
  persistence:
    enabled: true
    size: 5Gi

architecture:
  microservices:
    enabled: false

minio:
  enabled: true
  persistence:
    size: 10Gi

alloy:
  enabled: true
```

## Grafana Data Source Configuration

```yaml
# ConfigMap for Grafana provisioning
apiVersion: v1
kind: ConfigMap
metadata:
  name: grafana-datasources
  labels:
    grafana_datasource: "1"
data:
  pyroscope-ds.yaml: |
    apiVersion: 1
    datasources:
      - name: Pyroscope
        type: grafana-pyroscope-datasource
        access: proxy
        url: http://pyroscope-querier.pyroscope.svc.cluster.local:4040
        isDefault: false
        editable: true
```

## Upgrade Commands

```bash
# Update repository
helm repo update grafana

# Upgrade release
helm upgrade pyroscope grafana/pyroscope \
  -n pyroscope \
  --values values.yaml

# Rollback if needed
helm rollback pyroscope 1 -n pyroscope

# View release history
helm history pyroscope -n pyroscope
```

## Validation Commands

```bash
# Verify pods
kubectl get pods -n pyroscope

# Check services
kubectl get svc -n pyroscope

# View logs
kubectl logs -n pyroscope -l app.kubernetes.io/name=pyroscope --tail=100

# Test endpoint
kubectl run test-pyroscope --image=curlimages/curl:latest --rm -it -- \
  curl -v http://pyroscope.pyroscope:4040/ready
```
