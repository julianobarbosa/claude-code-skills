# API Server and etcd Troubleshooting Guide

## Common API Server Issues

### Symptoms

| Symptom | Description |
|---------|-------------|
| CrashLoopBackOff | Webhook failures blocking calls |
| Command Timeouts | Commands exceed SLA guarantees |
| High Latencies | 30+ seconds for kubectl commands |
| HTTP 429 | API server overloaded/throttling |
| Server Unable to Handle Request | Control plane unresponsive |

### Root Causes

1. Network rules blocking agent-to-API traffic
2. Custom webhook deadlock
3. Resource leakage (object accumulation)
4. AKS managed API server guard activation
5. Excessive LIST/PUT calls from clients
6. High etcd memory usage

## etcd Database Management

### Capacity Limits

| Property | Value |
|----------|-------|
| Default Limit | 8GB total capacity |
| Alert Threshold | 20GB memory usage |
| Large Database | >2GB considered large |

### Metric Names by Version

| Kubernetes Version | Metric Name |
|-------------------|-------------|
| v1.25 and earlier | `etcd_db_total_size_in_bytes` |
| v1.26-1.28 | `apiserver_storage_db_total_size_in_bytes` |

## Diagnostic Commands

### Check API Server Connectivity

```bash
kubectl aks config import \
  --subscription <subscriptionID> \
  --resource-group <resourceGroup> \
  --cluster-name <clusterName>

kubectl aks check-apiserver-connectivity --node <nodeName>
```

### Monitor etcd Database Size

```bash
kubectl get --raw /metrics | grep -E "etcd_db_total_size_in_bytes|apiserver_storage_size_bytes|apiserver_storage_db_total_size_in_bytes"
```

### Check API Server Metrics

```bash
kubectl get --raw /metrics | grep apiserver_
```

### Identify Webhooks

```bash
kubectl get validatingwebhookconfigurations
kubectl get mutatingwebhookconfigurations
```

### Analyze FlowSchemas

```bash
kubectl get flowschemas
kubectl get prioritylevelconfigurations
```

## Log Analytics Queries

### Top API Users (Resource-Specific Mode)

```kusto
AKSAudit
| where TimeGenerated between(now(-1h)..now())
| summarize count() by UserAgent
| top 10 by count_
```

### Top API Users (Azure Diagnostics Mode)

```kusto
AzureDiagnostics
| where Category == "kube-audit"
| extend event = parse_json(log_s)
| extend User = tostring(event.user.username)
| summarize count() by User
| top 10 by count_
```

### P99 Latency by Operation

```kusto
AKSAudit
| where TimeGenerated between(now(-1h)..now())
| extend HttpMethod = Verb
| extend Resource = tostring(ObjectRef.resource)
| extend latency = datetime_diff('millisecond', StageReceivedTime, RequestReceivedTime)
| summarize p99latency=percentile(latency, 99) by HttpMethod, Resource
```

### Failed API Requests

```kusto
AKSAudit
| where TimeGenerated > ago(1h)
| where ResponseStatus.code >= 400
| summarize count() by ResponseStatus.code, Verb, ObjectRef.resource
| order by count_ desc
```

## Resolution Steps

### Cause 1: Network Issues

Reconfigure network policies to allow unrestricted traffic between agent nodes and API server.

```bash
# Validate connectivity
kubectl aks check-apiserver-connectivity --node <nodeName>
```

### Cause 2: Webhook Deadlock

```bash
# Remove problematic webhooks
kubectl delete validatingwebhookconfigurations <name>
kubectl delete mutatingwebhookconfigurations <name>
```

### Cause 3: Resource Leakage

**Implement Resource Quotas:**

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: object-quota
spec:
  hard:
    pods: "100"
    jobs.batch: "50"
```

**Cleanup Completed Jobs:**

```bash
# Delete completed jobs
kubectl delete jobs --field-selector status.successful=1

# Delete failed pods
kubectl delete pods --field-selector status.phase=Failed

# Bulk delete by label
kubectl delete pods -l app=old-app
```

**Implement Auto-cleanup with TTL:**

```yaml
apiVersion: batch/v1
kind: Job
spec:
  ttlSecondsAfterFinished: 3600  # Auto-delete after 1 hour
