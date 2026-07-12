# Tempo Storage Configuration Reference

## Storage Architecture

Tempo stores all trace data in object storage with the following structure:

```
<bucketname>/<tenantID>/<blockID>/
├── meta.json
├── index
├── data
├── bloom_0
├── bloom_1
└── bloom_n
```

## Apache Parquet Block Format

**Default format** (since Tempo 2.0): vParquet4

**Benefits:**

- 5-10x less data pulled per query
- Search speed: 300 GB/s (vs 40-50 GB/s with legacy format)
- Selective column retrieval
- Required for TraceQL

**Dedicated Columns:**

- Well-known attributes stored in dedicated columns for faster retrieval
- All other attributes stored in generic key/value maps

## Object Store Backends

### AWS S3

**Required IAM Permissions:**

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:ListBucket",
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject"
      ],
      "Resource": [
        "arn:aws:s3:::my-tempo-bucket",
        "arn:aws:s3:::my-tempo-bucket/*"
      ]
    }
  ]
}
```

**Configuration:**

```yaml
storage:
  trace:
    backend: s3
    s3:
      bucket: my-tempo-bucket
      region: us-east-1
      endpoint: s3.us-east-1.amazonaws.com
      # Option 1: IAM Role (Recommended)
      # Use service account with IAM role annotation
      # Option 2: Access Keys
      access_key: ${AWS_ACCESS_KEY_ID}
      secret_key: ${AWS_SECRET_ACCESS_KEY}
      insecure: false

# For EKS with IRSA
serviceAccount:
  annotations:
    eks.amazonaws.com/role-arn: arn:aws:iam::123456789:role/tempo-role
```

**SSE-KMS Encryption:**

```yaml
storage:
  trace:
    s3:
      sse:
        type: SSE-KMS
        kms_key_id: <kms-key-arn>
```

### Azure Blob Storage

**Authentication Methods:**

#### 1. Workload Identity Federation (Recommended)

```yaml
serviceAccount:
  annotations:
    azure.workload.identity/client-id: <identity-client-id>

podLabels:
  azure.workload.identity/use: "true"

storage:
  trace:
    backend: azure
    azure:
      container_name: tempo-traces
      storage_account_name: mystorageaccount
      use_federated_token: true
      endpoint_suffix: blob.core.windows.net
```

#### 2. User-Assigned Managed Identity

```yaml
storage:
  trace:
    backend: azure
    azure:
      container_name: tempo-traces
      storage_account_name: mystorageaccount
      use_managed_identity: true
      user_assigned_id: <identity-client-id>
```

#### 3. Account Key (Development Only)

```yaml
storage:
  trace:
    backend: azure
    azure:
      container_name: tempo-traces
      storage_account_name: mystorageaccount
      storage_account_key: ${AZURE_STORAGE_KEY}

extraArgs:
  config.expand-env: true

extraEnv:
  - name: AZURE_STORAGE_KEY
    valueFrom:
      secretKeyRef:
        name: azure-storage-secret
        key: account-key
```

#### 4. SAS Token

```yaml
storage:
  trace:
    backend: azure
    azure:
      container_name: tempo-traces
      storage_account_name: mystorageaccount
      sas_token: ${AZURE_SAS_TOKEN}
```

**Required RBAC Role:**

- `Storage Blob Data Contributor` on the storage account

**Azure Configuration Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `storage_account_name` | String | Azure storage account name |
| `container_name` | String | Container for trace data |
| `prefix` | String | Optional path prefix |
| `endpoint_suffix` | String | Default: `blob.core.windows.net` |
| `hedge_requests_at` | Duration | Threshold for hedged requests |
| `hedge_requests_up_to` | Integer | Max hedged requests |

**Azurite Emulator (Local Development):**

```yaml
storage:
  trace:
    azure:
      endpoint_suffix: azurite-host.svc.cluster.local:10000
      # Tempo auto-detects non-blob endpoints
```

### Google Cloud Storage

**Configuration:**

```yaml
storage:
  trace:
    backend: gcs
    gcs:
      bucket_name: my-tempo-bucket
      prefix: tempo-traces/  # Optional
      # Uses Workload Identity or service account JSON
      service_account: |
        ${GCS_SERVICE_ACCOUNT_JSON}
```

**For GKE with Workload Identity:**

```yaml
serviceAccount:
  annotations:
    iam.gke.io/gcp-service-account: tempo@project.iam.gserviceaccount.com
```

### MinIO (On-Premises)

```yaml
storage:
  trace:
    backend: s3
    s3:
      endpoint: minio.minio.svc:9000
      bucket: tempo-traces
      access_key: ${MINIO_ACCESS_KEY}
      secret_key: ${MINIO_SECRET_KEY}
      insecure: true  # Set false for TLS
