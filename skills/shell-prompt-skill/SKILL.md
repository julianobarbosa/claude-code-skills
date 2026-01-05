---
name: shell-prompt
description: Modern shell prompt configuration with Powerlevel10k and Starship. Use when configuring shell prompts, optimizing prompt performance, comparing P10k vs Starship, setting up instant prompt, troubleshooting slow prompts, or migrating between prompt frameworks. Covers benchmarking, git status optimization, and cross-shell compatibility.
---

# Shell Prompt Skill

Configure high-performance shell prompts with Powerlevel10k and Starship.

## Overview

Modern shell prompts provide:
- Git status with branch, dirty state, and remote tracking
- Environment indicators (Python venv, Node version, K8s context)
- Execution time for long-running commands
- Exit code visualization
- Async updates for responsive experience

## Quick Comparison

| Feature | Powerlevel10k | Starship |
|---------|---------------|----------|
| **Language** | Zsh (pure shell) | Rust (binary) |
| **Shell Support** | Zsh only | Bash, Zsh, Fish, PowerShell, etc. |
| **First Prompt** | ~10ms (instant) | ~40-50ms |
| **Git (large repo)** | Async, never blocks | Can timeout (>500ms) |
| **Maintenance** | Life support (stable) | Actively developed |
| **Config Format** | Zsh script | TOML |

## Performance Summary

### Benchmark Results (zsh-bench)

| Metric | Target | Powerlevel10k | Starship |
|--------|--------|---------------|----------|
| First prompt lag | <50ms | **24ms** | ~40-50ms |
| Command lag | <10ms | **15ms** | ~40ms |
| Git status (small) | <30ms | <10ms | ~185-250ms |
| Git status (large) | <100ms | Async/instant | Varies/timeout |

### Key Performance Factors

1. **Powerlevel10k uses gitstatus daemon** - C++ binary running in background
2. **Starship forks on every prompt** - Rust binary spawned each time
3. **Instant Prompt** - P10k exclusive feature, shows prompt in ~10ms

## Powerlevel10k

### Installation

```bash
# With Oh My Zsh
git clone --depth=1 https://github.com/romkatv/powerlevel10k.git \
  ${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/themes/powerlevel10k

# Set in .zshrc
ZSH_THEME="powerlevel10k/powerlevel10k"

# Run configuration wizard
p10k configure
```

### Instant Prompt Setup

Add at the **very top** of `~/.zshrc` (before anything else):

```zsh
# Enable Powerlevel10k instant prompt
if [[ -r "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh" ]]; then
  source "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh"
fi
```

Add at the **end** of `~/.zshrc`:

```zsh
# Source Powerlevel10k config
[[ -f ~/.p10k.zsh ]] && source ~/.p10k.zsh
```

### Configuration Options

Key settings in `~/.p10k.zsh`:

```zsh
# Left prompt segments
typeset -g POWERLEVEL9K_LEFT_PROMPT_ELEMENTS=(
  os_icon
  dir
  vcs
  newline
  prompt_char
)

# Right prompt segments
typeset -g POWERLEVEL9K_RIGHT_PROMPT_ELEMENTS=(
  status
  command_execution_time
  background_jobs
  virtualenv
  kubecontext
  azure
  aws
  context
  time
)

# Transient prompt (clean up previous prompts)
typeset -g POWERLEVEL9K_TRANSIENT_PROMPT=always

# Directory truncation
typeset -g POWERLEVEL9K_SHORTEN_STRATEGY=truncate_to_unique
typeset -g POWERLEVEL9K_SHORTEN_DIR_LENGTH=3
```

### Performance Tuning

```zsh
# Disable slow segments
typeset -g POWERLEVEL9K_DISABLE_GITSTATUS=false  # Keep enabled!

# Large repo optimization
typeset -g POWERLEVEL9K_VCS_MAX_INDEX_SIZE_DIRTY=1000

# Async git status (default, don't change)
typeset -g POWERLEVEL9K_VCS_BACKENDS=(git)

# Reduce segment count for speed
typeset -g POWERLEVEL9K_RIGHT_PROMPT_ELEMENTS=(status command_execution_time)
```

## Starship

### Installation

```bash
# macOS
brew install starship

# Linux (curl)
curl -sS https://starship.rs/install.sh | sh

# Cargo
cargo install starship --locked
```

### Shell Integration

**Zsh** (`~/.zshrc`):
```zsh
eval "$(starship init zsh)"
```

**Bash** (`~/.bashrc`):
```bash
eval "$(starship init bash)"
```

**Fish** (`~/.config/fish/config.fish`):
```fish
starship init fish | source
```

### Configuration

Create `~/.config/starship.toml`:

```toml
# Minimal fast config
format = """
$directory\
$git_branch\
$git_status\
$character"""

# Prompt character
[character]
success_symbol = "[>](bold green)"
error_symbol = "[>](bold red)"

# Directory
[directory]
truncation_length = 3
truncate_to_repo = true

# Git branch
[git_branch]
format = "[$branch]($style) "
style = "bold purple"

# Git status - can be slow!
[git_status]
format = '([$all_status$ahead_behind]($style) )'
style = "bold red"
disabled = false  # Set true if slow
```

### Performance Optimization

