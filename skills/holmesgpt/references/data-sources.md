# HolmesGPT Data Sources & Toolsets

Complete reference for built-in and custom data source integrations.

## Built-in Toolsets Overview

HolmesGPT includes 30+ pre-built integrations organized by category.

### Kubernetes & Cloud Infrastructure

| Toolset | Description | Configuration |
|---------|-------------|---------------|
| `kubernetes/core` | Core K8s resources (pods, deploys, svcs) | kubeconfig |
| `kubernetes/logs` | Pod and container logs | Uses kubeconfig |
| `aks` | Azure Kubernetes Service node health | Azure credentials |
| `openshift` | OpenShift-specific resources | OpenShift CLI |
| `docker` | Docker container inspection | Docker socket |

### Monitoring & Observability

| Toolset | Description | Configuration |
|---------|-------------|---------------|
| `prometheus/metrics` | Prometheus metrics queries | `PROMETHEUS_URL` |
| `grafana` | Grafana dashboards | Grafana API |
| `loki` | Grafana Loki log queries | Loki URL |
| `tempo` | Grafana Tempo traces | Tempo URL |
| `datadog` | DataDog metrics and logs | `DATADOG_API_KEY`, `DATADOG_APP_KEY` |
| `newrelic` | New Relic monitoring | New Relic API |
| `coralogix` | Coralogix logs | Coralogix API |
| `opensearch` | OpenSearch logs and status | OpenSearch URL |

### Prometheus Integration Details

HolmesGPT can query Prometheus metrics to diagnose performance issues.

**Enable Prometheus Toolset:**

```yaml
toolsets:
  prometheus/metrics:
    enabled: true

env:
  - name: PROMETHEUS_URL
    value: "http://prometheus-server.monitoring.svc.cluster.local"
  # Optional: For authenticated Prometheus
  - name: PROMETHEUS_USERNAME
    valueFrom:
      secretKeyRef:
        name: holmesgpt-secrets
        key: prometheus-username
  - name: PROMETHEUS_PASSWORD
    valueFrom:
      secretKeyRef:
        name: holmesgpt-secrets
        key: prometheus-password
```

**Example Prometheus Queries:**

HolmesGPT translates natural language to PromQL automatically:

```bash
# Memory analysis
holmes ask "show memory usage trend for payment-service over last hour"
# Uses: rate(container_memory_usage_bytes{pod=~"payment.*"}[1h])

# CPU throttling detection
holmes ask "which pods have the highest CPU throttling?"
# Uses: rate(container_cpu_cfs_throttled_seconds_total[5m])

# Error rate analysis
holmes ask "what's the error rate for api-gateway?"
# Uses: rate(http_requests_total{status=~"5.."}[5m])

# Resource saturation
holmes ask "are any nodes running low on resources?"
# Uses: node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes

# Pod restarts
holmes ask "which pods have restarted most in the last 24 hours?"
# Uses: increase(kube_pod_container_status_restarts_total[24h])
```

**Prometheus-Specific Runbook:**

```yaml
runbooks:
  - alert_name: "HighMemoryUsage"
    instructions: |
      ## Prometheus Queries to Run
      1. Current usage: `container_memory_usage_bytes{pod="<pod>"}`
      2. Usage trend: `rate(container_memory_usage_bytes{pod="<pod>"}[1h])`
      3. Limit comparison: `container_memory_usage_bytes / container_spec_memory_limit_bytes`

      ## Thresholds
      - Warning: > 80% of limit
      - Critical: > 90% of limit

  - alert_name: "HighLatency"
    instructions: |
      ## Prometheus Queries to Run
      1. P99 latency: `histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m]))`
      2. Request rate: `rate(http_requests_total[5m])`
      3. Error rate: `rate(http_requests_total{status=~"5.."}[5m])`
```

### Grafana Loki Integration

```yaml
toolsets:
  loki:
    enabled: true

env:
  - name: LOKI_URL
    value: "http://loki.monitoring.svc.cluster.local:3100"
```

**Example Loki Queries:**

```bash
# Search for errors
holmes ask "show errors from payment-service in the last 30 minutes"

# Analyze log patterns
holmes ask "what are the most common error messages in production?"

# Correlate with events
holmes ask "show logs around the time of the last pod restart"
```

### Data & Messaging

| Toolset | Description | Configuration |
|---------|-------------|---------------|
| `kafka` | Kafka cluster health | Kafka connection |
| `rabbitmq` | RabbitMQ queue status | RabbitMQ API |
| `mongodb-atlas` | MongoDB Atlas metrics | `MONGODB_ATLAS_*` keys |
| `azure-sql` | Azure SQL Database | Azure credentials |

### Infrastructure & DevOps

| Toolset | Description | Configuration |
|---------|-------------|---------------|
| `argocd` | ArgoCD application status | ArgoCD API |
| `helm` | Helm release information | Helm CLI |
| `cilium` | Cilium network policies | Cilium CLI |
| `aws` | AWS resource inspection (via MCP) | AWS credentials |

