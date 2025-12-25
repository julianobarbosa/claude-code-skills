# Keyboard Shortcuts Reference

Complete keyboard shortcuts for iTerm2 and tmux.

## iTerm2 Shortcuts

### Window & Tab Management

| Action | Shortcut |
|--------|----------|
| New Window | `Cmd+N` |
| New Tab | `Cmd+T` |
| Close Tab/Window | `Cmd+W` |
| Next Tab | `Cmd+}` or `Cmd+Shift+]` |
| Previous Tab | `Cmd+{` or `Cmd+Shift+[` |
| Go to Tab 1-9 | `Cmd+1` through `Cmd+9` |
| Go to Window 1-9 | `Cmd+Option+1` through `Cmd+Option+9` |
| Full Screen | `Cmd+Enter` |
| Undo Close Session | `Cmd+Z` |

### Split Panes

| Action | Shortcut |
|--------|----------|
| Split Vertically | `Cmd+D` |
| Split Horizontally | `Cmd+Shift+D` |
| Navigate to Pane | `Cmd+Option+Arrow` |
| Navigate Previous Pane | `Cmd+[` |
| Navigate Next Pane | `Cmd+]` |
| Maximize Current Pane | `Cmd+Shift+Enter` |
| Close Pane | `Cmd+W` |
| Move Pane to New Tab | Drag pane title bar |
| Move Pane to New Window | `Cmd+Shift+Option+Drag` |

### Search & Selection

| Action | Shortcut |
|--------|----------|
| Find | `Cmd+F` |
| Find Next | `Cmd+G` |
| Find Previous | `Cmd+Shift+G` |
| Select All | `Cmd+A` |
| Open Selection | `Cmd+Shift+O` |
| Autocomplete | `Cmd+;` |
| Open Paste History | `Cmd+Shift+H` |

### Shell Integration

| Action | Shortcut |
|--------|----------|
| Mark Current Location | `Cmd+Shift+M` |
| Jump to Mark | `Cmd+Shift+J` |
| Previous Mark/Prompt | `Cmd+Shift+Up` |
| Next Mark/Prompt | `Cmd+Shift+Down` |
| Alert on Next Mark | `Cmd+Option+A` |

### Utilities

| Action | Shortcut |
|--------|----------|
| Clear Buffer | `Cmd+K` |
| Clear to Start of Line | `Ctrl+U` |
| Instant Replay | `Cmd+Option+B` |
| Find Cursor | `Cmd+/` |
| Show Timestamps | View > Show Timestamps |
| Broadcast Input (all panes) | Shell > Broadcast Input |
| Open Quickly | `Cmd+Shift+O` |
| Composer (AI) | `Cmd+Shift+.` |

### Text Manipulation

| Action | Shortcut |
|--------|----------|
| Copy | `Cmd+C` |
| Paste | `Cmd+V` |
| Paste Escaped | `Cmd+Option+V` |
| Paste Slowly | Advanced Paste menu |
| Font Size Increase | `Cmd++` |
| Font Size Decrease | `Cmd+-` |
| Reset Font Size | `Cmd+0` |

## tmux Shortcuts

Default prefix key: `Ctrl+b`

### Sessions

| Action | Shortcut |
|--------|----------|
| New Session | `tmux new -s name` |
| Detach | `Ctrl+b d` |
| List Sessions | `Ctrl+b s` |
| Rename Session | `Ctrl+b $` |
| Previous Session | `Ctrl+b (` |
| Next Session | `Ctrl+b )` |
| Kill Session | `tmux kill-session -t name` |

### Windows

| Action | Shortcut |
|--------|----------|
| New Window | `Ctrl+b c` |
| Close Window | `Ctrl+b &` |
| Rename Window | `Ctrl+b ,` |
| List Windows | `Ctrl+b w` |
| Next Window | `Ctrl+b n` |
| Previous Window | `Ctrl+b p` |
| Go to Window 0-9 | `Ctrl+b 0` through `Ctrl+b 9` |
| Last Active Window | `Ctrl+b l` |
| Find Window | `Ctrl+b f` |

### Panes

| Action | Shortcut |
|--------|----------|
| Split Vertically | `Ctrl+b %` |
| Split Horizontally | `Ctrl+b "` |
| Navigate Panes | `Ctrl+b Arrow` |
| Next Pane | `Ctrl+b o` |
| Previous Pane | `Ctrl+b ;` |
| Zoom Pane | `Ctrl+b z` |
| Close Pane | `Ctrl+b x` |
| Swap with Next | `Ctrl+b }` |
| Swap with Previous | `Ctrl+b {` |
| Convert to Window | `Ctrl+b !` |
| Show Pane Numbers | `Ctrl+b q` |
| Resize Pane | `Ctrl+b Ctrl+Arrow` |

### Copy Mode (vi keys)

| Action | Shortcut |
|--------|----------|
| Enter Copy Mode | `Ctrl+b [` |
| Quit Copy Mode | `q` |
| Start Selection | `Space` |
| Copy Selection | `Enter` |
| Paste Buffer | `Ctrl+b ]` |
| Search Forward | `/` |
| Search Backward | `?` |
| Next Search Match | `n` |
| Previous Match | `N` |
| Go to Top | `g` |
| Go to Bottom | `G` |
| Page Up | `Ctrl+u` |
| Page Down | `Ctrl+d` |

### Miscellaneous

| Action | Shortcut |
|--------|----------|
| Command Prompt | `Ctrl+b :` |
| List Key Bindings | `Ctrl+b ?` |
| Clock Mode | `Ctrl+b t` |
| Reload Config | `:source-file ~/.tmux.conf` |

## iTerm2 tmux Integration Mode

When running `tmux -CC`:

| Action | Shortcut |
|--------|----------|
| Detach Cleanly | `Esc` |
| Force Quit | `X` |
| Toggle Logging | `L` |
| Run tmux Command | `C` |

**Pro Tip:** In tmux integration mode, use native iTerm2 shortcuts instead of tmux prefix shortcuts.
