# uv CLI Reference

Complete command reference for uv - the Python package and project manager.

## Command Structure

```text
uv [OPTIONS] <COMMAND>
```

## Top-Level Commands

| Command | Description |
|---------|-------------|
| `uv init` | Create a new project |
| `uv add` | Add dependencies to the project |
| `uv remove` | Remove dependencies from the project |
| `uv sync` | Update the project's environment |
| `uv lock` | Update the project's lockfile |
| `uv run` | Run a command or script |
| `uv tree` | Display the project's dependency tree |
| `uv export` | Export the project's lockfile to alternate formats |
| `uv version` | Read or update the project's version |
| `uv format` | Format Python code in the project |
| `uv tool` | Run and install commands provided by Python packages |
| `uv python` | Manage Python versions and installations |
| `uv pip` | Manage Python packages with pip-compatible interface |
| `uv venv` | Create a virtual environment |
| `uv build` | Build Python packages into distributions |
| `uv publish` | Upload distributions to an index |
| `uv cache` | Manage uv's cache |
| `uv auth` | Manage authentication |
| `uv self` | Manage the uv executable |
| `uv help` | Display documentation for a command |

---

## Project Commands

### uv init

Create a new project.

```bash
uv init [OPTIONS] [PATH]
```

**Options:**

| Option | Description |
|--------|-------------|
| `--name <NAME>` | Project name (defaults to directory name) |
| `--package` | Create a Python package (default) |
| `--app` | Create an application project |
| `--lib` | Create a library project |
| `--script` | Create a standalone script with inline metadata |
| `--python <VERSION>` | Python version requirement |
| `--no-readme` | Skip README.md creation |
| `--no-pin-python` | Don't create .python-version |
| `--build-backend <BACKEND>` | Build backend (hatchling, flit-core, etc.) |
| `--vcs <VCS>` | Initialize version control (git, none) |

**Examples:**

```bash
uv init my-project
uv init --lib my-library
uv init --app --python 3.12 my-app
uv init --script example.py
```

### uv add

Add dependencies to the project.

```bash
uv add [OPTIONS] <PACKAGES>...
```

**Options:**

| Option | Description |
|--------|-------------|
| `--dev` | Add to development dependencies |
| `--group <GROUP>` | Add to specific dependency group |
| `--optional <EXTRA>` | Add as optional dependency (extra) |
| `--script <SCRIPT>` | Add to inline script metadata |
| `--editable` | Install as editable package |
| `--no-sync` | Don't sync after adding |
| `--frozen` | Don't update lockfile |
| `--locked` | Assert lockfile unchanged |
| `--upgrade-package <PKG>` | Upgrade specific package |
| `--index <URL>` | Package index for this dependency |
| `--python <VERSION>` | Python version for resolution |

**Examples:**

```bash
uv add requests flask
uv add "httpx>=0.20,<1.0"
uv add --dev pytest ruff mypy
uv add --group test pytest-cov
uv add --optional api fastapi uvicorn
uv add --script example.py pandas
uv add "git+https://github.com/user/repo"
uv add torch --index https://download.pytorch.org/whl/cpu
```

### uv remove

Remove dependencies from the project.

```bash
uv remove [OPTIONS] <PACKAGES>...
```

**Options:**

| Option | Description |
|--------|-------------|
| `--dev` | Remove from development dependencies |
| `--group <GROUP>` | Remove from specific group |
| `--optional <EXTRA>` | Remove from optional dependencies |
| `--script <SCRIPT>` | Remove from inline script metadata |
| `--no-sync` | Don't sync after removing |

**Examples:**

```bash
uv remove requests
uv remove --dev pytest
uv remove --group test pytest-cov
```

### uv sync

Update the project's environment.

```bash
uv sync [OPTIONS]
```

**Options:**

| Option | Description |
|--------|-------------|
| `--frozen` | Don't update lockfile |
| `--locked` | Assert lockfile unchanged |
| `--no-dev` | Exclude dev dependencies |
| `--only-dev` | Only dev dependencies |
| `--group <GROUP>` | Include specific group |
| `--no-group <GROUP>` | Exclude specific group |
| `--all-groups` | Include all groups |
| `--no-default-groups` | Exclude default groups |
| `--extra <EXTRA>` | Include optional dependency |
| `--all-extras` | Include all optional dependencies |
| `--no-install-project` | Don't install the project itself |
| `--no-install-workspace` | Don't install workspace members |
| `--no-editable` | Install as non-editable |
| `--exact` | Remove extraneous packages |
| `--inexact` | Keep extraneous packages |
| `--python <VERSION>` | Python version |

**Examples:**

```bash
uv sync
uv sync --locked
uv sync --no-dev --all-extras
uv sync --group test --group lint
uv sync --no-install-project  # Dependencies only (Docker caching)
```

