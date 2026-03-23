# AKS Networking Guide

Comprehensive reference for Azure Kubernetes Service networking models, subnet sizing, and integration with Azure VNets.

## CNI Comparison Matrix

| Feature | Azure CNI | Kubenet | CNI Overlay | CNI + Cilium |
|---------|-----------|---------|-------------|-------------|
| Pod IP source | VNet subnet | Private bridge (NAT) | Overlay network | Overlay network |
| Pod IPs routable in VNet | Yes | No (requires UDR) | No | No |
| Min node subnet | /24 recommended | /24 recommended | /27 minimum | /27 minimum |
| IP consumption per node | node + (max_pods * nodes) | 1 IP per node | 1 IP per node | 1 IP per node |
| Max pods per node (default) | 30 | 110 | 250 | 250 |
| Max pods per node (max) | 250 | 110 | 250 | 250 |
| Network Policy support | Azure + Calico | Calico only | Azure + Calico | Cilium (native) |
| Windows node pools | Yes | No | Yes | No |
| Service mesh integration | External (Istio, etc.) | External | External | Native (Cilium) |
| eBPF dataplane | No | No | No | Yes |
| Performance overhead | Lowest (native VNet) | Moderate (NAT) | Low (VXLAN) | Lowest (eBPF) |
| DNS resolution | Azure DNS | Azure DNS | Azure DNS | Azure DNS |
| Dual-stack (IPv4/IPv6) | Yes | No | Yes | Yes |
| Private endpoint access | Direct (same VNet) | Via UDR | Via UDR or NAT | Via UDR or NAT |
| Complexity | Medium | Low | Low | Medium |
| Recommended for | Large clusters needing VNet-routed pods | Dev/test, small clusters | Most production workloads | Advanced networking, observability |

## Node Subnet Sizing Formulas

### Azure CNI (VNet-Allocated Pod IPs)

Every pod gets a real VNet IP. This is the most IP-hungry model.

```
required_IPs = (max_pods_per_node + 1) * node_count + reserved(5)
```

Default max_pods_per_node = 30, so:

```
required_IPs = 31 * node_count + 5
```

| Nodes | Required IPs | Min Prefix | Usable IPs |
|-------|-------------|------------|------------|
| 10 | 315 | /23 (512) | 507 |
| 50 | 1,555 | /21 (2,048) | 2,043 |
| 100 | 3,105 | /20 (4,096) | 4,091 |
| 250 | 7,755 | /19 (8,192) | 8,187 |

### Kubenet (NAT Bridge)

Only node IPs come from the VNet. Pods use a private 10.244.0.0/16 overlay.

```
required_IPs = node_count + 5
```

| Nodes | Required IPs | Min Prefix | Usable IPs |
|-------|-------------|------------|------------|
| 10 | 15 | /28 (16) | 11 |
| 50 | 55 | /26 (64) | 59 |
| 100 | 105 | /25 (128) | 123 |
| 400 | 405 | /23 (512) | 507 |

### CNI Overlay / CNI + Cilium

Like Kubenet for node IPs -- only nodes consume VNet addresses. Pods get overlay IPs.

```
required_IPs = node_count + 5
```

Same table as Kubenet, but with higher max_pods_per_node (250 vs 110) and no UDR requirement.

| Nodes | Required IPs | Min Prefix | Usable IPs |
|-------|-------------|------------|------------|
| 10 | 15 | /28 (16) | 11 |
| 50 | 55 | /26 (64) | 59 |
| 100 | 105 | /25 (128) | 123 |
| 500 | 505 | /23 (512) | 507 |

## Pod CIDR Planning

The pod CIDR defines the address space for pod IPs in overlay models (Kubenet, CNI Overlay, CNI + Cilium).

### Defaults

| Parameter | Default Value |
|-----------|--------------|
| Pod CIDR | 10.244.0.0/16 (65,536 IPs) |
| Per-node pod CIDR | /24 (256 IPs per node, drawn from pod CIDR) |

### Sizing the Pod CIDR

```
pod_cidr_size = nodes * (2^(32 - per_node_prefix))
```

With default /24 per node:
- 256 nodes need 256 * 256 = 65,536 IPs = /16
- 512 nodes need a /15
- 1,000 nodes need a /14

### Overlap Rules

- Pod CIDR **must not overlap** with:
  - VNet address space (e.g., 10.248.0.0/20)
  - Service CIDR
  - Docker bridge CIDR (172.17.0.0/16 by default)
  - Any peered VNet address space
- Pod CIDR **can overlap** with:
  - Pod CIDRs in other, non-peered clusters (they are isolated)
- The default 10.244.0.0/16 is safe for this project's 10.248.0.0/20 VNet (no overlap)

## Service CIDR Planning

The service CIDR provides ClusterIP addresses for Kubernetes services.

### Defaults

| Parameter | Default Value |
|-----------|--------------|
| Service CIDR | 10.0.0.0/16 |
| DNS Service IP | 10.0.0.10 (must be within service CIDR) |

