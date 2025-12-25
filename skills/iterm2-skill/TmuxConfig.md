# tmux Configuration Guide

Complete guide to configuring tmux via ~/.tmux.conf.

## Configuration File Location

tmux reads configuration from:
1. `/etc/tmux.conf` (system-wide)
2. `~/.tmux.conf` (user)
3. `~/.config/tmux/tmux.conf` (XDG)

Create if it doesn't exist:
```bash
touch ~/.tmux.conf
```

## Essential Configuration

### Recommended Starter Config

```bash
# ~/.tmux.conf - Essential tmux configuration

# ---------- General Settings ----------

# Use 256 colors and true color
set -g default-terminal "screen-256color"
set -sa terminal-overrides ",xterm*:Tc"

# Enable mouse support
set -g mouse on

# Increase history limit
set -g history-limit 50000

# Start window numbering at 1
set -g base-index 1
setw -g pane-base-index 1

# Renumber windows when one is closed
set -g renumber-windows on

# Faster escape time (for vim)
set -sg escape-time 0

# Enable focus events for vim
set -g focus-events on

# Use vi mode in copy mode
setw -g mode-keys vi

# Automatically rename windows
setw -g automatic-rename on

# ---------- Key Bindings ----------

# Change prefix to Ctrl+a (optional)
# set -g prefix C-a
# unbind C-b
# bind C-a send-prefix

# Reload config with prefix + r
bind r source-file ~/.tmux.conf \; display "Config reloaded!"

# Split panes with | and -
bind | split-window -h -c "#{pane_current_path}"
bind - split-window -v -c "#{pane_current_path}"
bind '"' split-window -v -c "#{pane_current_path}"
bind % split-window -h -c "#{pane_current_path}"

# New window in current path
bind c new-window -c "#{pane_current_path}"

# Vim-style pane navigation
bind h select-pane -L
bind j select-pane -D
bind k select-pane -U
bind l select-pane -R

# Resize panes with vim keys
bind -r H resize-pane -L 5
bind -r J resize-pane -D 5
bind -r K resize-pane -U 5
bind -r L resize-pane -R 5

# Quick pane switching with Alt+arrow
bind -n M-Left select-pane -L
bind -n M-Right select-pane -R
bind -n M-Up select-pane -U
bind -n M-Down select-pane -D

# Copy mode improvements
bind -T copy-mode-vi v send -X begin-selection
bind -T copy-mode-vi y send -X copy-pipe-and-cancel "pbcopy"
bind -T copy-mode-vi Enter send -X copy-pipe-and-cancel "pbcopy"

# ---------- Status Bar ----------

set -g status-position bottom
set -g status-interval 1
set -g status-style bg=black,fg=white

# Left status
set -g status-left-length 30
set -g status-left '#[fg=green]#S '

# Right status
set -g status-right-length 60
set -g status-right '#[fg=yellow]%H:%M:%S #[fg=green]%d-%b-%y'

# Window status
setw -g window-status-current-style fg=black,bg=green
setw -g window-status-format ' #I:#W '
setw -g window-status-current-format ' #I:#W '
```

## Configuration Options Reference

### Server Options (set -s)

| Option | Default | Description |
|--------|---------|-------------|
| `escape-time` | 500 | Delay after escape key (ms) |
| `exit-empty` | on | Exit when no sessions |
| `exit-unattached` | off | Exit when no clients attached |
| `focus-events` | off | Pass focus events to apps |

### Session Options (set -g)

| Option | Default | Description |
|--------|---------|-------------|
| `base-index` | 0 | Starting window index |
| `default-terminal` | screen | Default TERM value |
| `history-limit` | 2000 | Scrollback lines per pane |
| `mouse` | off | Enable mouse support |
| `prefix` | C-b | Prefix key |
| `renumber-windows` | off | Renumber on close |
| `status` | on | Show status bar |
| `status-position` | bottom | Status bar position |

### Window Options (setw -g)

