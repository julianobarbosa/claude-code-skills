#!/usr/bin/env bash
# Git Worktree Shell Functions
# Source this file in ~/.zshrc or ~/.bashrc
# Usage: source ~/.config/git-worktree/functions.sh

# Configuration
export WORKTREE_TERMINAL="${WORKTREE_TERMINAL:-auto}"  # auto, tmux, iterm2, basic

# Detect terminal environment
_wt_detect_terminal() {
    if [[ "$WORKTREE_TERMINAL" != "auto" ]]; then
        echo "$WORKTREE_TERMINAL"
    elif [[ -n "$TMUX" ]]; then
        echo "tmux"
    elif [[ "$TERM_PROGRAM" == "iTerm.app" ]]; then
        echo "iterm2"
    else
        echo "basic"
    fi
}

# Get repository root and name
_wt_repo_info() {
    local root
    root=$(git rev-parse --show-toplevel 2>/dev/null) || return 1
    echo "$root"
}

_wt_repo_name() {
    local root
    root=$(_wt_repo_info) || return 1
    basename "$root"
}

# Main worktree creation function
wt() {
    local name="$1"
    local base_branch="${2:-main}"

    if [[ -z "$name" ]]; then
        echo "Usage: wt <worktree-name> [base-branch]"
        echo "       wt feature-auth main"
        return 1
    fi

    local repo_root
    repo_root=$(_wt_repo_info) || {
        echo "Error: Not in a git repository"
        return 1
    }

    local worktree_path="$repo_root/.worktrees/$name"

    # Create worktree directory
    mkdir -p "$repo_root/.worktrees"

    # Create worktree with new branch
    if git worktree add -b "$name" "$worktree_path" "$base_branch" 2>/dev/null; then
        echo "Created worktree with new branch: $name"
    elif git worktree add "$worktree_path" "$name" 2>/dev/null; then
        echo "Attached to existing branch: $name"
    else
        echo "Error: Failed to create worktree '$name'"
        echo "Hint: Check if branch exists or worktree path is in use"
        return 1
    fi

    # Terminal-specific handling
    case "$(_wt_detect_terminal)" in
        tmux)
            _wt_tmux_window "$name" "$worktree_path"
            ;;
        iterm2)
            _wt_iterm2_tab "$name" "$worktree_path"
            ;;
        basic)
            cd "$worktree_path" || return 1
            echo "Changed to: $worktree_path"
            ;;
    esac
}

# tmux window creation
_wt_tmux_window() {
    local name="$1"
    local path="$2"

    # Create new window with worktree name
    tmux new-window -n "$name" -c "$path"
    echo "Created tmux window: $name"
}

# iTerm2 tab creation
_wt_iterm2_tab() {
    local name="$1"
    local path="$2"

    osascript - "$path" "$name" <<'APPLESCRIPT'
on run argv
    set worktreePath to item 1 of argv
    set worktreeName to item 2 of argv
    tell application "iTerm2"
        tell current window
            create tab with default profile
            tell current session
                set name to worktreeName
                write text "cd '" & worktreePath & "' && clear"
            end tell
        end tell
    end tell
end run
APPLESCRIPT

    echo "Created iTerm2 tab: $name"
}

# Remove worktree
wt-rm() {
    local name="$1"

    if [[ -z "$name" ]]; then
        echo "Usage: wt-rm <worktree-name>"
        return 1
    fi

    local repo_root
    repo_root=$(_wt_repo_info) || {
        echo "Error: Not in a git repository"
        return 1
    }

    local worktree_path="$repo_root/.worktrees/$name"

    # Check if worktree exists
    if [[ ! -d "$worktree_path" ]]; then
        echo "Error: Worktree '$name' not found at $worktree_path"
        return 1
    fi

    # Remove git worktree
    git worktree remove "$worktree_path" --force 2>/dev/null || {
        echo "Warning: Failed to remove worktree, forcing prune"
        rm -rf "$worktree_path"
        git worktree prune
    }

    # Terminal-specific cleanup
    case "$(_wt_detect_terminal)" in
        tmux)
            tmux kill-window -t "$name" 2>/dev/null
            echo "Closed tmux window: $name"
            ;;
        iterm2)
            _wt_iterm2_close_tab "$name"
            echo "Closed iTerm2 tab: $name"
            ;;
    esac

    # Optionally delete branch
    git branch -d "$name" 2>/dev/null && echo "Deleted branch: $name"

    echo "Removed worktree: $name"
}

# Close iTerm2 tab by name
_wt_iterm2_close_tab() {
    local name="$1"

    osascript - "$name" <<'APPLESCRIPT'
on run argv
    set tabName to item 1 of argv
    tell application "iTerm2"
        tell current window
            repeat with t in tabs
                tell t
                    repeat with s in sessions
                        if name of s is tabName then
                            close s
                            return
                        end if
                    end repeat
                end tell
            end repeat
        end tell
    end tell
end run
APPLESCRIPT
}

# List worktrees
wt-ls() {
    local repo_root
    repo_root=$(_wt_repo_info) || {
        echo "Error: Not in a git repository"
        return 1
    }

    echo "Git Worktrees:"
    echo "=============="
    git worktree list
    echo ""
    echo "Worktree directory: $repo_root/.worktrees"
}

