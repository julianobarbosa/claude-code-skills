# Atuin Workflows Reference

Advanced usage patterns and workflow automation with Atuin.

## Daily Development Workflow

### Morning Startup

```bash
# Sync history from other machines
atuin sync

# Quick check of yesterday's work
atuin search --after "yesterday" --cwd $(pwd)

# Find that command you were running
atuin search --filter-mode directory "docker"
```

### During Development

```bash
# Search within current project
# Press Ctrl+R, type query
# Press Ctrl+R again to cycle: session → directory → host → global

# Find successful builds only
atuin search --exit 0 "make build"

# Find all test runs
atuin search "pytest\|npm test\|cargo test"
```

### End of Day

```bash
# Review what you did
atuin history list --after "today 9am" --cmd-only

# Check your patterns
atuin stats --period day

# Ensure sync is up to date
atuin sync
```

## Multi-Machine Workflow

### Primary Workstation Setup

```bash
# Register account (first time)
atuin register -u myuser -e me@example.com

# Import all history
atuin import auto

# Enable sync v2 for efficiency
cat >> ~/.config/atuin/config.toml << 'EOF'
[sync]
records = true
EOF

# Initial sync
atuin sync
```

### Secondary Machine Setup

```bash
# Install Atuin
curl --proto '=https' --tlsv1.2 -LsSf https://setup.atuin.sh | sh

# Add shell integration
echo 'eval "$(atuin init zsh)"' >> ~/.zshrc
source ~/.zshrc

# Login (use same credentials)
atuin login -u myuser

# Sync to get all history
atuin sync

# Now you have unified history across machines!
```

### Laptop + Desktop + Server

```bash
# All machines use same account
# History automatically syncs

# On any machine, search global history:
atuin search --filter-mode global "kubectl"

# Filter to specific host:
atuin search --host my-server "systemctl"

# See where a command was run:
atuin history list --format "{hostname}\t{command}" | grep "docker"
```

## Project-Specific Workflows

### Per-Project History

```bash
# Navigate to project
cd ~/projects/myapp

# Search only this directory's history
atuin search --filter-mode directory "npm"

# Or set as default (press Ctrl+R repeatedly to cycle modes)
# Config: filter_mode_shell_up_key_binding = "directory"

# Find all commands run in this repo (workspace mode)
atuin search --filter-mode workspace "git"
```

### Monorepo Navigation

```bash
# In monorepo root
cd ~/projects/monorepo

# Find commands in specific subdirectory
atuin search --cwd ~/projects/monorepo/packages/api "test"

# Search across workspace (git root)
atuin search --filter-mode workspace "build"
```

## Debugging & Investigation

### Find the Failing Command

```bash
# Find recent failures
atuin search --exit 1 --after "1 hour ago"

# Find specific failing command
atuin search --exit 1 "make"

# See exit codes in output
atuin history list --format "{exit}\t{command}" --limit 20
```

### Recreate Environment

```bash
# Find all commands run in a directory
atuin search --cwd /path/to/project --after "yesterday"

# Export for documentation
atuin history list --cwd /path/to/project --after "yesterday" --cmd-only > commands.txt
```

### Incident Response

```bash
# What happened in the last hour?
atuin history list --after "1 hour ago"

# Find all commands on production server
atuin search --host prod-server-01 --after "today"

# Successful commands only
atuin search --host prod-server-01 --exit 0 --after "today"
```

## Pipeline & Automation

### CI/CD History Preservation

```bash
# In CI, set unique session
export ATUIN_SESSION="ci-$(date +%Y%m%d-%H%M%S)"

# Initialize without binding keys
eval "$(atuin init bash --disable-up-arrow --disable-ctrl-r)"

# Commands now recorded with CI session identifier
```

### Scripted History Analysis

```bash
# Export history for analysis
atuin history list --cmd-only > all_commands.txt

# Find most used commands
atuin stats --count 50 > top_commands.txt

# Commands per day
atuin history list --format "{time}" | cut -d' ' -f1 | uniq -c

# Export specific time range
atuin history list --after "2024-01-01" --before "2024-02-01" --cmd-only > january.txt
```

### Backup Workflow

```bash
# Backup encryption key (CRITICAL)
cp ~/.local/share/atuin/key ~/backups/atuin-key-$(date +%Y%m%d).txt

# Backup database
cp ~/.local/share/atuin/history.db ~/backups/atuin-history-$(date +%Y%m%d).db

# Backup config
cp ~/.config/atuin/config.toml ~/backups/atuin-config.toml
```

## Power User Workflows

### Quick Command Replay

```bash
# Ctrl+R → search → Tab (select without execute)
# Edit the command, then Enter

# Alt+1 through Alt+9 for quick select
# Shows last 9 commands, Alt+N to select Nth
```

### Context-Aware Search

