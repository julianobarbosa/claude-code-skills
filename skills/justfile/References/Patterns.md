# Justfile Patterns by Project Type

Recipe **content** for common stacks. These show *what recipes a domain needs* — drop them into the
appropriate `.justfiles/<concern>.just` module and apply the house conventions from `SKILL.md`
(three-line header, `_default` first, `env_var_or_default`, doc comments). Each complete example
below already carries the header so it passes `Tools/lint.ts`; the fragments under "Common Patterns"
are snippets to compose into a module.

## Terraform / Infrastructure (`.justfiles/infra.just`)

```just
#!/usr/bin/env just --justfile
set shell := ["bash", "-euo", "pipefail", "-c"]
set dotenv-load := true

# --- Recipes ---

# List recipes in this module
_default:
    @just --list --unsorted

# Initialize Terraform with backend config
init:
    terraform init \
        -backend-config="subscription_id=$TF_VAR_BACKEND_SUBSCRIPTION_ID" \
        -backend-config="resource_group_name=$TF_VAR_BACKEND_RESOURCE_GROUP_NAME" \
        -backend-config="storage_account_name=$TF_VAR_BACKEND_STORAGE_ACCOUNT_NAME" \
        -backend-config="container_name=$TF_VAR_BACKEND_CONTAINER_NAME" \
        -backend-config="key=$TF_VAR_BACKEND_KEY"

# Validate Terraform configuration
validate:
    terraform validate

# Format Terraform files
fmt:
    terraform fmt -recursive

# Generate and review a Terraform plan
plan: validate
    terraform plan

# Apply Terraform changes
apply:
    terraform apply

# Show Terraform outputs
outputs:
    terraform output

# Recreate a specific resource
# resource - the Terraform address to replace
recreate resource:
    terraform apply -replace "{{resource}}"

# Run Checkov security scan
checkov:
    checkov --directory .

# Destroy Terraform resources — DESTRUCTIVE, prompts for confirmation
[confirm("Are you sure you want to destroy resources?")]
destroy:
    terraform destroy
```

## Go Project (`.justfiles/dev.just`)

```just
#!/usr/bin/env just --justfile
set shell := ["bash", "-euo", "pipefail", "-c"]
set dotenv-load := false

# --- Variables ---
version := `git describe --tags --always --dirty 2>/dev/null || echo "dev"`
ldflags := "-ldflags \"-X main.version=" + version + "\""

# --- Recipes ---

# List recipes in this module
_default:
    @just --list --unsorted

# Build the binary
build:
    go build {{ldflags}} -o bin/app ./cmd/app

# Run all tests
test:
    go test -v -race ./...

# Run linters
lint:
    golangci-lint run

# Format code
fmt:
    go fmt ./...
    goimports -w .

# Remove build artifacts
clean:
    rm -rf bin/ dist/
```

## Python Project (`.justfiles/dev.just`)

```just
#!/usr/bin/env just --justfile
set shell := ["bash", "-euo", "pipefail", "-c"]
set dotenv-load := true

# --- Recipes ---

# List recipes in this module
_default:
    @just --list --unsorted

# Install dependencies
install:
    uv sync

# Run tests
# args - extra pytest arguments (default: "")
test *args="":
    uv run pytest -v {{args}}

# Run linters
lint:
    uv run ruff check .

# Format code
fmt:
    uv run ruff format .

# Type check
typecheck:
    uv run mypy src/

# Remove caches and build output
clean:
    rm -rf .pytest_cache .ruff_cache __pycache__ .mypy_cache dist/
```

## Docker / Container (`.justfiles/docker.just`)

```just
#!/usr/bin/env just --justfile
set shell := ["bash", "-euo", "pipefail", "-c"]
set dotenv-load := false

# --- Variables ---
image := env_var_or_default("IMAGE", "ghcr.io/user/app")
tag := `git describe --tags --always --dirty 2>/dev/null || echo "latest"`

# --- Recipes ---

# List recipes in this module
_default:
    @just --list --unsorted

# Build the image
build:
    docker build -t {{image}}:{{tag}} -t {{image}}:latest .

# Push the image
push:
    docker push {{image}}:{{tag}}
    docker push {{image}}:latest

# Build a multi-arch image and push
buildx:
    docker buildx build \
        --platform linux/amd64,linux/arm64 \
        --tag {{image}}:{{tag}} \
        --tag {{image}}:latest \
        --push .
```

## Azure / Bastion SSH Tunneling (`.justfiles/infra.just`)

```just
#!/usr/bin/env just --justfile
set shell := ["bash", "-euo", "pipefail", "-c"]
set dotenv-load := true

# --- Variables ---
vm_ip := env_var_or_default("VM_IP", "10.0.2.4")
vm_port := env_var_or_default("VM_PORT", "50022")

# --- Recipes ---

# List recipes in this module
_default:
    @just --list --unsorted

# Open an SSH tunnel via Azure Bastion
tunnel:
    az network bastion tunnel \
        --name "$ARM_BASTION_NAME" \
        --resource-group "$ARM_RESOURCE_GROUP" \
        --target-ip-address {{vm_ip}} \
        --resource-port 22 \
        --port {{vm_port}} &

# Kill the tunnel process
kill-tunnel:
    #!/usr/bin/env bash
    if [ -f .tunnel.pid ]; then
        kill "$(cat .tunnel.pid)" && rm -f .tunnel.pid
        echo "Tunnel killed"
    else
        echo "No tunnel process found"
    fi
```

## Ansible (`.justfiles/infra.just`)

```just
#!/usr/bin/env just --justfile
set shell := ["bash", "-euo", "pipefail", "-c"]
set dotenv-load := true

# --- Variables ---
playbook := env_var_or_default("PLAYBOOK", "local.yml")
inventory := env_var_or_default("INVENTORY", "inventory/hosts.ini")

# --- Recipes ---

# List recipes in this module
_default:
    @just --list --unsorted

# Run the playbook
# args - extra ansible-playbook arguments (default: "")
play *args="":
    ansible-playbook -i {{inventory}} {{playbook}} {{args}}

# Dry run (check mode)
check:
    ansible-playbook -i {{inventory}} {{playbook}} --check --diff

# List inventory hosts
hosts:
    ansible-inventory -i {{inventory}} --list
```

## Common Patterns (snippets to compose)

### Grouped recipes

```just
[group("ci")]
ci-lint:
    ...

[group("deploy")]
deploy-production:
    ...
```

### Confirmation for dangerous operations

```just
# Destroy everything — DESTRUCTIVE, prompts for confirmation
[confirm("This will destroy ALL resources. Continue?")]
destroy:
    terraform destroy
```

### Hidden helper recipes

```just
# Ensure required tools are installed
[private]
_ensure-tools:
    #!/usr/bin/env bash
    for cmd in terraform az jq; do
        command -v "$cmd" >/dev/null || { echo "Missing: $cmd"; exit 1; }
    done

# Plan, guarded by the tool check
plan: _ensure-tools
    terraform plan
```
