---
name: tmux
description: "tmux and tmuxp session configuration, management, and troubleshooting. Use when creating, editing, debugging, or optimizing tmuxp YAML configs, designing tmux workspace layouts, fixing tmux session errors, managing multi-environment terminal setups, or working with tmux panes, windows, and sessions. Also use when the user mentions tmuxp, .tmuxp, tmux layouts, session_name, or terminal workspace organization."
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
---

# tmux & tmuxp Skill

Create, edit, debug, and optimize tmux sessions via tmuxp YAML configurations.

## Quick Decisions

| Task | Approach |
|------|----------|
| **New project workspace** | Create tmuxp YAML from template |
| **Fix session load error** | Check session_name, YAML syntax, tool availability |
| **Multi-environment K8s** | Use environment vars + per-env windows with safety guards |
| **Simple dev setup** | 2-3 windows: editor, server, terminal |
| **Complex infra** | before_script validation + helper scripts + monitoring windows |
| **Capture existing layout** | `tmuxp freeze` then clean up the output |

## Session Name Rules

tmux session names **cannot contain periods (`.`) or colons (`:`)**.

Common pitfall: using `${USER}` in session_name when the username contains periods (e.g., `first.last`). Always use a static name or sanitize:

```yaml
# BAD - breaks if USER contains periods
session_name: ${USER}-project

# GOOD - static name
session_name: project-dev

# GOOD - sanitized
session_name: project-${USER//\./-}
```

## Configuration Structure

```yaml
session_name: project-name          # Required. No periods or colons.
start_directory: ~/Projects/foo     # Default working dir for all windows
environment:                        # Session-wide env vars
  PROJECT_ROOT: ~/Projects/foo
suppress_history: false             # Whether to hide commands from shell history

before_script: |                    # Runs before session creation. Exit 1 = abort.
  echo "Validating..."

after_script: |                     # Runs after session is destroyed
  echo "Cleaning up..."

windows:
  - window_name: editor             # Window identifier
    focus: true                     # Make this the active window on load
    layout: main-vertical           # Pane layout
    start_directory: ~/Projects/foo/src
    options:
      main-pane-width: 70%          # Layout-specific options
    shell_command_before:            # Runs in ALL panes before pane commands
      - source ~/.zshrc
    panes:
      - focus: true                 # Active pane within window
        shell_command:
          - vim .
      - shell_command:
          - npm test -- --watch
```

## Layouts

| Layout | Use For | Pane Arrangement |
|--------|---------|------------------|
| `main-vertical` | Editor + sidebars | Large left, stacked right |
| `main-horizontal` | Logs + status | Large top, split bottom |
| `even-horizontal` | Equal side-by-side | Equal horizontal splits |
| `even-vertical` | Equal stacked | Equal vertical splits |
| `tiled` | Monitoring dashboards | Grid of equal panes |

Control main pane size via options:
```yaml
options:
  main-pane-width: 70%    # For main-vertical
  main-pane-height: 65%   # For main-horizontal
```

Capture a custom layout from a running session:
```bash
tmux display-message -p '#{window_layout}'
# Returns: "bb62,159x48,0,0{79x48,0,0,79x48,80,0}"
```

## Pane Definitions

```yaml
panes:
  # Simple command
  - vim README.md

  # Multiple commands
  - shell_command:
      - cd ~/project
      - source .venv/bin/activate
      - python app.py

  # Empty pane
  - null     # or: blank, pane

  # With focus
  - focus: true
    shell_command:
      - k9s
```

## Environment Variables

```yaml
environment:
  # Static values
  PROJECT_NAME: my-app

  # Reference existing vars (expanded at load time)
  HOME_DIR: ${HOME}

  # Multi-environment pattern
  K8S_CTX_DEV: aks-myapp-dev
  K8S_CTX_STG: aks-myapp-stg
  K8S_CTX_PRD: aks-myapp-prd

  # Defaults
  EDITOR: ${EDITOR:-vim}
```

Never hardcode secrets. Reference env vars from the shell: `${AZURE_SUBSCRIPTION_ID}`.

## before_script Validation

Use before_script to validate prerequisites. Exit 1 aborts session creation:

```yaml
before_script: |
  # Check project exists
  [ -d "$PROJECT_ROOT" ] || { echo "Project not found"; exit 1; }

  # Check required tools
  for tool in kubectl terraform docker; do
    command -v $tool >/dev/null || echo "Warning: $tool not found"
  done

  # Check connectivity
  kubectl cluster-info >/dev/null 2>&1 || echo "Warning: Cannot reach cluster"
```

## Production Safety Patterns

Protect production environments with read-only access and warnings:

```yaml
- window_name: k8s-prod
  panes:
    - shell_command:
        - echo "PRODUCTION - READ-ONLY ACCESS"
        - echo "DO NOT use: apply, delete, edit, patch"
        - kubectl config use-context $K8S_CTX_PRD
        - k9s --readonly
```

## CLI Commands

```bash
tmuxp load config-name          # Load from ~/.tmuxp/
tmuxp load ./path/to/file.yaml  # Load from path
tmuxp load -y config-name       # Skip confirmation prompt
tmuxp load -d config-name       # Load detached (background)
tmuxp ls                        # List available configs
tmuxp freeze session-name       # Capture running session to YAML
tmuxp convert file.json         # Convert JSON config to YAML
tmuxp edit config-name          # Edit config in $EDITOR
tmuxp debug-info                # Show environment info
```

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `BadSessionName: contains periods` | `session_name` has `.` (often from `${USER}`) | Remove `${USER}` prefix or sanitize |
| `BadSessionName: contains colons` | `session_name` has `:` | Remove colons from name |
| Session already exists | Duplicate session_name | Kill old: `tmux kill-session -t name` |
| Commands not executing | Shell compatibility | Test commands manually first |
| Layout broken | Terminal too small for layout | Use predefined layouts or test with `tmuxp load -d` |
| Env vars not expanding | Wrong syntax | Use `${VAR}` not `$VAR` in YAML values |

Debug: `tmuxp -v load config.yaml` for verbose output.

## References

- [WORKFLOWS.md](references/WORKFLOWS.md) - Common workflow patterns (dev, infra, monitoring)
- [BEST-PRACTICES.md](references/BEST-PRACTICES.md) - Production patterns, safety, organization
- [templates/](templates/) - Ready-to-use config templates

## Workflow: Create New Config

1. Identify the project type (dev, infra, monitoring, mixed)
2. Choose a template from `templates/`
3. Set session_name (no periods/colons), start_directory, environment vars
4. Design windows by function (editor, server, logs, k8s, etc.)
5. Pick layouts matching each window's purpose
6. Add before_script validation if the project has external dependencies
7. Add production safety guards for any prod-access windows
8. Test: `tmuxp load -d config.yaml` then `tmux attach -t session-name`