```bash
# Automatic context (in git repo)
# Up arrow defaults to session history
# Ctrl+R opens full search

# Change default behavior:
# filter_mode_shell_up_key_binding = "directory"
# Now up arrow shows directory history
```

### Statistics-Driven Optimization

```bash
# Review your patterns
atuin stats

# If certain commands are frequent, create aliases
# Example output shows:
#  1. git status     (2,345)
#  2. cd             (1,890)
#  3. git diff       (1,234)

# Create aliases for top commands
alias gs="git status"
alias gd="git diff"

# Sync aliases across machines (v18.1+)
atuin dotfiles alias set gs "git status"
atuin dotfiles alias set gd "git diff"
```

### Shell Integration Customization

```zsh
# Custom keybindings in .zshrc

# Keep up arrow for local history
eval "$(atuin init zsh --disable-up-arrow)"
bindkey '^[[A' up-line-or-history

# Custom binding for Atuin
bindkey '^[r' atuin-search  # Alt+R instead of Ctrl+R
```

## Team Workflows

### Shared Self-Hosted Server

```bash
# Team server setup (admin)
docker run -d \
  --name atuin-team \
  -p 8888:8888 \
  -v /data/atuin:/data \
  -e ATUIN_OPEN_REGISTRATION=true \
  ghcr.io/atuinsh/atuin:latest server start

# Team members configure
# sync_address = "https://atuin.company.internal"

# Each member has separate account
# No history shared between accounts (privacy preserved)
```

### Documentation from History

```bash
# Generate runbook from actual commands
atuin search --cwd /path/to/project --cmd-only | \
  grep -E "^(docker|kubectl|make|npm)" > runbook-commands.md

# Add context
echo "# Deployment Commands" > runbook.md
echo "" >> runbook.md
atuin search --exit 0 "kubectl apply" --cmd-only >> runbook.md
```

## Integration with Other Tools

### Atuin + fzf (Hybrid)

```bash
# Use Atuin for command history
# Use fzf for file/directory finding

# In .zshrc
eval "$(atuin init zsh)"
# fzf bindings except Ctrl+R
source /path/to/fzf/shell/completion.zsh
# Don't source key-bindings.zsh (conflicts with Atuin)

# Manual fzf file finding
bindkey '^T' fzf-file-widget
```

### Atuin + tmux

```bash
# Each tmux pane gets unique ATUIN_SESSION
# History automatically separated by session

# Search across all tmux sessions
atuin search --filter-mode host "query"

# Search current pane only
atuin search --filter-mode session "query"
```

### Atuin + direnv

```bash
# direnv sets project-specific env
# Atuin tracks per-directory history

# Natural workflow:
cd ~/project  # direnv loads env
# Press Ctrl+R → shows project history
# Ctrl+R again → switches to global
```

## Security-Conscious Workflows

### Sensitive Project

```toml
# ~/.config/atuin/config.toml

# Strong filtering
secrets_filter = true
history_filter = [
  ".*password.*",
  ".*secret.*",
  ".*token.*",
  ".*api.key.*",
  "^vault.*",
  "^aws configure.*"
]

# Filter sensitive directories
cwd_filter = [
  "/projects/classified",
  "/secrets"
]
```

### Air-Gapped / Offline Mode

```toml
# ~/.config/atuin/config.toml

# Disable all sync
auto_sync = false
sync_address = ""

# Local-only usage
# Full functionality without network
```

### Audit Trail

```bash
# Export for compliance
atuin history list \
  --format "{time}\t{hostname}\t{user}\t{cwd}\t{exit}\t{command}" \
  --after "2024-01-01" \
  --before "2024-02-01" \
  > audit-january-2024.tsv

# Include in audit logs
```

## Troubleshooting Workflow

### Performance Issues

```bash
# 1. Check database size
du -h ~/.local/share/atuin/history.db

# 2. Check entry count
sqlite3 ~/.local/share/atuin/history.db "SELECT COUNT(*) FROM history"

# 3. Prune if large
atuin history prune --older-than "1 year"

# 4. Vacuum
sqlite3 ~/.local/share/atuin/history.db "VACUUM"

# 5. Use faster settings
# search_mode = "prefix"
# filter_mode = "session"
```

### Sync Debugging

```bash
# 1. Check status
atuin status

# 2. Debug sync
ATUIN_LOG=debug atuin sync 2>&1 | tee sync-debug.log

# 3. Force full resync
atuin sync --force

# 4. Re-authenticate if needed
atuin logout
atuin login -u <USERNAME>
atuin sync
```

### History Recovery

```bash
# If database corrupted:
# 1. Backup current
mv ~/.local/share/atuin/history.db ~/.local/share/atuin/history.db.bak

# 2. If using sync, re-download
atuin sync

# 3. If no sync, reimport
atuin import auto

# 4. Restore from backup if available
cp ~/backups/atuin-history.db ~/.local/share/atuin/history.db
```
