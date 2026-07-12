# ShellCheck CI/CD Integration Guide

Complete guide for integrating ShellCheck into development workflows.

## Pre-commit Hooks

### Official Pre-commit Hook

Add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/koalaman/shellcheck-precommit
    rev: v0.11.0
    hooks:
      - id: shellcheck
        # Optional: customize arguments
        args: ["--severity=warning"]
```

### Alternative: shellcheck-py

```yaml
repos:
  - repo: https://github.com/shellcheck-py/shellcheck-py
    rev: v0.9.0.5
    hooks:
      - id: shellcheck
```

### Custom Pre-commit Script

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Find all staged shell scripts
staged_scripts=$(git diff --cached --name-only --diff-filter=ACMR | grep -E '\.(sh|bash|zsh)$')

if [[ -n "$staged_scripts" ]]; then
    echo "Running ShellCheck on staged scripts..."

    # Run shellcheck on all staged scripts
    if ! echo "$staged_scripts" | xargs shellcheck; then
        echo "ShellCheck found issues. Please fix them before committing."
        exit 1
    fi
fi

exit 0
```

Make executable:
```bash
chmod +x .git/hooks/pre-commit
```

## GitHub Actions

### Basic Workflow

```yaml
# .github/workflows/shellcheck.yml
name: ShellCheck

on:
  push:
    branches: [main, develop]
    paths:
      - '**.sh'
      - '**.bash'
  pull_request:
    paths:
      - '**.sh'
      - '**.bash'

jobs:
  shellcheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run ShellCheck
        uses: ludeeus/action-shellcheck@master
        with:
          severity: warning
          scandir: './scripts'
          format: gcc
          additional_files: 'entrypoint'
```

### Advanced Workflow with Annotations

```yaml
name: ShellCheck

on: [push, pull_request]

jobs:
  shellcheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install ShellCheck
        run: sudo apt-get install -y shellcheck

      - name: Find shell scripts
        id: scripts
        run: |
          scripts=$(find . -type f \( -name "*.sh" -o -name "*.bash" \) ! -path "./.git/*")
          echo "scripts<<EOF" >> $GITHUB_OUTPUT
          echo "$scripts" >> $GITHUB_OUTPUT
          echo "EOF" >> $GITHUB_OUTPUT

      - name: Run ShellCheck
        run: |
          echo "${{ steps.scripts.outputs.scripts }}" | xargs shellcheck -f gcc || true

      - name: ShellCheck with annotations
        run: |
          echo "${{ steps.scripts.outputs.scripts }}" | xargs shellcheck -f json | \
            jq -r '.[] | "::warning file=\(.file),line=\(.line),col=\(.column)::\(.message) [\(.code)]"'
```

### Matrix Testing Multiple Shells

```yaml
name: ShellCheck Multi-Shell

on: [push, pull_request]

jobs:
  shellcheck:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        shell: [sh, bash, dash, ksh]
    steps:
      - uses: actions/checkout@v4

      - name: Run ShellCheck for ${{ matrix.shell }}
        run: |
          find ./scripts -name "*.sh" -exec shellcheck -s ${{ matrix.shell }} {} +
```

## GitLab CI/CD

### Basic Pipeline

```yaml
# .gitlab-ci.yml
shellcheck:
  image: koalaman/shellcheck-alpine:stable
  stage: test
  script:
    - find . -name "*.sh" -exec shellcheck {} +
  only:
    changes:
      - "**/*.sh"
```

### With Artifacts

```yaml
shellcheck:
  image: koalaman/shellcheck-alpine:stable
  stage: lint
  script:
    - find . -name "*.sh" -print0 | xargs -0 shellcheck -f checkstyle > shellcheck-report.xml || true
  artifacts:
    reports:
      junit: shellcheck-report.xml
    paths:
      - shellcheck-report.xml
    expire_in: 1 week
```

## Jenkins

### Declarative Pipeline

```groovy
pipeline {
    agent any

    stages {
        stage('ShellCheck') {
            steps {
                sh '''
                    find . -name "*.sh" | xargs shellcheck -f checkstyle > shellcheck.xml || true
                '''
            }
            post {
                always {
                    recordIssues tools: [checkStyle(pattern: 'shellcheck.xml')]
                }
            }
        }
    }
}
```

### With Docker

```groovy
pipeline {
    agent {
        docker {
            image 'koalaman/shellcheck-alpine:stable'
        }
    }

    stages {
        stage('Lint') {
            steps {
                sh 'find . -name "*.sh" -exec shellcheck {} +'
            }
        }
    }
}
```

## CircleCI

```yaml
# .circleci/config.yml
version: 2.1

orbs:
  shellcheck: circleci/shellcheck@3.2.0

workflows:
  lint:
    jobs:
      - shellcheck/check:
          dir: ./scripts
          severity: warning
          exclude: SC1091
```

## Travis CI

