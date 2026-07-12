# Pyroscope Troubleshooting Reference

Complete guide for diagnosing and resolving common Pyroscope issues.

## Diagnostic Commands

### Pod Status

```bash
# Check all Pyroscope pods
kubectl get pods -n pyroscope -l app.kubernetes.io/name=pyroscope

# Describe specific pod
kubectl describe pod pyroscope-ingester-0 -n pyroscope

# Check pod events
kubectl get events -n pyroscope --sort-by='.lastTimestamp'
```

### Logs

```bash
# All components
kubectl logs -n pyroscope -l app.kubernetes.io/name=pyroscope --tail=100

# Specific component
kubectl logs -n pyroscope -l app.kubernetes.io/component=ingester --tail=200
kubectl logs -n pyroscope -l app.kubernetes.io/component=distributor --tail=200
kubectl logs -n pyroscope -l app.kubernetes.io/component=querier --tail=200
kubectl logs -n pyroscope -l app.kubernetes.io/component=compactor --tail=200

# Follow logs
kubectl logs -f -n pyroscope -l app.kubernetes.io/component=ingester

# Previous container logs (after restart)
kubectl logs -n pyroscope pyroscope-ingester-0 --previous
```

### Health Checks

```bash
# Readiness
kubectl exec -it pyroscope-0 -n pyroscope -- curl http://localhost:4040/ready

# Ring status (ingesters)
kubectl exec -it pyroscope-0 -n pyroscope -- curl http://localhost:4040/ingester/ring

# Configuration
kubectl exec -it pyroscope-0 -n pyroscope -- curl http://localhost:4040/config

# Metrics
kubectl exec -it pyroscope-0 -n pyroscope -- curl http://localhost:4040/metrics
```

### Connectivity Tests

```bash
# Test from within cluster
kubectl run test-pyroscope --image=curlimages/curl:latest --rm -it -- \
  curl -v http://pyroscope.pyroscope:4040/ready

# Test push endpoint
kubectl run test-push --image=curlimages/curl:latest --rm -it -- \
  curl -X POST http://pyroscope.pyroscope:4040/ingest \
  -H "Content-Type: application/json" \
  -d '{"name":"test"}'

# Test from SDK perspective
kubectl run test-sdk --image=curlimages/curl:latest --rm -it -- \
  curl -v http://pyroscope-distributor.pyroscope:4040/ready
```

## Common Issues

### 1. Ingester Out of Memory (OOM)

**Symptoms:**

- Pod restarts with OOMKilled status
- Memory usage spikes before crash
- Ingester logs show memory pressure

**Diagnosis:**

```bash
# Check OOM status
kubectl describe pod pyroscope-ingester-0 -n pyroscope | grep -A5 "State:"

# Check memory usage
kubectl top pods -n pyroscope -l app.kubernetes.io/component=ingester
```

**Solutions:**

```yaml
# Increase memory limits
ingester:
  resources:
    limits:
      memory: 16Gi
    requests:
      memory: 8Gi

# Reduce batch size
pyroscope:
  config:
    ingester:
      max_block_duration: 30m  # Flush more frequently
```

### 2. Storage Authentication Failed

**Symptoms:**

- Ingester/Compactor failing to start
- "access denied" or "unauthorized" in logs
- Storage-related error messages

**AWS S3:**

```bash
# Verify IAM role
aws sts get-caller-identity

# Check bucket policy
aws s3 ls s3://pyroscope-bucket/

# Verify environment variables
kubectl exec -it pyroscope-ingester-0 -n pyroscope -- env | grep AWS
```

**Azure Blob:**

```bash
# Verify managed identity
az identity show --name pyroscope-identity --resource-group <rg>

# Check RBAC assignment
az role assignment list --scope /subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.Storage/storageAccounts/<storage>

# Assign if missing
az role assignment create \
  --role "Storage Blob Data Contributor" \
  --assignee-object-id <principal-id> \
  --scope <storage-scope>

# Create containers if missing
az storage container create --name pyroscope-data --account-name <storage>
```

**GCS:**

```bash
# Verify service account
kubectl get secret pyroscope-gcs-sa -n pyroscope -o yaml

# Check IAM binding
gcloud projects get-iam-policy <project> --filter="bindings.members:serviceAccount:*"
```

### 3. Profiles Not Appearing

**Symptoms:**

- No data in Grafana Pyroscope datasource
- SDKs appear to send successfully
- No errors in SDK logs

**Diagnosis:**

```bash
# Check distributor is receiving data
kubectl logs -n pyroscope -l app.kubernetes.io/component=distributor --tail=100 | grep -i "push"

# Check ingester is receiving from distributor
kubectl logs -n pyroscope -l app.kubernetes.io/component=ingester --tail=100 | grep -i "append"

# Verify ring membership
kubectl exec -it pyroscope-0 -n pyroscope -- curl http://localhost:4040/ingester/ring | jq '.shards'
```

**Solutions:**

