# uv Command Reference

Complete reference for uv (astral-sh/uv) Python package manager.

## Installation

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Update uv
uv self update
```

## Project Management

```bash
# Initialize
uv init <name>                    # Create new project
uv init --lib <name>              # Create library project
uv init --app <name>              # Create application project

# Dependencies
uv add <package>                  # Add dependency
uv add <package>==1.0.0           # Add specific version
uv add <package>>=1.0,<2.0        # Add version range
uv add --dev <package>            # Add dev dependency
uv add --optional <group> <pkg>   # Add optional dependency
uv remove <package>               # Remove dependency

# Sync & Lock
uv lock                           # Generate/update lockfile
uv sync                           # Sync environment with lockfile
uv sync --frozen                  # Sync without updating lock
uv sync --all-extras              # Include all optional deps
```

## Running Code

```bash
# Run commands in project environment
uv run python script.py           # Run Python script
uv run pytest                     # Run pytest
uv run flask run                  # Run Flask
uv run <any-command>              # Run any command

# Run with specific Python
uv run --python 3.12 script.py
```

## Tools (pipx replacement)

```bash
# Run tools ephemerally
uvx ruff check .                  # Run ruff without installing
uvx black .                       # Run black formatter
uvx --from package tool           # Run tool from package

# Install tools globally
uv tool install ruff              # Install tool
uv tool upgrade ruff              # Upgrade tool
uv tool uninstall ruff            # Remove tool
uv tool list                      # List installed tools
```

## Python Version Management

```bash
# Install Python versions
uv python install 3.12            # Install specific version
uv python install 3.11 3.12       # Install multiple versions
uv python list                    # List available versions
uv python list --installed        # List installed versions

# Pin version for project
uv python pin 3.12                # Creates .python-version file

# Create venv with specific version
uv venv --python 3.12
```

## Virtual Environments

```bash
# Create venv
uv venv                           # Create .venv
uv venv myenv                     # Create named venv
uv venv --python 3.12             # With specific Python

# Activate (standard way)
source .venv/bin/activate         # Linux/macOS
.venv\Scripts\activate            # Windows
```

## pip Interface (drop-in replacement)

```bash
# Install packages
uv pip install <package>
uv pip install -r requirements.txt
uv pip install -e .               # Editable install

# Compile requirements
uv pip compile requirements.in -o requirements.txt
uv pip compile --universal        # Platform-independent

# Sync environment
uv pip sync requirements.txt

# Other pip commands
uv pip list
uv pip show <package>
uv pip freeze
uv pip uninstall <package>
```

## Scripts with Inline Dependencies

```bash
# Add dependencies to script
uv add --script script.py requests pandas

# Run script (auto-installs deps)
uv run script.py
```

Script format:

```python
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "requests>=2.31",
#     "pandas>=2.0",
# ]
# ///

import requests
import pandas as pd
# ...
```

## Build & Publish

```bash
# Build package
uv build                          # Build sdist and wheel
uv build --sdist                  # Build source dist only
uv build --wheel                  # Build wheel only

# Publish to PyPI
uv publish                        # Publish to PyPI
uv publish --token <token>        # With API token
```

## Configuration

### pyproject.toml

```toml
[project]
name = "my-package"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "flask>=3.0",
]

[project.optional-dependencies]
dev = ["pytest", "ruff", "mypy"]

[tool.uv]
dev-dependencies = [
    "pytest>=8.0",
]
```

## Environment Variables

```bash
UV_CACHE_DIR          # Cache directory location
UV_NO_CACHE           # Disable cache
UV_PYTHON             # Default Python version
UV_SYSTEM_PYTHON      # Use system Python
UV_COMPILE_BYTECODE   # Compile .pyc files
```
