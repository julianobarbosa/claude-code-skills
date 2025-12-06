# direnv Troubleshooting Reference

Comprehensive troubleshooting guide for common direnv issues.

## Diagnostic Commands

```bash
# Check direnv status
direnv status

# Show current environment dump
direnv dump

# Show human-readable diff
direnv show_dump

# Export in shell format
direnv export bash
direnv export zsh
direnv export fish

# Force reload
direnv reload

# Check version
direnv version

# Edit .envrc with $EDITOR
direnv edit
```

## Common Issues

### Issue: Environment Not Loading

**Symptoms:**
- Variables not set after entering directory
- No direnv output on `cd`

**Diagnostic:**

```bash
cd /path/to/project
direnv status
```

**Solutions:**

1. **Allow the .envrc:**

   ```bash
   direnv allow
   ```

2. **Verify hook is installed:**

   ```bash
   # Zsh
   grep "direnv hook" ~/.zshrc

   # Bash
   grep "direnv hook" ~/.bashrc
   ```

3. **Source shell config:**

   ```bash
   source ~/.zshrc  # or ~/.bashrc
   ```

4. **Restart terminal completely**

5. **Force reload:**

   ```bash
   direnv reload
   ```

---

### Issue: Shell Hook Not Working

**Symptoms:**
- `direnv: command not found`
- No environment changes on `cd`

**Solutions:**

1. **Check if direnv is in PATH:**

   ```bash
   which direnv
   type direnv
   ```

2. **Add hook to correct file:**

   | Shell | File |
   |-------|------|
   | Zsh | `~/.zshrc` |
   | Bash | `~/.bashrc` (Linux) or `~/.bash_profile` (macOS) |
   | Fish | `~/.config/fish/config.fish` |

3. **Hook placement - must be at END of file:**

   ```bash
   # ~/.zshrc

   # ... other configuration ...
   # pyenv, rbenv, nvm, etc.

   # direnv hook LAST
   eval "$(direnv hook zsh)"
   ```

4. **Interactive shell only:**

   For bash, ensure hook is in interactive config:

   ```bash
   # ~/.bashrc
   if [[ $- == *i* ]]; then
     eval "$(direnv hook bash)"
   fi
   ```

---

### Issue: .envrc Blocked / Not Trusted

**Symptoms:**

```
direnv: error /path/to/.envrc is blocked. Run `direnv allow` to approve its content
```

**Solutions:**

1. **Review and allow:**

   ```bash
   cat .envrc  # Review content
   direnv allow
   ```

2. **Allow specific path:**

   ```bash
   direnv allow /path/to/project
   ```

3. **Auto-allow trusted paths** (in `~/.config/direnv/direnv.toml`):

   ```toml
   [whitelist]
   prefix = ["/home/user/trusted-projects"]
   ```

   > Use with caution - security risk.

---

### Issue: Slow Loading / Performance

**Symptoms:**
- Shell prompt delayed on `cd`
- High CPU usage

**Diagnostic:**

```bash
# Time the loading
time (cd /project && direnv export bash)
```

**Solutions:**

1. **Reduce watch_file calls:**

   ```bash
   # Instead of many watch_file
   watch_file file1 file2 file3

   # Use fewer watches
   watch_file package.json
   ```

