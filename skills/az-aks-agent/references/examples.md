# Azure AKS Agent Practical Examples

## Setup Examples

### Initial Setup for New Users

```bash
# Step 1: Verify Azure CLI version (must be 2.76+)
az version

# Step 2: Install the AKS Agent extension
az extension add --name aks-agent --debug

# Step 3: Login to Azure
az login

# Step 4: Set your subscription
az account set --subscription "My AKS Subscription"

# Step 5: Initialize LLM configuration
az aks agent-init

# Step 6: Get cluster credentials
az aks get-credentials \
  --resource-group cafehyna-rg \
  --name cafehyna-dev

# Step 7: Verify connection
kubectl get nodes

# Step 8: Start using the agent
az aks agent -g cafehyna-rg -n cafehyna-dev
```

### Setup with Azure OpenAI

```bash
# Set environment variables
export AZURE_API_KEY="your-api-key"
export AZURE_API_BASE="https://my-openai.openai.azure.com/"
export AZURE_API_VERSION="2025-04-01-preview"

# Or create config file
cat > ~/.azure/aksAgent.config << 'EOF'
llm_provider: azure
azure_api_base: https://my-openai.openai.azure.com/
azure_api_version: 2025-04-01-preview
model: gpt-4o
max_steps: 10
EOF

# Test the setup
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "What's the cluster health status?"
```

## Cluster Health Examples

### Daily Health Check

```bash
# Comprehensive cluster health check
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "Perform a comprehensive health check of my cluster including nodes, system pods, and resource utilization"

# Quick health summary
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "Give me a quick health summary"
```

### Node Health Analysis

```bash
# Check node status
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "Are all nodes healthy and ready? Check for any NotReady nodes or resource pressure"

# Node pool analysis
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "Analyze my node pools and their resource utilization"

# Spot node issues
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "Are there any issues with spot instance nodes?"
```

### Control Plane Health

```bash
# API server health
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "Check the health of the Kubernetes API server and control plane components"

# etcd health
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "What's the status of etcd? Any latency or storage issues?"
```

## Pod Troubleshooting Examples

### CrashLoopBackOff Investigation

```bash
# General CrashLoopBackOff diagnosis
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "I have pods in CrashLoopBackOff state. Identify them and explain why they're crashing"

# Namespace-specific
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "Why are pods crashing in the production namespace? Show logs and events"
```

### Pending Pods Analysis

```bash
# Find pending pods
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "Find all pending pods and explain why they can't be scheduled"

# Resource-related pending
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "Are there pods pending due to insufficient CPU or memory?"

# Node selector issues
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "Are there pods pending due to node selector or toleration mismatches?"
```

### OOMKilled Containers

```bash
# Find OOMKilled containers
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "Find containers that have been OOMKilled and analyze their memory patterns"

# Memory recommendations
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "Which deployments need memory limit adjustments based on OOMKilled events?"
```

### Image Pull Errors

```bash
# Image pull failures
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "Find pods with ImagePullBackOff and identify the cause"

# Registry access issues
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "Are there any container registry authentication issues?"
```

## Networking Examples

### Service Connectivity

```bash
# Service discovery issues
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "Debug why Service X cannot reach Service Y in the cluster"

# LoadBalancer issues
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "Why is my LoadBalancer service not getting an external IP?"

# Internal service DNS
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "Verify DNS resolution is working for cluster services"
```

### Network Policy Analysis

```bash
# Network policy audit
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "List all network policies and check if any are blocking expected traffic"

# Traffic flow analysis
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "Is traffic from namespace A allowed to reach namespace B?"
```

### Ingress Troubleshooting

```bash
# Ingress status
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "Check the status of all Ingress resources and their backends"

# Certificate issues
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "Are there any TLS certificate issues with my Ingresses?"

# Ingress controller health
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "Is the NGINX ingress controller healthy?"
```

## Storage Examples

### PVC Troubleshooting

```bash
# Pending PVCs
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "Find PersistentVolumeClaims stuck in Pending state and explain why"

# Storage class issues
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "Are there any issues with Azure Disk or Azure File storage classes?"

# Volume attachment
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "Check for pods stuck waiting for volume attachment"
```

### CSI Driver Issues

```bash
# CSI driver status
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "Check the health of CSI drivers in the cluster"

# Key Vault CSI
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "Are there issues with Azure Key Vault CSI driver secret mounts?"
```

## Security Examples

### RBAC Analysis

```bash
# RBAC audit
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "Review RBAC configuration for overly permissive roles"

# Service account analysis
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "Are there service accounts with cluster-admin privileges that shouldn't have them?"

# Missing permissions
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "Why is pod X getting Forbidden errors when accessing the API?"
```

### Pod Security

```bash
# Security context issues
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "Find pods running as root or with privileged containers"

# Pod Security Standards
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "Are there pods violating Pod Security Standards?"
```

### Secret Management

```bash
# Secret audit
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "Are there any secrets that are not being used or might be exposed?"

# Secret mounting issues
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "Check if secrets are properly mounted in pods"
```

## Performance Examples

### Resource Utilization

```bash
# Cluster resource usage
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "Show me cluster-wide CPU and memory utilization with recommendations"

# High resource consumers
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "Which pods are using the most CPU and memory?"

# Resource recommendations
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "Based on actual usage, suggest resource request and limit adjustments"
```

### Scaling Analysis

