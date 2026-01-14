# AddHooks Workflow

Add new hooks to an existing pre-commit configuration.

## Trigger

- "add hook"
- "add linting"
- "add formatter"
- "add security scanning"
- "add terraform hooks"
- "add python linting"

## Workflow

### Step 1: Analyze Current Configuration

```bash
# Check existing hooks
bun run Tools/PreCommitManager.ts list

# Or manually review
cat .pre-commit-config.yaml
```

### Step 2: Identify Hook to Add

Common hook additions by category:

| Need | Hook |
|------|------|
| Python formatting | black, ruff-format |
| Python linting | flake8, ruff, pylint |
| Python type checking | mypy, pyright |
| JS/TS formatting | prettier, biome |
| JS/TS linting | eslint, biome |
| Terraform validation | terraform_fmt, terraform_validate |
| Terraform security | terraform_trivy, checkov |
| Secret detection | gitleaks, detect-secrets |
| YAML validation | yamllint |
| Shell linting | shellcheck |
| Commit messages | conventional-pre-commit |

### Step 3: Add Hook Configuration

#### Adding to Existing Repository

If the hook is from a repository already in your config, just add to `hooks:`:

```yaml
- repo: https://github.com/pre-commit/pre-commit-hooks
  rev: v5.0.0
  hooks:
    - id: trailing-whitespace
    - id: end-of-file-fixer
    # Add new hook here
    - id: check-ast
```

#### Adding New Repository

Add new repo block:

```yaml
repos:
  # Existing repos...

  # New repo
  - repo: https://github.com/new-repo/hooks
    rev: v1.0.0
    hooks:
      - id: new-hook
```

### Step 4: Common Hook Additions

#### Add Secret Detection
```yaml
- repo: https://github.com/gitleaks/gitleaks
  rev: v8.21.2
  hooks:
    - id: gitleaks
```

#### Add Python Type Checking
```yaml
- repo: https://github.com/pre-commit/mirrors-mypy
  rev: v1.13.0
  hooks:
    - id: mypy
      additional_dependencies:
        - types-requests
        - types-PyYAML
```

#### Add Terraform Docs
```yaml
# Add to existing pre-commit-terraform repo
- id: terraform_docs
  args:
    - --hook-config=--path-to-file=README.md
    - --hook-config=--create-file-if-not-exist=true
```

#### Add Conventional Commits
```yaml
- repo: https://github.com/compilerla/conventional-pre-commit
  rev: v3.6.0
  hooks:
    - id: conventional-pre-commit
      stages: [commit-msg]
      args: [feat, fix, docs, style, refactor, perf, test, chore, ci, build]
```

Then install commit-msg hook:
```bash
pre-commit install --hook-type commit-msg
```

#### Add Security Scanning (Checkov)
```yaml
- repo: https://github.com/bridgecrewio/checkov
  rev: 3.2.277
  hooks:
    - id: checkov
      args: [--quiet, --compact]
```

#### Add Markdown Linting
```yaml
- repo: https://github.com/igorshubovych/markdownlint-cli
  rev: v0.42.0
  hooks:
    - id: markdownlint
      args: [--fix]
```

#### Add Shell Script Linting
```yaml
- repo: https://github.com/shellcheck-py/shellcheck-py
  rev: v0.10.0.1
  hooks:
    - id: shellcheck
      args: [-x]
```

### Step 5: Test New Hook

```bash
# Update hook cache
pre-commit clean
pre-commit install --install-hooks

# Run specific hook
pre-commit run <hook-id> --all-files

# Run all hooks
pre-commit run --all-files
```

### Step 6: Commit Changes

```bash
git add .pre-commit-config.yaml
git commit -m "chore: add <hook-name> pre-commit hook"
```

## Hook Configuration Tips

### Filtering Files
```yaml
- id: eslint
  files: \.[jt]sx?$  # Only JS/TS files
  exclude: ^(vendor|node_modules)/
```

### Custom Arguments
```yaml
- id: flake8
  args: [--max-line-length=88, --extend-ignore=E203]
```

### Adding Dependencies
```yaml
- id: mypy
  additional_dependencies:
    - types-requests>=2.31
    - pydantic>=2.0
```

### Running at Specific Stages
```yaml
- id: gitleaks
  stages: [pre-commit, pre-push]
```

### Always Run (Even Without Matches)
```yaml
- id: generate-api-docs
  always_run: true
  pass_filenames: false
```

## Finding Hook IDs

1. Check repository's `.pre-commit-hooks.yaml`:
   ```bash
   curl -s https://raw.githubusercontent.com/pre-commit/pre-commit-hooks/main/.pre-commit-hooks.yaml
   ```

2. Check pre-commit hooks index: https://pre-commit.com/hooks.html

3. Check repository README for hook documentation
