# CustomHook Workflow

Create custom pre-commit hooks for project-specific needs.

## Trigger

- "create custom hook"
- "write local hook"
- "project-specific hook"
- "custom pre-commit"

## Local Hook Types

### 1. Script Hook

Simple shell/python script executed as-is.

```yaml
- repo: local
  hooks:
    - id: my-script-hook
      name: My Script Hook
      entry: ./scripts/check.sh
      language: script
      files: \.py$
```

### 2. System Hook

Uses system-installed executable.

```yaml
- repo: local
  hooks:
    - id: my-system-hook
      name: My System Hook
      entry: /usr/local/bin/my-tool
      language: system
      types: [python]
```

### 3. Python Hook

Python script with optional dependencies.

```yaml
- repo: local
  hooks:
    - id: my-python-hook
      name: My Python Hook
      entry: python scripts/check.py
      language: python
      additional_dependencies: [requests, pyyaml]
```

### 4. Node Hook

Node.js script with npm dependencies.

```yaml
- repo: local
  hooks:
    - id: my-node-hook
      name: My Node Hook
      entry: node scripts/check.js
      language: node
      additional_dependencies: [lodash, chalk]
```

## Common Custom Hook Examples

### API Key Check

```yaml
- repo: local
  hooks:
    - id: check-api-keys
      name: Check for API Keys
      entry: bash -c 'if grep -rE "(api_key|API_KEY|apikey)\\s*[:=]\\s*['\''\""][^'\''\"\n]+['\''\""]" "$@"; then echo "API key found!"; exit 1; fi'
      language: system
      types: [text]
```

### Kubernetes Manifest Validation

```yaml
- repo: local
  hooks:
    - id: validate-k8s
      name: Validate Kubernetes Manifests
      entry: kubectl apply --dry-run=client -f
      language: system
      files: \.(yaml|yml)$
      types: [yaml]
```

### Helm Template Validation

```yaml
- repo: local
  hooks:
    - id: helm-template
      name: Helm Template Check
      entry: bash -c 'for chart in $(find . -name Chart.yaml -exec dirname {} \;); do helm template "$chart" > /dev/null || exit 1; done'
      language: system
      pass_filenames: false
      always_run: true
```

### Docker Build Check

```yaml
- repo: local
  hooks:
    - id: docker-build
      name: Docker Build Check
      entry: docker build --no-cache -f
      language: system
      files: Dockerfile
```

### Python Import Sort Check

```yaml
- repo: local
  hooks:
    - id: check-imports
      name: Check Import Order
      entry: python -c "
        import sys
        for f in sys.argv[1:]:
            with open(f) as file:
                lines = file.readlines()
                imports = [l for l in lines if l.startswith('import') or l.startswith('from')]
                if imports != sorted(imports):
                    print(f'{f}: imports not sorted')
                    sys.exit(1)
      "
      language: system
      types: [python]
```

### TypeScript Type Check

```yaml
- repo: local
  hooks:
    - id: tsc-check
      name: TypeScript Type Check
      entry: npx tsc --noEmit
      language: system
      files: \.[jt]sx?$
      pass_filenames: false
```

### Prettier with Specific Config

```yaml
- repo: local
  hooks:
    - id: prettier-custom
      name: Prettier (Custom Config)
      entry: npx prettier --config .prettierrc.custom.json --write
      language: system
      types_or: [javascript, jsx, ts, tsx, json, yaml]
```

### Database Migration Check

```yaml
- repo: local
  hooks:
    - id: check-migrations
      name: Check Database Migrations
      entry: python manage.py makemigrations --check --dry-run
      language: system
      pass_filenames: false
      always_run: true
```

### License Header Check

```yaml
- repo: local
  hooks:
    - id: license-header
      name: Check License Header
      entry: bash -c '
        header="# Copyright (c) 2024 Company Name"
        for file in "$@"; do
          if ! head -1 "$file" | grep -q "^$header"; then
            echo "$file: missing license header"
            exit 1
          fi
        done
      '
      language: system
      types: [python]
```

