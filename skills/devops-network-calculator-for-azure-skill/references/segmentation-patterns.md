# Network Segmentation Patterns

Comprehensive guide to Azure VNet segmentation, NSG design, and subnet architecture.

## Hub-Spoke vs Flat VNet

### When to Use Hub-Spoke

- Multiple workloads or teams sharing centralized services (firewall, DNS, VPN)
- Spoke-to-spoke traffic must be inspected or filtered
- Separate billing or RBAC per spoke
- Multiple environments (dev/staging/prod) sharing a single egress point
- Enterprise environments with 5+ VNets

### When to Use Flat VNet (Single VNet)

- Single-purpose infrastructure (this project)
- All subnets serve one workload or one environment
- No spoke-to-spoke routing requirements
- Simpler operations and lower cost (no NVA/firewall required)
- Fewer than 5 distinct network segments

### This Project Uses Flat VNet -- Correctly

The project deploys a single /20 VNet with 4 subnets serving one environment. There is no cross-workload routing requirement, no shared services hub, and no multi-team isolation need. A hub-spoke topology would add unnecessary Azure Firewall cost (~$1,000/mo) and operational complexity for zero security benefit.

## Subnet Purpose Isolation

Each subnet should serve exactly one purpose. Mixing purposes defeats NSG isolation.

### Standard Subnet Taxonomy

| Subnet | Purpose | NSG Profile | NAT GW | Typical Prefix |
|--------|---------|-------------|--------|---------------|
| GatewaySubnet | VPN/ExpressRoute termination | No NSG allowed | No | /27-/26 |
| AzureBastionSubnet | Bastion jump host | Bastion-specific rules | No | /26 |
| PublicSubnet | Internet-facing workloads (LB, App GW) | Allow inbound 80/443 | Yes | /24-/22 |
| PrivateSubnet | Backend services, APIs, workers | Deny all inbound from internet | Yes | /24-/22 |
| DataSubnet | Databases, storage, caches | Allow only from PrivateSubnet | Optional | /24-/26 |
| AKSSubnet | Kubernetes node pools | AKS-specific (see AKS guide) | Yes | /23-/21 |
| ManagementSubnet | CI/CD agents, monitoring, admin | Restricted inbound, broad outbound | Yes | /26-/24 |

### Isolation Principles

1. **Gateway never mixes with workloads** -- GatewaySubnet has Azure-imposed restrictions (no NSG, no UDR)
2. **Bastion is always isolated** -- its NSG rules are unique and must not leak to other subnets
3. **Public and private are always separate** -- different inbound exposure profiles
4. **Data tier is behind private** -- databases should never be in the same subnet as app servers
5. **AKS gets its own subnet** -- node autoscaling can consume unpredictable IPs

## NSG Rule Design Patterns

### Priority Spacing

Always space priorities by 10 to allow future insertions:

```
100  AllowHTTPS
110  AllowHTTP
120  AllowSSHFromBastion
...
4000 DenyAllInbound
```

Avoid using consecutive priorities (100, 101, 102) -- inserting a rule between them requires renumbering.

### Least Privilege Template

```
Inbound Rules:
  100  Allow [specific source] to [specific port] TCP
  110  Allow [specific source] to [specific port] TCP
  ...
  4000 DenyAllInbound    ← explicit deny-all catchall

Outbound Rules:
  100  Allow [service tag] on [specific port] TCP
  110  Allow [service tag] on [specific port] TCP
  ...
  4000 DenyAllOutbound   ← explicit deny-all catchall
```

### Service Tag Usage

Always prefer service tags over IP addresses:

| Instead of... | Use Service Tag |
|---------------|----------------|
| Azure DC IP ranges | AzureCloud |
| Container registry IPs | AzureContainerRegistry |
| Load balancer probe IPs | AzureLoadBalancer |
| Key Vault endpoints | AzureKeyVault |
| Monitor endpoints | AzureMonitor |
| AAD endpoints | AzureActiveDirectory |
| Storage account IPs | Storage |
| SQL Server IPs | Sql |

### NSG Per Subnet, Not Per NIC

Associate NSGs at the subnet level, not individual NICs. Per-NIC NSGs create management complexity and make it easy to miss a VM.

### Bastion Subnet NSG Pattern

