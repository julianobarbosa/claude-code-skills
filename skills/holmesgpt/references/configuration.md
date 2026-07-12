# HolmesGPT Configuration Reference

Complete configuration options for all deployment methods.

## Robusta Platform Integration

HolmesGPT is a core component of the [Robusta](https://robusta.dev) Kubernetes
observability platform. When deployed alongside Robusta, additional features
are available:

- **Automatic Alert Enrichment**: Robusta forwards alerts with full context
- **Unified Dashboard**: View investigations in Robusta UI
- **Playbook Integration**: Trigger HolmesGPT from Robusta automation playbooks
- **Bi-directional Sync**: Investigation results feed back into Robusta

### Standalone vs Robusta-Integrated

| Feature | Standalone | With Robusta |
|---------|-----------|--------------|
| Alert Investigation | Manual trigger | Automatic |
| UI Dashboard | None (CLI only) | Robusta UI |
| Alert Context | Basic | Enriched |
| Playbook Automation | No | Yes |

### Robusta Helm Values

```yaml
# In Robusta's values.yaml
enableHolmesGPT: true
holmes:
  additionalEnvVars:
    - name: ROBUSTA_ACCOUNT_ID
      valueFrom:
        secretKeyRef:
          name: robusta-secrets
          key: account-id
    - name: ROBUSTA_API_KEY
      valueFrom:
        secretKeyRef:
          name: robusta-secrets
          key: api-key

# HolmesGPT specific settings
holmesConfig:
  modelList:
    sonnet:
      api_key: "{{ env.ANTHROPIC_API_KEY }}"
      model: anthropic/claude-sonnet-4-20250514
      temperature: 0
```

### Enable Robusta Toolset (Standalone)

```yaml
# When running HolmesGPT standalone but connecting to Robusta
toolsets:
  robusta:
    enabled: true
env:
  - name: ROBUSTA_API_KEY
    valueFrom:
      secretKeyRef:
        name: holmesgpt-secrets
        key: robusta-api-key
```

## Environment Variables

### AI Provider Configuration

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key | For OpenAI |
| `ANTHROPIC_API_KEY` | Anthropic Claude API key | For Anthropic |
| `AZURE_API_KEY` | Azure OpenAI API key | For Azure |
| `AZURE_API_BASE` | Azure OpenAI endpoint URL | For Azure |
| `AZURE_API_VERSION` | Azure API version | For Azure |
| `AWS_ACCESS_KEY_ID` | AWS access key | For Bedrock |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key | For Bedrock |
| `AWS_DEFAULT_REGION` | AWS region (e.g., `us-east-1`) | For Bedrock |
| `GEMINI_API_KEY` | Google Gemini API key | For Gemini |
| `GOOGLE_API_KEY` | Alternative Google API key | For Google |
| `VERTEXAI_PROJECT` | Google Cloud project ID | For Vertex AI |
| `VERTEXAI_LOCATION` | Vertex AI location | For Vertex AI |
| `GOOGLE_APPLICATION_CREDENTIALS` | Service account JSON path | Vertex AI |

### HolmesGPT Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `HOLMES_CONFIG_PATH` | `~/.holmes/config.yaml` | Custom config file path |
| `HOLMES_LOG_LEVEL` | `INFO` | Log verbosity (DEBUG/INFO/WARN/ERROR) |
| `HOLMES_CACHE_DIR` | - | Directory for caching data |
| `HOLMES_POST_PROCESSING_PROMPT` | - | Custom post-processing template |
| `MODEL_LIST_FILE_LOCATION` | - | Path to model definitions YAML |

### Data Source Configuration

| Variable | Description |
|----------|-------------|
| `PROMETHEUS_URL` | Prometheus server URL |
| `GITHUB_TOKEN` | GitHub API access token |
| `DATADOG_API_KEY` | DataDog API key |
| `DATADOG_APP_KEY` | DataDog application key |
| `CONFLUENCE_BASE_URL` | Confluence instance URL |
| `CONFLUENCE_EMAIL` | Confluence user email |
| `CONFLUENCE_API_KEY` | Confluence API key |
| `MONGODB_ATLAS_PUBLIC_KEY` | MongoDB Atlas public key |
| `MONGODB_ATLAS_PRIVATE_KEY` | MongoDB Atlas private key |
| `SLAB_API_KEY` | Slab integration key |

### LLM Tool Calling

| Variable | Default | Description |
|----------|---------|-------------|
| `LLMS_WITH_STRICT_TOOL_CALLS` | `azure/gpt-4.1` | Strict tool calls |
| `TOOL_SCHEMA_NO_PARAM_OBJECT_IF_NO_PARAMS` | `false` | Gemini compat |

## Config File Structure

Location: `~/.holmes/config.yaml`

```yaml
# Default model to use
model: sonnet

# Model definitions (alternative to environment-based)
modelList:
  sonnet:
    api_key: "${ANTHROPIC_API_KEY}"
    model: anthropic/claude-sonnet-4-20250514
    temperature: 0
  gpt4:
    api_key: "${OPENAI_API_KEY}"
    model: openai/gpt-4.1
    temperature: 0.1

# Default toolsets to enable
toolsets:
  - kubernetes/core
  - kubernetes/logs
  - prometheus/metrics

# Custom toolset files
custom_toolsets:
  - ~/toolsets/my-custom-toolset.yaml

# Runbook directories
runbooks:
  - ~/runbooks/
  - /etc/holmes/runbooks/

# Logging
log_level: INFO

# Cache settings
cache_dir: ~/.holmes/cache

# Prometheus configuration
prometheus:
  url: http://prometheus:9090
  auth:
    username: admin
    password: "${PROMETHEUS_PASSWORD}"

# Slack integration
slack:
  token: "${SLACK_BOT_TOKEN}"
  default_channel: "#alerts"
```

## Helm Chart Configuration

### Complete values.yaml Reference

```yaml
# Image configuration
image:
  repository: robustadev/holmes
  tag: latest
  pullPolicy: IfNotPresent

# Registry (if using private registry)
registry: robustadev

# Replica count
replicaCount: 1

# Environment variables
env:
  - name: ANTHROPIC_API_KEY
    valueFrom:
      secretKeyRef:
        name: holmesgpt-secrets
        key: anthropic-api-key
  - name: PROMETHEUS_URL
    value: "http://prometheus-server.monitoring.svc.cluster.local"
  - name: HOLMES_LOG_LEVEL
    value: "INFO"

# Model configuration
modelList:
  sonnet:
    api_key: "{{ env.ANTHROPIC_API_KEY }}"
    model: anthropic/claude-sonnet-4-20250514
    temperature: 0
  gpt4:
    api_key: "{{ env.OPENAI_API_KEY }}"
    model: openai/gpt-4.1
    temperature: 0

# Toolset configuration
toolsets:
  kubernetes/core:
    enabled: true
  kubernetes/logs:
    enabled: true
  prometheus/metrics:
    enabled: true
  robusta:
    enabled: false
  internet:
    enabled: false
  github:
    enabled: false

# Custom MCP servers (Model Context Protocol)
mcpServers: {}

# Logging and telemetry
logLevel: INFO  # DEBUG, INFO, WARN, ERROR
enableTelemetry: false
sentryDSN: ""

# Post-processing
enablePostProcessing: false
postProcessingPrompt: ""

# Resource limits
resources:
  requests:
    cpu: 100m
    memory: 1024Mi
  limits:
    cpu: 500m
    memory: 2048Mi

# Service account configuration
createServiceAccount: true
customServiceAccountName: ""
customClusterRoleRules: []

# Image pull secrets
imagePullSecrets: []

# Scheduling
nodeSelector: {}
tolerations: []
affinity: {}
priorityClassName: ""

# OpenShift compatibility
openshift: false

# Additional volumes
additionalVolumes: []
additionalVolumeMounts: []

# Pod annotations
podAnnotations: {}

# Pod security context
podSecurityContext:
  runAsNonRoot: true
  runAsUser: 1000
  fsGroup: 1000

# Container security context
securityContext:
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities:
    drop:
      - ALL
```

## Model Configuration

### Model List YAML Format

```yaml
# model_list.yaml
modelList:
  # Anthropic models
  sonnet:
    api_key: "${ANTHROPIC_API_KEY}"
    model: anthropic/claude-sonnet-4-20250514
    temperature: 0
    max_tokens: 4096

  opus:
    api_key: "${ANTHROPIC_API_KEY}"
    model: anthropic/claude-opus-4-20250514
    temperature: 0

  # OpenAI models
  gpt4:
    api_key: "${OPENAI_API_KEY}"
    model: openai/gpt-4.1
    temperature: 0.1

  gpt4o:
    api_key: "${OPENAI_API_KEY}"
    model: openai/gpt-4o
    temperature: 0

  # Azure OpenAI
  azure-gpt4:
    api_key: "${AZURE_API_KEY}"
    model: azure/gpt-4-deployment
    api_base: "${AZURE_API_BASE}"
    api_version: "2024-02-15-preview"
    temperature: 0

  # AWS Bedrock
  bedrock-claude:
    model: bedrock/anthropic.claude-3-sonnet-20240229-v1:0
    aws_access_key_id: "${AWS_ACCESS_KEY_ID}"
    aws_secret_access_key: "${AWS_SECRET_ACCESS_KEY}"
    aws_region: "${AWS_DEFAULT_REGION}"
    temperature: 0

  # Google Gemini
  gemini:
    api_key: "${GEMINI_API_KEY}"
    model: gemini/gemini-1.5-pro
    temperature: 0

  # Ollama (local)
  ollama-llama:
    model: ollama/llama3.1:70b
    api_base: "http://localhost:11434"
    temperature: 0
```

Use with:

```bash
export MODEL_LIST_FILE_LOCATION="/path/to/model_list.yaml"
holmes ask "query" --model=sonnet
```

## Provider-Specific Features

### Anthropic (Claude)

**Prompt Caching**: Reduces costs by caching system prompts.

```yaml
modelList:
  sonnet:
    api_key: "${ANTHROPIC_API_KEY}"
    model: anthropic/claude-sonnet-4-20250514
    temperature: 0
    # Prompt caching is automatic for supported models
```

**Recommended Models:**

- `claude-sonnet-4-20250514` - Best balance of performance and cost
- `claude-opus-4-20250514` - Highest capability for complex analysis

### OpenAI

**Reasoning Effort Levels** (GPT-5 and O-series models):

```yaml
modelList:
  gpt5-high:
    api_key: "${OPENAI_API_KEY}"
    model: openai/gpt-5
    temperature: 0
    reasoning_effort: high  # Options: minimal, low, medium, high
```

**Reasoning Effort Options:**

| Level | Use Case |
|-------|----------|
| `minimal` | Simple queries, fast responses |
| `low` | Standard troubleshooting |
| `medium` | Complex analysis (default) |
| `high` | Deep investigation, multi-step reasoning |

### AWS Bedrock

**Extended Context Window** (up to 1M tokens):

```yaml
modelList:
  bedrock-claude-extended:
    model: bedrock/anthropic.claude-3-5-sonnet-20241022-v2:0
    aws_access_key_id: "${AWS_ACCESS_KEY_ID}"
    aws_secret_access_key: "${AWS_SECRET_ACCESS_KEY}"
    aws_region: "us-east-1"
    temperature: 0
    # Supports up to 1M token context window
```

**IAM Policy Required:**

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
    "Resource": "arn:aws:bedrock:*:*:foundation-model/*"
  }]
}
```

### Ollama (Local LLMs)

**Important Limitations:**

- Tool-calling support varies by model
- Recommended models with tool support: `llama3.1:70b`, `mistral`, `qwen2.5`
- Models without tool support will have degraded functionality

```yaml
modelList:
  ollama-local:
    model: ollama/llama3.1:70b
    api_base: "http://localhost:11434"
    temperature: 0

  # For Kubernetes deployment, use service DNS
  ollama-cluster:
    model: ollama/llama3.1:70b
    api_base: "http://ollama.ollama.svc.cluster.local:11434"
    temperature: 0
