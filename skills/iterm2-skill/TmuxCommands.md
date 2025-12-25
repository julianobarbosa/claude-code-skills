# tmux Command Reference

Complete reference for tmux terminal multiplexer commands.

## Session Management

### Creating Sessions

```bash
# New session (auto-named)
tmux
tmux new
tmux new-session

# New named session
tmux new -s mysession

# New session with window name
tmux new -s mysession -n mywindow

# New session detached
tmux new -s mysession -d

# New session, attach if exists
tmux new-session -A -s mysession
```

### Attaching to Sessions

```bash
# Attach to last session
tmux attach
tmux a

# Attach to named session
tmux attach -t mysession
tmux a -t mysession

# Attach, detach other clients
tmux attach -dt mysession

# Attach read-only
tmux attach -r -t mysession
```

### Listing & Killing Sessions

```bash
# List all sessions
tmux ls
tmux list-sessions

# Kill specific session
tmux kill-session -t mysession

# Kill all sessions except current
tmux kill-session -a

# Kill all sessions except named
tmux kill-session -a -t mysession

# Kill entire server
tmux kill-server
```

### Renaming Sessions

```bash
# From command line
tmux rename-session -t old_name new_name

# From within tmux (prefix then $)
Ctrl+b $
```

## Window Management

### Creating Windows

```bash
# New window (from within tmux)
Ctrl+b c

# New window via command
tmux new-window

# New window with name
tmux new-window -n mywindow

# New window in background
tmux new-window -d -n mywindow
```

### Navigating Windows

```bash
# List all windows
Ctrl+b w

# Next window
Ctrl+b n

# Previous window
Ctrl+b p

# Go to window by number
Ctrl+b 0-9

# Last active window
Ctrl+b l

# Find window by name
Ctrl+b f
```

### Managing Windows

```bash
# Rename current window
Ctrl+b ,

# Kill current window
Ctrl+b &

# Swap windows
tmux swap-window -s 2 -t 1

# Move window to index
tmux move-window -t 3

# Renumber all windows
tmux move-window -r
```

## Pane Management

### Splitting Panes

```bash
# Split vertical (side by side)
Ctrl+b %
tmux split-window -h

# Split horizontal (top/bottom)
Ctrl+b "
tmux split-window -v

# Split with specific size (percentage)
tmux split-window -h -p 30

# Split with specific size (cells)
tmux split-window -v -l 10
```

### Navigating Panes

```bash
# Move between panes
Ctrl+b Arrow

# Next pane
Ctrl+b o

# Previous pane
Ctrl+b ;

# Show pane numbers (then press number)
Ctrl+b q

# Jump to pane by number
Ctrl+b q 0-9
```

### Resizing Panes

```bash
# Resize (hold Ctrl)
Ctrl+b Ctrl+Arrow

# Resize by specific amount
tmux resize-pane -D 10  # Down
tmux resize-pane -U 10  # Up
tmux resize-pane -L 10  # Left
tmux resize-pane -R 10  # Right

# Resize to percentage
tmux resize-pane -x 50%
tmux resize-pane -y 30%

# Toggle zoom (full window)
Ctrl+b z
```

### Managing Panes

```bash
# Close pane
Ctrl+b x

# Convert pane to window
Ctrl+b !

# Swap panes
Ctrl+b }  # Swap with next
Ctrl+b {  # Swap with previous

# Join pane from another window
tmux join-pane -s :2.0 -t :1

# Send pane to another window
tmux join-pane -t :2

# Rotate panes
Ctrl+b Ctrl+o  # Rotate forward
Ctrl+b Alt+o   # Rotate backward

# Apply layouts
Ctrl+b Space        # Cycle through layouts
Ctrl+b Alt+1-5      # Apply specific layout
```

### Layout Presets

| Shortcut | Layout |
|----------|--------|
| `Ctrl+b Alt+1` | Even horizontal |
| `Ctrl+b Alt+2` | Even vertical |
| `Ctrl+b Alt+3` | Main horizontal |
| `Ctrl+b Alt+4` | Main vertical |
| `Ctrl+b Alt+5` | Tiled |

## Copy Mode

### Entering Copy Mode

```bash
# Enter copy mode
Ctrl+b [

# Scroll up in copy mode
PageUp or Ctrl+b PageUp
```

### Navigation (vi mode)

| Key | Action |
|-----|--------|
| `h/j/k/l` | Move cursor |
| `w/b` | Word forward/back |
| `0/$` | Start/end of line |
| `g/G` | Top/bottom |
| `Ctrl+f/b` | Page down/up |
| `/` | Search forward |
| `?` | Search backward |
| `n/N` | Next/prev match |

### Selection & Copy

```bash
# Start selection
Space

# Copy selection (exits copy mode)
Enter

# Paste buffer
Ctrl+b ]

# List buffers
tmux list-buffers

# Save buffer to file
tmux save-buffer ~/buffer.txt

# Load file to buffer
tmux load-buffer ~/file.txt
```

## Configuration

### Common tmux.conf Settings

```bash
# Change prefix from Ctrl+b to Ctrl+a
set -g prefix C-a
unbind C-b
bind C-a send-prefix

# Enable mouse support
set -g mouse on

# Use vi keys in copy mode
setw -g mode-keys vi

# Start window numbering at 1
set -g base-index 1
setw -g pane-base-index 1

# Renumber windows on close
set -g renumber-windows on

# Increase history limit
set -g history-limit 10000

# Enable 256 colors
set -g default-terminal "screen-256color"

# Faster escape time
set -sg escape-time 0

# Enable focus events
set -g focus-events on

# Aggressive resize
setw -g aggressive-resize on
```

### Key Binding Examples

```bash
# Reload config with r
bind r source-file ~/.tmux.conf \; display "Config reloaded!"

# Split panes using | and -
bind | split-window -h
bind - split-window -v

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
```

### Applying Configuration

```bash
# Reload from within tmux
Ctrl+b :source-file ~/.tmux.conf

# Or with bound key (after adding bind above)
Ctrl+b r

# From command line
tmux source-file ~/.tmux.conf
```

## Scripting & Automation

### Running Commands in Sessions

```bash
# Send keys to a session
tmux send-keys -t mysession "echo hello" Enter

# Run command in new window
tmux new-window "htop"

# Run command in new session
tmux new-session -d -s work "vim"

# Execute command and wait
tmux run-shell "sleep 5 && echo done"
```

### Environment Variables

```bash
# Set environment variable
tmux set-environment MY_VAR "value"

# Get environment variable
tmux show-environment MY_VAR

# Update from shell environment
tmux set-environment -g MY_VAR "$MY_VAR"
```

### Display Messages

```bash
# Show message
tmux display-message "Hello World"

# Show for specific duration
tmux display-message -d 5000 "5 second message"
```