# Switch to worktree
wt-cd() {
    local name="$1"

    if [[ -z "$name" ]]; then
        echo "Usage: wt-cd <worktree-name>"
        return 1
    fi

    local repo_root
    repo_root=$(_wt_repo_info) || {
        echo "Error: Not in a git repository"
        return 1
    }

    local worktree_path="$repo_root/.worktrees/$name"

    if [[ -d "$worktree_path" ]]; then
        cd "$worktree_path" || return 1
        echo "Changed to: $worktree_path"
    else
        echo "Error: Worktree '$name' not found"
        return 1
    fi
}

# Create tmux session for worktree
wt-session() {
    local name="$1"
    local base_branch="${2:-main}"

    if [[ -z "$name" ]]; then
        echo "Usage: wt-session <session-name> [base-branch]"
        return 1
    fi

    # Create worktree first (without terminal integration)
    local original_terminal="$WORKTREE_TERMINAL"
    export WORKTREE_TERMINAL="basic"
    wt "$name" "$base_branch"
    export WORKTREE_TERMINAL="$original_terminal"

    local repo_root
    repo_root=$(_wt_repo_info)
    local worktree_path="$repo_root/.worktrees/$name"

    # Create or attach to tmux session
    if tmux has-session -t "$name" 2>/dev/null; then
        tmux attach-session -t "$name"
    else
        tmux new-session -d -s "$name" -c "$worktree_path"
        tmux attach-session -t "$name"
    fi
}

# Cleanup merged worktrees
wt-cleanup() {
    local name="$1"

    if [[ -z "$name" ]]; then
        echo "Usage: wt-cleanup <worktree-name>"
        return 1
    fi

    local repo_root
    repo_root=$(_wt_repo_info) || {
        echo "Error: Not in a git repository"
        return 1
    }

    # Switch to main worktree
    cd "$repo_root" || return 1

    # Update main
    git fetch origin
    git pull origin main 2>/dev/null || git pull origin master 2>/dev/null

    # Remove worktree
    wt-rm "$name"
}

# Cleanup all merged worktrees
wt-cleanup-merged() {
    local main_dir
    main_dir=$(git worktree list | head -1 | awk '{print $1}')

    echo "Scanning for merged worktrees..."

    git worktree list | tail -n +2 | while read -r line; do
        local wt_path wt_branch
        wt_path=$(echo "$line" | awk '{print $1}')
        wt_branch=$(echo "$line" | awk '{print $3}' | tr -d '[]')

        if git branch --merged main 2>/dev/null | grep -q "$wt_branch"; then
            echo "Removing merged worktree: $wt_branch"
            git worktree remove "$wt_path" --force 2>/dev/null
            git branch -d "$wt_branch" 2>/dev/null
        fi
    done

    echo "Cleanup complete"
}

# Prune stale worktrees
wt-prune() {
    echo "Pruning stale worktrees..."
    git worktree prune -v
    echo "Done"
}

# Status of all worktrees
wt-status() {
    echo "Worktree Status:"
    echo "================"

    git worktree list | while read -r line; do
        local wt_path wt_branch
        wt_path=$(echo "$line" | awk '{print $1}')
        wt_branch=$(echo "$line" | awk '{print $3}' | tr -d '[]')

        echo ""
        echo "📁 $wt_branch ($wt_path)"

        (
            cd "$wt_path" 2>/dev/null || exit
            local status
            status=$(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')
            if [[ "$status" -gt 0 ]]; then
                echo "   ⚠️  $status uncommitted changes"
            else
                echo "   ✅ Clean"
            fi

            local ahead behind
            ahead=$(git rev-list --count HEAD@{upstream}..HEAD 2>/dev/null || echo "0")
            behind=$(git rev-list --count HEAD..HEAD@{upstream} 2>/dev/null || echo "0")

            if [[ "$ahead" -gt 0 ]] || [[ "$behind" -gt 0 ]]; then
                echo "   📊 ↑$ahead ↓$behind"
            fi
        )
    done
}

# Shell completions for zsh
if [[ -n "$ZSH_VERSION" ]]; then
    _wt_completion() {
        local branches worktrees
        branches=$(git branch --format='%(refname:short)' 2>/dev/null)
        worktrees=$(git worktree list --porcelain 2>/dev/null | grep '^worktree' | cut -d' ' -f2 | xargs -I{} basename {} 2>/dev/null)

        _alternative \
            "branches:branch:($branches)" \
            "worktrees:worktree:($worktrees)"
    }

    compdef _wt_completion wt wt-rm wt-cd wt-cleanup
fi

# Shell completions for bash
if [[ -n "$BASH_VERSION" ]]; then
    _wt_completion_bash() {
        local cur="${COMP_WORDS[COMP_CWORD]}"
        local branches worktrees

        branches=$(git branch --format='%(refname:short)' 2>/dev/null)
        worktrees=$(git worktree list --porcelain 2>/dev/null | grep '^worktree' | cut -d' ' -f2 | xargs -I{} basename {} 2>/dev/null)

        COMPREPLY=($(compgen -W "$branches $worktrees" -- "$cur"))
    }

    complete -F _wt_completion_bash wt wt-rm wt-cd wt-cleanup
fi

# Aliases
alias wtl='wt-ls'
alias wtr='wt-rm'
alias wtc='wt-cd'
alias wts='wt-status'
alias wtp='wt-prune'

echo "Git worktree functions loaded. Type 'wt --help' or 'wt-ls' to get started."