### ArgoCD Integration Details

HolmesGPT can investigate ArgoCD sync failures and application health issues.

**Enable ArgoCD Toolset:**

```yaml
toolsets:
  argocd:
    enabled: true

env:
  - name: ARGOCD_SERVER
    value: "argocd-server.argocd.svc.cluster.local"
  - name: ARGOCD_AUTH_TOKEN
    valueFrom:
      secretKeyRef:
        name: holmesgpt-secrets
        key: argocd-token
```

**Create ArgoCD Token:**

```bash
# Generate token for HolmesGPT service account
argocd account generate-token --account holmesgpt --id holmesgpt-token

# Store in secret
kubectl create secret generic holmesgpt-secrets \
  --namespace holmesgpt \
  --from-literal=argocd-token="<generated-token>"
```

**Example ArgoCD Queries:**

```bash
# Investigate sync failures
holmes ask "why is application payment-service out of sync?"

# Check application health
holmes ask "what ArgoCD applications are degraded?"

# Analyze sync history
holmes ask "show recent sync failures for production apps"

# Investigate specific error
holmes ask "analyze ArgoCD sync error: ComparisonError for deployment/api"
```

**ArgoCD-Specific Runbook:**

```yaml
runbooks:
  - alert_name: "ArgoCDAppOutOfSync"
    instructions: |
      ## Investigation Steps
      1. Check app sync status: `argocd app get <app-name>`
      2. Review sync history: `argocd app history <app-name>`
      3. Check for resource conflicts
      4. Verify Git repository accessibility

      ## Common Causes
      - Manual changes to cluster resources
      - Git repository access issues
      - Resource conflicts with other controllers
      - Invalid manifests in Git
```

### Documentation & Collaboration

| Toolset | Description | Configuration |
|---------|-------------|---------------|
| `confluence` | Confluence wiki search | `CONFLUENCE_*` vars |
| `notion` | Notion database queries | Notion API |
| `servicenow` | ServiceNow incidents | ServiceNow API |
| `slab` | Slab documentation | `SLAB_API_KEY` |
| `github` | GitHub issues and PRs | `GITHUB_TOKEN` |

### Utilities

| Toolset | Description | Configuration |
|---------|-------------|---------------|
| `internet` | Web search capabilities | None |
| `datetime` | Date/time utilities | None |
| `bash` | Shell command execution | None (caution) |
| `robusta` | Robusta platform integration | Robusta API |

## Enabling Toolsets

### CLI Usage

```bash
# Use default toolsets
holmes ask "what pods are crashing?"

# Add custom toolset
holmes ask "query" -t /path/to/custom-toolset.yaml

# Multiple toolsets
holmes ask "query" -t toolset1.yaml -t toolset2.yaml
```

### Helm Configuration

```yaml
toolsets:
  # Kubernetes (recommended baseline)
  kubernetes/core:
    enabled: true
  kubernetes/logs:
    enabled: true

  # Monitoring
  prometheus/metrics:
    enabled: true
  grafana:
    enabled: false
  loki:
    enabled: false

  # DevOps tools
  argocd:
    enabled: true
  helm:
    enabled: true

  # Documentation
  confluence:
    enabled: false
  github:
    enabled: false

  # Utilities
  internet:
    enabled: false  # Disable for security
  bash:
    enabled: false  # Disable for security
```

### Config File

```yaml
# ~/.holmes/config.yaml
toolsets:
  - kubernetes/core
  - kubernetes/logs
  - prometheus/metrics
  - argocd

custom_toolsets:
  - ~/toolsets/my-custom.yaml
```

## Custom Toolset Development

### Basic Structure

```yaml
# custom-toolset.yaml
toolsets:
  my-toolset:
    description: "Description for the LLM"
    prerequisites: "Required tools/access"
    tags:
      - kubernetes
      - monitoring
    installation: |
      Instructions for setup
    tools:
      - name: tool_name
        description: "What this tool does"
        command: |
          command to execute
        parameters:
          - name: param_name
            description: "Parameter description"
            required: true
        additionalInstructions: |
          How to interpret output
```

### Variable Types

#### LLM-Inferred Variables (double braces)

```yaml
command: |
  kubectl get pods -n {{ namespace }} -l app={{ app_name }}
```

The LLM will determine appropriate values based on context.

#### Environment Variables (single braces with $)

```yaml
command: |
  curl -H "Authorization: Bearer ${API_TOKEN}" ${API_URL}/endpoint
```

Hidden from LLM, sourced from environment.

### Example: Custom Grafana Toolset

