# direnv Standard Library Reference

Complete reference for all direnv stdlib functions.

## PATH Functions

### PATH_add

Add directories to the beginning of PATH.

```bash
# Add single directory
PATH_add bin

# Add multiple directories
PATH_add bin scripts tools

# Add node_modules binaries
PATH_add node_modules/.bin

# Absolute path
PATH_add /opt/custom/bin
```

### PATH_rm

Remove directories matching patterns from PATH.

```bash
# Remove by pattern (glob)
PATH_rm "*/.git/bin"

# Remove specific path
PATH_rm "/old/path/bin"
```

### path_add (lowercase)

Synonym for PATH_add.

```bash
path_add bin
```

### MANPATH_add

Add directories to MANPATH.

```bash
MANPATH_add man
MANPATH_add /opt/custom/share/man
```

## Environment File Functions

### dotenv

Load a .env file into the environment.

```bash
# Load .env from current directory
dotenv

# Load specific file
dotenv .env.local

# Load with path
dotenv config/.env

# Multiple files (loaded in order)
dotenv .env
dotenv .env.local
```

**.env format:**

```bash
# Comments are supported
KEY=value
QUOTED="value with spaces"
MULTILINE="line1\nline2"
EMPTY=
```

### dotenv_if_exists

Load .env file only if it exists (no error if missing).

```bash
# Safe loading
dotenv_if_exists .env.local
dotenv_if_exists .env.${APP_ENV}
```

### source_env

Source another .envrc file.

```bash
# Source specific file
source_env ../.envrc
source_env /path/to/.envrc

# Source relative path
source_env ../shared/.envrc
```

### source_env_if_exists

Source .envrc only if it exists.

```bash
source_env_if_exists .envrc.local
source_env_if_exists ../.envrc
```

### source_up

Load .envrc from parent directories (searches upward).

```bash
# Load first .envrc found in parent directories
source_up

# Specify maximum depth (default: unlimited)
source_up 2
```

### source_up_if_exists

Load parent .envrc if found, no error if not found.

```bash
source_up_if_exists
```

### source_url

Download and source a script from URL with hash verification.

```bash
# Source with SHA256 verification
source_url "https://example.com/script.sh" "sha256-abc123..."
```

## Layout Functions

Layouts configure the environment for specific programming languages.

### layout python / layout python3

Create and activate a Python virtual environment.

```bash
# Use default Python
layout python

# Use Python 3 explicitly
layout python3

# Use specific version
layout python python3.11

# Use specific interpreter path
layout python /usr/local/bin/python3.12
```

**What it does:**
- Creates virtualenv in `.direnv/python-<version>`
- Adds virtualenv to PATH
- Sets VIRTUAL_ENV environment variable

### layout pipenv

Use Pipenv for virtual environment management.

```bash
layout pipenv
```

**What it does:**
- Uses `pipenv --venv` to locate virtualenv
- Activates the Pipenv environment

### layout poetry

Use Poetry for virtual environment management.

```bash
layout poetry
```

### layout node

Configure Node.js environment.

```bash
layout node
```

**What it does:**
- Adds `node_modules/.bin` to PATH
- Sets NPM_CONFIG_PREFIX

### layout ruby

Configure Ruby environment with local gem installation.

```bash
layout ruby
```

**What it does:**
- Sets GEM_HOME to `.direnv/ruby`
- Adds gem bin directory to PATH

### layout go

Configure Go environment.

```bash
layout go
```

**What it does:**
- Sets GOPATH to current directory
- Adds `$GOPATH/bin` to PATH

### layout perl

Configure Perl local::lib environment.

```bash
layout perl
```

**What it does:**
- Sets up local::lib in `.direnv/perl5`
- Configures PERL5LIB and PATH

### layout julia

Configure Julia depot path.

```bash
layout julia
```

### layout r

Configure R library paths.

```bash
layout r
```

### layout anaconda / layout miniconda

Activate Anaconda/Miniconda environment.

```bash
# Use environment by name
layout anaconda myenv

# Use environment by path
layout anaconda /path/to/env
```

## Nix Functions

### use nix

Load environment from `shell.nix` or `default.nix`.

```bash
# Load from shell.nix
use nix

# Load from specific file
use nix -p python3 nodejs
```

### use flake

Load environment from a Nix flake.

```bash
# Load default devShell
use flake

# Load specific output
use flake ".#devShells.x86_64-linux.default"

# Load from nixpkgs
use flake "nixpkgs#hello"
```

