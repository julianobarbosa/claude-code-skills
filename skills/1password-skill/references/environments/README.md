# Developer Environments Reference

## Overview

1Password Developer Environments provide a dedicated location to store, organize, and manage project secrets as environment variables. This reference covers both the native GUI feature and CLI tools.

## Feature Status

| Feature | GUI Support | CLI Support |
|---------|-------------|-------------|
| Create environment | Yes | `op-env-create.ts` |
| Update environment | Yes | `op-env-update.ts` |
| Delete environment | Yes | `op-env-delete.ts` |
| Show environment | Yes | `op-env-show.ts` |
| List environments | Yes | `op-env-list.ts` |
| Export to .env | Yes | `op-env-export.ts` |
| Mount .env file | Yes (beta) | No |
| AWS Secrets Manager sync | Yes (beta) | No |

## CLI Tools

Tools are written in TypeScript and require [Bun](https://bun.sh) runtime.

### Setup

```bash
# Navigate to tools directory
cd tools

# Run any tool
bun run src/op-env-list.ts --help
```

### Available Tools

| Tool | Description |
|------|-------------|
| `op-env-create.ts` | Create new environment item |
| `op-env-update.ts` | Update existing environment |
| `op-env-delete.ts` | Delete environment item |
| `op-env-show.ts` | Display environment details |
| `op-env-list.ts` | List all environment items |
| `op-env-export.ts` | Export to .env format |

## Quick Start

### Create Environment

```bash
cd tools

# From inline variables
bun run src/op-env-create.ts my-app-dev Personal \
    API_KEY=secret123 \
    DB_HOST=localhost \
    DB_PORT=5432

# From .env file
bun run src/op-env-create.ts my-app-prod Production \
    --from-file .env.production
```

### Update Environment

```bash
# Update single variable
bun run src/op-env-update.ts my-app-dev Personal API_KEY=new-key

# Merge from file
bun run src/op-env-update.ts my-app-dev Personal --from-file .env.local

# Remove variables
bun run src/op-env-update.ts my-app-dev Personal --remove OLD_KEY,DEPRECATED
```

### View & Export

```bash
# List all environments
bun run src/op-env-list.ts

# Show details (masked)
bun run src/op-env-show.ts my-app-dev Personal

# Show with values
bun run src/op-env-show.ts my-app-dev Personal --reveal

# Export to .env
bun run src/op-env-export.ts my-app-dev Personal > .env

# Export as template
bun run src/op-env-export.ts my-app-dev Personal --format op-refs > .env.tpl
```

### Delete Environment

```bash
# Interactive
bun run src/op-env-delete.ts old-app Personal

# Force delete
bun run src/op-env-delete.ts old-app Personal --force

# Archive instead
bun run src/op-env-delete.ts old-app Personal --archive
```

## Storage Model

CLI tools store environments as API Credential items with:
- **Category:** API Credential
- **Tags:** `environment` (configurable)
- **Section:** `variables` (contains all env vars)
- **Field Type:** CONCEALED (for all values)

### Secret Reference Format

```
op://<vault>/<environment-name>/variables/<key>
```

Example:
```
op://Personal/my-app-dev/variables/API_KEY
```

## Integration Patterns

### With op run

```bash
# Create template
bun run src/op-env-export.ts my-app Production --format op-refs > .env.tpl

# Run command with injected secrets
op run --env-file .env.tpl -- ./deploy.sh
```

### With op inject

```bash
# Create template
bun run src/op-env-export.ts my-app Production --format op-refs > config.tpl

# Inject secrets into file
op inject -i config.tpl -o config.env
```

### In CI/CD

```yaml
# GitHub Actions example
- name: Load secrets
  run: |
    bun run src/op-env-export.ts ci-secrets CI-CD > .env
  env:
    OP_SERVICE_ACCOUNT_TOKEN: ${{ secrets.OP_SERVICE_ACCOUNT_TOKEN }}
```

## Best Practices

1. **Naming Convention:** Use `project-environment` format (e.g., `myapp-dev`, `myapp-prod`)
2. **Tagging:** Always use `environment` tag for discoverability
3. **Vault Organization:** Separate vaults per environment or team
4. **Access Control:** Use 1Password groups for team access
5. **Templates:** Use `--format op-refs` for CI/CD pipelines

## Limitations

1. **GUI-Only Features:**
   - Local .env file mounting (requires desktop app)
   - AWS Secrets Manager sync

2. **CLI Workarounds:**
   - Tools use API Credential category (not native Environment type)
   - No direct mapping to GUI Environments view
   - Manual sync between GUI environments and CLI items

## Related Documentation

- [inventory.md](./inventory.md) - Current environments inventory
- [cli-commands.md](../cli-commands.md) - Full CLI reference
- [1Password Environments Docs](https://developer.1password.com/docs/environments)
