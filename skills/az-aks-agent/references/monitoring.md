# AKS Monitoring Comprehensive Guide

## Architecture Overview

AKS monitoring operates on a multi-layered architecture with five primary data sources:

```
┌─────────────────────────────────────────────────────────────┐
│                     Azure Monitor                            │
├────────────┬────────────┬────────────┬────────────┬─────────┤
│  Platform  │ Prometheus │  Activity  │  Resource  │Container│
│  Metrics   │  Metrics   │    Logs    │    Logs    │Insights │
│  (Free)    │ (Managed)  │ (Sub-level)│  (11 cat)  │  (App)  │
└────────────┴────────────┴────────────┴────────────┴─────────┘
```

## Data Sources

| Source | Collection | Cost | Use Case |
|--------|------------|------|----------|
| Platform Metrics | Automatic | Free | Basic health monitoring |
| Prometheus Metrics | Managed Service | Per ingestion | Cloud-native metrics |
| Activity Logs | Automatic | Free | Subscription events |
| Resource Logs | Diagnostic Settings | Per GB | Control plane logs |
| Container Insights | Enable addon | Per GB | App telemetry |

## Container Insights Setup

### Prerequisites

- Log Analytics workspace (same subscription as AKS)
- Managed identity authentication (recommended)
- Azure Monitor Data Collection Rules (DCRs)

### Enable via Azure CLI

```bash
az aks enable-addons \
  --resource-group <resource-group> \
  --name <cluster-name> \
  --addons monitoring \
  --workspace-resource-id <log-analytics-workspace-id>
```

### Cost Optimization Groupings (via DCRs)

| Grouping | Tables | Use Case |
|----------|--------|----------|
| All (Default) | All standard CI tables | Required for default visualizations |
| Performance | Perf, InsightsMetrics | Core performance tracking |
| Logs & Events | ContainerLog/V2, KubeEvents, KubePodInventory | Recommended with Prometheus |
| Workloads | Multiple tables | Workload-specific monitoring |
| Persistent Volumes | InsightsMetrics, KubePVInventory | Storage monitoring |

## Resource Logs Configuration

### Create Diagnostic Settings

```bash
az monitor diagnostic-settings create \
  --name AKS-Diagnostics \
  --resource /subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.ContainerService/managedClusters/{cluster} \
  --logs '[
    {"category": "kube-audit", "enabled": true},
    {"category": "kube-audit-admin", "enabled": true},
    {"category": "kube-apiserver", "enabled": true},
    {"category": "kube-controller-manager", "enabled": true},
    {"category": "kube-scheduler", "enabled": true},
    {"category": "cluster-autoscaler", "enabled": true},
    {"category": "cloud-controller-manager", "enabled": true},
    {"category": "guard", "enabled": true},
    {"category": "csi-azuredisk-controller", "enabled": true},
    {"category": "csi-azurefile-controller", "enabled": true},
    {"category": "csi-snapshot-controller", "enabled": true}
  ]' \
  --workspace /subscriptions/{sub}/resourcegroups/{rg}/providers/microsoft.operationalinsights/workspaces/{workspace} \
  --export-to-resource-specific true
```

### Log Categories

| Category | Description | Export Cost |
|----------|-------------|-------------|
| kube-apiserver | API server operations | Standard |
| kube-audit | All audit events | Standard |
| kube-audit-admin | Excludes get/list events | Standard |
| kube-controller-manager | Controller operations | Standard |
| kube-scheduler | Scheduler events | Standard |
| cluster-autoscaler | Auto-scaling operations | Standard |
| cloud-controller-manager | Cloud operations | Export Cost |
| guard | Authentication logs | Standard |
| csi-azuredisk-controller | Azure Disk CSI | Export Cost |
| csi-azurefile-controller | Azure File CSI | Export Cost |
| csi-snapshot-controller | Snapshot operations | Export Cost |
| karpenter-events | Node Auto Provisioning | Export Cost |

## Collection Modes

### Azure Diagnostics Mode

All data routes to `AzureDiagnostics` table, identified via Category column.

```kusto
AzureDiagnostics
| where Category == "kube-apiserver"
```

### Resource-Specific Mode (Recommended)

Data routes to dedicated tables:

- `AKSAudit` - All audit logs
- `AKSAuditAdmin` - Excludes get/list events
- `AKSControlPlane` - Control plane logs

```kusto
AKSAudit
| where TimeGenerated > ago(1h)

AKSControlPlane
| where Category == "kube-apiserver"
```

## Log Analytics Tables

