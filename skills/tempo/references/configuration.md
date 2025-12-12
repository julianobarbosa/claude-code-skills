# Tempo Configuration Reference

Complete configuration reference for Grafana Tempo. Most installations only require 10-20 of these options.

## Server Configuration

```yaml
server:
  http_listen_port: 3200          # Default HTTP port
  grpc_listen_port: 9095          # Default gRPC port
  graceful_shutdown_timeout: 30s
  http_server_read_timeout: 30s
  http_server_write_timeout: 30s
```

## Distributor Configuration

```yaml
distributor:
  ring:
    kvstore:
      store: memberlist           # memberlist, consul, etcd
    heartbeat_period: 5s
    heartbeat_timeout: 1m

  receivers:
    jaeger:
      protocols:
        grpc:
          endpoint: 0.0.0.0:14250
        thrift_http:
          endpoint: 0.0.0.0:14268
        thrift_compact:
          endpoint: 0.0.0.0:6831
        thrift_binary:
          endpoint: 0.0.0.0:6832

    otlp:
      protocols:
        grpc:
          endpoint: 0.0.0.0:4317
        http:
          endpoint: 0.0.0.0:4318

    opencensus:
      endpoint: 0.0.0.0:55678

    zipkin:
      endpoint: 0.0.0.0:9411

  # Forwarding to other services
  forwarders:
    - name: otlp
      queue:
        size: 1000
      backend: otlp
      otlp:
        endpoints:
          - http://other-service:4317
```

## Ingester Configuration

```yaml
ingester:
  lifecycler:
    ring:
      kvstore:
        store: memberlist
      replication_factor: 3       # Number of replicas
    heartbeat_period: 5s
    join_after: 10s
    min_ready_duration: 10s
    final_sleep: 30s

  # Trace processing
  trace_idle_period: 5s           # Flush to WAL after idle
  max_block_duration: 30m         # Max time before flush
  max_block_bytes: 524288000      # ~500MB default
  complete_block_timeout: 1h
  flush_check_period: 30s
  concurrent_flushes: 4           # Parallel flush operations

  # WAL configuration
  wal:
    path: /var/tempo/wal
    encoding: snappy              # snappy, lz4, gzip, none
    checkpoint_duration: 5m
    replay_memory_ceiling: 4GB    # ~75% of available memory
```

## Querier Configuration

```yaml
querier:
  frontend_worker:
    frontend_address: tempo-query-frontend:9095
    match_max_concurrent: true

  # Query behavior
  query_timeout: 30s              # Default query timeout
  max_concurrent_queries: 20      # Max parallel queries
  search_query_timeout: 30s       # Search timeout
  trace_by_id_timeout: 10s        # Trace lookup timeout

  # Shuffle sharding
  shuffle_sharding_ingesters_enabled: true
  shuffle_sharding_ingesters_lookback_period: 1h

  # Backend search windows
  query_backend_after: 15m        # Search backend if older than this
  query_ingesters_until: 30m      # Search ingesters if newer than this

  # Size limits
  max_spans_per_span_set: 100
  query_expr_size_limit_bytes: 131072  # 128KB
```

## Query Frontend Configuration

```yaml
query_frontend:
  # Result streaming
  search:
    concurrent_jobs: 1000
    target_bytes_per_job: 104857600  # 100MB
    default_result_limit: 20
    max_result_limit: 0             # 0 = unlimited
    max_duration: 168h              # 7 days

  # TraceQL metrics
  metrics:
    max_duration: 24h
    query_backend_after: 15m
    concurrent_jobs: 1000
    target_bytes_per_job: 104857600

  # Trace by ID
  trace_by_id:
    query_shards: 50
    hedge_requests_at: 2s
    hedge_requests_up_to: 2
```

## Compactor Configuration

```yaml
compactor:
  ring:
    kvstore:
      store: memberlist

  compaction:
    compaction_window: 1h         # Time window to compact
    block_retention: 336h         # 14 days default retention
    max_block_bytes: 107374182400 # ~107GB max block size
    compacted_block_retention: 1h
    v2_in_buffer_bytes: 5242880
    v2_out_buffer_bytes: 20971520
    v2_prefetch_traces_count: 1000

  # Deletion
  retention_concurrency: 10
```

## Storage Configuration

### Global Storage Settings

