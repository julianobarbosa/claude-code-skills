# Makefile → Justfile Migration Guide

Lookup table and per-feature notes for converting a `Makefile`. The procedure is in
`Workflows/MigrateFromMake.md`; the target Justfile must follow the house conventions in `SKILL.md`.

## Syntax Translation Table

| Make | Just | Notes |
|------|------|-------|
| `.PHONY: target` | *(not needed)* | just doesn't track files |
| `default: help` / first target | `_default:` recipe | First recipe is the default; house style requires `_default` |
| `@command` | `@command` | Same — suppress echo |
| `$(VAR)` or `${VAR}` | `{{var}}` | Variable interpolation |
| `$$VAR` | `$VAR` | Shell variable (no double-dollar escape) |
| `VAR := value` | `var := "value"` | Strings must be quoted |
| `VAR ?= default` | `var := env_var_or_default("VAR", "default")` | Env fallback (house style) |
| `$(shell cmd)` | `` `cmd` `` | Backtick evaluation (parse-time — see gotchas) |
| `export VAR` | `export var := "value"` | Or `set export` globally |
| `target: dep1 dep2` | `target: dep1 dep2` | Same syntax |
| `.DEFAULT_GOAL := help` | Put `_default` first | |
| `include file.mk` | `import 'file.just'` or `mod` | |
| Tab indentation | Spaces or tabs | Consistent within file (header pins shell) |
| `ifeq / endif` | `if expr { } else { }` | Inline conditionals |
| `$(MAKEFILE_LIST)` | *(not needed)* | `just --list` is built-in |

## Key Differences

### 1. No double-dollar escaping

In Make, `$$` passes a literal `$` to the shell. In just, use `$` directly:

```makefile
# Make
target:
    echo $$HOME
    for f in $$files; do echo $$f; done
```

```just
# Just
target:
    echo $HOME
    for f in $files; do echo $f; done
```

### 2. Each line is a separate shell

Like make, each line runs in its own shell — but just makes multi-line scripts easy via shebang
recipes:

```makefile
# Make — awkward line continuation
target:
    @if [ -f file ]; then \
        echo "found"; \
    else \
        echo "missing"; \
    fi
```

```just
# Just — shebang recipe (runs as a single script)
target:
    #!/usr/bin/env bash
    if [ -f file ]; then
        echo "found"
    else
        echo "missing"
    fi
```

### 3. String quoting

Just variables must be quoted strings; Make variables are unquoted:

```makefile
# Make
VERSION := 1.0.0
IMAGE := myapp
```

```just
# Just
version := "1.0.0"
image := "myapp"
```

### 4. Self-documenting help

Make needs a grep/awk hack; just has it built in. Comments above recipes become `--list`
descriptions:

```makefile
# Make
help: ## Show help
    @grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
      awk 'BEGIN {FS = ":.*?## "}; {printf "%-20s %s\n", $$1, $$2}'
```

```just
# Just
# List all available recipes
_default:
    @just --list --unsorted
```

### 5. Environment variables

Make uses `$$VAR` in recipes; just uses `$VAR` directly and supports dotenv via the house header
(`set dotenv-load := true`):

```makefile
# Make
init:
    @terraform init \
        -backend-config="subscription_id=$$TF_VAR_BACKEND_SUBSCRIPTION_ID"
```

```just
# Just (header already sets dotenv-load)
init:
    terraform init \
        -backend-config="subscription_id=$TF_VAR_BACKEND_SUBSCRIPTION_ID"
```

### 6. Arguments

Make doesn't natively support recipe arguments; just does:

```makefile
# Make — hacky workaround
recreate:
    @terraform apply -replace "azurerm_linux_virtual_machine.azxdev01"
```

```just
# Just — parameterized
# resource - the Terraform address to replace
recreate resource:
    terraform apply -replace "{{resource}}"

# Usage: just recreate azurerm_linux_virtual_machine.azxdev01
```

## Coexistence Strategy

During migration, keep both files — `Makefile` and `Justfile` don't conflict. Migrate one concern
at a time, verify each recipe with `just --dry-run <recipe>`, then remove the corresponding target
from the Makefile. Delete the Makefile only once every recipe works and `Tools/lint.ts` passes.
