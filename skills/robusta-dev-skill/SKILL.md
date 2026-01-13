---
name: RobustaDev
description: Robusta Kubernetes observability and alert automation platform. USE WHEN installing Robusta OR configuring playbooks OR setting up notification sinks OR troubleshooting Kubernetes alerts OR creating custom actions OR integrating with Prometheus/AlertManager OR automating incident remediation.
---

# RobustaDev

Comprehensive guide for Robusta - the SRE agent that transforms Kubernetes alerts into actionable insights using playbooks, AI investigation, and automated remediation.

## Quick Reference

| Component | Purpose |
|-----------|---------|
| **Playbooks** | Rules engine defining alert responses |
| **Triggers** | Events that activate playbook execution |
| **Actions** | Remediation steps and enrichments |
| **Sinks** | Notification destinations (Slack, Teams, PagerDuty, etc.) |

## Workflow Routing

| Workflow | Trigger | File |
|----------|---------|------|
| **Install** | "install robusta", "deploy robusta" | `Workflows/Install.md` |
| **ConfigurePlaybooks** | "create playbook", "configure playbook" | `Workflows/ConfigurePlaybooks.md` |
| **ConfigureSinks** | "setup slack", "configure notifications" | `Workflows/ConfigureSinks.md` |
| **Troubleshoot** | "robusta not working", "alerts not firing" | `Workflows/Troubleshoot.md` |

## Installation Quick Start

### Prerequisites
- Kubernetes cluster
- Helm 3.x installed
- kubectl configured

### All-in-One Installation (Robusta + Prometheus)

```bash
# Generate configuration
pipx run robusta-cli gen-config --enable-prometheus-stack

# Or using Docker
curl -fsSL -o robusta https://docs.robusta.dev/master/_static/robusta
chmod +x robusta
./robusta gen-config --enable-prometheus-stack

# Install via Helm
helm repo add robusta https://robusta-charts.storage.googleapis.com
helm repo update
helm install robusta robusta/robusta \
  -f ./generated_values.yaml \
  --set clusterName=<YOUR_CLUSTER_NAME>

# Verify installation
kubectl get pods -A | grep robusta
```

### Standalone Installation (Existing Prometheus)

```bash
pipx run robusta-cli gen-config
helm install robusta robusta/robusta -f ./generated_values.yaml
```

## Playbook Structure

```yaml
# Example playbook in generated_values.yaml
customPlaybooks:
  - triggers:
      - on_prometheus_alert:
          alert_name: KubePodCrashLooping
    actions:
      - logs_enricher: {}
      - pod_events_enricher: {}
    sinks:
      - slack
```

### Trigger Types

| Trigger | Description |
|---------|-------------|
| `on_prometheus_alert` | Fires on Prometheus/AlertManager alerts |
| `on_pod_create` | When pod is created |
| `on_pod_update` | When pod is updated |
| `on_deployment_update` | When deployment changes |
| `on_schedule` | Cron-based scheduled execution |
| `on_kubernetes_warning_event` | On K8s warning events |

### Common Actions

| Action | Purpose |
|--------|---------|
| `logs_enricher` | Add pod logs to alert |
| `pod_events_enricher` | Add K8s events |
| `node_cpu_enricher` | Add CPU metrics |
| `node_memory_enricher` | Add memory metrics |
| `deployment_status_enricher` | Add deployment info |
| `delete_pod` | Auto-remediate by deleting pod |
| `node_bash_enricher` | Run bash commands on node |

## Sink Configuration

### Slack

```yaml
sinksConfig:
  - slack_sink:
      name: main_slack
      slack_channel: alerts
      api_key: xoxb-your-token
```

### Microsoft Teams

```yaml
sinksConfig:
  - ms_teams_sink:
      name: teams_alerts
      webhook_url: https://outlook.office.com/webhook/...
```

### PagerDuty

```yaml
sinksConfig:
  - pagerduty_sink:
      name: pagerduty
      api_key: your-integration-key
```

### Webhook (Generic)

```yaml
sinksConfig:
  - webhook_sink:
      name: custom_webhook
      url: https://your-endpoint.com/alerts
```

## Examples

**Example 1: Install Robusta with Prometheus**
```
User: "Install Robusta on my AKS cluster"
-> Generate config with gen-config --enable-prometheus-stack
-> Add Helm repo and install with cluster name
-> Verify pods are running
```

**Example 2: Create crash loop enrichment playbook**
```
User: "Add pod logs to CrashLoopBackOff alerts"
-> Create playbook with on_prometheus_alert trigger
-> Add logs_enricher and pod_events_enricher actions
-> Configure Slack sink for notifications
```

**Example 3: Configure Slack notifications**
```
User: "Send Robusta alerts to #k8s-alerts Slack channel"
-> Add slack_sink to sinksConfig
-> Set channel name and API key
-> Optionally filter by severity or namespace
```

**Example 4: Debug missing alerts**
```
User: "Robusta isn't sending alerts to Slack"
-> Check robusta-runner pod logs
-> Verify sink configuration in generated_values.yaml
-> Test with manual trigger: robusta playbooks trigger
```

## Key Concepts

### Alert Flow
```
Prometheus Alert -> AlertManager -> Robusta -> Playbook -> Actions -> Sinks
```

### Playbook Components
1. **Triggers** - What events activate the playbook
2. **Actions** - What to do when triggered (enrich, remediate)
3. **Sinks** - Where to send the result

### Smart Grouping
Robusta groups related alerts using Slack threads to reduce notification spam.

### AI Investigation (HolmesGPT)
Optional AI-powered root cause analysis available with Robusta Pro or self-hosted HolmesGPT.

## Reference Documentation

- `references/Installation.md` - Detailed installation guide
- `references/Playbooks.md` - Complete playbook reference
- `references/Triggers.md` - All trigger types
- `references/Actions.md` - Available actions
- `references/Sinks.md` - Sink configuration
- `references/Troubleshooting.md` - Common issues and fixes

## External Resources

- [Official Docs](https://docs.robusta.dev/master/)
- [GitHub](https://github.com/robusta-dev/robusta)
- [Robusta Platform](https://platform.robusta.dev) (SaaS UI)