### Rules

- Service CIDR **must not overlap** with VNet address space, pod CIDR, or peered networks
- DNS service IP must be within the service CIDR but **not** the first IP (network address)
- By convention, DNS IP is at the `.10` offset (e.g., 10.0.0.10 for 10.0.0.0/16)
- A /16 supports 65,531 services (far exceeding most cluster needs)
- For smaller clusters, /20 (4,091 services) is sufficient

### Recommended Values for This Project

| Parameter | Value | Rationale |
|-----------|-------|-----------|
| VNet | 10.248.0.0/20 | Project allocation |
| Pod CIDR | 10.244.0.0/16 | Default, no overlap with VNet |
| Service CIDR | 10.245.0.0/16 | Adjacent to pod CIDR, no overlap |
| DNS Service IP | 10.245.0.10 | Convention: .10 offset |

## Private AKS Cluster Requirements

A private AKS cluster exposes the API server only via a private endpoint inside the VNet.

### Mandatory Components

1. **Private DNS Zone** for the API server
   - Zone name: `privatelink.<region>.azmk8s.io`
   - Must be linked to the VNet where the cluster lives
   - Must be linked to any VNet that needs to resolve the API server (e.g., CI/CD agents)

2. **VNet Link** from the private DNS zone to the cluster VNet
   - Auto-registration not required (AKS manages the A record)
   - Additional VNet links needed for hub VNets in hub-spoke topologies

3. **No Public API Endpoint**
   - `public_network_access_enabled = false`
   - API server accessible only from within the VNet or via peered/VPN-connected networks
   - CI/CD pipelines must run from within the network (self-hosted agents, Bastion, VPN)

### Network Flow for Private AKS

```
Developer/CI Agent
  └─> VPN / Bastion / Private Network
       └─> Private Endpoint (10.248.x.x)
            └─> AKS API Server
                 └─> Node Pool (VNet subnet)
                      └─> Pods (overlay or VNet IPs)
```

### Terraform Configuration Pattern

```hcl
resource "azurerm_kubernetes_cluster" "aks" {
  private_cluster_enabled       = true
  public_network_access_enabled = false
  private_dns_zone_id           = azurerm_private_dns_zone.aks.id

  network_profile {
    network_plugin      = "azure"    # or "none" for CNI Overlay
    network_plugin_mode = "overlay"  # for CNI Overlay
    pod_cidr            = "10.244.0.0/16"
    service_cidr        = "10.245.0.0/16"
    dns_service_ip      = "10.245.0.10"
  }
}
```

## AKS-Specific NSG Rules

### Required Outbound Rules

| Priority | Name | Destination | Port | Protocol | Purpose |
|----------|------|-------------|------|----------|---------|
| 100 | AllowAzureMonitor | AzureMonitor | 443 | TCP | Metrics and logs |
| 110 | AllowMCR | MicrosoftContainerRegistry | 443 | TCP | Pull system images |
| 120 | AllowACR | AzureContainerRegistry | 443 | TCP | Pull application images |
| 130 | AllowAzureAD | AzureActiveDirectory | 443 | TCP | Authentication |
| 140 | AllowNTP | * | 123 | UDP | Time synchronization |
| 150 | AllowAzureCloud | AzureCloud | 443 | TCP | Azure platform services |
| 160 | AllowDNS | * | 53 | TCP/UDP | DNS resolution |

### Required Inbound Rules

| Priority | Name | Source | Port | Protocol | Purpose |
|----------|------|--------|------|----------|---------|
| 100 | AllowLBProbes | AzureLoadBalancer | * | * | Health probes |
| 110 | AllowVNetInbound | VirtualNetwork | * | * | Intra-VNet communication |

### Service Tags for AKS

| Service Tag | Purpose | When Required |
|-------------|---------|---------------|
| AzureCloud | All Azure platform traffic | Always |
| AzureContainerRegistry | ACR image pulls | When using ACR |
| MicrosoftContainerRegistry | MCR system image pulls | Always |
| AzureMonitor | Monitoring and diagnostics | Always (for Container Insights) |
| AzureActiveDirectory | AAD authentication | Always |
| AzureLoadBalancer | Load balancer health probes | Always |
| VirtualNetwork | Intra-VNet traffic | Always |
| AzureKeyVault | Key Vault access | When using CSI secret store |

## Integration with This Project (10.248.0.0/20)

### Available Space for AKS

Based on current allocation analysis:

```
VNet: 10.248.0.0/20 (4,096 IPs total)

Currently allocated:
  GatewaySubnet:      10.248.0.0/22   (1,024 IPs)
  PublicSubnet:        10.248.4.0/22   (1,024 IPs)
  AzureBastionSubnet: 10.248.8.0/26   (64 IPs)
  PrivateSubnet:      10.248.9.0/24   (256 IPs)

Best fit for AKS: 10.248.10.0/23 (512 IPs, 507 usable)
```

