# Shell Prompt Troubleshooting

Common issues and solutions for Powerlevel10k and Starship.

## Quick Diagnostics

### Check Current Setup

```bash
# What shell?
echo $SHELL
echo $ZSH_VERSION

# What prompt?
echo $ZSH_THEME          # P10k via OMZ
which starship           # Starship installed?

# P10k status
[[ -f ~/.p10k.zsh ]] && echo "P10k config exists"

# Starship status
[[ -f ~/.config/starship.toml ]] && echo "Starship config exists"
```

### Timing Analysis

```bash
# Shell startup time
time zsh -i -c exit

# Starship module timing
starship timings

# P10k profiling (add to .zshrc)
zmodload zsh/zprof
# Then at end:
zprof
```

## Powerlevel10k Issues

### Icons/Glyphs Not Displaying

**Symptom**: Boxes, question marks, or missing icons

**Solution 1: Install Nerd Font**

```bash
# macOS
brew tap homebrew/cask-fonts
brew install --cask font-meslo-lg-nerd-font

# Or download manually from
# https://github.com/ryanoasis/nerd-fonts/releases
```

**Solution 2: Configure Terminal**

1. Open terminal preferences
2. Set font to "MesloLGS NF" or installed Nerd Font
3. Restart terminal

**Solution 3: Use ASCII-only mode**

```bash
# Re-run wizard with "no" to font questions
p10k configure
```

### Instant Prompt Errors

**Symptom**: Warnings about console output during instant prompt

**Solution 1: Move output above instant prompt block**

```zsh
# This BEFORE instant prompt:
echo "Welcome!"

# Instant prompt block
if [[ -r "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh" ]]; then
  source "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh"
fi

# Everything else AFTER
```

**Solution 2: Suppress warnings**

```zsh
# In ~/.p10k.zsh
typeset -g POWERLEVEL9K_INSTANT_PROMPT=quiet
```

**Solution 3: Disable instant prompt**

```zsh
# In ~/.p10k.zsh
typeset -g POWERLEVEL9K_INSTANT_PROMPT=off
```

### gitstatus Failed to Initialize

**Symptom**: `[ERROR]: gitstatus failed to initialize`

**Solution 1: Clear cache**

```bash
rm -rf ~/.cache/gitstatus
exec zsh
```

**Solution 2: Manual binary install**

```bash
# Check architecture
uname -m

# Download appropriate binary from
# https://github.com/romkatv/gitstatus/releases

# Place in ~/.cache/gitstatus/
```

**Solution 3: Build from source**

```bash
git clone --depth=1 https://github.com/romkatv/gitstatus.git
cd gitstatus
./build -w
```

### Slow in Git Repositories

**Symptom**: Prompt freezes when entering repo

**Solution 1: Reduce dirty check threshold**

```zsh
# ~/.p10k.zsh
typeset -g POWERLEVEL9K_VCS_MAX_INDEX_SIZE_DIRTY=100
```

**Solution 2: Disable dirty check**

```zsh
typeset -g POWERLEVEL9K_VCS_MAX_INDEX_SIZE_DIRTY=-1
```

**Solution 3: Disable git entirely**

```zsh
typeset -g POWERLEVEL9K_DISABLE_GITSTATUS=true
```

### Theme Not Loading

**Symptom**: Default zsh prompt instead of P10k

**Check 1: Theme path**

```bash
ls ${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/themes/powerlevel10k
```

**Check 2: .zshrc setting**

```bash
grep ZSH_THEME ~/.zshrc
# Should be: ZSH_THEME="powerlevel10k/powerlevel10k"
```

**Check 3: Oh My Zsh loading**

```bash
grep "source.*oh-my-zsh.sh" ~/.zshrc
```

**Solution: Reinstall**

```bash
rm -rf ${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/themes/powerlevel10k
git clone --depth=1 https://github.com/romkatv/powerlevel10k.git \
  ${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/themes/powerlevel10k
exec zsh
```

### Configuration Wizard Issues

**Symptom**: `p10k configure` doesn't work

**Solution 1: Source manually**

```bash
source ~/.oh-my-zsh/custom/themes/powerlevel10k/powerlevel10k.zsh-theme
p10k configure
```

**Solution 2: Reset config**

```bash
rm ~/.p10k.zsh
exec zsh
# Wizard should start automatically
```

## Starship Issues

### Prompt Not Showing

**Symptom**: Default shell prompt instead of Starship

**Check 1: Installation**

```bash
which starship
starship --version
```

**Check 2: Shell integration**

```bash
# Zsh
grep starship ~/.zshrc
# Should have: eval "$(starship init zsh)"

# Bash
grep starship ~/.bashrc
```

**Solution: Add integration**

```zsh
# ~/.zshrc
eval "$(starship init zsh)"
```

### Git Status Timeout

**Symptom**: `[WARN] - Executing command "/usr/bin/git" timed out`

**Solution 1: Increase timeout**

