# Justfile Templates

Copy-and-adapt starting points that satisfy the house conventions in `SKILL.md`. After adapting,
run `bun Tools/lint.ts <dir>` and fix any failures.

## Root Justfile (thin orchestrator)

The root holds project-wide variables, module imports, and shortcut recipes that delegate to
modules. Extract recipes into modules by concern even for small projects.

```just
#!/usr/bin/env just --justfile
set shell := ["bash", "-euo", "pipefail", "-c"]
set dotenv-load := true

# --- Variables ---
app_name := env_var_or_default("APP_NAME", "myapp")

# --- Modules ---
mod docker '.justfiles/docker.just'
mod test '.justfiles/test.just'
mod ci '.justfiles/ci.just'

# --- Recipes ---

# List all available recipes
_default:
    @just --list --unsorted --list-submodules

# Start the development environment (shortcut)
dev: docker-dev

# Run tests (shortcut)
test *filter="":
    just -f "{{justfile()}}" test run {{filter}}

# Build the project (shortcut)
build: docker-build

# Run linters (shortcut)
lint: ci-lint

# Run all quality gates
check: lint test

# Tear down everything — DESTRUCTIVE, prompts for confirmation
destroy:
    @echo "This will destroy everything. Continue? [y/N]" && read ans && [ "$ans" = "y" ]
    echo "Destroying..."
```

## Module file (`.justfiles/<name>.just`)

Modules use the same three-line header and their own `_default`. Module recipes run from the
module's directory, so build absolute paths with `source_directory() / ".."` instead of bare
relative paths.

```just
#!/usr/bin/env just --justfile
set shell := ["bash", "-euo", "pipefail", "-c"]
set dotenv-load := false

# --- Variables ---
root := source_directory() / ".."
registry := env_var_or_default("REGISTRY", "ghcr.io/myorg")
image := env_var_or_default("IMAGE", "myapp")
tag := env_var_or_default("TAG", "latest")

# --- Recipes ---

# List recipes in this module
_default:
    @just --list --unsorted

# Build the Docker image
# target - build stage to target (default: production)
build target="production":
    docker build --target {{target}} -t {{registry}}/{{image}}:{{tag}} .

# Push the image to the registry
push: build
    docker push {{registry}}/{{image}}:{{tag}}

# Run the container locally
# args - additional docker run arguments (default: "")
run *args="":
    docker run --rm {{args}} {{registry}}/{{image}}:{{tag}}
```

## Single-concern project (one `dev.just`)

For a Go/Rust/Python project with only build/test/lint/fmt, use a single `dev.just` module and keep
the root thin with shortcuts.

```just
# .justfiles/dev.just
#!/usr/bin/env just --justfile
set shell := ["bash", "-euo", "pipefail", "-c"]
set dotenv-load := false

# --- Variables ---
root := source_directory() / ".."

# --- Recipes ---

# List recipes in this module
_default:
    @just --list --unsorted

# Run the test suite
test *args="":
    cargo test {{args}}

# Run linters
lint:
    cargo clippy -- -D warnings

# Format code
fmt:
    cargo fmt
```
