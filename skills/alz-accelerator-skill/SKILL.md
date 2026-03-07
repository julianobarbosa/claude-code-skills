---
name: alz-accelerator-skill
description: Deploy Azure Landing Zones using the ALZ Accelerator with AVM (Azure Verified Modules). Use this skill whenever the user mentions Azure Landing Zones, ALZ, Azure landing zone accelerator, AVM modules for landing zones, deploying management groups, hub-and-spoke networking, Virtual WAN, platform landing zones, or asks about Bicep vs Terraform for Azure infrastructure. Also trigger when the user wants to bootstrap CI/CD for Azure platform deployment, set up management groups hierarchy, or deploy connectivity/identity/management platform subscriptions.
---

# Azure Landing Zones Accelerator Skill

Deploy Azure Landing Zones using the ALZ Accelerator with Azure Verified Modules (AVM). This skill captures the recommended workflow, decision framework, and best practices from the ALZ core team.

## Key Concepts

**AVM (Azure Verified Modules):** An infrastructure-as-code standard for deploying Azure resources following best practices. AVM has resource modules (single resources) and pattern modules (complex architectural patterns composed from resource modules). AVM is the only recommended way to deploy Azure Landing Zones infrastructure.

**ALZ Accelerator:** A tool that bootstraps the entire Azure Landing Zone deployment including CI/CD pipelines, version control, and infrastructure configuration. It uses AVM modules under the hood.

**Deployment Stacks (Bicep):** Used by the Bicep accelerator to handle resource lifecycle management, eliminating the pain of manually managing policy assignments and resource deletions.

## Decision Framework: Bicep vs Terraform

Guide the user through this decision before proceeding with deployment.

### When to Choose Terraform

- Team already has Terraform expertise
- Multi-cloud strategy (AWS, GCP, Azure) — avoids learning two IaC languages
- Terraform ALZ modules are more mature (released ~early 2025) with full configuration via tfvars
- Need for state-based drift detection

### When to Choose Bicep

- Azure-only organization with no multi-cloud plans
- Team familiar with ARM templates or Azure-native tooling
- No state file to manage (pro and con — simpler ops but less drift visibility)
- Microsoft ARM/Bicep product groups recommend Bicep for Azure-only shops
- Bicep ALZ released ~Feb 2026 with full AVM support, deployment stacks, and customizable modules

### Neutral Position

- Both use AVM modules — same underlying resource definitions
- Both are supported by the accelerator with identical bootstrapping UX
- The gap between them is closing rapidly in 2026
- **Default recommendation:** Match the team's existing skills

## Accelerator Deployment Workflow

### Prerequisites

1. Install the ALZ PowerShell module:

   ```powershell
   Install-Module -Name ALZ
   ```

2. Ensure you have:
   - Azure CLI or PowerShell authenticated
   - GitHub PAT or Azure DevOps PAT (depending on VCS choice)
   - At least 4 platform subscriptions: Management, Connectivity, Identity, Security
   - A bootstrap subscription for state storage and identities

### Step 1: Launch the Accelerator

```powershell
Deploy-Accelerator
```

The accelerator runs interactively with guided prompts. No parameters are required (as of the latest release).

### Step 2: Software Checks

The accelerator validates required software is installed. Address any missing dependencies before proceeding.

### Step 3: Choose Cache Location

Select where to store temporary files during setup. The default is usually fine.

### Step 4: IaC Language Selection

Choose between:

- **Terraform** — More mature configuration, everything via tfvars
- **Bicep** — Azure-native, no state file, deployment stacks for lifecycle management

### Step 5: Version Control & CI/CD Platform

Choose from:

- **GitHub** (default, recommended)
- **Azure DevOps**
- **Local filesystem** (for custom bootstrapping)

### Step 6: Connectivity Scenario

Select the networking topology:

- **Hub and Spoke** — Traditional hub-spoke with VNet peering (most common)
- **Virtual WAN** — Azure Virtual WAN managed hub
- **Multi-region** variants of the above

### Step 7: Interactive Configuration

The accelerator queries Azure for your existing resources and presents selection prompts:

1. **Bootstrap region** — Where to deploy state storage and identities
2. **Root management group** — Parent MG for the ALZ hierarchy
3. **Platform subscriptions:**
   - Management subscription (Log Analytics, monitoring)
   - Identity subscription (Active Directory, DNS)
   - Connectivity subscription (Hub VNet, Firewall, VPN/ER gateways)
   - Security subscription (Sentinel, Defender)
