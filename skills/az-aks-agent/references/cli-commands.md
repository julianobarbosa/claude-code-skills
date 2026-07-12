# Azure AKS Agent CLI Commands Reference

## Installation Commands

### Install Extension

```bash
# Standard installation
az extension add --name aks-agent

# Installation with debug output
az extension add --name aks-agent --debug

# Force upgrade existing installation
az extension add --name aks-agent --upgrade
```

### Verify Installation

```bash
# List installed extensions
az extension list

# Show extension details
az extension show --name aks-agent

# Get help
az aks agent --help
```

### Remove Extension

```bash
# Remove the extension
az extension remove --name aks-agent

# Remove with debug output
az extension remove --name aks-agent --debug
```

## Configuration Commands

### Initialize Configuration

```bash
# Interactive configuration wizard
az aks agent-init

# This wizard will:
# 1. Ask for LLM provider selection
# 2. Request API credentials
# 3. Save configuration to ~/.azure/aksAgent.config
```

### Configuration File Location

```bash
# Default location
~/.azure/aksAgent.config

# Specify custom config file
az aks agent --config-file /path/to/custom/config.yaml
```

## Core Agent Commands

### Basic Usage

```bash
# Interactive mode (default)
az aks agent -g <resource-group> -n <cluster-name>

# With specific query
az aks agent -g <resource-group> -n <cluster-name> \
  --query "What's wrong with my cluster?"

# Non-interactive mode
az aks agent -g <resource-group> -n <cluster-name> \
  --no-interactive \
  --query "Check cluster health"
```

### Complete Parameter Reference

```bash
az aks agent \
  --resource-group <resource-group>     # Required: Azure resource group
  --name <cluster-name>                 # Required: AKS cluster name
  --api-key <api-key>                   # Optional: LLM API key (overrides env/config)
  --config-file <path>                  # Optional: Custom config file path
  --max-steps <number>                  # Optional: Max investigation steps (default: 10)
  --model <model>                       # Optional: LLM model specification
  --no-interactive                      # Optional: Disable interactive mode
  --show-tool-output                    # Optional: Show tool execution output
  --refresh-toolsets                    # Optional: Refresh available toolsets
```

## Model Specifications

### Azure OpenAI Models

```bash
# GPT-4o (recommended)
az aks agent -g myRG -n myCluster --model "azure/gpt-4o"

# GPT-4o Mini
az aks agent -g myRG -n myCluster --model "azure/gpt-4o-mini"
```

### OpenAI Models

```bash
# GPT-4o
az aks agent -g myRG -n myCluster --model "gpt-4o"

# GPT-4o Mini
az aks agent -g myRG -n myCluster --model "gpt-4o-mini"
```

### Anthropic Models

```bash
# Claude Sonnet 4.0
az aks agent -g myRG -n myCluster --model "anthropic/claude-sonnet-4"

# Claude 3.5 Sonnet
az aks agent -g myRG -n myCluster --model "anthropic/claude-3-5-sonnet"
```

### Gemini Models

```bash
# Gemini Pro
az aks agent -g myRG -n myCluster --model "gemini/gemini-pro"
```

## Environment Variables

### API Keys

```bash
# Azure OpenAI
export AZURE_API_KEY="your-azure-openai-api-key"

# OpenAI
export OPENAI_API_KEY="your-openai-api-key"

# Anthropic
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# Gemini
export GEMINI_API_KEY="your-gemini-api-key"
```

### Azure OpenAI Specific

```bash
# API Base URL (required for Azure OpenAI)
export AZURE_API_BASE="https://your-endpoint.openai.azure.com/"

# API Version
export AZURE_API_VERSION="2025-04-01-preview"
```

## Related Azure CLI Commands

### AKS Cluster Management

```bash
# Get cluster credentials (required before using agent)
az aks get-credentials \
  --resource-group <resource-group> \
  --name <cluster-name> \
  --overwrite-existing

# List clusters
az aks list --resource-group <resource-group> -o table

# Show cluster details
az aks show --resource-group <resource-group> --name <cluster-name>

# Check cluster health
az aks show \
  --resource-group <resource-group> \
  --name <cluster-name> \
  --query "agentPoolProfiles[].{name:name,count:count,vmSize:vmSize,status:provisioningState}"
```

