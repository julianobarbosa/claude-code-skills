# uv Integrations Reference

Comprehensive guide to integrating uv with Docker, CI/CD, tools, and other systems.

---

## Docker Integration

### Official Docker Images

**Distroless (uv binary only):**

```text
ghcr.io/astral-sh/uv:latest
ghcr.io/astral-sh/uv:0.9.18
ghcr.io/astral-sh/uv:0.9
```

**With OS (Alpine):**

```text
ghcr.io/astral-sh/uv:alpine
ghcr.io/astral-sh/uv:alpine3.22
```

**With OS (Debian):**

```text
ghcr.io/astral-sh/uv:debian-slim
ghcr.io/astral-sh/uv:bookworm-slim
ghcr.io/astral-sh/uv:trixie-slim
```

**With Python:**

```text
ghcr.io/astral-sh/uv:python3.12-bookworm-slim
ghcr.io/astral-sh/uv:python3.12-alpine
```

### Installing uv in Dockerfile

**Copy from distroless image (recommended):**

```dockerfile
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
```

**Pin to specific version:**

```dockerfile
COPY --from=ghcr.io/astral-sh/uv:0.9.18 /uv /uvx /bin/
```

**Pin to SHA256:**

```dockerfile
# Use full SHA for reproducible builds
COPY --from=ghcr.io/astral-sh/uv@sha256:2381d6aa60c326b71... \
  /uv /uvx /bin/
```

**Using installer script:**

```dockerfile
RUN apt-get update && apt-get install -y curl ca-certificates
ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
ENV PATH="/root/.local/bin/:$PATH"
```

### Basic Dockerfile Pattern

```dockerfile
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
COPY pyproject.toml uv.lock ./

ENV UV_NO_DEV=1
RUN uv sync --locked

COPY . .

ENV PATH="/app/.venv/bin:$PATH"
CMD ["python", "-m", "my_app"]
```

### Multi-Stage Build (Optimized)

```dockerfile
# Build stage
FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Install dependencies first (cache layer)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

# Copy source and sync project
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

# Runtime stage
FROM python:3.12-slim
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
CMD ["python", "-m", "my_app"]
```

### Non-Editable Production Build

```dockerfile
FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-editable

COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable

FROM python:3.12-slim
COPY --from=builder /app/.venv /app/.venv
CMD ["/app/.venv/bin/my-app"]
```

### Docker Caching

```dockerfile
# Enable cache mount
ENV UV_LINK_MODE=copy  # Required for separate filesystems

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked
```

### Docker Environment Variables

```dockerfile
ENV UV_NO_DEV=1              # Exclude dev dependencies
ENV UV_COMPILE_BYTECODE=1    # Compile .pyc files
ENV UV_LINK_MODE=copy        # Required for cache mounts
ENV UV_NO_CACHE=1            # Disable caching (smaller image)
```

### .dockerignore

```gitignore
.venv/
__pycache__/
*.pyc
.git/
.pytest_cache/
.mypy_cache/
.ruff_cache/
```

---

## GitHub Actions

### Basic Setup

```yaml
name: CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v5

      - name: Install uv
        uses: astral-sh/setup-uv@v7

      - name: Set up Python
        run: uv python install

      - name: Install dependencies
        run: uv sync --locked

      - name: Run tests
        run: uv run pytest
```

### With Caching

```yaml
- name: Install uv
  uses: astral-sh/setup-uv@v7
  with:
    enable-cache: true
    version: "0.9.18"  # Pin version
```

### Matrix Testing

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]
    steps:
      - uses: actions/checkout@v5
      - uses: astral-sh/setup-uv@v7
        with:
          python-version: ${{ matrix.python-version }}
      - run: uv sync --locked
      - run: uv run pytest
```

### Using setup-python (Faster)

```yaml
- uses: actions/setup-python@v6
  with:
    python-version-file: ".python-version"

- uses: astral-sh/setup-uv@v7
  with:
    enable-cache: true
```

### Manual Caching

```yaml
env:
  UV_CACHE_DIR: /tmp/.uv-cache

jobs:
  test:
    steps:
      - uses: actions/cache@v4
        with:
          path: /tmp/.uv-cache
          key: uv-${{ runner.os }}-${{ hashFiles('uv.lock') }}
          restore-keys: |
            uv-${{ runner.os }}-${{ hashFiles('uv.lock') }}
            uv-${{ runner.os }}

      - run: uv sync --locked
      - run: uv run pytest
      - run: uv cache prune --ci
