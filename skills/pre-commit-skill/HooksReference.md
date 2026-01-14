# Pre-Commit Hooks Reference

Comprehensive catalog of pre-commit hooks organized by language and purpose.

## Official Pre-Commit Hooks

**Repository:** `https://github.com/pre-commit/pre-commit-hooks`

| Hook ID | Description |
|---------|-------------|
| `trailing-whitespace` | Trims trailing whitespace |
| `end-of-file-fixer` | Ensures files end with newline |
| `check-yaml` | Validates YAML syntax |
| `check-json` | Validates JSON syntax |
| `check-toml` | Validates TOML syntax |
| `check-xml` | Validates XML syntax |
| `check-added-large-files` | Prevents large files from being committed |
| `check-merge-conflict` | Checks for merge conflict strings |
| `check-case-conflict` | Checks for case conflicts in filenames |
| `check-symlinks` | Checks for broken symlinks |
| `check-executables-have-shebangs` | Ensures executables have shebangs |
| `check-shebang-scripts-are-executable` | Ensures shebang scripts are executable |
| `detect-private-key` | Detects private keys |
| `mixed-line-ending` | Fixes mixed line endings |
| `no-commit-to-branch` | Prevents commits to protected branches |
| `pretty-format-json` | Formats JSON files |
| `requirements-txt-fixer` | Sorts requirements.txt |
| `sort-simple-yaml` | Sorts simple YAML files |
| `file-contents-sorter` | Sorts file contents |
| `fix-byte-order-marker` | Removes UTF-8 BOM |

```yaml
- repo: https://github.com/pre-commit/pre-commit-hooks
  rev: v5.0.0
  hooks:
    - id: trailing-whitespace
    - id: end-of-file-fixer
    - id: check-yaml
    - id: check-json
    - id: check-added-large-files
      args: [--maxkb=1000]
    - id: check-merge-conflict
    - id: detect-private-key
    - id: no-commit-to-branch
      args: [--branch, main, --branch, master]
```

---

## Python Hooks

### Black (Formatter)
```yaml
- repo: https://github.com/psf/black
  rev: 24.10.0
  hooks:
    - id: black
      language_version: python3.11
      args: [--line-length=88]
```

### isort (Import Sorter)
```yaml
- repo: https://github.com/pycqa/isort
  rev: 5.13.2
  hooks:
    - id: isort
      args: [--profile=black]
```

### Flake8 (Linter)
```yaml
- repo: https://github.com/pycqa/flake8
  rev: 7.1.1
  hooks:
    - id: flake8
      args: [--max-line-length=88, --extend-ignore=E203]
```

### mypy (Type Checker)
```yaml
- repo: https://github.com/pre-commit/mirrors-mypy
  rev: v1.13.0
  hooks:
    - id: mypy
      additional_dependencies: [types-requests, types-PyYAML]
```

### Ruff (Fast Linter + Formatter)
```yaml
- repo: https://github.com/astral-sh/ruff-pre-commit
  rev: v0.7.3
  hooks:
    - id: ruff
      args: [--fix]
    - id: ruff-format
```

### Bandit (Security)
```yaml
- repo: https://github.com/pycqa/bandit
  rev: 1.7.10
  hooks:
    - id: bandit
      args: [-c, pyproject.toml]
      additional_dependencies: ["bandit[toml]"]
```

### pyupgrade (Modernizer)
```yaml
- repo: https://github.com/asottile/pyupgrade
  rev: v3.19.0
  hooks:
    - id: pyupgrade
      args: [--py311-plus]
```

### autopep8 (Formatter)
```yaml
- repo: https://github.com/hhatto/autopep8
  rev: v2.3.1
  hooks:
    - id: autopep8
```

---

## JavaScript/TypeScript Hooks

### Prettier (Formatter)
```yaml
- repo: https://github.com/pre-commit/mirrors-prettier
  rev: v4.0.0-alpha.8
  hooks:
    - id: prettier
      types_or: [javascript, jsx, ts, tsx, json, yaml, css, scss, markdown]
```