```yaml
# Verify SDK configuration
pyroscope.Start(pyroscope.Config{
    ApplicationName: "my-app",       # Must be set
    ServerAddress:   "http://pyroscope:4040", # Verify URL
    Logger:          pyroscope.StandardLogger, # Enable logging
})

# Check network policy allows traffic
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-pyroscope-ingestion
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: pyroscope
  ingress:
    - from: []
      ports:
        - port: 4040
```

### 4. Query Timeouts

**Symptoms:**

- Queries hang or timeout
- "context deadline exceeded" errors
- Slow flame graph rendering

**Diagnosis:**

```bash
# Check querier logs
kubectl logs -n pyroscope -l app.kubernetes.io/component=querier --tail=100 | grep -i "timeout\|slow"

# Check query-frontend logs
kubectl logs -n pyroscope -l app.kubernetes.io/component=query-frontend --tail=100

# Check store-gateway for historical queries
kubectl logs -n pyroscope -l app.kubernetes.io/component=store-gateway --tail=100
```

**Solutions:**

```yaml
# Increase query timeout
pyroscope:
  config:
    querier:
      query_timeout: 5m
      max_concurrent: 8

    query_scheduler:
      max_outstanding_requests_per_tenant: 2048

# Scale queriers
querier:
  replicas: 5
```

### 5. High Cardinality Labels

**Symptoms:**

- Memory usage increases rapidly
- Slow queries
- "too many labels" errors

**Diagnosis:**

```bash
# Check unique label combinations
kubectl exec -it pyroscope-0 -n pyroscope -- \
  curl "http://localhost:4040/querier.v1.QuerierService/Series" \
  -H "Content-Type: application/json" \
  -d '{"matchers":[]}'
```

**Solutions:**

```yaml
# Limit label cardinality
pyroscope:
  config:
    validation:
      max_label_names_per_series: 25
      max_label_name_length: 1024
      max_label_value_length: 2048
```

### 6. Ring Unhealthy

**Symptoms:**

- Ingesters showing as UNHEALTHY
- "ring not ready" errors
- Failed writes

**Diagnosis:**

```bash
# Check ring status
kubectl exec -it pyroscope-0 -n pyroscope -- curl http://localhost:4040/ingester/ring

# Check memberlist connectivity
kubectl exec -it pyroscope-0 -n pyroscope -- curl http://localhost:4040/memberlist

# Verify DNS resolution
kubectl exec -it pyroscope-0 -n pyroscope -- nslookup pyroscope-memberlist
```

**Solutions:**

```yaml
# Verify memberlist configuration
pyroscope:
  config:
    memberlist:
      bind_port: 7946
      join:
        - dnssrv+pyroscope-memberlist._tcp.pyroscope.svc.cluster.local

# Check headless service exists
apiVersion: v1
kind: Service
metadata:
  name: pyroscope-memberlist
spec:
  clusterIP: None
  selector:
    app.kubernetes.io/name: pyroscope
  ports:
    - name: memberlist
      port: 7946
      protocol: UDP
```

### 7. Compactor Not Running

**Symptoms:**

- Blocks not being compacted
- Storage usage growing rapidly
- Old data not being deleted

**Diagnosis:**

```bash
# Check compactor logs
kubectl logs -n pyroscope -l app.kubernetes.io/component=compactor --tail=200

# Check compactor ring
kubectl exec -it pyroscope-compactor-0 -n pyroscope -- \
  curl http://localhost:4040/compactor/ring
```

**Solutions:**

```yaml
# Verify compactor configuration
pyroscope:
  config:
    compactor:
      compaction_interval: 30m
      retention_enabled: true
      retention_delete_delay: 2h
      compaction_concurrency: 4
```

### 8. SDK Connection Refused

**Symptoms:**

- "connection refused" in application logs
- Profiles not being sent
- SDK timeout errors

**Diagnosis:**

```bash
# Test connectivity from application pod
kubectl exec -it <app-pod> -n <app-ns> -- \
  curl -v http://pyroscope.pyroscope:4040/ready

# Check service exists
kubectl get svc -n pyroscope pyroscope
```

**Solutions:**

```bash
# Verify service DNS
kubectl run test-dns --image=busybox --rm -it -- nslookup pyroscope.pyroscope.svc.cluster.local

# Check endpoint
kubectl get endpoints -n pyroscope pyroscope
```

### 9. Alloy Not Scraping

**Symptoms:**

- No profiles from auto-instrumented apps
- Alloy running but not collecting data
- Annotations present but ignored

**Diagnosis:**

```bash
# Check Alloy logs
kubectl logs -n pyroscope -l app.kubernetes.io/name=alloy --tail=200

# Verify targets
kubectl exec -it <alloy-pod> -n pyroscope -- \
  wget -qO- http://localhost:12345/agent/api/v1/targets
```

**Solutions:**

