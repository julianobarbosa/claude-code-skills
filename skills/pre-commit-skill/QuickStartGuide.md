# Pre-Commit Quick Start Guide

## Installation

### Using pip (Recommended)
```bash
pip install pre-commit
```

### Using Homebrew (macOS)
```bash
brew install pre-commit
```

### Using pipx (Isolated)
```bash
pipx install pre-commit
```

### Verify Installation
```bash
pre-commit --version
```

## 4-Step Setup

### Step 1: Create Configuration

Create `.pre-commit-config.yaml` in your repository root:

```yaml
# Minimal starter config
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
```

Or generate a sample:
```bash
pre-commit sample-config > .pre-commit-config.yaml
```

### Step 2: Install Git Hooks

```bash
pre-commit install
```

This creates `.git/hooks/pre-commit` that runs automatically on `git commit`.

### Step 3: Test on All Files (Optional but Recommended)

```bash
pre-commit run --all-files
```

### Step 4: Commit Your Config

```bash
git add .pre-commit-config.yaml
git commit -m "chore: add pre-commit configuration"
```

## Essential Commands

| Command | Description |
|---------|-------------|
| `pre-commit install` | Install hooks to git |
| `pre-commit install --install-hooks` | Install and download hook dependencies |
| `pre-commit run` | Run on staged files |
| `pre-commit run --all-files` | Run on all files |
| `pre-commit run <hook-id>` | Run specific hook |
| `pre-commit autoupdate` | Update hooks to latest versions |
| `pre-commit clean` | Clear cached hook environments |
| `pre-commit uninstall` | Remove git hooks |

## Skipping Hooks

### Skip all hooks (emergency only)
```bash
git commit --no-verify -m "message"
```

### Skip specific hooks
```bash
SKIP=flake8,black git commit -m "message"
```

## Common Starter Configurations

### Python Project
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 24.10.0
    hooks:
      - id: black

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort

  - repo: https://github.com/pycqa/flake8
    rev: 7.1.1
    hooks:
      - id: flake8
```

### JavaScript/TypeScript Project
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-json
      - id: check-added-large-files

  - repo: https://github.com/pre-commit/mirrors-prettier
    rev: v4.0.0-alpha.8
    hooks:
      - id: prettier
        types_or: [javascript, jsx, ts, tsx, json, yaml, markdown]

  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v9.14.0
    hooks:
      - id: eslint
        files: \.[jt]sx?$
        additional_dependencies:
          - eslint@9.14.0
          - typescript
```

### Infrastructure Project (Terraform/Kubernetes)
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
        args: [--allow-multiple-documents]

  - repo: https://github.com/antonbabenko/pre-commit-terraform
    rev: v1.96.2
    hooks:
      - id: terraform_fmt
      - id: terraform_validate
      - id: terraform_docs
      - id: terraform_tflint

  - repo: https://github.com/adrienverge/yamllint
    rev: v1.35.1
    hooks:
      - id: yamllint
        args: [-c, .yamllint.yaml]
```

## Best Practices

1. **Pin versions**: Always use specific `rev` tags, never branches
2. **Run autoupdate regularly**: Keep hooks current with `pre-commit autoupdate`
3. **Test in CI**: Run `pre-commit run --all-files` in your CI pipeline
4. **Commit config first**: Add `.pre-commit-config.yaml` before enabling hooks
5. **Start minimal**: Add hooks incrementally, fix issues as you go

## Troubleshooting

### Hooks not running
```bash
pre-commit install  # Reinstall hooks
```

### Clear cache if hooks are stale
```bash
pre-commit clean
pre-commit install --install-hooks
```

### Check hook environments
```bash
ls ~/.cache/pre-commit/
```

### Debug mode
```bash
PRE_COMMIT_VERBOSE=1 pre-commit run --all-files
```
