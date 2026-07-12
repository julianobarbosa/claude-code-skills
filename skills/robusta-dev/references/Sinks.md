# Sinks Reference

Complete reference for Robusta notification sinks.

## Sink Configuration

All sinks are configured in `generated_values.yaml`:

```yaml
sinksConfig:
  - <sink_type>:
      name: <unique_identifier>
      <sink_parameters>
      scope:
        include:
          - <filter>
        exclude:
          - <filter>
```

## Communication Platforms

### Slack

```yaml
sinksConfig:
  - slack_sink:
      name: main_slack
      slack_channel: k8s-alerts
      api_key: xoxb-your-bot-token
      thread_messages: true       # Group in threads
      message_format: standard    # standard, minimal, detailed
```

**Slack Bot Setup:**
1. Create app at api.slack.com/apps
2. Add OAuth scopes: `chat:write`, `files:write`
3. Install to workspace
4. Invite bot to channel

### Microsoft Teams

```yaml
sinksConfig:
  - ms_teams_sink:
      name: teams_alerts
      webhook_url: https://outlook.office.com/webhook/...
```

**Teams Webhook Setup:**
1. Channel → ... → Connectors
2. Add "Incoming Webhook"
3. Copy webhook URL

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

### Telegram

```yaml
sinksConfig:
  - telegram_sink:
      name: telegram
      bot_token: "123456:ABC-DEF..."
      chat_id: "-100123456789"
```

## Incident Management

### PagerDuty

```yaml
sinksConfig:
  - pagerduty_sink:
      name: pagerduty
      api_key: your-integration-key
      routing_key: your-routing-key  # Optional
```

### OpsGenie

```yaml
sinksConfig:
  - opsgenie_sink:
      name: opsgenie
      api_key: your-api-key
      teams:
        - platform-team
      priority: P2  # P1-P5
```

### VictorOps (Splunk On-Call)

```yaml
sinksConfig:
  - victorops_sink:
      name: victorops
      url: https://alert.victorops.com/integrations/generic/...
      routing_key: your-routing-key
```

### Incident.io

```yaml
sinksConfig:
  - incidentio_sink:
      name: incidentio
      api_key: your-api-key
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
      dedupe: true  # Prevent duplicates
```

### ServiceNow

```yaml
sinksConfig:
  - servicenow_sink:
      name: servicenow
      instance: your-instance
      username: admin
      password: your-password
      table: incident
```

## Data/Analytics

### Kafka

```yaml
sinksConfig:
  - kafka_sink:
      name: kafka_alerts
      kafka_url: kafka-bootstrap:9092
      topic: robusta-alerts
      username: user           # Optional
      password: pass           # Optional
      security_protocol: SASL_SSL
```

### DataDog

```yaml
sinksConfig:
  - datadog_sink:
      name: datadog
      api_key: your-datadog-api-key
```

### Elasticsearch

```yaml
sinksConfig:
  - elasticsearch_sink:
      name: elasticsearch
      url: https://elasticsearch:9200
      index: robusta-alerts
      username: elastic
      password: your-password
```

### Webhook (Generic)

```yaml
sinksConfig:
  - webhook_sink:
      name: custom_webhook
      url: https://your-endpoint.com/alerts
      headers:
        Authorization: "Bearer token"
        Content-Type: "application/json"
```

## Robusta Platform

### Robusta UI (SaaS)

```yaml
sinksConfig:
  - robusta_sink:
      name: robusta_ui
      token: <generated-during-setup>
```

## Debugging

### File Sink

```yaml
sinksConfig:
  - file_sink:
      name: debug_file
      file_name: /tmp/robusta-alerts.log
```

### SMTP/Email

```yaml
sinksConfig:
  - mail_sink:
      name: email_alerts
      mailto: alerts@company.com
      smtp_host: smtp.company.com
      smtp_port: 587
      username: alerts@company.com
      password: your-password
```

## Sink Filtering

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

### Exclude Namespaces

```yaml
sinksConfig:
  - slack_sink:
      name: main_slack
      slack_channel: alerts
      api_key: ...
      scope:
        exclude:
          - namespace: kube-system
          - namespace: monitoring
```

## Multiple Sinks

Configure multiple sinks for different purposes:

```yaml
sinksConfig:
  # All alerts to main channel
  - slack_sink:
      name: all_alerts
      slack_channel: k8s-alerts
      api_key: xoxb-...

  # Critical alerts to pager
  - pagerduty_sink:
      name: critical_pager
      api_key: ...
      scope:
        include:
          - labels:
              severity: critical

  # Production issues to dedicated channel
  - slack_sink:
      name: prod_alerts
      slack_channel: prod-critical
      api_key: xoxb-...
      scope:
        include:
          - namespace: production

  # Archive all to Elasticsearch
  - elasticsearch_sink:
      name: archive
      url: https://es:9200
      index: robusta-alerts
```

## Testing Sinks

```bash
# Test all sinks
kubectl exec -n robusta deploy/robusta-runner -- robusta demo

# Check sink status in logs
kubectl logs -n robusta deploy/robusta-runner | grep -i sink
```
