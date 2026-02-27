# 1Password Developer Environments Inventory

## Overview

This document tracks all Developer Environments configured in 1Password under the Barbosa account.

**Account:** Barbosa
**Last Updated:** 2026-02-19
**Vault:** hypera (service account access)

## Current Environments

| # | Environment Name | Description | Vault | Status | Created |
|---|-----------------|-------------|-------|--------|---------|
| 1 | Azure OpenAI-finops | Azure OpenAI FinOps configuration | hypera | Active | 2026-02-19 |
| 2 | devops-team-pim | DevOps Team PIM access credentials | hypera | Active | 2026-02-19 |
| 3 | .dotfiles | Dotfiles environment variables | hypera | Active | 2026-02-19 |
| 4 | hypera-github-python-devops | GitHub credentials for Python DevOps projects | hypera | Active | 2026-02-19 |
| 5 | hypera-azure-rg-hypera-cafehyna-web | Azure Resource Group - Cafehyna Web (Production) | hypera | Active | 2026-02-19 |
| 6 | devops-team-azure-quota-automation | DevOps team Azure quota automation credentials | hypera | Active | 2026-02-19 |
| 7 | hypera-azure-rg-hypera-cafehyna-web-dev | Azure Resource Group - Cafehyna Web Dev | hypera | Active | 2026-02-19 |
| 8 | hypera | General Hypera environment credentials | hypera | Active | 2026-02-19 |
| 9 | rg-hypera-aks-python-infra-dev | AKS Python infrastructure dev credentials | hypera | Active | 2026-02-19 |
| 10 | hypera-azure-devops-team-az-cli-pim | Azure DevOps Team - AZ CLI PIM credentials | hypera | Active | 2026-02-19 |
| 11 | repos-github-zsh | GitHub credentials for ZSH repository | hypera | Active | 2026-02-19 |

## Environment Categories

### Azure Environments
- `hypera-azure-rg-hypera-cafehyna-web-dev` - Development Azure resources
- `hypera-azure-rg-hypera-cafehyna-web` - Production Azure resources
- `hypera-azure-devops-team-az-cli-pim` - Azure CLI with PIM integration
- `Azure OpenAI-finops` - Azure OpenAI service configuration
- `devops-team-azure-quota-automation` - Azure quota automation

### Kubernetes / Infrastructure
- `rg-hypera-aks-python-infra-dev` - AKS Python infrastructure dev

### GitHub Environments
- `hypera-github-python-devops` - Python DevOps automation
- `repos-github-zsh` - ZSH dotfiles repository

### Team Environments
- `devops-team-pim` - DevOps team PIM credentials
- `hypera-azure-devops-team-az-cli-pim` - Azure DevOps AZ CLI PIM

### General
- `hypera` - General infrastructure credentials
- `.dotfiles` - Dotfiles configuration
- `devops-team-azure-quota-automation` - Quota automation

## CLI Management

All environments were created via CLI using `op item create` with:
- **Category:** API Credential
- **Tag:** `environment`
- **Vault:** `hypera`
- **Initial variable:** `PLACEHOLDER=initialized` (replace with real values)

### Populate Variables

Add real variables to replace the placeholder:
```bash
# Edit environment to add real variables
op item edit "<env-name>" --vault hypera \
  variables.MY_KEY[concealed]=my-value \
  variables.PLACEHOLDER[delete]
```

### Access via CLI Tools

```bash
cd ~/.claude/skills/1password-skill/tools
# OR
cd .claude/skills/1password-skill/tools

# List all environments
bun run list --vault hypera

# Show environment details
bun run show "hypera" hypera

# Export to .env file
bun run export "hypera-azure-rg-hypera-cafehyna-web-dev" hypera > .env

# Create op:// reference
op read "op://hypera/<env-name>/variables/<KEY>"
```

### Direct CLI Access

```bash
# Read specific variable
op read "op://hypera/hypera/variables/API_KEY"

# Use with op run
op run --env-file .env.tpl -- ./deploy.sh

# List all environment items
op item list --vault hypera --tags environment --format json | jq '.[].title'
```

## Secret References Format

All variables use the format:
```
op://hypera/<env-name>/variables/<KEY>
```

Examples:
- `op://hypera/hypera/variables/API_KEY`
- `op://hypera/devops-team-pim/variables/AZURE_CLIENT_ID`
- `op://hypera/Azure OpenAI-finops/variables/OPENAI_API_KEY`

## Notes

- All environments created 2026-02-19 via CLI (service account access to `hypera` vault)
- Initial `PLACEHOLDER=initialized` variable should be replaced with real values
- Developer Environments is a beta feature in 1Password (GUI-native type different from CLI API Credential items)
- CLI items use `API Credential` category + `environment` tag as the programmatic equivalent
- Use `op-env-update` to add variables once values are known
