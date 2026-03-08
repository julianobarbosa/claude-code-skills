# Makefile to Justfile Migration Guide

## Syntax Translation Table

| Make | Just | Notes |
|---|---|---|
| `.PHONY: target` | *(not needed)* | just doesn't track files |
| `default: help` | `default` recipe or `[private] default:` | First recipe is default |
| `@command` | `@command` | Same — suppress echo |
| `$(VAR)` or `${VAR}` | `{{var}}` | Variable interpolation |
| `$$VAR` | `$VAR` | Shell variable (no double-dollar escape) |
| `VAR := value` | `var := "value"` | Strings must be quoted |
| `VAR ?= default` | `var := env('VAR', 'default')` | Env fallback pattern |
| `$(shell cmd)` | `` `cmd` `` | Backtick evaluation |
| `export VAR` | `export var := "value"` | Or `set export` globally |
| `target: dep1 dep2` | `target: dep1 dep2` | Same syntax |
| `.DEFAULT_GOAL := help` | Put default recipe first | Or use `[default]` attribute |
| `include file.mk` | `import 'file.just'` | Import syntax |
| Tab indentation | Spaces or tabs | Consistent within file |
| `ifeq / endif` | `if expr { } else { }` | Inline conditionals |
| `$(MAKEFILE_LIST)` | *(not needed)* | `just --list` is built-in |

## Key Differences to Remember

### 1. No Double-Dollar Escaping

In Make, `$$` is needed to pass a literal `$` to the shell. In just, use `$` directly:

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

### 2. Each Line is a Separate Shell

Like make, each line runs in its own shell. But just makes it easy to use shebang
recipes for multi-line scripts:

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
# Just — shebang recipe (runs as single script)
target:
    #!/usr/bin/env bash
    if [ -f file ]; then
        echo "found"
    else
        echo "missing"
    fi
```

### 3. String Quoting

Just variables must be quoted strings. Make variables are unquoted:

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

### 4. Self-Documenting Help

Make requires a grep/awk hack. Just has it built in:

```makefile
# Make
help: ## Show help
    @grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
      awk 'BEGIN {FS = ":.*?## "}; {printf "%-20s %s\n", $$1, $$2}'
```

```just
# Just — comments above recipes become descriptions automatically
[private]
default:
    @just --list --unsorted

# Show help information
help:
    @just --list
```

### 5. Environment Variables

Make uses `$$VAR` in recipes. Just uses `$VAR` directly and supports dotenv:

```makefile
# Make
init:
    @terraform init \
        -backend-config="subscription_id=$$TF_VAR_BACKEND_SUBSCRIPTION_ID"
```

```just
# Just
set dotenv-load

init:
    terraform init \
        -backend-config="subscription_id=$TF_VAR_BACKEND_SUBSCRIPTION_ID"
```

### 6. Arguments

Make doesn't natively support recipe arguments. Just does:

```makefile
# Make — hacky workaround
recreate:
    @terraform apply -replace "azurerm_linux_virtual_machine.azxdev01"
```

```just
# Just — parameterized
recreate resource:
    terraform apply -replace "{{resource}}"

# Usage: just recreate azurerm_linux_virtual_machine.azxdev01
```

## Step-by-Step Migration Process

1. **Read the existing Makefile** — understand all targets, variables, and dependencies
2. **Create `justfile`** with `set dotenv-load` and `set shell` at the top
3. **Convert variables** — quote values, replace `$(shell ...)` with backticks
4. **Convert targets to recipes** — remove `.PHONY`, convert `$$` to `$`
5. **Add `[private] default:` recipe** — replaces `.DEFAULT_GOAL`
6. **Add comments above recipes** — they become `--list` descriptions
7. **Parameterize hardcoded values** — use recipe arguments where appropriate
8. **Add `[confirm]`** to destructive recipes (destroy, clean, etc.)
9. **Test each recipe** — run `just --dry-run <recipe>` to verify
10. **Remove Makefile** — once all recipes work correctly

## Coexistence Strategy

During migration, you can keep both files. Just won't conflict with make since
they use different filenames (`justfile` vs `Makefile`). Migrate one target at
a time and test before removing it from the Makefile.