```toml
# ~/.config/starship.toml
command_timeout = 2000  # 2 seconds
```

**Solution 2: Disable git_status**

```toml
[git_status]
disabled = true
```

**Solution 3: Optimize git**

```bash
# For very large repos
git config core.untrackedCache true
git config core.fsmonitor true
```

### Module Not Appearing

**Symptom**: Expected module missing from prompt

**Check 1: Detection files**

```bash
# Show what Starship detects
starship explain
```

**Check 2: Module disabled**

```toml
# Check if disabled in config
[python]
disabled = false  # Make sure this isn't true
```

**Solution: Force detection**

```toml
[python]
detect_files = []
detect_folders = []
detect_extensions = []
python_binary = ["python3", "python"]
disabled = false
```

### Slow Prompt

**Symptom**: Noticeable delay after each command

**Step 1: Identify slow module**

```bash
starship timings
```

**Step 2: Disable culprit**

```toml
# If git_status is slow
[git_status]
disabled = true

# If python detection is slow
[python]
disabled = true
```

### Config Not Loading

**Symptom**: Changes to starship.toml have no effect

**Check 1: Config location**

```bash
echo $STARSHIP_CONFIG
ls ~/.config/starship.toml
```

**Check 2: TOML syntax**

```bash
# Validate TOML
starship config  # Will error on invalid syntax
```

**Solution: Specify config path**

```bash
export STARSHIP_CONFIG=~/.config/starship.toml
```

### Wrong Version Detected

**Symptom**: Shows wrong Python/Node/etc. version

**Solution 1: Specify binary path**

```toml
[python]
python_binary = ["/usr/local/bin/python3", "python3"]
```

**Solution 2: Check PATH order**

```bash
which python
which -a python  # All in PATH
```

## General Issues

### Prompt Appears Twice

**Symptom**: Duplicate prompts displayed

**Cause**: Multiple prompt initializations

**Solution**: Check for duplicate init calls

```bash
grep -E "(p10k|starship)" ~/.zshrc
# Remove duplicates
```

### Colors Wrong

**Symptom**: Incorrect or missing colors

**Check 1: Terminal color support**

```bash
echo $TERM
# Should be xterm-256color or similar
```

**Check 2: COLORTERM**

```bash
echo $COLORTERM
# Should be truecolor for full support
```

**Solution: Set terminal type**

```zsh
# ~/.zshrc
export TERM=xterm-256color
export COLORTERM=truecolor
```

### SSH Breaks Prompt

**Symptom**: Prompt works locally but not over SSH

**Check 1: TERM forwarding**

```bash
ssh -t user@host 'echo $TERM'
```

**Solution 1: Set TERM on remote**

```zsh
# Remote ~/.zshrc
export TERM=xterm-256color
```

**Solution 2: Configure SSH**

```
# ~/.ssh/config
Host *
  SetEnv TERM=xterm-256color
```

### tmux/screen Issues

**Symptom**: Prompt breaks in tmux

**Solution 1: tmux term setting**

```bash
# ~/.tmux.conf
set -g default-terminal "screen-256color"
set -ga terminal-overrides ",xterm-256color:Tc"
```

**Solution 2: Force shell**

```bash
# ~/.tmux.conf
set -g default-shell /bin/zsh
```

## Recovery Procedures

### Reset to Default Prompt

**Zsh without frameworks**:

```zsh
# Minimal .zshrc
PROMPT='%n@%m:%~%# '
```

**With Oh My Zsh**:

```zsh
# In .zshrc
ZSH_THEME="robbyrussell"
```

### Complete P10k Reset

```bash
# Remove all P10k files
rm -rf ~/.p10k.zsh
rm -rf ~/.cache/p10k-*
rm -rf ~/.cache/gitstatus

# Reinstall
rm -rf ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/themes/powerlevel10k
git clone --depth=1 https://github.com/romkatv/powerlevel10k.git \
  ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/themes/powerlevel10k

exec zsh
```

### Complete Starship Reset

```bash
# Remove config
rm ~/.config/starship.toml

# Remove from shell
# Edit ~/.zshrc and remove: eval "$(starship init zsh)"

# Uninstall
brew uninstall starship
# or
rm $(which starship)

exec zsh
```

## Getting Help

### Powerlevel10k

- GitHub Issues: https://github.com/romkatv/powerlevel10k/issues
- Note: Maintainer no longer responding (project on life support)
- Search existing issues for solutions

### Starship

- GitHub Discussions: https://github.com/starship/starship/discussions
- GitHub Issues: https://github.com/starship/starship/issues
- Discord: https://discord.gg/starship

### Debug Information to Collect

```bash
# System info
uname -a
echo $SHELL
echo $ZSH_VERSION
echo $TERM

# P10k
cat ~/.p10k.zsh | head -50
ls -la ~/.cache/gitstatus/

# Starship
starship --version
cat ~/.config/starship.toml
starship timings
starship explain
```
