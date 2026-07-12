# Actions Reference

Complete reference for Robusta playbook actions.

## Log Actions

### logs_enricher

Adds container logs to alert.

```yaml
actions:
  - logs_enricher:
      container_name: main      # Optional: specific container
      previous_logs: true       # Include previous container logs
      warn_on_missing_label: true
      regex_replacer_patterns:  # Redact sensitive data
        - pattern: "password=.*"
          replacement: "password=REDACTED"
```

### pod_events_enricher

Adds Kubernetes events for the pod.

```yaml
actions:
  - pod_events_enricher:
      max_events: 10
```

## Graph/Metrics Actions

### pod_graph_enricher

Generates resource usage graphs for pod.

```yaml
actions:
  - pod_graph_enricher:
      resource_type: Memory    # Memory or CPU
      display_limits: true     # Show limits line
```

### cpu_graph_enricher

CPU-specific graph enricher.

```yaml
actions:
  - cpu_graph_enricher:
      resource_type: CPU
```

### node_cpu_enricher

Node-level CPU information.

```yaml
actions:
  - node_cpu_enricher: {}
```

### node_memory_enricher

Node-level memory information.

```yaml
actions:
  - node_memory_enricher: {}
```

### custom_graph_enricher

Custom PromQL query graph.

```yaml
actions:
  - custom_graph_enricher:
      graph_title: "Request Rate"
      promql_query: "rate(http_requests_total{pod='$pod'}[5m])"
      graph_duration_minutes: 60
```

### prometheus_enricher

Execute custom PromQL query.

```yaml
actions:
  - prometheus_enricher:
      query: "sum(rate(http_requests_total[5m]))"
```

## OOM Actions

### pod_oom_killer_enricher

Information about OOM kill events.

```yaml
actions:
  - pod_oom_killer_enricher: {}
```

### oom_killer_graph_enricher

Memory graph with OOM events marked.

```yaml
actions:
  - oom_killer_graph_enricher:
      delay_graph_s: 30  # Wait before generating
```

## Status Actions

### pod_status_enricher

Pod status and conditions.

```yaml
actions:
  - pod_status_enricher: {}
```

### deployment_status_enricher

Deployment status details.

```yaml
actions:
  - deployment_status_enricher: {}
```

### node_status_enricher

Node status and conditions.

```yaml
actions:
  - node_status_enricher: {}
```

### node_running_pods_enricher

List pods running on node.

```yaml
actions:
  - node_running_pods_enricher:
      max_pods: 20
```

### node_allocatable_resources_enricher

Node allocatable resources.

```yaml
actions:
  - node_allocatable_resources_enricher: {}
```

### cluster_status_enricher

Overall cluster status.

```yaml
actions:
  - cluster_status_enricher: {}
```

### related_pods_enricher

Find related pods (same deployment, etc.).

```yaml
actions:
  - related_pods_enricher: {}
```

## Remediation Actions

### delete_pod

Delete the affected pod.

```yaml
actions:
  - delete_pod:
      force: false          # Force delete
      grace_period: 30      # Seconds
```

### node_bash_enricher

Run bash command on node.

```yaml
actions:
  - node_bash_enricher:
      bash_command: "df -h"
```

### pod_bash_enricher

Run command in pod container.

```yaml
actions:
  - pod_bash_enricher:
      bash_command: "ls -la /app"
```

### restart_loop_reporter

Report restart loop with details.

```yaml
actions:
  - restart_loop_reporter:
      restart_reason: OOMKilled
```

## Report Actions

### event_report

Generate event report.

```yaml
actions:
  - event_report:
      title: "Kubernetes Event"
```

### create_finding

Create custom finding/alert.

```yaml
actions:
  - create_finding:
      title: "Custom Alert"
      aggregation_key: "custom-alert"
      severity: HIGH
      description: "Something happened"
```

## External Integration Actions

### send_to_webhook

Send data to external webhook.

```yaml
actions:
  - send_to_webhook:
      url: "https://my-api.com/alerts"
      headers:
        Authorization: "Bearer token"
```

### jira_issue_reporter

Create Jira ticket.

```yaml
actions:
  - jira_issue_reporter:
      project_key: "OPS"
      issue_type: "Bug"
```

## Silencing Actions

### silence_alert

Silence an alert temporarily.

```yaml
actions:
  - silence_alert:
      duration_minutes: 60
      comment: "Known issue, investigating"
```

## Customization

### Adding Custom Actions

Custom actions can be defined via Python:

```python
# In a custom playbook file
from robusta.api import *

@action
def my_custom_action(event: PodEvent):
    pod = event.get_pod()
    event.add_enrichment([
        MarkdownBlock(f"Pod {pod.metadata.name} info")
    ])
```

Load custom actions:

```yaml
# In generated_values.yaml
playbookRepos:
  - url: https://github.com/my-org/my-playbooks
    key: my-actions
```

## Action Parameters

All actions support these common parameters:

| Parameter | Type | Description |
|-----------|------|-------------|
| `rate_limit` | int | Seconds between executions |
| `timeout` | int | Action timeout in seconds |
