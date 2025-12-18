# HolmesGPT Troubleshooting Guide

Common issues and solutions for HolmesGPT deployments.

## Common Issues

### 1. API Key Not Found

**Symptoms:**

- "API key not found" error
- Authentication failures
- Empty responses

**Solutions:**

```bash
# Verify environment variable is set
echo $ANTHROPIC_API_KEY
echo $OPENAI_API_KEY

# Set inline for testing
ANTHROPIC_API_KEY="sk-ant-..." holmes ask "test"

# Check in Kubernetes
kubectl get secret holmesgpt-secrets -n holmesgpt -o yaml

# Verify secret is mounted
kubectl exec -n holmesgpt deployment/holmesgpt-holmes -- env | grep API_KEY
```

### 2. Kubernetes Access Issues

**Symptoms:**

- "pods is forbidden" error
- Empty resource lists
- RBAC permission denied

**Solutions:**

```bash
# Check service account permissions
kubectl auth can-i get pods \
  --as=system:serviceaccount:holmesgpt:holmesgpt-holmes

kubectl auth can-i list events \
  --as=system:serviceaccount:holmesgpt:holmesgpt-holmes

# Verify ClusterRole
kubectl get clusterrole holmesgpt-holmes -o yaml

# Verify ClusterRoleBinding
kubectl get clusterrolebinding holmesgpt-holmes -o yaml

# Check if service account exists
kubectl get sa -n holmesgpt
```

**Fix RBAC:**

```yaml
# Add to Helm values
createServiceAccount: true
customClusterRoleRules:
  - apiGroups: [""]
    resources: ["pods", "pods/log", "services", "events", "nodes"]
    verbs: ["get", "list", "watch"]
  - apiGroups: ["apps"]
    resources: ["deployments", "replicasets", "statefulsets", "daemonsets"]
    verbs: ["get", "list", "watch"]
```

### 3. Data Truncation

**Symptoms:**

- Incomplete analysis
- Missing important information
- "Data truncated" warnings

**Solutions:**

```bash
# Be more specific in queries
# Bad:
holmes ask "what's happening in the cluster?"

# Good:
holmes ask "what pods are crashing in production namespace?"

# Use time ranges
holmes ask "show errors from the last hour in payment-service"

# Target specific components
holmes ask "analyze payment-service deployment in production"
```

**Configure output limits:**

```yaml
# In Helm values
env:
  - name: HOLMES_MAX_OUTPUT_LENGTH
    value: "50000"
```

### 4. Missing Data Access

**Symptoms:**

- "Cannot connect to Prometheus"
- Empty metrics
- Toolset connection failures

**Solutions:**

```bash
# Verify Prometheus connectivity
kubectl exec -n holmesgpt deployment/holmesgpt-holmes -- \
  curl -s http://prometheus-server.monitoring.svc.cluster.local/api/v1/query?query=up

# Check environment variables
kubectl exec -n holmesgpt deployment/holmesgpt-holmes -- env | grep PROMETHEUS

# Test from within cluster
kubectl run test-curl --rm -it --restart=Never --image=curlimages/curl -- \
  curl -s http://prometheus-server.monitoring.svc.cluster.local/api/v1/status/config
```

**Fix connectivity:**

```yaml
# In Helm values
env:
  - name: PROMETHEUS_URL
    value: "http://prometheus-server.monitoring.svc.cluster.local"
```

### 5. Model Limitations

**Symptoms:**

- Poor analysis quality
- Incorrect conclusions
- Slow responses

**Solutions:**

```bash
# Use better model
holmes ask "complex issue" --model opus

# Check available models
cat ~/.holmes/config.yaml

# Use recommended models
# Best: Claude Sonnet 4.0/4.5, Claude Opus
# Good: GPT-4.1, GPT-4o
# Basic: GPT-3.5 (not recommended for complex issues)
```

### 6. Ineffective Prompts

**Symptoms:**

- Generic or unhelpful responses
- AI asks for more information
- Irrelevant suggestions

**Solutions:**

```bash
# Bad queries:
holmes ask "why is my pod not working?"
holmes ask "what's wrong?"
holmes ask "check everything"

# Good queries:
holmes ask "why is payment-service pod restarting in production namespace?"
holmes ask "analyze CrashLoopBackOff for api-gateway deployment"
holmes ask "investigate high memory usage in monitoring namespace pods"
```

