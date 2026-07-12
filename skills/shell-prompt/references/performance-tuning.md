# Shell Prompt Performance Tuning

Advanced guide for optimizing shell prompt performance.

## Understanding Prompt Latency

### Key Metrics

| Metric | Acceptable | Good | Excellent |
|--------|-----------|------|-----------|
| First prompt lag | <200ms | <50ms | <20ms |
| Command lag | <50ms | <20ms | <10ms |
| Git status | <200ms | <50ms | <20ms |

### Perception Thresholds

- **<10ms**: Imperceptible, feels instant
- **10-50ms**: Barely noticeable
- **50-100ms**: Noticeable but acceptable
- **100-200ms**: Slow, annoying
- **>200ms**: Very slow, interrupts flow

## Benchmarking Tools

### zsh-bench (Comprehensive)

```bash
# Install
git clone https://github.com/romkatv/zsh-bench ~/zsh-bench

# Run benchmark
~/zsh-bench/zsh-bench

# Output metrics:
# - creates_tty: whether test runs in TTY
# - has_compsys: completion system loaded
# - has_syntax_highlighting: syntax highlighting enabled
# - has_autosuggestions: autosuggestions enabled
# - has_git_prompt: git info in prompt
# - first_prompt_lag_ms: time to first prompt
# - first_command_lag_ms: time for first command
# - command_lag_ms: subsequent command latency
# - input_lag_ms: input responsiveness
# - exit_time_ms: shell exit time
```

### Manual Timing

```bash
# Zsh startup time (10 iterations)
for i in {1..10}; do
  time zsh -i -c exit
done

# Average startup time
repeat 10 { time zsh -i -c exit } 2>&1 | grep real | awk '{sum+=$2} END {print sum/10}'

# Profile with zprof
# Add to top of .zshrc:
zmodload zsh/zprof

# Add to bottom of .zshrc:
zprof

# Then start new shell to see profile
```

### Starship Timing

```bash
# Per-module timing
starship timings

# Sample output:
#  aws           -   <1ms  -    ~
#  directory     -    4ms  -    ~/project
#  git_branch    -    2ms  -    main
#  git_status    -  185ms  -    [!+]  <- SLOW!
#  character     -   <1ms  -    >
```

## Common Performance Bottlenecks

### 1. Git Status in Large Repos

**Symptoms**: Prompt freezes when entering repo directory

**Causes**:
- Many untracked files
- Large index
- Slow disk I/O
- Remote git operations

**Solutions**:

```zsh
# Powerlevel10k: Limit dirty check
typeset -g POWERLEVEL9K_VCS_MAX_INDEX_SIZE_DIRTY=100

# Powerlevel10k: Disable git entirely
typeset -g POWERLEVEL9K_DISABLE_GITSTATUS=true
```

```toml
# Starship: Disable git_status
[git_status]
disabled = true

# Or increase timeout
command_timeout = 2000
```

### 2. Language Version Detection

**Symptoms**: Slow prompt in project directories

**Causes**:
- Python/Node/Ruby version managers
- Multiple detect_files checks
- Traversing up directory tree

**Solutions**:

```toml
# Starship: Disable language modules
[python]
disabled = true

[nodejs]
disabled = true

[ruby]
disabled = true

[package]
disabled = true
```

### 3. Cloud Context Lookups

**Symptoms**: Slow prompt with AWS/Azure/GCP modules

**Causes**:
- Reading config files
- API calls for credentials
- Token refresh

**Solutions**:

```zsh
# Powerlevel10k: Show only on relevant commands
typeset -g POWERLEVEL9K_AWS_SHOW_ON_COMMAND='aws|terraform'
typeset -g POWERLEVEL9K_KUBECONTEXT_SHOW_ON_COMMAND='kubectl|helm'
```

```toml
# Starship: Disable cloud modules
[aws]
disabled = true

[gcloud]
disabled = true

[azure]
disabled = true

[kubernetes]
disabled = true
```

### 4. Slow Shell Startup

**Symptoms**: Long delay opening new terminal

**Causes**:
- Heavy plugin loading
- Compinit regeneration
- Slow .zshrc execution

**Solutions**:

```zsh
# Lazy load completions (only regenerate daily)
autoload -Uz compinit
if [[ -n ~/.zcompdump(#qN.mh+24) ]]; then
  compinit
else
  compinit -C
fi

# Use instant prompt (P10k)
# Add at top of .zshrc - see P10k docs

# Defer slow plugins
zsh-defer source heavy-plugin.zsh
```

## Powerlevel10k Optimization

### Fastest P10k Config

```zsh
# ~/.p10k.zsh

# Minimal segments
typeset -g POWERLEVEL9K_LEFT_PROMPT_ELEMENTS=(dir vcs newline prompt_char)
typeset -g POWERLEVEL9K_RIGHT_PROMPT_ELEMENTS=(status command_execution_time)

# Lean style (no separators)
typeset -g POWERLEVEL9K_LEFT_SEGMENT_SEPARATOR=''
typeset -g POWERLEVEL9K_RIGHT_SEGMENT_SEPARATOR=''
typeset -g POWERLEVEL9K_LEFT_SUBSEGMENT_SEPARATOR=' '
typeset -g POWERLEVEL9K_RIGHT_SUBSEGMENT_SEPARATOR=' '

# Transient prompt
typeset -g POWERLEVEL9K_TRANSIENT_PROMPT=always

# Git optimization
typeset -g POWERLEVEL9K_VCS_MAX_INDEX_SIZE_DIRTY=100
typeset -g POWERLEVEL9K_VCS_BACKENDS=(git)

# Directory optimization
typeset -g POWERLEVEL9K_SHORTEN_STRATEGY=truncate_to_unique
typeset -g POWERLEVEL9K_SHORTEN_DIR_LENGTH=2

# Disable wizard
typeset -g POWERLEVEL9K_DISABLE_CONFIGURATION_WIZARD=true
```

