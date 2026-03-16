# Terraform Snippets

HCL templates matching the existing `rg-hypera-packer-image` repo patterns. Uses AVM (Azure Verified Modules).

## VNet + Subnets Module Block

Uses `Azure/avm-res-network-virtualnetwork/azurerm`. Match the version to the project's current pin.

```hcl
module "virtualnetwork" {
  source  = "Azure/avm-res-network-virtualnetwork/azurerm"
  version = "~> 0.8.0"

  name                = local.vnet_name
  resource_group_name = azurerm_resource_group.RESOURCE_GROUP.name
  location            = azurerm_resource_group.RESOURCE_GROUP.location
  address_space       = var.vnet_address_space
  tags                = local.common_tags

  subnets = {
    "SUBNET_KEY" = {
      name                                          = "SUBNET_NAME"
      address_prefixes                              = var.SUBNET_VAR
      private_link_service_network_policies_enabled = true
      private_endpoint_network_policies_enabled     = true
      service_endpoints = [
        # Add as needed: Microsoft.Sql, Microsoft.Storage, etc.
      ]
      # Optional: NAT Gateway association
      nat_gateway = {
        id = module.avm_nat_gateway.resource_id
      }
      # Optional: NSG association
      network_security_group = {
        id = azurerm_network_security_group.NSG_NAME.id
      }
    }
  }
}
```

### Special Azure Subnet Names

These subnets MUST use exact names — do not apply naming conventions:
- `GatewaySubnet` — VPN/ExpressRoute gateway
- `AzureFirewallSubnet` — Azure Firewall
- `AzureBastionSubnet` — Azure Bastion

## Variable Declarations

Pattern from `variables.tf`:

```hcl
variable "vnet_address_space" {
  description = "VNet address space CIDR"
  type        = list(string)
}

variable "vnet_subnet_PURPOSE" {
  description = "Subnet CIDR for PURPOSE"
  type        = list(string)
}
```

## Naming Locals

Pattern from `name.tf`:

```hcl
locals {
  # VNet
  vnet_name = "vnet-${var.resource_group_name}-${var.environment}-${var.azure_region_shortcode}"

  # Subnets (custom names follow snet- convention)
  subnet_PURPOSE_name = "snet-PURPOSE-${var.resource_group_name}-${var.environment}-${var.azure_region_shortcode}"

  # Azure-mandated names (no convention applied)
  subnet_bastion_name = "AzureBastionSubnet"
  subnet_gateway_name = "GatewaySubnet"  # or snet-gateway-... for non-VPN gateways

  # NSG
  nsg_PURPOSE_name = "nsg-PURPOSE-${var.resource_group_name}-${var.environment}-${var.azure_region_shortcode}"

  # NAT Gateway
  nat_gateway_name     = "natg-${var.resource_group_name}-${var.environment}-${var.azure_region_shortcode}"
  nat_gateway_pip_name = "natg-pip-${var.resource_group_name}-${var.environment}-${var.azure_region_shortcode}"
}
```

## NSG Association

Pattern from `nsg.tf`:

```hcl
resource "azurerm_network_security_group" "PURPOSE-nsg" {
  name                = local.nsg_PURPOSE_name
  location            = azurerm_resource_group.RESOURCE_GROUP.location
  resource_group_name = azurerm_resource_group.RESOURCE_GROUP.name
  tags                = local.common_tags

  # Inbound: Bastion SSH/RDP
  security_rule {
    name                       = "Allow_Bastion_Inbound"
    priority                   = 100
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_ranges    = ["22", "3389"]
    source_address_prefix      = "BASTION_SUBNET_CIDR"
    destination_address_prefix = "*"
  }

  # Outbound: HTTPS, HTTP, DNS
  security_rule {
    name                       = "Allow_HTTPS_Outbound"
    priority                   = 100
    direction                  = "Outbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "443"
    source_address_prefix      = "*"
    destination_address_prefix = "Internet"
  }

  security_rule {
    name                       = "Allow_HTTP_Outbound"
    priority                   = 110
    direction                  = "Outbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_range     = "80"
    source_address_prefix      = "*"
    destination_address_prefix = "Internet"
  }

  security_rule {
    name                       = "Allow_DNS_Outbound"
    priority                   = 120
    direction                  = "Outbound"
    access                     = "Allow"
    protocol                   = "*"
    source_port_range          = "*"
    destination_port_range     = "53"
    source_address_prefix      = "*"
    destination_address_prefix = "Internet"
  }
}
```

## NAT Gateway

Pattern from `natg.tf` using AVM module:

```hcl
module "avm_nat_gateway" {
  source  = "Azure/avm-res-network-natgateway/azurerm"
  version = "0.2.1"

  name                    = local.nat_gateway_name
  location                = azurerm_resource_group.RESOURCE_GROUP.location
  resource_group_name     = azurerm_resource_group.RESOURCE_GROUP.name
  idle_timeout_in_minutes = 4
  sku_name                = "Standard"
  tags                    = local.common_tags
  enable_telemetry        = var.enable_avm_telemetry
  zones                   = null  # Non-zonal for dev; ["1","2","3"] for prd

  public_ip_prefix_length = 0  # Manage prefix externally

  public_ips = {
    "NATG_PIP_KEY" = {
      name = local.nat_gateway_pip_name
    }
  }

  public_ip_configuration = {
    allocation_method       = "Static"
    sku                     = "Standard"
    zones                   = []
    ddos_protection_mode    = "VirtualNetworkInherited"
    idle_timeout_in_minutes = 4
  }
}
```

## AKS Network Profile (Azure CNI Overlay)

```hcl
resource "azurerm_kubernetes_cluster" "aks" {
  # ... other config ...

  network_profile {
    network_plugin      = "azure"
    network_plugin_mode = "overlay"
    service_cidr        = "OVERLAY_SERVICE_CIDR"  # e.g., 172.25.0.0/16
    dns_service_ip      = "OVERLAY_SERVICE_BASE+10"  # e.g., 172.25.0.10
    pod_cidr            = "OVERLAY_POD_CIDR"  # e.g., 172.24.0.0/16
  }
}
```

## tfvars Pattern

```hcl
vnet_address_space = ["VNET_CIDR"]

vnet_subnet_PURPOSE = ["SUBNET_CIDR"]
# Repeat for each subnet
```
