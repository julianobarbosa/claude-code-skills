# Network Calculator Workflow

## Initialization

Detect the user's request type from their input and route to the appropriate action.

## Command Dispatch

### Calculate (CIDR info, host sizing)
1. Run: `python3 ./scripts/network-calc.py calculate <CIDR>` or `--from-hosts N`
2. Present results in a formatted table
3. If `--split` requested, show all resulting subnets

### Analyze (VNet utilization, gaps)
1. Run: `python3 ./scripts/network-calc.py analyze --vnet <CIDR> --subnets <list>`
2. Or: `python3 ./scripts/network-calc.py analyze --from-tfvars <path>`
3. Present allocation table, utilization %, and gap analysis
4. Highlight gaps suitable for new workloads (AKS, containers, databases)

### Validate (overlap detection, Azure constraints)
1. Run: `python3 ./scripts/network-calc.py validate --vnet <CIDR> --subnets <list>`
2. Report all violations with severity (CRITICAL, ERROR, WARNING)
3. If valid, confirm with green status
4. Exit code 1 = violations found (compatible with pre-commit hooks)

### First-Fit (find optimal subnet placement)
1. Run: `python3 ./scripts/network-calc.py first-fit --vnet <CIDR> --subnets <list> --hosts N`
2. Returns the optimal CIDR for the requested host count
3. Shows placement within available gaps

### Plan AKS Network
1. Read `references/aks-networking-guide.md` for CNI comparison and sizing formulas
2. Ask user for: CNI type, max nodes, max pods per node
3. Calculate node subnet size, pod CIDR, service CIDR
4. Run first-fit against current VNet to place AKS subnet
5. Generate NSG rules from `templates/nsg-rules-aks.tfvars.tpl`

### Plan Multi-Environment
1. Run: `python3 ./scripts/network-calc.py plan-multi --base <CIDR> --envs N --prefix P`
2. Present environment allocation table
3. Fill `templates/multi-env-plan.md.tpl` with results
4. Validate no overlaps between environments

### Best Practices Query
Route to the appropriate reference file:
- CIDR math → `references/cidr-calculation-guide.md`
- AKS networking → `references/aks-networking-guide.md`
- Segmentation → `references/segmentation-patterns.md`
- Azure limits → `references/azure-constraints.md`

## Output Rules

- Always present CIDR calculations in structured tables
- When generating Terraform output, follow `terraform/variables.tf` variable naming
- Always run validate after any calculation before presenting final results
- Include utilization percentage in all analysis outputs

## Integration

Users can add these targets to their justfile:
```just
net-calc *ARGS:
    python3 .claude/skills/devops-network-calculator-for-azure/scripts/network-calc.py {{ARGS}}

net-validate:
    python3 .claude/skills/devops-network-calculator-for-azure/scripts/network-calc.py validate --from-tfvars terraform/terraform.tfvars
```
