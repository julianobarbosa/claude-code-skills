# tmuxp Workflow Patterns

## Table of Contents

1. [Development Workflow](#development-workflow)
2. [Infrastructure / DevOps Workflow](#infrastructure--devops-workflow)
3. [Monitoring Dashboard](#monitoring-dashboard)
4. [AI-Assisted Development](#ai-assisted-development)
5. [Multi-Environment Kubernetes](#multi-environment-kubernetes)
6. [CI/CD Pipeline Management](#cicd-pipeline-management)
7. [Database Operations](#database-operations)

---

## Development Workflow

Standard software development setup: editor, server, tests, git.

```yaml
session_name: myapp-dev
start_directory: ~/Projects/myapp

windows:
  - window_name: editor
    focus: true
    layout: main-vertical
    options:
      main-pane-width: 70%
    panes:
      - focus: true
        shell_command:
          - vim .
      - shell_command:
          - npm test -- --watch
      - shell_command:
          - watch -n 5 "git status -sb && echo '' && git log --oneline -5"

  - window_name: server
    layout: even-horizontal
    panes:
      - shell_command:
          - npm run dev
      - shell_command:
          - tail -f logs/dev.log 2>/dev/null || echo "No log file yet"

  - window_name: terminal
    panes:
      - shell_command:
          - echo "Ready for commands"
```

**When to use**: Any project with a dev server, test suite, and editor.

---

## Infrastructure / DevOps Workflow

Terraform, cloud resources, and infrastructure management.

```yaml
session_name: infra-project
start_directory: ~/Repos/infrastructure
environment:
  CLOUD_PROVIDER: azure
  RESOURCE_GROUP: rg-myproject
  TF_WORKSPACE: dev

before_script: |
  echo "Checking prerequisites..."
  for tool in terraform az kubectl helm; do
    command -v $tool >/dev/null || echo "Warning: $tool not found"
  done
  az account show >/dev/null 2>&1 || echo "Warning: Not logged into Azure"

windows:
  - window_name: terraform
    focus: true
    layout: main-horizontal
    options:
      main-pane-height: 70%
    panes:
      - focus: true
        shell_command:
          - echo "Terraform Workspace: ${TF_WORKSPACE}"
          - terraform workspace list 2>/dev/null || echo "Not initialized"
      - shell_command:
          - echo "Plan/Apply output will appear here"

  - window_name: cloud-resources
    layout: even-horizontal
    panes:
      - shell_command:
          - az resource list -g ${RESOURCE_GROUP} -o table 2>/dev/null || echo "No resources"
      - shell_command:
          - echo "Resource management pane"

  - window_name: monitoring
    layout: tiled
    panes:
      - htop || top
      - shell_command:
          - kubectl top nodes 2>/dev/null || echo "No cluster connected"
      - shell_command:
          - docker stats --no-stream 2>/dev/null || echo "Docker not running"
```

**When to use**: Managing cloud infrastructure, Terraform plans, resource lifecycle.

---

## Monitoring Dashboard

Real-time system and application monitoring.

```yaml
session_name: monitoring
environment:
  K8S_NAMESPACE: default

windows:
  - window_name: system
    layout: tiled
    panes:
      - htop || top
      - shell_command:
          - docker stats 2>/dev/null || echo "Docker not running"
      - shell_command:
          - watch -n 5 "df -h | head -10"
      - shell_command:
          - watch -n 2 "free -h"

  - window_name: kubernetes
    layout: tiled
    panes:
      - shell_command:
          - watch -n 5 "kubectl get pods -n ${K8S_NAMESPACE} 2>/dev/null"
      - shell_command:
          - kubectl get events -n ${K8S_NAMESPACE} --sort-by='.lastTimestamp' -w 2>/dev/null || echo "No cluster"
      - shell_command:
          - watch -n 10 "kubectl top nodes 2>/dev/null"
      - shell_command:
          - watch -n 10 "kubectl top pods -n ${K8S_NAMESPACE} 2>/dev/null"

  - window_name: logs
    layout: even-vertical
    panes:
      - shell_command:
          - if command -v stern >/dev/null; then
              stern -n ${K8S_NAMESPACE} ".*"
            else
              kubectl logs -n ${K8S_NAMESPACE} -f --tail=50 --prefix=true 2>/dev/null || echo "No pods"
            fi
      - shell_command:
          - kubectl get events --all-namespaces --field-selector type=Warning --sort-by='.lastTimestamp' 2>/dev/null | tail -20
```

**When to use**: Oncall, incident investigation, system health checks.

---

## AI-Assisted Development

Workspace with AI coding agents alongside traditional tools.

```yaml
session_name: ai-dev
start_directory: ~/Projects/myapp

windows:
  - window_name: ai-agent
    focus: true
    layout: main-horizontal
    options:
      main-pane-height: 70%
    panes:
      - focus: true
        shell_command:
          - echo "AI Agent workspace"
          - claude
      - shell_command:
          - echo "Validation pane (run tests, check output)"

  - window_name: code-review
    panes:
      - shell_command:
          - echo "Code review and git operations"
          - git status

  - window_name: docs
    layout: even-horizontal
    panes:
      - shell_command:
          - echo "Documentation reference"
      - shell_command:
          - echo "Notes and scratch"
```

**When to use**: Working with Claude Code, GitHub Copilot, or other AI agents.

---

## Multi-Environment Kubernetes

Separate windows per environment with increasing safety.

```yaml
session_name: k8s-ops
environment:
  APP_NS: myapp
  K8S_CTX_DEV: aks-myapp-dev
  K8S_CTX_STG: aks-myapp-stg
  K8S_CTX_PRD: aks-myapp-prd

before_script: |
  for env in dev stg prd; do
    CTX_VAR="K8S_CTX_${env^^}"
    CTX="${!CTX_VAR}"
    kubectl config get-contexts -o name | grep -q "^${CTX}$" \
      && echo "OK: $CTX" || echo "MISSING: $CTX"
  done

windows:
  - window_name: k8s-dev
    focus: true
    layout: main-horizontal
    options:
      main-pane-height: 65%
    panes:
      - focus: true
        shell_command:
          - kubectl config use-context ${K8S_CTX_DEV}
          - echo "DEV - Full access"
      - shell_command:
          - watch -n 2 "kubectl get pods -n ${APP_NS}"

  - window_name: k8s-staging
    layout: even-vertical
    panes:
      - shell_command:
          - echo "STAGING - Be careful with changes"
          - kubectl config use-context ${K8S_CTX_STG}
      - shell_command:
          - watch -n 5 "kubectl get pods -n ${APP_NS}"

  - window_name: k8s-prod
    layout: even-vertical
    panes:
      - shell_command:
          - echo "PRODUCTION - READ-ONLY"
          - echo "DO NOT use: apply, delete, edit, patch, scale"
          - kubectl config use-context ${K8S_CTX_PRD}
          - k9s --readonly
      - shell_command:
          - watch -n 30 "kubectl top pods -n ${APP_NS} 2>/dev/null"
```

**When to use**: Managing Kubernetes across dev/staging/production.

---

## CI/CD Pipeline Management

Monitor and manage CI/CD pipelines.

```yaml
session_name: cicd-ops

windows:
  - window_name: pipelines
    focus: true
    layout: main-horizontal
    options:
      main-pane-height: 70%
    panes:
      - focus: true
        shell_command:
          - echo "Pipeline management"
          - echo "gh run list / az pipelines runs list"
      - shell_command:
          - echo "Build logs will appear here"

  - window_name: artifacts
    layout: even-horizontal
    panes:
      - shell_command:
          - echo "Docker images and artifacts"
          - docker images --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}" | head -20
      - shell_command:
          - echo "Registry operations"

  - window_name: deploy
    panes:
      - shell_command:
          - echo "Deployment operations"
          - echo "ArgoCD / Helm / kubectl"
```

**When to use**: Managing CI/CD pipelines, reviewing builds, deploying releases.

---

## Database Operations

Database management and migration workflows.

```yaml
session_name: db-ops
environment:
  DB_HOST_DEV: localhost
  DB_NAME: myapp_dev

windows:
  - window_name: db-console
    focus: true
    layout: main-vertical
    options:
      main-pane-width: 60%
    panes:
      - focus: true
        shell_command:
          - echo "Database console"
          - echo "psql / mysql / mongosh"
      - shell_command:
          - echo "Migration management"
          - echo "make db-migrate / alembic upgrade head"

  - window_name: db-monitoring
    layout: even-horizontal
    panes:
      - shell_command:
          - echo "Connection monitoring"
      - shell_command:
          - echo "Query performance"
```

**When to use**: Database administration, migrations, performance tuning.
