# FindWaste Workflow

Discover orphaned and wasted Azure resources across all subscriptions.

## Prerequisites

- Read `../AzureToolReference.md` for Resource Graph query patterns

## Steps

### 1. Query Orphaned Disks

```bash
az graph query -q "
  Resources
  | where type =~ 'microsoft.compute/disks'
  | where managedBy == '' or isnull(managedBy)
  | project name, resourceGroup, subscriptionId,
            diskSizeGB=properties.diskSizeGB,
            sku=sku.name, location
" --first 1000
```

### 2. Query Stopped VMs

```bash
az graph query -q "
  Resources
  | where type =~ 'microsoft.compute/virtualMachines'
  | where properties.extended.instanceView.powerState.code == 'PowerState/deallocated'
  | project name, resourceGroup, subscriptionId,
            vmSize=properties.hardwareProfile.vmSize, location
" --first 1000
```

### 3. Query Unassociated Public IPs

```bash
az graph query -q "
  Resources
  | where type =~ 'microsoft.network/publicipaddresses'
  | where properties.ipConfiguration == '' or isnull(properties.ipConfiguration)
  | project name, resourceGroup, subscriptionId, location
" --first 1000
```

### 4. Categorize by Type and Size

Group discovered waste by:
- **Disk type:** StandardSSD_LRS, Premium_LRS, Standard_LRS, Premium_ZRS, etc.
- **Disk size:** Small (<128GB), Medium (128-1024GB), Large (>1024GB)
- **Subscription:** Group by subscription for ownership attribution

### 5. Calculate Monthly Waste

For each orphaned resource, estimate cost using:

```
mcp__azure__pricing → pricing_get
  Parameters: service_name, sku_name, region
```

Sum by category and overall.

### 6. Verify Specific Resources (Optional)

If user asks about specific disks (e.g., "are the P50 disks orphaned?"):

```
mcp__azure__compute → compute_vm_get
  Check managedBy field on specific disks
  Cross-reference disk names against VM disk attachments
```

### 7. Present Waste Report

Output format:

```markdown
## Orphaned Resources Summary

| Category | Count | Monthly Waste (BRL) | Annual Waste (BRL) |
|----------|-------|--------------------|--------------------|
| Unattached Disks | {n} | {amount} | {amount} |
| Stopped VMs | {n} | {amount} | {amount} |
| Unused Public IPs | {n} | {amount} | {amount} |
| **Total** | | **{total}** | **{total}** |

### Disk Breakdown

| Disk Type | Count | Est. Monthly (BRL) |
|-----------|-------|--------------------|
| StandardSSD_LRS | {n} | {amount} |
| Premium_LRS | {n} | {amount} |
```

## Output

- Categorized waste report with BRL amounts
- Specific resource details if requested
- Recommendation: cleanup candidates vs resources to investigate further
