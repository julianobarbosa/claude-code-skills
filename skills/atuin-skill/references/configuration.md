# Atuin Configuration Reference

Complete reference for all Atuin configuration options.

## File Locations

```
~/.config/atuin/config.toml       # Main configuration
~/.local/share/atuin/history.db   # SQLite history database
~/.local/share/atuin/key          # Encryption key (BACKUP THIS!)
~/.local/share/atuin/session      # Server session token
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `ATUIN_CONFIG_DIR` | Override config directory |
| `ATUIN_DATA_DIR` | Override data directory |
| `ATUIN_SESSION` | Current session ID (auto-set) |
| `ATUIN_LOG` | Log level (debug, info, warn, error) |

## Core Configuration

### Path Settings

```toml
# ~/.config/atuin/config.toml

# Database location
db_path = "~/.local/share/atuin/history.db"

# Encryption key location
key_path = "~/.local/share/atuin/key"

# Session token location
session_path = "~/.local/share/atuin/session"
```

### Search Configuration

```toml
# Search algorithm
search_mode = "fuzzy"
# Options:
#   prefix   - Match from start (fastest)
#   fulltext - Substring match anywhere
#   fuzzy    - Fuzzy matching (default)
#   skim     - Skim-style fuzzy finder

# Default filter scope
filter_mode = "global"
# Options:
#   global    - All history across all machines
#   host      - Current hostname only
#   session   - Current terminal session only
#   directory - Current working directory only
#   workspace - Git repository root

# Separate modes for shell up-key binding
search_mode_shell_up_key_binding = "fuzzy"
filter_mode_shell_up_key_binding = "session"
```

### UI Configuration

```toml
# Display style
style = "compact"
# Options:
#   auto    - Automatic based on terminal
#   full    - Full metadata display
#   compact - Condensed view (default)

# Invert UI (search bar at top)
invert = false

# Maximum lines for inline mode (0 = full screen)
inline_height = 40

# Show command preview
show_preview = true

# Maximum preview lines
max_preview_height = 4

# Show keybinding help
show_help = true

# Show filter mode tabs
show_tabs = true

# Exit behavior on Escape
exit_mode = "return-original"
# Options:
#   return-original - Return original command
#   return-query    - Return search query
```

### Input Configuration

```toml
# Execute on Enter (vs select and confirm)
enter_accept = false

# Command chaining with && and ||
command_chaining = false

# Keymap mode
keymap_mode = "emacs"
# Options:
#   emacs      - Emacs-style (default)
#   vim-normal - Vim normal mode
#   vim-insert - Vim insert mode
#   auto       - Detect from shell

# Cursor styles per keymap
[keymap_cursor]
emacs = "blink-block"
vim_insert = "blink-bar"
vim_normal = "steady-block"

# Use Ctrl+N instead of Alt+N for quick select (macOS)
ctrl_n_shortcuts = true
```

### History Configuration

```toml
# Store commands that failed (non-zero exit)
store_failed = true

# Default output format for history list
history_format = "{time}\t{command}\t{duration}"
```

### Privacy & Filtering

```toml
# Enable automatic secrets filtering
# Filters: AWS keys, GitHub tokens, passwords, etc.
secrets_filter = true

# Regex patterns to exclude from history
history_filter = [
  "^password",
  "^secret",
  ".*--password.*",
  "^export.*API_KEY",
  "^export.*SECRET",
  "mysql.*-p[^ ]*",
  "psql.*password"
]

# Directories to exclude from history
cwd_filter = [
  "^/tmp",
  "^/private/tmp",
  "^/var/folders"
]
```

## Sync Configuration

### Basic Sync Settings

```toml
# Sync server address
sync_address = "https://api.atuin.sh"

# Automatic sync when logged in
auto_sync = true

# Sync frequency (human-readable: 10s, 20m, 1h)
sync_frequency = "1h"
```

### Sync v2 (Recommended)

```toml
# Enable sync v2 protocol (faster, more efficient)
[sync]
records = true
```

### Network Settings

```toml
# Request timeout (seconds)
network_timeout = 30

# Connection timeout (seconds)
network_connect_timeout = 5

# Local database timeout (seconds)
local_timeout = 5
```

## Daemon Configuration (v18.3+)

```toml
[daemon]
# Enable background daemon
enabled = true