```bash
# HPA issues
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "Why is my HorizontalPodAutoscaler not scaling?"

# Cluster autoscaler
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "Is the cluster autoscaler working correctly? Are there pending pods that should trigger scale-up?"
```

## Application-Specific Examples

### Deployment Issues

```bash
# Deployment rollout status
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "Check the rollout status of all deployments and identify any stuck rollouts"

# Failed deployments
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "Why did the deployment of my-app fail?"

# Deployment recommendations
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "What improvements do you recommend for my deployment configurations?"
```

### StatefulSet Issues

```bash
# StatefulSet health
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "Check the health of StatefulSets and their ordered pod management"

# Database pods
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "Are my database StatefulSet pods healthy with proper PVC attachments?"
```

### Job/CronJob Issues

```bash
# Failed jobs
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "Find failed Jobs and CronJobs and explain why they failed"

# CronJob schedule issues
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "Are my CronJobs running on schedule? Any missed executions?"
```

## Events Analysis Examples

### Recent Cluster Events

```bash
# All recent events
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "Show me all Warning events in the last hour"

# Critical events
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "Are there any critical events that need immediate attention?"
```

### Node Events

```bash
# Node events
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "Show me node-related events including auto-repairs"

# Auto-repair analysis
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "Have there been any node auto-repair events recently? What triggered them?"
```

## Automation Examples

### Health Check Script

```bash
#!/bin/bash
# daily-health-check.sh
# Run daily cluster health check and save report

RESOURCE_GROUP="cafehyna-rg"
CLUSTER_NAME="cafehyna-dev"
REPORT_DIR="./health-reports"
DATE=$(date +%Y-%m-%d)

mkdir -p "$REPORT_DIR"

echo "Running daily health check for $CLUSTER_NAME..."

az aks agent \
  -g "$RESOURCE_GROUP" \
  -n "$CLUSTER_NAME" \
  --no-interactive \
  --query "Perform a comprehensive health check including:
    1. Node status and resource pressure
    2. System pod health
    3. Warning events in the last 24 hours
    4. Resource utilization trends
    5. Any pods in error states
    6. Network connectivity status
    Provide a summary with severity levels and recommended actions." \
  > "$REPORT_DIR/health-$DATE.txt"

echo "Report saved to $REPORT_DIR/health-$DATE.txt"
```

### Multi-Cluster Check

```bash
#!/bin/bash
# check-all-clusters.sh
# Check health across multiple clusters

RESOURCE_GROUP="cafehyna-rg"
CLUSTERS=("cafehyna-dev" "cafehyna-hub" "cafehyna-prd")

for cluster in "${CLUSTERS[@]}"; do
  echo ""
  echo "========================================"
  echo "Cluster: $cluster"
  echo "========================================"

  az aks get-credentials \
    --resource-group "$RESOURCE_GROUP" \
    --name "$cluster" \
    --overwrite-existing

  az aks agent \
    -g "$RESOURCE_GROUP" \
    -n "$cluster" \
    --no-interactive \
    --max-steps 5 \
    --query "Quick health status: any critical issues?"
done
```

### Incident Response Template

```bash
#!/bin/bash
# incident-response.sh
# Quick incident response diagnostic

RESOURCE_GROUP="${1:-cafehyna-rg}"
CLUSTER_NAME="${2:-cafehyna-dev}"
NAMESPACE="${3:-default}"

echo "Starting incident response diagnostic..."
echo "Cluster: $CLUSTER_NAME"
echo "Namespace: $NAMESPACE"
echo ""

# Get cluster credentials
az aks get-credentials \
  --resource-group "$RESOURCE_GROUP" \
  --name "$CLUSTER_NAME" \
  --overwrite-existing

# Run comprehensive diagnostic
az aks agent \
  -g "$RESOURCE_GROUP" \
  -n "$CLUSTER_NAME" \
  --show-tool-output \
  --query "INCIDENT RESPONSE for namespace $NAMESPACE:
    1. List all pods in error states with their events
    2. Check for recent Warning events
    3. Verify node health
    4. Check resource constraints
    5. Review recent deployments or changes
    6. Network connectivity status
    7. Service endpoint health
    Provide root cause analysis and immediate remediation steps."
```

## Interactive Session Examples

### Starting Interactive Session

```bash
# Start interactive session
az aks agent -g cafehyna-rg -n cafehyna-dev

# In the interactive session, you can ask follow-up questions:
# > What's wrong with my cluster?
# > Can you provide more details about the networking issue you mentioned?
# > How do I fix the pending pods?
# > Show me the relevant kubectl commands
```

### Guided Troubleshooting Flow

```bash
# Step 1: Start with broad question
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "What issues exist in my cluster?"

# Step 2: Dive deeper based on findings
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "Tell me more about the pod failures in production namespace"

# Step 3: Get remediation steps
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "How do I fix the OOMKilled pods you identified?"

# Step 4: Verify the fix
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "Verify that the memory limit changes I made are working"
```

## Best Practice Query Examples

### Proactive Queries

```bash
# Optimization recommendations
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "What optimizations do you recommend for my cluster?"

# Cost optimization
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "Are there opportunities to reduce costs through resource right-sizing?"

# Security hardening
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "What security improvements do you recommend?"
```

### Pre-Deployment Checks

```bash
# Readiness check
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "Is the cluster ready for a new deployment? Check capacity and health"

# Namespace preparation
az aks agent -g cafehyna-rg -n cafehyna-dev \
  --query "Check if namespace 'new-app' has proper resource quotas and network policies"
```