```

**Ollama Prerequisites:**

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model with tool support
ollama pull llama3.1:70b

# Verify it's running
curl http://localhost:11434/api/tags
```

### Google Gemini / Vertex AI

**Gemini Configuration:**

```yaml
modelList:
  gemini:
    api_key: "${GEMINI_API_KEY}"
    model: gemini/gemini-1.5-pro
    temperature: 0
```

**Important:** For Gemini compatibility, set:

```bash
export TOOL_SCHEMA_NO_PARAM_OBJECT_IF_NO_PARAMS=true
```

**Vertex AI Configuration:**

```yaml
modelList:
  vertex-gemini:
    model: vertex_ai/gemini-1.5-pro
    vertex_project: "${VERTEXAI_PROJECT}"
    vertex_location: "${VERTEXAI_LOCATION}"
    temperature: 0
```

**Vertex AI Prerequisites:**

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account.json"
export VERTEXAI_PROJECT="your-gcp-project"
export VERTEXAI_LOCATION="us-central1"
```

### Azure OpenAI

```yaml
modelList:
  azure-gpt4:
    api_key: "${AZURE_API_KEY}"
    model: azure/your-deployment-name
    api_base: "${AZURE_API_BASE}"
    api_version: "2024-02-15-preview"
    temperature: 0
