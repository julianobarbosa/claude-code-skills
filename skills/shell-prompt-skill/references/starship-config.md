# Starship Configuration Reference

Complete guide to configuring Starship prompt with TOML.

## File Location

```
~/.config/starship.toml     # Main config file
$STARSHIP_CONFIG            # Override via environment variable
```

## Installation

### Package Managers

```bash
# macOS
brew install starship

# Arch Linux
pacman -S starship

# Windows (scoop)
scoop install starship

# Windows (winget)
winget install starship
```

### Binary Install

```bash
# Linux/macOS
curl -sS https://starship.rs/install.sh | sh

# With specific directory
curl -sS https://starship.rs/install.sh | sh -s -- --bin-dir ~/.local/bin
```

### Cargo

```bash
cargo install starship --locked
```

## Shell Integration

### Zsh

```zsh
# ~/.zshrc
eval "$(starship init zsh)"
```

### Bash

```bash
# ~/.bashrc
eval "$(starship init bash)"
```

### Fish

```fish
# ~/.config/fish/config.fish
starship init fish | source
```

### PowerShell

```powershell
# Microsoft.PowerShell_profile.ps1
Invoke-Expression (&starship init powershell)
```

### Nushell

```nu
# config.nu
use ~/.cache/starship/init.nu
```

## Basic Configuration

### Minimal Fast Config

```toml
# ~/.config/starship.toml

# Prompt format
format = """
$directory\
$git_branch\
$git_status\
$character"""

# Disable newline at start
add_newline = false

# Character
[character]
success_symbol = "[>](bold green)"
error_symbol = "[>](bold red)"
```

### Full-Featured Config

```toml
# ~/.config/starship.toml

format = """
[┌─](bold blue)$os$username$hostname$directory$git_branch$git_status$git_state
[└─](bold blue)$character"""

add_newline = false
command_timeout = 1000

[os]
disabled = false
style = "bold white"

[username]
show_always = false
style_user = "bold yellow"
format = "[$user]($style)@"

[hostname]
ssh_only = true
format = "[$hostname]($style):"
style = "bold green"

[directory]
truncation_length = 3
truncate_to_repo = true
style = "bold cyan"
format = "[$path]($style)[$read_only]($read_only_style) "

[git_branch]
format = "[$symbol$branch(:$remote_branch)]($style) "
symbol = " "
style = "bold purple"

[git_status]
format = '([$all_status$ahead_behind]($style))'
style = "bold red"
conflicted = "="
ahead = "⇡${count}"
behind = "⇣${count}"
diverged = "⇕⇡${ahead_count}⇣${behind_count}"
untracked = "?${count}"
stashed = "*${count}"
modified = "!${count}"
staged = "+${count}"
renamed = "»${count}"
deleted = "✘${count}"

[character]
success_symbol = "[❯](bold green)"
error_symbol = "[❯](bold red)"
vimcmd_symbol = "[❮](bold green)"
```

## Module Configuration

### Directory

```toml
[directory]
truncation_length = 3
truncate_to_repo = true
truncation_symbol = "…/"
home_symbol = "~"
read_only = " 󰌾"
read_only_style = "bold red"
style = "bold cyan"
format = "[$path]($style)[$read_only]($read_only_style) "

# Substitutions
[directory.substitutions]
"Documents" = "󰈙 "
"Downloads" = " "
"Music" = " "
"Pictures" = " "
"~/projects" = " "
```

### Git Branch

```toml
[git_branch]
format = "[$symbol$branch(:$remote_branch)]($style) "
symbol = " "
style = "bold purple"
truncation_length = 20
truncation_symbol = "…"
only_attached = false
always_show_remote = false
```

### Git Status

```toml
[git_status]
format = '([\[$all_status$ahead_behind\]]($style) )'
style = "bold red"
conflicted = "="
ahead = "⇡${count}"
behind = "⇣${count}"
diverged = "⇕⇡${ahead_count}⇣${behind_count}"
untracked = "?${count}"
stashed = "$${count}"
modified = "!${count}"
staged = "+${count}"
renamed = "»${count}"
deleted = "✘${count}"
# Performance: disable if slow
disabled = false
```

### Git State

```toml
[git_state]
format = '\([$state( $progress_current/$progress_total)]($style)\) '
rebase = "REBASING"
merge = "MERGING"
revert = "REVERTING"
cherry_pick = "CHERRY-PICKING"
bisect = "BISECTING"
am = "AM"
am_or_rebase = "AM/REBASE"
style = "bold yellow"
```

### Command Duration

```toml
[cmd_duration]
min_time = 2000  # milliseconds
format = "took [$duration]($style) "
style = "bold yellow"
show_milliseconds = false
show_notifications = false  # Desktop notifications
min_time_to_notify = 45000
```

### Status (Exit Code)

```toml
[status]
format = '[$symbol$status]($style) '
symbol = "✖ "
success_symbol = ""
not_executable_symbol = "🚫"
not_found_symbol = "🔍"
sigint_symbol = "🧱"
signal_symbol = "⚡"
style = "bold red"
map_symbol = true
disabled = false
```

### Python

```toml
[python]
format = '[${symbol}${pyenv_prefix}(${version})(\($virtualenv\))]($style) '
symbol = " "
style = "bold yellow"
pyenv_version_name = false
pyenv_prefix = "pyenv "
python_binary = ["python", "python3", "python2"]
detect_extensions = ["py"]
detect_files = [".python-version", "Pipfile", "pyproject.toml", "requirements.txt", "setup.py", "tox.ini"]
detect_folders = []
# Disable if causing slowness
disabled = false
```

### Node.js