```yaml
storage:
  trace:
    backend: azure                # local, s3, gcs, azure

    # Block polling
    blocklist_poll: 5m
    blocklist_poll_fallback: true
    blocklist_poll_jitter_ms: 500
    blocklist_poll_tenant_index_builders: 1

    # Bloom filters
    bloom_filter_false_positive: 0.01
    bloom_filter_shard_size_bytes: 102400

    # Index
    index_downsample_bytes: 1048576

    # WAL
    wal:
      path: /var/tempo/wal
      encoding: snappy

    # Cache
    cache: memcached
    memcached:
      host: tempo-memcached:11211
      service: memcached-client
      timeout: 500ms
```

### Azure Storage

```yaml
storage:
  trace:
    backend: azure
    azure:
      container_name: tempo-traces
      storage_account_name: mystorageaccount
      # Authentication (choose one):
      use_federated_token: true           # Workload Identity
      # use_managed_identity: true        # Managed Identity
      # user_assigned_id: <client-id>     # User-assigned MI
      # storage_account_key: <key>        # Account key (dev)
      endpoint_suffix: blob.core.windows.net
      hedge_requests_at: 400ms
      hedge_requests_up_to: 2
```

### S3 Storage

```yaml
storage:
  trace:
    backend: s3
    s3:
      bucket: my-tempo-bucket
      region: us-east-1
      endpoint: s3.us-east-1.amazonaws.com
      access_key: <access-key>           # Or use IAM role
      secret_key: <secret-key>
      insecure: false
      hedge_requests_at: 400ms
      hedge_requests_up_to: 2
```

### GCS Storage

```yaml
storage:
  trace:
    backend: gcs
    gcs:
      bucket_name: my-tempo-bucket
      prefix: tempo/                     # Optional
      # Uses Workload Identity or service account
```

## Limits Configuration

### Global Limits

```yaml
overrides:
  defaults:
    # Ingestion limits
    ingestion_rate_limit_bytes: 15000000    # 15MB/s
    ingestion_burst_size_bytes: 20000000    # 20MB burst
    max_bytes_per_trace: 5000000            # 5MB per trace
    max_traces_per_user: 0                  # 0 = unlimited

    # Query limits
    max_search_bytes_per_trace: 0           # 0 = unlimited

    # Forwarders
    forwarders: []
```

### Per-Tenant Overrides

```yaml
overrides:
  defaults:
    ingestion_rate_limit_bytes: 15000000

  # Per-tenant overrides
  tenant-a:
    ingestion_rate_limit_bytes: 50000000
    max_bytes_per_trace: 10000000

  tenant-b:
    ingestion_rate_limit_bytes: 5000000
    max_bytes_per_trace: 2000000
```

## Metrics Generator Configuration

```yaml
metrics_generator:
  ring:
    kvstore:
      store: memberlist

  processor:
    service_graphs:
      wait: 10s
      max_items: 10000
      workers: 10
      histogram_buckets: [0.1, 0.2, 0.4, 0.8, 1.6, 3.2, 6.4, 12.8]

    span_metrics:
      histogram_buckets: [0.002, 0.004, 0.008, 0.016, 0.032, 0.064, 0.128, 0.256, 0.512, 1.024, 2.048, 4.096, 8.192, 16.384]
      intrinsic_dimensions:
        service: true
        span_name: true
        span_kind: true
        status_code: true
        status_message: false

    local_blocks:
      block_duration: 5m
      max_live_traces: 100000
      max_block_duration: 1h
      flush_check_period: 10s

  # Storage for WAL
  storage:
    path: /var/tempo/generator/wal
    remote_write:
      - url: http://prometheus:9090/api/v1/write
        send_exemplars: true

  # Collection interval
  collection_interval: 15s

  # Processor selection
  processors:
    - service-graphs
    - span-metrics
    # - local-blocks    # For TraceQL metrics
```

## Multi-Tenancy

```yaml
multitenancy_enabled: true        # Enable multi-tenant mode

# All requests require X-Scope-OrgID header
# Tenant ID is used for:
# - Storage isolation
# - Per-tenant limits
# - Access control (external)
```

## Hash Ring Configuration

### Memberlist (Default)

```yaml
memberlist:
  bind_port: 7946
  join_members:
    - tempo-gossip-ring:7946
  abort_if_cluster_join_fails: false
  max_join_retries: 10
  min_join_backoff: 1s
  max_join_backoff: 1m
```