### uv lock

Update the project's lockfile.

```bash
uv lock [OPTIONS]
```

**Options:**

| Option | Description |
|--------|-------------|
| `--check` | Check if lockfile is up-to-date |
| `--upgrade` | Upgrade all packages |
| `--upgrade-package <PKG>` | Upgrade specific package |
| `--script <SCRIPT>` | Lock script dependencies |
| `--python <VERSION>` | Python version |

**Examples:**

```bash
uv lock
uv lock --check  # CI validation
uv lock --upgrade
uv lock --upgrade-package requests
uv lock --script example.py
```

### uv run

Run a command or script in the project environment.

```bash
uv run [OPTIONS] [COMMAND]...
```

**Options:**

| Option | Description |
|--------|-------------|
| `--with <PKG>` | Add temporary dependency |
| `--with-requirements <FILE>` | Add temporary requirements |
| `--module, -m` | Run Python module |
| `--script` | Run as script |
| `--isolated` | Run in isolated environment |
| `--no-sync` | Don't sync environment |
| `--no-project` | Ignore project context |
| `--frozen` | Don't update lockfile |
| `--locked` | Assert lockfile unchanged |
| `--active` | Prefer active virtual environment |
| `--env-file <FILE>` | Load .env file |
| `--python <VERSION>` | Python version |
| `--all-extras` | Include all optional dependencies |
| `--extra <EXTRA>` | Include specific extra |
| `--group <GROUP>` | Include specific group |
| `--no-dev` | Exclude dev dependencies |

**Examples:**

```bash
uv run python script.py
uv run pytest -v
uv run --with pandas python analyze.py
uv run -m my_module
uv run --isolated ruff check .
uv run --env-file .env.local python app.py
echo 'print("hello")' | uv run -
```

### uv tree

Display the project's dependency tree.

```bash
uv tree [OPTIONS]
```

**Options:**

| Option | Description |
|--------|-------------|
| `--depth <N>` | Maximum display depth |
| `--package <PKG>` | Focus on specific package |
| `--prune <PKG>` | Prune specific packages |
| `--invert` | Show reverse dependencies |
| `--no-dev` | Exclude dev dependencies |

**Examples:**

```bash
uv tree
uv tree --depth 2
uv tree --package requests
uv tree --invert --package urllib3
```

### uv export

Export the lockfile to alternate formats.

```bash
uv export [OPTIONS]
```

**Options:**

| Option | Description |
|--------|-------------|
| `--format <FORMAT>` | Output format (requirements-txt, pylock.toml) |
| `--output-file, -o <FILE>` | Output file path |
| `--no-hashes` | Exclude hashes |
| `--no-dev` | Exclude dev dependencies |
| `--all-extras` | Include all extras |
| `--extra <EXTRA>` | Include specific extra |

**Examples:**

```bash
uv export --format requirements-txt -o requirements.txt
uv export --format pylock.toml
uv export --format cyclonedx1.5 -o sbom.json
```

---

## Python Management Commands

### uv python install

Install Python versions.

```bash
uv python install [OPTIONS] [VERSIONS]...
```

**Options:**

| Option | Description |
|--------|-------------|
| `--default` | Install as default (python, python3 executables) |
| `--reinstall` | Reinstall existing versions |
| `--preview` | Include preview releases |

**Examples:**

```bash
uv python install
uv python install 3.12
uv python install 3.11 3.12 3.13
uv python install pypy
uv python install 3.12 --default
```

### uv python list

List available and installed Python versions.

```bash
uv python list [OPTIONS] [VERSION]
```

**Options:**

| Option | Description |
|--------|-------------|
| `--only-installed` | Show only installed versions |
| `--all-versions` | Include all patch versions |
| `--all-platforms` | Show downloads for all platforms |

**Examples:**

```bash
uv python list
uv python list --only-installed
uv python list 3.12
uv python list pypy
```

### uv python pin

Pin Python version for the project.

```bash
uv python pin [OPTIONS] <VERSION>
```

**Options:**

| Option | Description |
|--------|-------------|
| `--global` | Pin globally (user-level) |
| `--resolved` | Pin exact resolved version |

**Examples:**

```bash
uv python pin 3.12
uv python pin --global 3.12
uv python pin 3.12.5 --resolved
```

### uv python find

Find Python executable.

```bash
uv python find [OPTIONS] [VERSION]
```

**Options:**

| Option | Description |
|--------|-------------|
| `--system` | Ignore virtual environments |
| `--no-project` | Ignore project requirements |

**Examples:**

```bash
uv python find
uv python find ">=3.11"
uv python find 3.12
```

### uv python upgrade

Upgrade Python installations.

```bash
uv python upgrade [OPTIONS] [VERSIONS]...
```

