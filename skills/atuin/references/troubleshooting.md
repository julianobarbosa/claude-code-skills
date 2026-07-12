# Atuin Troubleshooting Guide

Common issues and solutions for Atuin.

## Diagnostic Commands

```bash
# Run full diagnostics
atuin doctor

# Show system information
atuin info

# Debug mode
ATUIN_LOG=debug atuin search
ATUIN_LOG=debug atuin sync
```

## Installation Issues

### Shell Integration Not Working

**Symptom**: Ctrl+R doesn't open Atuin, or uses default history search.

**Solution**:
```bash
# 1. Check if atuin is installed
which atuin
atuin --version

# 2. Check shell integration
grep atuin ~/.zshrc    # For Zsh
grep atuin ~/.bashrc   # For Bash

# 3. Add integration if missing
# Zsh:
echo 'eval "$(atuin init zsh)"' >> ~/.zshrc

# Bash:
echo 'eval "$(atuin init bash)"' >> ~/.bashrc

# Fish:
echo 'atuin init fish | source' >> ~/.config/fish/config.fish

# 4. Reload shell
exec $SHELL
```

### ATUIN_SESSION Not Set

**Symptom**: `atuin doctor` shows ATUIN_SESSION not set.

**Solution**:
```bash
# Shell integration must be loaded
# Check rc file includes atuin init

# Reload shell
exec zsh  # or exec bash

# Verify
echo $ATUIN_SESSION
# Should output a UUID
```

### Command Not Found

**Symptom**: `atuin: command not found`

**Solution**:
```bash
# Check PATH
echo $PATH | grep -E "(\.cargo/bin|\.local/bin)"

# Add to PATH if missing
# For cargo install:
export PATH="$HOME/.cargo/bin:$PATH"

# For system install:
export PATH="$HOME/.local/bin:$PATH"

# Add to shell rc file
echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.zshrc
```

## Search Issues

### Ctrl+R Opens Wrong Search

**Symptom**: Ctrl+R opens fzf or default history instead of Atuin.

**Solution**:
```bash
# Check for conflicting bindings
bindkey | grep "\\^R"

# Remove fzf history binding if present
# In .zshrc, remove or comment:
# source /path/to/fzf/shell/key-bindings.zsh

# Or disable fzf history specifically
export FZF_CTRL_R_COMMAND=""

# Ensure atuin init is AFTER fzf setup in .zshrc
```

### No History Showing

**Symptom**: Search shows no results.

**Solution**:
```bash
# Check if history exists
atuin history list --limit 10

# If empty, import history
atuin import auto

# Check import results
atuin stats

# Verify database exists
ls -la ~/.local/share/atuin/history.db
```

### Search Is Slow

**Symptom**: Noticeable delay when opening search.

**Solution**:
```toml
# ~/.config/atuin/config.toml

# Use faster search mode
search_mode = "prefix"

# Limit to session by default
filter_mode = "session"

# Reduce preview
show_preview = false

# Smaller inline height
inline_height = 20
```

### Fuzzy Search Not Matching

**Symptom**: Expected results not appearing.

**Solution**:
```bash
# Try different search modes
atuin search --search-mode fulltext "query"
atuin search --search-mode prefix "query"

# Change default in config
# search_mode = "fulltext"
```

## Sync Issues

### Sync Failing

**Symptom**: `atuin sync` returns error.

**Solution**:
```bash
# 1. Check network
curl https://api.atuin.sh/healthz

# 2. Check login status
atuin status

# 3. Re-login if needed
atuin logout
atuin login -u <USERNAME>

# 4. Force sync
atuin sync --force

# 5. Debug mode
ATUIN_LOG=debug atuin sync
```

### Authentication Failed

**Symptom**: Login fails or sync returns 401.

**Solution**:
```bash
# Clear session and re-login
rm ~/.local/share/atuin/session
atuin login -u <USERNAME>

# If password forgotten:
# Use email recovery or create new account
```

### Sync Conflict / Duplicate History

**Symptom**: Same commands appearing multiple times.

**Solution**:
```bash
# Enable sync v2 (handles conflicts better)
# In config.toml:
# [sync]
# records = true

# Force full resync
atuin sync --force
```

### Self-Hosted Server Connection Failed

**Symptom**: Can't connect to self-hosted server.

**Solution**:
```bash
# 1. Check server is running
curl http://your-server:8888/healthz

# 2. Check config
grep sync_address ~/.config/atuin/config.toml

# 3. Ensure correct URL format
# sync_address = "http://localhost:8888"
# NOT: sync_address = "localhost:8888"

# 4. Check firewall/port
nc -zv your-server 8888
```

## Database Issues

### Corrupted Database

**Symptom**: Errors about database corruption.

**Solution**:
```bash
# 1. Check database integrity
sqlite3 ~/.local/share/atuin/history.db "PRAGMA integrity_check"

# 2. If corrupt, backup and recreate
mv ~/.local/share/atuin/history.db ~/.local/share/atuin/history.db.bak

# 3. Reimport history
atuin import auto

# 4. Resync (if using sync)
atuin sync
```

### Database Locked

**Symptom**: "database is locked" errors.

**Solution**:
```bash
# 1. Check for multiple atuin processes
pgrep -a atuin

# 2. Kill daemon if running
pkill atuin

# 3. Try again
atuin search
```

