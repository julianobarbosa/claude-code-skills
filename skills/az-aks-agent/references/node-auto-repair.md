# AKS Node Auto-Repair Reference

## Overview

AKS continuously monitors worker node health and automatically initiates repairs when nodes become unhealthy. This is a managed service with no additional configuration required.

## How It Works

### Health Monitoring

- AKS monitors worker node health continuously
- Works with Azure VM platform
- Repairs initiated by `aks-remediator` service account

### Detection Criteria

| Condition | Detection Time |
|-----------|----------------|
| Node reports `NotReady` | Consecutive checks within 10 minutes |
| Node fails to report status | No status for 10 minutes |

### Trigger Threshold

- Node must be unhealthy for **at least 5 minutes** before repair initiates

## Repair Process

### Repair Sequence (Progressive)

```
Reboot → Reimage → Redeploy (Linux only)
```

| Step | Action | Description |
|------|--------|-------------|
| 1 | Reboot | Restart the VM |
| 2 | Reimage | Reinstall OS from image |
| 3 | Redeploy | Provision new VM (Linux only) |

### Retry Logic

- Entire sequence retried **up to 3 times**
- **Total completion window**: Up to 1 hour

### Timeline Example

| Time | Action |
|------|--------|
| 0-10 min | Health checks detect unhealthy node |
| 10 min | Node marked as NotReady |
| 15 min | Reboot initiated (after 5-min grace) |
| ~60 min | Final deadline for all attempts |

## Conditions That Block Auto-Repair

### Shutdown Taints Present

```yaml
# Auto-repair does NOT occur if these taints exist:
node.cloudprovider.kubernetes.io/shutdown
ToBeDeletedByClusterAutoscaler
```

### Upgrade In Progress

```yaml
# Auto-repair blocked with these annotations:
cluster-autoscaler.kubernetes.io/scale-down-disabled: "true"
kubernetes.azure.com/azure-cluster-autoscaler-scale-down-disabled-reason: "upgrade"
```

### Other Blocking Conditions

- Network configuration errors preventing status reporting
- Node failed to initially register as healthy

## Monitoring Auto-Repair Events

### View Events

```bash
# Get all events
kubectl get events

# Watch auto-repair events
kubectl get events --field-selector source=aks-auto-repair --watch

# Events for specific node
kubectl get events --field-selector involvedObject.name=<node-name>
```

### Event Retention

- Local retention: **1 hour**
- Extended retention: Enable **Container Insights** (90+ days)

## Event Types

### Action Events

| Reason | Description |
|--------|-------------|
| `NodeRebootStart` | Reboot action initiating |
| `NodeRebootEnd` | Reboot action completed |
| `NodeReimageStart` | Reimage action initiating |
| `NodeReimageEnd` | Reimage action completed |
| `NodeRedeployStart` | Redeploy action initiating |
| `NodeRedeployEnd` | Redeploy action completed |

### Error Events

| Reason | Description |
|--------|-------------|
| `NodeRebootError` | Reboot action failed |
| `NodeReimageError` | Reimage action failed |
| `NodeRedeployError` | Redeploy action failed |

### Example Event Messages

```
# Start Event
Node auto-repair is initiating a reboot action due to NotReady status persisting for more than 5 minutes.

# End Event
Reboot action from node auto-repair is completed.

# Error Event
Node auto-repair reboot action failed due to an operation failure. See error details: [Error code]
```

## Manual Health Checks

```bash
# View node status
kubectl get nodes

# Describe specific node
kubectl describe node <node-name>

# Check node conditions
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.conditions[?(@.type=="Ready")].status}{"\n"}{end}'

# View node events
kubectl get events --field-selector involvedObject.name=<node-name>
```

## Diagnostic Script

```bash
#!/bin/bash
# check-node-health.sh

echo "=== Node Status ==="
kubectl get nodes

echo -e "\n=== NotReady Nodes ==="
kubectl get nodes | grep NotReady

echo -e "\n=== Node Conditions ==="
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.conditions[?(@.type=="Ready")].status}{"\t"}{.status.conditions[?(@.type=="Ready")].reason}{"\n"}{end}'

echo -e "\n=== Auto-Repair Events ==="
kubectl get events --field-selector source=aks-auto-repair --sort-by='.lastTimestamp'

echo -e "\n=== Recent Warning Events ==="
kubectl get events --field-selector type=Warning --sort-by='.lastTimestamp' | head -20
```

## Configuration

### No Direct Configuration Available

Node auto-repair is a managed service with:

- **Enabled by default**
- Fixed detection and retry logic
- Cannot be disabled
- Cannot be customized

### Recommendations

1. **Enable Container Insights** for extended event retention
2. **Monitor Events Regularly** for anomalies
3. **Manual Intervention** if issues persist after auto-repair
4. **Review Troubleshooting Docs** for persistent failures

## Integration with Other Features

### Cluster Autoscaler

- Auto-repair coordinates with cluster autoscaler
- Respects scale-down disabled annotations
- Handles autoscaler shutdown taints

### Node Pools

- Auto-repair applies to all node pools
- Works with both system and user pools
- Handles spot instance nodes

### Upgrade Operations

- Auto-repair paused during upgrades
- Resumes after upgrade completion
- Respects upgrade annotations

## Troubleshooting Persistent Issues

### Node Remains Unhealthy After Auto-Repair

1. Check kubelet logs
2. Review node events
3. Verify network connectivity
4. Check for resource exhaustion
5. Contact Azure support if needed

### Commands for Investigation

```bash
# Get kubelet logs
kubectl get --raw "/api/v1/nodes/<node>/proxy/logs/messages" | grep kubelet

# Check network connectivity
kubectl run nettest --image=busybox --rm -it --restart=Never -- wget -qO- kubernetes.default.svc.cluster.local

# Review node resources
kubectl describe node <node> | grep -A 10 "Allocated resources"
```

## Best Practices

1. **Enable Container Insights** for long-term event monitoring
2. **Set up alerts** for repeated auto-repair events
3. **Review events weekly** for patterns
4. **Document recurring issues** for trend analysis
5. **Plan capacity** to prevent resource-related failures
6. **Use multiple node pools** for workload isolation