```

### Publishing to PyPI

```yaml
name: Publish

on:
  push:
    tags:
      - v*

jobs:
  publish:
    runs-on: ubuntu-latest
    environment:
      name: pypi
    permissions:
      id-token: write
      contents: read
    steps:
      - uses: actions/checkout@v5
      - uses: astral-sh/setup-uv@v7

      - name: Build
        run: uv build

      - name: Publish
        run: uv publish
```

---

## GitLab CI/CD

### Basic Configuration

```yaml
variables:
  UV_VERSION: "0.9.18"
  UV_CACHE_DIR: .uv-cache
  UV_LINK_MODE: copy  # Required for GitLab

test:
  image: ghcr.io/astral-sh/uv:$UV_VERSION-python3.12-bookworm-slim
  cache:
    key:
      files:
        - uv.lock
    paths:
      - $UV_CACHE_DIR
  script:
    - uv sync --locked
    - uv run pytest
    - uv cache prune --ci
```

### Distroless Image

```yaml
test:
  image:
    name: ghcr.io/astral-sh/uv:$UV_VERSION
    entrypoint: [""]  # Required for distroless
  script:
    - uv sync --locked
```

### Using System Python

```yaml
variables:
  UV_SYSTEM_PYTHON: 1

test:
  image: python:3.12-slim
  script:
    - curl -LsSf https://astral.sh/uv/install.sh | sh
    - export PATH="$HOME/.local/bin:$PATH"
    - uv pip install -r requirements.txt
```

---

## Pre-Commit Hooks

### Configuration

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/uv-pre-commit
    rev: 0.9.18
    hooks:
      # Keep uv.lock in sync with pyproject.toml
      - id: uv-lock

      # Export to requirements.txt
      - id: uv-export
```

### Compile Requirements

```yaml
repos:
  - repo: https://github.com/astral-sh/uv-pre-commit
    rev: 0.9.18
    hooks:
      - id: pip-compile
        args: [requirements.in, -o, requirements.txt]
```

### Multiple Requirements Files

```yaml
repos:
  - repo: https://github.com/astral-sh/uv-pre-commit
    rev: 0.9.18
    hooks:
      - id: pip-compile
        name: pip-compile requirements.in
        args: [requirements.in, -o, requirements.txt]
      - id: pip-compile
        name: pip-compile requirements-dev.in
        args: [requirements-dev.in, -o, requirements-dev.txt]
        files: ^requirements-dev\.(in|txt)$
```

---

## Tools and Scripts

### Running Tools (uvx)

```bash
# One-off tool execution
uvx ruff check .
uvx black --check .
uvx mypy src/

# Specific version
uvx ruff@0.5.0 check .

# With dependencies
uvx --with mkdocs-material mkdocs build

# From different package
uvx --from httpie http https://api.example.com
```

### Installing Tools Globally

```bash
# Install
uv tool install ruff
uv tool install "ruff==0.5.0"
uv tool install --python 3.12 mypy

# List installed
uv tool list

# Upgrade
uv tool upgrade ruff
uv tool upgrade --all

# Uninstall
uv tool uninstall ruff

# Add to PATH
uv tool update-shell
```

### Scripts with Inline Dependencies (PEP 723)

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "requests<3",
#   "rich",
# ]
# ///

import requests
from rich import print

response = requests.get("https://api.example.com")
print(response.json())
```

```bash
# Make executable and run
chmod +x script.py
./script.py

# Or run directly
uv run script.py

# Add dependencies to script
uv add --script script.py pandas
```

---

## direnv Integration

### Basic .envrc

```bash
# .envrc
if has uv; then
  VIRTUAL_ENV="$(pwd)/.venv"
  if [[ ! -d "$VIRTUAL_ENV" ]]; then
    uv venv
  fi
  PATH_add "$VIRTUAL_ENV/bin"
  export VIRTUAL_ENV
fi
```

### Custom Layout Function

Add to `~/.config/direnv/direnvrc`:

```bash
layout_uv() {
  if ! has uv; then
    log_error "uv not found. Install from https://astral.sh/uv"
    return 1
  fi

  VIRTUAL_ENV="$(pwd)/.venv"
  if [[ ! -d "$VIRTUAL_ENV" ]]; then
    uv venv
  fi

  PATH_add "$VIRTUAL_ENV/bin"
  export VIRTUAL_ENV
}
```

Usage in `.envrc`:

```bash
layout uv
```

---

## IDE Integration

### VS Code

`settings.json`:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.terminal.activateEnvironment": true
}
```