```

### Cause 4: API Server Guard Activation

```bash
# Identify guard
kubectl get flowschemas
kubectl get prioritylevelconfigurations

# Remove guard
kubectl delete flowschema aks-managed-apiserver-guard
kubectl delete prioritylevelconfiguration aks-managed-apiserver-guard

# Preserve custom configs
kubectl label prioritylevelconfiguration aks-managed-apiserver-guard \
  aks-managed-skip-update-operation=true
```

### Cause 5: Excessive API Calls

**Optimize Client Patterns:**

- Use field selectors to limit LIST results
- Implement client-side caching
- Use informers instead of repeated LIST calls
- Batch operations where possible

**Throttle Problematic Clients:**

```yaml
apiVersion: flowcontrol.apiserver.k8s.io/v1beta2
kind: FlowSchema
metadata:
  name: restrict-bad-client
spec:
  priorityLevelConfiguration:
    name: very-low-priority
  rules:
  - resourceRules:
    - resources: ["pods"]
      verbs: ["list"]
    subjects:
    - kind: ServiceAccount
      serviceAccount:
        name: bad-client-account
        namespace: default
---
apiVersion: flowcontrol.apiserver.k8s.io/v1beta2
kind: PriorityLevelConfiguration
metadata:
  name: very-low-priority
spec:
  type: Limited
  limited:
    assuredConcurrencyShares: 5
    limitResponse:
      type: Reject
```

### Cause 6: High etcd Memory

- Follow Cause 3 & 5 solutions
- Move environment variables to ConfigMaps
- Split large Secrets/ConfigMaps
- Optimize resource specifications

## Azure Portal Diagnostics

**Access Path:** AKS cluster → Diagnose and Solve Problems → Cluster and Control Plane Availability and Performance

### Available Tools

| Tool | Description |
|------|-------------|
| Etcd Capacity Issues | Database size growth analysis |
| Etcd Performance Issues | Performance bottleneck identification |
| API Server Resource Intensive Listing Detector | Excessive LIST operation detection |
| Etcd Performance Analyzer | Deep etcd metrics analysis |
| Resource Health | Component downtime visibility |

## Monitoring Best Practices

### Proactive Monitoring

- Monitor etcd database size continuously
- Track API server latency metrics (P99)
- Set alerts on HTTP 429 response rates
- Monitor control plane component health

### Alert Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| etcd Database Size | >4GB | >6GB |
| API Server P99 Latency | >5s | >15s |
| HTTP 429 Rate | >1% | >5% |
| Inflight Requests | >400 | >800 |

## Prevention Strategy

1. **Implement resource quotas** per namespace
2. **Use TTL values** for temporary objects
3. **Implement client-side caching** and informers
4. **Set up field/label selector** best practices
5. **Regular cleanup** of failed/completed jobs
6. **Monitor excessive API users**

## Critical Warning

If API server becomes unresponsive due to severe etcd memory pressure, **contact Azure support immediately** rather than attempting troubleshooting steps.

## Diagnostic Script

```bash
#!/bin/bash
# diagnose-control-plane.sh

echo "=== etcd Database Size ==="
kubectl get --raw /metrics 2>/dev/null | grep -E "etcd_db_total_size|apiserver_storage" | head -5

echo -e "\n=== API Server Metrics ==="
kubectl get --raw /metrics 2>/dev/null | grep -E "apiserver_request_total|apiserver_current_inflight" | head -10

echo -e "\n=== FlowSchemas ==="
kubectl get flowschemas

echo -e "\n=== Priority Level Configurations ==="
kubectl get prioritylevelconfigurations

echo -e "\n=== Validating Webhooks ==="
kubectl get validatingwebhookconfigurations

echo -e "\n=== Mutating Webhooks ==="
kubectl get mutatingwebhookconfigurations

echo -e "\n=== Object Counts ==="
echo "Pods: $(kubectl get pods -A --no-headers 2>/dev/null | wc -l)"
echo "Jobs: $(kubectl get jobs -A --no-headers 2>/dev/null | wc -l)"
echo "ConfigMaps: $(kubectl get configmaps -A --no-headers 2>/dev/null | wc -l)"
echo "Secrets: $(kubectl get secrets -A --no-headers 2>/dev/null | wc -l)"
```
