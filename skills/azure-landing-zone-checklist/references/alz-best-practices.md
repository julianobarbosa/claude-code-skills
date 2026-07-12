# Azure Landing Zone — Best Practice Recommendations

This reference contains Microsoft Cloud Adoption Framework (CAF) and Well-Architected Framework recommendations for each ALZ Accelerator checklist decision. Use these when the user defers a decision or asks for guidance.

## Table of Contents
- [Bootstrap Settings](#bootstrap-settings)
- [Network Topology](#network-topology)
- [Security & Monitoring](#security--monitoring)
- [Identity & Access](#identity--access)
- [IP Addressing](#ip-addressing)
- [Policy & Governance](#policy--governance)
- [CI/CD Pipeline](#cicd-pipeline)

---

## Bootstrap Settings

### IaC Type: Bicep vs Terraform

Both are fully supported. Key differences:
- **Bicep**: Azure-native, no state management needed, tighter Azure integration
- **Terraform**: Multi-cloud, larger ecosystem, state file management required (but accelerator handles this)

Recommendation: Match the team's existing skillset. If no preference, Terraform has broader community support.

### Version Control System

- **Azure DevOps**: Best for enterprises already using Azure ecosystem, supports private networking with self-hosted agents
- **GitHub**: Best for open-source-friendly teams, GitHub Actions integration
- **Local**: Only for testing/development, not production deployments

Recommendation: Match existing organizational tooling.

### Starter Module

Always use `platform_landing_zone` — it's the comprehensive module that deploys the full ALZ architecture including management groups, policies, connectivity, and identity resources.

### Resource Naming

Default naming (`alz`, `mgmt`, postfix `1`) is suitable for most deployments. Customize only if:
- Organization has strict naming conventions
- Multiple ALZ deployments exist in the same tenant
- Regulatory requirements dictate specific naming patterns

### Parent Management Group

Default (Tenant Root Group) is recommended for initial deployments. Use a custom parent only if:
- The tenant is shared across multiple organizations
- There's an existing management group hierarchy to preserve
- Regulatory isolation requires a separate management group tree

---

## Network Topology

### Hub & Spoke vs Virtual WAN

| Factor | Hub & Spoke | Virtual WAN |
|--------|-------------|-------------|
| Complexity | Simpler, full control | Microsoft-managed routing |
| Cost | Lower for small deployments | Higher base cost, scales better |
| Customization | Full NSG/UDR control | Limited routing customization |
| NVA support | Native | Requires specific integration |
| Best for | Most organizations | Large enterprises with 50+ VNets |

Recommendation: Hub & Spoke for most organizations. vWAN only for very large, multi-region deployments with complex routing needs.

### Single vs Multi-Region

Start with single-region unless:
- Business continuity requires active-active or active-passive across regions
- Data residency laws require resources in multiple geographies
- Latency requirements demand regional proximity to users

Recommendation: Start single-region, expand later. The ALZ architecture supports adding regions incrementally.

### Azure Firewall vs NVA

- **Azure Firewall**: Fully managed, auto-scales, native Azure integration, simpler operations
- **NVA (e.g., Palo Alto, Fortinet)**: Existing vendor relationship, specific feature requirements, existing firewall policies to migrate

Recommendation: Azure Firewall unless the organization has existing NVA investments or specific feature requirements not available in Azure Firewall.

---

## Security & Monitoring

### Azure Monitoring Agent (AMA)

Keep enabled. AMA provides:
- Centralized log collection to Log Analytics
- Data Collection Rules (DCR) for flexible data routing
- Performance monitoring across all deployed resources
- Integration with Azure Monitor alerts and workbooks

Disabling AMA removes visibility into platform health. Only disable if using a third-party monitoring solution that replaces all AMA capabilities.

### Microsoft Defender for Cloud

Keep all plans enabled. Defender provides:
- **Servers**: Vulnerability assessment, endpoint detection, file integrity monitoring
- **Storage**: Malware scanning, anomaly detection on storage accounts
- **SQL/Databases**: SQL injection detection, access anomaly alerts
- **Key Vault**: Unusual access pattern detection, secret enumeration alerts
- **DNS**: DNS tunneling detection, communication with known malicious domains
- **ARM**: Suspicious management plane operations, privilege escalation attempts

The cost of Defender is significantly lower than the cost of a security incident. Only disable specific plans if a third-party tool covers that exact capability.

### Azure Monitor Baseline Alerts (AMBA) — Terraform only

Deploy AMBA policies. They provide out-of-the-box alerting for:
- Platform resource health (VPN Gateway, ExpressRoute, Firewall)
- Service health notifications
- Resource availability metrics

Without AMBA, platform issues may go undetected until users report problems.

### DDoS Protection Plan

Deploy DDoS Protection Plan. It provides:
- Network-layer protection for all public IPs in linked VNets
- Automatic traffic scrubbing during attacks
- Attack analytics and rapid response support
- Cost protection (credits for scale-out during attacks)

Note: DDoS Protection Plan has a monthly base cost (~$2,944/month). For budget-constrained deployments, DDoS Network Protection (per-IP) is an alternative.

### Zero Trust Security

Enable Zero Trust configuration. It enforces:
- Least-privilege access across all management groups
- Micro-segmentation between network tiers
- Continuous verification of identity and device compliance
- NSG/ASG rules that default-deny and explicitly allow required flows

Zero Trust is not an "extra" security layer — it's the baseline architectural pattern that Microsoft recommends for all new Azure deployments.

---

## Identity & Access

### Dedicated Identity Subscription

The Identity subscription hosts:
- Azure AD Domain Services (if needed)
- Domain controllers (if extending on-premises AD)
- DNS forwarders
- Identity-related Private Endpoints

It should be separate from Management and Connectivity to maintain security boundaries.

### Dedicated Security Subscription

A dedicated Security subscription is recommended for:
- Microsoft Sentinel workspace
- Defender for Cloud data
- Security automation (Logic Apps, Functions)
- Security-specific Log Analytics workspace

If budget is constrained, Security workloads can share the Management subscription, but this reduces the security boundary between operations and security teams.

---

## IP Addressing

### Subnet Sizing for Hub VNet

| Subnet | Minimum Size | Recommended | Purpose |
|--------|-------------|-------------|---------|
| GatewaySubnet | /27 | /27 | VPN/ExpressRoute (max 32 IPs, Azure requirement) |
| AzureFirewallSubnet | /26 | /26 | Azure Firewall (64 IPs, supports auto-scale) |
| AzureFirewallManagementSubnet | /26 | /26 | Firewall management (forced tunneling scenarios) |
| AzureBastionSubnet | /26 | /26 | Azure Bastion (supports up to 50 concurrent sessions per /26) |
| Shared Services | /24 | /24 | DNS forwarders, monitoring agents, jump boxes |
| DNS Resolver Inbound | /28 | /28 | Azure DNS Private Resolver inbound endpoint |
| DNS Resolver Outbound | /28 | /28 | Azure DNS Private Resolver outbound endpoint |

### Address Space Planning

- Allocate generously — IP space is free, re-addressing is expensive
- Use /13 per subscription for maximum flexibility (524,288 addresses)
- Use /16 for individual VNets (65,534 addresses)
- Ensure no overlap with on-premises ranges
- Reserve space for future growth (AKS clusters, additional spokes)

### On-Premises Integration

When VPN or ExpressRoute connects to on-premises:
- Document all on-premises CIDR ranges to prevent overlap
- Include on-premises public IPs in firewall/NSG rule comments
- Plan for NAT if overlapping ranges cannot be avoided

---

## Policy & Governance

### Default Policy Assignments

Keep all default ALZ policy assignments. They enforce:
- Allowed resource locations
- Required tags
- Diagnostic settings to Log Analytics
- Network security baseline
- Encryption requirements

Recommendation: Use enforcement mode changes (`DoNotEnforce`) rather than removing policies. This preserves audit trail while allowing exceptions.

### Custom Management Group Names

Use default ALZ management group names unless:
- Organization has strict naming conventions for all Azure resources
- Multiple ALZ deployments exist and need disambiguation
- Regulatory requirements dictate specific naming

Default names are well-documented and recognized by Microsoft support, making troubleshooting easier.

---

## CI/CD Pipeline

### Separate Template Repository

Use a separate repository for CI/CD templates. This:
- Prevents developers from modifying pipeline definitions
- Creates a security boundary between infrastructure code and deployment logic
- Allows pipeline template updates independent of infrastructure changes

### Private Networking for State Storage

Enable private networking for Terraform state storage. This:
- Prevents state files from being accessible over the internet
- State files contain sensitive information (resource IDs, configuration details)
- Required for compliance in most regulated industries

### Self-Hosted Agents/Runners

Use self-hosted agents when private networking is enabled. They:
- Can access private endpoints (storage accounts, Key Vaults)
- Run inside the organization's network boundary
- Provide more control over the execution environment
- Are required when state storage is not publicly accessible

### Branch Policies

Enable branch policies to:
- Require pull requests for all changes to main/production branches
- Enforce code review before infrastructure changes are applied
- Create an audit trail of who approved what changes
- Prevent accidental direct pushes to production

### Pipeline Approvers

Configure at least 2 approvers for the apply stage:
- Ensures no single person can make infrastructure changes unilaterally
- Creates accountability for production-impacting changes
- Required by most compliance frameworks (SOC 2, ISO 27001)
