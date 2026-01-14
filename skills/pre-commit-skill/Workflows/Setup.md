# Setup Workflow

Initialize pre-commit for a new or existing project.

## Trigger

- "setup pre-commit"
- "initialize pre-commit"
- "add pre-commit to project"
- "create pre-commit config"

## Workflow

### Step 1: Check Prerequisites

```bash
# Check if pre-commit is installed
pre-commit --version

# If not installed, recommend installation
pip install pre-commit
# or
brew install pre-commit
```

### Step 2: Detect Project Type

Examine the project to determine appropriate hooks:

| Indicator | Project Type |
|-----------|--------------|
| `pyproject.toml`, `setup.py`, `requirements.txt` | Python |
| `package.json` | JavaScript/TypeScript |
| `*.tf` files | Terraform |
| `Chart.yaml` | Helm |
| `kustomization.yaml` | Kustomize |
| `Dockerfile` | Docker |
| `go.mod` | Go |
| `Cargo.toml` | Rust |

### Step 3: Generate Configuration

Use HookGenerator to create appropriate config:

```bash
# For Python project
bun run Tools/HookGenerator.ts python

# For JavaScript project
bun run Tools/HookGenerator.ts javascript

# For Infrastructure project
bun run Tools/HookGenerator.ts infrastructure

# For minimal setup
bun run Tools/HookGenerator.ts minimal
```

### Step 4: Install Git Hooks

```bash
# Install hooks
pre-commit install

# Also install commit-msg hooks if using conventional commits
pre-commit install --hook-type commit-msg

# Pre-download dependencies (optional but recommended)
pre-commit install --install-hooks
```

### Step 5: Initial Run

```bash
# Test on all files
pre-commit run --all-files

# If issues found, fix them
git add -A
pre-commit run --all-files
```

### Step 6: Commit Configuration

```bash
git add .pre-commit-config.yaml
git commit -m "chore: add pre-commit configuration"
```

## Sample Configurations by Project Type

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

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.7.3
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.13.0
    hooks:
      - id: mypy

  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.21.2
    hooks:
      - id: gitleaks
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

  - repo: https://github.com/biomejs/pre-commit
    rev: v0.5.0
    hooks:
      - id: biome-check
        additional_dependencies: ["@biomejs/biome@1.9.4"]

  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.21.2
    hooks:
      - id: gitleaks
```

### Terraform Project
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/antonbabenko/pre-commit-terraform
    rev: v1.96.2
    hooks:
      - id: terraform_fmt
      - id: terraform_validate
      - id: terraform_docs
      - id: terraform_tflint
      - id: terraform_trivy
        args:
          - --args=--severity=HIGH,CRITICAL

  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.21.2
    hooks:
      - id: gitleaks
```

## Supporting Files

### .yamllint.yaml
```yaml
extends: default
rules:
  line-length:
    max: 120
  truthy:
    check-keys: false
  document-start: disable
```

### pyproject.toml (for Python)
```toml
[tool.ruff]
line-length = 88
target-version = "py311"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP"]

[tool.mypy]
python_version = "3.11"
strict = true
```

### biome.json (for JavaScript)
```json
{
  "$schema": "https://biomejs.dev/schemas/1.9.4/schema.json",
  "formatter": {
    "enabled": true,
    "indentStyle": "space"
  },
  "linter": {
    "enabled": true
  }
}
```

## Common Issues

### Permission Denied
```bash
chmod +x .git/hooks/pre-commit
```

### Hooks Not Running
```bash
pre-commit install  # Reinstall
```

### Cache Issues
```bash
pre-commit clean
pre-commit install --install-hooks
```
