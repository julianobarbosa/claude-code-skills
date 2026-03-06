# Azure Tool Reference

Quick reference for all Azure tools used by AzureFinOps workflows.

## MCP Tools (mcp__azure__*)

| Tool | Command | Purpose |
|------|---------|---------|
| `mcp__azure__subscription_list` | `subscription_list` | List all accessible subscriptions |
| `mcp__azure__advisor` | `advisor_recommendation_list` | Cost optimization recommendations |
| `mcp__azure__pricing` | `pricing_get` | PAYG and reserved instance pricing |
| `mcp__azure__compute` | `compute_vm_get`, `compute_vm_list` | VM details and inventory |
| `mcp__azure__sql` | `sql_server_list`, `sql_db_list` | SQL Server and database inventory |
| `mcp__azure__storage` | `storage_account_list` | Storage account details |
| `mcp__azure__monitor` | `monitor_metrics_list` | Resource utilization metrics |

### MCP Tool Invocation Pattern

```
mcp__azure__compute → compute_vm_list
  Parameters: subscription, resource_group (optional)
  Returns: List of VMs with SKU, location, status

mcp__azure__pricing → pricing_get
  Parameters: service_name, sku_name, region
  Returns: PAYG price, 1yr RI price, 3yr RI price
```

## CLI Commands (No MCP Equivalent)

### Reservation Orders

```bash
# List all reservation orders in tenant
az reservations reservation-order list --query "[].{name:name, displayName:displayName, createdDateTime:createdDateTime}" -o table

# List reservations within a specific order
az reservations reservation list --reservation-order-id <ORDER_ID> --query "[].{name:name, sku:sku.name, quantity:quantity, location:location, provisioningState:provisioningState}" -o table
```

### Resource Graph Queries

```bash
# Find orphaned (unattached) managed disks
az graph query -q "Resources | where type =~ 'microsoft.compute/disks' | where managedBy == '' or isnull(managedBy) | project name, resourceGroup, subscriptionId, properties.diskSizeGB, sku.name, location" --first 1000

# Find stopped/deallocated VMs
az graph query -q "Resources | where type =~ 'microsoft.compute/virtualMachines' | where properties.extended.instanceView.powerState.code == 'PowerState/deallocated' | project name, resourceGroup, subscriptionId" --first 1000

# Find unassociated public IPs
az graph query -q "Resources | where type =~ 'microsoft.network/publicipaddresses' | where properties.ipConfiguration == '' or isnull(properties.ipConfiguration) | project name, resourceGroup, subscriptionId" --first 1000
```

## Tool Selection Guide

| Task | Preferred Tool | Why |
|------|---------------|-----|
| Reservation orders/details | `az reservations` CLI | No MCP equivalent exists |
| Orphaned resource queries | `az graph query` CLI | Resource Graph needs full KQL |
| Subscription listing | MCP `subscription_list` | Simpler wrapper |
| Advisor recommendations | MCP `advisor` | Structured output |
| Pricing comparison | MCP `pricing` | Clean API parameters |
| VM/disk/storage lookup | MCP `compute`/`storage` | Typed responses |
| Batch offline analysis | Python CLI (`uv run`) | When MCP/CLI auth unavailable |

## Authentication Notes

- MCP tools use the active Azure CLI session (`az login`)
- CLI commands require `az login` with tenant access
- If auth expires mid-workflow, re-authenticate: `az login --tenant <TENANT_ID>`
- Python CLI fallback reads from exported CSV data when live auth unavailable
