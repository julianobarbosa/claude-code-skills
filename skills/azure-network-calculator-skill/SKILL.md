---
name: azure-network-calculator-skill
description: Azure network planning — CIDR calculation, subnet allocation, VNet sizing, IP address planning, snet layout, network capacity, Azure networking, hub-spoke topology. USE WHEN CIDR, subnet, VNet, snet, network planning, IP address, Azure networking, calculate network, plan network, validate CIDR, network capacity, address space.
---

## Customization

**Before executing, check for user customizations at:**
`~/.claude/skills/PAI/USER/SKILLCUSTOMIZATIONS/azure-network-calculator-skill/`

If this directory exists, load and apply any PREFERENCES.md, configurations, or resources found there. These override default behavior. If the directory does not exist, proceed with skill defaults.

## MANDATORY: Voice Notification (REQUIRED BEFORE ANY ACTION)

**You MUST send this notification BEFORE doing anything else when this skill is invoked.**

1. **Send voice notification**:

   ```bash
   curl -s -X POST http://localhost:8888/notify \
     -H "Content-Type: application/json" \
     -d '{"message": "Running the WORKFLOWNAME workflow in the azure-network-calculator-skill skill to ACTION"}' \
     > /dev/null 2>&1 &
   ```

2. **Output text notification**:
   ```
   Running the **WorkflowName** workflow in the **azure-network-calculator-skill** skill to ACTION...
   ```

**This is not optional. Execute this curl command immediately upon skill invocation.**

# azure-network-calculator-skill

Automates CIDR calculation, subnet allocation, and Terraform code generation for Hypera's Azure hub-spoke infrastructure.

## Workflow Routing

| Intent                                         | Workflow                                            | Description                                   |
| ---------------------------------------------- | --------------------------------------------------- | --------------------------------------------- |
| Plan a VNet + subnets for a new resource group | [PlanNetwork](Workflows/PlanNetwork.md)             | Design complete network layout with Terraform |
| Check if a CIDR overlaps existing allocations  | [ValidateCidr](Workflows/ValidateCidr.md)           | Overlap detection against master allocation   |
| Show remaining capacity in a subscription/VNet | [CalculateCapacity](Workflows/CalculateCapacity.md) | Available /20 and /24 blocks                  |

**If the user's intent is ambiguous, ask which workflow to run.**

## Quick Reference

### CIDR Hierarchy

```
/13  (subscription)  = 524,288 addresses = 128 x /20 VNets
/20  (VNet)          =   4,096 addresses =  16 x /24 subnets
/24  (subnet)        =     256 addresses =     251 usable (Azure reserves 5)
/22  (large subnet)  =   1,024 addresses =   1,019 usable
/27  (gateway)       =      32 addresses =      27 usable
/26  (firewall)      =      64 addresses =      59 usable
```

### VNet Index Formula

```
VNet[i] address = subscription_base + (i * 4096)    # 4096 = 2^(32-20)
VNet[i] CIDR    = calculated_address/20
```

Each `/13` subscription holds exactly **128** `/20` VNets (index 0-127).

### Azure Reserved IPs (5 per subnet)

| Offset | Purpose         |
| ------ | --------------- |
| +0     | Network address |
| +1     | Default gateway |
| +2     | DNS mapping     |
| +3     | DNS mapping     |
| Last   | Broadcast       |

### Naming Convention

```
snet-{purpose}-{rg}-{env}-{region}
vnet-{rg}-{env}-{region}
nsg-{purpose}-{rg}-{env}-{region}
natg-{rg}-{env}-{region}
```

Where `{rg}` is the resource group name (without `rg-hypera-` prefix), `{env}` is `dev`/`hlg`/`prd`, `{region}` is the shortcode (e.g., `eus`).

## Context Files

| File                                               | Purpose                                     |
| -------------------------------------------------- | ------------------------------------------- |
| [CidrMasterAllocation.md](CidrMasterAllocation.md) | All 16 subscriptions, known VNets, formulas |
| [SubnetTemplates.md](SubnetTemplates.md)           | 4 workload archetype subnet layouts         |
| [TerraformSnippets.md](TerraformSnippets.md)       | AVM module HCL matching repo patterns       |