4. **Bootstrap subscription** — For Terraform state storage and managed identities

### Step 8: Naming Convention

Accept defaults or customize resource naming patterns for the bootstrap resources.

### Step 9: Runner Configuration

Choose between:

- **Self-hosted runners** — Recommended for private networking
- **Microsoft-hosted runners** — Simpler but requires public endpoints

If self-hosted, choose whether to enable **private networking** (storage accounts not publicly accessible).

### Step 10: Authentication

Provide:

- **Personal Access Token** — GitHub PAT or Azure DevOps PAT (stored as environment variable, never in config files)
- **GitHub/ADO organization name**
- **Apply approver** — Username that approves plan-to-apply stage

### Step 11: Review & Open in IDE

The accelerator generates configuration files and opens them in VS Code. Review and update:

1. **Platform landing zone config:**
   - Primary and secondary deployment regions (e.g., UK South, UK West)
   - Defender email security contact
2. **Sensitive values** are stored as environment variables in the current terminal session, not in plain text files

### Step 12: Bootstrap Deployment

Confirm the configuration is complete. The accelerator bootstraps:

- State storage (Terraform) or deployment stack (Bicep)
- Managed identities for CI/CD
- GitHub repos/Azure DevOps projects with pipelines
- Branch policies and approvals

## Post-Deployment

After the accelerator completes:

1. **CI/CD pipelines** are created in your chosen VCS
2. **Plan/What-If stage** runs automatically on PR
3. **Apply/Deploy stage** requires approval from the configured approver
4. **Subsequent changes** are made through the configuration files and pushed through the pipeline

## AVM Module Architecture

The ALZ deployment uses these key AVM pattern modules:

| Module                   | Purpose                                                                                 |
| ------------------------ | --------------------------------------------------------------------------------------- |
| Management Groups        | Hierarchy: Tenant Root → Platform (Mgmt, Conn, Identity) → Landing Zones (Corp, Online) |
| Management               | Log Analytics workspace, Automation Account, monitoring                                 |
| Connectivity (Hub-Spoke) | Hub VNet, Azure Firewall, VPN/ER Gateways, DNS                                          |
| Connectivity (vWAN)      | Virtual WAN, Virtual Hubs, routing                                                      |
| Identity                 | DNS zones, domain controllers networking                                                |
| Policy                   | Azure Policy assignments, custom policy definitions                                     |

You can use these modules standalone (compose them yourself) or through the accelerator (recommended path).

## Rules

1. **Always use AVM modules** — Never deploy ALZ resources with raw azurerm/azapi resources when an AVM module exists
2. **Use the accelerator** — Don't manually compose the modules unless you have a specific reason; the accelerator handles bootstrapping, CI/CD, and configuration
3. **Match team skills** — Don't push Terraform on a Bicep team or vice versa
4. **Private networking for production** — Use self-hosted runners with private networking for any production deployment
5. **Never store PATs in config files** — The accelerator uses environment variables for sensitive values; maintain this pattern
6. **Four platform subscriptions minimum** — Management, Connectivity, Identity, Security — don't collapse them
7. **Plan before apply** — Always review the plan/what-if output before approving deployment
8. **Customize via config, not module edits** — For Terraform, all customization goes through tfvars. For Bicep, you can edit modules directly but prefer the config approach when possible

## Troubleshooting

| Issue                              | Resolution                                                                                                            |
| ---------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| Deployment stacks bugs (Bicep)     | Known limitations — what-if not fully supported. Check [ALZ GitHub issues](https://github.com/Azure/ALZ-Bicep/issues) |
| Policy assignment conflicts        | Use the separated custom vs default policy structure (Bicep 2026 release)                                             |
| State file management (Terraform)  | State is bootstrapped automatically; don't manually modify the backend config                                         |
| Upgrade pain from old ALZ versions | The new Bicep release decouples your customizations from upstream modules                                             |

## Resources

- Questions form: `aka.ms/alz/quests`
- ALZ documentation: `aka.ms/alz`
- AVM registry: `aka.ms/avm`
- ALZ Accelerator docs: `aka.ms/alz/accelerator`
