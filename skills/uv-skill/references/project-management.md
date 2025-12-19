# uv Project Management Reference

Comprehensive guide to managing Python projects with uv.

## Project Structure

### Core Files

```text
my-project/
├── pyproject.toml          # Project definition (required)
├── uv.lock                  # Lock file (auto-generated)
├── .venv/                   # Virtual environment (auto-created)
├── .python-version         # Python version pin (optional)
├── README.md
└── src/
    └── my_project/
        ├── __init__.py
        └── main.py
```

### File Purposes

| File | Purpose | Version Control |
|------|---------|-----------------|
| `pyproject.toml` | Project metadata, dependencies, configuration | Yes |
| `uv.lock` | Exact resolved versions for reproducibility | Yes |
| `.venv/` | Virtual environment (auto-excluded) | No |
| `.python-version` | Python version pin | Yes |

---

## pyproject.toml Configuration

### Minimal Configuration

```toml
[project]
name = "my-project"
version = "0.1.0"
```

### Complete Example

```toml
[project]
name = "my-project"
version = "0.1.0"
description = "My awesome Python project"
readme = "README.md"
license = { text = "MIT" }
authors = [
    { name = "Your Name", email = "you@example.com" }
]
keywords = ["python", "example"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
]
requires-python = ">=3.11"

# Main dependencies
dependencies = [
    "requests>=2.28",
    "click>=8.0",
    "pydantic>=2.0",
]

# Optional dependencies (extras)
[project.optional-dependencies]
api = ["fastapi>=0.100", "uvicorn>=0.23"]
database = ["sqlalchemy>=2.0", "alembic>=1.12"]
all = ["my-project[api,database]"]

# Entry points
[project.scripts]
my-cli = "my_project.cli:main"

[project.gui-scripts]
my-gui = "my_project.gui:main"

[project.entry-points."my_project.plugins"]
plugin-a = "my_project.plugins:PluginA"

# URLs
[project.urls]
Homepage = "https://github.com/user/my-project"
Documentation = "https://my-project.readthedocs.io"
Repository = "https://github.com/user/my-project"

# Build system
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

# Dependency groups (PEP 735)
[dependency-groups]
dev = ["pytest>=8", "ruff>=0.5", "mypy>=1.10"]
test = ["pytest-cov>=5", "pytest-asyncio>=0.23"]
docs = ["sphinx>=7", "myst-parser>=3"]
lint = ["ruff>=0.5", "mypy>=1.10", "pre-commit>=3"]

# UV-specific configuration
[tool.uv]
# Default groups to install
default-groups = ["dev"]

# Alternative dev dependencies (deprecated, use dependency-groups)
dev-dependencies = ["pytest", "ruff"]

# Constraint dependencies
constraint-dependencies = ["grpcio<1.65"]

# Override dependencies (force specific versions)
override-dependencies = ["werkzeug==2.3.0"]

# Exclude from resolution
exclude-dependencies = ["some-package"]

# Package indexes
[[tool.uv.index]]
name = "pytorch"
url = "https://download.pytorch.org/whl/cpu"
explicit = true

[[tool.uv.index]]
name = "private"
url = "https://pypi.company.com/simple"

# Dependency sources
[tool.uv.sources]
# Git repository
my-lib = { git = "https://github.com/user/my-lib" }
my-lib-branch = { git = "https://github.com/user/my-lib", branch = "develop" }
my-lib-tag = { git = "https://github.com/user/my-lib", tag = "v1.0.0" }
my-lib-rev = { git = "https://github.com/user/my-lib", rev = "abc123" }

# Local path
local-pkg = { path = "./packages/local-pkg" }
local-editable = { path = "./packages/local-pkg", editable = true }

# Specific index
torch = { index = "pytorch" }

# URL
direct-pkg = { url = "https://example.com/package-1.0.0.whl" }

# Environment markers
[tool.uv.sources.jax]
marker = "sys_platform == 'linux'"

# Target environments for resolution
[tool.uv]
environments = [
    "sys_platform == 'darwin'",
    "sys_platform == 'linux'",
]

# Conflicts (mutually exclusive extras/groups)
[tool.uv]
conflicts = [
    [
        { extra = "cpu" },
        { extra = "cuda" },
    ]
]

# pip interface settings (only for uv pip commands)
[tool.uv.pip]
index-url = "https://pypi.org/simple"
```

---

## Dependency Management

### Adding Dependencies

