# SetupTmux Workflow

Setup and configure tmux for optimal iTerm2 integration.

## Prerequisites

- iTerm2 installed on macOS
- tmux installed (`brew install tmux`)

## Steps

### 1. Verify Installation

```bash
# Check tmux is installed
which tmux
tmux -V

# If not installed
brew install tmux
```

### 2. Create Configuration File

Create `~/.tmux.conf` with recommended settings:

```bash
# Essential settings for iTerm2 integration
set -g default-terminal "screen-256color"
set -sa terminal-overrides ",xterm*:Tc"
set -g mouse on
set -g history-limit 50000
set -g base-index 1
setw -g pane-base-index 1
set -g renumber-windows on
set -sg escape-time 0
set -g focus-events on
setw -g mode-keys vi

# Reload config binding
bind r source-file ~/.tmux.conf \; display "Reloaded!"

# Better splits
bind | split-window -h -c "#{pane_current_path}"
bind - split-window -v -c "#{pane_current_path}"

# Vim-style navigation
bind h select-pane -L
bind j select-pane -D
bind k select-pane -U
bind l select-pane -R

# Copy to macOS clipboard
bind -T copy-mode-vi y send -X copy-pipe-and-cancel "pbcopy"
```

### 3. Choose Integration Mode

**Option A: Native tmux (traditional)**
```bash
tmux new -s main
```
- Use tmux shortcuts (Ctrl+b prefix)
- Works in any terminal
- Full tmux feature set

**Option B: iTerm2 Integration Mode (recommended)**
```bash
tmux -CC
```
- tmux windows appear as native iTerm2 tabs/windows
- Use iTerm2 shortcuts (Cmd-based)
- Sessions persist through SSH disconnects
- Best of both worlds

### 4. Test the Setup

```bash
# Start integrated session
tmux -CC

# Create windows and panes using iTerm2 shortcuts:
# Cmd+D for vertical split
# Cmd+Shift+D for horizontal split
# Cmd+T for new tab

# Detach with Esc or Shell > tmux > Detach

# Reattach
tmux -CC attach
```

### 5. Optional: Install TPM (Plugin Manager)

```bash
git clone https://github.com/tmux-plugins/tpm ~/.tmux/plugins/tpm
```

Add to `~/.tmux.conf`:
```bash
set -g @plugin 'tmux-plugins/tpm'
set -g @plugin 'tmux-plugins/tmux-sensible'
set -g @plugin 'tmux-plugins/tmux-resurrect'

run '~/.tmux/plugins/tpm/tpm'
```

Install plugins: `Ctrl+b I`

## Verification

1. Open iTerm2
2. Run `tmux -CC`
3. Verify native window integration works
4. Test Cmd+D and Cmd+Shift+D for splits
5. Detach with Esc
6. Verify `tmux ls` shows session
7. Reattach with `tmux -CC attach`

## Common Issues

**tmux not found:**
```bash
brew install tmux
```

**Integration mode not working:**
- Ensure iTerm2 is up to date
- Check Settings > General > tmux

**Colors look wrong:**
```bash
# Add to .tmux.conf
set -g default-terminal "screen-256color"
set -sa terminal-overrides ",xterm*:Tc"
```
