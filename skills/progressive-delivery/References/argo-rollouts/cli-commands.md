# CLI Commands Reference

## Installation

### kubectl-argo-rollouts Plugin

```bash
# macOS (Homebrew)
brew install argoproj/tap/kubectl-argo-rollouts

# Linux/macOS (curl)
curl -LO https://github.com/argoproj/argo-rollouts/releases/latest/download/kubectl-argo-rollouts-$(uname -s | tr '[:upper:]' '[:lower:]')-amd64
chmod +x kubectl-argo-rollouts-*
sudo mv kubectl-argo-rollouts-* /usr/local/bin/kubectl-argo-rollouts

# Windows (PowerShell)
Invoke-WebRequest -Uri https://github.com/argoproj/argo-rollouts/releases/latest/download/kubectl-argo-rollouts-windows-amd64 -OutFile kubectl-argo-rollouts.exe
```

### Verify Installation

```bash
kubectl argo rollouts version
```

## Rollout Management Commands

### Get Rollout Status

```bash
# Basic status
kubectl argo rollouts get rollout <rollout-name>

# Watch mode (live updates)
kubectl argo rollouts get rollout <rollout-name> -w

# All namespaces
kubectl argo rollouts get rollout <rollout-name> -A

# Specific namespace
kubectl argo rollouts get rollout <rollout-name> -n <namespace>

# Output as YAML
kubectl argo rollouts get rollout <rollout-name> -o yaml
```

### Status Check

```bash
# Check rollout status
kubectl argo rollouts status <rollout-name>

# Wait for rollout to complete
kubectl argo rollouts status <rollout-name> --watch

# Timeout after specified duration
kubectl argo rollouts status <rollout-name> --timeout 5m
```

### List Rollouts

```bash
# List all rollouts
kubectl argo rollouts list rollouts

# All namespaces
kubectl argo rollouts list rollouts -A

# Specific namespace
kubectl argo rollouts list rollouts -n <namespace>

# Watch mode
kubectl argo rollouts list rollouts -w
```

## Rollout Control Commands

### Promote

```bash
# Promote to next step or full promotion
kubectl argo rollouts promote <rollout-name>

# Skip current step only
kubectl argo rollouts promote <rollout-name> --skip-current-step

# Skip all remaining steps (full promotion)
kubectl argo rollouts promote <rollout-name> --full
```

### Pause

```bash
# Pause rollout
kubectl argo rollouts pause <rollout-name>
```

### Resume

```bash
# Resume paused rollout (continues to next step)
kubectl argo rollouts promote <rollout-name>
```

### Abort

```bash
# Abort rollout (scales down canary, routes to stable)
kubectl argo rollouts abort <rollout-name>
```

### Retry

```bash
# Retry a failed rollout
kubectl argo rollouts retry <rollout-name>
```

### Undo (Rollback)

```bash
# Undo to previous revision
kubectl argo rollouts undo <rollout-name>

# Undo to specific revision
kubectl argo rollouts undo <rollout-name> --to-revision=2
```

### Restart

```bash
# Restart rollout (triggers new rollout with same spec)
kubectl argo rollouts restart <rollout-name>
```

### Set Image

```bash
# Update container image
kubectl argo rollouts set image <rollout-name> <container>=<image>:<tag>

# Example
kubectl argo rollouts set image my-rollout app=nginx:1.21
```

## Analysis Commands

### List AnalysisRuns

```bash
# List all analysis runs
kubectl argo rollouts list analysisruns

# Watch mode
kubectl argo rollouts list analysisruns -w
```

### Get AnalysisRun

```bash
# Get specific analysis run
kubectl argo rollouts get analysisrun <analysisrun-name>

# Watch mode
kubectl argo rollouts get analysisrun <analysisrun-name> -w
```

## Experiment Commands

### List Experiments

```bash
# List all experiments
kubectl argo rollouts list experiments

# Watch mode
kubectl argo rollouts list experiments -w
```

### Get Experiment

```bash
# Get specific experiment
kubectl argo rollouts get experiment <experiment-name>

# Watch mode
kubectl argo rollouts get experiment <experiment-name> -w
```

## Dashboard

### Start Dashboard

```bash
# Start web dashboard on localhost:3100
kubectl argo rollouts dashboard

# Custom port
kubectl argo rollouts dashboard --port 8080

# Custom address
kubectl argo rollouts dashboard --address 0.0.0.0
```

## Validation Commands

### Lint

```bash
# Validate rollout YAML
kubectl argo rollouts lint -f rollout.yaml

# Validate with specific namespace
kubectl argo rollouts lint -f rollout.yaml -n <namespace>
```

## Notifications

### Create Notification

```bash
# Create notification ConfigMap (for notification controller)
kubectl argo rollouts notifications template get <template-name>

# List notification templates
kubectl argo rollouts notifications template list

# List triggers
kubectl argo rollouts notifications trigger list
```

## Common Usage Patterns

### Deploy New Version

```bash
# Update image and monitor
kubectl argo rollouts set image my-rollout app=myapp:v2
kubectl argo rollouts get rollout my-rollout -w
```

### Manual Canary Progression

```bash
# Start rollout (image update triggers rollout)
kubectl argo rollouts set image my-rollout app=myapp:v2

# Wait for first step
kubectl argo rollouts status my-rollout

# Promote to next step
kubectl argo rollouts promote my-rollout

# Continue promoting...
kubectl argo rollouts promote my-rollout
```

### Emergency Rollback

```bash
# Abort current deployment
kubectl argo rollouts abort my-rollout

# Or undo to previous
kubectl argo rollouts undo my-rollout

# Verify stable
kubectl argo rollouts get rollout my-rollout
```

### Debug Failed Rollout

```bash
# Check rollout status
kubectl argo rollouts get rollout my-rollout

# Check analysis runs
kubectl argo rollouts list analysisruns

# Get failed analysis details
kubectl argo rollouts get analysisrun <failed-run-name>

# Retry after fixing issue
kubectl argo rollouts retry my-rollout
```

## Output Formats

| Flag | Description |
|------|-------------|
| `-o yaml` | Output as YAML |
| `-o json` | Output as JSON |
| `-o wide` | Wide output with additional columns |
| `-w` | Watch mode (live updates) |

## Namespace Flags

| Flag | Description |
|------|-------------|
| `-n <namespace>` | Specific namespace |
| `-A` or `--all-namespaces` | All namespaces |

## Common Options

```bash
# Help for any command
kubectl argo rollouts <command> --help

# Verbose output
kubectl argo rollouts <command> -v=6

# Dry run (where applicable)
kubectl argo rollouts <command> --dry-run
```