### Large Database / Slow Performance

**Symptom**: Database file very large, operations slow.

**Solution**:
```bash
# Check database size
ls -lh ~/.local/share/atuin/history.db

# Optimize database
sqlite3 ~/.local/share/atuin/history.db "VACUUM"

# Prune old history
atuin history prune --older-than "1 year"

# Check entry count
sqlite3 ~/.local/share/atuin/history.db "SELECT COUNT(*) FROM history"
```

## Key and Encryption Issues

### Lost Encryption Key

**Symptom**: Can't decrypt history after reinstall.

**Solution**:
```bash
# If you have backup:
cp /path/to/backup/key ~/.local/share/atuin/key

# If no backup - must start fresh:
atuin logout
rm ~/.local/share/atuin/key
rm ~/.local/share/atuin/session

# Delete server account
atuin account delete

# Re-register
atuin register -u <USERNAME> -e <EMAIL>
```

### Key Mismatch Between Machines

**Symptom**: Sync works but can't decrypt history from other machine.

**Solution**:
```bash
# All machines must use the SAME key

# On working machine, backup key:
cat ~/.local/share/atuin/key
# Save this value securely

# On broken machine:
# Replace key with the correct one
echo "your-key-value" > ~/.local/share/atuin/key

# Resync
atuin sync --force
```

## Shell-Specific Issues

### Zsh: Slow Startup

**Symptom**: Shell takes long to start after adding Atuin.

**Solution**:
```bash
# Time the init
time (eval "$(atuin init zsh)")

# If slow, check for issues:
atuin doctor

# Use lazy loading (add to .zshrc):
atuin-init() {
  eval "$(atuin init zsh)"
  unfunction atuin-init
}
# Bind to first Ctrl+R
zle -N atuin-init
bindkey '^R' atuin-init
```

### Bash: History Not Saving

**Symptom**: Commands not appearing in Atuin history.

**Solution**:
```bash
# Check PROMPT_COMMAND
echo $PROMPT_COMMAND
# Should include atuin

# Ensure proper init
eval "$(atuin init bash)"

# Check for conflicting PROMPT_COMMAND settings
# Atuin needs to be included
```

### Fish: Errors on Init

**Symptom**: Fish shows errors on startup.

**Solution**:
```bash
# Check Fish version (needs 3.0+)
fish --version

# Correct init syntax
atuin init fish | source

# NOT:
# eval "$(atuin init fish)"  # Wrong for Fish!
```

## Import Issues

### Import Not Finding History

**Symptom**: `atuin import auto` imports nothing.

**Solution**:
```bash
# Check history file exists
ls -la ~/.zsh_history
ls -la ~/.bash_history

# Check history file format
file ~/.zsh_history

# Try specific import
atuin import zsh
atuin import bash

# Check for extended history format (Zsh)
head ~/.zsh_history
# Should show timestamps if extended history is on
```

### Duplicate Entries After Import

**Symptom**: Same command appears multiple times.

**Solution**:
```bash
# Import is idempotent - running twice shouldn't duplicate
# But if you have duplicates from before:

# Export unique commands
atuin history list --cmd-only | sort -u > unique_cmds.txt

# Clear and reimport (drastic)
rm ~/.local/share/atuin/history.db
atuin import auto
```

## Performance Optimization

### General Slowness

```toml
# ~/.config/atuin/config.toml

# Faster search
search_mode = "prefix"
filter_mode = "session"

# Minimal UI
show_preview = false
show_help = false
inline_height = 15
style = "compact"

# Reduce sync
sync_frequency = "4h"
auto_sync = false  # Manual sync only
```

### Large History Database

```bash
# Check size
du -h ~/.local/share/atuin/history.db

# Prune old entries
atuin history prune --older-than "6 months"

# Vacuum database
sqlite3 ~/.local/share/atuin/history.db "VACUUM"
```

## Reset Everything

### Complete Reset

```bash
# 1. Logout
atuin logout

# 2. Remove all local data
rm -rf ~/.local/share/atuin
rm -rf ~/.config/atuin

# 3. Remove shell integration
# Edit .zshrc/.bashrc and remove atuin lines

# 4. Reinstall
curl --proto '=https' --tlsv1.2 -LsSf https://setup.atuin.sh | sh

# 5. Reconfigure
eval "$(atuin init zsh)"
atuin import auto
# Optionally: atuin register / atuin login
```

### Uninstall Completely

```bash
# Remove binary
rm $(which atuin)

# Remove data
rm -rf ~/.local/share/atuin
rm -rf ~/.config/atuin

# Remove shell integration
# Edit .zshrc/.bashrc and remove:
# eval "$(atuin init zsh)"

# Reload shell
exec $SHELL
```

## Getting Help

### Resources

- **Doctor**: `atuin doctor` - Built-in diagnostics
- **Docs**: https://docs.atuin.sh
- **Forum**: https://forum.atuin.sh
- **Discord**: Community support
- **GitHub Issues**: https://github.com/atuinsh/atuin/issues

### Reporting Bugs

```bash
# Include this info in bug reports:
atuin --version
atuin info
atuin doctor

# System info
uname -a
echo $SHELL
```
