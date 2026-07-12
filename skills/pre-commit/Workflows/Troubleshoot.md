# Troubleshoot Workflow

Debug and fix pre-commit hook issues.

## Trigger

- "fix pre-commit"
- "pre-commit failing"
- "hook not working"
- "debug pre-commit"
- "pre-commit error"

## Common Issues and Solutions

### 1. Hooks Not Running

**Symptoms:**
- Git commits without running hooks
- No output when committing

**Solutions:**

```bash
# Reinstall hooks
pre-commit install

# Also install commit-msg hooks if needed
pre-commit install --hook-type commit-msg

# Verify hook is installed
ls -la .git/hooks/pre-commit
```

### 2. Hook Execution Errors

**Symptoms:**
- Hook fails with error messages
- Specific hook returns non-zero exit code

**Debug Steps:**

```bash
# Run with verbose output
PRE_COMMIT_VERBOSE=1 pre-commit run <hook-id> --all-files

# Run specific hook on specific file
pre-commit run <hook-id> --files path/to/file.py

# Check hook environment
pre-commit run <hook-id> --verbose
```

### 3. Cache/Environment Issues

**Symptoms:**
- "Failed to install..." errors
- Inconsistent behavior
- Wrong versions running

**Solutions:**

```bash
# Clear all cached environments
pre-commit clean

# Reinstall with fresh dependencies
pre-commit install --install-hooks

# Check cache location
ls ~/.cache/pre-commit/
```

### 4. Version Mismatch

**Symptoms:**
- "Hook not found" errors
- Repository version doesn't have expected hook

**Solutions:**

```bash
# Update hooks to latest versions
pre-commit autoupdate

# Check available hooks in repo
pre-commit try-repo <repo-url> --all-files

# Validate configuration
bun run Tools/HookValidator.ts
```

### 5. Configuration Errors

**Symptoms:**
- YAML parsing errors
- "Invalid config" messages

**Solutions:**

```bash
# Validate YAML syntax
python -c "import yaml; yaml.safe_load(open('.pre-commit-config.yaml'))"

# Validate configuration
bun run Tools/HookValidator.ts --verbose

# Check for common issues
pre-commit validate-config .pre-commit-config.yaml
```

### 6. Slow Hook Execution

**Symptoms:**
- Hooks take too long
- Timeout errors

**Solutions:**

```yaml
# Limit files processed
- id: slow-hook
  files: ^src/  # Only check src/ directory

# Run hooks in parallel (default)
# Or force serial for problematic hooks
- id: problematic-hook
  require_serial: true

# Skip slow hooks temporarily
SKIP=slow-hook git commit -m "message"
```

### 7. Dependency Issues

**Symptoms:**
- "ModuleNotFoundError"
- "Package not found"
- Missing dependencies

**Solutions:**

```yaml
# Add required dependencies
- id: mypy
  additional_dependencies:
    - types-requests
    - pydantic>=2.0

# For node hooks
- id: eslint
  additional_dependencies:
    - eslint@9.14.0
    - typescript
    - "@typescript-eslint/parser"
```

### 8. Git Hook Conflicts

**Symptoms:**
- Other tools overwriting hooks
- Husky/lefthook conflicts

**Solutions:**

```bash
# Check what's in hooks directory
cat .git/hooks/pre-commit

# Reinstall pre-commit hooks
pre-commit install --allow-missing-config

# If using husky, disable it
rm -rf .husky
```

### 9. Terraform Hook Issues

**Symptoms:**
- terraform_validate fails
- "Provider not found"

**Solutions:**

```bash
# Initialize terraform first
terraform init

# Clear terraform cache
rm -rf .terraform
terraform init

# Use retry option
- id: terraform_validate
  args:
    - --hook-config=--retry-once-with-cleanup=true
```

### 10. File Pattern Issues

**Symptoms:**
- Hook not running on expected files
- Hook running on wrong files

**Debug:**

```bash
# Test file pattern matching
pre-commit run <hook-id> --files specific/file.py

# Check what files would be matched
pre-commit run <hook-id> --all-files --verbose
```

**Fix:**

```yaml
# Use correct regex patterns
- id: eslint
  files: \.[jt]sx?$  # Matches .js, .jsx, .ts, .tsx
  exclude: ^(dist|node_modules)/
```

## Debug Techniques

### Enable Verbose Mode
```bash
PRE_COMMIT_VERBOSE=1 pre-commit run --all-files
```

### Trace Mode (for pre-commit-terraform)
```bash
PCT_LOG=trace pre-commit run terraform_validate
```

### Check Hook Exit Code
```bash
pre-commit run <hook-id> --all-files; echo "Exit code: $?"
```

### Inspect Hook Environment
```bash
# Find hook's virtual environment
ls ~/.cache/pre-commit/

# Activate and inspect
source ~/.cache/pre-commit/<hash>/py_env-python3.11/bin/activate
pip list
```

### Test Hook in Isolation
```bash
# Try running hook directly from repo
pre-commit try-repo https://github.com/psf/black --all-files
```

## Recovery Steps

### Complete Reset
```bash
# 1. Remove all hooks
pre-commit uninstall

# 2. Clear cache
pre-commit clean

# 3. Remove git hooks
rm .git/hooks/pre-commit
rm .git/hooks/commit-msg

# 4. Reinstall
pre-commit install --install-hooks
pre-commit install --hook-type commit-msg

# 5. Test
pre-commit run --all-files
```

### Skip Hooks Temporarily
```bash
# Skip all hooks (use sparingly)
git commit --no-verify -m "emergency commit"

# Skip specific hooks
SKIP=flake8,mypy git commit -m "skip linting"
```

## Error Messages Reference

| Error | Cause | Solution |
|-------|-------|----------|
| `Hook '<id>' not found` | Wrong hook ID or version | Check repo's .pre-commit-hooks.yaml |
| `Failed to install...` | Network/dependency issue | `pre-commit clean && pre-commit install --install-hooks` |
| `Executable not found` | Missing system dependency | Install required tool (terraform, helm, etc.) |
| `Check failed` | Hook found issues | Fix the issues or add exceptions |
| `Timeout` | Hook too slow | Add timeout or file filters |
