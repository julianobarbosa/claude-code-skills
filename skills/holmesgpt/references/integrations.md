# HolmesGPT Integrations Reference

Complete guide for integrating HolmesGPT with alerting platforms, messaging
services, and incident management tools.

## Slack Integration

### Sending Analysis to Slack

HolmesGPT can send investigation results directly to Slack channels.

**CLI Usage:**

```bash
# Send to a specific channel
holmes ask "why is payment-service crashing?" \
  --destination slack \
  --slack-token xoxb-your-bot-token \
  --slack-channel "#incidents"

# Send alert investigation to Slack
holmes investigate alertmanager \
  --alertmanager-url http://alertmanager:9093 \
  --destination slack \
  --slack-token $SLACK_BOT_TOKEN \
  --slack-channel "#alerts"
```

### Creating a Slack Bot

1. Go to [api.slack.com/apps](https://api.slack.com/apps) and create a new app
2. Under "OAuth & Permissions", add these Bot Token Scopes:
   - `chat:write` - Send messages
   - `chat:write.public` - Send to channels without joining
   - `files:write` - Upload files (for large outputs)
3. Install the app to your workspace
4. Copy the "Bot User OAuth Token" (starts with `xoxb-`)

### Helm Configuration for Slack

```yaml
env:
  - name: SLACK_BOT_TOKEN
    valueFrom:
      secretKeyRef:
        name: holmesgpt-secrets
        key: slack-bot-token
  - name: SLACK_CHANNEL
    value: "#holmesgpt-alerts"

# In values.yaml destination configuration
destinations:
  slack:
    enabled: true
    default_channel: "#holmesgpt-alerts"
```

### Slack Message Formatting

HolmesGPT formats messages with sections:

```text
:mag: *HolmesGPT Investigation*

*Alert:* KubePodCrashLooping
*Namespace:* production

*Key Findings:*
• Pod restarted 5 times in the last hour
• OOMKilled events detected
• Memory usage exceeded limits

*Root Cause:*
Memory leak in application causing OOM kills

*Recommended Actions:*
1. Increase memory limits
2. Investigate memory leak
3. Enable memory profiling
```

## PagerDuty Integration

### Investigating PagerDuty Incidents

```bash
# Investigate open incidents
holmes investigate pagerduty \
  --pagerduty-api-key $PAGERDUTY_API_KEY

# Update incidents with analysis
holmes investigate pagerduty \
  --pagerduty-api-key $PAGERDUTY_API_KEY \
  --update

# Investigate specific incident
holmes investigate pagerduty \
  --pagerduty-api-key $PAGERDUTY_API_KEY \
  --incident-id P123ABC \
  --update
```

### PagerDuty API Key Setup

1. Go to PagerDuty > Integrations > API Access Keys
2. Create a new API key with read/write access
3. Store securely in Kubernetes secret

```bash
kubectl create secret generic holmesgpt-secrets \
  --namespace holmesgpt \
  --from-literal=pagerduty-api-key="your-api-key"
```

### Helm Configuration for PagerDuty

```yaml
env:
  - name: PAGERDUTY_API_KEY
    valueFrom:
      secretKeyRef:
        name: holmesgpt-secrets
        key: pagerduty-api-key

# Enable PagerDuty integration
integrations:
  pagerduty:
    enabled: true
    update_incidents: true
    add_notes: true
```

### PagerDuty Integration Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| Read-only | Fetch incidents, no updates | Testing, read-only access |
| Notes | Add investigation as notes | Non-intrusive documentation |
| Update | Modify incident details | Full automation |

## OpsGenie Integration

### Investigating OpsGenie Alerts

```bash
# Investigate open alerts
holmes investigate opsgenie \
  --opsgenie-api-key $OPSGENIE_API_KEY

# Update alerts with findings
holmes investigate opsgenie \
  --opsgenie-api-key $OPSGENIE_API_KEY \
  --update

# Filter by priority
holmes investigate opsgenie \
  --opsgenie-api-key $OPSGENIE_API_KEY \
  --priority P1,P2
```

### OpsGenie API Key Setup

1. Go to OpsGenie > Settings > API key management
2. Create a new API key with appropriate permissions
3. Store in Kubernetes secret

```yaml
env:
  - name: OPSGENIE_API_KEY
    valueFrom:
      secretKeyRef:
        name: holmesgpt-secrets
        key: opsgenie-api-key
```

## AlertManager Integration

### Webhook Receiver Setup

Configure AlertManager to send alerts to HolmesGPT for automatic investigation.

**AlertManager Configuration:**

```yaml
# alertmanager.yml
route:
  receiver: default
  routes:
    - match:
        severity: critical
      receiver: holmesgpt
      continue: true

receivers:
  - name: default
    # Your default receiver config

  - name: holmesgpt
    webhook_configs:
      - url: 'http://holmesgpt-holmes.holmesgpt.svc.cluster.local/api/investigate'
        send_resolved: false
        max_alerts: 10
```

### Investigating AlertManager Alerts

```bash
# Basic investigation
holmes investigate alertmanager \
  --alertmanager-url http://alertmanager:9093

# With authentication
holmes investigate alertmanager \
  --alertmanager-url http://alertmanager:9093 \
  --alertmanager-username admin \
  --alertmanager-password $ALERTMANAGER_PASSWORD

# Filter by alert name
holmes investigate alertmanager \
  --alertmanager-url http://alertmanager:9093 \
  --alertname "KubePodCrashLooping"

# With custom runbook
holmes investigate alertmanager \
  --alertmanager-url http://alertmanager:9093 \
  -r ~/runbooks/kubernetes.yaml
```

## Jira Integration

### Investigating Jira Issues

```bash
# Investigate issues in a project
holmes investigate jira \
  --jira-url https://company.atlassian.net \
  --jira-username user@company.com \
  --jira-api-token $JIRA_TOKEN \
  --jira-project OPS

# Filter by JQL
holmes investigate jira \
  --jira-url https://company.atlassian.net \
  --jira-username user@company.com \
  --jira-api-token $JIRA_TOKEN \
  --jira-jql "project = OPS AND status = Open AND labels = incident"
```

### Jira API Token Setup

1. Go to [id.atlassian.com/manage-profile/security/api-tokens](https://id.atlassian.com/manage-profile/security/api-tokens)
2. Create a new API token
3. Store in secret

```yaml
env:
  - name: JIRA_URL
    value: "https://company.atlassian.net"
  - name: JIRA_USERNAME
    value: "user@company.com"
  - name: JIRA_API_TOKEN
    valueFrom:
      secretKeyRef:
        name: holmesgpt-secrets
        key: jira-api-token
```

## GitHub Integration

### Investigating GitHub Issues

```bash
# Investigate issues in a repository
holmes investigate github \
  --github-token $GITHUB_TOKEN \
  --github-repo owner/repo

# Filter by labels
holmes investigate github \
  --github-token $GITHUB_TOKEN \
  --github-repo owner/repo \
  --github-labels "bug,priority:high"

# Update issues with analysis
holmes investigate github \
  --github-token $GITHUB_TOKEN \
  --github-repo owner/repo \
  --update
```

### GitHub Token Permissions

Required permissions for the GitHub token:

- `repo` - Full repository access (for private repos)
- `public_repo` - Public repository access only
- `read:org` - Read organization info (optional)

## Webhook Configuration

### Generic Webhook Output

Send HolmesGPT analysis to any webhook endpoint.

```bash
# Send to custom webhook
holmes ask "analyze cluster health" \
  --destination webhook \
  --webhook-url https://your-service.com/api/holmes \
  --webhook-headers "Authorization: Bearer $TOKEN"
```

### Webhook Payload Structure

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "source": "holmesgpt",
  "type": "investigation",
  "data": {
    "query": "why is payment-service crashing?",
    "analysis": "Full analysis text...",
    "sections": {
      "alert_explanation": "...",
      "key_findings": "...",
      "root_causes": "...",
      "next_steps": "..."
    },
    "model": "sonnet",
    "token_count": 1500
  }
}
```

### Webhook Helm Configuration

```yaml
webhooks:
  - name: custom-webhook
    url: "https://your-service.com/api/alerts"
    headers:
      Authorization: "Bearer ${WEBHOOK_TOKEN}"
      Content-Type: "application/json"
    events:
      - investigation_complete
      - critical_alert
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Investigate Deployment Failure

on:
  workflow_run:
    workflows: ["Deploy"]
    types: [completed]

jobs:
  investigate:
    if: ${{ github.event.workflow_run.conclusion == 'failure' }}
    runs-on: ubuntu-latest
    steps:
      - name: Install HolmesGPT
        run: pip install holmesgpt

      - name: Configure kubectl
        uses: azure/k8s-set-context@v3
        with:
          kubeconfig: ${{ secrets.KUBECONFIG }}

      - name: Investigate Failure
        env:
          ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
          SLACK_BOT_TOKEN: ${{ secrets.SLACK_BOT_TOKEN }}
        run: |
          holmes ask "analyze deployment failure for ${{ github.repository }}" \
            --destination slack \
            --slack-token $SLACK_BOT_TOKEN \
            --slack-channel "#deployments"
```

### GitLab CI

```yaml
investigate_failure:
  stage: post-deploy
  when: on_failure
  image: python:3.11
  script:
    - pip install holmesgpt
    - |
      holmes ask "why did deployment fail for $CI_PROJECT_NAME?" \
        --destination slack \
        --slack-token $SLACK_BOT_TOKEN \
        --slack-channel "#deployments"
  only:
    - main
```

### Azure DevOps

```yaml
- task: Bash@3
  displayName: 'Investigate Failure'
  condition: failed()
  inputs:
    targetType: 'inline'
    script: |
      pip install holmesgpt
      export ANTHROPIC_API_KEY=$(ANTHROPIC_API_KEY)
      holmes ask "analyze deployment failure for $(Build.Repository.Name)" \
        --destination slack \
        --slack-token $(SLACK_BOT_TOKEN) \
        --slack-channel "#azure-deployments"
```

## Robusta Integration

HolmesGPT integrates seamlessly with Robusta for automated alert enrichment.

### Robusta Playbook Configuration

```yaml
# robusta_playbook.yaml
customPlaybooks:
  - triggers:
      - on_prometheus_alert:
          alert_name: KubePodCrashLooping
    actions:
      - holmes_investigate:
          model: sonnet
          add_to_timeline: true
```

### Environment Variables for Robusta

```yaml
env:
  - name: ROBUSTA_ACCOUNT_ID
    valueFrom:
      secretKeyRef:
        name: robusta-secrets
        key: account-id
  - name: ROBUSTA_SIGNING_KEY
    valueFrom:
      secretKeyRef:
        name: robusta-secrets
        key: signing-key
```

## Best Practices

### Secret Management

1. **Never hardcode credentials** - Use Kubernetes Secrets or external secret managers
2. **Rotate tokens regularly** - Set up token rotation policies
3. **Use minimal permissions** - Grant only required access levels
4. **Audit access** - Monitor and log integration usage

### Rate Limiting Considerations

| Integration | Recommended Rate | Notes |
|-------------|------------------|-------|
| Slack | 1 msg/sec | Slack rate limits |
| PagerDuty | 60 req/min | API tier dependent |
| OpsGenie | 100 req/min | Plan dependent |
| GitHub | 5000 req/hr | Authenticated limit |
| Jira | 100 req/min | Cloud limits |

### Error Handling

```bash
# Retry with exponential backoff
RETRY_COUNT=0
MAX_RETRIES=3

until holmes investigate pagerduty --pagerduty-api-key $KEY \
  || [ $RETRY_COUNT -eq $MAX_RETRIES ]; do
  RETRY_COUNT=$((RETRY_COUNT + 1))
  SLEEP_TIME=$((2 ** RETRY_COUNT))
  echo "Retry $RETRY_COUNT in $SLEEP_TIME seconds..."
  sleep $SLEEP_TIME
done
```

### Multi-Integration Setup

```yaml
# Complete multi-integration values.yaml
env:
  - name: ANTHROPIC_API_KEY
    valueFrom:
      secretKeyRef:
        name: holmesgpt-secrets
        key: anthropic-api-key
  - name: SLACK_BOT_TOKEN
    valueFrom:
      secretKeyRef:
        name: holmesgpt-secrets
        key: slack-bot-token
  - name: PAGERDUTY_API_KEY
    valueFrom:
      secretKeyRef:
        name: holmesgpt-secrets
        key: pagerduty-api-key
  - name: GITHUB_TOKEN
    valueFrom:
      secretKeyRef:
        name: holmesgpt-secrets
        key: github-token
  - name: ALERTMANAGER_URL
    value: "http://alertmanager.monitoring.svc.cluster.local:9093"

integrations:
  slack:
    enabled: true
    default_channel: "#holmesgpt"
  pagerduty:
    enabled: true
    update_incidents: true
  alertmanager:
    enabled: true
    webhook: true
  github:
    enabled: true
```