```toml
# ~/.config/starship.toml

# Increase timeout for slow repos
command_timeout = 1000  # ms, default 500

# Scan timeout for git
[git_status]
disabled = false
# Reduce scan depth
# windows_starship = '/mnt/c/...'  # WSL optimization

# Disable slow modules
[python]
disabled = true

[nodejs]
disabled = true

[package]
disabled = true
```

### Debugging Performance

```bash
# Show timing per module
starship explain

# Time the prompt
starship timings

# Example output:
#  aws            -   <1ms  -  ~
#  character      -   <1ms  -  >
#  directory      -    4ms  -  ~/projects/myapp
#  git_branch     -    2ms  -  main
#  git_status     -  185ms  -  [!+]  <-- SLOW!
```

## Performance Comparison Deep Dive

### Architecture Differences

**Powerlevel10k (gitstatus daemon)**:
```
┌─────────────┐     pipes      ┌─────────────┐
│    Zsh      │ <============> │  gitstatusd │
│  (prompt)   │                │   (C++ daemon)
└─────────────┘                └─────────────┘
       │                              │
       │ async                        │ keeps state
       │ never blocks                 │ in memory
       ▼                              ▼
   Instant prompt              Fast git queries
```

**Starship (fork per prompt)**:
```
┌─────────────┐   fork+exec    ┌─────────────┐
│    Zsh      │ ────────────>  │  starship   │
│  (prompt)   │                │   (Rust)    │
└─────────────┘                └─────────────┘
       │                              │
       │ synchronous                  │ calls git
       │ blocks until done            │ each time
       ▼                              ▼
   Wait for prompt             git status (can be slow)
```

### Large Repository Performance

| Repository | Powerlevel10k | Starship |
|------------|---------------|----------|
| Linux kernel | <20ms (async) | Timeout likely |
| Chromium | <20ms (async) | 4+ seconds |
| Small project | <10ms | ~200ms |
| Empty dir | <10ms | ~40ms |

### When Each Wins

**Powerlevel10k wins when**:
- Working in large monorepos
- Maximum performance required
- Using Zsh exclusively
- Want instant prompt feature

**Starship wins when**:
- Need cross-shell consistency
- Prefer TOML over Zsh config
- Want active development/features
- Small-to-medium repos only

## Migration Guide

### Starship to Powerlevel10k

```bash
# 1. Install P10k
git clone --depth=1 https://github.com/romkatv/powerlevel10k.git \
  ${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/themes/powerlevel10k

# 2. Update .zshrc
# Remove: eval "$(starship init zsh)"
# Add: ZSH_THEME="powerlevel10k/powerlevel10k"

# 3. Run wizard
p10k configure

# 4. Add instant prompt (see above)
```

### Powerlevel10k to Starship

```bash
# 1. Install Starship
brew install starship  # or curl method

# 2. Update .zshrc
# Remove: ZSH_THEME="powerlevel10k/powerlevel10k"
# Remove: instant prompt block
# Remove: source ~/.p10k.zsh
# Add: eval "$(starship init zsh)"

# 3. Create config
mkdir -p ~/.config && touch ~/.config/starship.toml

# 4. Configure modules
# See templates in references/starship-config.md
```

## Benchmarking Your Setup

### Using zsh-bench

```bash
# Install
git clone https://github.com/romkatv/zsh-bench ~/zsh-bench

# Run benchmark
~/zsh-bench/zsh-bench

# Key metrics to watch:
# - first_prompt_lag_ms: <50ms ideal
# - command_lag_ms: <10ms ideal
```

### Manual Timing

```bash
# Zsh startup time
time zsh -i -c exit

# Per-command timing
TIMEFMT='%*E seconds'
time (for i in {1..10}; do zsh -i -c 'print -P "$PROMPT"' >/dev/null; done)

# Starship specific
starship timings
```

## Troubleshooting

### Slow Prompt

```bash
# Check which segment is slow
starship timings  # Starship
# or
zsh -xv  # P10k (verbose trace)

# Common culprits:
# - git_status in large repos
# - python/node version detection
# - cloud context (aws/azure/gcloud)
```

### P10k: gitstatus Failed

```bash
# Reinstall gitstatusd
rm -rf ~/.cache/gitstatus

# Restart zsh
exec zsh
```

### Starship: Git Timeout

```toml
# ~/.config/starship.toml

# Option 1: Increase timeout
command_timeout = 2000

# Option 2: Disable git_status
[git_status]
disabled = true
```

## Maintenance Status (2025)

### Powerlevel10k

> "I won't be breaking powerlevel10k and I don't expect it to break on its own."
> — romkatv, maintainer

- **Status**: Life support (works, no new features)
- **Bugs**: Only exceptional fixes
- **PRs**: Rarely merged
- **Recommendation**: Safe to use, won't break

### Starship

- **Status**: Actively developed
- **Releases**: Regular updates
- **Community**: Growing
- **Recommendation**: Good for cross-shell needs

## References

- [references/powerlevel10k-config.md](references/powerlevel10k-config.md) - Complete P10k configuration
- [references/starship-config.md](references/starship-config.md) - Starship TOML templates
- [references/performance-tuning.md](references/performance-tuning.md) - Advanced optimization
- [references/troubleshooting.md](references/troubleshooting.md) - Common issues and fixes

## External Links

- Powerlevel10k: https://github.com/romkatv/powerlevel10k
- Starship: https://starship.rs/
- zsh-bench: https://github.com/romkatv/zsh-bench
- gitstatus: https://github.com/romkatv/gitstatus