```yaml
toolsets:
  grafana-custom:
    description: "Query Grafana dashboards and panels"
    prerequisites: "Grafana API access"
    tags:
      - monitoring
      - grafana
    tools:
      - name: list_dashboards
        description: "List all Grafana dashboards"
        command: |
          curl -s -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
            "${GRAFANA_URL}/api/search?type=dash-db" | jq '.[] | {uid, title}'

      - name: get_dashboard
        description: "Get a specific dashboard by UID"
        command: |
          curl -s -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
            "${GRAFANA_URL}/api/dashboards/uid/{{ dashboard_uid }}" | jq '.dashboard'
        parameters:
          - name: dashboard_uid
            description: "Dashboard UID"
            required: true

      - name: query_panel
        description: "Query a specific panel's data"
        command: |
          curl -s -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
            "${GRAFANA_URL}/api/ds/query" \
            -d '{"queries": [{"refId": "A", "datasourceId": \
            {{ datasource_id }}, "rawSql": "{{ query }}"}]}'
        parameters:
          - name: datasource_id
            description: "Datasource ID"
          - name: query
            description: "Query to execute"
```

### Example: Custom Health Check Toolset

```yaml
toolsets:
  service-health:
    description: "Check health of internal services"
    prerequisites: "Network access to services"
    tools:
      - name: check_endpoint_health
        description: "Check HTTP endpoint health"
        command: |
          curl -s -o /dev/null -w "%{http_code}" \
            http://{{ service }}.{{ namespace }}.svc.cluster.local:{{ port }}/health
        parameters:
          - name: service
            description: "Service name"
          - name: namespace
            description: "Kubernetes namespace"
          - name: port
            description: "Service port"
            default: "8080"
        additionalInstructions: |
          200 = healthy, 5xx = server error, 4xx = client error

      - name: check_database_connectivity
        description: "Test database connection"
        command: |
          kubectl run db-check --rm -i --restart=Never --image=postgres:15 \
            -- pg_isready -h {{ host }} -p {{ port }} -U {{ user }}
        parameters:
          - name: host
            description: "Database host"
          - name: port
            description: "Database port"
            default: "5432"
          - name: user
            description: "Database user"
```

### Example: Kubernetes Diagnostics Toolset

```yaml
toolsets:
  k8s-diagnostics:
    description: "Advanced Kubernetes diagnostic commands"
    tools:
      - name: check_node_pressure
        description: "Check for node resource pressure conditions"
        command: |
          kubectl get nodes -o json | jq '.items[] | {
            name: .metadata.name,
            conditions: [.status.conditions[] |
              select(.type | test("Pressure")) | {type, status}]
          }'

      - name: get_pod_resource_usage
        description: "Get actual resource usage for pods in namespace"
        command: |
          kubectl top pods -n {{ namespace }} --sort-by=memory
        parameters:
          - name: namespace
            description: "Target namespace"

      - name: check_pvc_status
        description: "Check PersistentVolumeClaim status"
        command: |
          kubectl get pvc -n {{ namespace }} -o json | jq '.items[] | {
            name: .metadata.name,
            status: .status.phase,
            capacity: .status.capacity.storage,
            storageClass: .spec.storageClassName
          }'
        parameters:
          - name: namespace
            description: "Target namespace"

      - name: get_events
        description: "Get recent events filtered by type"
        command: |
          kubectl get events -n {{ namespace }} \
            --sort-by='.lastTimestamp' \
            --field-selector type={{ event_type }} -o json | \
            jq '.items[-10:] | .[] |
              {time: .lastTimestamp, reason: .reason, message: .message}'
        parameters:
          - name: namespace
            description: "Target namespace"
          - name: event_type
            description: "Event type (Normal or Warning)"
            default: "Warning"
```

## MCP Server Integration

HolmesGPT supports Model Context Protocol (MCP) servers for extended capabilities.

### Configuration

```yaml
# In Helm values.yaml
mcpServers:
  aws-mcp:
    command: "npx"
    args:
      - "-y"
      - "@aws-mcp/server"
    env:
      AWS_REGION: "us-east-1"

  github-mcp:
    command: "npx"
    args:
      - "-y"
      - "@github-mcp/server"
    env:
      GITHUB_TOKEN: "${GITHUB_TOKEN}"
```

## Custom Docker Image for Additional Tools

When you need binaries not in the base image:

```dockerfile
# Dockerfile
FROM us-central1-docker.pkg.dev/genuine-flight-317411/devel/holmes:latest

# Install custom tools
RUN apt-get update && apt-get install -y \
    postgresql-client \
    mysql-client \
    redis-tools

# Add custom scripts
COPY scripts/ /usr/local/bin/
RUN chmod +x /usr/local/bin/*.sh

# Add custom toolsets
COPY toolsets/ /etc/holmes/toolsets/
```

Build and use:

```bash
docker build -t my-holmes:latest .

# In Helm values
image:
  repository: my-registry/my-holmes
  tag: latest
```

## Toolset Best Practices

1. **Start Minimal**: Enable only kubernetes/core and kubernetes/logs initially
2. **Add Incrementally**: Enable additional toolsets as needed
3. **Security First**: Disable `internet` and `bash` in production unless required
4. **Use Environment Variables**: Never hardcode secrets in toolset YAML
5. **Test Custom Toolsets**: Verify commands work before deploying
6. **Document Prerequisites**: Clearly state required permissions and access
7. **Handle Large Outputs**: Use `llm_summarize` transformer for verbose commands
