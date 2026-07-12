# Azure AKS Agent Troubleshooting Guide

## Installation Issues

### Extension Installation Fails

**Symptom:** `az extension add --name aks-agent` fails with an error.

**Diagnosis:**

```bash
# Check Azure CLI version
az version

# Version must be 2.76 or higher
```

**Solution:**

```bash
# Upgrade Azure CLI
az upgrade

# Or install specific version
# On macOS
brew upgrade azure-cli

# On Ubuntu/Debian
curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash

# Retry installation
az extension add --name aks-agent --debug
```

### Extension Already Installed Error

**Symptom:** Error indicates extension is already installed.

**Solution:**

```bash
# Remove existing extension
az extension remove --name aks-agent

# Reinstall
az extension add --name aks-agent
```

## Authentication Issues

### Not Logged In to Azure

**Symptom:** `Please run 'az login' to setup account.`

**Solution:**

```bash
# Interactive login
az login

# Or with device code (for remote sessions)
az login --use-device-code

# Or with service principal
az login --service-principal \
  -u <app-id> \
  -p <password> \
  --tenant <tenant-id>
```

### Wrong Subscription

**Symptom:** Cluster not found but exists in a different subscription.

**Diagnosis:**

```bash
# Check current subscription
az account show

# List all subscriptions
az account list -o table
```

**Solution:**

```bash
# Set correct subscription
az account set --subscription <subscription-id-or-name>

# Verify
az account show
```

### Cluster Credentials Not Found

**Symptom:** Unable to connect to the cluster.

**Solution:**

```bash
# Get cluster credentials
az aks get-credentials \
  --resource-group <resource-group> \
  --name <cluster-name> \
  --overwrite-existing

# Verify connection
kubectl get nodes
```

## LLM Configuration Issues

### API Key Not Set

**Symptom:** `Error: API key not found`

**Diagnosis:**

```bash
# Check environment variable
echo $AZURE_API_KEY    # For Azure OpenAI
echo $OPENAI_API_KEY   # For OpenAI
```

**Solution:**

```bash
# Set environment variable
export AZURE_API_KEY="your-api-key"

# Or run configuration wizard
az aks agent-init

# Or provide key directly
az aks agent -g myRG -n myCluster --api-key "your-key"
```

### Invalid API Base URL

**Symptom:** Connection errors when using Azure OpenAI.

**Cause:** Using AI Foundry URI instead of direct OpenAI endpoint.

**Solution:**

```bash
# Correct format (direct OpenAI endpoint)
export AZURE_API_BASE="https://your-resource.openai.azure.com/"

# Incorrect format (AI Foundry - will not work)
# export AZURE_API_BASE="https://your-aiservices.azure.com/"
```

### Invalid API Version

**Symptom:** API version not supported error.

**Solution:**

```bash
# Use a supported API version
export AZURE_API_VERSION="2025-04-01-preview"

# Or update in config file
# ~/.azure/aksAgent.config
# azure_api_version: 2025-04-01-preview
```

### Model Not Found

**Symptom:** Model deployment not found.

**Cause:** Deployment name doesn't match model name.

**Solution:**

```bash
# Verify deployment exists in Azure OpenAI Studio
# Deployment name should match model name (e.g., "gpt-4o")

# List deployments
az cognitiveservices account deployment list \
  --name <openai-resource-name> \
  --resource-group <resource-group> \
  -o table
```

## Performance Issues

### Slow Response Times

**Symptom:** Agent takes a long time to respond.

**Causes:**

1. Insufficient TPM (Tokens Per Minute) quota
2. High cluster complexity
3. Network latency

**Solutions:**

```bash
# Check current TPM in Azure Portal or:
az cognitiveservices account deployment show \
  --name <openai-resource-name> \
  --resource-group <resource-group> \
  --deployment-name <deployment-name>

# Increase TPM quota (minimum recommended: 1,000,000)
# Done via Azure Portal: Azure OpenAI > Resource > Deployments > Edit

# Reduce max steps for faster (but less thorough) analysis
az aks agent -g myRG -n myCluster --max-steps 5
```

### Rate Limiting Errors

**Symptom:** `429 Too Many Requests` errors.

**Solution:**

```bash
# 1. Increase TPM quota (Azure Portal)

# 2. Reduce request frequency

# 3. Use a different model with higher quota
az aks agent -g myRG -n myCluster --model "azure/gpt-4o-mini"
```

### Context Window Exceeded

**Symptom:** Errors about context length or token limits.

**Cause:** Cluster data exceeds model's context window.

**Solution:**

```bash
# Use a model with larger context window
# gpt-4o supports 128,000+ tokens

# Reduce max steps to limit data collection
az aks agent -g myRG -n myCluster --max-steps 5

# Focus query on specific namespace/resource
az aks agent -g myRG -n myCluster \
  --query "Check pods in the production namespace only"
```