| Option | Default | Description |
|--------|---------|-------------|
| `aggressive-resize` | off | Resize to smallest client |
| `automatic-rename` | on | Auto-rename windows |
| `mode-keys` | emacs | Copy mode key bindings |
| `pane-base-index` | 0 | Starting pane index |
| `xterm-keys` | on | Pass xterm keys |

## Key Binding Syntax

### Basic Binding

```bash
# bind KEY command
bind r source-file ~/.tmux.conf
```

### Binding with Flags

```bash
# -r: repeatable (hold prefix, tap key multiple times)
bind -r H resize-pane -L 5

# -n: no prefix required
bind -n M-Left select-pane -L

# -T: specify key table
bind -T copy-mode-vi v send -X begin-selection
```

### Unbinding Keys

```bash
# Remove a binding
unbind C-b

# Remove all bindings in table
unbind -a -T prefix
```

## Status Bar Configuration

### Format Variables

| Variable | Description |
|----------|-------------|
| `#S` | Session name |
| `#I` | Window index |
| `#W` | Window name |
| `#P` | Pane index |
| `#H` | Hostname |
| `#h` | Short hostname |
| `#T` | Pane title |
| `#F` | Window flags |

### Style Attributes

```bash
# Colors
fg=colour231    # Foreground (0-255 or named)
bg=colour234    # Background

# Named colors
fg=black,red,green,yellow,blue,magenta,cyan,white

# Attributes
bold,dim,underscore,blink,reverse,hidden,italics

# Combined
set -g status-style bg=black,fg=white,bold
```

### Status Bar Components

```bash
# Left side
set -g status-left-length 50
set -g status-left '#[fg=green,bold]#S #[fg=white]| '

# Right side
set -g status-right-length 100
set -g status-right '#[fg=cyan]#(whoami)@#H #[fg=yellow]%Y-%m-%d %H:%M'

# Window format
setw -g window-status-format '#I:#W#F'
setw -g window-status-current-format '#[fg=green,bold]#I:#W#F'
```

## Hooks

Run commands on events:

```bash
# After creating new session
set-hook -g after-new-session 'run-shell "echo session created"'

# After creating new window
set-hook -g after-new-window 'rename-window "new"'

# After client attached
set-hook -g client-attached 'display-message "Welcome!"'
```

## Plugin Management (TPM)

### Installing TPM

```bash
git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm
```

### Configuration

```bash
# List of plugins
set -g @plugin 'tmux-plugins/tpm'
set -g @plugin 'tmux-plugins/tmux-sensible'
set -g @plugin 'tmux-plugins/tmux-resurrect'
set -g @plugin 'tmux-plugins/tmux-continuum'

# Initialize TPM (keep at bottom)
run '~/.tmux/plugins/tpm/tpm'
```

### Popular Plugins

| Plugin | Description |
|--------|-------------|
| `tmux-sensible` | Sensible defaults |
| `tmux-resurrect` | Save/restore sessions |
| `tmux-continuum` | Auto-save sessions |
| `tmux-yank` | Clipboard integration |
| `tmux-prefix-highlight` | Show prefix status |
| `tmux-pain-control` | Pane navigation bindings |

### TPM Commands

| Keys | Action |
|------|--------|
| `prefix + I` | Install plugins |
| `prefix + U` | Update plugins |
| `prefix + alt + u` | Uninstall plugins |

## iTerm2 Integration

For iTerm2 tmux control mode:

```bash
# Recommended settings for iTerm2 integration
set -g assume-paste-time 0
set -g focus-events on

# Note: When using tmux -CC, you use iTerm2's
# native shortcuts instead of tmux bindings
```

Run with: `tmux -CC` or `tmux -CC attach`

## Troubleshooting

### Colors Not Working

```bash
# Check terminal
echo $TERM

# In tmux.conf
set -g default-terminal "screen-256color"
set -sa terminal-overrides ",*256col*:Tc"
```

### Slow Escape Key

```bash
# Reduce escape time (default is 500ms)
set -sg escape-time 10
```

### Mouse Not Working

```bash
# Enable mouse
set -g mouse on
```

### Reload Config

```bash
# From within tmux
tmux source-file ~/.tmux.conf

# Or if you have the binding
Ctrl+b r
```