```yaml
# Verify pod annotations
apiVersion: apps/v1
kind: Deployment
metadata:
  name: my-app
spec:
  template:
    metadata:
      annotations:
        profiles.grafana.com/cpu.scrape: "true"
        profiles.grafana.com/cpu.port: "8080"

# Check Alloy configuration
alloy:
  alloy:
    configMap:
      content: |
        discovery.kubernetes "pods" {
          role = "pod"
        }
        pyroscope.scrape "default" {
          targets = discovery.kubernetes.pods.targets
          forward_to = [pyroscope.write.default.receiver]
        }
```

### 10. Store-Gateway Slow Sync

**Symptoms:**

- Historical queries slow
- Store-gateway high CPU during sync
- "bucket sync" messages in logs

**Diagnosis:**

```bash
# Check sync status
kubectl logs -n pyroscope -l app.kubernetes.io/component=store-gateway --tail=200 | grep -i "sync"

# Check block count
kubectl exec -it pyroscope-store-gateway-0 -n pyroscope -- \
  curl http://localhost:4040/store-gateway/blocks
```

**Solutions:**

```yaml
# Tune sync interval
pyroscope:
  config:
    store_gateway:
      sync_interval: 30m  # Increase if too frequent
      ignore_blocks_within: 6h  # Skip recent blocks
```

## Performance Tuning

### Ingestion Optimization

```yaml
# High throughput configuration
pyroscope:
  config:
    distributor:
      push_timeout: 10s
      ingestion_tenant_shard_size: 8

    ingester:
      max_block_duration: 1h
      flush_check_period: 30s
```

### Query Optimization

```yaml
# Faster queries
pyroscope:
  config:
    querier:
      max_concurrent: 16
      query_store_after: 2h

    query_frontend:
      max_outstanding_per_tenant: 400
```

### Storage Optimization

```yaml
# Efficient storage
pyroscope:
  config:
    compactor:
      compaction_concurrency: 8
      block_ranges:
        - 1h
        - 4h
        - 12h
```

## Metrics to Monitor

### Key Metrics

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `pyroscope_ingester_memory_profiles` | In-memory profiles | > 1M |
| `pyroscope_distributor_push_duration_seconds` | Push latency | > 5s p99 |
| `pyroscope_querier_query_duration_seconds` | Query latency | > 30s p99 |
| `pyroscope_compactor_runs_completed_total` | Compaction runs | 0 for > 2h |
| `pyroscope_ring_members` | Ring membership | < expected |

### Prometheus Rules

```yaml
groups:
  - name: pyroscope
    rules:
      - alert: PyroscopeIngesterOOM
        expr: |
          container_memory_working_set_bytes{container="ingester"}
          / container_spec_memory_limit_bytes{container="ingester"} > 0.9
        for: 5m
        labels:
          severity: warning

      - alert: PyroscopeCompactorNotRunning
        expr: |
          increase(pyroscope_compactor_runs_completed_total[2h]) == 0
        for: 10m
        labels:
          severity: warning

      - alert: PyroscopeRingUnhealthy
        expr: |
          pyroscope_ring_members{state="UNHEALTHY"} > 0
        for: 5m
        labels:
          severity: critical
```

## Log Analysis

### Common Log Patterns

**Successful ingestion:**

```text
level=info component=distributor msg="pushed profiles" tenant=anonymous count=100
```

**Storage errors:**

```text
level=error component=ingester msg="failed to upload block" err="access denied"
```

**Ring issues:**

```text
level=warn component=ring msg="instance not found in ring" instance=pyroscope-ingester-0
```

**Query issues:**

```text
level=error component=querier msg="query failed" err="context deadline exceeded"
```

### Grep Commands

```bash
# Find errors
kubectl logs -n pyroscope -l app.kubernetes.io/name=pyroscope | grep -i "error\|fail\|panic"

# Find storage issues
kubectl logs -n pyroscope -l app.kubernetes.io/component=ingester | grep -i "storage\|upload\|s3\|azure\|gcs"

# Find ring issues
kubectl logs -n pyroscope -l app.kubernetes.io/name=pyroscope | grep -i "ring\|memberlist"

# Find query issues
kubectl logs -n pyroscope -l app.kubernetes.io/component=querier | grep -i "query\|timeout"
```

## Recovery Procedures

### Restart Components

```bash
# Restart specific component
kubectl rollout restart deployment/pyroscope-distributor -n pyroscope
kubectl rollout restart statefulset/pyroscope-ingester -n pyroscope

# Restart all
kubectl rollout restart deployment -n pyroscope
kubectl rollout restart statefulset -n pyroscope
```

### Clear Stuck State

```bash
# Delete PVC if corrupted (data loss!)
kubectl delete pvc pyroscope-ingester-data-pyroscope-ingester-0 -n pyroscope

# Force delete stuck pod
kubectl delete pod pyroscope-ingester-0 -n pyroscope --force --grace-period=0
```

### Scale Down/Up

```bash
# Scale down
kubectl scale statefulset pyroscope-ingester --replicas=0 -n pyroscope

# Scale up
kubectl scale statefulset pyroscope-ingester --replicas=3 -n pyroscope
```
