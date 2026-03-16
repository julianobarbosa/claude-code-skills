# Subnet Templates

Four workload archetypes covering ~90% of Hypera deployments. For custom layouts, use these as starting points and adjust.

## Template 1: Hub Network

For centralized connectivity, firewall, bastion, and shared services.

| Subnet | Offset | CIDR Mask | Usable Hosts | Purpose | Azure Name Requirement |
|--------|--------|-----------|--------------|---------|----------------------|
| GatewaySubnet | +0.0 | /27 | 27 | VPN/ExpressRoute Gateway | Must be "GatewaySubnet" |
| AzureFirewallSubnet | +0.64 | /26 | 59 | Azure Firewall | Must be "AzureFirewallSubnet" |
| AzureBastionSubnet | +0.128 | /26 | 59 | Azure Bastion | Must be "AzureBastionSubnet" |
| snet-shared-services | +1.0 | /24 | 251 | Monitoring, DNS, shared tools | — |
| snet-aks-nodes | +2.0 | /22 | 1,019 | AKS cluster nodes (CNI Overlay) | — |

**Total /24 blocks consumed:** ~7 of 16 (gateway+fw+bastion share block 0, shared=block 1, AKS=blocks 2-5)
**Next available:** block 6 (+6.0)

**Offset calculation example** (VNet base 10.136.16.0/20):
- GatewaySubnet: 10.136.16.0/27
- AzureFirewallSubnet: 10.136.16.64/26
- AzureBastionSubnet: 10.136.16.128/26
- snet-shared-services: 10.136.17.0/24
- snet-aks-nodes: 10.136.18.0/22

## Template 2: 3-Tier App (Dev)

Standard development environment with application, data, and integration tiers.

| Subnet | Offset | CIDR Mask | Usable Hosts | Purpose |
|--------|--------|-----------|--------------|---------|
| snet-app-tier | +0.0 | /24 | 251 | App Services, VMs, containers |
| snet-data-tier | +1.0 | /24 | 251 | PostgreSQL, SQL, Redis |
| snet-integration | +2.0 | /24 | 251 | Logic Apps, Functions, APIs |
| snet-private-endpoints | +3.0 | /24 | 251 | Private Endpoints for PaaS |
| snet-aks-nodes | +4.0 | /24 | 251 | AKS nodes (dev scale) |

**Total /24 blocks consumed:** 5 of 16
**Next available:** block 5 (+5.0)

**Offset calculation example** (VNet base 10.144.16.0/20):
- snet-app-tier: 10.144.16.0/24
- snet-data-tier: 10.144.17.0/24
- snet-integration: 10.144.18.0/24
- snet-private-endpoints: 10.144.19.0/24
- snet-aks-nodes: 10.144.20.0/24

## Template 3: 3-Tier App (Prd)

Production environment — same structure as dev but with `/22` AKS subnet for scale.

| Subnet | Offset | CIDR Mask | Usable Hosts | Purpose |
|--------|--------|-----------|--------------|---------|
| snet-app-tier | +0.0 | /24 | 251 | App Services, VMs, containers |
| snet-data-tier | +1.0 | /24 | 251 | PostgreSQL, SQL, Redis |
| snet-integration | +2.0 | /24 | 251 | Logic Apps, Functions, APIs |
| snet-private-endpoints | +3.0 | /24 | 251 | Private Endpoints for PaaS |
| snet-aks-nodes | +4.0 | /22 | 1,019 | AKS nodes (production scale) |

**Total /24 blocks consumed:** 8 of 16 (4 x /24 + 1 x /22 = 4 + 4)
**Next available:** block 8 (+8.0)

**Offset calculation example** (VNet base 10.136.32.0/20):
- snet-app-tier: 10.136.32.0/24
- snet-data-tier: 10.136.33.0/24
- snet-integration: 10.136.34.0/24
- snet-private-endpoints: 10.136.35.0/24
- snet-aks-nodes: 10.136.36.0/22

## Template 4: Packer/DevOps

Infrastructure tooling — image builds, CI/CD agents, automation. Matches `rg-hypera-packer-image` pattern.

| Subnet | Offset | CIDR Mask | Usable Hosts | Purpose |
|--------|--------|-----------|--------------|---------|
| snet-private | +12.0 | /24 | 251 | Packer VMs, build agents (NAT GW + NSG) |
| snet-public | +14.0 | /24 | 251 | Public-facing services (NAT GW) |
| snet-gateway | +15.0 | /27 | 27 | VPN/ExpressRoute Gateway |
| AzureBastionSubnet | +15.32 | /27 | 27 | Azure Bastion secure access |

**Total /24 blocks consumed:** ~4 of 16 (blocks 12, 14, 15 used; 0-11 and 13 free)
**Next available:** block 0 (+0.0)

**Note:** This template leaves blocks 0-11 and 13 intentionally free for workload subnets and private endpoints. Additional subnets can be added:
- snet-workload-01: block 1 (+1.0, /24)
- snet-private-endpoints: block 2 (+2.0, /24)

**Offset calculation example** (VNet base 10.248.0.0/20):
- snet-private: 10.248.12.0/24
- snet-public: 10.248.14.0/24
- snet-gateway: 10.248.15.0/27
- AzureBastionSubnet: 10.248.15.32/27

## Applying Templates

To apply a template to a VNet base address:

1. Take the VNet base (e.g., `10.160.0.0/20`)
2. Parse octets: `A.B.C.0` where C is the third octet
3. For each subnet, add the offset to the third and fourth octets:
   - `+N.M` means: third_octet = C + N, fourth_octet = M
4. Apply the mask

**Service endpoints by template:**

| Subnet | Recommended Service Endpoints |
|--------|-------------------------------|
| snet-data-tier | Microsoft.Sql, Microsoft.Storage |
| snet-private | Microsoft.ServiceBus, Microsoft.Sql, Microsoft.Storage |
| snet-public | Microsoft.ContainerRegistry, Microsoft.ServiceBus, Microsoft.Storage |
| AzureBastionSubnet | Microsoft.Storage |