```

### Local Filesystem (Development Only)

```yaml
storage:
  trace:
    backend: local
    local:
      path: /var/tempo/traces
    wal:
      path: /var/tempo/wal
```

**Limitations:**

- NOT production-supported
- Single-node only
- No persistence across pod restarts

## Retention Configuration

**Enable Retention:**

```yaml
compactor:
  compaction:
    block_retention: 336h  # 14 days (minimum: 1h)
```

**Compactor Configuration:**

```yaml
compactor:
  config:
    compaction:
      compaction_window: 1h
      block_retention: 336h        # 14 days
      max_block_bytes: 107374182400  # ~107GB
      compacted_block_retention: 1h
```

## Write Ahead Log (WAL)

**Purpose:** Records incoming data for crash recovery.

**Configuration:**

```yaml
ingester:
  config:
    trace_idle_period: 5s    # Flush to WAL after idle
    max_block_duration: 30m  # Max time before flush
    complete_block_timeout: 1h

storage:
  trace:
    wal:
      path: /var/tempo/wal
      encoding: snappy
```

**Requirements:**

- Use StatefulSets with persistent volumes
- Each ingester must have unique WAL directory
- Expect ~10-15GB disk usage per ingester

## Caching

### Background Cache

```yaml
storage:
  trace:
    cache: memcached
    memcached:
      host: tempo-memcached.monitoring.svc
      service: memcached-client
      timeout: 500ms
      max_idle_conns: 16
```

### Search Cache

```yaml
storage:
  trace:
    search:
      cache_control:
        footer: true
        column_index: true
        offset_index: true
```

## Bloom Filters and Indexes

**Configuration:**

```yaml
storage:
  trace:
    blocklist_poll: 5m
    blocklist_poll_fallback: true

    # Bloom filter settings
    bloom_filter_false_positive: 0.01
    bloom_filter_shard_size_bytes: 102400  # 100KiB

    # Index settings
    index_downsample_bytes: 1048576  # 1MiB
```

## Performance Optimization

### Hedging Requests

Reduce long-tail latency by sending parallel requests:

```yaml
storage:
  trace:
    azure:
      hedge_requests_at: 400ms
      hedge_requests_up_to: 2
    s3:
      hedge_requests_at: 400ms
      hedge_requests_up_to: 2
```

### Block List Polling

```yaml
storage:
  trace:
    blocklist_poll: 5m
    blocklist_poll_jitter_ms: 500
    blocklist_poll_tenant_index_builders: 1
```

## Azure Lifecycle Management

Automatically delete old data:

```json
{
  "rules": [
    {
      "enabled": true,
      "name": "tempo-cleanup",
      "type": "Lifecycle",
      "definition": {
        "actions": {
          "baseBlob": {
            "delete": {
              "daysAfterModificationGreaterThan": 60
            }
          }
        },
        "filters": {
          "blobTypes": ["blockBlob"],
          "prefixMatch": ["tempo-traces/"]
        }
      }
    }
  ]
}
```

## Deployment Mode Considerations

### Monolithic Mode

- Apply storage config under `tempo.storage.trace`

### Distributed Mode

- Apply at root `storage.trace` level
- Propagate `extraArgs` and `extraEnv` to all services:
  - distributor
  - ingester
  - querier
  - queryFrontend
  - compactor

```yaml
# Distributed mode - propagate env vars
distributor:
  extraArgs:
    config.expand-env: true
  extraEnv:
    - name: AZURE_STORAGE_KEY
      valueFrom:
        secretKeyRef:
          name: azure-secret
          key: key

ingester:
  extraArgs:
    config.expand-env: true
  extraEnv:
    - name: AZURE_STORAGE_KEY
      valueFrom:
        secretKeyRef:
          name: azure-secret
          key: key

# Repeat for querier, queryFrontend, compactor
```

## Storage Troubleshooting

### Azure Container Not Found

```bash
az storage container create --name tempo-traces --account-name <storage>
```

### Azure Authorization Failure

```bash
# Check role assignments
az role assignment list --scope <storage-scope> --query "[?principalId=='<principal-id>']"

# Assign role if missing
az role assignment create \
  --role "Storage Blob Data Contributor" \
  --assignee-object-id <principal-id> \
  --scope <storage-scope>

# Restart pod to refresh token
kubectl delete pod -n monitoring <tempo-pod>
```

### S3 Access Denied

```bash
# Verify IAM policy
aws iam get-policy --policy-arn <policy-arn>

# Test bucket access
aws s3 ls s3://my-tempo-bucket/
```

### Compactor Issues

```bash
# Check compactor logs
kubectl logs -n monitoring -l app.kubernetes.io/component=compactor --tail=200

# Verify compactor is running
kubectl get pods -n monitoring -l app.kubernetes.io/component=compactor
```
