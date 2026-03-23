# Azure Network Constraints Reference

Quick reference for Azure networking hard limits, reserved addresses, and naming rules.

## Reserved IP Addresses Per Subnet

Azure reserves 5 IP addresses in every subnet:

| Address | Purpose |
|---------|---------|
| x.x.x.0 | Network address |
| x.x.x.1 | Default gateway |
| x.x.x.2 | Azure DNS mapping |
| x.x.x.3 | Azure DNS mapping |
| x.x.x.255 | Broadcast (last address) |

**Formula:** `usable_hosts = 2^(32 - prefix_length) - 5`

## Usable Hosts by Prefix Length

| Prefix | Total IPs | Usable (Azure) | Typical Use |
|--------|-----------|-----------------|-------------|
| /16 | 65,536 | 65,531 | Large VNet |
| /17 | 32,768 | 32,763 | Multi-workload VNet |
| /18 | 16,384 | 16,379 | Medium VNet |
| /19 | 8,192 | 8,187 | Large subnet |
| /20 | 4,096 | 4,091 | Standard VNet (this project) |
| /21 | 2,048 | 2,043 | Large workload subnet |
| /22 | 1,024 | 1,019 | AKS nodes (Azure CNI) |
| /23 | 512 | 507 | AKS nodes (CNI Overlay) |
| /24 | 256 | 251 | Standard workload subnet |
| /25 | 128 | 123 | Small workload |
| /26 | 64 | 59 | Min: Bastion, Firewall |
| /27 | 32 | 27 | Min: Gateway, RouteServer |
| /28 | 16 | 11 | Minimal workload |
| /29 | 8 | 3 | Azure minimum subnet |

## Minimum Subnet Sizes by Purpose

| Subnet Name | Min Prefix | Min IPs | Required Name |
|-------------|-----------|---------|---------------|
| AzureBastionSubnet | /26 | 64 | Exact (mandatory) |
| GatewaySubnet | /27 (/26 for ExpressRoute) | 32 | Exact (mandatory) |
| AzureFirewallSubnet | /26 | 64 | Exact (mandatory) |
| AzureFirewallManagementSubnet | /26 | 64 | Exact (mandatory) |
| RouteServerSubnet | /27 | 32 | Exact (mandatory) |
| AKS node subnet (Azure CNI) | /24 recommended | 256 | User-defined |
| AKS node subnet (CNI Overlay) | /27 minimum | 32 | User-defined |
| General purpose | /29 minimum | 8 | User-defined |

## Azure Resource Limits

| Resource | Limit |
|----------|-------|
| Subnets per VNet | 3,000 |
| VNets per subscription per region | 1,000 |
| NSG rules per NSG | 1,000 |
| Address spaces per VNet | 500 |
| VNet peerings per VNet | 500 |
| Route tables per subscription | 200 |
| Routes per route table | 400 |
| DNS servers per VNet | 25 |
| Private endpoints per VNet | 1,000 |
| Service endpoints per subnet | 25 (service limit) |
| Network interfaces per VNet | 65,536 |
| Public IPs per subscription | 1,000 (Standard) |

## Naming Constraints

| Rule | Details |
|------|---------|
| Mandatory names | `AzureBastionSubnet`, `GatewaySubnet`, `AzureFirewallSubnet` must use exact names |
| Subnet name length | 1-80 characters |
| Allowed characters | Alphanumeric, hyphen, underscore, period |
| VNet name length | 2-64 characters |
| NSG name length | 1-80 characters |

## VNet Peering Constraints

- Address spaces of peered VNets **must not overlap**
- Peering is non-transitive (A peers B, B peers C does not mean A reaches C without NVA/firewall)
- Hub-spoke requires UDRs or Azure Firewall for spoke-to-spoke traffic
- Maximum 500 peerings per VNet

## Private DNS Zone Limits

- 25 linked VNets per private DNS zone (with auto-registration)
- 1,000 linked VNets per private DNS zone (without auto-registration)
- Private AKS clusters require a private DNS zone for the API server