| Table | Description |
|-------|-------------|
| AzureActivity | Azure resource activity logs |
| AzureDiagnostics | Multi-component diagnostic logs |
| AzureMetrics | Platform metrics |
| AKSAudit | Kubernetes API audit logs |
| AKSAuditAdmin | Kubernetes admin audit logs |
| AKSControlPlane | Control plane component logs |
| ContainerInventory | Container information |
| ContainerLog / ContainerLogV2 | Application logs |
| KubeEvents | Kubernetes events |
| KubeNodeInventory | Node inventory data |
| KubePodInventory | Pod inventory data |
| KubeServices | Kubernetes services |
| InsightsMetrics | Container insights metrics |
| Perf | Performance data |
| Heartbeat | Agent heartbeat |
| Syslog | System logs |

## Log Analytics Queries

### Count Logs by Category

```kusto
AzureDiagnostics
| where ResourceType == "MANAGEDCLUSTERS"
| summarize count() by Category
```

### API Server Logs

```kusto
AzureDiagnostics
| where Category == "kube-apiserver"
```

### Detailed Audit Logs

```kusto
let starttime = datetime("2023-02-23");
let endtime = datetime("2023-02-24");
AzureDiagnostics
| where TimeGenerated between(starttime..endtime)
| where Category == "kube-audit"
| extend event = parse_json(log_s)
| extend HttpMethod = tostring(event.verb)
| extend User = tostring(event.user.username)
| extend Apiserver = pod_s
| extend SourceIP = tostring(event.sourceIPs[0])
| project TimeGenerated, Category, HttpMethod, User, Apiserver, SourceIP, OperationName, event
```

### Container Logs with Errors

```kusto
ContainerLogV2
| where LogLevel == "error"
| project TimeGenerated, PodName, ContainerName, LogMessage
```

### Pod Restart Analysis

```kusto
KubePodInventory
| where PodRestartCount > 0
| summarize max(PodRestartCount) by PodName, Namespace
| order by max_PodRestartCount desc
```

### Node Resource Usage

```kusto
InsightsMetrics
| where Name == "node_cpu_usage_percentage" or Name == "node_memory_rss_percentage"
| summarize avg(Val) by Name, Computer, bin(TimeGenerated, 5m)
| render timechart
```

## Alert Configuration

### Recommended Alert Rules

| Alert | Description |
|-------|-------------|
| KubeCPUQuotaOvercommit | CPU quota overcommitment |
| KubeMemoryQuotaOvercommit | Memory quota overcommitment |
| KubeContainerOOMKilledCount | Container OOMKilled events |
| KubeNodeUnreachable | Node unreachable |
| KubePodCrashLooping | Pod crash looping |
| KubeContainerAverageCPUHigh | High container CPU |
| KubeContainerAverageMemoryHigh | High container memory |

### Create Metric Alert

```bash
az monitor metrics alert create \
  --name "High-CPU-Alert" \
  --resource-group <rg> \
  --scopes <aks-resource-id> \
  --condition "avg node_cpu_usage_percentage > 80" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --action <action-group-id>
```

## Real-Time Monitoring

### Live Data Features

- Live logs for pods, containers, workloads
- Live metrics for CPU, memory, network I/O
- Live events for Kubernetes resources
- Requires: Container Insights + direct Kubernetes API access

### Enable Live Metrics

```bash
kubectl proxy &
# Access via Azure Portal Live Data feature
```

## Network Metrics

### Default Metrics (K8s 1.29+)

| Metric | Description |
|--------|-------------|
| Forwarded Packets/Bytes | Network traffic forwarded |
| Dropped Packets | Packets dropped |
| TCP/UDP States | Connection state counts |

### Disable Per-Node

```bash
kubectl label node <node-name> networking.azure.com/node-network-metrics=disabled
```

## Integration Options

| Integration | Purpose |
|-------------|---------|
| Container Insights | Logs, events, performance |
| Managed Prometheus | Cloud-native metrics |
| Azure Managed Grafana | Visualization + dashboards |
| Azure Copilot | Portal configuration |
| Power BI | Business intelligence |

## Best Practices

1. **Use Resource-Specific Mode**: Easier querying and Basic logs tier support
2. **Enable ContainerLogV2**: Better schema, cost savings with Basic tier
3. **Implement Cost Groupings**: Use DCRs to control ingestion
4. **Set Up Alerts**: Proactive issue detection
5. **Use Prometheus for Metrics**: Cloud-native compatibility
6. **Retain Critical Logs**: Configure appropriate retention periods
7. **Disable Unnecessary Logs**: kube-audit generates high volume; use kube-audit-admin