```

**Environment Variables:**

```bash
export AZURE_API_KEY="your-azure-key"
export AZURE_API_BASE="https://your-resource.openai.azure.com"
export AZURE_API_VERSION="2024-02-15-preview"
```

## Custom Runbooks

### Runbook Format

```yaml
# runbooks/kubernetes-alerts.yaml
runbooks:
  - alert_name: "KubePodCrashLooping"
    instructions: |
      ## Investigation Steps
      1. Check pod logs: `kubectl logs <pod> --previous`
      2. Check pod events: `kubectl describe pod <pod>`
      3. Check resource limits and requests
      4. Look for OOMKilled events

      ## Common Causes
      - Application startup failures
      - Missing configuration/secrets
      - Resource exhaustion
      - Dependency unavailable

  - alert_name: "KubeDeploymentReplicasMismatch"
    instructions: |
      ## Investigation Steps
      1. Check deployment status: `kubectl get deployment <name>`
      2. Check ReplicaSet: `kubectl get rs`
      3. Check pending pods: `kubectl get pods | grep Pending`

      ## Common Causes
      - Insufficient cluster resources
      - Node affinity/taints preventing scheduling
      - PVC binding issues

  - alert_name: "HighMemoryUsage"
    instructions: |
      ## Investigation Steps
      1. Identify top memory consumers
      2. Check for memory leaks
      3. Review application heap settings

      ## Remediation
      - Increase memory limits
      - Restart affected pods
      - Scale horizontally