### File Size Check

```yaml
- repo: local
  hooks:
    - id: check-file-size
      name: Check File Size
      entry: bash -c '
        max_size=1000000  # 1MB
        for file in "$@"; do
          size=$(stat -f%z "$file" 2>/dev/null || stat -c%s "$file")
          if [ "$size" -gt "$max_size" ]; then
            echo "$file: exceeds max size ($size > $max_size bytes)"
            exit 1
          fi
        done
      '
      language: system
      types: [file]
```

## Creating a Hook Repository

For reusable hooks, create a dedicated repository.

### Structure

```
my-hooks/
├── .pre-commit-hooks.yaml
├── hooks/
│   ├── check-api-keys.sh
│   ├── validate-k8s.py
│   └── lint-terraform.sh
└── README.md
```

### .pre-commit-hooks.yaml

```yaml
- id: check-api-keys
  name: Check for API Keys
  entry: hooks/check-api-keys.sh
  language: script
  types: [text]

- id: validate-k8s
  name: Validate Kubernetes Manifests
  entry: hooks/validate-k8s.py
  language: python
  types: [yaml]
  additional_dependencies: [kubernetes>=25.0.0, pyyaml>=6.0]

- id: lint-terraform
  name: Lint Terraform Files
  entry: hooks/lint-terraform.sh
  language: script
  files: \.tf$
```

### Sample Hook Script (hooks/check-api-keys.sh)

```bash
#!/bin/bash
set -euo pipefail

# Patterns to search for
patterns=(
    "api_key\s*[:=]\s*['\"][^'\"]+['\"]"
    "API_KEY\s*[:=]\s*['\"][^'\"]+['\"]"
    "secret\s*[:=]\s*['\"][^'\"]+['\"]"
)

found=0
for file in "$@"; do
    for pattern in "${patterns[@]}"; do
        if grep -qiE "$pattern" "$file"; then
            echo "Potential secret found in $file"
            grep -niE "$pattern" "$file"
            found=1
        fi
    done
done

exit $found
```

### Sample Python Hook (hooks/validate-k8s.py)

```python
#!/usr/bin/env python3
import sys
import yaml

def validate_manifest(filepath):
    with open(filepath) as f:
        docs = list(yaml.safe_load_all(f))

    for doc in docs:
        if doc is None:
            continue

        if 'apiVersion' not in doc:
            print(f"{filepath}: missing apiVersion")
            return False

        if 'kind' not in doc:
            print(f"{filepath}: missing kind")
            return False

    return True

if __name__ == '__main__':
    success = True
    for filepath in sys.argv[1:]:
        if not validate_manifest(filepath):
            success = False

    sys.exit(0 if success else 1)
```

### Using Your Hook Repository

```yaml
# In .pre-commit-config.yaml
- repo: https://github.com/yourorg/my-hooks
  rev: v1.0.0
  hooks:
    - id: check-api-keys
    - id: validate-k8s
```

## Best Practices

### 1. Handle No Files Gracefully

```bash
#!/bin/bash
if [ $# -eq 0 ]; then
    exit 0  # No files to check
fi
```

### 2. Exit Codes

- `0`: Success (hook passed)
- `1`: Failure (issues found)
- Other non-zero: Error

### 3. Provide Helpful Output

```bash
echo "Checking $file..."
if [ $found -eq 1 ]; then
    echo "❌ Issues found in $file"
    echo "  Line 42: potential API key"
else
    echo "✅ $file passed"
fi
```

### 4. Make Scripts Executable

```bash
chmod +x hooks/*.sh
chmod +x hooks/*.py
```

### 5. Test Locally

```bash
# Test with specific files
pre-commit run my-hook --files path/to/file.py

# Test with all files
pre-commit run my-hook --all-files

# Try repo directly
pre-commit try-repo . my-hook --all-files
```
