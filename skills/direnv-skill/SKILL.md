---
name: direnv
description: Guide for using direnv - a shell extension for loading directory-specific environment variables. Use when setting up project environments, creating .envrc files, configuring per-project environment variables, integrating with Python/Node/Ruby/Go layouts, working with Nix flakes, or troubleshooting environment loading issues on macOS and Linux.
---

# direnv Skill

Shell extension for loading and unloading environment variables based on the current directory.

## Overview

direnv enables:
- Per-project environment configurations
- Automatic loading of 12-factor app environment variables
- Isolated development environments with language-specific layouts
- Secure allowlist-based security model
- Integration with Nix, asdf, and version managers

## Quick Start

### Installation

```bash
# macOS
brew install direnv

# Linux (Debian/Ubuntu)
sudo apt install direnv

# Linux (binary)
curl -sfL https://direnv.net/install.sh | bash

# Verify
direnv version
```

### Shell Hook Configuration

**Zsh** (`~/.zshrc`):
```bash
eval "$(direnv hook zsh)"
```

**Bash** (`~/.bashrc`):
```bash
eval "$(direnv hook bash)"
```

**Fish** (`~/.config/fish/config.fish`):
```fish
direnv hook fish | source
```

> Place hook at end of file, after other shell extensions.

### Basic Usage

```bash
# Create .envrc
echo 'export MY_VAR=value' > .envrc

# Allow the .envrc (required for security)
direnv allow

# Block an .envrc
direnv deny

# Force reload
direnv reload

# Check status
direnv status
```

## Essential Commands

| Command | Description |
|---------|-------------|
| `direnv allow [path]` | Allow/trust an .envrc file |
| `direnv deny [path]` | Revoke trust from .envrc |
| `direnv reload` | Force reload current .envrc |
| `direnv status` | Show current direnv state |
| `direnv edit` | Open .envrc in $EDITOR |
| `direnv prune` | Remove expired/revoked .envrc |
| `direnv version` | Show installed version |

## Standard Library (stdlib)

direnv includes a powerful stdlib. Use these functions instead of raw exports.

### PATH Management

```bash
# Add to PATH (prepends safely)
PATH_add bin
PATH_add node_modules/.bin
PATH_add scripts

# Add multiple paths
PATH_add bin scripts tools

# Remove from PATH
PATH_rm "*/.git/bin"
```

### Environment File Loading

```bash
# Load .env file
dotenv

# Load specific file
dotenv .env.local

# Load if exists (no error if missing)
dotenv_if_exists .env.local

# Load parent .envrc
source_up

# Load specific .envrc
source_env ../.envrc

# Load if exists
source_env_if_exists .envrc.local
```

### Language Layouts

```bash
# Python - creates virtualenv in .direnv/
layout python
layout python3
layout python python3.11

# Node.js - adds node_modules/.bin to PATH
layout node

# Ruby - sets GEM_HOME
layout ruby

# Go - configures GOPATH
layout go

# Perl - local::lib
layout perl

# Pipenv
layout pipenv
```

### Nix Integration

```bash
# Load nix-shell environment
use nix

# Load Nix flake
use flake

# Specific flake
use flake "nixpkgs#hello"
```

