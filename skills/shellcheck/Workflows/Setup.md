# Setup Workflow

Configure ShellCheck for a project with configuration file, pre-commit hooks, and CI integration.

## Trigger

- "setup shellcheck for this project"
- "configure shellcheck"
- "add shellcheck to CI"
- "install shellcheck"

## Process

### 1. Check Installation

```bash
# Check if installed
if command -v shellcheck >/dev/null 2>&1; then
    echo "ShellCheck $(shellcheck --version | head -2 | tail -1) installed"
else
    echo "ShellCheck not installed"
fi
```

### 2. Install ShellCheck

**macOS:**
```bash
brew install shellcheck
```

**Debian/Ubuntu:**
```bash
sudo apt-get update && sudo apt-get install -y shellcheck
```

**Arch Linux:**
```bash
sudo pacman -S shellcheck
```

**Fedora:**
```bash
sudo dnf install ShellCheck
```

**From Binary (Linux):**
```bash
VERSION="v0.11.0"
wget -qO- "https://github.com/koalaman/shellcheck/releases/download/${VERSION}/shellcheck-${VERSION}.linux.x86_64.tar.xz" | tar -xJf -
sudo cp "shellcheck-${VERSION}/shellcheck" /usr/local/bin/
```

### 3. Create .shellcheckrc

Create project configuration:

```bash
cat > .shellcheckrc << 'EOF'
# ShellCheck Configuration
# https://www.shellcheck.net/wiki/

# Shell dialect (sh, bash, dash, ksh, busybox)
shell=bash

# Source file handling
source-path=SCRIPTDIR
source-path=SCRIPTDIR/lib
external-sources=true

# Enable dataflow analysis
extended-analysis=true

# Enable optional checks
enable=deprecate-which
enable=quote-safe-variables
enable=require-variable-braces

# Disable common false positives (customize as needed)
# disable=SC1090  # Can't follow non-constant source
# disable=SC1091  # Not following sourced file
# disable=SC2034  # Variable appears unused
EOF
```

### 4. Setup Pre-commit Hook

**Option A: Using pre-commit framework**

Create/update `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/koalaman/shellcheck-precommit
    rev: v0.11.0
    hooks:
      - id: shellcheck
        args: ["--severity=warning"]
```

Install:
```bash
pip install pre-commit
pre-commit install
```

**Option B: Git hook directly**

```bash
cat > .git/hooks/pre-commit << 'EOF'
#!/bin/bash
# ShellCheck pre-commit hook

set -euo pipefail

# Find staged shell scripts
staged=$(git diff --cached --name-only --diff-filter=ACMR | grep -E '\.(sh|bash)$' || true)

if [[ -n "$staged" ]]; then
    echo "Running ShellCheck..."
    if ! echo "$staged" | xargs shellcheck; then
        echo ""
        echo "ShellCheck found issues. Fix them or use:"
        echo "  git commit --no-verify"
        exit 1
    fi
    echo "ShellCheck passed!"
fi
EOF

chmod +x .git/hooks/pre-commit
```

### 5. Setup CI Pipeline

**GitHub Actions:**

Create `.github/workflows/shellcheck.yml`:

```yaml
name: ShellCheck

on:
  push:
    branches: [main, develop]
    paths:
      - '**.sh'
      - '**.bash'
      - '.shellcheckrc'
  pull_request:
    paths:
      - '**.sh'
      - '**.bash'
      - '.shellcheckrc'

jobs:
  shellcheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run ShellCheck
        uses: ludeeus/action-shellcheck@master
        with:
          severity: warning
          scandir: '.'
          format: gcc
```

**GitLab CI:**

Add to `.gitlab-ci.yml`:

```yaml
shellcheck:
  image: koalaman/shellcheck-alpine:stable
  stage: lint
  script:
    - find . -name "*.sh" -not -path "./.git/*" -exec shellcheck {} +
  only:
    changes:
      - "**/*.sh"
      - ".shellcheckrc"
```

### 6. Add Makefile Target

```makefile
# Add to Makefile
SHELL_SCRIPTS := $(shell find . -name "*.sh" -not -path "./.git/*")

.PHONY: lint lint-shell

lint-shell:
	@echo "Running ShellCheck..."
	@shellcheck $(SHELL_SCRIPTS)

lint: lint-shell
	@echo "All linters passed!"
```

### 7. Editor Configuration

**VS Code:**

Create `.vscode/settings.json`:

```json
{
  "shellcheck.enable": true,
  "shellcheck.run": "onSave",
  "shellcheck.exclude": [],
  "shellcheck.customArgs": ["-x"]
}
```

**Vim (with ALE):**

Add to `.vimrc` or project `.vimrc`:

```vim
let g:ale_linters = {'sh': ['shellcheck'], 'bash': ['shellcheck']}
let g:ale_sh_shellcheck_options = '-x'
```

## Output Format

After setup, present summary:

```markdown
## ShellCheck Setup Complete

### Files Created/Modified

| File | Purpose |
|------|---------|
| `.shellcheckrc` | Project configuration |
| `.pre-commit-config.yaml` | Pre-commit hook |
| `.github/workflows/shellcheck.yml` | CI pipeline |
| `Makefile` | Added `lint-shell` target |

### Quick Commands

```bash
# Check all scripts
make lint-shell

# Check single file
shellcheck script.sh

# Auto-fix issues
shellcheck -f diff script.sh | patch -p1

# Run pre-commit manually
pre-commit run shellcheck --all-files
```

### Configuration Summary

- **Shell:** bash
- **Optional checks:** deprecate-which, quote-safe-variables, require-variable-braces
- **Severity:** warning (CI), all (local)
- **Source paths:** SCRIPTDIR, SCRIPTDIR/lib

### Next Steps

1. Run `shellcheck scripts/*.sh` to check existing scripts
2. Fix any issues or add justified suppressions
3. Commit the configuration files
```

## Customization Options

Ask user about preferences:

1. **Shell dialect:** bash (default), sh, zsh, ksh
2. **Strictness level:** relaxed, standard (default), strict
3. **Optional checks:** which ones to enable
4. **CI platform:** GitHub Actions, GitLab CI, none
5. **Pre-commit:** pre-commit framework, git hook, none
