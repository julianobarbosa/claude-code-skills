# uv Python Version Management Reference

Comprehensive guide to managing Python versions with uv.

## Overview

uv provides integrated Python version management:

- Automatic Python downloads when needed
- Multiple version installations
- Version pinning per project or globally
- Support for CPython, PyPy, GraalPy, and Pyodide

---

## Installing Python

### Basic Installation

```bash
# Install latest Python
uv python install

# Install specific version
uv python install 3.12
uv python install 3.12.5

# Install multiple versions
uv python install 3.11 3.12 3.13

# Install with default executables (python, python3)
uv python install 3.12 --default
```

### Alternative Implementations

```bash
# PyPy
uv python install pypy
uv python install pypy@3.10

# GraalPy
uv python install graalpy

# Specific implementation version
uv python install cpython@3.12
```

### Version Constraints

```bash
# Range constraint
uv python install ">=3.11,<3.13"

# Latest satisfying constraint
uv python install ">=3.10"
```

### Installation Options

```bash
# Reinstall existing versions
uv python install --reinstall

# Include preview releases
uv python install --preview
```

---

## Listing Python Versions

### Basic Listing

```bash
# Show available and installed versions
uv python list

# Filter by version
uv python list 3.12
uv python list pypy

# Show only installed
uv python list --only-installed
```

### Advanced Listing

```bash
# Include all patch versions
uv python list --all-versions

# Show downloads for all platforms
uv python list --all-platforms
```

### Output Example

```text
cpython-3.13.1-macos-aarch64-none     # installed
cpython-3.12.8-macos-aarch64-none     # installed
cpython-3.12.7-macos-aarch64-none     # available
cpython-3.11.10-macos-aarch64-none    # installed
pypy-3.10.14-macos-aarch64-none       # available
```

---

## Version Pinning

### Project-Level Pin

```bash
# Create .python-version in current directory
uv python pin 3.12

# Pin exact version
uv python pin 3.12.5

# Pin with resolved exact version
uv python pin 3.12 --resolved
```

### Global Pin

```bash
# User-level default
uv python pin --global 3.12
```

### Pin File Format

`.python-version`:

```text
3.12
```

For multiple versions (`.python-versions`):

```text
3.11
3.12
3.13
```

### pyproject.toml Constraint

```toml
[project]
requires-python = ">=3.11"
```

---

## Finding Python

### Basic Find

```bash
# Find first available Python
uv python find

# Find specific version
uv python find 3.12
uv python find ">=3.11"
```

### Find Options

```bash
# Ignore virtual environments
uv python find --system

# Ignore project requirements
uv python find --no-project
```

### Discovery Order

1. Managed Python installations (`UV_PYTHON_INSTALL_DIR`)
2. `PATH` executables (`python`, `python3`, `python3.x`)
3. Windows registry / Microsoft Store (Windows only)

---

## Version Selection

### Command-Line Override

```bash
# Use specific version for any command
uv sync --python 3.12
uv run --python 3.11 python script.py
uv venv --python 3.12
```

### Environment Variable

```bash
# Set default Python
export UV_PYTHON=3.12
```

### Selection Priority

1. `--python` command-line argument
2. `UV_PYTHON` environment variable
3. `.python-version` file (searches up directory tree)
4. `requires-python` in `pyproject.toml`
5. First available Python

---

## Version Request Formats

### Standard Formats

| Format | Example | Description |
|--------|---------|-------------|
| Major | `3` | Any 3.x version |
| Minor | `3.12` | Any 3.12.x version |
| Patch | `3.12.5` | Exact version |
| Range | `>=3.11,<3.13` | Version constraint |
| Implementation | `cpython`, `pypy` | Specific implementation |
| Combined | `cpython@3.12` | Implementation + version |
| Path | `/usr/bin/python3` | Executable path |
| Name | `python3.12` | Executable name |

### Special Variants

```bash
# Free-threaded Python (3.13+)
uv python install 3.13t
uv python install 3.13+freethreaded

# Debug build
uv python install 3.13d
uv python install 3.13+debug

# Force GIL-enabled (3.14+)
uv python install 3.14+gil
```

### Platform-Specific

```bash
# Full specification
uv python install cpython-3.12.3-macos-aarch64-none
uv python install cpython-3.12.3-linux-x86_64-gnu
```

---

## Upgrading Python

### Upgrade Command (Preview)

```bash
# Upgrade to latest patch version
uv python upgrade 3.12

# Upgrade all installed versions
uv python upgrade
```