### Instant Prompt Best Practices

```zsh
# At VERY TOP of .zshrc (before anything else)
if [[ -r "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh" ]]; then
  source "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh"
fi

# Everything that needs console input ABOVE this block
# Everything else BELOW

# Suppress warnings if needed
typeset -g POWERLEVEL9K_INSTANT_PROMPT=quiet
```

### gitstatus Tuning

```zsh
# Reduce index scan threshold
typeset -g POWERLEVEL9K_VCS_MAX_INDEX_SIZE_DIRTY=100

# Disable for huge repos (>10k files)
typeset -g POWERLEVEL9K_VCS_MAX_INDEX_SIZE_DIRTY=-1

# Only show branch, not status
typeset -g POWERLEVEL9K_VCS_GIT_HOOKS=(git-remotebranch)
```

## Starship Optimization

### Fastest Starship Config

```toml
# ~/.config/starship.toml

# Minimal format
format = "$directory$git_branch$character"
add_newline = false
command_timeout = 500

[directory]
truncation_length = 2
truncate_to_repo = true
style = "cyan"

[git_branch]
format = "[$branch]($style) "
style = "purple"
truncation_length = 15

# DISABLE git_status (biggest impact)
[git_status]
disabled = true

[character]
success_symbol = "[>](green)"
error_symbol = "[>](red)"

# Disable ALL language detectors
[python]
disabled = true

[nodejs]
disabled = true

[rust]
disabled = true

[golang]
disabled = true

[java]
disabled = true

[ruby]
disabled = true

[php]
disabled = true

[package]
disabled = true

# Disable cloud contexts
[aws]
disabled = true

[gcloud]
disabled = true

[azure]
disabled = true

[kubernetes]
disabled = true
```

### Timeout Configuration

```toml
# Global timeout (default 500ms)
command_timeout = 1000

# For specific modules that need more time
# (Individual modules don't have timeout settings,
#  but you can increase global timeout)
```

## Shell Configuration Optimization

### Lazy Loading

```zsh
# Lazy load nvm (slow by default)
lazy_load_nvm() {
  unset -f nvm node npm npx
  export NVM_DIR="$HOME/.nvm"
  [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
}
nvm() { lazy_load_nvm && nvm "$@" }
node() { lazy_load_nvm && node "$@" }
npm() { lazy_load_nvm && npm "$@" }
npx() { lazy_load_nvm && npx "$@" }

# Lazy load pyenv
lazy_load_pyenv() {
  unset -f pyenv python python3 pip pip3
  export PYENV_ROOT="$HOME/.pyenv"
  eval "$(pyenv init -)"
}
pyenv() { lazy_load_pyenv && pyenv "$@" }
python() { lazy_load_pyenv && python "$@" }
python3() { lazy_load_pyenv && python3 "$@" }
```

### Completion Caching

```zsh
# Only regenerate completions once per day
autoload -Uz compinit
if [[ -n ${ZDOTDIR:-$HOME}/.zcompdump(#qN.mh+24) ]]; then
  compinit
else
  compinit -C  # Skip security check
fi
```

### Plugin Manager Optimization

```zsh
# Zinit turbo mode (deferred loading)
zinit ice wait lucid
zinit light zsh-users/zsh-autosuggestions

zinit ice wait lucid atload'_zsh_autosuggest_start'
zinit light zsh-users/zsh-syntax-highlighting

# Compile plugins
zinit ice compile'*.zsh'
zinit light some/plugin
```

## Measuring Improvements

### Before/After Comparison

```bash
# Create baseline
~/zsh-bench/zsh-bench > ~/prompt-baseline.txt

# Make changes to config
# ...

# Compare
~/zsh-bench/zsh-bench > ~/prompt-optimized.txt
diff ~/prompt-baseline.txt ~/prompt-optimized.txt
```

### Continuous Monitoring

```zsh
# Add to .zshrc for timing info
REPORTTIME=1  # Report commands taking >1 second

# Prompt render time in RPROMPT
RPROMPT='%F{8}${PROMPT_RENDER_TIME}ms%f'
```

## Platform-Specific Tips

### macOS

```bash
# Use fast git from Homebrew
brew install git

# Ensure using Homebrew git, not Xcode
which git  # Should be /opt/homebrew/bin/git
```

### Linux

```bash
# Increase inotify watches for large repos
echo 'fs.inotify.max_user_watches=524288' | sudo tee -a /etc/sysctl.conf
sudo sysctl -p
```

### WSL

```toml
# Starship: Avoid Windows paths
[directory]
truncation_length = 3
# Don't traverse Windows filesystem
```

```zsh
# P10k: Avoid Windows git
export GIT_OPTIONAL_LOCKS=0
```

## Summary: Optimization Checklist

1. **[ ] Benchmark current state** with zsh-bench
2. **[ ] Enable instant prompt** (P10k only)
3. **[ ] Disable git_status** in large repos
4. **[ ] Remove unused language modules**
5. **[ ] Disable cloud context modules** or limit to relevant commands
6. **[ ] Lazy load version managers** (nvm, pyenv, rbenv)
7. **[ ] Cache completions** (compinit -C)
8. **[ ] Use lean/minimal prompt style**
9. **[ ] Reduce segment count** to essentials
10. **[ ] Benchmark again** and compare
