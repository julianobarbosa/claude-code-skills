# AKS Control Plane Metrics Reference

## Overview

Control plane metrics provide visibility into the health and performance of AKS managed control plane components including API Server and etcd.

## Prerequisites

- Managed Identity Authentication on AKS cluster
- Managed service for Prometheus in Azure Monitor
- Azure Private Link is NOT supported

## Enable Control Plane Metrics

### Step 1: Install Preview Extension

```bash
az extension add --name aks-preview
az extension update --name aks-preview
```

### Step 2: Register Feature Flag

```bash
az feature register --namespace "Microsoft.ContainerService" \
  --name "AzureMonitorMetricsControlPlanePreview"

# Verify registration (takes a few minutes)
az feature show --namespace "Microsoft.ContainerService" \
  --name "AzureMonitorMetricsControlPlanePreview"
```

### Step 3: Refresh Provider

```bash
az provider register --namespace "Microsoft.ContainerService"
```

### Step 4: Enable Metrics on Cluster

```bash
az aks update --name $CLUSTER_NAME --resource-group $RESOURCE_GROUP
```

## Available Metrics

### API Server Metrics

| Metric | Description |
|--------|-------------|
| `apiserver_admission_webhook_admission_duration_seconds` | Webhook admission duration |
| `apiserver_longrunning_requests` | Long-running requests count |
| `apiserver_request_duration_seconds_bucket` | Request duration histogram (bucket) |
| `apiserver_request_duration_seconds_sum` | Request duration histogram (sum) |
| `apiserver_request_duration_seconds_count` | Request duration histogram (count) |
| `apiserver_request_total` | Total API requests |
| `apiserver_cache_list_fetched_objects_total` | Cache list fetches |
| `apiserver_flowcontrol_demand_seats_average` | Flow control demand |

### etcd Metrics

| Metric | Description |
|--------|-------------|
| `etcd_server_has_leader` | Leader election status |
| `etcd_mvcc_db_total_size_in_bytes` | Database size |
| `etcd_server_leader_changes_seen_total` | Leader change count |
| `etcd_disk_wal_fsync_duration_seconds` | WAL fsync latency |
| `etcd_disk_backend_commit_duration_seconds` | Backend commit latency |
| `etcd_network_peer_sent_bytes_total` | Peer network sent |
| `etcd_network_peer_received_bytes_total` | Peer network received |

## Default Configuration

```yaml
# Default targets (ON by default)
controlplane-apiserver = true
controlplane-etcd = true

# Optional targets (OFF by default)
controlplane-cluster-autoscaler = false
controlplane-kube-scheduler = false
controlplane-kube-controller-manager = false
controlplane-node-auto-provisioning = false
```

## Configuration Profiles

### Option A: Minimal Ingestion (Default)

Only collects essential metrics for API server and etcd.

### Option B: All Metrics from All Targets

```bash
# Download configmap
wget https://raw.githubusercontent.com/Azure/prometheus-collector/main/otelcollector/configmaps/ama-metrics-settings-configmap.yaml

# Edit: set minimalingestionprofile = false

# Apply
kubectl apply -f ama-metrics-settings-configmap.yaml -n kube-system
```

### Option C: Specific Metrics from Specific Targets

```yaml
# In configmap: set minimalingestionprofile = false
# Specify metrics with pipe-separated list

controlplane-apiserver = "apiserver_admission_webhook_admission_duration_seconds|apiserver_longrunning_requests"

# For histograms (include all three variants):
controlplane-apiserver = "apiserver_request_duration_seconds_bucket|apiserver_request_duration_seconds_sum|apiserver_request_duration_seconds_count"
```

Apply the configmap:

```bash
kubectl apply -f configmap-controlplane.yaml -n kube-system
```

## Optional Targets

### Cluster Autoscaler Metrics

```yaml
controlplane-cluster-autoscaler = true
```

Available metrics:

- `cluster_autoscaler_cluster_safe_to_autoscale`
- `cluster_autoscaler_scaled_up_nodes_total`
- `cluster_autoscaler_scaled_down_nodes_total`
- `cluster_autoscaler_unneeded_nodes_count`
- `cluster_autoscaler_unschedulable_pods_count`

### Kube Scheduler Metrics

```yaml
controlplane-kube-scheduler = true
```

Available metrics:

- `scheduler_pending_pods`
- `scheduler_unschedulable_pods`
- `scheduler_queue_incoming_pods_total`
- `scheduler_schedule_attempts_total`

### Kube Controller Manager Metrics

```yaml
controlplane-kube-controller-manager = true
```

Available metrics:

- `workqueue_depth`
- `rest_client_requests_total`
- `rest_client_request_duration_seconds`

### Node Auto-Provisioning (Karpenter)

```yaml
controlplane-node-auto-provisioning = true
```

Available metrics:

- `karpenter_pods_state`
- `karpenter_nodes_created_total`
- `karpenter_nodes_terminated_total`

## Querying Metrics

### Azure Portal

1. Navigate to AKS cluster resource
2. Left menu → Monitor > Monitor Settings
3. Access linked Azure Monitor workspace
4. Under "Managed Prometheus" → Prometheus explorer

### Pre-built Grafana Dashboards

- **API Server**: <https://grafana.com/grafana/dashboards/20331-kubernetes-api-server/>
- **etcd**: <https://grafana.com/grafana/dashboards/20330-kubernetes-etcd/>

## CLI Commands Reference

| Action | Command |
|--------|---------|
| Install extension | `az extension add --name aks-preview` |
| Update extension | `az extension update --name aks-preview` |
| Register feature | `az feature register --namespace "Microsoft.ContainerService" --name "AzureMonitorMetricsControlPlanePreview"` |
| Check feature | `az feature show --namespace "Microsoft.ContainerService" --name "AzureMonitorMetricsControlPlanePreview"` |
| Refresh provider | `az provider register --namespace "Microsoft.ContainerService"` |
| Enable metrics | `az aks update --name $CLUSTER_NAME --resource-group $RESOURCE_GROUP` |
| Disable metrics | `az aks update --disable-azure-monitor-metrics --name $CLUSTER_NAME --resource-group $RESOURCE_GROUP` |
| Unregister feature | `az feature unregister --namespace "Microsoft.ContainerService" --name "AzureMonitorMetricsControlPlanePreview"` |

## Important Notes

1. **Preview Feature**: Not production-ready
2. **Private Link**: Not supported
3. **Self-hosted Prometheus**: Cannot scrape control plane metrics
4. **Managed Prometheus Only**: Only supported collection method
5. **Configmap Namespace**: Apply to `kube-system` namespace
6. **Histogram Metrics**: Always include `_bucket`, `_sum`, and `_count` suffixes
7. **Data Latency**: Several minutes after enabling
8. **High-Cardinality Warning**: `apiserver_request_sli_duration_seconds_bucket` not collected by default

## Scrape Configuration

Default scrape interval: 30 seconds (configurable)

```yaml
# Configmap fields to verify
default-targets-metrics-keep-list: <metrics>
minimal-ingestion-profile: true/false
default-scrape-settings-enabled: true/false
```
