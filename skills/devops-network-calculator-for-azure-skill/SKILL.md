---
name: devops-network-calculator-for-azure
description: "Azure network planning, CIDR calculation, subnet sizing, and best-practices tool. Use this skill whenever the user asks about subnet sizing, CIDR planning, AKS networking, NSG rules, network segmentation, IP address management, VNet planning, address space analysis, overlap detection, or any Azure networking topic. Also trigger when the user mentions network calculator, net-calc, calculate hosts, plan subnets, or asks about Azure network best practices, even if they don't explicitly say 'network calculator'."
---

# Azure Network Calculator

Offline Azure network planning tool. Calculates CIDRs, detects overlaps, analyzes VNet utilization, plans AKS networking, and generates Terraform-ready output. Zero external dependencies — uses Python stdlib only.

## Quick Start

```bash
# What CIDR do I need for 500 hosts?
python3 scripts/network-calc.py calculate --from-hosts 500

# Analyze current VNet
python3 scripts/network-calc.py analyze --from-tfvars terraform/terraform.tfvars

# Validate for overlaps (pre-commit compatible)
python3 scripts/network-calc.py validate --from-tfvars terraform/terraform.tfvars

# Find where to place a new subnet
python3 scripts/network-calc.py first-fit --vnet 10.248.0.0/20 \
  --subnets "10.248.0.0/22,10.248.4.0/22,10.248.8.0/26,10.248.9.0/24" --hosts 500
```

## Commands

| Command | Purpose | Reference |
|---------|---------|-----------|
| `calculate` | CIDR info, host sizing, subnet splitting | [CIDR Guide](./references/cidr-calculation-guide.md) |
| `analyze` | VNet utilization, gap analysis | [CIDR Guide](./references/cidr-calculation-guide.md) |
| `validate` | Overlap detection, Azure constraint checks | [Azure Constraints](./references/azure-constraints.md) |
| `first-fit` | Find optimal placement for new subnet | [CIDR Guide](./references/cidr-calculation-guide.md) |
| `plan-multi` | Multi-environment VNet allocation | [Segmentation](./references/segmentation-patterns.md) |

## Project Context

This project's current VNet: `10.248.0.0/20` (4,096 IPs, 57.8% utilized)

| Subnet | CIDR | Usable |
|--------|------|--------|
| GatewaySubnet | 10.248.0.0/22 | 1,019 |
| PublicSubnet | 10.248.4.0/22 | 1,019 |
| AzureBastionSubnet | 10.248.8.0/26 | 59 |
| PrivateSubnet | 10.248.9.0/24 | 251 |
| **Available gaps** | | **1,708** |

Key files: `terraform/terraform.tfvars`, `terraform/networking.tf`, `terraform/nsg.tf`

## Azure Quick Reference

- **5 reserved IPs** per subnet (.0, .1, .2, .3, broadcast)
- **Bastion:** min /26 | **Gateway:** min /27 | **Firewall:** min /26
- **Max subnets/VNet:** 3,000 | **Max NSG rules:** 1,000
- Full reference: [Azure Constraints](./references/azure-constraints.md)

## Reference Guides

| Guide | When to Read |
|-------|-------------|
| [CIDR Calculation Guide](./references/cidr-calculation-guide.md) | Subnet sizing, gap analysis, overlap detection |
| [AKS Networking Guide](./references/aks-networking-guide.md) | CNI comparison, pod/service CIDR, node sizing |
| [Segmentation Patterns](./references/segmentation-patterns.md) | Design patterns, anti-patterns, decision matrices |
| [Azure Constraints](./references/azure-constraints.md) | Hard limits, naming rules, reserved addresses |

## Templates

| Template | Purpose |
|----------|---------|
| [VNet Layout](./templates/vnet-layout.tfvars.tpl) | Terraform variable blocks for VNet config |
| [AKS NSG Rules](./templates/nsg-rules-aks.tfvars.tpl) | NSG rules for AKS workloads |
| [Multi-Env Plan](./templates/multi-env-plan.md.tpl) | Multi-environment planning output |

## Execution

Follow the instructions in `./workflow.md`.