**Examples:**

```bash
uv python upgrade 3.12  # Upgrade to latest 3.12.x
uv python upgrade       # Upgrade all installed
```

### uv python uninstall

Uninstall Python versions.

```bash
uv python uninstall <VERSIONS>...
```

**Examples:**

```bash
uv python uninstall 3.11
uv python uninstall 3.11 3.12
```

---

## Tool Commands

### uv tool run (uvx)

Run a tool without installing.

```bash
uvx [OPTIONS] <COMMAND>...
uv tool run [OPTIONS] <COMMAND>...
```

**Options:**

| Option | Description |
|--------|-------------|
| `--from <PKG>` | Package to run from |
| `--with <PKG>` | Additional dependencies |
| `--python <VERSION>` | Python version |
| `--isolated` | Ignore installed version |

**Examples:**

```bash
uvx ruff check .
uvx black --check .
uvx --from httpie http https://api.example.com
uvx ruff@0.5.0 check .
uvx --with mkdocs-material mkdocs build
uvx --python 3.12 mypy .
```

### uv tool install

Install a tool globally.

```bash
uv tool install [OPTIONS] <PACKAGE>
```

**Options:**

| Option | Description |
|--------|-------------|
| `--with <PKG>` | Additional packages |
| `--with-editable <PKG>` | Additional editable packages |
| `--python <VERSION>` | Python version |
| `--force` | Overwrite existing executables |
| `--reinstall` | Reinstall if already installed |

**Examples:**

```bash
uv tool install ruff
uv tool install "ruff==0.5.0"
uv tool install ruff --python 3.12
uv tool install mkdocs --with mkdocs-material
```

### uv tool list

List installed tools.

```bash
uv tool list [OPTIONS]
```

**Options:**

| Option | Description |
|--------|-------------|
| `--show-paths` | Show executable paths |

### uv tool upgrade

Upgrade installed tools.

```bash
uv tool upgrade [OPTIONS] [TOOL]
```

**Options:**

| Option | Description |
|--------|-------------|
| `--all` | Upgrade all tools |
| `--upgrade-package <PKG>` | Upgrade specific dependency |
| `--reinstall` | Reinstall packages |

**Examples:**

```bash
uv tool upgrade ruff
uv tool upgrade --all
```

### uv tool uninstall

Uninstall a tool.

```bash
uv tool uninstall <TOOL>
```

### uv tool update-shell

Update shell configuration for tool PATH.

```bash
uv tool update-shell
```

---

## Virtual Environment Commands

### uv venv

Create a virtual environment.

```bash
uv venv [OPTIONS] [PATH]
```

**Options:**

| Option | Description |
|--------|-------------|
| `--python <VERSION>` | Python version |
| `--system-site-packages` | Allow access to system packages |
| `--seed` | Install seed packages (pip, setuptools) |
| `--relocatable` | Make environment relocatable |
| `--prompt <NAME>` | Custom prompt name |

**Examples:**

```bash
uv venv
uv venv .venv
uv venv --python 3.12 my-env
uv venv --seed  # Include pip
```

---

## pip Interface Commands

### uv pip install

Install packages.

```bash
uv pip install [OPTIONS] <PACKAGES>...
```

**Options:**

| Option | Description |
|--------|-------------|
| `-r, --requirement <FILE>` | Requirements file |
| `-e, --editable <PATH>` | Editable install |
| `-c, --constraint <FILE>` | Constraint file |
| `--index-url <URL>` | Package index |
| `--extra-index-url <URL>` | Additional index |
| `--no-deps` | Don't install dependencies |
| `--no-binary <PKG>` | Build from source |
| `--only-binary <PKG>` | Only use wheels |
| `--upgrade, -U` | Upgrade packages |
| `--reinstall` | Reinstall packages |
| `--system` | Use system Python |
| `--python <VERSION>` | Target Python |

**Examples:**

```bash
uv pip install flask
uv pip install -r requirements.txt
uv pip install -e .
uv pip install --upgrade requests
```

### uv pip uninstall

Uninstall packages.

```bash
uv pip uninstall [OPTIONS] <PACKAGES>...
```

### uv pip compile

Compile requirements.

```bash
uv pip compile [OPTIONS] <SRC>...
```

**Options:**

| Option | Description |
|--------|-------------|
| `-o, --output-file <FILE>` | Output file |
| `--upgrade` | Upgrade all packages |
| `--upgrade-package <PKG>` | Upgrade specific package |
| `--no-header` | Omit header comment |
| `--generate-hashes` | Include hashes |
| `--all-extras` | Include all extras |

**Examples:**

```bash
uv pip compile requirements.in -o requirements.txt
uv pip compile pyproject.toml -o requirements.txt
uv pip compile requirements.in --upgrade
```