2. **Use nix-direnv for Nix:**

   Install [nix-direnv](https://github.com/nix-community/nix-direnv):

   ```bash
   # Caches nix-shell evaluation
   nix-env -i nix-direnv
   ```

   Then in `.envrc`:

   ```bash
   if ! has nix_direnv_version || ! nix_direnv_version 2.3.0; then
     source_url "https://raw.githubusercontent.com/nix-community/nix-direnv/2.3.0/direnvrc" "sha256-..."
   fi
   use flake
   ```

3. **Minimize source_up calls:**

   ```bash
   # Only source_up if needed
   source_up_if_exists
   ```

4. **Cache expensive operations:**

   ```bash
   # Cache in .direnv/
   CACHE_DIR=".direnv/cache"
   mkdir -p "$CACHE_DIR"

   if [[ ! -f "$CACHE_DIR/expensive-result" ]]; then
     expensive_command > "$CACHE_DIR/expensive-result"
   fi
   source "$CACHE_DIR/expensive-result"
   ```

---

### Issue: Variables Not Unloading

**Symptoms:**
- Environment variables persist after leaving directory
- Old values remain

**Solutions:**

1. **Check for exported functions:**

   ```bash
   # Functions persist across direnv
   # Avoid export_function when possible
   ```

2. **Restart shell:**

   ```bash
   exec $SHELL
   ```

3. **Clear direnv cache:**

   ```bash
   rm -rf .direnv/
   direnv reload
   ```

4. **Verify unload:**

   ```bash
   cd /project
   echo $MY_VAR  # Should be set
   cd /
   echo $MY_VAR  # Should be empty
   ```

---

### Issue: Layout Python Not Working

**Symptoms:**
- Virtual environment not created
- Wrong Python version

**Diagnostic:**

```bash
ls -la .direnv/
python --version
which python
```

**Solutions:**

1. **Clear and recreate:**

   ```bash
   rm -rf .direnv/
   direnv reload
   ```

2. **Specify Python version:**

   ```bash
   layout python python3.11
   ```

3. **Check Python availability:**

   ```bash
   which python3.11
   python3.11 --version
   ```

4. **Use uv instead (modern):**

   ```bash
   # In ~/.config/direnv/direnvrc
   layout_uv() {
     if [[ ! -d .venv ]]; then
       uv venv
     fi
     VIRTUAL_ENV="$PWD/.venv"
     PATH_add "$VIRTUAL_ENV/bin"
     export VIRTUAL_ENV
   }
   ```

   ```bash
   # In .envrc
   layout uv
   ```

---

### Issue: dotenv Not Loading

**Symptoms:**
- Variables from .env not available
- `dotenv: command not found`

**Solutions:**

1. **Check .env file exists:**

   ```bash
   ls -la .env
   ```

2. **Verify .env format:**

   ```bash
   # Valid format
   KEY=value
   QUOTED="value with spaces"

   # Invalid (no export needed)
   export KEY=value  # Remove 'export'
   ```

3. **Use dotenv_if_exists:**

   ```bash
   dotenv_if_exists  # No error if missing
   ```

4. **Check file permissions:**

   ```bash
   chmod 644 .env
   ```

---

### Issue: source_up Not Finding Parent

**Symptoms:**
- Parent .envrc not loaded
- `source_up: No ancestor .envrc found`

**Solutions:**

1. **Verify parent .envrc exists:**

   ```bash
   ls -la ../.envrc
   ls -la ../../.envrc
   ```

2. **Use source_up_if_exists:**

   ```bash
   source_up_if_exists  # Silent if not found
   ```

3. **Explicit source:**

   ```bash
   source_env ../.envrc
   source_env_if_exists ../../.envrc
   ```

---

### Issue: Nix/Flake Errors

**Symptoms:**
- `use nix` or `use flake` fails
- Very slow loading

**Solutions:**

1. **Install nix-direnv:**

   ```bash
   nix-env -i nix-direnv
   ```

2. **Add to ~/.config/direnv/direnvrc:**

   ```bash
   source ~/.nix-profile/share/nix-direnv/direnvrc
   ```

3. **Or inline in .envrc:**

   ```bash
   if ! has nix_direnv_version || ! nix_direnv_version 2.3.0; then
     source_url "https://raw.githubusercontent.com/nix-community/nix-direnv/2.3.0/direnvrc" \
       "sha256-Dmd+j63L84wuzgyjITIfSxSD57Tx7v51DMxVZOsiUD8="
   fi

   use flake
   ```

4. **Enable flakes in nix.conf:**

   ```
   # ~/.config/nix/nix.conf
   experimental-features = nix-command flakes
   ```

---

### Issue: IDE Not Picking Up Environment

**Symptoms:**
- VS Code terminal doesn't have variables
- IDE tools can't find dependencies

**Solutions:**

1. **VS Code - Install extension:**

   Install [direnv extension](https://marketplace.visualstudio.com/items?itemName=mkhl.direnv)

2. **JetBrains - Install plugin:**

   Install [direnv integration](https://plugins.jetbrains.com/plugin/15285-direnv-integration)

3. **Open terminal from correct directory:**

   ```bash
   cd /project
   code .  # Open VS Code from project directory
   ```

4. **Restart IDE after direnv allow**

---

### Issue: Conflicting with Version Managers

**Symptoms:**
- rbenv, pyenv, nvm conflicts
- Wrong versions used

**Solutions:**

1. **Hook order - direnv LAST:**

   ```bash
   # ~/.zshrc

   # Version managers first
   eval "$(pyenv init -)"
   eval "$(rbenv init -)"
   export NVM_DIR="$HOME/.nvm"
   [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh"

   # direnv hook LAST
   eval "$(direnv hook zsh)"
   ```

2. **Use direnv's version manager functions:**

   ```bash
   # .envrc
   use node 18
   use rbenv
   use pyenv
   ```

3. **Or set version files:**

   ```bash
   # .envrc
   watch_file .node-version
   watch_file .ruby-version
   watch_file .python-version
   ```

---

## Debug Script

Save as `debug-direnv.sh`:

```bash
#!/bin/bash
set -e

echo "=== direnv Debug Info ==="
echo

echo "Version:"
direnv version
echo

echo "Status:"
direnv status
echo

echo "Shell:"
echo "$SHELL"
echo

echo "Hook in config:"
case "$SHELL" in
  *zsh)
    grep "direnv" ~/.zshrc 2>/dev/null || echo "Not found in ~/.zshrc"
    ;;
  *bash)
    grep "direnv" ~/.bashrc 2>/dev/null || echo "Not found in ~/.bashrc"
    ;;
  *fish)
    grep "direnv" ~/.config/fish/config.fish 2>/dev/null || echo "Not found"
    ;;
esac
echo

echo ".envrc content:"
if [[ -f .envrc ]]; then
  cat .envrc
else
  echo "No .envrc in current directory"
fi
echo

echo "direnv allow status:"
if [[ -f .envrc ]]; then
  direnv status | grep -i allowed || echo "Not allowed"
fi
echo

echo ".direnv directory:"
ls -la .direnv/ 2>/dev/null || echo "No .direnv directory"
echo

echo "Environment variables from direnv:"
direnv export bash 2>/dev/null | head -20 || echo "No exports"
```

Run:

```bash
chmod +x debug-direnv.sh
./debug-direnv.sh
```

## Getting Help

1. **Official documentation:** https://direnv.net/
2. **GitHub issues:** https://github.com/direnv/direnv/issues
3. **Man page:** `man direnv` / `man direnv-stdlib`

## Reset Everything

Nuclear option - reset all direnv state:

```bash
# Remove all allowed .envrc entries
direnv prune

# Clear cache
rm -rf ~/.local/share/direnv/

# Clear project cache
rm -rf .direnv/

# Restart shell
exec $SHELL

# Re-allow
cd /project
direnv allow
```