### Kubectl Commands for Events

```bash
# List all events
kubectl get events

# List events in specific namespace
kubectl get events -n <namespace>

# Watch events in real-time
kubectl get events --watch

# Watch auto-repair events
kubectl get events --field-selector=source=aks-auto-repair --watch

# Get events sorted by timestamp
kubectl get events --sort-by='.lastTimestamp'

# Get events for a specific pod
kubectl get events --field-selector involvedObject.name=<pod-name>

# Describe pod (includes events)
kubectl describe pod <pod-name> -n <namespace>
```

### Azure Monitor Integration

```bash
# Enable Container Insights
az aks enable-addons \
  --resource-group <resource-group> \
  --name <cluster-name> \
  --addons monitoring \
  --workspace-resource-id <log-analytics-workspace-id>

# Check monitoring addon status
az aks show \
  --resource-group <resource-group> \
  --name <cluster-name> \
  --query "addonProfiles.omsagent"
```

## Example Config Files

### Azure OpenAI Configuration

```yaml
# ~/.azure/aksAgent.config
llm_provider: azure
azure_api_base: https://my-openai.openai.azure.com/
azure_api_version: 2025-04-01-preview
azure_api_key: sk-xxxxxxxxxxxx
model: gpt-4o
max_steps: 10
```

### OpenAI Configuration

```yaml
# ~/.azure/aksAgent.config
llm_provider: openai
openai_api_key: sk-xxxxxxxxxxxx
model: gpt-4o
max_steps: 10
```

### Anthropic Configuration

```yaml
# ~/.azure/aksAgent.config
llm_provider: anthropic
anthropic_api_key: sk-ant-xxxxxxxxxxxx
model: claude-sonnet-4
max_steps: 10
```

## Batch Processing Examples

### Script for Multiple Clusters

```bash
#!/bin/bash
# check-all-clusters.sh

CLUSTERS=("cluster1" "cluster2" "cluster3")
RESOURCE_GROUP="my-resource-group"
QUERY="What's the overall health status?"

for cluster in "${CLUSTERS[@]}"; do
  echo "=== Checking $cluster ==="
  az aks agent \
    -g "$RESOURCE_GROUP" \
    -n "$cluster" \
    --no-interactive \
    --query "$QUERY"
  echo ""
done
```

### CI/CD Pipeline Integration

```yaml
# azure-pipelines.yml
steps:
  - task: AzureCLI@2
    inputs:
      azureSubscription: 'my-subscription'
      scriptType: 'bash'
      scriptLocation: 'inlineScript'
      inlineScript: |
        # Install extension
        az extension add --name aks-agent

        # Run health check
        az aks agent \
          -g $(RESOURCE_GROUP) \
          -n $(CLUSTER_NAME) \
          --no-interactive \
          --api-key $(AKS_AGENT_API_KEY) \
          --query "Are there any critical issues?"
```

## Output Formatting

### Show Tool Output

```bash
# Display what tools the agent is running
az aks agent -g myRG -n myCluster \
  --show-tool-output \
  --query "Check pod health"
```

### Verbose Mode

```bash
# Enable debug output
az aks agent -g myRG -n myCluster --debug

# Combined with tool output
az aks agent -g myRG -n myCluster \
  --debug \
  --show-tool-output
```

## Quick Reference Card

| Action | Command |
|--------|---------|
| Install | `az extension add --name aks-agent` |
| Configure | `az aks agent-init` |
| Interactive | `az aks agent -g RG -n CLUSTER` |
| Query | `az aks agent -g RG -n CLUSTER --query "..."` |
| Batch | `az aks agent -g RG -n CLUSTER --no-interactive --query "..."` |
| Debug | `az aks agent -g RG -n CLUSTER --debug` |
| Remove | `az extension remove --name aks-agent` |
