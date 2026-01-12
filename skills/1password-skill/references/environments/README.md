# Developer Environments Reference

## Overview

1Password Developer Environments provide a dedicated location to store, organize, and manage project secrets as environment variables. This reference covers both the native GUI feature and CLI workarounds.

## Feature Status

| Feature | GUI Support | CLI Support |
|---------|-------------|-------------|
| Create environment | Yes | Via tools* |
| Update environment | Yes | Via tools* |
| Delete environment | Yes | Via tools* |
| List environments | Yes | `op env ls`** |
| Export to .env | Yes | Via tools* |
| Mount .env file | Yes (beta) | No |
| AWS Secrets Manager sync | Yes (beta) | No |

*Using `op item` commands with API Credential category
**Only lists env vars with op:// references in shell

## CLI Tools

The tools in `../tools/` provide environment management capabilities:

| Tool | Description |
|------|-------------|
| `op-env-create.sh` | Create new environment item |
| `op-env-update.sh` | Update existing environment |
| `op-env-delete.sh` | Delete environment item |
| `op-env-show.sh` | Display environment details |
| `op-env-list.sh` | List all environment items |
| `op-env-export.sh` | Export to .env format |

## Quick Start

### Create Environment

```bash
# From inline variables
./tools/op-env-create.sh my-app-dev Development \
    API_KEY=secret123 \
    DB_HOST=localhost \
    DB_PORT=5432

# From .env file
./tools/op-env-create.sh my-app-prod Production \
    --from-file .env.production
```

### Update Environment

```bash
# Update single variable
./tools/op-env-update.sh my-app-dev Development API_KEY=new-key

# Merge from file
./tools/op-env-update.sh my-app-dev Development --from-file .env.local

# Remove variables
./tools/op-env-update.sh my-app-dev Development --remove OLD_KEY,DEPRECATED
```

### View & Export

```bash
# List all environments
./tools/op-env-list.sh

# Show details (masked)
./tools/op-env-show.sh my-app-dev Development

# Show with values
./tools/op-env-show.sh my-app-dev Development --reveal

# Export to .env
./tools/op-env-export.sh my-app-dev Development > .env

# Export as template
./tools/op-env-export.sh my-app-dev Development --format op-refs > .env.tpl
```

### Delete Environment

```bash
# Interactive
./tools/op-env-delete.sh old-app Development

# Force delete
./tools/op-env-delete.sh old-app Development --force

# Archive instead
./tools/op-env-delete.sh old-app Development --archive
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
op://Development/my-app-dev/variables/API_KEY
```

## Integration Patterns

### With op run

```bash
# Create template
./tools/op-env-export.sh my-app Production --format op-refs > .env.tpl

# Run command with injected secrets
op run --env-file .env.tpl -- ./deploy.sh
```

### With op inject

```bash
# Create template
./tools/op-env-export.sh my-app Production --format op-refs > config.tpl

# Inject secrets into file
op inject -i config.tpl -o config.env
```

### In CI/CD

```yaml
# GitHub Actions example
- name: Load secrets
  run: |
    ./tools/op-env-export.sh ci-secrets CI-CD > .env
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
   - Visual environment management

2. **CLI Workarounds:**
   - Tools use API Credential category (not native Environment type)
   - No direct mapping to GUI Environments view
   - Manual sync between GUI environments and CLI items

## Related Documentation

- [inventory.md](./inventory.md) - Current environments inventory
- [cli-commands.md](../cli-commands.md) - Full CLI reference
- [1Password Environments Docs](https://developer.1password.com/docs/environments)
