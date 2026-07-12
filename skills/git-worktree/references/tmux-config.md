# tmux Configuration for Git Worktrees

Optimal tmux settings for managing multiple worktree environments.

## Session Configuration

Add to `~/.tmux.conf`:

```tmux
# Window naming
set-option -g automatic-rename off
set-option -g allow-rename off

# Start windows at 1 instead of 0
set -g base-index 1
setw -g pane-base-index 1

# Renumber windows when one is closed
set -g renumber-windows on

# Status bar showing worktree info
set -g status-right '#[fg=cyan]#{pane_current_path} #[fg=white]| #[fg=yellow]%H:%M'
set -g status-right-length 100

# Window status format
setw -g window-status-format '#I:#W'
setw -g window-status-current-format '#[fg=yellow,bold]#I:#W#[fg=default]'

# Quick window switching
bind -n M-1 select-window -t 1
bind -n M-2 select-window -t 2
bind -n M-3 select-window -t 3
bind -n M-4 select-window -t 4
bind -n M-5 select-window -t 5
bind -n M-6 select-window -t 6
bind -n M-7 select-window -t 7
bind -n M-8 select-window -t 8
bind -n M-9 select-window -t 9
```

## Worktree-Specific Bindings

```tmux
# Create new worktree window (prompts for name)
bind W command-prompt -p "Worktree name:" "run-shell 'wt %%'"

# List worktrees in a popup
bind G display-popup -E "git worktree list | less"

# Quick switch to main worktree
bind M run-shell "tmux select-window -t main 2>/dev/null || tmux display 'No main window'"

# Kill worktree window and cleanup
bind X confirm-before -p "Remove worktree #W? (y/n)" "run-shell 'wt-rm #W'"
```

## Session Layout Script

Create `~/.config/tmux/worktree-session.sh`:

```bash
#!/usr/bin/env bash
# Usage: tmux-worktree-session.sh <project-path>

PROJECT_PATH="$1"
PROJECT_NAME=$(basename "$PROJECT_PATH")

# Create or attach to session
tmux has-session -t "$PROJECT_NAME" 2>/dev/null

if [ $? != 0 ]; then
    # Create session with main window
    tmux new-session -d -s "$PROJECT_NAME" -n "main" -c "$PROJECT_PATH"

    # Get existing worktrees and create windows
    cd "$PROJECT_PATH"
    git worktree list --porcelain | grep '^worktree' | while read -r line; do
        wt_path=$(echo "$line" | cut -d' ' -f2)
        wt_name=$(basename "$wt_path")

        # Skip main worktree
        if [[ "$wt_path" == "$PROJECT_PATH" ]]; then
            continue
        fi

        # Create window for each worktree
        tmux new-window -t "$PROJECT_NAME" -n "$wt_name" -c "$wt_path"
    done

    # Select main window
    tmux select-window -t "$PROJECT_NAME:main"
fi

# Attach to session
tmux attach-session -t "$PROJECT_NAME"
```

## Window Hooks

Auto-configure windows when created for worktrees:

```tmux
# Hook: when window is created for a worktree
set-hook -g after-new-window 'if-shell "git rev-parse --git-dir 2>/dev/null" "setenv -g WORKTREE_ACTIVE 1"'

# Hook: cleanup when window is destroyed
set-hook -g window-closed 'run-shell "echo Window closed: #W >> /tmp/tmux-worktree.log"'
```

## Status Bar Integration

Show worktree info in status bar:

```tmux
# Left status: session and window
set -g status-left '#[fg=green]#S #[fg=white]| '
set -g status-left-length 40

# Right status: git branch and worktree path
set -g status-right '#[fg=cyan]#(cd #{pane_current_path}; git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "no git") #[fg=white]| #[fg=yellow]#{pane_current_path}'
set -g status-right-length 120

# Update status every 5 seconds
set -g status-interval 5
```

## Pane Layouts for Worktrees

```tmux
# Preset layout: editor + terminal
bind L select-layout main-vertical \; \
       resize-pane -t 1 -x 60%

# Preset layout: equal split for code review
bind E select-layout even-horizontal

# Split and cd to same worktree
bind | split-window -h -c "#{pane_current_path}"
bind - split-window -v -c "#{pane_current_path}"
```

## fzf Integration

Quick worktree switching with fzf:

```tmux
# Switch to worktree window using fzf
bind f display-popup -E "tmux list-windows -F '#W' | fzf --reverse | xargs tmux select-window -t"

# Switch to worktree directory using fzf
bind F display-popup -E "git worktree list | fzf --reverse | awk '{print \$1}' | xargs -I{} tmux send-keys 'cd {}' Enter"
```

## Environment Variables

Pass worktree info to new windows:

```tmux
# Set environment for worktree windows
set-environment -g WORKTREE_TERMINAL "tmux"

# Update environment on attach
set -g update-environment "WORKTREE_TERMINAL"
```
