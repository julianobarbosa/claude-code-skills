# Triggers Reference

Complete reference for Robusta playbook triggers.

## Prometheus/AlertManager Triggers

### on_prometheus_alert

Fires when Prometheus AlertManager sends an alert.

```yaml
triggers:
  - on_prometheus_alert:
      alert_name: KubePodCrashLooping  # Exact or regex
      alert_severity: critical          # Optional: info, warning, critical
      status: firing                    # Optional: firing, resolved
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `alert_name` | string/regex | Alert name pattern |
| `alert_severity` | string | Filter by severity |
| `status` | string | firing or resolved |
| `pod_name_prefix` | string | Filter by pod prefix |
| `namespace_prefix` | string | Filter by namespace prefix |

## Kubernetes Event Triggers

### on_kubernetes_warning_event

Fires on Kubernetes warning events.

```yaml
triggers:
  - on_kubernetes_warning_event:
      include:
        - FailedScheduling
        - BackOff
        - Unhealthy
      exclude:
        - TooManyPods
```

### on_kubernetes_any_event

Fires on any Kubernetes event (warning or normal).

```yaml
triggers:
  - on_kubernetes_any_event:
      include:
        - Pulling
        - Pulled
```

## Pod Lifecycle Triggers

### on_pod_create

Fires when a pod is created.

```yaml
triggers:
  - on_pod_create:
      name_prefix: api-
      namespace_prefix: production
```

### on_pod_update

Fires when a pod is updated.

```yaml
triggers:
  - on_pod_update:
      operation: Update
```

### on_pod_delete

Fires when a pod is deleted.

```yaml
triggers:
  - on_pod_delete: {}
```

### on_pod_oom_killed

Fires when a container is OOM killed.

```yaml
triggers:
  - on_pod_oom_killed:
      rate_limit: 1800  # Seconds between triggers
```

### on_container_state_change

Fires on container state transitions.

```yaml
triggers:
  - on_container_state_change:
      new_state: CrashLoopBackOff
```

## Deployment Triggers

### on_deployment_create

```yaml
triggers:
  - on_deployment_create: {}
```

### on_deployment_update

```yaml
triggers:
  - on_deployment_update:
      operation: Update
```

### on_deployment_delete

```yaml
triggers:
  - on_deployment_delete: {}
```

### on_deployment_replica_change

Fires when replica count changes.

```yaml
triggers:
  - on_deployment_replica_change:
      increase: true
      decrease: true
```

## Node Triggers

### on_node_create

```yaml
triggers:
  - on_node_create: {}
```

### on_node_update

```yaml
triggers:
  - on_node_update: {}
```

### on_node_delete

```yaml
triggers:
  - on_node_delete: {}
```

### on_node_status_change

Fires when node status changes (Ready/NotReady).

```yaml
triggers:
  - on_node_status_change:
      status: NotReady
```

## Job Triggers

### on_job_create

```yaml
triggers:
  - on_job_create: {}
```

### on_job_update

```yaml
triggers:
  - on_job_update: {}
```

### on_job_failure

Fires when a job fails.

```yaml
triggers:
  - on_job_failure: {}
```

### on_job_success

Fires when a job succeeds.

```yaml
triggers:
  - on_job_success: {}
```

## Schedule Triggers

### on_schedule

Fires on a cron schedule.

```yaml
triggers:
  - on_schedule:
      cron_schedule_repeat:
        cron_expression: "0 */6 * * *"  # Every 6 hours
```

**Cron Format:** `minute hour day month weekday`

| Expression | Description |
|------------|-------------|
| `0 * * * *` | Every hour |
| `0 0 * * *` | Daily at midnight |
| `0 9 * * 1` | Monday 9 AM |
| `*/15 * * * *` | Every 15 minutes |

## Service/Ingress Triggers

### on_service_create

```yaml
triggers:
  - on_service_create: {}
```

### on_ingress_create

```yaml
triggers:
  - on_ingress_create: {}
```

## HPA Triggers

### on_horizontalpodautoscaler_update

```yaml
triggers:
  - on_horizontalpodautoscaler_update: {}
```

## Manual Triggers

### on_manual_trigger

Can be triggered via API or CLI.

```yaml
triggers:
  - on_manual_trigger:
      action_params:
        param1: value1
```

**Trigger via CLI:**

```bash
kubectl exec -n robusta deploy/robusta-runner -- \
  robusta playbooks trigger manual_trigger \
  --action-params '{"param1": "value1"}'
```

## Trigger Filtering

All triggers support these common filters:

```yaml
triggers:
  - on_pod_create:
      name_prefix: api-
      namespace_prefix: prod
      labels_selector: "app=backend,tier=api"
```

| Filter | Description |
|--------|-------------|
| `name_prefix` | Resource name prefix |
| `namespace_prefix` | Namespace prefix |
| `labels_selector` | Label selector string |
