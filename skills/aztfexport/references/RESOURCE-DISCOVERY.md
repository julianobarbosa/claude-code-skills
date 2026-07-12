# Azure Resource Discovery — CLI Patterns

Azure CLI commands for finding resource IDs by type. All commands output the resource ID needed for `aztfexport resource`.

## Generic Fallback

Works for any resource type when you know the name:

```bash
# By name
az resource list --query "[?name=='RESOURCE_NAME']" -o table

# By name with resource ID only
az resource list --query "[?name=='RESOURCE_NAME'].id" -o tsv

# By type
az resource list --resource-type "Microsoft.Compute/virtualMachines" -o table

# By resource group
az resource list -g RESOURCE_GROUP_NAME -o table
```

## Monitor Alerts

Azure alerts span **3 different API endpoints** — check each if unsure of the alert type:

```bash
# Metric alerts
az monitor metrics alert list -g RG_NAME --query "[?name=='ALERT_NAME'].id" -o tsv

# Scheduled query rules (log alerts)
az monitor scheduled-query list -g RG_NAME --query "[?name=='ALERT_NAME'].id" -o tsv

# Activity log alerts
az monitor activity-log alert list -g RG_NAME --query "[?name=='ALERT_NAME'].id" -o tsv
```

**Tip:** If you don't know which type, run all three in parallel.

## Compute

```bash
# Virtual Machines
az vm list -g RG_NAME --query "[].{name:name, id:id}" -o table

# VM Scale Sets
az vmss list -g RG_NAME --query "[].{name:name, id:id}" -o table

# Disks
az disk list -g RG_NAME --query "[].{name:name, id:id}" -o table
```

## Networking

```bash
# Virtual Networks
az network vnet list -g RG_NAME --query "[].{name:name, id:id}" -o table

# Subnets (need vnet name)
az network vnet subnet list -g RG_NAME --vnet-name VNET_NAME --query "[].{name:name, id:id}" -o table

# Network Security Groups
az network nsg list -g RG_NAME --query "[].{name:name, id:id}" -o table

# Public IPs
az network public-ip list -g RG_NAME --query "[].{name:name, id:id}" -o table

# Load Balancers
az network lb list -g RG_NAME --query "[].{name:name, id:id}" -o table

# Application Gateways
az network application-gateway list -g RG_NAME --query "[].{name:name, id:id}" -o table

# NAT Gateways
az network nat gateway list -g RG_NAME --query "[].{name:name, id:id}" -o table
```

## Storage

```bash
# Storage Accounts
az storage account list -g RG_NAME --query "[].{name:name, id:id}" -o table
```

## Key Vault

```bash
az keyvault list -g RG_NAME --query "[].{name:name, id:id}" -o table
```

## Kubernetes (AKS)

```bash
az aks list -g RG_NAME --query "[].{name:name, id:id}" -o table
```

## Databases

```bash
# Azure SQL Server
az sql server list -g RG_NAME --query "[].{name:name, id:id}" -o table

# Azure SQL Database (need server name)
az sql db list -g RG_NAME -s SERVER_NAME --query "[].{name:name, id:id}" -o table

# CosmosDB
az cosmosdb list -g RG_NAME --query "[].{name:name, id:id}" -o table

# PostgreSQL Flexible Server
az postgres flexible-server list -g RG_NAME --query "[].{name:name, id:id}" -o table
```

## App Services

```bash
# Web Apps / App Services
az webapp list -g RG_NAME --query "[].{name:name, id:id}" -o table

# Function Apps
az functionapp list -g RG_NAME --query "[].{name:name, id:id}" -o table

# App Service Plans
az appservice plan list -g RG_NAME --query "[].{name:name, id:id}" -o table
```

## Container Registry

```bash
az acr list -g RG_NAME --query "[].{name:name, id:id}" -o table
```

## Azure Resource Graph (Cross-Subscription)

For finding resources across multiple subscriptions:

```bash
# By name across all subscriptions
az graph query -q "resources | where name == 'RESOURCE_NAME' | project id, name, type, resourceGroup"

# By type across all subscriptions
az graph query -q "resources | where type == 'microsoft.compute/virtualmachines' | project id, name, resourceGroup"
```

Requires `az extension add --name resource-graph` if not installed.
