# Atuin Commands Reference

Complete CLI reference for all Atuin commands.

## Command Overview

```
atuin <COMMAND>

Commands:
  history      Manipulate shell history
  search       Interactive history search
  sync         Sync with the server
  login        Login to the sync server
  logout       Logout from the sync server
  register     Register with the sync server
  status       Show sync status
  stats        Show command statistics
  doctor       Run diagnostic checks
  info         Show system information
  daemon       Manage the background daemon
  import       Import shell history
  gen-completions  Generate shell completions
  account      Manage account settings
  dotfiles     Manage synced dotfiles
  help         Print help information
```

## history

Manipulate shell history entries.

### history list

```bash
# List all history
atuin history list

# Last N entries
atuin history list --limit 50

# Commands only (no metadata)
atuin history list --cmd-only

# Reverse order (oldest first)
atuin history list --reverse

# Custom format
atuin history list --format "{time}\t{duration}\t{command}"

# Filter by session
atuin history list --session

# Filter by directory
atuin history list --cwd /path/to/dir
```

**Format placeholders:**
| Placeholder | Description |
|-------------|-------------|
| `{command}` | The command |
| `{time}` | Timestamp |
| `{duration}` | Execution time |
| `{exit}` | Exit code |
| `{cwd}` | Working directory |
| `{hostname}` | Machine hostname |
| `{user}` | Username |

### history prune

```bash
# Prune with interactive confirmation
atuin history prune

# Prune entries older than duration
atuin history prune --older-than "6 months"

# Prune by hostname
atuin history prune --hostname old-machine

# Dry run (show what would be deleted)
atuin history prune --dry-run
```

### history delete

```bash
# Delete specific entry by ID
atuin history delete <ID>

# Delete without confirmation
atuin history delete <ID> --force
```

## search

Interactive history search.

```bash
# Open interactive search
atuin search

# Search with initial query
atuin search "git push"

# Force interactive mode
atuin search --interactive "query"

# Non-interactive (print best match)
atuin search --cmd-only "query"
```

### Search Filters

```bash
# Filter by exit code
atuin search --exit 0 "make"        # Successful only
atuin search --exit 1 "test"        # Failed only

# Time-based filters
atuin search --after "yesterday"
atuin search --after "2024-01-01"
atuin search --after "1 week ago"
atuin search --after "3pm yesterday"
atuin search --before "2024-06-01"

# Directory filter
atuin search --cwd /path/to/project

# Hostname filter
atuin search --host my-laptop

# Session filter
atuin search --session

# Combine filters
atuin search --exit 0 --after "1 week ago" --cwd ~/projects "docker"
```

### Search Options

```bash
# Search mode override
atuin search --search-mode prefix "git"
atuin search --search-mode fuzzy "git"

# Filter mode override
atuin search --filter-mode global
atuin search --filter-mode host
atuin search --filter-mode session
atuin search --filter-mode directory

# Limit results
atuin search --limit 20 "query"

# Output format
atuin search --format "{command}" "query"
```

## sync

Synchronize history with the server.

```bash
# Standard sync
atuin sync

# Force full sync (re-download everything)
atuin sync --force

# Verbose output
atuin sync -v
```

## status

Show sync and account status.

```bash
# Show sync status
atuin status

# Output includes:
# - Username
# - Server address
# - Last sync time
# - Record counts
# - Sync status
```

## stats

Show command usage statistics.

```bash
# Show stats
atuin stats

# Top N commands
atuin stats --count 25

# Period filter
atuin stats --period day
atuin stats --period week
atuin stats --period month
atuin stats --period year
atuin stats --period all

# Example output:
# Total commands:   50,234
# Unique commands:  12,456
#
# Top 10 commands:
#  1. git status          (2,345)
#  2. cd                   (1,890)
#  3. ls                   (1,654)
#  4. git diff             (1,234)
#  5. docker ps            (987)
#  6. kubectl get pods     (876)
#  7. vim                  (765)
#  8. cat                  (654)
#  9. grep                 (543)
# 10. make                 (432)
```

## doctor

Run diagnostic checks.

```bash
# Run all diagnostics
atuin doctor

# Checks include:
# - Shell integration
# - Database integrity
# - Sync configuration
# - Network connectivity
# - Key file status
```

## info

Display system and configuration information.

```bash
# Show info
atuin info

# Output includes:
# - Atuin version
# - Shell
# - Database path
# - Config path
# - Sync status
# - Record counts
```

## Account Commands

### register

```bash
# Register new account
atuin register -u <USERNAME> -e <EMAIL>

# With password prompt
atuin register -u myuser -e me@example.com

# Will prompt for password
```

### login

```bash
# Login to existing account
atuin login -u <USERNAME>

# Login with specific key file
atuin login -u <USERNAME> --key /path/to/key
```

### logout

```bash
# Logout (clears session)
atuin logout
```

### account

```bash
# Show account info
atuin account

# Delete account (DESTRUCTIVE)
atuin account delete
```

## import

Import history from various sources.

```bash
# Auto-detect and import
atuin import auto

# Specific shell imports
atuin import zsh           # ~/.zsh_history
atuin import bash          # ~/.bash_history
atuin import fish          # Fish history
atuin import resh          # RESH history
atuin import zsh-hist-db   # zsh-histdb SQLite

# Import from specific file
atuin import zsh --file /path/to/.zsh_history
```

## daemon

Manage background daemon for continuous sync.

```bash
# Start daemon
atuin daemon

# Start in foreground
atuin daemon --foreground

# Check daemon status
atuin daemon status

# Stop daemon (if running in background)
# Use system process management or Ctrl+C
```

## gen-completions

Generate shell completion scripts.

```bash
# Zsh completions
atuin gen-completions --shell zsh > _atuin
sudo mv _atuin /usr/local/share/zsh/site-functions/_atuin

# Bash completions
atuin gen-completions --shell bash > atuin.bash
sudo mv atuin.bash /etc/bash_completion.d/

# Fish completions
atuin gen-completions --shell fish > atuin.fish
mv atuin.fish ~/.config/fish/completions/

# PowerShell completions
atuin gen-completions --shell powershell > _atuin.ps1
```

## dotfiles (v18.1+)

Manage synced aliases and shell configuration.

```bash
# Enable dotfiles sync (requires sync v2)
# Add to config.toml: [dotfiles] enabled = true

# Set an alias
atuin dotfiles alias set ll "ls -la"
atuin dotfiles alias set k "kubectl"
atuin dotfiles alias set g "git"

# List all aliases
atuin dotfiles alias list

# Get specific alias
atuin dotfiles alias get ll

# Delete alias
atuin dotfiles alias delete ll
```

## config

Manage configuration values.

```bash
# Set a config value
atuin config set search_mode fuzzy
atuin config set sync_frequency "30m"
atuin config set auto_sync true

# These modify ~/.config/atuin/config.toml
```

## Global Options

Available for all commands:

```bash
# Verbose output
atuin -v <command>
atuin --verbose <command>

# Help
atuin --help
atuin <command> --help

# Version
atuin --version
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Invalid arguments |
| 3 | Network error |
| 4 | Authentication error |

## Environment Variables for Commands

```bash
# Debug logging
ATUIN_LOG=debug atuin sync

# Custom config directory
ATUIN_CONFIG_DIR=/custom/path atuin search

# Custom data directory
ATUIN_DATA_DIR=/custom/data atuin history list
```