### What 10.248.10.0/23 Supports

| CNI Model | Max Nodes | Max Pods (total) | Notes |
|-----------|-----------|-------------------|-------|
| Azure CNI (30 pods/node) | 16 | 480 | IP-hungry: 31 IPs per node |
| Azure CNI (10 pods/node) | 46 | 460 | Reduced pod density |
| Kubenet | 507 | 55,770 | Only node IPs from VNet |
| CNI Overlay | 507 | 126,750 | Best density, overlay pods |
| CNI + Cilium | 507 | 126,750 | Same density + eBPF benefits |

### Recommendation for This Project

- **CNI Overlay** at 10.248.10.0/23 supports up to 507 nodes with 250 pods each
- Pod CIDR: 10.244.0.0/16 (no overlap with 10.248.0.0/20)
- Service CIDR: 10.245.0.0/16 (no overlap)
- DNS Service IP: 10.245.0.10

## Sizing Examples

### Small Cluster (10 Nodes)

| CNI Model | Node Subnet | Pod CIDR | Service CIDR | Total VNet IPs |
|-----------|-------------|----------|-------------|---------------|
| Azure CNI | /26 (64 IPs) | N/A (VNet) | 10.245.0.0/20 | 315 (node+pod) |
| Kubenet | /28 (16 IPs) | 10.244.0.0/20 | 10.245.0.0/20 | 15 |
| CNI Overlay | /28 (16 IPs) | 10.244.0.0/20 | 10.245.0.0/20 | 15 |
| CNI + Cilium | /28 (16 IPs) | 10.244.0.0/20 | 10.245.0.0/20 | 15 |

### Medium Cluster (50 Nodes)

| CNI Model | Node Subnet | Pod CIDR | Service CIDR | Total VNet IPs |
|-----------|-------------|----------|-------------|---------------|
| Azure CNI | /21 (2,048 IPs) | N/A (VNet) | 10.245.0.0/18 | 1,555 |
| Kubenet | /26 (64 IPs) | 10.244.0.0/18 | 10.245.0.0/20 | 55 |
| CNI Overlay | /26 (64 IPs) | 10.244.0.0/18 | 10.245.0.0/20 | 55 |
| CNI + Cilium | /26 (64 IPs) | 10.244.0.0/18 | 10.245.0.0/20 | 55 |

### Large Cluster (100 Nodes)

| CNI Model | Node Subnet | Pod CIDR | Service CIDR | Total VNet IPs |
|-----------|-------------|----------|-------------|---------------|
| Azure CNI | /20 (4,096 IPs) | N/A (VNet) | 10.245.0.0/17 | 3,105 |
| Kubenet | /25 (128 IPs) | 10.244.0.0/17 | 10.245.0.0/20 | 105 |
| CNI Overlay | /25 (128 IPs) | 10.244.0.0/17 | 10.245.0.0/20 | 105 |
| CNI + Cilium | /25 (128 IPs) | 10.244.0.0/17 | 10.245.0.0/20 | 105 |

## AKS Anti-Patterns

### 1. Using Azure CNI When You Do Not Need VNet-Routable Pods

Azure CNI consumes one VNet IP per pod. A 100-node cluster with 30 pods/node needs 3,105 IPs. CNI Overlay needs 105. Unless you require pods to be directly addressable from the VNet (e.g., legacy integration), use CNI Overlay.

### 2. Undersizing the Node Subnet

Leaving no room for node pool scaling causes autoscaler failures. Always size for 2x expected peak nodes.

### 3. Overlapping Pod CIDR with VNet or Peered Networks

The cluster will fail to deploy or pods will have unreachable IPs. Validate all CIDRs with `network-calc.py validate` before applying.

### 4. Using Kubenet for Production

Kubenet requires manual UDR management, has lower max pod counts (110), does not support Windows nodes, and lacks dual-stack. Use CNI Overlay instead.

### 5. Public API Server in Production

Exposing the API server to the internet is a critical security risk. Always use private clusters for production.

### 6. Hardcoding Service Tag IPs

Azure service tag IP ranges change. Always use service tags (e.g., `AzureCloud`) in NSG rules rather than hardcoded IP addresses.

### 7. Ignoring Cluster DNS Resolution

Private clusters need DNS resolution for the API server. Without a properly linked private DNS zone, kubectl commands fail from outside the cluster VNet.

### 8. Single Subnet for Multiple Node Pools

Using one subnet for system and user node pools prevents independent NSG rules and scaling. Use separate subnets for different pool types when security isolation is required.

### 9. No Egress Control

Allowing unrestricted outbound from AKS nodes is a data exfiltration risk. Use NAT Gateway for controlled egress and NSG rules with service tags to restrict destinations.

### 10. Skipping Network Policy

Running without network policy means any pod can reach any other pod. Enable Calico or Cilium network policy from day one -- retrofitting is painful.
