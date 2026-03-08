# Justfile Patterns by Project Type

## Terraform / Infrastructure

```just
set dotenv-load
set shell := ["bash", "-euco", "pipefail"]

[private]
default:
    @just --list --unsorted

# Initialize Terraform with backend config
init:
    terraform init \
        -backend-config="subscription_id=$TF_VAR_BACKEND_SUBSCRIPTION_ID" \
        -backend-config="resource_group_name=$TF_VAR_BACKEND_RESOURCE_GROUP_NAME" \
        -backend-config="storage_account_name=$TF_VAR_BACKEND_STORAGE_ACCOUNT_NAME" \
        -backend-config="container_name=$TF_VAR_BACKEND_CONTAINER_NAME" \
        -backend-config="key=$TF_VAR_BACKEND_KEY"

# Reconfigure Terraform backend
reconfigure:
    terraform init \
        -reconfigure \
        -backend-config="subscription_id=$TF_VAR_BACKEND_SUBSCRIPTION_ID" \
        -backend-config="resource_group_name=$TF_VAR_BACKEND_RESOURCE_GROUP_NAME" \
        -backend-config="storage_account_name=$TF_VAR_BACKEND_STORAGE_ACCOUNT_NAME" \
        -backend-config="container_name=$TF_VAR_BACKEND_CONTAINER_NAME" \
        -backend-config="key=$TF_VAR_BACKEND_KEY"

# Validate Terraform configuration
validate:
    cd terraform && terraform validate

# Format Terraform files
fmt:
    terraform fmt -recursive

# Generate and review Terraform plan
plan: validate
    terraform plan

# Apply Terraform changes
apply:
    terraform apply

# Refresh Terraform state
refresh: validate
    terraform plan --refresh-only

# Show Terraform outputs
outputs:
    terraform output

# Destroy Terraform resources
[confirm("Are you sure you want to destroy resources?")]
destroy:
    terraform destroy

# Recreate a specific resource
recreate resource:
    terraform apply -replace "{{resource}}"

# Run Checkov security scan
checkov:
    checkov --directory .
```

## Go Project

```just
set shell := ["bash", "-euco", "pipefail"]

version := `git describe --tags --always --dirty 2>/dev/null || echo "dev"`
ldflags := "-ldflags \"-X main.version=" + version + "\""

[private]
default:
    @just --list

# Build the binary
build:
    go build {{ldflags}} -o bin/app ./cmd/app

# Run all tests
test:
    go test -v -race ./...

# Run linter
lint:
    golangci-lint run

# Format code
fmt:
    go fmt ./...
    goimports -w .

# Clean build artifacts
clean:
    rm -rf bin/ dist/

# Build and test
all: fmt lint test build
```

## Python Project

```just
set dotenv-load
set shell := ["bash", "-euco", "pipefail"]

[private]
default:
    @just --list

# Install dependencies
install:
    uv sync

# Run tests
test *args:
    uv run pytest -v {{args}}

# Run linter
lint:
    uv run ruff check .

# Format code
fmt:
    uv run ruff format .

# Type check
typecheck:
    uv run mypy src/

# Clean caches
clean:
    rm -rf .pytest_cache .ruff_cache __pycache__ .mypy_cache dist/
```

## Docker / Container

```just
image := "ghcr.io/user/app"
tag := `git describe --tags --always --dirty 2>/dev/null || echo "latest"`

# Build Docker image
docker-build:
    docker build -t {{image}}:{{tag}} -t {{image}}:latest .

# Push Docker image
docker-push:
    docker push {{image}}:{{tag}}
    docker push {{image}}:latest

# Build multi-arch image
docker-buildx:
    docker buildx build \
        --platform linux/amd64,linux/arm64 \
        --tag {{image}}:{{tag}} \
        --tag {{image}}:latest \
        --push .
```

## Azure / Bastion / SSH Tunneling

```just
set dotenv-load

vm_ip := env('VM_IP', '10.0.2.4')
vm_port := env('VM_PORT', '50022')

# Create SSH tunnel via Azure Bastion
tunnel:
    az network bastion tunnel \
        --name "$ARM_BASTION_NAME" \
        --resource-group "$ARM_RESOURCE_GROUP" \
        --target-ip-address {{vm_ip}} \
        --resource-port 22 \
        --port {{vm_port}} &

# Kill tunnel process
kill-tunnel:
    #!/usr/bin/env bash
    if [ -f .tunnel.pid ]; then
        kill "$(cat .tunnel.pid)" && rm -f .tunnel.pid
        echo "Tunnel killed"
    else
        echo "No tunnel process found"
    fi
```

## Ansible

```just
set dotenv-load

playbook := "local.yml"
inventory := "inventory/hosts.ini"

# Run Ansible playbook
play *args:
    ansible-playbook -i {{inventory}} {{playbook}} {{args}}

# Dry run (check mode)
check:
    ansible-playbook -i {{inventory}} {{playbook}} --check --diff

# List hosts
hosts:
    ansible-inventory -i {{inventory}} --list
```

## Common Patterns

### Grouped Recipes

```just
[group("ci")]
ci-lint:
    ...

[group("ci")]
ci-test:
    ...

[group("deploy")]
deploy-staging:
    ...

[group("deploy")]
deploy-production:
    ...
```

### Confirmation for Dangerous Operations

```just
[confirm("This will destroy ALL resources. Continue?")]
destroy:
    terraform destroy

[confirm("Deploy to production?")]
deploy-prod:
    ./deploy.sh production
```

### Hidden Helper Recipes

```just
[private]
_ensure-tools:
    #!/usr/bin/env bash
    for cmd in terraform az jq; do
        command -v "$cmd" >/dev/null || { echo "Missing: $cmd"; exit 1; }
    done

plan: _ensure-tools
    terraform plan
```