> For performance, use [nix-direnv](https://github.com/nix-community/nix-direnv).

## Version Manager Functions

### use asdf

Load asdf version manager.

```bash
use asdf
```

### use node

Activate Node.js version (requires fnm, nodenv, or nvm).

```bash
# Use specific version (fuzzy matching)
use node 18
use node 18.17.0
use node lts

# Use version from .nvmrc
use node

# Use version from .node-version
use node
```

### use rbenv

Activate rbenv Ruby version.

```bash
use rbenv
```

### use pyenv

Activate pyenv Python version.

```bash
use pyenv
```

### use volta

Activate Volta Node.js version.

```bash
use volta
```

## Utility Functions

### has

Check if a command exists.

```bash
if has docker; then
  export DOCKER_HOST="unix:///var/run/docker.sock"
fi

if has uv; then
  layout_uv
else
  layout python3
fi
```

### expand_path

Expand relative path to absolute.

```bash
MYPATH=$(expand_path ./config)
export CONFIG_DIR="$MYPATH"
```

### find_up

Find a file by searching parent directories.

```bash
# Find package.json in current or parent directories
PACKAGE_JSON=$(find_up package.json)

if [[ -n "$PACKAGE_JSON" ]]; then
  export PROJECT_ROOT="$(dirname "$PACKAGE_JSON")"
fi
```

### user_rel_path

Convert absolute path to user-relative path.

```bash
# /home/user/projects -> ~/projects
SHORT_PATH=$(user_rel_path "$PWD")
```

### realpath.dirname / realpath.basename

Get directory name or base name of real path.

```bash
DIR=$(realpath.dirname "$PWD/.envrc")
NAME=$(realpath.basename "$PWD")
```

## Watch Functions

### watch_file

Trigger reload when file changes.

```bash
# Watch single file
watch_file package.json

# Watch multiple files
watch_file package.json package-lock.json

# Watch with glob
watch_file config/*.yaml
watch_file .tool-versions
```

### watch_dir

Watch directory for any changes (recursive).

```bash
watch_dir config
watch_dir src/templates
```

## Validation Functions

### env_vars_required

Fail if required environment variables are not set.

```bash
# Require single variable
env_vars_required API_KEY

# Require multiple variables
env_vars_required API_KEY DATABASE_URL REDIS_URL
```

### direnv_version

Require minimum direnv version.

```bash
# Require at least 2.32.0
direnv_version 2.32.0
```

## Logging Functions

### log_status

Log informational message.

```bash
log_status "using python $(python --version)"
log_status "kubernetes context: $(kubectl config current-context)"
```

### log_error

Log error message to stderr.

```bash
log_error "API_KEY not set"
```

## Git Functions

### on_git_branch

Check if on specific git branch.

```bash
if on_git_branch main; then
  export DEPLOY_ENV=production
elif on_git_branch staging; then
  export DEPLOY_ENV=staging
else
  export DEPLOY_ENV=development
fi

# Multiple branches
if on_git_branch main master; then
  export IS_DEFAULT_BRANCH=true
fi
```

## Control Functions

### strict_env

Enable strict mode (exit on undefined variables and errors).

```bash
strict_env

# After this, unset variable access will error
echo "$UNDEFINED_VAR"  # Will fail
```

### unstrict_env

Disable strict mode.

```bash
unstrict_env
```

### load_prefix

Configure environment for software installed in custom prefix.

```bash
# Load /opt/myapp/bin, /opt/myapp/lib, etc.
load_prefix /opt/myapp

# Adds to PATH, LD_LIBRARY_PATH, PKG_CONFIG_PATH, etc.
```

### semver_search

Find files matching semantic version pattern.

```bash
# Find python3.X binaries
PYTHON=$(semver_search /usr/bin "python" "3")
```

## Environment Export

### export_function

Export a bash function (use sparingly).

```bash
my_helper() {
  echo "helper function"
}
export_function my_helper
```

### setenv

Set environment variable (alias for export).

```bash
setenv MY_VAR "value"
```

## Advanced Functions

### fetchurl

Download file with caching.

```bash
# Download and cache
SCRIPT=$(fetchurl "https://example.com/script.sh" "sha256-...")
source "$SCRIPT"
```

### direnv_load

Load environment from subshell.

```bash
# Load from nix-shell
direnv_load nix-shell --run "direnv dump"

# Load from Docker
direnv_load docker run --rm myimage printenv
```

## Creating Custom Functions

Add to `~/.config/direnv/direnvrc`:

```bash
# Custom layout for uv (modern Python)
layout_uv() {
  local venv=".venv"

  if ! has uv; then
    log_error "uv not found"
    return 1
  fi

  if [[ ! -d "$venv" ]]; then
    log_status "creating venv with uv"
    uv venv
  fi

  VIRTUAL_ENV="$PWD/$venv"
  PATH_add "$VIRTUAL_ENV/bin"
  export VIRTUAL_ENV
  log_status "using uv virtualenv"
}

# AWS profile switcher
use_aws() {
  local profile="${1:-default}"
  export AWS_PROFILE="$profile"
  log_status "aws profile: $profile"
}

# Kubernetes context
use_kubectl() {
  local context="${1:-}"
  if [[ -n "$context" ]]; then
    kubectl config use-context "$context" >/dev/null 2>&1
    log_status "kubectl context: $context"
  fi
}

# Azure subscription
use_azure() {
  local subscription="${1:-}"
  if [[ -n "$subscription" ]]; then
    az account set --subscription "$subscription" >/dev/null 2>&1
    export AZURE_SUBSCRIPTION="$subscription"
    log_status "azure subscription: $subscription"
  fi
}

# Load secrets from 1Password
use_1password() {
  local vault="${1:-Personal}"
  local item="${2:-}"

  if ! has op; then
    log_error "1Password CLI not found"
    return 1
  fi

  if [[ -n "$item" ]]; then
    eval "$(op item get "$item" --vault "$vault" --format env)"
    log_status "loaded secrets from 1password: $item"
  fi
}
```

Usage:

```bash
# .envrc
layout uv
use_aws production
use_kubectl dev-cluster
use_azure my-subscription
```
