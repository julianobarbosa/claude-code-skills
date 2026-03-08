---
name: justfile-skill
description: |
  Create, edit, and maintain justfiles using the `just` command runner. Use this skill whenever
  the user mentions justfiles, just recipes, just command runner, or wants to migrate from
  Makefile/make to just. Also trigger when the user has a justfile in their project and asks
  about running, organizing, or documenting project commands. Covers migration from make,
  recipe design, variable patterns, dotenv integration, and cross-platform support.
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
---

# Just Command Runner Skill

`just` is a command runner (not a build system) that saves and runs project-specific commands
in a file called `justfile`. It uses make-inspired syntax but is simpler, more portable, and
avoids make's idiosyncrasies like `.PHONY`, tab sensitivity issues, and implicit rules.

## When to Use Just vs Make

| Scenario                                                | Tool                  |
| ------------------------------------------------------- | --------------------- |
| Project task automation (build, test, deploy, lint)     | **just**              |
| Actual file-based build dependencies (compile .c to .o) | **make**              |
| Cross-platform command runner                           | **just**              |
| Legacy projects already deep in make                    | **make** (or migrate) |

## Core Concepts

### Recipe = Target

Recipes are the core unit. Each recipe is a named set of commands:

```just
recipe-name:
    command1
    command2
```

- Indentation MUST be consistent (spaces or tabs, but pick one — `set ignore-comments` helps)
- Each line runs in a **separate shell** by default (use `set shell` or shebang recipes for multi-line scripts)
- No `.PHONY` needed — just doesn't track file timestamps

### Variables

```just
# Assignment
version := "1.0.0"

# Backtick evaluation (runs command, captures stdout)
git_hash := `git rev-parse --short HEAD`

# Environment variable access
home := env('HOME')

# Export to recipe commands
export DATABASE_URL := "postgres://localhost/mydb"
```

### Settings Block

Place settings at the top of the justfile:

```just
set dotenv-load           # Load .env file
set positional-arguments  # Pass recipe args as $1, $2, etc.
set shell := ["bash", "-euco", "pipefail"]  # Fail-fast shell
set export                # Export all variables as env vars
set quiet                 # Suppress command echoing (like @ in make)
```

### Recipe Arguments

```just
# Required argument
deploy target:
    echo "Deploying to {{target}}"

# Default value
greet name="World":
    echo "Hello {{name}}"

# Variadic (one or more)
test +targets:
    go test {{targets}}

# Variadic (zero or more)
lint *flags:
    eslint {{flags}} src/
```

### Dependencies

```just
# Run 'build' before 'test'
test: build
    cargo test

# Pass arguments to dependencies
push: (deploy "production")

# Multiple dependencies
all: clean build test lint
```

### Conditional Logic

```just
# Ternary-style conditional
rust_target := if os() == "macos" { "aarch64-apple-darwin" } else { "x86_64-unknown-linux-gnu" }

# In recipes
check:
    if [ -f .env ]; then echo "Found .env"; fi
```

### Platform-Specific Recipes

```just
[linux]
install:
    sudo apt install ripgrep

[macos]
install:
    brew install ripgrep

[windows]
install:
    choco install ripgrep
```

### Recipe Attributes

```just
[private]           # Hidden from --list
[no-cd]             # Don't cd to justfile directory
[confirm]           # Ask confirmation before running
[confirm("Deploy to production?")]
[no-exit-message]   # Suppress error message on failure
[group("deploy")]   # Group in --list output
[doc("Run the full test suite")]  # Custom doc string
```

### Shebang Recipes (Multi-line Scripts)

When a recipe needs to run as a single script rather than line-by-line:

```just
process-data:
    #!/usr/bin/env python3
    import json
    with open("data.json") as f:
        data = json.load(f)
    print(f"Found {len(data)} records")
```

### Self-Documenting Help

```just
# The default recipe — runs when you type `just` with no args
[private]
default:
    @just --list --unsorted
```

Comments above recipes become descriptions in `just --list`:

```just
# Initialize Terraform with backend config
init:
    terraform init
```

### Imports and Modules

```just
# Import another justfile
import 'ci.just'

# Module (namespaced)
mod deploy 'deploy.just'
# Usage: just deploy::production
```

## References

- [references/justfile-patterns.md](references/justfile-patterns.md) — Common justfile patterns by project type
- [references/make-migration.md](references/make-migration.md) — Makefile-to-justfile migration guide

## Useful Functions

| Function                  | Purpose                                      |
| ------------------------- | -------------------------------------------- |
| `os()`                    | Current OS (`linux`, `macos`, `windows`)     |
| `arch()`                  | CPU architecture (`x86_64`, `aarch64`)       |
| `env('KEY')`              | Get environment variable (aborts if missing) |
| `env('KEY', 'default')`   | Get env var with fallback                    |
| `invocation_directory()`  | Directory where `just` was called from       |
| `justfile_directory()`    | Directory containing the justfile            |
| `join(a, b)`              | Join path components                         |
| `parent_directory(path)`  | Parent of path                               |
| `file_name(path)`         | Filename component                           |
| `without_extension(path)` | Remove file extension                        |
| `uppercase(s)`            | Uppercase string                             |
| `lowercase(s)`            | Lowercase string                             |
| `replace(s, from, to)`    | String replacement                           |
| `trim(s)`                 | Trim whitespace                              |
| `quote(s)`                | Shell-quote a string                         |
| `sha256_file(path)`       | SHA-256 hash of file                         |
| `shell(cmd, args...)`     | Execute command, capture output              |

## Installation

```bash
# macOS
brew install just

# Cargo
cargo install just

# Pre-built binaries
curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh | bash -s -- --to /usr/local/bin

# Shell completions
just --completions zsh > ~/.zsh/completions/_just
just --completions bash > /etc/bash_completion.d/just
```