```
Inbound:
  100  Allow Internet      → 443/TCP    (Bastion portal access)
  110  Allow GatewayManager → 443/TCP   (Azure management)
  120  Allow AzureLoadBalancer → 443/TCP (Health probes)
  130  Allow VirtualNetwork → 8080,5701/TCP (Bastion data plane)
  4000 DenyAllInbound

Outbound:
  100  Allow VirtualNetwork → 22/TCP    (SSH to targets)
  110  Allow VirtualNetwork → 3389/TCP  (RDP to targets)
  120  Allow AzureCloud     → 443/TCP   (Azure diagnostics)
  130  Allow VirtualNetwork → 8080,5701/TCP (Bastion data plane)
  4000 DenyAllOutbound
```

### Private Subnet NSG Pattern

```
Inbound:
  100  Allow VirtualNetwork → 443/TCP   (Internal HTTPS)
  110  Allow VirtualNetwork → 22/TCP    (SSH from Bastion)
  4000 DenyAllInbound

Outbound:
  100  Allow AzureCloud     → 443/TCP   (Azure services)
  110  Allow Internet       → 443/TCP   (Package repos, APIs)
  120  Allow VirtualNetwork → 1433/TCP  (SQL to DataSubnet)
  4000 DenyAllOutbound
```

## NAT Gateway Placement

### Where to Associate NAT Gateway

| Subnet | NAT GW | Reason |
|--------|--------|--------|
| PublicSubnet | Yes | Workloads need stable egress IPs |
| PrivateSubnet | Yes | Backend services need outbound (updates, APIs) |
| AKSSubnet | Yes | Nodes need outbound for image pulls, monitoring |
| ManagementSubnet | Yes | CI agents need outbound for package downloads |
| GatewaySubnet | Never | Azure restriction -- not compatible |
| AzureBastionSubnet | Never | Bastion manages its own connectivity |

### NAT Gateway Sizing

- 1 NAT GW supports up to 64,000 concurrent SNAT connections per public IP
- Assign 1-16 public IPs per NAT GW
- Each public IP adds 64,000 SNAT connections
- A single NAT GW can serve multiple subnets in the same VNet

## Service Endpoint vs Private Endpoint

### Decision Matrix

| Factor | Service Endpoint | Private Endpoint |
|--------|-----------------|------------------|
| Traffic path | Microsoft backbone (optimized route) | Private IP in your VNet |
| Cost | Free | ~$7.30/month per endpoint + data processing |
| DNS complexity | None | Requires private DNS zone |
| NSG compatibility | Yes (service tags) | Yes (private IP) |
| Cross-VNet access | No (VNet-scoped) | Yes (via peering/VPN) |
| On-premises access | No | Yes (via VPN/ExpressRoute) |
| Data exfiltration protection | Limited (entire service) | Strong (specific resource) |
| Setup complexity | Low (subnet-level flag) | Medium (DNS + NIC + approval) |
| Supported services | ~20 services | 100+ services |

### When to Use Service Endpoints

- Budget-constrained environments
- Single-VNet deployments with no hybrid connectivity
- Services that only need VNet-to-Azure-service access
- Quick wins: Storage, SQL, Key Vault, Cosmos DB

### When to Use Private Endpoints

- Regulatory requirements for private connectivity
- Hybrid environments (on-prem needs access)
- Multi-VNet architectures (hub-spoke)
- Data exfiltration prevention is a requirement
- Services not supported by service endpoints

### This Project's Approach

Service endpoints are appropriate because:
- Single VNet deployment (no cross-VNet access needed)
- No hybrid/on-premises connectivity requirement
- Cost optimization (no per-endpoint charges)
- Simpler DNS (no private DNS zones to manage)

## Anti-Patterns

### 1. 0.0.0.0/0 Ingress on Any Rule Except Bastion HTTPS

**Why it is wrong:** Opening all internet traffic to any subnet is the most common misconfiguration in Azure. Only `AzureBastionSubnet` should allow inbound from `Internet` on port 443.

**Fix:** Use specific source service tags (`VirtualNetwork`, `AzureLoadBalancer`) or source IP ranges. Never use `*` or `0.0.0.0/0` as source for inbound rules on workload subnets.

### 2. Wildcard Port Ranges on Inbound Rules

**Why it is wrong:** `*` as destination port range allows every port. Attackers scan for open ports and exploit any service they find.

