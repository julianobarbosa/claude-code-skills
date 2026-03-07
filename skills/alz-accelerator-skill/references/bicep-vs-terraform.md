# Bicep vs Terraform for Azure Landing Zones — Detailed Comparison

## Feature Matrix (as of early 2026)

| Feature | Terraform | Bicep |
|---------|-----------|-------|
| AVM module support | Full (released early 2025) | Full (released Feb 2026) |
| Configuration method | tfvars files only | Config files + direct module editing |
| State management | Terraform state in Azure Storage | No state file — uses Deployment Stacks |
| Drift detection | Built-in via state | Limited (deployment stacks partial) |
| What-If support | terraform plan (full) | Partial — deployment stacks what-if has gaps |
| Multi-cloud | Yes (core Terraform strength) | No — Azure only |
| Policy management | Via tfvars configuration | Separated custom vs default policies |
| Upgrade path | Standard module versioning | Full repo ownership — no more pulling during pipeline |
| CI/CD bootstrapping | Accelerator (GitHub, ADO, local) | Accelerator (GitHub, ADO, local) |
| Private networking | Self-hosted runners supported | Self-hosted runners supported |

## Terraform Strengths

- **Mature configuration model:** Everything customizable through tfvars without touching module code
- **State-based operations:** Reliable drift detection, import, targeted apply
- **Multi-cloud portable skills:** Same language for AWS, GCP, Azure
- **Longer ALZ track record:** ~1 year head start on AVM integration
- **Ecosystem:** Rich provider ecosystem, community modules

## Bicep Strengths

- **No state file:** Eliminates state locking issues, state corruption, state migration
- **Deployment Stacks:** Azure-native lifecycle management for resource cleanup
- **Full module ownership:** You get the complete repository — customize anything without waiting for upstream releases
- **Separated policy management:** Custom policies and Azure default policies are cleanly separated
- **Azure product group recommendation:** ARM/Bicep teams recommend Bicep for Azure-only organizations
- **First-class Azure integration:** No provider version lag, immediate support for new Azure features

## Decision Checklist

Ask the user these questions to guide the decision:

1. **Does your organization use or plan to use non-Azure clouds?**
   - Yes → Terraform (avoid learning two IaC languages)
   - No → Either works, lean Bicep

2. **Does your team have existing IaC expertise?**
   - Strong Terraform team → Terraform
   - Strong ARM/Bicep team → Bicep
   - No existing expertise → Bicep (simpler ops, no state management)

3. **Do you need robust drift detection?**
   - Critical requirement → Terraform
   - Nice-to-have → Either works

4. **How important is immediate access to new Azure features?**
   - Very important → Bicep (no provider lag)
   - Can wait for provider updates → Either works

5. **How do you feel about state file management?**
   - Comfortable with it → Terraform
   - Want to avoid it → Bicep

## ALZ Core Team Positions

From the ALZ weekly video (2026):
- **Matt:** "Whichever one your team is best suited for — it's down to team skills" (diplomatic answer)
- **Jared:** "Obviously Terraform better" (joking, but acknowledges Terraform's maturity lead)
- **Zach:** Leans Bicep due to familiarity but notes Terraform is equally viable
- **Consensus:** The gap is closing rapidly in 2026. Both are fully supported with AVM.