```

Use with:

```bash
holmes investigate alertmanager -r ~/runbooks/
# or in config.yaml
runbooks:
  - ~/runbooks/
```

## CLI Configuration Options

### Global Flags

| Flag | Description |
|------|-------------|
| `--model` | Select model from modelList |
| `--config` | Path to config file |
| `-t, --toolset` | Additional toolset file |
| `-r, --runbook` | Runbook file or directory |
| `--log-level` | Override log level |
| `--interactive` | Enable interactive mode |

### Ask Command Flags

| Flag | Description |
|------|-------------|
| `-f, --file` | Include file content in query |
| `--prompt-file` | Read prompt from file |
| `--destination` | Output destination (slack, etc.) |
| `--slack-token` | Slack bot token |
| `--slack-channel` | Target Slack channel |

### Investigate Command Flags

| Flag | Description |
|------|-------------|
| `--alertmanager-url` | AlertManager URL |
| `--pagerduty-api-key` | PagerDuty API key |
| `--opsgenie-api-key` | OpsGenie API key |
| `--jira-url` | Jira instance URL |
| `--update` | Write analysis back to source |

## Multi-Cluster Support

HolmesGPT can investigate multiple Kubernetes clusters from a single deployment.

### CLI: Multiple Contexts

```bash
# Specify kubeconfig context
holmes ask "check pods in production" --context prod-cluster

# Use different kubeconfig file
holmes ask "investigate alert" --kubeconfig ~/.kube/prod-config

# Environment variable
export KUBECONFIG=~/.kube/prod-config:~/.kube/staging-config
holmes ask "compare deployments across clusters"
```

### Helm: Multi-Cluster Configuration

```yaml
# Mount multiple kubeconfig files
additionalVolumes:
  - name: kubeconfigs
    secret:
      secretName: cluster-kubeconfigs

additionalVolumeMounts:
  - name: kubeconfigs
    mountPath: /etc/kubernetes/
    readOnly: true

