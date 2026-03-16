# PlanNetwork Workflow

Design a complete VNet + subnet layout for a new resource group, with Terraform code generation.

## Inputs

Gather these from the user (ask if not provided):

1. **Subscription** — which of the 16 subscriptions (e.g., `solucoes-dev`, `infrastructure-dev`)
2. **Workload type** — one of: `hub`, `3tier-dev`, `3tier-prd`, `packer-devops`, or `custom`
3. **Resource group name** — e.g., `rg-hypera-painelclientes`
4. **Environment** — `dev`, `hlg`, or `prd`
5. **Region** — defaults to `eastus` (shortcode `eus`)
6. **VNet index** — specific index or "next available" (default)
7. **Include AKS?** — if yes, allocate overlay CIDRs

## Steps

### Step 1: Load Master Allocation

Read [CidrMasterAllocation.md](../CidrMasterAllocation.md):
- Find the subscription's `/13` base address
- List known VNet allocations for that subscription
- Determine next available VNet index (if not specified)

### Step 2: Calculate VNet CIDR

```
subscription_base = from master table (e.g., 10.160.0.0 for solucoes-dev)
vnet_index = next available or user-specified
vnet_base_offset = vnet_index * 4096

# Convert offset to octets:
octet2_add = floor(vnet_index * 16 / 256)
octet3 = (vnet_index * 16) mod 256

vnet_cidr = subscription_base.octet1 . (subscription_base.octet2 + octet2_add) . octet3 . 0 / 20
```

**Verify:** The calculated VNet falls within the subscription's `/13` range.

### Step 3: Load Subnet Template

Read [SubnetTemplates.md](../SubnetTemplates.md) and load the selected archetype.

### Step 4: Calculate Subnet CIDRs

For each subnet in the template:
1. Parse the VNet base: `A.B.C.0`
2. Apply offset: `A.B.(C + offset_octet3).(offset_octet4) / mask`
3. Calculate usable hosts: `2^(32-mask) - 5`

### Step 5: Apply Naming Convention

For each subnet:
```
snet-{purpose}-{rg_short}-{env}-{region_short}
```

Where `rg_short` strips the `rg-hypera-` prefix from the resource group name.

Azure-mandated names (`GatewaySubnet`, `AzureFirewallSubnet`, `AzureBastionSubnet`) override this convention.

### Step 6: Allocate AKS Overlay CIDRs (if applicable)

Read the AKS Overlay CIDR table in [CidrMasterAllocation.md](../CidrMasterAllocation.md):
- Find next available pair
- Assign: even = Pod CIDR, odd = Service CIDR
- DNS Service IP = Service CIDR base + 10

### Step 7: Generate Terraform Code

Read [TerraformSnippets.md](../TerraformSnippets.md) and produce:
- `networking.tf` — VNet module block with all subnets
- `variables.tf` additions — variable declarations for each CIDR
- `name.tf` additions — naming locals
- `terraform.tfvars` additions — concrete CIDR values
- `nsg.tf` additions (if template includes NSG)
- `natg.tf` additions (if template includes NAT Gateway)

### Step 8: Output

Present a structured summary:

```
## Network Plan: {resource_group} ({subscription})

### VNet
| Property | Value |
|----------|-------|
| Name | vnet-{name}-{env}-{region} |
| CIDR | X.Y.Z.0/20 |
| Range | X.Y.Z.0 - X.Y.(Z+15).255 |
| Index | {index} of 128 |

### Subnets
| Name | CIDR | Usable Hosts | Purpose |
|------|------|--------------|---------|
| ... | ... | ... | ... |

### AKS Overlay (if applicable)
| Component | CIDR |
|-----------|------|
| Pod CIDR | 172.XX.0.0/16 |
| Service CIDR | 172.XX.0.0/16 |
| DNS Service IP | 172.XX.0.10 |

### Capacity After Allocation
| Metric | Value |
|--------|-------|
| VNets used / total | X / 128 |
| /24 blocks used in this VNet | X / 16 |
| Next available /24 in VNet | X.Y.Z.0/24 |

### Terraform Code
[generated HCL]
```

## Validation Checklist

Before presenting output, verify:
- [ ] VNet CIDR falls within subscription's /13 range
- [ ] No overlap with known VNet allocations
- [ ] All subnet CIDRs fall within the VNet's /20 range
- [ ] No subnet CIDRs overlap each other
- [ ] /22 subnets are aligned to /22 boundaries (third octet divisible by 4 relative to VNet base)
- [ ] Azure-mandated subnet names are used where required
- [ ] AKS overlay CIDRs don't conflict with existing allocations
