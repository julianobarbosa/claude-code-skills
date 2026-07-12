# tmuxp Best Practices

## Table of Contents

1. [Naming Conventions](#naming-conventions)
2. [Window Organization](#window-organization)
3. [Production Safety](#production-safety)
4. [Helper Scripts](#helper-scripts)
5. [Error Handling](#error-handling)
6. [Performance](#performance)
7. [File Organization](#file-organization)
8. [Common Pitfalls](#common-pitfalls)

---

## Naming Conventions

### Session Names

- Use kebab-case: `project-name`, `k8s-ops`, `dev-workspace`
- **No periods** (tmux rejects them): `juliano-dev` not `juliano.dev`
- **No colons** (tmux rejects them): `k8s-dev` not `k8s:dev`
- Keep names short and descriptive for `tmux switch-client -t name`
- Avoid `${USER}` prefix — usernames often contain periods

### Window Names

Use descriptive names. Emojis are optional but help visual scanning:

```yaml
# Without emojis (clean, functional)
- window_name: editor
- window_name: k8s-dev
- window_name: monitoring

# With emojis (visual scanning in tmux status bar)
- window_name: "editor"
- window_name: "k8s-dev"
- window_name: "monitoring"
```

### File Names

- Match the session purpose: `project-dev.yaml`, `k8s-monitoring.yaml`
- Include environment when relevant: `myapp-stg.yaml`
- Use kebab-case consistently

---

## Window Organization

### Group by Function

Organize windows by role, not by tool:

```yaml
# GOOD - grouped by function
windows:
  - window_name: develop     # Editor, tests, git
  - window_name: serve       # Dev server, hot reload
  - window_name: infra       # Terraform, cloud CLI
  - window_name: deploy      # K8s, Helm, ArgoCD
  - window_name: observe     # Logs, metrics, events

# BAD - grouped by tool
windows:
  - window_name: vim
  - window_name: kubectl
  - window_name: terraform
```

### Window Count Guidelines

| Project Type | Recommended Windows |
|-------------|-------------------|
| Simple dev | 2-3 (editor, server, terminal) |
| Full-stack | 4-5 (editor, server, tests, db, terminal) |
| Infrastructure | 3-5 (IaC, cloud, K8s, monitoring) |
| Multi-env K8s | 4-6 (per-env windows + monitoring) |
| Complex project | 8-10 max (cognitive overload beyond this) |

### Focus Management

Always set `focus: true` on the window and pane you want active on load:

```yaml
windows:
  - window_name: editor
    focus: true              # This window is active on session start
    panes:
      - focus: true          # This pane is active within the window
        shell_command:
          - vim .
      - shell_command:
          - npm test
```

---

## Production Safety

### Tiered Access Pattern

Implement increasing restrictions as environments get more critical:

```
DEV:     Full access, all commands
STAGING: Warnings displayed, careful messaging
PROD:    Read-only tools, explicit warnings, no write commands
```

### Read-Only Production

```yaml
- window_name: k8s-prod
  panes:
    - shell_command:
        - echo "PRODUCTION - READ-ONLY"
        - echo "Allowed: get, describe, logs, top"
        - echo "Forbidden: apply, delete, edit, patch, scale"
        - k9s --context $K8S_CTX_PRD --readonly
```

### Confirmation Helpers

Generate safety wrappers in before_script:

```yaml
before_script: |
  HELPER="$HOME/.tmuxp-helpers-${PROJECT_NAME}.sh"
  cat > "$HELPER" << 'SCRIPT'
  kprd() {
    echo "WARNING: Switching to PRODUCTION"
    read -p "Are you sure? (y/N) " -n 1 -r
    echo
    [[ $REPLY =~ ^[Yy]$ ]] || return 1
    kubectl config use-context "$K8S_CTX_PRD"
  }
  SCRIPT
```

---

## Helper Scripts

### Auto-Generated Helpers

Create project-specific helper scripts via before_script:

```yaml
before_script: |
  HELPER="${HOME}/.tmuxp-helpers-${PROJECT_NAME}.sh"
  if [ ! -f "$HELPER" ]; then
    cat > "$HELPER" << 'EOF'
    # Quick context switching
    kdev() { kubectl config use-context "$K8S_CTX_DEV"; }
    kstg() { kubectl config use-context "$K8S_CTX_STG"; }

    # Common operations
    pods() { kubectl get pods -n "$APP_NS" "$@"; }
    logs() { kubectl logs -n "$APP_NS" -f "$@"; }
    events() { kubectl get events -n "$APP_NS" --sort-by='.lastTimestamp'; }

    # Help
    project-help() {
      echo "Available commands:"
      echo "  kdev/kstg  - Switch K8s context"
      echo "  pods       - List pods"
      echo "  logs       - Tail logs"
      echo "  events     - Show events"
    }
    EOF
    echo "Helper script created: $HELPER"
  fi
```

### shell_command_before for Auto-Loading

```yaml
windows:
  - window_name: k8s
    shell_command_before:
      - source "$HOME/.tmuxp-helpers-${PROJECT_NAME}.sh" 2>/dev/null
    panes:
      - kubectl get pods
```

---

## Error Handling

### Graceful Failures in Panes

Always handle missing tools or connectivity issues:

```yaml
panes:
  # GOOD - handles failure gracefully
  - shell_command:
      - kubectl get pods 2>/dev/null || echo "Cannot connect to cluster"
      - command -v stern >/dev/null && stern ".*" || kubectl logs -f --tail=50

  # BAD - crashes or shows raw errors
  - shell_command:
      - kubectl get pods
      - stern ".*"
```

### before_script Validation Levels

```yaml
before_script: |
  # CRITICAL - abort if missing
  [ -d "$PROJECT_ROOT" ] || { echo "Error: project not found"; exit 1; }

  # IMPORTANT - warn but continue
  command -v kubectl >/dev/null || echo "Warning: kubectl not found"

  # NICE TO HAVE - silent fallback
  command -v stern >/dev/null 2>&1  # Used later with fallback
```

### Common Validation Checks

```bash
# Directory exists
[ -d "$PROJECT_ROOT" ] || exit 1

# Tool available
command -v kubectl >/dev/null || echo "Warning: kubectl missing"

# Cloud authenticated
az account show >/dev/null 2>&1 || echo "Warning: Not logged into Azure"

# K8s cluster reachable
kubectl cluster-info >/dev/null 2>&1 || echo "Warning: Cluster unreachable"

# Docker running
docker info >/dev/null 2>&1 || echo "Warning: Docker not running"

# Git repo valid
[ -d .git ] || echo "Warning: Not a git repository"
```

---

## Performance

### Avoid Slow Commands in Panes

Commands in panes run sequentially. Slow commands block the pane:

```yaml
# BAD - blocks pane for seconds
panes:
  - shell_command:
      - az resource list -g mygroup -o table   # 5+ seconds
      - kubectl get pods                        # Waits for above

# GOOD - fast startup, run slow commands on demand
panes:
  - shell_command:
      - echo "Run: az resource list -g mygroup -o table"
      - echo "Run: kubectl get pods"
```

### Use watch for Polling (Not Loops)

```yaml
# GOOD - built-in, clean exit with Ctrl+C
- watch -n 5 "kubectl get pods"

# OK for complex logic - but harder to interrupt
- while true; do kubectl get pods; sleep 5; done
```

### Detached Loading for Testing

```bash
# Test config without attaching
tmuxp load -d config.yaml

# Then attach if it worked
tmux attach -t session-name
```

---

## File Organization

### For Small Collections (< 20 configs)

Flat structure in `~/.tmuxp/`:

```
~/.tmuxp/
├── project-a.yaml
├── project-b.yaml
├── k8s-ops.yaml
└── monitoring.yaml
```

### For Large Collections (20+ configs)

Group by category:

```
~/.tmuxp/
├── dev/
│   ├── webapp.yaml
│   └── api.yaml
├── infra/
│   ├── terraform.yaml
│   └── k8s-ops.yaml
├── client-name/
│   ├── project-a.yaml
│   └── project-b.yaml
└── monitoring.yaml
```

Load grouped configs: `tmuxp load infra/k8s-ops.yaml`

### Version Control

Store configs in a dotfiles repo managed by GNU Stow or similar:

```
dotfiles/
└── tmuxp/
    └── .tmuxp/
        ├── project.yaml
        └── ...
```

---

## Common Pitfalls

| Pitfall | Problem | Solution |
|---------|---------|----------|
| `${USER}` in session_name | Usernames with periods break tmux | Use static names |
| Missing quotes on special chars | YAML parsing errors | Quote strings with `:`, `#`, `{`, `}` |
| Hardcoded paths | Config not portable | Use `${HOME}`, `${PROJECT_ROOT}` |
| Too many windows | Cognitive overload | Max 8-10 windows per session |
| No error handling | Broken panes on tool absence | Always use `|| echo "fallback"` |
| Slow pane commands | Blocked panes on load | Use echo + manual run for slow ops |
| No before_script validation | Session loads with broken deps | Validate critical tools and paths |
| Prod without safety guards | Accidental destructive commands | Read-only tools + warnings |
| Custom layout strings | Break on different terminal sizes | Prefer predefined layouts |
| `suppress_history: true` | Hard to debug command issues | Use `false` during development |