env:
  - name: KUBECONFIG
    value: "/etc/kubernetes/prod.kubeconfig:/etc/kubernetes/staging.kubeconfig"
```

### Create Multi-Cluster Secret

```bash
# Combine kubeconfigs into single secret
kubectl create secret generic cluster-kubeconfigs \
  --namespace holmesgpt \
  --from-file=prod.kubeconfig=/path/to/prod-kubeconfig \
  --from-file=staging.kubeconfig=/path/to/staging-kubeconfig
```

### Hub-and-Spoke Pattern

For large deployments, use a central HolmesGPT instance that connects to
multiple clusters:

```yaml
# Central hub values.yaml
replicaCount: 2

# Service account with cross-cluster RBAC
createServiceAccount: true
customClusterRoleRules:
  - apiGroups: [""]
    resources: ["pods", "services", "events", "nodes"]
    verbs: ["get", "list", "watch"]

# Environment for each cluster
env:
  - name: PROD_CLUSTER_URL
    value: "https://prod-api.example.com"
  - name: STAGING_CLUSTER_URL
    value: "https://staging-api.example.com"
```

## Cost Optimization

AI API costs can accumulate quickly. Use these strategies to optimize spending.

### Model Selection Strategy

| Use Case | Recommended Model | Relative Cost | Notes |
|----------|------------------|---------------|-------|
| Simple status checks | GPT-4o-mini | $ | Fast, cheap |
| Standard investigation | Claude Sonnet 4 | $$ | Best balance |
| Complex root cause analysis | Claude Opus 4.5 | $$$ | Highest accuracy |
| Batch processing | GPT-4.1 | $$ | Good throughput |

### Configure Model Tiers

```yaml
modelList:
  # Cheap tier for simple queries
  fast:
    api_key: "${OPENAI_API_KEY}"
    model: openai/gpt-4o-mini
    temperature: 0

  # Standard tier for most investigations
  default:
    api_key: "${ANTHROPIC_API_KEY}"
    model: anthropic/claude-sonnet-4-20250514
    temperature: 0

  # Premium tier for complex analysis
  deep:
    api_key: "${ANTHROPIC_API_KEY}"
    model: anthropic/claude-opus-4-20250514
    temperature: 0
```

Usage:

```bash
holmes ask "list unhealthy pods" --model fast
holmes ask "investigate crash" --model default
holmes ask "deep root cause analysis" --model deep
```

### Reduce Token Usage

1. **Be Specific in Queries**

   ```bash
   # Bad: Explores entire cluster
   holmes ask "what's wrong?"

   # Good: Targeted, uses fewer tokens
   holmes ask "why is payment-service crashing in prod namespace?"
   ```

2. **Limit Toolsets**

   ```yaml
   # Only enable what you need
   toolsets:
     kubernetes/core:
       enabled: true
     kubernetes/logs:
       enabled: true
     # Disable unused toolsets
     internet:
       enabled: false
     confluence:
       enabled: false
   ```

3. **Use Prompt Caching (Anthropic)**

   Anthropic models automatically cache system prompts, reducing costs by
   up to 90% for repeated queries with the same context.

### Monitor Costs

```yaml
# Enable verbose logging to track token usage
env:
  - name: HOLMES_LOG_LEVEL
    value: "INFO"  # Logs include token counts
```

**Log output includes:**

```text
INFO: Query completed. Tokens used: input=1500, output=800, total=2300
INFO: Estimated cost: $0.023 (claude-sonnet-4)
```

### Budget Alerts

Set up alerts in your AI provider dashboard:

- **Anthropic**: Console → Usage → Set spending limit
- **OpenAI**: Settings → Billing → Usage limits
- **Azure**: Cost Management → Budgets

### Cost Estimation

| Provider | Model | Input (per 1M tokens) | Output (per 1M tokens) |
|----------|-------|----------------------|------------------------|
| Anthropic | Claude Sonnet 4 | $3.00 | $15.00 |
| Anthropic | Claude Opus 4.5 | $15.00 | $75.00 |
| OpenAI | GPT-4.1 | $2.00 | $8.00 |
| OpenAI | GPT-4o-mini | $0.15 | $0.60 |

*Prices as of early 2025. Check provider websites for current pricing.*
