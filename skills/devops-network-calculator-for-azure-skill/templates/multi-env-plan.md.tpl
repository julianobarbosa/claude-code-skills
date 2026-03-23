# Multi-Environment Network Plan

**Generated:** {{date}}
**Base CIDR:** {{base_cidr}}
**Environments:** {{env_count}}

## Address Allocation

| Environment | VNet CIDR | Total IPs | Usable IPs | Status |
|-------------|-----------|-----------|------------|--------|
{{#each environments}}
| {{name}} | {{cidr}} | {{total_ips}} | {{usable_hosts}} | Planned |
{{/each}}

## Subnet Layout Per Environment

Each environment follows this standard layout:

| Subnet | Prefix | Hosts | Purpose |
|--------|--------|-------|---------|
| GatewaySubnet | /27 | 27 | VPN/ExpressRoute |
| AzureBastionSubnet | /26 | 59 | Bastion access |
| PublicSubnet | /24 | 251 | NAT GW outbound |
| PrivateSubnet | /24 | 251 | Workloads |
| AKSSubnet | /23 | 507 | Kubernetes nodes |
| DataSubnet | /24 | 251 | Databases, PE |

## Peering Matrix

| From | To | Overlap Check |
|------|----|---------------|
{{#each peering_pairs}}
| {{from}} | {{to}} | {{status}} |
{{/each}}

## Validation Results

- Overlap check: {{overlap_status}}
- Address space remaining: {{remaining}} IPs
- Peering safe: {{peering_safe}}
