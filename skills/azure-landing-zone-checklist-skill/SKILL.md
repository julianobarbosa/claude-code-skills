---
name: azure-landing-zone-checklist
description: >
  Fill out Microsoft Azure Landing Zone (ALZ) Accelerator checklists by interviewing the user,
  mapping their Azure subscriptions, integrating IP addressing documentation, and applying
  Microsoft Cloud Adoption Framework best practices. Produces a completed Excel checklist
  (.xlsx) ready for ALZ deployment. Use this skill whenever the user mentions Azure Landing Zone,
  ALZ checklist, landing zone accelerator, platform landing zone configuration, ALZ bootstrap,
  hub-and-spoke setup, Azure network topology planning, or wants to fill out any ALZ-related
  checklist or configuration file. Also trigger when the user uploads an Excel file that contains
  tabs like "Accelerator - Bootstrap", "Accelerator - Bicep", or "Accelerator - Terraform".
---

# Azure Landing Zone Checklist Skill

This skill guides you through filling out the Microsoft Azure Landing Zone (ALZ) Accelerator checklist — the spreadsheet that captures all decisions needed before deploying an ALZ using Bicep or Terraform via the ALZ Accelerator tool.

The goal is to produce a filled Excel checklist where every decision is justified, best practices are applied by default, and items requiring human input are clearly flagged for the user's attention.

## Why this matters

The ALZ Accelerator checklist is the single source of truth for a platform landing zone deployment. Getting it wrong means misconfigured networking, security gaps, or hours of rework. This skill ensures consistency by applying Microsoft's Cloud Adoption Framework (CAF) recommendations while respecting the user's existing infrastructure (IP ranges, subscriptions, naming conventions).

## Workflow

### Phase 1: Read the checklist

Read the uploaded `.xlsx` checklist using openpyxl to understand its structure. ALZ checklists typically have three tabs:

- **Accelerator - Bootstrap**: IaC type, VCS, subscriptions, naming, CI/CD settings
- **Accelerator - Bicep**: Scenario selection, component toggles, IP addressing, policies
- **Accelerator - Terraform**: Same as Bicep with additional options (AMBA, Sovereign LZ)

Parse the checklist to identify which fields already have values (column F = "Chosen Value") and which are empty. This tells you what the user has already decided vs. what needs input.

### Phase 2: Interview the user

Gather decisions through structured questions. Ask in batches of 3-4 questions to avoid overwhelming the user. Prioritize in this order:

**Batch 1 — Foundational decisions:**
- IaC type (Bicep or Terraform)
- Version control system (Azure DevOps, GitHub, or local)
- Network topology scenario (Hub & Spoke vs vWAN, single vs multi-region, Azure Firewall vs NVA)
- Azure region

**Batch 2 — Component decisions:**
- Which components to deploy (DDoS, Private DNS, Bastion, VPN Gateway, ExpressRoute, Zero Trust)
- Security posture (AMA, Defender plans)

**Batch 3 — Environment-specific details:**
- Azure DevOps / GitHub organization and project names
- Subscription IDs (Management, Connectivity, Identity, Security)
- Pipeline approvers
- IP addressing (ask if they have existing documentation)

When the user says "use best practices" or defers a decision, apply the recommendations from `references/alz-best-practices.md`. Always explain why a recommendation is made — users trust recommendations they understand.

### Phase 3: Map subscriptions

If the user provides a subscription list (from `az account list` or similar), map subscriptions to ALZ roles by matching naming patterns:

| Pattern | ALZ Role |
|---------|----------|
| `*mgmt*`, `*management*` | Management |
| `*connectivity*`, `*network*`, `*hub*` | Connectivity |
| `*identity*`, `*ad*`, `*entra*` | Identity |
| `*security*`, `*sentinel*`, `*defender*` | Security |

If a required subscription is missing (commonly Security), flag it with a yellow highlight and a comment explaining the options:
1. Create a dedicated subscription (recommended)
2. Share with Management subscription (budget-constrained alternative)

### Phase 4: Integrate IP addressing

If the user provides IP documentation (Markdown, CSV, Excel, or text), parse it to extract:

- **Subscription-level CIDR blocks** — map to ALZ hub/spoke VNets
- **Existing hub VNet layout** — identify subnet allocations (Gateway, Firewall, Bastion, shared services)
- **On-premises public IPs** — include in comments for VPN/firewall rule reference
- **AKS networking** — pod/service CIDRs if applicable

For the ALZ hub VNet, recommend this subnet layout using the connectivity subscription's CIDR block:

