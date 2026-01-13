# Configure Sinks

Workflow for setting up notification destinations in Robusta.

## Sink Configuration Location

All sinks are configured in `generated_values.yaml` under `sinksConfig`:

```yaml
sinksConfig:
  - <sink_type>:
      name: <unique_name>
      <sink_parameters>
```

## Communication Platforms

### Slack

```yaml
sinksConfig:
  - slack_sink:
      name: main_slack
      slack_channel: k8s-alerts
      api_key: xoxb-your-bot-token
      # Optional parameters
      # thread_messages: true          # Group alerts in threads
      # scope:                          # Filter alerts
      #   include:
      #     - namespace: production
```

**Getting Slack Token:**
1. Go to api.slack.com/apps
2. Create new app or use existing
3. Add `chat:write` and `files:write` scopes
4. Install to workspace
5. Copy Bot User OAuth Token

### Microsoft Teams

```yaml
sinksConfig:
  - ms_teams_sink:
      name: teams_alerts
      webhook_url: https://outlook.office.com/webhook/...
```

**Getting Teams Webhook:**
1. Go to Teams channel
2. Click ... > Connectors
3. Add "Incoming Webhook"
4. Copy webhook URL

### Discord

```yaml
sinksConfig:
  - discord_sink:
      name: discord_alerts
      url: https://discord.com/api/webhooks/...
```

### Google Chat

```yaml
sinksConfig:
  - google_chat_sink:
      name: gchat
      webhook_url: https://chat.googleapis.com/v1/spaces/...
```

## Incident Management

### PagerDuty

```yaml
sinksConfig:
  - pagerduty_sink:
      name: pagerduty_critical
      api_key: your-integration-key
      # Optional
      # scope:
      #   include:
      #     - labels:
      #         severity: critical
```

### OpsGenie

```yaml
sinksConfig:
  - opsgenie_sink:
      name: opsgenie
      api_key: your-api-key
      # teams:
      #   - team_name
```

### VictorOps (Splunk On-Call)

```yaml
sinksConfig:
  - victorops_sink:
      name: victorops
      url: https://alert.victorops.com/integrations/generic/...
      routing_key: your-routing-key
```

## Ticketing Systems

### Jira

```yaml
sinksConfig:
  - jira_sink:
      name: jira_tickets
      url: https://your-instance.atlassian.net
      username: your-email@company.com
      api_key: your-api-token
      project_name: OPS
      issue_type: Bug
```

### ServiceNow

```yaml
sinksConfig:
  - servicenow_sink:
      name: servicenow
      instance: your-instance
      username: admin
      password: your-password
```

## Data & Integration

### Kafka

```yaml
sinksConfig:
  - kafka_sink:
      name: kafka_alerts
      kafka_url: kafka-bootstrap:9092
      topic: robusta-alerts
```

### Webhook (Generic)

```yaml
sinksConfig:
  - webhook_sink:
      name: custom_webhook
      url: https://your-endpoint.com/alerts
      # headers:
      #   Authorization: Bearer token
```

### DataDog

```yaml
sinksConfig:
  - datadog_sink:
      name: datadog
      api_key: your-datadog-api-key
```

### File Sink (Debugging)

```yaml
sinksConfig:
  - file_sink:
      name: debug_file
      file_name: /tmp/robusta-alerts.log
```

## Robusta UI (SaaS)

```yaml
sinksConfig:
  - robusta_sink:
      name: robusta_ui
      token: <generated-during-setup>
```

## Filtering Alerts per Sink

### By Namespace

```yaml
sinksConfig:
  - slack_sink:
      name: prod_slack
      slack_channel: prod-alerts
      api_key: xoxb-...
      scope:
        include:
          - namespace: production
  - slack_sink:
      name: dev_slack
      slack_channel: dev-alerts
      api_key: xoxb-...
      scope:
        include:
          - namespace: development
          - namespace: staging
```

### By Severity

```yaml
sinksConfig:
  - pagerduty_sink:
      name: pagerduty_critical
      api_key: ...
      scope:
        include:
          - labels:
              severity: critical
  - slack_sink:
      name: slack_warnings
      slack_channel: warnings
      api_key: ...
      scope:
        include:
          - labels:
              severity: warning
```

### By Alert Name

```yaml
sinksConfig:
  - slack_sink:
      name: slack_pod_issues
      slack_channel: pod-alerts
      api_key: ...
      scope:
        include:
          - name: KubePod.*
```

## Applying Changes

```bash
helm upgrade robusta robusta/robusta \
  -f ./generated_values.yaml \
  --namespace robusta

# Verify sinks loaded
kubectl logs -n robusta deploy/robusta-runner | grep -i sink
```

## Testing Sinks

```bash
# Send test message to all sinks
kubectl exec -n robusta deploy/robusta-runner -- \
  robusta demo
```