```toml
[nodejs]
format = "[$symbol($version)]($style) "
symbol = " "
style = "bold green"
detect_extensions = ["js", "mjs", "cjs", "ts", "mts", "cts"]
detect_files = ["package.json", ".node-version", ".nvmrc"]
detect_folders = ["node_modules"]
not_capable_style = "bold red"
disabled = false
```

### Kubernetes

```toml
[kubernetes]
format = '[$symbol$context( \($namespace\))]($style) '
symbol = "☸ "
style = "bold blue"
disabled = false
# Only show on specific commands
detect_files = []
detect_folders = []
detect_extensions = []
detect_env_vars = ["KUBECONFIG"]

# Context aliases
[kubernetes.context_aliases]
"gke_.*_(?P<cluster>[\\w-]+)" = "gke-$cluster"
"arn:aws:eks:.*:.*:cluster/(?P<cluster>[\\w-]+)" = "eks-$cluster"
```

### AWS

```toml
[aws]
format = '[$symbol($profile)(\($region\))(\[$duration\])]($style) '
symbol = " "
style = "bold yellow"
disabled = false
expiration_symbol = "X"
force_display = false

[aws.region_aliases]
us-east-1 = "ue1"
us-west-2 = "uw2"
eu-west-1 = "ew1"

[aws.profile_aliases]
CompanyAccount-production = "prod"
CompanyAccount-development = "dev"
```

### Azure

```toml
[azure]
format = "[$symbol($subscription)]($style) "
symbol = " "
style = "bold blue"
disabled = false
```

### Docker

```toml
[docker_context]
format = "[$symbol$context]($style) "
symbol = " "
style = "bold blue"
only_with_files = true
detect_files = ["docker-compose.yml", "docker-compose.yaml", "Dockerfile"]
detect_folders = []
disabled = false
```

### Terraform

```toml
[terraform]
format = "[$symbol$workspace]($style) "
symbol = "💠 "
style = "bold 105"
detect_files = [".terraform", "*.tf", "*.hcl"]
detect_folders = [".terraform"]
disabled = false
```

### Time

```toml
[time]
format = "[$time]($style) "
style = "bold white"
use_12hr = false
time_format = "%H:%M"
utc_time_offset = "local"
disabled = true  # Disabled by default
time_range = "-"  # Always show, or use "09:00:00-17:00:00"
```

## Performance Optimization

### Minimal Config for Speed

```toml
# Fastest possible Starship config

format = "$directory$git_branch$character"
add_newline = false
command_timeout = 500

[directory]
truncation_length = 2
truncate_to_repo = true

[git_branch]
format = "[$branch]($style) "
style = "purple"

# Disable git_status (biggest performance hit)
[git_status]
disabled = true

[character]
success_symbol = "[>](green)"
error_symbol = "[>](red)"

# Disable all language detectors
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

[package]
disabled = true
```

### Increase Timeouts

```toml
# For large repos
command_timeout = 2000  # 2 seconds (default 500ms)

[git_status]
disabled = false  # Keep enabled but with longer timeout
```

### Disable Specific Modules

```toml
# Modules that can be slow
[python]
disabled = true

[nodejs]
disabled = true

[package]
disabled = true

[git_status]
disabled = true  # Biggest impact on large repos
```

## Debugging

### Show Timing Per Module

```bash
starship timings
```

Output:
```
 aws           -   <1ms  -    ~
 character     -   <1ms  -    >
 cmd_duration  -   <1ms  -
 directory     -    4ms  -    ~/projects/app
 git_branch    -    2ms  -    main
 git_status    -  185ms  -    [!+]
```

### Explain Current Prompt

```bash
starship explain
```

### Check Configuration

```bash
starship config
```

### Print Prompt

```bash
starship prompt
```

## Custom Modules

### Basic Custom Command

```toml
[custom.giturl]
command = "git remote get-url origin | sed 's/.*github.com[:\\/]//' | sed 's/.git$//'"
when = "git rev-parse --git-dir 2>/dev/null"
format = "[$output]($style) "
style = "bold cyan"
```

### Environment Variable

```toml
[env_var.KUBECONFIG]
format = "[$env_value]($style) "
style = "bold yellow"
disabled = false
```

### Custom with Shell

```toml
[custom.docker_host]
command = "echo $DOCKER_HOST | sed 's|tcp://||'"
when = '[ -n "$DOCKER_HOST" ]'
shell = ["bash", "--noprofile", "--norc"]
format = "[🐋 $output]($style) "
style = "bold blue"
```

## Presets

### Apply a Preset

```bash
# List available presets
starship preset --list

# Apply preset
starship preset nerd-font-symbols -o ~/.config/starship.toml
starship preset plain-text-symbols -o ~/.config/starship.toml
starship preset pure-preset -o ~/.config/starship.toml
starship preset tokyo-night -o ~/.config/starship.toml
```

### Popular Presets

- `nerd-font-symbols` - Uses Nerd Font icons
- `plain-text-symbols` - ASCII only, no special fonts
- `pure-preset` - Minimal like Pure prompt
- `tokyo-night` - Dark theme inspired by Tokyo Night
- `gruvbox-rainbow` - Gruvbox color scheme
- `pastel-powerline` - Soft colors with powerline

## Common Issues

### Git Status Slow

```toml
# Option 1: Disable
[git_status]
disabled = true

# Option 2: Increase timeout
command_timeout = 2000
```

### Module Not Showing

```bash
# Check if module is detecting correctly
cd /path/to/project
starship explain

# Force module to show
[python]
detect_files = []
detect_folders = []
detect_extensions = []
python_binary = ["python3"]
```

### Wrong Version Detected

```toml
# Specify binary path
[python]
python_binary = ["/usr/local/bin/python3", "python3", "python"]
```

### Prompt Too Slow

```bash
# Identify slow modules
starship timings

# Disable culprits
[git_status]
disabled = true

[python]
disabled = true
```
