# Playbooks Reference

Complete reference for Robusta playbook configuration.

## Playbook Structure

```yaml
customPlaybooks:
  - triggers:
      - <trigger_type>:
          <trigger_parameters>
    actions:
      - <action_name>:
          <action_parameters>
    sinks:
      - <sink_name>
    scope:
      include:
        - <filter>
      exclude:
        - <filter>
```

## Built-in Playbooks

Robusta includes default playbooks for common alerts:

| Alert | Default Actions |
|-------|-----------------|
| KubePodCrashLooping | logs_enricher, pod_events_enricher |
| KubePodNotReady | pod_status_enricher |
| KubeDeploymentReplicasMismatch | deployment_status_enricher |
| KubeNodeNotReady | node_status_enricher |
| CPUThrottlingHigh | cpu_graph_enricher |

## Playbook Priority

Playbooks are evaluated in order. First matching playbook wins. Use `stop: true` to prevent further processing:

```yaml
customPlaybooks:
  - triggers:
      - on_prometheus_alert:
          alert_name: CriticalAlert
    actions:
      - logs_enricher: {}
    stop: true  # Don't process other playbooks
```

## Scope Filtering

### By Namespace

```yaml
scope:
  include:
    - namespace: production
    - namespace: staging
  exclude:
    - namespace: kube-system
```

### By Labels

```yaml
scope:
  include:
    - labels:
        team: backend
        env: prod
```

### By Alert Name (Regex)

```yaml
scope:
  include:
    - name: KubePod.*
    - name: .*Memory.*
```

### By Severity

```yaml
triggers:
  - on_prometheus_alert:
      alert_name: ".*"
      alert_severity: critical
```

## Common Playbook Patterns

### Crash Loop Enrichment

```yaml
customPlaybooks:
  - triggers:
      - on_prometheus_alert:
          alert_name: KubePodCrashLooping
    actions:
      - logs_enricher:
          previous_logs: true
      - pod_events_enricher: {}
      - pod_graph_enricher:
          resource_type: Memory
```

### Resource Monitoring

```yaml
customPlaybooks:
  - triggers:
      - on_prometheus_alert:
          alert_name: CPUThrottlingHigh
    actions:
      - cpu_graph_enricher:
          resource_type: CPU
      - node_cpu_enricher: {}
      - prometheus_enricher:
          query: "container_cpu_usage_seconds_total{pod='$pod'}"
```

### Scheduled Reports

```yaml
customPlaybooks:
  - triggers:
      - on_schedule:
          cron_schedule_repeat:
            cron_expression: "0 9 * * 1"  # Monday 9 AM
    actions:
      - cluster_status_enricher: {}
    sinks:
      - slack
```

### Auto-Remediation

```yaml
customPlaybooks:
  - triggers:
      - on_prometheus_alert:
          alert_name: KubePodCrashLooping
          alert_severity: critical
    actions:
      - logs_enricher: {}
      - delete_pod:
          force: false
          grace_period: 30
```

### OOM Detection

```yaml
customPlaybooks:
  - triggers:
      - on_pod_oom_killed: {}
    actions:
      - pod_oom_killer_enricher: {}
      - oom_killer_graph_enricher: {}
      - custom_graph_enricher:
          graph_title: "Memory Timeline"
          promql_query: "container_memory_working_set_bytes{pod='$pod'}"
```

## Playbook Variables

Available variables in playbook actions:

| Variable | Description |
|----------|-------------|
| `$pod` | Pod name |
| `$namespace` | Namespace |
| `$node` | Node name |
| `$deployment` | Deployment name |
| `$container` | Container name |
| `$alert_name` | Alert name |
| `$severity` | Alert severity |

## Global Configuration

```yaml
globalConfig:
  alertThrottleMinutes: 5      # Deduplicate alerts
  finding_processor_workers: 4  # Parallel processing
  timezone: "America/New_York"  # Timestamp timezone
```

## Disabling Built-in Playbooks

```yaml
builtinPlaybooks:
  - triggers:
      - on_prometheus_alert:
          alert_name: Watchdog
    actions: []  # Disable by setting empty actions
```