Note: Only supports patch upgrades (3.12.x -> 3.12.y), not minor upgrades.

### Auto-Upgrade Virtual Environments (Preview)

```bash
# Enable with preview features
uv python install 3.12 --preview-features python-upgrade
```

---

## Uninstalling Python

```bash
# Remove specific version
uv python uninstall 3.11

# Remove multiple versions
uv python uninstall 3.11 3.12
```

---

## Configuration

### Environment Variables

| Variable | Purpose |
|----------|---------|
| `UV_PYTHON` | Default Python version |
| `UV_PYTHON_INSTALL_DIR` | Python installation directory |
| `UV_PYTHON_PREFERENCE` | Version selection preference |
| `UV_NO_PYTHON_DOWNLOADS` | Disable automatic downloads |
| `UV_MANAGED_PYTHON` | Require uv-managed Python |

### Python Preference

Configure how uv selects Python:

```toml
# uv.toml or [tool.uv] in pyproject.toml
[tool.uv]
python-preference = "managed"  # default
```

Options:

- `managed` - Prefer uv-managed, fall back to system
- `only-managed` - Only use uv-managed versions
- `system` - Prefer system over managed
- `only-system` - Only use system versions

### Disable Auto-Download

```bash
# Command-line
uv sync --no-python-downloads

# Environment variable
export UV_NO_PYTHON_DOWNLOADS=1

# Configuration file
[tool.uv]
python-downloads = "manual"
```

---

## Supported Implementations

### CPython (Default)

- Source: Astral's `python-build-standalone`
- Self-contained, portable, performant
- Aliases: `cpython`, `cp`

### PyPy

- Source: PyPy project official distributions
- JIT-compiled Python
- Aliases: `pypy`, `pp`

### GraalPy

- Source: GraalPy project distributions
- Aliases: `graalpy`, `gp`

### Pyodide

- WebAssembly Python
- Alias: `pyodide`

---

## Platform Support

### Supported Platforms

| Platform | Architecture | Notes |
|----------|--------------|-------|
| macOS | x86_64, aarch64 | Rosetta 2 supports x86_64 on ARM |
| Linux | x86_64, aarch64 | glibc-based |
| Windows | x86_64, aarch64 | WoA emulation for x86_64 |

### Transparent Emulation

On macOS (aarch64) with Rosetta 2:

- Both x86_64 and aarch64 binaries work
- uv can use either, packages must match architecture

On Windows (ARM) with WoA:

- x86_64 binaries work via emulation
- Same architectural consistency requirement

---

## Windows Integration

### Registry Integration

uv automatically registers managed Python in Windows registry (PEP 514):

- Enables discovery by `py` launcher
- Enables discovery by other tools

### Using py Launcher

```cmd
py -V:Astral/CPython3.13.1
```

---

## Common Workflows

### Multi-Version Testing

```bash
# Install multiple versions
uv python install 3.10 3.11 3.12 3.13

# Test against each
for v in 3.10 3.11 3.12 3.13; do
  uv run --python $v pytest
done
```

### Project with Specific Version

```bash
# Pin version
uv python pin 3.12

# Sync will use pinned version
uv sync

# Run uses pinned version
uv run python --version
```

### Isolated Tool Execution

```bash
# Run tool with specific Python
uvx --python 3.11 ruff check .

# Install tool with specific Python
uv tool install --python 3.12 mypy
```

### CI/CD Configuration

```yaml
# GitHub Actions
- uses: astral-sh/setup-uv@v7
  with:
    python-version: "3.12"

# Or use matrix
strategy:
  matrix:
    python-version: ["3.10", "3.11", "3.12"]
steps:
  - uses: astral-sh/setup-uv@v7
    with:
      python-version: ${{ matrix.python-version }}
```

---

## Troubleshooting

### Version Not Found

```bash
# Check available versions
uv python list --all-versions

# Check if installed
uv python list --only-installed

# Force download
uv python install 3.12
```

### Wrong Version Selected

```bash
# Check what's being used
uv python find

# Explicitly specify
uv run --python 3.12 python --version

# Check .python-version
cat .python-version

# Check pyproject.toml
grep requires-python pyproject.toml
```

### Virtual Environment Issues

```bash
# Recreate with specific version
rm -rf .venv
uv venv --python 3.12
uv sync
```

### System Python Conflicts

```bash
# Use only managed Python
export UV_MANAGED_PYTHON=1

# Or configure
[tool.uv]
python-preference = "only-managed"
```
