# Tips and Tricks

Community-sourced tips, power user patterns, and best practices.

## Top Productivity Patterns

### 1. Context-Aware Up Arrow (Most Loved Feature)

Configure Up Arrow and Ctrl+R to behave differently:

```toml
# Up Arrow: prefix search, only this directory
search_mode_shell_up_key_binding = "prefix"
filter_mode_shell_up_key_binding = "directory"

# Ctrl+R: fuzzy search, global scope
search_mode = "fuzzy"
filter_mode = "global"
```

**Why:** Up Arrow feels like enhanced readline (muscle memory), while Ctrl+R gives you full-power global search.

### 2. Workspace-Aware Filtering

```toml
workspaces = true
```

Automatically filters history to the current git repository. Perfect for project-specific command recall — no more seeing production commands while in your dev repo.

### 3. Enter to Execute, Tab to Edit

```toml
enter_accept = true
```

Press Enter to immediately run the selected command. Press Tab to place it on the command line for editing. Much faster than the default where both insert for editing.

### 4. Compact Style with Host Column (Multi-Machine)

```toml
style = "compact"

[ui]
columns = ["exit", "duration", "host", "command"]
```

Shows exit codes and which machine a command was run on — essential for multi-machine setups.

### 5. Use Stats to Discover Alias Candidates

```bash
atuin stats -c 20
```

If you see `git status` 500 times, create `alias gs="git status"`. Atuin's stats make this data-driven.

### 6. N-gram Analysis for Workflow Patterns

```bash
atuin stats -n 2    # Common command pairs
atuin stats -n 3    # Common triplets
```

Discover patterns like `git add` -> `git commit` -> `git push` to create shell functions.

## Security Best Practices

### Save Your Encryption Key Immediately

```bash
atuin key
# Copy this to 1Password/Bitwarden NOW
# It CANNOT be recovered if lost
```

### Filter Secrets Automatically

```toml
secrets_filter = true    # Default, keeps it enabled
```

Auto-blocks: AWS keys, GitHub PATs, Slack tokens, Stripe keys, GitLab PATs, npm tokens, Azure storage keys, Google service account keys.

### Custom History Exclusions

```toml
history_filter = [
  ".*password=.*",
  ".*secret=.*",
  "^mysql.*-p.*",
  "^curl.*-u .*:.*",
  "^export (AWS_|GITHUB_|STRIPE_|DATABASE_URL)",
  "^ssh-keygen",
  "^openssl.*-passout",
]
```

### Prune After Adding Filters

```bash
atuin history prune --dry-run    # Preview what will be deleted
atuin history prune              # Actually delete matching entries
```

## Shell Integration Tips

### fzf Coexistence

Load Atuin **after** fzf in your shell config so Atuin takes Ctrl+R precedence:

```zsh
# ~/.zshrc
source <(fzf --zsh)           # fzf keeps Ctrl+T and Alt+C
eval "$(atuin init zsh)"       # Atuin takes Ctrl+R (loaded last = wins)
```

### Custom Keybindings

```zsh
export ATUIN_NOBIND="true"
eval "$(atuin init zsh)"

# Custom bindings
bindkey '^r' atuin-search           # Ctrl+R for search
bindkey '^[[A' atuin-up-search      # Up arrow for contextual
bindkey '^f' atuin-search           # Ctrl+F as additional binding
```

### macOS Alt Key Fix

Alt+1-9 quick-select doesn't work on macOS Terminal. Fix:

```toml
ctrl_n_shortcuts = true    # Use Ctrl+1-9 instead of Alt+1-9
```

### Recommended .zshrc Order

```zsh
# 1. Plugin manager
source ~/.sheldon/init.zsh

# 2. Prompt
eval "$(starship init zsh)"

# 3. fzf (for files, NOT history)
source <(fzf --zsh)

# 4. Zoxide
eval "$(zoxide init --cmd cd zsh)"

# 5. Atuin (LAST — takes Ctrl+R from fzf)
eval "$(atuin init zsh)"
```

## Sync Strategies

### Aggressive Sync (Low Latency)

```toml
sync_frequency = "0"    # Sync after every command
```

### Background Daemon Sync

```toml
[daemon]
enabled = true
sync_frequency = 60     # Every minute
```

Best for: ZFS filesystems (avoids SQLite write issues), SSH sessions where you want history ready on arrival.

### Force Full Re-sync

```bash
atuin sync -f    # Re-download everything
```

## Dotfiles Sync (Aliases Across Machines)

```toml
[sync]
records = true

[dotfiles]
enabled = true
```

```bash
# Set aliases that sync everywhere
atuin dotfiles alias set k 'kubectl'
atuin dotfiles alias set g 'git'
atuin dotfiles alias set dc 'docker compose'
atuin dotfiles alias set ll 'ls -lah'
atuin dotfiles alias set tf 'terraform'

# Set environment variables
atuin dotfiles var set EDITOR 'nvim'
atuin dotfiles var set PAGER 'less'

# List what's synced
atuin dotfiles alias list
atuin dotfiles var list
```

Restart shell after changes.

## Performance Tips

### ZFS Users: Enable Daemon

SQLite has compatibility issues with ZFS. The daemon takes writes off the hot path:

```toml
[daemon]
enabled = true
```

### Large History (60K+ entries)

Upgrade to v15+ which uses variable page sizes (1100 default vs old 100), dramatically improving sync speed.

### Reduce Empty Query Lag

The first search keystroke is always slower than subsequent ones. Type at least one character quickly to avoid the empty-query delay.

### History Dedup

```bash
atuin history dedup    # Remove duplicates (same command + cwd + hostname)
```

## Tmux Integration

```toml
[tmux]
enabled = true
width = "80%"
height = "60%"
```

Opens Atuin in a tmux popup window (requires tmux >= 3.2). Supported in zsh, bash, and fish. Does **not** work with iTerm's native tmux integration.

## Complementary Tool Stack

| Tool | Purpose | Complements Atuin |
|------|---------|-------------------|
| **Zoxide** | Smart `cd` | "Like Atuin but for directories" |
| **fzf** | General fuzzy finder | File finding (Atuin handles history) |
| **Starship** | Cross-shell prompt | Git info, cmd duration display |
| **Chezmoi** | Dotfile management | Config files (Atuin handles aliases) |
| **ble.sh** | Bash line editor | Best Bash integration for Atuin |

## Comparison Quick Reference

| Feature | Atuin | McFly | hstr |
|---------|-------|-------|------|
| Storage | SQLite | SQLite | Text |
| Search | Fuzzy/prefix/fulltext/skim | Neural ranking | Substring/regex |
| Sync | E2E encrypted | No | No |
| Stats | Built-in | No | No |
| Dotfiles | Aliases + vars | No | No |
| Shell support | 6 shells | 3 shells | 2 shells |
| Active dev | Very active | Slower | Maintenance |