```bash
# Add to project.dependencies
uv add requests
uv add "requests>=2.28"
uv add requests flask sqlalchemy

# Add development dependencies
uv add --dev pytest ruff mypy

# Add to specific group
uv add --group test pytest-cov
uv add --group lint ruff mypy

# Add optional dependency (extra)
uv add --optional api fastapi uvicorn

# Add from different sources
uv add "git+https://github.com/user/repo"
uv add "git+https://github.com/user/repo@v1.0.0"
uv add "../local-package"
uv add torch --index https://download.pytorch.org/whl/cpu

# Platform-specific dependency
uv add "jax; sys_platform == 'linux'"
```

### Removing Dependencies

```bash
uv remove requests
uv remove --dev pytest
uv remove --group test pytest-cov
uv remove --optional api fastapi
```

### Updating Dependencies

```bash
# Upgrade all dependencies
uv lock --upgrade

# Upgrade specific package
uv lock --upgrade-package requests

# Change version constraint
uv add "requests>=2.30"
```

---

## Lock File Management

### Lock File Behavior

The `uv.lock` file:

- Contains exact resolved versions for all platforms/Python versions
- Is human-readable TOML format
- Should be committed to version control
- Is managed by uv (don't edit manually)

### Lock Commands

```bash
# Create/update lock file
uv lock

# Check if lock file is up-to-date
uv lock --check

# Upgrade all packages
uv lock --upgrade

# Upgrade specific package
uv lock --upgrade-package requests
uv lock --upgrade-package "requests==2.32.0"
```

### Lock File Freshness

Lock file is considered outdated when:

- Dependencies added/removed from pyproject.toml
- Version constraints changed to exclude locked version

Lock file remains valid when:

- New upstream versions released (explicit upgrade needed)
- Constraint changes still include locked version

---

## Environment Synchronization

### Basic Sync

```bash
# Sync environment (includes dev by default)
uv sync

# Use exact lockfile (CI/production)
uv sync --locked

# Don't update lockfile
uv sync --frozen
```

### Controlling What's Installed

```bash
# Exclude development dependencies
uv sync --no-dev

# Only development dependencies
uv sync --only-dev

# Include specific group
uv sync --group test
uv sync --group test --group lint

# Exclude specific group
uv sync --no-group lint

# All groups
uv sync --all-groups

# No default groups
uv sync --no-default-groups

# Include extras (optional dependencies)
uv sync --extra api
uv sync --all-extras

# Only specific group (no project)
uv sync --only-group test
```

### Partial Installation (Docker/CI Optimization)

```bash
# Install dependencies without project
uv sync --no-install-project

# Skip specific packages
uv sync --no-install-package dev-only-lib

# Skip workspace members
uv sync --no-install-workspace
```

### Sync Options

```bash
# Remove extraneous packages (default)
uv sync --exact

# Keep extraneous packages
uv sync --inexact

# Non-editable install
uv sync --no-editable
```

---

## Running Commands

### Basic Execution

```bash
# Run command in project environment
uv run python script.py
uv run pytest
uv run my-cli --help

# Run Python module
uv run -m my_module

# Arguments after command passed directly
uv run pytest -v --tb=short
```

### Execution Options

```bash
# Use lockfile only (error if outdated)
uv run --locked python script.py

# Don't check environment freshness
uv run --frozen python script.py

# Don't sync environment
uv run --no-sync python script.py

# Include temporary dependency
uv run --with pandas python analyze.py

# Isolated environment
uv run --isolated python script.py

# Load environment file
uv run --env-file .env python app.py

# Include extras
uv run --all-extras python script.py
uv run --extra api python script.py
```

---

## Workspaces

### Workspace Structure

```text
workspace-root/
├── pyproject.toml          # Workspace root
├── uv.lock                  # Single lockfile for entire workspace
├── packages/
│   ├── package-a/
│   │   ├── pyproject.toml
│   │   └── src/
│   └── package-b/
│       ├── pyproject.toml
│       └── src/
└── apps/
    └── my-app/
        ├── pyproject.toml
        └── src/
```

### Workspace Configuration

```toml
# workspace-root/pyproject.toml
[tool.uv.workspace]
members = ["packages/*", "apps/*"]

# Exclude patterns
exclude = ["packages/deprecated-*"]
```

### Workspace Commands

```bash
# Sync all workspace members
uv sync --all-packages

# Run in specific package
uv run --package package-a pytest

# Add dependency to workspace member
uv add --package package-a requests
```

---

## Dependency Groups (PEP 735)

### Defining Groups

```toml
[dependency-groups]
dev = [
    "pytest>=8",
    "ruff>=0.5",
    "mypy>=1.10",
]
test = [
    "pytest-cov>=5",
    "pytest-asyncio>=0.23",
]
docs = [
    "sphinx>=7",
    "myst-parser>=3",
]
all = [
    { include-group = "test" },
    { include-group = "docs" },
]

# Group with Python version constraint
[tool.uv.dependency-groups]
typing = { requires-python = ">=3.10" }
```

### Using Groups

```bash
# Default behavior (includes default-groups)
uv sync

# Include specific group
uv sync --group test

# Multiple groups
uv sync --group test --group docs

# Exclude group
uv sync --no-group lint

# All groups
uv sync --all-groups

# Only specific group
uv sync --only-group test
```

### Default Groups

```toml
[tool.uv]
# Single group
default-groups = ["dev"]

# Multiple groups
default-groups = ["dev", "lint"]

# All groups
default-groups = "all"
```

---

## Optional Dependencies (Extras)

### Defining Extras

```toml
[project.optional-dependencies]
api = ["fastapi>=0.100", "uvicorn>=0.23"]
database = ["sqlalchemy>=2.0", "alembic>=1.12"]
redis = ["redis>=5.0"]
all = ["my-project[api,database,redis]"]
```

### Using Extras

```bash
# Sync with extra
uv sync --extra api

# Multiple extras
uv sync --extra api --extra database

# All extras
uv sync --all-extras

# Run with extra
uv run --extra api python app.py
```

---

## Package Indexes

### Configuring Indexes

```toml
# Default index (replaces PyPI)
[[tool.uv.index]]
url = "https://pypi.company.com/simple"
default = true

# Additional index
[[tool.uv.index]]
name = "pytorch"
url = "https://download.pytorch.org/whl/cpu"

# Explicit index (only for explicitly mapped packages)
[[tool.uv.index]]
name = "private"
url = "https://private.pypi.org/simple"
explicit = true

# Map package to index
[tool.uv.sources]
torch = { index = "pytorch" }
private-pkg = { index = "private" }
```

### Index Authentication

```bash
# Environment variable
UV_INDEX_PRIVATE_USERNAME=user
UV_INDEX_PRIVATE_PASSWORD=pass

# Or login
uv auth login https://private.pypi.org
```

---

## Constraints and Overrides

### Constraint Dependencies

Limit versions without adding as dependencies:

```toml
[tool.uv]
constraint-dependencies = [
    "grpcio<1.65",
    "protobuf<5.0",
]
```

### Override Dependencies

Force specific versions (dangerous - use sparingly):

```toml
[tool.uv]
override-dependencies = [
    "werkzeug==2.3.0",
]
```

### Build Constraints

Constrain build dependencies:

```toml
[tool.uv]
build-constraint-dependencies = [
    "setuptools==60.0.0",
]
```

---

## Exporting Lock Files

### Export Formats

```bash
# Requirements.txt format
uv export --format requirements-txt -o requirements.txt

# PEP 751 pylock.toml
uv export --format pylock.toml -o pylock.toml

# CycloneDX SBOM
uv export --format cyclonedx1.5 -o sbom.json
```

### Export Options

```bash
# Without hashes
uv export --format requirements-txt --no-hashes

# Without dev dependencies
uv export --no-dev

# With specific extras
uv export --extra api

# With all extras
uv export --all-extras
```

---

## Virtual and Non-Package Projects

### Virtual Project (No Package)

For applications that won't be published:

```toml
[project]
name = "my-app"
version = "0.1.0"

[tool.uv]
package = false  # Don't treat as installable package
```

### Unmanaged Project

Opt out of uv management:

```toml
[tool.uv]
managed = false
```

---

## Best Practices

### Version Control

```gitignore
# .gitignore
.venv/
__pycache__/
*.pyc
.pytest_cache/
.mypy_cache/
.ruff_cache/
dist/
*.egg-info/

# Don't ignore these:
# pyproject.toml
# uv.lock
# .python-version
```

### Development Workflow

1. **Initial setup:**

   ```bash
   uv sync
   ```

2. **Add dependencies:**

   ```bash
   uv add requests
   uv add --dev pytest
   ```

3. **Run code:**

   ```bash
   uv run python script.py
   uv run pytest
   ```

4. **Update dependencies:**

   ```bash
   uv lock --upgrade-package requests
   ```

5. **Commit changes:**

   ```bash
   git add pyproject.toml uv.lock
   git commit -m "Update dependencies"
   ```

### CI/CD

```bash
# Always use --locked in CI
uv sync --locked

# Prune cache after CI job
uv cache prune --ci
```

### Docker

```dockerfile
# Install dependencies first (for caching)
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project

# Then copy source
COPY . .
RUN uv sync --locked
```