```
Hub VNet: <connectivity-base>/16
  GatewaySubnet:                <base>.0.0/27     (30 hosts)
  AzureFirewallSubnet:          <base>.0.64/26    (62 hosts)
  AzureFirewallManagementSubnet:<base>.0.128/26   (62 hosts)
  AzureBastionSubnet:           <base>.0.192/26   (62 hosts)
  Shared Services:              <base>.1.0/24     (254 hosts)
  DNS Resolver Inbound:         <base>.2.0/28
  DNS Resolver Outbound:        <base>.2.16/28
```

If no IP documentation is provided, use ALZ defaults and flag for review.

### Phase 5: Fill the checklist

Use openpyxl to write values into column F ("Chosen Value") of the appropriate tabs. Apply consistent formatting:

```python
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.comments import Comment

# Confirmed values — green background
green_fill = PatternFill('solid', fgColor='CCE5CC')

# Items needing user action — yellow background + red bold text
yellow_fill = PatternFill('solid', fgColor='FFFF00')
action_font = Font(bold=True, color='FF0000', size=10)

# Informational notes — italic yellow background
note_fill = PatternFill('solid', fgColor='FFFFCC')
note_font = Font(italic=True, size=10)
```

**For every cell you fill:**
- Add a Comment explaining the rationale or best practice reference
- Use green fill for confirmed decisions
- Use yellow fill + red text for items requiring user action (e.g., "TO BE DEFINED", "TO BE PROVIDED")
- Use light yellow fill + italic for items using defaults that the user should review

**Tab-specific logic:**

Only fill the tab matching the user's IaC choice. Clear the other tab if it had values from a previous attempt. For the active tab:

1. **Scenarios section**: Set the chosen scenario to "Yes", all others to "No". Highlight the selected one with a brighter green.
2. **Options section**: Apply the user's component choices. For any option not explicitly discussed, apply best practice defaults and note this in the comment.
3. **Bootstrap tab**: Always fill regardless of IaC choice — it's shared.

### Phase 6: Present results

After saving the filled checklist:

1. Print a summary table showing all filled values
2. List the items flagged for user action (yellow highlights)
3. Call out any architectural considerations (e.g., cross-region peering needed if ALZ region differs from existing infrastructure)
4. Provide the file link for download

## Best practice recommendations

Read `references/alz-best-practices.md` for the full set of recommendations. The key defaults to apply when the user defers:

- **Private networking**: true (state storage should never be publicly accessible)
- **Separate CI/CD template repo**: true (security boundary between code and pipeline definitions)
- **Branch policies**: true (require PRs for all changes)
- **Self-hosted agents/runners**: true (required for private networking)
- **DDoS Protection**: Yes (network-layer protection for all VNet resources)
- **Private DNS Zones**: Yes (required for Private Endpoints across hub-spoke)
- **Azure Bastion**: Yes (secure VM access without public IP exposure)
- **AMA (Azure Monitoring Agent)**: Keep enabled (centralized monitoring)
- **Defender plans**: Keep enabled (threat detection across all resource types)
- **Zero Trust**: Yes (least-privilege access and micro-segmentation)
- **AMBA alerts** (Terraform only): Yes (proactive monitoring of platform resources)
- **Sovereign Landing Zone**: No (unless explicitly required for compliance)

## Cross-region considerations

If the user's existing infrastructure is in a different region than the ALZ deployment, flag this in the Bootstrap tab's region comment. They'll need to plan for cross-region VNet peering between the ALZ hub and any existing hub-spoke topology.

## Cell Reference Map

The checklist has a fixed structure. Use these exact cell references when writing values to avoid row-offset bugs. Always verify by checking that column B (Name) matches the expected field before writing to column F.

### Bootstrap Tab (Accelerator - Bootstrap)

