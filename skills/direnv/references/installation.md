# direnv Installation Reference

Complete installation and shell configuration guide for all platforms.

## Installation Methods

### macOS

**Homebrew (Recommended):**

```bash
brew install direnv
```

**MacPorts:**

```bash
sudo port install direnv
```

**Nix:**

```bash
nix-env -i direnv
```

### Linux

**Debian/Ubuntu:**

```bash
sudo apt update
sudo apt install direnv
```

**Fedora:**

```bash
sudo dnf install direnv
```

**Arch Linux:**

```bash
sudo pacman -S direnv
```

**Alpine:**

```bash
apk add direnv
```

**Nix:**

```bash
nix-env -i direnv
```

**Binary Installer (Any Linux):**

```bash
curl -sfL https://direnv.net/install.sh | bash
```

**From Source:**

```bash
# Requires Go 1.16+
git clone https://github.com/direnv/direnv
cd direnv
make
sudo make install
```

### Windows

**Scoop:**

```powershell
scoop install direnv
```

**Chocolatey:**

```powershell
choco install direnv
```

**Git Bash/MSYS2:**

```bash
pacman -S direnv
```

**WSL:**

Use Linux installation methods.

### Verify Installation

```bash
direnv version
# Expected: 2.32.0 or higher
```

## Shell Hook Configuration

The shell hook is **required** for direnv to work. It must be added to your shell's configuration file.

### Zsh

Add to `~/.zshrc`:

```bash
eval "$(direnv hook zsh)"
```

**With Oh My Zsh:**

Add `direnv` to your plugins array in `~/.zshrc`:

```bash
plugins=(git docker direnv)
```

**With Prezto:**

Enable the direnv module in `~/.zpreztorc`:

```bash
zstyle ':prezto:load' pmodule \
  'environment' \
  'terminal' \
  'editor' \
  'history' \
  'directory' \
  'spectrum' \
  'utility' \
  'completion' \
  'prompt' \
  'direnv'
```

### Bash

Add to `~/.bashrc`:

```bash
eval "$(direnv hook bash)"
```

> For macOS with bash, also add to `~/.bash_profile` if it sources `~/.bashrc`.

### Fish

Add to `~/.config/fish/config.fish`:

```fish
direnv hook fish | source
```

### PowerShell

Add to PowerShell profile (`$PROFILE`):

```powershell
Invoke-Expression "$(direnv hook pwsh)"
```

### Elvish

Add to `~/.elvish/rc.elv`:

```elvish
eval (direnv hook elvish | slurp)
```

### Tcsh

Add to `~/.cshrc`:

```tcsh
eval `direnv hook tcsh`
```

### Nushell

Add to `$nu.config-path`:

```nu
$env.config = ($env.config | merge {
  hooks: {
    pre_prompt: [{ ||
      if (which direnv | is-empty) {
        return
      }
      direnv export json | from json | default {} | load-env
    }]
  }
})
```

### POSIX Shell

Add to `~/.profile`:

```sh
eval "$(direnv hook sh)"
```

## Applying Shell Configuration

After adding the hook, apply the changes:

```bash
# Zsh
source ~/.zshrc

# Bash
source ~/.bashrc

# Fish
source ~/.config/fish/config.fish
```

Or simply restart your terminal.

## Hook Placement Guidelines

1. **Place at the end** - The hook should be the last line in your config, after:
   - Other shell extensions (rvm, nvm, pyenv)
   - Prompt customizations
   - Path modifications

2. **After version managers** - If using asdf, rbenv, pyenv, nvm:

   ```bash
   # ~/.zshrc

   # Version managers first
   eval "$(pyenv init -)"
   eval "$(rbenv init -)"

   # direnv last
   eval "$(direnv hook zsh)"
   ```

## Updating direnv

### Homebrew

```bash
brew upgrade direnv
```

### Self-update (binary install)

```bash
direnv version  # Check current
curl -sfL https://direnv.net/install.sh | bash  # Reinstall latest
```

### Package Managers

```bash
# Debian/Ubuntu
sudo apt update && sudo apt upgrade direnv

# Fedora
sudo dnf upgrade direnv

# Arch
sudo pacman -Syu direnv
```

## Global Configuration

Create `~/.config/direnv/direnv.toml`:

```toml
[global]
# Hide environment diff in output
hide_env_diff = false

# Load .env files
load_dotenv = true

# Warn when using old stdlib functions
warn_timeout = "5s"

# Disable loading .envrc globally (emergency)
# disable_stdin = true

[whitelist]
# Auto-allow specific paths (use with caution)
# prefix = ["/home/user/trusted-projects"]
# exact = ["/home/user/specific-project/.envrc"]
```

## Verification

After installation, verify everything works:

```bash
# 1. Check version
direnv version

# 2. Create test directory
mkdir /tmp/direnv-test && cd /tmp/direnv-test

# 3. Create .envrc
echo 'export TEST_VAR=hello' > .envrc

# 4. Allow it
direnv allow

# 5. Verify variable is set
echo $TEST_VAR
# Should output: hello

# 6. Leave directory and verify unloading
cd /tmp
echo $TEST_VAR
# Should be empty

# 7. Cleanup
rm -rf /tmp/direnv-test
```

## Troubleshooting Installation

### Hook Not Working

1. Verify hook is in correct config file:

   ```bash
   # Zsh
   grep "direnv hook" ~/.zshrc

   # Bash
   grep "direnv hook" ~/.bashrc
   ```

2. Source the config:

   ```bash
   source ~/.zshrc  # or ~/.bashrc
   ```

3. Restart terminal completely

4. Check for conflicts:

   ```bash
   # Look for duplicate hooks
   grep -r "direnv" ~/.*rc ~/.*profile 2>/dev/null
   ```

### Permission Denied

```bash
# Make direnv executable
chmod +x $(which direnv)
```

### Old Version Warnings

```bash
# Update to latest
brew upgrade direnv  # macOS
sudo apt upgrade direnv  # Ubuntu
```

### PATH Issues

Ensure direnv is in PATH:

```bash
which direnv
# Should return path like /usr/local/bin/direnv

# If not found, add to PATH
export PATH="/usr/local/bin:$PATH"  # Add to shell config
```

## Uninstallation

### Homebrew

```bash
brew uninstall direnv
```

### Manual

```bash
# Remove binary
sudo rm $(which direnv)

# Remove configuration
rm -rf ~/.config/direnv
rm -rf ~/.local/share/direnv

# Remove hook from shell config (edit manually)
```

Remember to remove the hook from your shell configuration files.