### PyCharm

1. Open Project Settings > Python Interpreter
2. Add Interpreter > Add Local Interpreter
3. Select Existing > Navigate to `.venv/bin/python`

---

## Environment Variables Reference

### Core Settings

| Variable | Purpose | Example |
|----------|---------|---------|
| `UV_CACHE_DIR` | Cache directory | `/tmp/.uv-cache` |
| `UV_PYTHON` | Default Python | `3.12` |
| `UV_PROJECT` | Project directory | `/path/to/project` |
| `UV_CONFIG_FILE` | Config file path | `/path/to/uv.toml` |

### Index Configuration

| Variable | Purpose | Example |
|----------|---------|---------|
| `UV_DEFAULT_INDEX` | Default package index | `https://pypi.org/simple` |
| `UV_INDEX` | Additional indexes | `https://private.pypi.org` |
| `UV_INDEX_{NAME}_USERNAME` | Index username | `user` |
| `UV_INDEX_{NAME}_PASSWORD` | Index password | `pass` |

### Resolution Control

| Variable | Purpose | Example |
|----------|---------|---------|
| `UV_FROZEN` | Don't update lockfile | `1` |
| `UV_LOCKED` | Assert lockfile unchanged | `1` |
| `UV_NO_DEV` | Exclude dev dependencies | `1` |
| `UV_CONSTRAINT` | Constraint files | `constraints.txt` |

### Build Settings

| Variable | Purpose | Example |
|----------|---------|---------|
| `UV_COMPILE_BYTECODE` | Compile .pyc | `1` |
| `UV_LINK_MODE` | Link mode | `copy`, `hardlink`, `symlink` |
| `UV_NO_BINARY` | Build from source | `1` |
| `UV_NO_BUILD` | Only use wheels | `1` |

### Network Settings

| Variable | Purpose | Example |
|----------|---------|---------|
| `UV_HTTP_TIMEOUT` | HTTP timeout (seconds) | `30` |
| `UV_OFFLINE` | Disable network | `1` |
| `UV_NATIVE_TLS` | Use system TLS | `1` |

### Python Management

| Variable | Purpose | Example |
|----------|---------|---------|
| `UV_PYTHON_INSTALL_DIR` | Python install location | `/opt/python` |
| `UV_NO_PYTHON_DOWNLOADS` | Disable auto-download | `1` |
| `UV_MANAGED_PYTHON` | Require managed Python | `1` |

---

## Common Integration Patterns

### Makefile

```makefile
.PHONY: install test lint format

install:
 uv sync --locked

test:
 uv run pytest -v

lint:
 uv run ruff check .
 uv run mypy src/

format:
 uv run ruff format .
 uv run ruff check --fix .

build:
 uv build

publish:
 uv publish
```

### tox Alternative

```bash
# Run tests across Python versions
for py in 3.10 3.11 3.12; do
  uv run --python $py pytest
done
```

### Docker Compose Development

```yaml
# docker-compose.yml
services:
  app:
    build: .
    volumes:
      - .:/app
      - /app/.venv  # Preserve container's venv
    command: uv run python -m my_app

# docker-compose.override.yml (development)
services:
  app:
    develop:
      watch:
        - action: sync
          path: .
          target: /app
          ignore:
            - .venv/
        - action: rebuild
          path: ./pyproject.toml
```

### Deployment Script

```bash
#!/bin/bash
set -e

# Production deployment
uv sync --locked --no-dev
uv run python -m my_app
```

---

## Troubleshooting Integrations

### Docker Issues

| Issue | Solution |
|-------|----------|
| Cache mount failures | Set `UV_LINK_MODE=copy` |
| Slow builds | Use multi-stage builds with cache mounts |
| Large images | Use `--no-cache` or distroless base |

### CI/CD Issues

| Issue | Solution |
|-------|----------|
| Lockfile changes | Use `--locked` flag |
| Cache bloat | Run `uv cache prune --ci` |
| Slow jobs | Enable caching in setup action |

### Tool Issues

| Issue | Solution |
|-------|----------|
| Tool not on PATH | Run `uv tool update-shell` |
| Wrong tool version | Use `uvx tool@version` |
| Python version mismatch | Use `--python` flag |
