# tmux Integration for Worktrees

Advanced tmux configuration and shell functions for worktree management.

## Recommended tmux.conf Settings

```tmux
# Prevent automatic window renaming (keeps worktree names stable)
set-option -g automatic-rename off
set-option -g allow-rename off

# Start windows at 1
set -g base-index 1
setw -g pane-base-index 1

# Renumber windows when one is closed
set -g renumber-windows on

# Status bar showing git branch and path
set -g status-right '#[fg=cyan]#(cd #{pane_current_path}; git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "no git") #[fg=white]| #[fg=yellow]#{pane_current_path}'
set -g status-right-length 120
set -g status-interval 5

# Quick window switching with Alt+number
bind -n M-1 select-window -t 1
bind -n M-2 select-window -t 2
bind -n M-3 select-window -t 3
bind -n M-4 select-window -t 4
bind -n M-5 select-window -t 5
```

## Worktree-Specific Bindings

```tmux
# List worktrees in a popup
bind G display-popup -E "git worktree list | less"

# Switch to worktree window using fzf
bind f display-popup -E "tmux list-windows -F '#W' | fzf --reverse | xargs tmux select-window -t"

# Split and cd to same worktree
bind | split-window -h -c "#{pane_current_path}"
bind - split-window -v -c "#{pane_current_path}"
```

## Shell Functions

Add to `~/.zshrc` or `~/.bashrc`:

```bash
# Create worktree with tmux window in current session
wt() {
    local name="$1"
    local base_branch="${2:-main}"
    local repo_root=$(git rev-parse --show-toplevel 2>/dev/null)

    if [[ -z "$repo_root" ]]; then
        echo "Error: Not in a git repository"
        return 1
    fi

    local worktree_path="$repo_root/.claude/worktrees/$name"
    mkdir -p "$repo_root/.claude/worktrees"

    # Create worktree
    if git worktree add -b "$name" "$worktree_path" "$base_branch" 2>/dev/null; then
        echo "Created worktree: $name"
    elif git worktree add "$worktree_path" "$name" 2>/dev/null; then
        echo "Attached to existing branch: $name"
    else
        echo "Error: Failed to create worktree"
        return 1
    fi

    # tmux window in current session
    if [[ -n "$TMUX" ]]; then
        local session=$(tmux display-message -p '#S')
        tmux new-window -n "${session}-${name}" -c "$worktree_path"
        echo "Created tmux window: ${session}-${name}"
    else
        cd "$worktree_path"
    fi
}

# Remove worktree and tmux window
wt-rm() {
    local name="$1"
    local repo_root=$(git rev-parse --show-toplevel 2>/dev/null)
    local worktree_path="$repo_root/.claude/worktrees/$name"

    git worktree remove "$worktree_path" --force 2>/dev/null

    if [[ -n "$TMUX" ]]; then
        local session=$(tmux display-message -p '#S')
        tmux kill-window -t "${session}-${name}" 2>/dev/null
    fi

    git branch -d "$name" 2>/dev/null
    echo "Removed worktree: $name"
}

# List worktrees
wt-ls() { git worktree list; }

# Status of all worktrees
wt-status() {
    git worktree list | while read -r line; do
        local wt_path=$(echo "$line" | awk '{print $1}')
        local wt_branch=$(echo "$line" | awk '{print $3}' | tr -d '[]')
        local status=$(cd "$wt_path" 2>/dev/null && git status --porcelain | wc -l | tr -d ' ')
        if [[ "$status" -gt 0 ]]; then
            echo "$wt_branch: $status uncommitted changes"
        else
            echo "$wt_branch: clean"
        fi
    done
}

# Cleanup merged worktrees
wt-cleanup-merged() {
    git worktree list | tail -n +2 | while read -r line; do
        local wt_path=$(echo "$line" | awk '{print $1}')
        local wt_branch=$(echo "$line" | awk '{print $3}' | tr -d '[]')
        if git branch --merged main 2>/dev/null | grep -q "$wt_branch"; then
            echo "Removing merged: $wt_branch"
            git worktree remove "$wt_path" --force 2>/dev/null
            git branch -d "$wt_branch" 2>/dev/null
        fi
    done
}
```

## Shell Completions (zsh)

```zsh
_wt_completion() {
    local branches=$(git branch --format='%(refname:short)' 2>/dev/null)
    local worktrees=$(git worktree list --porcelain 2>/dev/null | grep '^worktree' | cut -d' ' -f2 | xargs -I{} basename {} 2>/dev/null)
    _alternative \
        "branches:branch:($branches)" \
        "worktrees:worktree:($worktrees)"
}
compdef _wt_completion wt wt-rm
```