# Sync frequency in seconds (daemon mode)
sync_frequency = 300

# Socket path (Unix)
socket_path = "/tmp/atuin-daemon.sock"

# Enable systemd socket activation
systemd_socket = false

# TCP port (alternative to socket)
tcp_port = 0  # 0 = disabled
```

## Stats Configuration

```toml
[stats]
# Commands where subcommands are significant
common_subcommands = [
  "cargo",
  "git",
  "go",
  "kubectl",
  "docker",
  "docker-compose",
  "npm",
  "yarn",
  "pnpm",
  "bun",
  "make",
  "just",
  "systemctl",
  "apt",
  "brew",
  "pip",
  "poetry"
]

# Prefixes to strip from stats (e.g., sudo)
common_prefix = [
  "sudo",
  "doas",
  "time"
]
```

## Theme Configuration (v18.4+)

```toml
[theme]
# Theme name (empty = default)
name = ""

# Debug theme loading
debug = false

# Maximum inheritance depth
max_depth = 5
```

## Dotfiles Sync (v18.1+)

```toml
[dotfiles]
# Enable alias synchronization
enabled = true
```

Then use:
```bash
# Set an alias
atuin dotfiles alias set ll "ls -la"

# List aliases
atuin dotfiles alias list

# Get alias
atuin dotfiles alias get ll

# Delete alias
atuin dotfiles alias delete ll
```

## Complete Example Configuration

```toml
# ~/.config/atuin/config.toml

## Core paths (usually defaults are fine)
# db_path = "~/.local/share/atuin/history.db"
# key_path = "~/.local/share/atuin/key"
# session_path = "~/.local/share/atuin/session"

## Search behavior
search_mode = "fuzzy"
filter_mode = "global"
filter_mode_shell_up_key_binding = "session"

## UI
style = "compact"
inline_height = 40
show_preview = true
show_help = true
show_tabs = true
enter_accept = false
invert = false

## Input
keymap_mode = "emacs"
ctrl_n_shortcuts = true

## Privacy
secrets_filter = true
store_failed = true
history_filter = [
  "^password",
  ".*--password.*",
  "^export.*KEY",
  "^export.*SECRET",
  "^export.*TOKEN"
]

## Sync
sync_address = "https://api.atuin.sh"
auto_sync = true
sync_frequency = "1h"

[sync]
records = true

## Network
network_timeout = 30
network_connect_timeout = 5

## Daemon (optional)
[daemon]
enabled = false
sync_frequency = 300

## Stats
[stats]
common_subcommands = [
  "cargo",
  "git",
  "kubectl",
  "docker",
  "npm"
]
common_prefix = ["sudo"]

## Dotfiles (optional)
[dotfiles]
enabled = false
```

## Configuration Validation

```bash
# Check configuration
atuin doctor

# Show current config values
atuin info

# Debug config loading
ATUIN_LOG=debug atuin search
```

## Shell-Specific Integration Options

### Zsh

```zsh
# Basic init
eval "$(atuin init zsh)"

# With options
eval "$(atuin init zsh --disable-up-arrow)"
eval "$(atuin init zsh --disable-ctrl-r)"
```

### Bash

```bash
# Basic init
eval "$(atuin init bash)"

# With options
eval "$(atuin init bash --disable-up-arrow)"
```

### Fish

```fish
# Basic init
atuin init fish | source

# With options
atuin init fish --disable-up-arrow | source
```

### Init Options

| Option | Description |
|--------|-------------|
| `--disable-up-arrow` | Don't bind up arrow |
| `--disable-ctrl-r` | Don't bind Ctrl+R |

## Environment-Specific Configs

### Minimal (Performance Focus)

```toml
search_mode = "prefix"
filter_mode = "session"
style = "compact"
inline_height = 20
show_preview = false
show_help = false
auto_sync = false
```

### Privacy-Focused (No Sync)

```toml
auto_sync = false
sync_address = ""
secrets_filter = true
store_failed = false
history_filter = [
  ".*password.*",
  ".*secret.*",
  ".*token.*",
  ".*key.*"
]
```

### Multi-Machine (Heavy Sync)

```toml
auto_sync = true
sync_frequency = "15m"
filter_mode = "global"

[sync]
records = true

[daemon]
enabled = true
sync_frequency = 60
```