**Query improvement tips:**

- Include namespace
- Specify deployment/pod name
- Mention the specific symptom
- Provide time context if relevant

### 7. Helm Installation Failures

**Symptoms:**

- `helm install` errors
- Missing resources
- Configuration not applied

**Solutions:**

```bash
# Debug installation
helm install holmesgpt robusta/holmes -f values.yaml --debug --dry-run

# Check values syntax
helm lint robusta/holmes -f values.yaml

# Verify repo is updated
helm repo update

# Check for existing resources
kubectl get all -n holmesgpt

# Clean up failed installation
helm uninstall holmesgpt -n holmesgpt
kubectl delete namespace holmesgpt
```

### 8. Pod Not Starting

**Symptoms:**

- Pod stuck in Pending/CrashLoopBackOff
- ImagePullBackOff errors
- OOMKilled

**Solutions:**

```bash
# Check pod status
kubectl describe pod -n holmesgpt -l app.kubernetes.io/name=holmes

# Check events
kubectl get events -n holmesgpt --sort-by='.lastTimestamp'

# Check logs
kubectl logs -n holmesgpt deployment/holmesgpt-holmes --previous

# Check resources
kubectl top pod -n holmesgpt
```

**Common fixes:**

```yaml
# Increase resources
resources:
  requests:
    memory: "2048Mi"
    cpu: "200m"
  limits:
    memory: "4096Mi"

# Fix image pull
imagePullSecrets:
  - name: registry-credentials
```

### 9. Slow Responses

**Symptoms:**

- Queries take too long
- Timeouts
- Incomplete results

**Solutions:**

```bash
# Use faster model for simple queries
holmes ask "list pods" --model gpt4o

# Reduce scope
holmes ask "check payment-service only"

# Disable unnecessary toolsets
```

**Optimize configuration:**

```yaml
# Disable unused toolsets
toolsets:
  internet:
    enabled: false
  confluence:
    enabled: false

# Use faster models for routine checks
modelList:
  fast:
    model: openai/gpt-4o-mini
    temperature: 0
```

### 10. Interactive Mode Issues

**Symptoms:**

- Commands not recognized
- Context lost
- Cannot execute /run commands

**Solutions:**

```bash
# Ensure interactive mode is started
holmes ask "question" --interactive

# Clear corrupted context
/clear

# Check available commands
/help

# If /run doesn't work, verify shell access
# Some deployments restrict shell execution
```

## Diagnostic Commands

### Check HolmesGPT Status

```bash
# Pod status
kubectl get pods -n holmesgpt -o wide

# Pod logs
kubectl logs -n holmesgpt deployment/holmesgpt-holmes -f

# Pod events
kubectl describe pod -n holmesgpt -l app.kubernetes.io/name=holmes

# Resource usage
kubectl top pod -n holmesgpt
```

### Test Connectivity

```bash
# Test API endpoint (after port-forward)
kubectl port-forward -n holmesgpt svc/holmesgpt-holmes 8080:80 &
curl -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{"ask": "test", "model": "sonnet"}'

# Test from within cluster
kubectl run test-holmes --rm -it --restart=Never --image=curlimages/curl -- \
  curl -X POST http://holmesgpt-holmes.holmesgpt.svc.cluster.local/api/chat \
  -H "Content-Type: application/json" \
  -d '{"ask": "test", "model": "sonnet"}'
```

### Verify Configuration

```bash
# Check Helm values applied
helm get values holmesgpt -n holmesgpt

# Check configmaps
kubectl get configmap -n holmesgpt -o yaml

# Check secrets (without revealing values)
kubectl get secrets -n holmesgpt

# Check environment in pod
kubectl exec -n holmesgpt deployment/holmesgpt-holmes -- env | sort
```

## Getting Help

1. **Slack Community**: Cloud Native Slack #holmesgpt channel
2. **GitHub Issues**: <https://github.com/robusta-dev/holmesgpt/issues>
3. **Documentation**: <https://holmesgpt.dev/>
4. **DeepWiki AI Support**: Built-in support assistant

### Reporting Issues

Include in bug reports:

- HolmesGPT version
- Deployment method (CLI/Helm/Docker)
- AI provider and model
- Error messages and logs
- Steps to reproduce
- Expected vs actual behavior