### Consul

```yaml
ring:
  kvstore:
    store: consul
    consul:
      host: consul:8500
      acl_token: <token>
```

### Etcd

```yaml
ring:
  kvstore:
    store: etcd
    etcd:
      endpoints:
        - etcd:2379
```

## Search Configuration

```yaml
search:
  # Query sharding
  query_backend_after: 15m
  query_ingesters_until: 30m

  # External hedge requests
  external_hedge_requests_at: 8s
  external_hedge_requests_up_to: 2

  # Tag search
  prefer_self: 10                 # Prefer recent data weight
```

## Usage Report

```yaml
usage_report:
  reporting_enabled: true         # Send anonymous usage stats
```

## Important Default Values

| Parameter | Default | Description |
|-----------|---------|-------------|
| HTTP Port | 3200 | HTTP listen port |
| gRPC Port | 9095 | gRPC listen port |
| Rate Limit | 15MB/s | Ingestion rate limit |
| Burst Size | 20MB | Ingestion burst |
| Max Trace Size | 5MB | Maximum trace size |
| Trace Idle Period | 5s | Flush to WAL after idle |
| Block Retention | 336h (14d) | Block expiration |
| Max Block Size | 500MB | Ingester block size |
| Replication Factor | 3 | Number of ingester replicas |
| Query Timeout | 30s | Default query timeout |

## Helm Values Mapping

### Monolithic Mode

```yaml
# tempo chart values.yaml
tempo:
  server:
    http_listen_port: 3200

  storage:
    trace:
      backend: azure
      azure:
        container_name: tempo-traces
        storage_account_name: mystorageaccount

  ingester:
    trace_idle_period: 5s
    max_block_duration: 30m

  overrides:
    defaults:
      ingestion_rate_limit_bytes: 15000000
```

### Distributed Mode

```yaml
# tempo-distributed chart values.yaml
tempo:
  structuredConfig:
    storage:
      trace:
        backend: azure
        azure:
          container_name: tempo-traces

    ingester:
      trace_idle_period: 5s

    compactor:
      compaction:
        block_retention: 336h

    overrides:
      defaults:
        ingestion_rate_limit_bytes: 15000000
```

## Environment Variable Expansion

Enable environment variable substitution:

```yaml
# Helm values
extraArgs:
  config.expand-env: true

extraEnv:
  - name: AZURE_STORAGE_KEY
    valueFrom:
      secretKeyRef:
        name: tempo-secret
        key: storage-key

# In config
storage:
  trace:
    azure:
      storage_account_key: ${AZURE_STORAGE_KEY}
```

## Configuration Validation

```bash
# Validate configuration
tempo -config.file=/etc/tempo/config.yaml -config.verify-flags

# Print resolved configuration
tempo -config.file=/etc/tempo/config.yaml -print-config-stderr
```

## Common Configuration Patterns

### Development

```yaml
storage:
  trace:
    backend: local
    local:
      path: /var/tempo/traces

ingester:
  max_block_duration: 5m

compactor:
  compaction:
    block_retention: 24h
```

### Production (Azure)

```yaml
storage:
  trace:
    backend: azure
    azure:
      container_name: tempo-traces
      storage_account_name: prodstorageaccount
      use_federated_token: true
      hedge_requests_at: 400ms
      hedge_requests_up_to: 2

ingester:
  lifecycler:
    ring:
      replication_factor: 3

compactor:
  compaction:
    block_retention: 336h

overrides:
  defaults:
    ingestion_rate_limit_bytes: 50000000
    max_bytes_per_trace: 10000000
```

### High-Throughput

```yaml
distributor:
  ring:
    kvstore:
      store: memberlist

ingester:
  concurrent_flushes: 8
  max_block_bytes: 1073741824    # 1GB

querier:
  max_concurrent_queries: 50

overrides:
  defaults:
    ingestion_rate_limit_bytes: 600000000  # 600MB/s
    ingestion_burst_size_bytes: 800000000
```

## Breaking Changes

### Tempo 2.9+

- Review release notes before upgrading

### Port Migration (Chart v1.21.1+)

- Default HTTP port changed from 3100 to 3200

### Configuration Structure (Chart v1.19.0+)

- `overrides` structure reorganized
