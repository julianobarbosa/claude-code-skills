# iTerm2 Configuration for Git Worktrees

iTerm2 setup for seamless worktree management with tabs, profiles, and automation.

## Profile Setup

### Create Worktree Profile

1. Open iTerm2 Preferences (`Cmd + ,`)
2. Go to Profiles > + (Add new profile)
3. Configure:

```
Name: Worktree
Badge: WT: \(session.name)
Working Directory: Advanced Configuration
  - Working Directory for New Tabs: Reuse previous session's directory
Title: \(session.name) - \(path)
```

### Profile JSON Export

Save to `~/.config/iterm2/worktree-profile.json`:

```json
{
  "Name": "Worktree",
  "Guid": "worktree-profile-guid",
  "Badge Text": "WT: \\(session.name)",
  "Custom Directory": "Recycle",
  "Working Directory": ".worktrees",
  "Title Components": 2,
  "Custom Window Title": "Worktree",
  "Use Custom Window Title": true,
  "Terminal Type": "xterm-256color",
  "Scrollback Lines": 10000,
  "Unlimited Scrollback": false,
  "Close Sessions On End": true,
  "Jobs to Ignore": ["rlogin", "ssh", "slogin", "telnet"],
  "Triggers": [
    {
      "partial": true,
      "regex": "^\\[WORKTREE\\]",
      "action": "HighlightTextTrigger",
      "parameter": {
        "textColor": "#00FF00"
      }
    }
  ]
}
```

## AppleScript Functions

### Create Tab for Worktree

Save to `~/.config/iterm2/scripts/new-worktree-tab.applescript`:

```applescript
on run argv
    set worktreePath to item 1 of argv
    set worktreeName to item 2 of argv

    tell application "iTerm2"
        tell current window
            create tab with profile "Worktree"
            tell current session
                set name to worktreeName
                write text "cd '" & worktreePath & "' && clear && echo '[WORKTREE] " & worktreeName & " ready'"
            end tell
        end tell
    end tell
end run
```

### Create Window for Worktree

Save to `~/.config/iterm2/scripts/new-worktree-window.applescript`:

```applescript
on run argv
    set worktreePath to item 1 of argv
    set worktreeName to item 2 of argv

    tell application "iTerm2"
        create window with profile "Worktree"
        tell current session of current window
            set name to worktreeName
            write text "cd '" & worktreePath & "' && clear && echo '[WORKTREE] " & worktreeName & " ready'"
        end tell
    end tell
end run
```

### Split Pane for Worktree

```applescript
on run argv
    set worktreePath to item 1 of argv
    set direction to item 2 of argv  -- "vertical" or "horizontal"

    tell application "iTerm2"
        tell current session of current window
            if direction is "vertical" then
                set newSession to split vertically with profile "Worktree"
            else
                set newSession to split horizontally with profile "Worktree"
            end if
            tell newSession
                write text "cd '" & worktreePath & "'"
            end tell
        end tell
    end tell
end run
```

## Shell Functions

Add to `~/.zshrc`:

```zsh
# iTerm2 worktree functions
if [[ "$TERM_PROGRAM" == "iTerm.app" ]]; then

    # Create worktree with iTerm2 tab
    wt() {
        local name="$1"
        local base_branch="${2:-main}"
        local repo_root=$(git rev-parse --show-toplevel 2>/dev/null)

        if [[ -z "$repo_root" ]]; then
            echo "Error: Not in a git repository"
            return 1
        fi

        local worktree_path="$repo_root/.worktrees/$name"

        # Create worktree
        mkdir -p "$repo_root/.worktrees"
        if ! git worktree add -b "$name" "$worktree_path" "$base_branch" 2>/dev/null; then
            if ! git worktree add "$worktree_path" "$name" 2>/dev/null; then
                echo "Error: Failed to create worktree"
                return 1
            fi
        fi

        # Create iTerm2 tab
        osascript - "$worktree_path" "$name" <<'EOF'
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
EOF

        echo "Created worktree: $name"
    }

    # Remove worktree and close tab
    wt-rm() {
        local name="$1"
        local repo_root=$(git rev-parse --show-toplevel 2>/dev/null)
        local worktree_path="$repo_root/.worktrees/$name"

        # Remove git worktree
        git worktree remove "$worktree_path" --force 2>/dev/null

        # Close iTerm2 tab with matching name
        osascript - "$name" <<'EOF'
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
EOF

        git branch -d "$name" 2>/dev/null
        echo "Removed worktree: $name"
    }

fi
```

## Keyboard Shortcuts

Configure in iTerm2 Preferences > Keys > Key Bindings:

| Shortcut | Action | Command |
|----------|--------|---------|
| `Cmd+Shift+W` | New Worktree Tab | Run AppleScript: `new-worktree-tab.applescript` |
| `Cmd+Shift+N` | New Worktree Window | Run AppleScript: `new-worktree-window.applescript` |
| `Cmd+Shift+L` | List Worktrees | Send text: `git worktree list\n` |

## Tab Colors

Distinguish worktree tabs by color:

```zsh
# Set iTerm2 tab color based on worktree
iterm2_set_tab_color() {
    local r=$1 g=$2 b=$3
    printf "\033]6;1;bg;red;brightness;%d\a" "$r"
    printf "\033]6;1;bg;green;brightness;%d" "$g"
    printf "\033]6;1;bg;blue;brightness;%d\a" "$b"
}

# Color coding for worktree types
wt-color() {
    local name=$(basename "$PWD")
    case "$name" in
        feature-*) iterm2_set_tab_color 50 150 50 ;;   # Green for features
        bugfix-*)  iterm2_set_tab_color 200 100 50 ;;  # Orange for bugfixes
        hotfix-*)  iterm2_set_tab_color 200 50 50 ;;   # Red for hotfixes
        *)         iterm2_set_tab_color 100 100 200 ;; # Blue for others
    esac
}

# Auto-color on directory change
chpwd_functions+=(wt-color)
```

## Badge Configuration

Show worktree info in tab badge:

```zsh
# Update iTerm2 badge with worktree info
iterm2_set_badge() {
    printf "\033]1337;SetBadgeFormat=%s\007" "$(echo -n "$1" | base64)"
}

# Set badge when entering worktree
wt-badge() {
    if git rev-parse --git-dir > /dev/null 2>&1; then
        local branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
        local wt=$(basename "$PWD")
        iterm2_set_badge "WT: $wt\n$branch"
    fi
}

# Auto-update badge on directory change
chpwd_functions+=(wt-badge)
```

## Triggers

Add triggers to highlight worktree-related output:

In iTerm2 Preferences > Profiles > Worktree > Advanced > Triggers:

| Regex | Action | Parameter |
|-------|--------|-----------|
| `^\[WORKTREE\]` | Highlight Text | Green |
| `^Created worktree:` | Post Notification | Worktree Created |
| `^Removed worktree:` | Post Notification | Worktree Removed |
| `fatal:.*worktree` | Highlight Text | Red |

## Integration with tmux

When running tmux inside iTerm2:

```zsh
# Detect environment and use appropriate method
wt() {
    if [[ -n "$TMUX" ]]; then
        # Use tmux window
        wt-tmux "$@"
    elif [[ "$TERM_PROGRAM" == "iTerm.app" ]]; then
        # Use iTerm2 tab
        wt-iterm "$@"
    else
        # Fallback: just create worktree and cd
        wt-basic "$@"
    fi
}
```
