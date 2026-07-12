# HolmesGPT Commands Reference

Complete CLI command documentation with examples.

## Command Overview

| Command | Description |
|---------|-------------|
| `holmes ask` | Interactive troubleshooting queries |
| `holmes investigate` | Automated alert investigation |
| `holmes --help` | Show help information |

## holmes ask

The primary command for interactive troubleshooting.

### Basic Syntax

```bash
holmes ask "<query>" [options]
```

### Options

| Flag | Description |
|------|-------------|
| `--model <name>` | Model from modelList (default: configured default) |
| `-f, --file <path>` | Include file content in query |
| `--prompt-file <path>` | Read prompt from file |
| `-t, --toolset <path>` | Additional toolset YAML file |
| `-r, --runbook <path>` | Runbook file or directory |
| `--interactive` | Enable interactive mode |
| `--destination <dest>` | Output destination (slack, etc.) |
| `--slack-token <token>` | Slack bot token |
| `--slack-channel <channel>` | Target Slack channel |
| `--config <path>` | Config file path |
| `--log-level <level>` | Log verbosity |

### Examples

#### Basic Queries

```bash
# Simple troubleshooting
holmes ask "what pods are unhealthy and why?"

# Namespace-specific
holmes ask "why are pods crashing in production namespace?"

# Specific workload
holmes ask "investigate high memory usage in payment-service deployment"

# Check cluster health
holmes ask "summarize the overall health of my cluster"
```

#### With File Context

```bash
# Include log file
holmes ask "analyze these logs for errors" -f /tmp/app-logs.txt

# Include multiple files
holmes ask "compare these configurations" -f config1.yaml -f config2.yaml

# From prompt file (for complex queries)
holmes ask --prompt-file ~/prompts/investigation.txt
```

#### Model Selection

```bash
# Use specific model
holmes ask "complex analysis needed" --model opus

# Use faster model for simple queries
holmes ask "list namespaces" --model gpt4o
```

#### Interactive Mode

```bash
# Start interactive session
holmes ask "investigate alert" --interactive

# Start with initial context
holmes ask "payment service issues" --interactive
```

#### CI/CD Integration

```bash
# Send to Slack
holmes ask "why did deployment fail?" \
  --destination slack \
  --slack-token xoxb-your-token \
  --slack-channel "#deployments"

# With specific namespace context
holmes ask "analyze deployment failure in staging namespace for app-v2" \
  --destination slack \
  --slack-token $SLACK_TOKEN \
  --slack-channel "#alerts"
```

#### Custom Toolsets

```bash
# Use custom toolset
holmes ask "check database health" -t ~/toolsets/database.yaml

# Multiple toolsets
holmes ask "full system check" \
  -t ~/toolsets/database.yaml \
  -t ~/toolsets/messaging.yaml
```

## holmes investigate

Automated alert investigation from various sources.

### Investigate Syntax

```bash
holmes investigate <source> [options]
```

### Alert Sources

#### AlertManager

```bash
# Basic AlertManager investigation
holmes investigate alertmanager --alertmanager-url http://localhost:9093

# With authentication
holmes investigate alertmanager \
  --alertmanager-url http://alertmanager:9093 \
  --alertmanager-username admin \
  --alertmanager-password secret

# Filter by alertname
holmes investigate alertmanager \
  --alertmanager-url http://localhost:9093 \
  --alertname "KubePodCrashLooping"

# With runbooks
holmes investigate alertmanager \
  --alertmanager-url http://localhost:9093 \
  -r ~/runbooks/kubernetes.yaml
```

#### PagerDuty

```bash
# Investigate PagerDuty incidents
holmes investigate pagerduty --pagerduty-api-key $PAGERDUTY_KEY

# Update incident with analysis
holmes investigate pagerduty \
  --pagerduty-api-key $PAGERDUTY_KEY \
  --update

# Specific incident
holmes investigate pagerduty \
  --pagerduty-api-key $PAGERDUTY_KEY \
  --incident-id P123ABC
```

#### OpsGenie

```bash
# Investigate OpsGenie alerts
holmes investigate opsgenie --opsgenie-api-key $OPSGENIE_KEY

# Update with findings
holmes investigate opsgenie \
  --opsgenie-api-key $OPSGENIE_KEY \
  --update
```

#### Jira

```bash
# Investigate Jira issues
holmes investigate jira \
  --jira-url https://company.atlassian.net \
  --jira-username user@company.com \
  --jira-api-token $JIRA_TOKEN

# Specific project
holmes investigate jira \
  --jira-url https://company.atlassian.net \
  --jira-project OPS \
  --jira-username user@company.com \
  --jira-api-token $JIRA_TOKEN
```

#### GitHub Issues

```bash
# Investigate GitHub issues
holmes investigate github \
  --github-token $GITHUB_TOKEN \
  --github-repo owner/repo

# With labels filter
holmes investigate github \
  --github-token $GITHUB_TOKEN \
  --github-repo owner/repo \
  --github-labels "bug,priority:high"
```

### Common Options

| Flag | Description |
|------|-------------|
| `--model <name>` | Model to use |
| `--update` | Write analysis back to source |
| `-r, --runbook <path>` | Runbook for additional context |
| `--dry-run` | Show what would be done |
| `--max-alerts <n>` | Maximum alerts to process |

## Interactive Mode Slash Commands

When in interactive mode (`--interactive`), these slash commands are available:

### Navigation & Session Management

| Command | Description |
|---------|-------------|
| `/help` | Display all available commands and descriptions |
| `/exit` | Leave interactive mode (alternative: Ctrl+C twice) |
| `/clear` | Reset conversation history and begin anew |