| Row | Cell | Field (col B) | Config Setting (col D) |
|-----|------|---------------|------------------------|
| 4 | F4 | Infrastructure as Code | iac_type |
| 5 | F5 | Version control system | bootstrap_module_name |
| 6 | F6 | Starter module | starter_module_name |
| 8 | F8 | Bootstrap resource region | bootstrap_location |
| 9 | F9 | Parent management group id | root_parent_management_group_id |
| 10 | F10 | Management subscription id | subscription_id_management |
| 11 | F11 | Connectivity subscription id | subscription_id_connectivity |
| 12 | F12 | Identity subscription id | subscription_id_identity |
| 13 | F13 | Security subscription id | subscription_id_identity (note: template typo) |
| 15 | F15 | Bootstrap subscription id | bootstrap_subscription_id |
| 16 | F16 | Resource naming: service name | service_name |
| 17 | F17 | Resource naming: environment name | environment_name |
| 18 | F18 | Resource naming: postfix number | postfix_number |
| 21 | F21 | Use separate repository for templates | use_separate_repository_for_templates |
| 22 | F22 | Use private networking | use_private_networking |
| 23 | F23 | Allow storage access from my IP | allow_storage_access_from_my_ip |
| 24 | F24 | Apply approvers | apply_approvers |
| 25 | F25 | Create branch policies | create_branch_policies |
| 28 | F28 | Azure DevOps PAT | azure_devops_personal_access_token |
| 29 | F29 | Azure DevOps Agent PAT | azure_devops_agents_personal_access_token |
| 30 | F30 | Azure DevOps Organization | azure_devops_organization_name |
| 31 | F31 | Azure DevOps legacy url | azure_devops_use_organisation_legacy_url |
| 32 | F32 | Create Azure DevOps Project | azure_devops_create_project |
| 33 | F33 | Azure DevOps Project | azure_devops_project_name |
| 34 | F34 | Use self hosted agents | use_self_hosted_agents |

Note: Rows 7, 14, 19, 20, 26, 27, 35, 36, 41 are blank or section headers — skip them.

### Bicep Tab (Accelerator - Bicep) — Scenarios

| Row | Cell | Scenario |
|-----|------|----------|
| 6 | F6 | Multi-Region Hub & Spoke + Azure Firewall |
| 7 | F7 | Multi-Region vWAN + Azure Firewall |
| 8 | F8 | Multi-Region Hub & Spoke + NVA |
| 9 | F9 | Multi-Region vWAN + NVA |
| 10 | F10 | Management Groups, Policy and Management Only |
| 11 | F11 | Single-Region Hub & Spoke + Azure Firewall |
| 12 | F12 | Single-Region vWAN + Azure Firewall |
| 13 | F13 | Single-Region Hub & Spoke + NVA |
| 14 | F14 | Single-Region vWAN + NVA |

### Bicep Tab — Options (rows 17-30)

| Row | Cell | Option |
|-----|------|--------|
| 17 | F17 | Resource naming convention |
| 18 | F18 | Custom management group names |
| 19 | F19 | Deploy DDOS Protection Plan |
| 20 | F20 | Deploy Private DNS |
| 21 | F21 | Deploy Bastion Host |
| 22 | F22 | Deploy VPN Gateway |
| 23 | F23 | Deploy ExpressRoute Gateway |
| 24 | F24 | Deploy to more than 2 regions |
| 25 | F25 | IP Addressing |
| 26 | F26 | Change a policy assignment enforcement mode |
| 27 | F27 | Remove a policy assignment |
| 28 | F28 | Turn off Azure Monitoring Agent |
| 29 | F29 | Turn off Defender Plans |
| 30 | F30 | Zero Trust Security |

### Terraform Tab (Accelerator - Terraform)

Same scenario layout as Bicep (rows 6-14). Options are rows 17-32:

| Row | Cell | Option |
|-----|------|--------|
| 17 | F17 | Resource naming convention |
| 18 | F18 | Custom management group names |
| 19 | F19 | Deploy DDOS Protection Plan |
| 20 | F20 | Deploy Private DNS |
| 21 | F21 | Deploy Bastion Host |
| 22 | F22 | Deploy VPN Gateway |
| 23 | F23 | Deploy ExpressRoute Gateway |
| 24 | F24 | Deploy to more than 2 regions |
| 25 | F25 | IP Addressing |
| 26 | F26 | Change a policy assignment enforcement mode |
| 27 | F27 | Remove a policy assignment |
| 28 | F28 | Turn off Azure Monitoring Agent |
| 29 | F29 | Deploy Azure Monitoring Baseline Alerts (AMBA) |
| 30 | F30 | Turn off Defender Plans |
| 31 | F31 | Zero Trust Security |
| 32 | F32 | Sovereign Landing Zone |

**Validation approach**: Before writing any value, read cell B{row} and verify it matches the expected field name. If it doesn't match, scan the sheet to find the correct row. This prevents silent data corruption from template version differences.

## Output format

The final deliverable is an `.xlsx` file with:
- All three tabs preserved from the original template
- Column F filled with chosen values
- Cell comments with rationale and best practice references
- Color coding: green (confirmed), yellow (needs action), light yellow (defaults to review)
- A clear summary in the conversation listing all decisions and flagged items
