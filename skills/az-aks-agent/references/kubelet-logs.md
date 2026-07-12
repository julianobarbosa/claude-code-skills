# AKS Kubelet Logs Guide

## Overview

Kubelet logs provide critical information about node-level operations, pod lifecycle management, and container runtime interactions in AKS clusters.

## Access Methods

### Method A: kubectl Raw API (Quick - No SSH)

```bash
# Set node name
export NODE_NAME="aks-agentpool-xxxxxxx-0"

# Get kubelet logs via raw API
kubectl get --raw "/api/v1/nodes/$NODE_NAME/proxy/logs/messages" | grep kubelet
```

**Advantages:**

- Quickest method
- No SSH access required
- Useful for rapid diagnostics

### Method B: SSH Connection (Detailed Access)

```bash
# 1. Establish SSH connection to node
# 2. Enter host environment
chroot /host

# 3. View kubelet logs
journalctl -u kubelet -o cat
```

### Method C: Container Insights

Azure Monitor Container Insights provides:

- Syslog collection for kubelet logs
- Integration with Log Analytics
- Centralized log aggregation

## Log Locations

### Linux Nodes

| Property | Value |
|----------|-------|
| Access Method | journalctl (systemd) |
| View Command | `journalctl -u kubelet -o cat` |
| Storage | systemd journal |
| Unit | kubelet.service |

### Windows Nodes

| Property | Value |
|----------|-------|
| File Location | `C:\k\kubelet.log` |
| View Command | `more C:\k\kubelet.log` |
| Format | Plain text |

## Log Format

```
I0508 12:26:17.905042    8672 kubelet_node_status.go:497] Using Node Hostname from cloudprovider: "aks-agentpool-xxxxxxx-0"
I0508 12:26:28.920125    8672 server.go:796] GET /stats/summary: (10.370874ms) 200 [[Ruby] 10.244.0.x:52492]
```

### Format Components

| Component | Description | Example |
|-----------|-------------|---------|
| Log Level | I=Info, W=Warning, E=Error | `I` |
| Timestamp | MMDD HH:MM:SS.microseconds | `0508 12:26:17.905042` |
| Process ID | Kubelet process identifier | `8672` |
| Source File | File name and line number | `kubelet_node_status.go:497` |
| Message | Log content | `Using Node Hostname...` |

## CLI Commands

### Prerequisites

```bash
export RESOURCE_GROUP_NAME="<ResourceGroupName>"
export AKS_CLUSTER_NAME="<AKSClusterName>"
az aks get-credentials --resource-group $RESOURCE_GROUP_NAME --name $AKS_CLUSTER_NAME
```

### Retrieve Kubelet Logs

```bash
# Via kubectl raw API
export NODE_NAME="aks-agentpool-xxxxxxx-0"
kubectl get --raw "/api/v1/nodes/$NODE_NAME/proxy/logs/messages" | grep kubelet

# Via az aks command invoke
az aks command invoke -g $RESOURCE_GROUP_NAME -n $AKS_CLUSTER_NAME \
  --command "chroot /host && journalctl -u kubelet -o cat"
```

### Filter Logs

```bash
# Last 100 lines
kubectl get --raw "/api/v1/nodes/$NODE_NAME/proxy/logs/messages" | grep kubelet | tail -100

# Errors only
kubectl get --raw "/api/v1/nodes/$NODE_NAME/proxy/logs/messages" | grep -E "^E.*kubelet"

# Warnings and errors
kubectl get --raw "/api/v1/nodes/$NODE_NAME/proxy/logs/messages" | grep -E "^[EW].*kubelet"

# Time range (via journalctl on node)
journalctl -u kubelet --since "2024-01-01 00:00:00" --until "2024-01-01 12:00:00"
```

## Common Issues in Kubelet Logs

### Node Status Issues

| Issue | Log Pattern | Cause |
|-------|-------------|-------|
| Node Not Ready | `connection failures`, `certificate errors` | Kubelet fails to report status |
| Certificate Expired | `certificate validation failed` | TLS cert expiration |
| Auto-repair Failed | `node recovery` patterns | Multiple restart attempts |

