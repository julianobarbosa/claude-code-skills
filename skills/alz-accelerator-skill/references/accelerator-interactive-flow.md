# ALZ Accelerator Interactive Flow — Step-by-Step Reference

This documents the exact interactive flow demonstrated by the ALZ core team (Jared) in the ALZ Weekly video series (2026).

## Prerequisites Checklist

Before running `Deploy-Accelerator`:

- [ ] ALZ PowerShell module installed (`Install-Module -Name ALZ`)
- [ ] Azure CLI authenticated (`az login`)
- [ ] GitHub PAT or Azure DevOps PAT ready
- [ ] Platform subscriptions created:
  - Management subscription
  - Connectivity subscription
  - Identity subscription
  - Security subscription
  - Bootstrap subscription (for state/identities)
- [ ] Root management group identified or created

## Interactive Flow Sequence

### Phase 1: Setup

```
Deploy-Accelerator
```

1. **Software validation** — Checks for required tools (az, terraform/bicep, git)
2. **Cache directory** — Where to store temp files (accept default or specify)
   - If directory exists with prior data, confirm overwrite
3. **IaC selection** — `Terraform` or `Bicep`
4. **VCS selection** — `GitHub` (default) | `Azure DevOps` | `Local filesystem`
5. **Connectivity scenario** — Multiple options:
   - Scenario 1: Full multi-region hub-and-spoke virtual networking
   - Other scenarios for vWAN, single-region, etc.

### Phase 2: Azure Resource Discovery

The accelerator queries your Azure tenant to discover:
- Available regions
- Existing management groups
- Available subscriptions

This takes ~1 minute depending on tenant size.

### Phase 3: Configuration Prompts

Each prompt shows numbered options from your Azure tenant:

6. **Bootstrap region** — Select from numbered list of Azure regions
   - Example: `49` for Sweden Central
7. **Root management group** — Select parent MG for ALZ hierarchy
8. **Management subscription** — Select from numbered subscription list
9. **Identity subscription** — Select from list
10. **Connectivity subscription** — Select from list
11. **Security subscription** — Select from list
12. **Bootstrap subscription** — For Terraform state storage / managed identities

### Phase 4: Bootstrap Configuration

13. **Resource naming convention** — Accept defaults or customize prefix/suffix
14. **Runner type** — `Self-hosted` or `Microsoft-hosted`
    - Self-hosted recommended for private networking
15. **Private networking** — Yes/No (storage account public access)
    - Recommended: Yes for production
16. **Personal Access Token** — Paste PAT (displayed obfuscated)
17. **GitHub/ADO organization name** — Your org handle
18. **Apply approver** — Username for plan→apply approval gate

### Phase 5: Review & Customize

19. **Open in VS Code?** — Yes (default) opens generated config files
20. **Review generated files:**
    - Bootstrap config: All selections pre-populated
    - Sensitive values: Stored as env vars in terminal session, NOT in files
    - Platform landing zone config: Requires manual edits:
      - Primary deployment region (e.g., `uksouth`)
      - Secondary deployment region (e.g., `ukwest`)
      - Defender email security contact
21. **Confirm configuration complete** — Type `yes` when done editing

### Phase 6: Bootstrap Execution

22. The accelerator runs Terraform/Bicep to provision:
    - Azure Storage Account (Terraform state backend)
    - Managed Identities (for CI/CD pipeline auth)
    - GitHub repository with Actions workflows / ADO project with pipelines
    - Branch policies and protection rules
    - Approval gates between plan and apply stages

## File Structure Generated

```
<output-directory>/
  bootstrap/
    terraform.tfvars          # Bootstrap configuration (auto-generated)
  platform/
    terraform.tfvars          # Platform landing zone config (needs manual edits)
  .github/
    workflows/                # CI/CD pipeline definitions (if GitHub)
```

## Key Security Points

- PATs are stored as **environment variables** in the current terminal session
- They are **never written to config files** in plain text
- The accelerator displays sensitive values as obfuscated text
- Self-hosted runners + private networking = no public storage endpoints

## Notes from the Demo

- The interactive mode is new (early 2026) — previously required manual config file editing
- The "advanced scenario" docs still show the old manual method
- Planning docs are linked from each prompt for reference (`aka.ms/alz/accelerator`)
- You can still supply input config files directly for automation/CI scenarios