> For better flakes support: [nix-direnv](https://github.com/nix-community/nix-direnv)

### Version Managers

```bash
# rbenv
use rbenv

# Node.js (fuzzy matching)
use node 18
use node 18.17.0

# From .nvmrc
use node
```

### Validation

```bash
# Require variables
env_vars_required API_KEY DATABASE_URL

# Watch for file changes
watch_file package.json
watch_file config/*.yaml
watch_dir config

# Check git branch
if on_git_branch main; then
  export DEPLOY_ENV=production
fi

# Minimum version
direnv_version 2.32.0

# Strict mode (exit on errors)
strict_env
```

## Recommended .envrc Template

```bash
#!/usr/bin/env bash
# .envrc - Project environment configuration

# Enforce direnv version
direnv_version 2.32.0

# Load .env file if exists
dotenv_if_exists

# Load local overrides (not committed)
source_env_if_exists .envrc.local

# Language-specific layout
layout node
# or: layout python3

# Add project paths
PATH_add bin
PATH_add scripts

# Development settings
export NODE_ENV=development
export LOG_LEVEL=debug

# Watch configuration files
watch_file package.json
watch_file .tool-versions
```

## Project Structure Best Practice

```
my-project/
├── .envrc           # Development environment (committed)
├── .envrc.local     # Local overrides (gitignored)
├── .env             # Environment variables (gitignored)
├── .env.example     # Template for team members (committed)
└── .direnv/         # Cache directory (gitignored)
```

### .gitignore

```gitignore
# Environment files with secrets
.env
.env.local
.envrc.local

# direnv cache
.direnv/
```

## Layered Configuration

Use parent directory inheritance:

```bash
# ~/projects/.envrc (global dev settings)
export EDITOR=vim
export PAGER=less

# ~/projects/api/.envrc
source_up  # Inherit from parent
export API_PORT=3000
layout node

# ~/projects/api/feature-x/.envrc
source_up  # Inherit from api
export FEATURE_FLAG=true
```

## Custom Extensions

Create at `~/.config/direnv/direnvrc`:

```bash
# ~/.config/direnv/direnvrc

# Kubernetes context switcher
use_kubernetes() {
  local context="${1:-default}"
  export KUBECONFIG="${HOME}/.kube/config"
  kubectl config use-context "$context" >/dev/null 2>&1
  log_status "kubernetes context: $context"
}

# AWS profile switcher
use_aws() {
  local profile="${1:-default}"
  export AWS_PROFILE="$profile"
  log_status "aws profile: $profile"
}

# Azure subscription
use_azure() {
  local subscription="$1"
  export AZURE_SUBSCRIPTION="$subscription"
  az account set --subscription "$subscription" >/dev/null 2>&1
  log_status "azure subscription: $subscription"
}

# uv Python layout (modern alternative)
layout_uv() {
  if ! has uv; then
    log_error "uv not found. Install: curl -LsSf https://astral.sh/uv/install.sh | sh"
    return 1
  fi

  VIRTUAL_ENV="$(pwd)/.venv"
  if [[ ! -d "$VIRTUAL_ENV" ]]; then
    uv venv
  fi

  PATH_add "$VIRTUAL_ENV/bin"
  export VIRTUAL_ENV
}
```

Usage in .envrc:

```bash
use kubernetes dev-cluster
use aws production
layout uv
```

## Common Patterns

### Python with uv

```bash
# .envrc
direnv_version 2.32.0
dotenv_if_exists

# Use uv for Python
if has uv; then
  layout_uv
else
  layout python3
fi

export PYTHONDONTWRITEBYTECODE=1
```

### Node.js Project

```bash
# .envrc
direnv_version 2.32.0
dotenv_if_exists
source_env_if_exists .envrc.local

layout node

export NODE_ENV=development
export PORT=3000

watch_file package.json
```

### Kubernetes Development

```bash
# .envrc
dotenv_if_exists

use_kubernetes dev-cluster

export KUBECONFIG="${HOME}/.kube/config"
export KUBE_NAMESPACE=my-app

PATH_add bin
```

### Multi-Environment Support

```bash
# .envrc
direnv_version 2.32.0

# Determine environment
if on_git_branch main; then
  ENV=production
elif on_git_branch staging; then
  ENV=staging
else
  ENV=development
fi

export APP_ENV="$ENV"

# Load environment-specific config
dotenv_if_exists ".env.$ENV"
source_env_if_exists ".envrc.$ENV"

log_status "environment: $ENV"
```

## Troubleshooting Quick Reference

```bash
# Check status
direnv status

# Force reload
direnv reload

# Re-allow .envrc
direnv allow

# Debug environment
direnv dump
direnv show_dump

# Export for debugging
direnv export bash
```

### Common Issues

| Issue | Solution |
|-------|----------|
| Environment not loading | Run `direnv allow` |
| Hook not working | Verify hook in shell config, restart shell |
| Slow loading | Use nix-direnv for Nix; reduce watch_file calls |
| Variables not unloading | Check for `export -f` functions; restart shell |

## IDE Integration

### VS Code

Install [direnv extension](https://marketplace.visualstudio.com/items?itemName=mkhl.direnv).

### JetBrains IDEs

Install [direnv integration plugin](https://plugins.jetbrains.com/plugin/15285-direnv-integration).

### Emacs

```elisp
(use-package envrc
  :hook (after-init . envrc-global-mode))
```

### Vim/Neovim

```vim
" Use direnv.vim plugin
Plug 'direnv/direnv.vim'
```

## Security Notes

1. **Always review .envrc before allowing** - direnv executes arbitrary code
2. **Never commit secrets** - Use .env files in .gitignore
3. **Use .envrc.local for sensitive overrides** - Keep local, never commit
4. **Trust hierarchy** - Parent directories can override child settings

## References

- `references/installation.md` - Complete installation guide
- `references/stdlib-functions.md` - Full stdlib reference
- `references/troubleshooting.md` - Extended troubleshooting
- Official docs: https://direnv.net/
- Stdlib reference: https://direnv.net/man/direnv-stdlib.1.html
- nix-direnv: https://github.com/nix-community/nix-direnv
