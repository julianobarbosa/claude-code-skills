# Just Language Reference

The `just` language: recipes, variables, settings, arguments, dependencies, conditionals,
attributes, functions, and installation. Style-neutral syntax — apply the house conventions in
`SKILL.md` (header, `_default`, `env_var_or_default`, `.justfiles/` modules) when assembling a real
Justfile.

## Recipe = Target

Recipes are the core unit — a named set of commands:

```just
recipe-name:
    command1
    command2
```

- Indentation MUST be consistent (the three-line header pins `set shell`).
- Each line runs in a **separate shell** by default — use a shebang recipe for multi-line scripts.
- No `.PHONY` needed — just doesn't track file timestamps.

## Variables

```just
# Assignment
version := "1.0.0"

# Backtick evaluation (runs command, captures stdout — at parse time, every invocation)
git_hash := `git rev-parse --short HEAD`

# Environment variable with fallback (house style — never bare env())
home := env_var_or_default("HOME", "/root")

# Export to recipe commands as an env var
export DATABASE_URL := "postgres://localhost/mydb"
```

## Settings

The three-line house header pins the most important ones. Other useful settings:

```just
set positional-arguments   # Pass recipe args as $1, $2, ...
set export                 # Export all variables as env vars
set dotenv-path := "..."   # Override which .env file dotenv-load reads
```

## Recipe Arguments

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

## Dependencies

```just
# Run 'build' before 'test'
test: build
    cargo test

# Pass arguments to a dependency
push: (deploy "production")

# Multiple dependencies
all: clean build test lint
```

## Conditionals

```just
# Ternary-style assignment
rust_target := if os() == "macos" { "aarch64-apple-darwin" } else { "x86_64-unknown-linux-gnu" }

# Inside a recipe
check:
    if [ -f .env ]; then echo "Found .env"; fi
```

## Platform-Specific Recipes

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

> Gotcha: on an OS with no matching variant, `just install` exits 0 silently — looks like success.

## Recipe Attributes

```just
[private]                          # Hidden from --list (still callable)
[no-cd]                            # Don't cd to justfile directory
[confirm]                          # Ask confirmation before running
[confirm("Deploy to production?")] # Custom confirmation prompt
[no-exit-message]                  # Suppress error message on failure
[group("deploy")]                  # Group in --list output
[doc("Run the full test suite")]   # Custom doc string
```

## Shebang Recipes (multi-line scripts)

When a recipe must run as one script instead of line-by-line (the fix for the separate-shell and
`pipefail` gotchas):

```just
process-data:
    #!/usr/bin/env python3
    import json
    with open("data.json") as f:
        data = json.load(f)
    print(f"Found {len(data)} records")
```

## Self-Documenting Help

The `_default` recipe runs when you type `just` with no args. Comments above recipes become their
`--list` descriptions:

```just
# List all available recipes
_default:
    @just --list --unsorted

# Initialize Terraform with backend config
init:
    terraform init
```

## Imports and Modules

```just
# Import another justfile (merged into the namespace)
import 'ci.just'

# Module (namespaced) — house style requires the explicit path
mod deploy '.justfiles/deploy.just'
# Usage: just deploy::production
```

## Useful Functions

| Function | Purpose |
|----------|---------|
| `os()` | Current OS (`linux`, `macos`, `windows`) |
| `arch()` | CPU architecture (`x86_64`, `aarch64`) |
| `env_var_or_default('KEY', 'default')` | Env var with fallback (house style) |
| `invocation_directory()` | Directory where `just` was called from |
| `justfile_directory()` | Directory containing the justfile |
| `source_directory()` | Directory of the current file (use in modules) |
| `join(a, b)` | Join path components |
| `parent_directory(path)` | Parent of path |
| `file_name(path)` | Filename component |
| `without_extension(path)` | Remove file extension |
| `uppercase(s)` / `lowercase(s)` | Case conversion |
| `replace(s, from, to)` | String replacement |
| `trim(s)` | Trim whitespace |
| `quote(s)` | Shell-quote a string |
| `sha256_file(path)` | SHA-256 hash of a file |
| `shell(cmd, args...)` | Execute command, capture output |

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
