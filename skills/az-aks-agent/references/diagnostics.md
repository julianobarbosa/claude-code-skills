# AKS Diagnostics Reference

## Overview

AKS Diagnose and Solve Problems is an intelligent, self-diagnostic tool built into the Azure portal that helps identify and resolve cluster problems automatically with no extra configuration or billing cost.

## Access Methods

### Azure Portal (Primary)

1. Navigate to your AKS cluster in Azure Portal
2. From service menu, select **Diagnose and solve problems**
3. Select a troubleshooting category or use search
4. Review alerts and click **View details**
5. Follow remediation steps

### Azure CLI - AKS Agent (AI-Powered)

```bash
# Describe cluster status
az aks agent "describe cluster <cluster-name> in resource group <rg-name>"

# Ask diagnostic questions
az aks agent "What's wrong with my cluster?"
az aks agent "How is my cluster [name] in resource group [rg]?"
az aks agent "Diagnose connectivity issues in my cluster"
```

### AKS Periscope (Log Collection)

```bash
# Install prerequisite
az extension add --name aks-preview

# Collect diagnostic information
az aks kollect

# View options
az aks kollect -h
```

**Periscope Collects:**

- Container logs (kube-system namespace by default)
- Docker and Kubelet system service logs
- Network outbound connectivity checks
- Node IP Tables

## Diagnostic Categories

### 1. Cluster and Control Plane Availability

- Service availability checks
- Throttling issue detection
- Control plane health status
- ETCD database health

### 2. Connectivity Issues

- Cluster DNS resolution errors
- Outbound communication routes
- Network connectivity validation
- Service-to-service connectivity

### 3. Best Practices

- VM resource provisioning recommendations
- Cluster upgrade planning
- Scaling operations guidance
- Subnet configuration validation

### 4. Overview (All Diagnostics)

- Runs all diagnostics across categories
- Displays comprehensive issue summary

## Cluster Insight Test Categories

| Category | Description |
|----------|-------------|
| Node-Related Issues | Problems causing cluster misbehavior |
| CRUD Operations | Issues from create, read, update, delete ops |
| Authentication/Authorization | Communication errors due to auth issues |

## Available Metrics

### Control Plane Metrics

| Metric | Description |
|--------|-------------|
| API Server CPU % | API server CPU usage |
| API Server Memory % | API server memory usage |
| ETCD CPU % | etcd database CPU usage |
| ETCD Memory % | etcd database memory usage |
| Inflight Requests | Current API requests in flight |

### Node Metrics

| Metric | Description |
|--------|-------------|
| CPU (millicores) | CPU usage per node |
| Memory Working Set | Memory usage in bytes |
| Disk Usage | Disk utilization per device |
| Network In/Out | Network traffic bytes |

### Pod Metrics

| Metric | Description |
|--------|-------------|
| Pods by Phase | Count by Pending, Running, Failed |
| Pods Ready | Pods in ready state |
| Pod Distribution | Distribution by namespace |

### Cluster Autoscaler Metrics

| Metric | Description |
|--------|-------------|
| Cluster Health | Overall health status |
| Scale Down Cooldown | Cooldown state indicator |
| Unneeded Nodes | Count of unneeded nodes |
| Unschedulable Pods | Pods that can't be scheduled |

## Interpreting Results

### Report Structure

Each diagnostic report provides:

1. **Issue Summary** - High-level problem overview
2. **Error Details** - Specific findings
3. **Severity Level** - Impact indication
4. **Recommended Actions** - Resolution steps
5. **Documentation Links** - Microsoft Learn references
6. **Related Metrics** - Performance data
7. **Logging Data** - Detailed logs

### Metric Interpretation Guide

| Metric | Normal | Warning | Critical |
|--------|--------|---------|----------|
| API Server CPU % | < 50% | 50-80% | > 80% |
| API Server Memory % | < 70% | 70-85% | > 85% |
| ETCD CPU % | < 40% | 40-70% | > 70% |
| Pod Ready State | 100% | 90-99% | < 90% |
| Unschedulable Pods | 0 | 1-5 | > 5 |

## Diagnostic Settings CLI Commands

### Create Diagnostic Setting

```bash
az monitor diagnostic-settings create \
  --resource /subscriptions/{sub-id}/resourceGroups/{rg}/providers/Microsoft.ContainerService/managedClusters/{cluster} \
  --name {diagnostic-setting-name} \
  --logs '[{
    "category": "kube-apiserver",
    "enabled": true
  }]' \
  --workspace /subscriptions/{sub-id}/resourceGroups/{rg}/providers/microsoft.operationalinsights/workspaces/{workspace}
```

### Available Log Categories

```bash
# Control plane logs
kube-apiserver              # API server operations
kube-controller-manager     # Controller manager operations
kube-scheduler              # Scheduler operations
cloud-controller-manager    # Cloud controller operations

# Audit logs
kube-audit                  # All operations (including get/list)
kube-audit-admin            # Only modifying operations

# System logs
cluster-autoscaler          # Autoscaler operations
csi-azuredisk-controller    # Azure Disk CSI driver
csi-azurefile-controller    # Azure File CSI driver
karpenter-events            # Karpenter provisioner events
```

## Log Analytics Queries

### Query API Server Logs

```kusto
AKSControlPlane
| where TimeGenerated > ago(1h)
| where log_s contains "error"
```

### Query Audit Logs

```kusto
AKSAudit
| where TimeGenerated > ago(24h)
| where ObjectRef_user contains "pod"
```

### Query Warning Events

```kusto
KubeEvents
| where TimeGenerated > ago(1h)
| where Type == "Warning"
```

### Count Logs by Category

```kusto
AzureDiagnostics
| where ResourceType == "MANAGEDCLUSTERS"
| summarize count() by Category
```

## Best Practices

1. **Start Broad**: Use general queries like "What's wrong with my cluster?"
2. **Be Descriptive**: Provide context about observed symptoms
3. **Review Carefully**: Understand recommendations before implementing
4. **Complement with Monitoring**: Use alongside Azure Monitor
5. **Collect Logs**: Use AKS Periscope for detailed analysis
6. **Cost Optimization**: Disable kube-audit when not needed; use kube-audit-admin instead

## Additional Tools

- **AKS Periscope**: Comprehensive log collection
- **Resource Health**: Historical health status in Azure Portal
- **VS Code AKS Extension**: Native IDE diagnostics support
- **AKS Triage Practices Guide**: Troubleshooting methodology