## Cluster Access Issues

### Insufficient RBAC Permissions

**Symptom:** Forbidden errors when querying cluster resources.

**Diagnosis:**

```bash
# Check current user's permissions
kubectl auth can-i --list

# Check specific permission
kubectl auth can-i get pods -n kube-system
```

**Solution:**

```bash
# Request cluster-admin role (or appropriate permissions)
# Contact cluster administrator

# Or use admin credentials
az aks get-credentials \
  --resource-group <resource-group> \
  --name <cluster-name> \
  --admin
```

### Network Connectivity Issues

**Symptom:** Cannot connect to API server.

**Diagnosis:**

```bash
# Test kubectl connectivity
kubectl cluster-info

# Check network
nc -zv <api-server-fqdn> 443
```

**Solution:**

```bash
# If using private cluster, ensure VPN/ExpressRoute connection

# If behind proxy
export HTTPS_PROXY=http://proxy:8080
export NO_PROXY=<api-server-fqdn>

# Refresh credentials
az aks get-credentials \
  --resource-group <resource-group> \
  --name <cluster-name> \
  --overwrite-existing
```

## Common AKS Events Issues

### Events Not Showing

**Symptom:** `kubectl get events` returns no results.

**Cause:** Events expire after 1 hour by default.

**Solution:**

```bash
# Enable Container Insights for long-term storage
az aks enable-addons \
  --resource-group <resource-group> \
  --name <cluster-name> \
  --addons monitoring \
  --workspace-resource-id <workspace-id>

# Query historical events via Azure Monitor
```

### Missing Auto-Repair Events

**Symptom:** No events from `aks-auto-repair` source.

**Diagnosis:**

```bash
# Check if auto-repair is enabled
az aks show \
  --resource-group <resource-group> \
  --name <cluster-name> \
  --query "agentPoolProfiles[].enableAutoScaling"
```

**Solution:**

```bash
# Enable auto-repair (enabled by default in newer clusters)
# Events are automatically emitted when repairs occur

# Watch for events
kubectl get events --field-selector=source=aks-auto-repair --watch
```

## Diagnostic Commands

### Full System Check

```bash
#!/bin/bash
# diagnostics.sh - Run full AKS Agent diagnostics

echo "=== Azure CLI Version ==="
az version

echo -e "\n=== Logged In Account ==="
az account show

echo -e "\n=== Extension Status ==="
az extension list | grep aks-agent

echo -e "\n=== Environment Variables ==="
echo "AZURE_API_KEY: ${AZURE_API_KEY:+SET (hidden)}"
echo "OPENAI_API_KEY: ${OPENAI_API_KEY:+SET (hidden)}"
echo "AZURE_API_BASE: $AZURE_API_BASE"

echo -e "\n=== Kubectl Context ==="
kubectl config current-context

echo -e "\n=== Cluster Connection ==="
kubectl cluster-info

echo -e "\n=== Node Status ==="
kubectl get nodes

echo -e "\n=== Config File ==="
cat ~/.azure/aksAgent.config 2>/dev/null || echo "No config file found"
```

### Test LLM Connection

```bash
# Simple query to test LLM connectivity
az aks agent -g myRG -n myCluster \
  --query "Say hello" \
  --max-steps 1 \
  --debug
```

### Verbose Debugging

```bash
# Enable all debug output
az aks agent -g myRG -n myCluster \
  --debug \
  --show-tool-output \
  --query "Check cluster health"
```

## Error Message Reference

| Error | Cause | Solution |
|-------|-------|----------|
| `Please run 'az login'` | Not authenticated | Run `az login` |
| `Subscription not found` | Wrong subscription | `az account set -s <sub-id>` |
| `API key not found` | Missing API key | Set env var or run `az aks agent-init` |
| `Model not found` | Wrong deployment name | Match deployment to model name |
| `429 Too Many Requests` | Rate limiting | Increase TPM quota |
| `Context length exceeded` | Too much data | Reduce `--max-steps` |
| `Forbidden` | RBAC issues | Request appropriate permissions |
| `Connection refused` | Network issues | Check VPN/firewall |

## Getting Help

### Official Resources

- [AKS Agent Troubleshooting Guide](https://learn.microsoft.com/en-us/azure/aks/cli-agent-for-aks-troubleshoot)
- [AKS Agent FAQ](https://learn.microsoft.com/en-us/azure/aks/cli-agent-for-aks-faq)
- [GitHub Issues](https://github.com/Azure/agentic-cli-for-aks/issues)

### Support Channels

```bash
# Check AKS support policies
az aks show \
  --resource-group <resource-group> \
  --name <cluster-name> \
  --query "sku.tier"

# Note: AKS Agent is in preview and may have limited support
```
