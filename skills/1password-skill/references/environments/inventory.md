# 1Password Developer Environments Inventory

## Overview

This document tracks all Developer Environments configured in 1Password under the Barbosa account.

**Account:** Barbosa
**Last Updated:** 2026-01-12

## Current Environments

| # | Environment Name | Description | Status |
|---|-----------------|-------------|--------|
| 1 | hypera-azure-rg-hypera-cafehyna-web-dev | Azure Resource Group - Cafehyna Web Dev | Active |
| 2 | hypera-azure-devops-team-az-cli-pim | Azure DevOps Team - AZ CLI PIM credentials | Active |
| 3 | devops-team-pim | DevOps Team PIM access credentials | Active |
| 4 | hypera-github-python-devops | GitHub credentials for Python DevOps projects | Active |
| 5 | hypera-azure-rg-hypera-cafehyna-web | Azure Resource Group - Cafehyna Web (Production) | Active |
| 6 | repos-github-zsh | GitHub credentials for ZSH repository | Active |
| 7 | hypera | General Hypera environment credentials | Active |
| 8 | Azure OpenAI-finops | Azure OpenAI FinOps configuration | Active |

## Environment Categories

### Azure Environments
- `hypera-azure-rg-hypera-cafehyna-web-dev` - Development Azure resources
- `hypera-azure-rg-hypera-cafehyna-web` - Production Azure resources
- `hypera-azure-devops-team-az-cli-pim` - Azure CLI with PIM integration
- `Azure OpenAI-finops` - Azure OpenAI service configuration

### GitHub Environments
- `hypera-github-python-devops` - Python DevOps automation
- `repos-github-zsh` - ZSH dotfiles repository

### Team Environments
- `devops-team-pim` - DevOps team PIM credentials

### General
- `hypera` - General infrastructure credentials

## Usage Examples

### Access via GUI
1. Open 1Password Desktop App
2. Navigate to Developer > Environments
3. Click "View environment" on desired environment

### Access via CLI (using tools)

```bash
# List all environments
op-env-list.sh

# Show environment details
op-env-show.sh "hypera" "Barbosa"

# Export to .env file
op-env-export.sh "hypera-azure-rg-hypera-cafehyna-web-dev" "Barbosa" > .env

# Create op:// reference template
op-env-export.sh "repos-github-zsh" "Barbosa" --format op-refs > .env.tpl
```

### Direct CLI Access

```bash
# Read specific variable
op read "op://Barbosa/hypera/variables/API_KEY"

# Use with op run
op run --env-file .env.tpl -- ./deploy.sh
```

## Notes

- Developer Environments is a beta feature in 1Password
- Environments are managed primarily through the desktop GUI
- CLI tools in this skill provide workaround for CRUD operations
- Use the `environment` tag to track environment items created via CLI