### ESLint (Linter)
```yaml
- repo: https://github.com/pre-commit/mirrors-eslint
  rev: v9.14.0
  hooks:
    - id: eslint
      files: \.[jt]sx?$
      types: [file]
      additional_dependencies:
        - eslint@9.14.0
        - typescript
        - "@typescript-eslint/parser"
        - "@typescript-eslint/eslint-plugin"
```

### Biome (Fast Linter + Formatter)
```yaml
- repo: https://github.com/biomejs/pre-commit
  rev: v0.5.0
  hooks:
    - id: biome-check
      additional_dependencies: ["@biomejs/biome@1.9.4"]
```

---

## Terraform/Infrastructure Hooks

**Repository:** `https://github.com/antonbabenko/pre-commit-terraform`

### Core Terraform Hooks
```yaml
- repo: https://github.com/antonbabenko/pre-commit-terraform
  rev: v1.96.2
  hooks:
    - id: terraform_fmt
    - id: terraform_validate
    - id: terraform_docs
      args:
        - --hook-config=--path-to-file=README.md
        - --hook-config=--create-file-if-not-exist=true
    - id: terraform_tflint
      args:
        - --args=--config=__GIT_WORKING_DIR__/.tflint.hcl
```

### Security Scanning
```yaml
    - id: terraform_trivy
      args:
        - --args=--severity=HIGH,CRITICAL
    - id: terraform_checkov
      args:
        - --args=--quiet
        - --args=--compact
```

### Terragrunt
```yaml
    - id: terragrunt_fmt
    - id: terragrunt_validate
```

### Cost Estimation
```yaml
    - id: infracost_breakdown
      args:
        - --args=--path=.
        - --hook-config='.totalMonthlyCost|tonumber < 5000'
```

---

## Kubernetes/Helm Hooks

### Helm Lint
```yaml
- repo: https://github.com/gruntwork-io/pre-commit
  rev: v0.1.23
  hooks:
    - id: helmlint
```

### Kubeconform (Manifest Validation)
```yaml
- repo: https://github.com/yannh/kubeconform
  rev: v0.6.7
  hooks:
    - id: kubeconform
      args: [-strict, -ignore-missing-schemas]
```

### Checkov (IaC Security)
```yaml
- repo: https://github.com/bridgecrewio/checkov
  rev: 3.2.277
  hooks:
    - id: checkov
      args: [--framework, kubernetes]
```

### Kustomize
```yaml
- repo: local
  hooks:
    - id: kustomize-build
      name: kustomize build
      entry: kustomize build
      language: system
      files: kustomization\.ya?ml$
      pass_filenames: false
```

---

## YAML/JSON Hooks

### yamllint
```yaml
- repo: https://github.com/adrienverge/yamllint
  rev: v1.35.1
  hooks:
    - id: yamllint
      args: [-c, .yamllint.yaml]
```

**Sample `.yamllint.yaml`:**
```yaml
extends: default
rules:
  line-length:
    max: 120
  truthy:
    check-keys: false
  document-start: disable
```

### yamlfmt (Formatter)
```yaml
- repo: https://github.com/google/yamlfmt
  rev: v0.14.0
  hooks:
    - id: yamlfmt
```

### check-jsonschema
```yaml
- repo: https://github.com/python-jsonschema/check-jsonschema
  rev: 0.29.4
  hooks:
    - id: check-github-workflows
    - id: check-github-actions
    - id: check-dependabot
    - id: check-renovate
```

---

## Security Hooks

### Gitleaks (Secret Detection)
```yaml
- repo: https://github.com/gitleaks/gitleaks
  rev: v8.21.2
  hooks:
    - id: gitleaks
```

### detect-secrets
```yaml
- repo: https://github.com/Yelp/detect-secrets
  rev: v1.5.0
  hooks:
    - id: detect-secrets
      args: [--baseline, .secrets.baseline]
```

### TruffleHog
```yaml
- repo: local
  hooks:
    - id: trufflehog
      name: TruffleHog
      entry: trufflehog git file://. --since-commit HEAD --results=verified,unknown --fail
      language: system
      stages: [pre-commit, pre-push]
```

