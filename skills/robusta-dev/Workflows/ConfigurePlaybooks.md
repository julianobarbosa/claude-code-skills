# Configure Playbooks

Workflow for creating and managing Robusta playbooks.

## Playbook Structure

```yaml
customPlaybooks:
  - triggers:
      - <trigger_type>:
          <trigger_params>
    actions:
      - <action_name>:
          <action_params>
    sinks:
      - <sink_name>
```

## Common Playbook Patterns

### 1. Enrich CrashLoopBackOff Alerts

```yaml
customPlaybooks:
  - triggers:
      - on_prometheus_alert:
          alert_name: KubePodCrashLooping
    actions:
      - logs_enricher: {}
      - pod_events_enricher: {}
      - pod_graph_enricher:
          resource_type: Memory
```

### 2. Monitor High CPU Usage

```yaml
customPlaybooks:
  - triggers:
      - on_prometheus_alert:
          alert_name: CPUThrottlingHigh
    actions:
      - cpu_graph_enricher:
          resource_type: CPU
      - node_cpu_enricher: {}
```

### 3. Node Not Ready Alerts

```yaml
customPlaybooks:
  - triggers:
      - on_prometheus_alert:
          alert_name: KubeNodeNotReady
    actions:
      - node_status_enricher: {}
      - node_running_pods_enricher: {}
      - node_allocatable_resources_enricher: {}
```

### 4. Deployment Rollout Issues

```yaml
customPlaybooks:
  - triggers:
      - on_prometheus_alert:
          alert_name: KubeDeploymentReplicasMismatch
    actions:
      - deployment_status_enricher: {}
      - related_pods_enricher: {}
```

### 5. Scheduled Health Check

```yaml
customPlaybooks:
  - triggers:
      - on_schedule:
          cron_schedule_repeat:
            cron_expression: "0 */6 * * *"
    actions:
      - cluster_status_enricher: {}
    sinks:
      - slack
```

### 6. Auto-Remediation: Delete Stuck Pods

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
```

### 7. OOMKilled Detection

```yaml
customPlaybooks:
  - triggers:
      - on_pod_oom_killed: {}
    actions:
      - pod_oom_killer_enricher: {}
      - oom_killer_graph_enricher: {}
```

### 8. Custom Event Trigger

```yaml
customPlaybooks:
  - triggers:
      - on_kubernetes_warning_event:
          include:
            - FailedScheduling
            - BackOff
    actions:
      - event_report: {}
```

## Filtering Playbooks

### By Namespace

```yaml
customPlaybooks:
  - triggers:
      - on_prometheus_alert:
          alert_name: ".*"
    scope:
      include:
        - namespace: production
        - namespace: staging
```

### By Label

```yaml
customPlaybooks:
  - triggers:
      - on_prometheus_alert:
          alert_name: ".*"
    scope:
      include:
        - labels:
            team: backend
```

### By Severity

```yaml
customPlaybooks:
  - triggers:
      - on_prometheus_alert:
          alert_name: ".*"
          alert_severity: critical
```

## Applying Changes

After modifying `generated_values.yaml`:

```bash
# Upgrade Helm release
helm upgrade robusta robusta/robusta \
  -f ./generated_values.yaml \
  --namespace robusta

# Verify playbooks loaded
kubectl logs -n robusta deploy/robusta-runner | grep -i playbook

# List active playbooks
kubectl exec -n robusta deploy/robusta-runner -- robusta playbooks list
```

## Testing Playbooks

```bash
# Trigger a test alert manually
kubectl exec -n robusta deploy/robusta-runner -- \
  robusta playbooks trigger prometheus_alert \
  --alert-name TestAlert \
  --labels '{"severity":"warning"}'
```