**Fix:** Specify exact ports (443, 22, 3389) or narrow ranges (8080-8090). If you cannot enumerate the ports, the architecture needs redesign.

### 3. NSG with No Explicit Deny Rules

**Why it is wrong:** Azure has an implicit deny at priority 65500, but relying on it means you cannot distinguish "intentionally blocked" from "never considered." Auditors flag this.

**Fix:** Add explicit `DenyAllInbound` at priority 4000 and `DenyAllOutbound` at priority 4000. This documents intent and makes rule ordering visible.

### 4. Overlapping Subnets

**Why it is wrong:** Azure rejects overlapping subnets at deployment time, but overlapping CIDRs in Terraform variables cause confusing plan errors.

**Fix:** Run `network-calc.py validate` before every `terraform plan`. Add overlap checks to pre-commit hooks.

### 5. Bastion Subnet Smaller Than /26

**Why it is wrong:** Azure requires a minimum /26 (64 IPs) for AzureBastionSubnet. Deployment fails with a cryptic error if undersized.

**Fix:** Always allocate /26 for Bastion. Do not try to save IPs here.

### 6. Gateway Subnet Smaller Than /27

**Why it is wrong:** Azure requires a minimum /27 (32 IPs) for GatewaySubnet. ExpressRoute gateways need /26.

**Fix:** Allocate /27 minimum, /26 if ExpressRoute is possible in the future.

### 7. Missing NAT Gateway on Subnets Needing Outbound

**Why it is wrong:** Without NAT Gateway, VMs use ephemeral SNAT IPs that Azure can reassign. This causes intermittent outbound failures under load and makes IP allow-listing impossible.

**Fix:** Associate a NAT Gateway with every subnet that needs outbound internet access (public, private, AKS, management).

### 8. Public IPs on VMs When Bastion Is Available

**Why it is wrong:** Public IPs expose VMs directly to the internet. Bastion provides authenticated, audited, browser-based access without public IP exposure.

**Fix:** Remove public IPs from all VMs. Use Bastion for SSH/RDP. Use NAT Gateway for outbound.

### 9. Flat /16 Without Segmentation

**Why it is wrong:** A single /16 subnet with all resources has no network isolation. Any compromised VM can reach every other VM on any port.

**Fix:** Segment into purpose-specific subnets with dedicated NSGs. Even a minimal deployment benefits from gateway/bastion/public/private separation.

### 10. Hardcoded IPs Instead of Service Tags

**Why it is wrong:** Azure service IPs change without notice. Hardcoded IPs break when Azure updates its IP ranges, causing outages.

**Fix:** Always use service tags (`AzureCloud`, `AzureMonitor`, `Storage`, etc.). Azure updates service tag definitions automatically.

## This Project's Segmentation Design

### Current Layout

```
10.248.0.0/20 (4,096 IPs)
├── GatewaySubnet        10.248.0.0/22   (1,024 IPs) - VPN termination
├── PublicSubnet          10.248.4.0/22   (1,024 IPs) - Internet-facing, NAT GW
├── AzureBastionSubnet   10.248.8.0/26   (64 IPs)    - Bastion jump host
├── PrivateSubnet         10.248.9.0/24   (256 IPs)   - Backend services, NAT GW
├── [gap]                10.248.8.64/26  (192 IPs)   - Available
└── [gap]                10.248.10.0/23  (1,536 IPs) - Available (AKS candidate)
```

### Why This Design Is Correct

1. **Proper isolation:** Gateway, Bastion, public, and private subnets are fully separated with independent NSGs
2. **Mandatory names honored:** `GatewaySubnet` and `AzureBastionSubnet` use Azure's required exact names
3. **Minimum sizes met:** Bastion is /26 (meets /26 minimum), Gateway is /22 (exceeds /27 minimum)
4. **NAT Gateway correctly placed:** Associated with PublicSubnet and PrivateSubnet, not with GatewaySubnet or Bastion
5. **Growth room preserved:** 42% of address space (1,728 IPs) remains unallocated for future AKS or additional workloads
6. **Flat topology appropriate:** Single-purpose infrastructure with no cross-workload routing needs does not benefit from hub-spoke overhead
7. **No anti-patterns present:** No public IPs on VMs, no wildcard port rules, no overlapping subnets, explicit deny rules in all NSGs