### Trivy (Vulnerability Scanner)
```yaml
- repo: https://github.com/aquasecurity/trivy
  rev: v0.57.1
  hooks:
    - id: trivy-config
      args: [--severity, HIGH,CRITICAL]
```

---

## Shell Script Hooks

### shellcheck
```yaml
- repo: https://github.com/shellcheck-py/shellcheck-py
  rev: v0.10.0.1
  hooks:
    - id: shellcheck
      args: [-x]
```

### shfmt (Formatter)
```yaml
- repo: https://github.com/scop/pre-commit-shfmt
  rev: v3.10.0-1
  hooks:
    - id: shfmt
      args: [-i, "2", -ci]
```

### bashate
```yaml
- repo: https://github.com/openstack/bashate
  rev: 2.1.1
  hooks:
    - id: bashate
      args: [-i, E006]
```

---

## Go Hooks

### golangci-lint
```yaml
- repo: https://github.com/golangci/golangci-lint
  rev: v1.62.0
  hooks:
    - id: golangci-lint
```

### go-fmt
```yaml
- repo: https://github.com/dnephin/pre-commit-golang
  rev: v0.5.1
  hooks:
    - id: go-fmt
    - id: go-vet
    - id: go-imports
```

---

## Rust Hooks

### rustfmt
```yaml
- repo: https://github.com/doublify/pre-commit-rust
  rev: v1.0
  hooks:
    - id: fmt
    - id: cargo-check
```

---

## Docker Hooks

### hadolint (Dockerfile Linter)
```yaml
- repo: https://github.com/hadolint/hadolint
  rev: v2.12.0
  hooks:
    - id: hadolint
```

### docker-compose-check
```yaml
- repo: https://github.com/IamTheFij/docker-pre-commit
  rev: v3.0.1
  hooks:
    - id: docker-compose-check
```

---

## Documentation Hooks

### markdownlint
```yaml
- repo: https://github.com/igorshubovych/markdownlint-cli
  rev: v0.42.0
  hooks:
    - id: markdownlint
      args: [--fix]
```

### codespell (Typos)
```yaml
- repo: https://github.com/codespell-project/codespell
  rev: v2.3.0
  hooks:
    - id: codespell
      args: [-I, .codespell-ignore]
```

### typos (Fast Typo Checker)
```yaml
- repo: https://github.com/crate-ci/typos
  rev: v1.27.0
  hooks:
    - id: typos
```

---

## Git Commit Message Hooks

### commitlint
```yaml
- repo: https://github.com/alessandrojcm/commitlint-pre-commit-hook
  rev: v9.18.0
  hooks:
    - id: commitlint
      stages: [commit-msg]
      additional_dependencies: ["@commitlint/config-conventional"]
```

### conventional-pre-commit
```yaml
- repo: https://github.com/compilerla/conventional-pre-commit
  rev: v3.6.0
  hooks:
    - id: conventional-pre-commit
      stages: [commit-msg]
      args: [feat, fix, docs, style, refactor, perf, test, chore, ci, build]
```

---

## Complete Example Configuration

```yaml
# .pre-commit-config.yaml
default_stages: [pre-commit]
fail_fast: false

repos:
  # General hooks
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
        args: [--allow-multiple-documents]
      - id: check-json
      - id: check-added-large-files
        args: [--maxkb=1000]
      - id: check-merge-conflict
      - id: detect-private-key
      - id: no-commit-to-branch
        args: [--branch, main]

  # YAML
  - repo: https://github.com/adrienverge/yamllint
    rev: v1.35.1
    hooks:
      - id: yamllint
        args: [-c, .yamllint.yaml]

  # Security
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.21.2
    hooks:
      - id: gitleaks

  # Typos
  - repo: https://github.com/crate-ci/typos
    rev: v1.27.0
    hooks:
      - id: typos

  # Commit messages
  - repo: https://github.com/compilerla/conventional-pre-commit
    rev: v3.6.0
    hooks:
      - id: conventional-pre-commit
        stages: [commit-msg]
```

---

## Version Update Schedule

Run `pre-commit autoupdate` monthly to keep hooks current:

```bash
# Update all hooks
pre-commit autoupdate

# Update specific repo
pre-commit autoupdate --repo https://github.com/psf/black
```
