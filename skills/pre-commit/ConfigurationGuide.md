# Pre-Commit Configuration Guide

Advanced configuration options for `.pre-commit-config.yaml`.

## Configuration File Structure

```yaml
# Top-level configuration
default_install_hook_types: [pre-commit, commit-msg]
default_language_version:
  python: python3.11
  node: "20.0.0"
default_stages: [pre-commit]
files: ""           # Global file include pattern (regex)
exclude: ""         # Global file exclude pattern (regex)
fail_fast: false    # Stop after first failure
minimum_pre_commit_version: "3.0.0"

# Repository definitions
repos:
  - repo: https://github.com/example/hooks
    rev: v1.0.0
    hooks:
      - id: hook-name
        # Hook-specific configuration
```

## Repository Configuration

### Remote Repository
```yaml
- repo: https://github.com/pre-commit/pre-commit-hooks
  rev: v5.0.0  # Always use specific tag/SHA, never branch
  hooks:
    - id: trailing-whitespace
```

### Local Repository
```yaml
- repo: local
  hooks:
    - id: custom-check
      name: Custom Check
      entry: ./scripts/check.sh
      language: script
      files: \.py$
```

### Meta Hooks
```yaml
- repo: meta
  hooks:
    - id: check-hooks-apply
    - id: check-useless-excludes
    - id: identity
```

## Hook Configuration Options

| Option | Type | Description |
|--------|------|-------------|
| `id` | string | Hook identifier (required) |
| `name` | string | Display name override |
| `alias` | string | Alternative hook reference |
| `entry` | string | Command to run |
| `language` | string | Runtime language |
| `language_version` | string | Language version override |
| `files` | regex | File pattern to include |
| `exclude` | regex | File pattern to exclude |
| `types` | list | File types (AND logic) |
| `types_or` | list | File types (OR logic) |
| `exclude_types` | list | File types to exclude |
| `args` | list | Additional arguments |
| `stages` | list | Git hook stages |
| `additional_dependencies` | list | Extra packages |
| `always_run` | bool | Run even without matches |
| `pass_filenames` | bool | Pass filenames to hook |
| `require_serial` | bool | Disable parallelization |
| `verbose` | bool | Force output display |
| `log_file` | string | Output log path |

## File Filtering

### Using Regex Patterns
```yaml
hooks:
  - id: check-yaml
    files: ^config/.*\.ya?ml$
    exclude: ^config/secrets/
```

### Using File Types
```yaml
hooks:
  - id: prettier
    types_or:
      - javascript
      - jsx
      - ts
      - tsx
      - json
      - yaml
      - markdown
```

### Common File Types
- `text`, `binary`, `executable`, `directory`
- `python`, `javascript`, `typescript`, `json`, `yaml`, `toml`
- `markdown`, `html`, `css`, `scss`
- `shell`, `bash`, `zsh`
- `go`, `rust`, `java`, `c`, `cpp`
- `dockerfile`, `terraform`, `hcl`

## Git Hook Stages

```yaml
hooks:
  - id: commitlint
    stages: [commit-msg]

  - id: gitleaks
    stages: [pre-commit, pre-push]
```

Available stages:
- `pre-commit` (default)
- `pre-merge-commit`
- `pre-push`
- `commit-msg`
- `post-checkout`
- `post-commit`
- `post-merge`
- `post-rewrite`
- `prepare-commit-msg`
- `pre-rebase`

## Language Version Control

### Global Default
```yaml
default_language_version:
  python: python3.11
  node: "20.0.0"
  ruby: 3.2.0
  rust: 1.75.0
```

### Per-Hook Override
```yaml
hooks:
  - id: black
    language_version: python3.11
```

## Passing Arguments

### Static Arguments
```yaml
hooks:
  - id: flake8
    args: [--max-line-length=88, --extend-ignore=E203]
```

### Environment Variables
```yaml
hooks:
  - id: terraform_validate
    args:
      - --env-vars=AWS_DEFAULT_REGION="us-west-2"
```

### Git Directory Placeholder
```yaml
hooks:
  - id: terraform_tflint
    args:
      - --args=--config=__GIT_WORKING_DIR__/.tflint.hcl
```

## Additional Dependencies

### Python
```yaml
hooks:
  - id: mypy
    additional_dependencies:
      - types-requests
      - types-PyYAML
      - pydantic
```

### Node.js
```yaml
hooks:
  - id: eslint
    additional_dependencies:
      - eslint@9.14.0
      - typescript
      - "@typescript-eslint/parser"
```

## Conditional Execution

### Always Run (Even Without Matches)
```yaml
hooks:
  - id: generate-docs
    always_run: true
    pass_filenames: false
```

### Exclude Patterns
```yaml
hooks:
  - id: trailing-whitespace
    exclude: |
      (?x)^(
        .*\.snap$|
        .*\.lock$|
        vendor/.*
      )$
```

### Branch Protection
```yaml
hooks:
  - id: no-commit-to-branch
    args:
      - --branch=main
      - --branch=master
      - --pattern=release/.*
```

## Performance Optimization

### Parallelization Control
```yaml
hooks:
  - id: heavy-check
    require_serial: true  # Disable parallelization
```

### Fail Fast
```yaml
fail_fast: true  # Stop after first failure
```

### Cache Management
```bash
# Clear cached environments
pre-commit clean

# Pre-download dependencies
pre-commit install --install-hooks
```

## CI/CD Configuration

### Skip in CI
```yaml
hooks:
  - id: interactive-check
    stages: [pre-commit]  # Won't run in CI with --all-files
```

### Environment Detection
```yaml
- repo: local
  hooks:
    - id: ci-only-check
      name: CI Only Check
      entry: bash -c '[ -n "$CI" ] && ./check.sh || true'
      language: system
```

## Debugging

### Verbose Output
```yaml
hooks:
  - id: complex-check
    verbose: true
```

### Log to File
```yaml
hooks:
  - id: long-running-check
    log_file: /tmp/hook-output.log
```

### Environment Variables
```bash
# Debug mode
PRE_COMMIT_VERBOSE=1 pre-commit run

# Trace mode (for pre-commit-terraform)
PCT_LOG=trace pre-commit run terraform_validate

# Disable colors
PRE_COMMIT_COLOR=never pre-commit run
```

## Monorepo Support

### Subdirectory Targeting
```yaml
hooks:
  - id: terraform_fmt
    args:
      - --hook-config=--tf-path=./infrastructure
```

### Multiple Configs
```bash
# Run with specific config
pre-commit run -c .pre-commit-config.python.yaml
```

## Migration from Other Tools

### From husky (npm)
```yaml
# Replace package.json husky config with:
- repo: https://github.com/pre-commit/mirrors-eslint
  rev: v9.14.0
  hooks:
    - id: eslint
```

### From git hooks directory
```yaml
# Convert .git/hooks/pre-commit to:
- repo: local
  hooks:
    - id: legacy-hook
      name: Legacy Pre-commit Hook
      entry: ./scripts/legacy-hook.sh
      language: script
```
