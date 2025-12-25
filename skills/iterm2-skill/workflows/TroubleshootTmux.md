# TroubleshootTmux Workflow

Diagnose and fix common tmux and iTerm2 integration issues.

## Diagnostic Commands

Run these first to understand the environment:

```bash
# tmux version
tmux -V

# List running sessions
tmux ls

# Check tmux server
tmux info

# Check config syntax
tmux source-file ~/.tmux.conf
```

## Common Issues

### tmux Command Not Found

**Symptom:** `command not found: tmux`

**Fix:**
```bash
# Install with Homebrew
brew install tmux

# Verify
which tmux
tmux -V
```

### Sessions Not Persisting

**Symptom:** Session disappears after terminal close

**Causes:**
1. Running `tmux` without detaching first
2. tmux server killed
3. Running in non-session mode

**Fix:**
```bash
# Always detach properly
Ctrl+b d

# Or for iTerm2 integration
Press Esc

# Verify session exists
tmux ls

# Don't use `exit` in last pane - it kills session
```

### iTerm2 Integration Not Working

**Symptom:** `tmux -CC` doesn't create native windows

**Fixes:**

1. Update iTerm2:
```bash
# Check version
iTerm2 > About iTerm2
# Should be 3.0+ for tmux integration
```

2. Check tmux integration settings:
   - iTerm2 > Settings > General > tmux
   - Enable integration features

3. Reset integration:
```bash
# Kill all tmux sessions
tmux kill-server

# Restart iTerm2
# Try again
tmux -CC
```

### Colors Wrong or Missing

**Symptom:** Colors don't display correctly, vim looks wrong

**Fix:**
```bash
# Add to ~/.tmux.conf
set -g default-terminal "screen-256color"
set -sa terminal-overrides ",xterm*:Tc"

# Reload
tmux source-file ~/.tmux.conf

# Or set TERM in shell
export TERM=screen-256color
```

### Slow Escape Key

**Symptom:** Delay after pressing Escape (affects vim)

**Fix:**
```bash
# Add to ~/.tmux.conf
set -sg escape-time 10  # or 0

# Reload
tmux source-file ~/.tmux.conf
```

### Mouse Not Working

**Symptom:** Can't click or scroll with mouse

**Fix:**
```bash
# Add to ~/.tmux.conf
set -g mouse on

# Reload
tmux source-file ~/.tmux.conf
```

### Copy/Paste Not Working

**Symptom:** Can't copy text to system clipboard

**Fix for macOS:**
```bash
# Add to ~/.tmux.conf
set -g mouse on
bind -T copy-mode-vi y send -X copy-pipe-and-cancel "pbcopy"
bind -T copy-mode-vi Enter send -X copy-pipe-and-cancel "pbcopy"

# Enter copy mode
Ctrl+b [

# Select with mouse or Space to start, Enter to copy
# Paste normally with Cmd+V
```

### Config Changes Not Applied

**Symptom:** Changes to .tmux.conf don't take effect

**Fix:**
```bash
# Method 1: Reload from tmux command mode
Ctrl+b :source-file ~/.tmux.conf

# Method 2: If you have the binding
Ctrl+b r

# Method 3: Kill and restart
tmux kill-server
tmux new -s fresh
```

### "Terminal is not fully functional"

**Symptom:** Warning messages about terminal capabilities

**Fix:**
```bash
# Set correct TERM
export TERM=xterm-256color

# In .tmux.conf
set -g default-terminal "screen-256color"
```

### Panes Not Resizing Properly

**Symptom:** Split panes have wrong dimensions

**Fix:**
```bash
# Enable aggressive resize
setw -g aggressive-resize on

# Detach other clients
tmux attach -d
```

### Can't Detach (Integration Mode)

**Symptom:** Pressing Esc doesn't detach in iTerm2

**Fixes:**

1. Try pressing `Esc` multiple times
2. Use tmux Dashboard: Shell > tmux > Dashboard > Detach
3. Force quit: Press `X` in integration menu
4. Run in terminal: `tmux detach`

If completely stuck:
```bash
# Kill the integration client
tmux kill-session -t 0

# Or kill server
tmux kill-server
```

### "sessions should be nested with care"

**Symptom:** Warning when running tmux inside tmux

**Explanation:** You're trying to start tmux inside an existing session

**Fix:**
```bash
# Check if already in tmux
echo $TMUX

# If set, you're already in tmux
# Create new window instead
Ctrl+b c

# Or new session in background
tmux new -d -s another
```

## Recovery Commands

### Stuck Terminal

```bash
# Reset terminal
stty sane
reset
```

### Frozen tmux

```bash
# From another terminal
tmux kill-server

# Or kill specific session
tmux kill-session -t stuck_session
```

### Clean Restart

```bash
# Kill everything
tmux kill-server

# Remove socket (if corrupted)
rm -rf /tmp/tmux-$(id -u)

# Fresh start
tmux new -s fresh
```

## Debug Mode

Enable logging for bug reports:

```bash
# In iTerm2 integration mode
Press L to toggle logging

# Logs go to /tmp/tmux-*.log

# For tmux itself
tmux -vvv new -s debug
# Creates tmux-*.log files
```

## Getting Help

```bash
# tmux manual
man tmux

# List all key bindings
tmux list-keys

# Show all options
tmux show-options -g
tmux show-options -gw

# Check running config
tmux show-options -s
```