### Toolset Management

| Command | Description |
|---------|-------------|
| `/tools` | List configured toolsets with enabled/disabled status |
| `/context` | Display token usage and context size information |

### Output Control

| Command | Description |
|---------|-------------|
| `/auto` | Toggle automatic tool output display after AI responses |
| `/last` | Show tool outputs from the previous AI response |
| `/show [number\|name]` | Open scrollable modal for specific tool output |

**Modal Navigation (vim-style keys):**

- `j`/`k` - Move down/up
- `g`/`G` - Jump to top/bottom
- `d`/`u` - Half-page down/up
- `w` - Toggle word wrap
- `q` or `Esc` - Close modal

### Execution Commands

| Command | Description |
|---------|-------------|
| `/run <command>` | Execute shell command and optionally share with AI |
| `/shell` | Start interactive shell session; share with AI upon exit |

### Interactive Mode Examples

```bash
# Start session
$ holmes ask "investigate payment failures" --interactive

> AI begins investigation...

# Clear context for new topic
/clear

# Run custom command and share results
/run kubectl get pods -n production -o wide

# Show full output of last tool call
/show

# Review what AI knows
/context

# Exit session
/exit
```

### Human-in-the-Loop Workflow

```bash
$ holmes ask "investigate network issues" --interactive

> AI: I see connectivity problems. Can you run a network test?

# Run command AI can't access
/run ssh node1 ping -c 3 node2

> Pinging node2 (10.0.1.5):
> 64 bytes: icmp_seq=1 ttl=64 time=0.5ms
> 64 bytes: icmp_seq=2 ttl=64 time=0.4ms
> ...

> AI: Network connectivity looks good. Let me check DNS...
```

## Query Best Practices

### Effective Queries

```bash
# Good: Specific and contextual
holmes ask "why is payment-service pod restarting in production namespace?"

# Good: Clear scope
holmes ask "analyze CPU usage for deployments in monitoring namespace"

# Good: Actionable
holmes ask "investigate OOMKilled events in the last hour"
```

### Ineffective Queries

```bash
# Bad: Too vague
holmes ask "why is my pod not working?"

# Bad: No context
holmes ask "what's wrong?"

# Bad: Too broad
holmes ask "check everything"
```

### Query Patterns by Use Case

#### Troubleshooting Crashes

```bash
holmes ask "why is <deployment> crashing in <namespace>?"
holmes ask "analyze CrashLoopBackOff for <pod-name>"
holmes ask "what caused the last restart of <deployment>?"
```

#### Performance Issues

```bash
holmes ask "why is <service> slow?"
holmes ask "investigate high latency in <namespace>"
holmes ask "analyze memory usage trends for <deployment>"
```

#### Deployment Failures

```bash
holmes ask "why did <deployment> rollout fail?"
holmes ask "analyze pending pods in <namespace>"
holmes ask "check image pull errors for <deployment>"
```

#### Resource Issues

```bash
holmes ask "which pods are consuming most memory in <namespace>?"
holmes ask "identify resource bottlenecks in cluster"
holmes ask "check node capacity and utilization"
```

#### Network Issues

```bash
holmes ask "investigate service connectivity issues for <service>"
holmes ask "check network policies affecting <pod>"
holmes ask "analyze DNS resolution failures"
```

## Output Formats

### Default Output

Human-readable analysis with sections:

- Alert Explanation
- Key Findings
- Root Causes
- Next Steps

### JSON Output

```bash
# For programmatic processing
holmes ask "query" --output json
```

### Slack Output

```bash
# Formatted for Slack
holmes ask "query" --destination slack --slack-token $TOKEN --slack-channel "#alerts"
```

## Environment Variables for Commands

```bash
# Set defaults via environment
export HOLMES_MODEL="sonnet"
export HOLMES_LOG_LEVEL="DEBUG"
export PROMETHEUS_URL="http://prometheus:9090"
export ALERTMANAGER_URL="http://alertmanager:9093"

# Run with defaults
holmes ask "check cluster health"
holmes investigate alertmanager
```

## Scripting Examples

### Bash Script for CI/CD

```bash
#!/bin/bash
# investigate-failure.sh

DEPLOYMENT_NAME=$1
NAMESPACE=$2

# Check if deployment failed
ROLLOUT_CMD="kubectl rollout status deployment/$DEPLOYMENT_NAME"
if ! $ROLLOUT_CMD -n $NAMESPACE --timeout=300s; then
    # Trigger HolmesGPT investigation
    holmes ask "why did $DEPLOYMENT_NAME fail in $NAMESPACE?" \
        --destination slack \
        --slack-token "$SLACK_TOKEN" \
        --slack-channel "#deployments"
fi
```

### GitHub Actions Integration

```yaml
- name: Investigate Deployment Failure
  if: failure()
  run: |
    pip install holmesgpt
    REPO="${{ github.event.repository.name }}"
    holmes ask "analyze deployment failure for $REPO" \
      --destination slack \
      --slack-token ${{ secrets.SLACK_TOKEN }} \
      --slack-channel "#ci-alerts"
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
```

### Cron Job for Health Checks

```bash
#!/bin/bash
# daily-health-check.sh

export ANTHROPIC_API_KEY="your-key"

REPORT=$(holmes ask "summarize cluster health and any issues from the past 24 hours")

# Send to Slack if issues found
if echo "$REPORT" | grep -q "Warning\|Critical\|Error"; then
    holmes ask "detail the issues found in daily health check" \
        --destination slack \
        --slack-token "$SLACK_TOKEN" \
        --slack-channel "#daily-reports"
fi
```
