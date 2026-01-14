# Security Hooks for Pre-Commit

Comprehensive guide to secret detection and security scanning hooks.

## Secret Detection

### Gitleaks

Industry-standard secret detection tool.

```yaml
- repo: https://github.com/gitleaks/gitleaks
  rev: v8.21.2
  hooks:
    - id: gitleaks
```

**Custom Configuration (`.gitleaks.toml`):**
```toml
[extend]
useDefault = true

[[rules]]
id = "custom-api-key"
description = "Custom API Key Pattern"
regex = '''CUSTOM_API_[A-Z0-9]{32}'''
tags = ["key", "custom"]

[allowlist]
paths = [
  '''\.gitleaks\.toml$''',
  '''tests/fixtures/.*''',
]
```

**With Custom Config:**
```yaml
- id: gitleaks
  args: [--config, .gitleaks.toml]
```

### detect-secrets (Yelp)

Baseline-based secret detection.

```yaml
- repo: https://github.com/Yelp/detect-secrets
  rev: v1.5.0
  hooks:
    - id: detect-secrets
      args: [--baseline, .secrets.baseline]
```

**Initialize Baseline:**
```bash
detect-secrets scan > .secrets.baseline
```

**Audit Baseline:**
```bash
detect-secrets audit .secrets.baseline
```

### TruffleHog

Deep secret scanning with verification.

```yaml
- repo: local
  hooks:
    - id: trufflehog
      name: TruffleHog Secret Scan
      entry: trufflehog git file://. --since-commit HEAD --results=verified,unknown --fail
      language: system
      stages: [pre-commit, pre-push]
```

**Docker Alternative:**
```yaml
- repo: local
  hooks:
    - id: trufflehog-docker
      name: TruffleHog (Docker)
      entry: docker run --rm -v "$(pwd):/repo" trufflesecurity/trufflehog:latest git file:///repo --since-commit HEAD --fail
      language: system
```

---

## Infrastructure Security

### Checkov (IaC Security)

Static analysis for Terraform, Kubernetes, Docker, CloudFormation.

```yaml
- repo: https://github.com/bridgecrewio/checkov
  rev: 3.2.277
  hooks:
    - id: checkov
      args: [--quiet, --compact]
```

**Framework-Specific:**
```yaml
hooks:
  - id: checkov
    name: Checkov Terraform
    args: [--framework, terraform]
    files: \.tf$

  - id: checkov
    name: Checkov Kubernetes
    args: [--framework, kubernetes]
    files: \.(yaml|yml)$
```

**With Custom Config:**
```yaml
- id: checkov
  args: [--config-file, .checkov.yaml]
```

**Sample `.checkov.yaml`:**
```yaml
skip-check:
  - CKV_AWS_18  # Skip S3 logging check
  - CKV_K8S_21  # Skip default namespace check
soft-fail: false
framework:
  - terraform
  - kubernetes
```

### Trivy (Vulnerability Scanner)

Comprehensive vulnerability scanner.

```yaml
- repo: https://github.com/aquasecurity/trivy
  rev: v0.57.1
  hooks:
    - id: trivy-config
      args: [--severity, HIGH,CRITICAL]
```

**Terraform-Specific (via pre-commit-terraform):**
```yaml
- repo: https://github.com/antonbabenko/pre-commit-terraform
  rev: v1.96.2
  hooks:
    - id: terraform_trivy
      args:
        - --args=--severity=HIGH,CRITICAL
        - --args=--skip-dirs=.terraform
```

### Terrascan

Policy-as-code for Terraform.

```yaml
- repo: https://github.com/antonbabenko/pre-commit-terraform
  rev: v1.96.2
  hooks:
    - id: terrascan
      args:
        - --args=--policy-type=aws
        - --args=--severity=high
```

### tfsec (Deprecated - Use Trivy)

```yaml
# DEPRECATED: Use terraform_trivy instead
- repo: https://github.com/antonbabenko/pre-commit-terraform
  rev: v1.96.2
  hooks:
    - id: terraform_tfsec  # Deprecated
```

---

## Dependency Security

### Bandit (Python Security)