```yaml
# .travis.yml
language: shell

addons:
  apt:
    packages:
      - shellcheck

script:
  - find . -name "*.sh" -exec shellcheck {} +
```

## Azure DevOps

```yaml
# azure-pipelines.yml
trigger:
  paths:
    include:
      - '**/*.sh'

pool:
  vmImage: 'ubuntu-latest'

steps:
  - task: Bash@3
    displayName: 'Install ShellCheck'
    inputs:
      targetType: 'inline'
      script: |
        sudo apt-get update
        sudo apt-get install -y shellcheck

  - task: Bash@3
    displayName: 'Run ShellCheck'
    inputs:
      targetType: 'inline'
      script: |
        find . -name "*.sh" -exec shellcheck -f gcc {} +
```

## Makefile Integration

```makefile
# Makefile

SHELL_SCRIPTS := $(shell find . -name "*.sh" -not -path "./.git/*")

.PHONY: lint lint-fix check-shellcheck

# Check if shellcheck is installed
check-shellcheck:
	@command -v shellcheck >/dev/null 2>&1 || { echo "shellcheck not installed. Run: brew install shellcheck"; exit 1; }

# Run shellcheck
lint: check-shellcheck
	@echo "Running ShellCheck on $(words $(SHELL_SCRIPTS)) scripts..."
	@shellcheck $(SHELL_SCRIPTS)

# Run with severity filter
lint-warnings: check-shellcheck
	@shellcheck -S warning $(SHELL_SCRIPTS)

lint-errors: check-shellcheck
	@shellcheck -S error $(SHELL_SCRIPTS)

# Generate diff for auto-fixes
lint-fix: check-shellcheck
	@shellcheck -f diff $(SHELL_SCRIPTS) | patch -p1

# Generate JSON report
lint-report: check-shellcheck
	@shellcheck -f json $(SHELL_SCRIPTS) > shellcheck-report.json

# CI mode - fail on any issue
ci-lint: check-shellcheck
	@shellcheck -S warning -f gcc $(SHELL_SCRIPTS)
```

## Editor Integration

### VS Code

Install `vscode-shellcheck` extension:

```json
// .vscode/settings.json
{
  "shellcheck.enable": true,
  "shellcheck.run": "onSave",
  "shellcheck.executablePath": "shellcheck",
  "shellcheck.exclude": ["SC1091"],
  "shellcheck.customArgs": ["-x"]
}
```

### Vim/Neovim with ALE

```vim
" ~/.vimrc or init.vim
let g:ale_linters = {
\   'sh': ['shellcheck'],
\   'bash': ['shellcheck'],
\}

let g:ale_sh_shellcheck_options = '-x'
let g:ale_sh_shellcheck_exclusions = 'SC1091'
```

### Neovim with nvim-lint

```lua
-- lua/plugins/lint.lua
require('lint').linters_by_ft = {
  sh = {'shellcheck'},
  bash = {'shellcheck'},
}

require('lint').linters.shellcheck.args = {
  '-x',
  '-f', 'gcc',
  '-',
}
```

### Emacs with Flycheck

```elisp
;; ~/.emacs.d/init.el
(use-package flycheck
  :ensure t
  :init (global-flycheck-mode)
  :config
  (setq flycheck-shellcheck-follow-sources nil)
  (add-to-list 'flycheck-disabled-checkers 'sh-posix-dash))
```

### Sublime Text

Install `SublimeLinter-shellcheck` via Package Control.

## Docker Usage

### Basic Docker Run

```bash
# Check single file
docker run --rm -v "$PWD:/mnt" koalaman/shellcheck:stable /mnt/script.sh

# Check directory
docker run --rm -v "$PWD:/mnt" koalaman/shellcheck:stable /mnt/**/*.sh

# With options
docker run --rm -v "$PWD:/mnt" \
  -e SHELLCHECK_OPTS='-x -S warning' \
  koalaman/shellcheck:stable /mnt/scripts/*.sh
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  shellcheck:
    image: koalaman/shellcheck:stable
    volumes:
      - ./:/mnt:ro
      - ./.shellcheckrc:/root/.shellcheckrc:ro
    command: /mnt/scripts/*.sh
```

### Multi-stage Dockerfile with ShellCheck

```dockerfile
# Dockerfile
FROM koalaman/shellcheck:stable AS shellcheck
COPY scripts/ /scripts/
RUN shellcheck /scripts/*.sh

FROM ubuntu:22.04
COPY --from=shellcheck /scripts/ /app/scripts/
# ... rest of build
```

## Quality Gate Integration

### SonarQube

Use CheckStyle format and import:

```bash
shellcheck -f checkstyle *.sh > shellcheck-checkstyle.xml
```

### Codacy

ShellCheck is natively supported. Enable in repository settings.

### Code Climate

Add to `.codeclimate.yml`:

```yaml
version: "2"
plugins:
  shellcheck:
    enabled: true
    config:
      severity: warning
```

### CodeFactor

ShellCheck is enabled by default for shell scripts.