### uv pip sync

Sync environment with requirements.

```bash
uv pip sync [OPTIONS] <REQUIREMENTS>...
```

**Examples:**

```bash
uv pip sync requirements.txt
```

### uv pip freeze

List installed packages.

```bash
uv pip freeze [OPTIONS]
```

### uv pip list

List installed packages.

```bash
uv pip list [OPTIONS]
```

**Options:**

| Option | Description |
|--------|-------------|
| `--editable` | Only editable packages |
| `--exclude-editable` | Exclude editable packages |
| `--outdated` | Show outdated packages |
| `--format <FORMAT>` | Output format (columns, freeze, json) |

### uv pip show

Show package information.

```bash
uv pip show <PACKAGES>...
```

### uv pip check

Verify installed packages have compatible dependencies.

```bash
uv pip check
```

---

## Build and Publish Commands

### uv build

Build distributions.

```bash
uv build [OPTIONS] [SRC]
```

**Options:**

| Option | Description |
|--------|-------------|
| `--wheel` | Build only wheel |
| `--sdist` | Build only source distribution |
| `--out-dir, -o <DIR>` | Output directory |
| `--python <VERSION>` | Python version |
| `--no-build-isolation` | Disable build isolation |

**Examples:**

```bash
uv build
uv build --wheel
uv build -o dist/
```

### uv publish

Publish distributions.

```bash
uv publish [OPTIONS] [DIST]...
```

**Options:**

| Option | Description |
|--------|-------------|
| `--repository <URL>` | Repository URL |
| `--token <TOKEN>` | API token |
| `--username <USER>` | Username |
| `--password <PASS>` | Password |
| `--check-url <URL>` | Check if version exists |

**Examples:**

```bash
uv publish
uv publish dist/*
uv publish --token $PYPI_TOKEN
```

---

## Cache Commands

### uv cache clean

Clear cache.

```bash
uv cache clean [PACKAGES]...
```

### uv cache prune

Remove outdated cache entries.

```bash
uv cache prune [OPTIONS]
```

**Options:**

| Option | Description |
|--------|-------------|
| `--ci` | Aggressive pruning for CI |

### uv cache dir

Show cache directory path.

```bash
uv cache dir
```

---

## Authentication Commands

### uv auth login

Authenticate with a service.

```bash
uv auth login [OPTIONS] <SERVICE>
```

**Options:**

| Option | Description |
|--------|-------------|
| `-u, --username <USER>` | Username |
| `-t, --token` | Use API token |
| `--password <PASS>` | Password |
| `--keyring-provider <PROVIDER>` | Credential backend |

**Examples:**

```bash
uv auth login pypi
uv auth login pypi --token
uv auth login https://private.pypi.org
```

### uv auth logout

Remove authentication.

```bash
uv auth logout [OPTIONS] <SERVICE>
```

### uv auth token

Show authentication token.

```bash
uv auth token <SERVICE>
```

---

## Global Options

Available for most commands:

| Option | Description |
|--------|-------------|
| `-v, --verbose` | Verbose output |
| `-q, --quiet` | Quiet output |
| `--color <CHOICE>` | Color output (auto, always, never) |
| `--no-progress` | Hide progress bars |
| `--project <DIR>` | Project directory |
| `--directory <DIR>` | Working directory |
| `--config-file <FILE>` | Config file path |
| `--no-config` | Ignore config files |
| `--cache-dir <DIR>` | Cache directory |
| `--no-cache` | Disable caching |
| `--offline` | Disable network access |
| `--python <VERSION>` | Python version |
| `--managed-python` | Require uv-managed Python |
| `--no-managed-python` | Allow system Python |
| `--no-python-downloads` | Don't download Python |
| `-h, --help` | Show help |

---

## Version Request Formats

uv accepts various Python version formats:

| Format | Example | Description |
|--------|---------|-------------|
| Version | `3.12`, `3.12.5` | Specific version |
| Range | `>=3.11,<3.13` | Version constraint |
| Variant | `3.13t`, `3.13+freethreaded` | Free-threaded |
| Debug | `3.13d`, `3.13+debug` | Debug build |
| Implementation | `cpython`, `pypy` | Python implementation |
| Path | `/usr/bin/python3` | Executable path |

---

## Environment Variables

See `references/integrations.md` for complete environment variable reference.

Key variables:

- `UV_CACHE_DIR` - Cache directory
- `UV_PYTHON` - Default Python version
- `UV_INDEX_URL` / `UV_DEFAULT_INDEX` - Package index
- `UV_FROZEN` - Use lockfile without updating
- `UV_LOCKED` - Assert lockfile unchanged
- `UV_LINK_MODE` - Package linking mode
- `UV_COMPILE_BYTECODE` - Compile .pyc files