```yaml
- repo: https://github.com/pycqa/bandit
  rev: 1.7.10
  hooks:
    - id: bandit
      args: [-c, pyproject.toml, -r, src/]
      additional_dependencies: ["bandit[toml]"]
```

**Sample `pyproject.toml`:**
```toml
[tool.bandit]
exclude_dirs = ["tests", "venv"]
skips = ["B101"]  # Skip assert check
```

### Safety (Python Dependencies)

```yaml
- repo: https://github.com/Lucas-C/pre-commit-hooks-safety
  rev: v1.3.3
  hooks:
    - id: python-safety-dependencies-check
      files: requirements.*\.txt$
```

### npm-audit (Node.js)

```yaml
- repo: local
  hooks:
    - id: npm-audit
      name: npm audit
      entry: npm audit --audit-level=high
      language: system
      files: package-lock\.json$
      pass_filenames: false
```

---

## Code Quality Security

### Semgrep

Pattern-based code analysis.

```yaml
- repo: https://github.com/returntocorp/semgrep
  rev: v1.95.0
  hooks:
    - id: semgrep
      args: [--config, auto, --error]
```

**With Specific Rules:**
```yaml
- id: semgrep
  args:
    - --config=p/security-audit
    - --config=p/owasp-top-ten
    - --error
```

### CodeQL (via local hook)

```yaml
- repo: local
  hooks:
    - id: codeql
      name: CodeQL Analysis
      entry: codeql database analyze --format=sarif-latest
      language: system
      pass_filenames: false
```

---

## Complete Security Configuration

```yaml
# .pre-commit-config.yaml - Security Focus
repos:
  # Secret Detection
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: detect-private-key

  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.21.2
    hooks:
      - id: gitleaks

  - repo: https://github.com/Yelp/detect-secrets
    rev: v1.5.0
    hooks:
      - id: detect-secrets
        args: [--baseline, .secrets.baseline]

  # IaC Security
  - repo: https://github.com/bridgecrewio/checkov
    rev: 3.2.277
    hooks:
      - id: checkov
        args: [--quiet, --compact]

  # Python Security
  - repo: https://github.com/pycqa/bandit
    rev: 1.7.10
    hooks:
      - id: bandit
        args: [-c, pyproject.toml]
        additional_dependencies: ["bandit[toml]"]

  # Terraform Security
  - repo: https://github.com/antonbabenko/pre-commit-terraform
    rev: v1.96.2
    hooks:
      - id: terraform_trivy
        args:
          - --args=--severity=HIGH,CRITICAL

  # Pattern Analysis
  - repo: https://github.com/returntocorp/semgrep
    rev: v1.95.0
    hooks:
      - id: semgrep
        args: [--config, auto, --error]
```

---

## Handling False Positives

### Inline Ignores

**Gitleaks:**
```python
API_KEY = "test_key_12345"  # gitleaks:allow
```

**detect-secrets:**
```python
API_KEY = "test_key_12345"  # pragma: allowlist secret
```

**Checkov:**
```hcl
resource "aws_s3_bucket" "test" {
  #checkov:skip=CKV_AWS_18:Test bucket doesn't need logging
  bucket = "test-bucket"
}
```

**Trivy:**
```yaml
# trivy:ignore:AVD-AWS-0086
resource:
  type: aws_s3_bucket
```

### Baseline Files

```bash
# detect-secrets: Update baseline
detect-secrets scan --baseline .secrets.baseline

# Audit and mark false positives
detect-secrets audit .secrets.baseline
```

### Exclusion Patterns

```yaml
- id: gitleaks
  exclude: |
    (?x)^(
      tests/fixtures/.*|
      .*\.example$
    )$
```

---

## CI/CD Integration

### GitHub Actions

```yaml
name: Security Scan
on: [push, pull_request]
jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install pre-commit
      - run: pre-commit run gitleaks --all-files
      - run: pre-commit run checkov --all-files
```

### GitLab CI

```yaml
security-scan:
  stage: test
  image: python:3.11
  script:
    - pip install pre-commit
    - pre-commit run --all-files
  rules:
    - if: $CI_MERGE_REQUEST_ID
```
