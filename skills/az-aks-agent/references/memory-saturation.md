# AKS Memory Saturation Troubleshooting

## Overview

Memory saturation occurs when applications or processes need more memory than the container host can provide, or when the host exhausts available memory.

## Identification Methods

### Method 1: Container Insights (Azure Portal)

1. Navigate to **Kubernetes services** → Select cluster
2. Go to **Monitoring** → **Insights**
3. Select **Nodes** tab
4. Choose metric: **Memory working set (computed from Allocatable)**
5. Set percentiles to **Max**
6. Sort by **Max %** column

### Method 2: kubectl top

```bash
# Node memory usage
kubectl top node

# Example output
NAME                                STATUS   CPU(cores)   MEMORY(bytes)   MEMORY%
aks-agentpool-12345678-vmss000000   Ready    250m         4500Mi          69%
aks-agentpool-12345678-vmss000001   Ready    180m         3000Mi          46%
```

### Method 3: Inspektor Gadget (Advanced)

```bash
# Top 10 memory-consuming processes cluster-wide
kubectl gadget run top_process --sort -memoryRelative --max-entries 10

# By specific node
kubectl gadget run top_process --sort -memoryRelative --filter k8s.node==<node-name>

# By namespace
kubectl gadget run top_process --sort -memoryRelative --filter k8s.namespace==<namespace>

# By pod
kubectl gadget run top_process --sort -memoryRelative --filter k8s.podName==<pod-name>
```

## Symptoms and Indicators

| Indicator | Description | Impact |
|-----------|-------------|--------|
| **Unschedulable Pods** | New pods cannot be scheduled | Workloads pending |
| **Pod Eviction** | Kubelet evicts pods | Application disruption |
| **Node Not Ready** | Kubelet/containerd unresponsive | Node failure |
| **OOM Kill** | Processes forcefully terminated | Container crashes |

### Symptom Progression

```
Memory Pressure → Pod Eviction → Node Not Ready → OOM Kill
```

## Diagnostic Commands

### Basic Diagnostics

```bash
# Node memory usage
kubectl top node

# Describe node (shows allocatable resources)
kubectl describe node <node-name>

# Node conditions
kubectl get nodes -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.status.conditions[?(@.type=="MemoryPressure")].status}{"\n"}{end}'
```

### Detailed Pod Memory Analysis

```bash
# Pod memory usage on specific node
kubectl get pods --all-namespaces --output wide \
    | grep <node-name> \
    | awk '{print $1" "$2}' \
    | xargs -n2 kubectl top pods --namespace \
    | awk 'NR==1 || NR%2==0' \
    | sort -k3n \
    | column -t
```

### Memory Events

```bash
# OOMKilled events
kubectl get events --all-namespaces --field-selector reason=OOMKilling

# Memory pressure events
kubectl get events --all-namespaces | grep -i memory
```

## Resolution Steps

### Step 1: Implement Memory Requests and Limits

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: app
spec:
  containers:
  - name: app
    image: myapp:latest
    resources:
      requests:
        memory: "180Mi"      # Close to actual usage
      limits:
        memory: "300Mi"      # Prevent overcommitting
```

**Guidelines:**

- Set `requests` close to actual usage
- Set `limits` slightly higher as buffer
- Monitor actual usage to tune values

### Step 2: Enable Horizontal Pod Autoscaler

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: app
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 70
```

### Step 3: Apply Pod Anti-Affinity

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: high-memory-app
spec:
  template:
    spec:
      affinity:
        podAntiAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
          - labelSelector:
              matchExpressions:
              - key: app
                operator: In
                values:
                - high-memory-app
            topologyKey: kubernetes.io/hostname
```

### Step 4: Scale Up VM SKUs

```bash
# Create new node pool with higher memory VMs
az aks nodepool add \
  --resource-group <rg> \
  --cluster-name <cluster> \
  --name highmempool \
  --node-count 3 \
  --node-vm-size Standard_E8s_v3

# Cordon existing nodes
kubectl cordon <old-node>

# Drain workloads
kubectl drain <old-node> --ignore-daemonsets --delete-emptydir-data

# Delete old node pool
az aks nodepool delete \
  --resource-group <rg> \
  --cluster-name <cluster> \
  --name oldpool
```

### Step 5: Separate Workload Types

```yaml
# Dedicate node pool for applications
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      nodeSelector:
        agentpool: userpool
      tolerations:
      - key: "workload"
        operator: "Equal"
        value: "user"
        effect: "NoSchedule"
```

## Prevention Strategies

| Strategy | Implementation | Benefit |
|----------|----------------|---------|
| Right-sized Requests/Limits | Set memory request close to actual, limit slightly higher | Prevents overcommit |
| HPA | Deploy HorizontalPodAutoscaler | Distributes load |
| Pod Anti-Affinity | Spread high-memory pods | Prevents hotspots |
| Higher SKU VMs | Use VMs with more RAM | More headroom |
| Workload Isolation | Separate user and system pools | Stability |
| Continuous Monitoring | Track memory against allocatable | Early detection |

## Resource Quota for Namespaces

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: mem-quota
  namespace: production
spec:
  hard:
    requests.memory: "10Gi"
    limits.memory: "20Gi"
```

## Limit Range for Defaults

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: mem-limit-range
  namespace: production
spec:
  limits:
  - default:
      memory: "512Mi"
    defaultRequest:
      memory: "256Mi"
    type: Container
```

## Monitoring Queries

### Log Analytics - OOMKilled Containers

```kusto
KubeEvents
| where Reason == "OOMKilling"
| project TimeGenerated, Namespace, Name, Message
| order by TimeGenerated desc
```

### Memory Working Set by Node

```kusto
InsightsMetrics
| where Name == "node_memory_working_set_percentage"
| summarize avg(Val) by Computer, bin(TimeGenerated, 5m)
| render timechart
```

### Memory Saturation Alert Query

```kusto
InsightsMetrics
| where Name == "node_memory_working_set_percentage"
| summarize MaxMemory = max(Val) by Computer
| where MaxMemory > 90
```

## Critical Metrics to Monitor

| Metric | Description | Threshold |
|--------|-------------|-----------|
| Memory Working Set % | Allocatable percentage | Alert > 80% |
| Memory Requests vs Limits | Configuration ratio | Limits should be > requests |
| Actual Memory Usage | Per pod/node | Compare to limits |
| Node Allocatable | Available resources | Track remaining capacity |

## Best Practices Summary

1. **Set appropriate requests/limits** for all containers
2. **Monitor memory working set** against allocatable (not total)
3. **Use HPA** to scale horizontally before vertical
4. **Implement resource quotas** per namespace
5. **Use node pools** to separate workload types
6. **Set up alerts** for memory pressure conditions
7. **Regular capacity planning** based on actual usage
