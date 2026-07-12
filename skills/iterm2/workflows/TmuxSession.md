# TmuxSession Workflow

Manage tmux sessions for persistent terminal work.

## Use Cases

- Keep processes running after terminal close
- Maintain work context across SSH disconnects
- Organize multiple projects in separate sessions

## Session Operations

### Create New Session

**Named session (recommended):**
```bash
# Standard tmux
tmux new -s projectname

# iTerm2 integration mode
tmux -CC new -s projectname
```

**With initial command:**
```bash
tmux new -s dev -n editor "vim"
```

### List Sessions

```bash
# From command line
tmux ls

# From within tmux
Ctrl+b s  # Interactive session list
```

### Attach to Session

```bash
# Standard tmux
tmux attach -t projectname
tmux a -t projectname  # Short form

# iTerm2 integration mode
tmux -CC attach -t projectname

# Attach to most recent
tmux attach
tmux -CC attach
```

### Detach from Session

**Standard tmux:**
- `Ctrl+b d`

**iTerm2 integration:**
- Press `Esc`
- Or Shell > tmux > Detach

### Switch Between Sessions

From within tmux:
- `Ctrl+b s` - Interactive session list
- `Ctrl+b (` - Previous session
- `Ctrl+b )` - Next session

### Rename Session

```bash
# From command line
tmux rename-session -t old_name new_name

# From within session
Ctrl+b $
```

### Kill Session

```bash
# Specific session
tmux kill-session -t projectname

# All except current
tmux kill-session -a

# All sessions
tmux kill-server
```

## Session Workflows

### Project-Based Sessions

Create dedicated sessions per project:

```bash
# Work projects
tmux new -s work-api
tmux new -s work-frontend
tmux new -s work-docs

# Personal
tmux new -s dotfiles
tmux new -s learning

# List all
tmux ls
```

### Multi-Window Session Setup

```bash
# Create session with first window
tmux new -s myproject -n editor -d

# Add more windows
tmux new-window -t myproject -n server
tmux new-window -t myproject -n logs

# Attach to it
tmux attach -t myproject
```

### SSH Persistent Sessions

For remote work that survives disconnects:

```bash
# On remote server
ssh myserver

# Create or attach to session
tmux new -A -s main

# Do your work...

# Disconnect (Ctrl+b d or close terminal)
# Session keeps running

# Reconnect later
ssh myserver
tmux attach -t main
# You're right where you left off
```

### iTerm2 Integration for SSH

**Important:** `tmux -CC` integration mode only works when tmux runs locally on your Mac. For remote servers, use standard tmux mode.

```bash
# LOCAL machine - can use integration mode
tmux -CC

# REMOTE server - use standard tmux
ssh myserver
tmux new -s main      # Standard mode, not -CC

# Why? The -CC protocol requires iTerm2 to communicate
# directly with tmux. Over SSH, use standard tmux shortcuts.
```

**Hybrid approach for persistent remote work:**
```bash
# SSH to server
ssh myserver

# Use standard tmux on remote
tmux new -A -s main

# Your session persists across:
# - SSH disconnects
# - Network changes
# - Terminal crashes

# Reconnect later
ssh myserver
tmux attach -t main
# You're right where you left off
```

## Best Practices

1. **Always name sessions** - Makes management easier
2. **Use integration mode** - `tmux -CC` for best iTerm2 experience
3. **Detach, don't quit** - Session survives for later
4. **One session per project** - Clean context switching
5. **Regular cleanup** - Kill unused sessions

## Quick Reference

| Action | Command |
|--------|---------|
| New named session | `tmux new -s name` |
| List sessions | `tmux ls` |
| Attach | `tmux attach -t name` |
| Detach | `Ctrl+b d` or `Esc` (iTerm2) |
| Switch session | `Ctrl+b s` |
| Kill session | `tmux kill-session -t name` |
| iTerm2 mode | `tmux -CC` |
| iTerm2 attach | `tmux -CC attach` |