### Connectivity Issues

| Issue | Log Pattern | Cause |
|-------|-------------|-------|
| API Server Unreachable | `connection refused` | Network policy blocking |
| Network Timeout | `timeout` | NSG rule violations |
| DNS Failure | `name resolution` | CoreDNS issues |

### Resource Issues

| Issue | Log Pattern | Cause |
|-------|-------------|-------|
| OOM | `evicted`, `memory pressure` | Memory saturation |
| Disk Pressure | `disk pressure` | Node disk full |
| CPU Throttling | `CPU consuming` | High CPU workloads |

### Pod Lifecycle Issues

| Issue | Log Pattern | Cause |
|-------|-------------|-------|
| Pod Eviction | `evicted` | Resource constraints |
| Container Start Failure | `failed to start container` | Image pull or runtime error |
| Volume Mount Failure | `mount failed` | Storage issues |

## Troubleshooting Workflow

### Step 1: Identify Issue Category

- Cluster creation failures
- Upgrade/scaling operations
- Node status problems
- Connectivity issues
- Performance degradation

### Step 2: Collect Logs

```bash
# Quick collection
kubectl get --raw "/api/v1/nodes/$NODE_NAME/proxy/logs/messages" | grep kubelet > kubelet-logs.txt

# Detailed collection (SSH)
journalctl -u kubelet -o cat > kubelet-detailed.txt
```

### Step 3: Analyze Patterns

```bash
# Search for errors
grep -E "^E" kubelet-logs.txt

# Search for specific issues
grep -i "certificate" kubelet-logs.txt
grep -i "connection refused" kubelet-logs.txt
grep -i "timeout" kubelet-logs.txt
grep -i "evicted" kubelet-logs.txt
```

### Step 4: Correlate with Events

```bash
# Get node events
kubectl get events --field-selector involvedObject.name=$NODE_NAME

# Describe node
kubectl describe node $NODE_NAME
```

## Key Diagnostic Patterns

### Error Patterns to Search

| Pattern | Meaning |
|---------|---------|
| `certificate` | Certificate-related issues |
| `connection refused` | Network connectivity problems |
| `not ready` | Node readiness issues |
| `evicted` | Pod eviction due to resources |
| `timeout` | Operation timeout issues |
| `failed to start` | Container start failures |
| `mount failed` | Volume mount issues |
| `image pull` | Image pull failures |

### Log Level Reference

| Level | Prefix | Description |
|-------|--------|-------------|
| Info | `I` | Normal operations |
| Warning | `W` | Potential issues |
| Error | `E` | Errors requiring attention |
| Fatal | `F` | Critical failures |

## Additional Tools

### AKS Diagnose and Solve Problems

- Automated self-diagnostic in Azure Portal
- No additional configuration needed
- Covers connectivity, best practices, cluster health

### AKS Periscope

- Detailed log collection tool
- Comprehensive node diagnostics
- Network connectivity checks

### Data Collection Methods

- Real-time system insights capture
- TCP dump from nodes
- TCP packet capture from pods
- Container dumps (Windows)

## Access Methods Comparison

| Method | Time | Detail | SSH | Best For |
|--------|------|--------|-----|----------|
| kubectl raw API | <1 min | Medium | No | Quick diagnostics |
| SSH + journalctl | 2-5 min | High | Yes | Deep investigation |
| Container Insights | 5+ min | Medium | No | Long-term monitoring |
| Portal Diagnostics | 2-3 min | Medium | No | Automated recommendations |

## Best Practices

1. **Start with kubectl raw API** for quick diagnostics
2. **Use SSH for deep investigation** when raw API is insufficient
3. **Enable Container Insights** for continuous log collection
4. **Set up log-based alerts** for critical patterns
5. **Correlate with Kubernetes events** for context
6. **Document common patterns** for your workloads
