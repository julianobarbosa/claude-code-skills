#!/usr/bin/env bash
# ============================================================
# Azure Reservations Consumption — Azure CLI Commands
# Requires: az CLI + resource-graph extension
# ============================================================

# Install the resource-graph extension if not already present
az extension add --name resource-graph --only-show-errors

# Login (skip if already authenticated)
# az login

# ============================================================
# 1. Reservation Utilization Summary (all reservations)
# ============================================================
echo "=== Reservation Utilization Summary ==="
az graph query -q "
reservationsresources
| where type =~ 'microsoft.capacity/reservationorders/reservations'
| extend
    reservationName   = tostring(name),
    skuName           = tostring(sku.name),
    location          = tostring(location),
    reservedFor       = tostring(properties.reservedResourceType),
    appliedScopeType  = tostring(properties.appliedScopeType),
    quantity          = toint(properties.quantity),
    provisioningState = tostring(properties.provisioningState),
    expiryDate        = tostring(properties.expiryDate),
    utilization_1d    = todouble(properties.utilization.aggregates[0].value),
    utilization_7d    = todouble(properties.utilization.aggregates[1].value),
    utilization_30d   = todouble(properties.utilization.aggregates[2].value)
| project
    reservationName, skuName, location, reservedFor,
    appliedScopeType, quantity, provisioningState, expiryDate,
    utilization_1d_pct=round(utilization_1d,2),
    utilization_7d_pct=round(utilization_7d,2),
    utilization_30d_pct=round(utilization_30d,2)
| order by utilization_30d_pct asc" \
--output table


# ============================================================
# 2. Reservations with Utilization Status Flag
# ============================================================
echo ""
echo "=== Reservation Utilization Status (Healthy/Warning/Critical) ==="
az graph query -q "
reservationsresources
| where type =~ 'microsoft.capacity/reservationorders/reservations'
| extend
    reservationName  = tostring(name),
    skuName          = tostring(sku.name),
    location         = tostring(location),
    reservedFor      = tostring(properties.reservedResourceType),
    utilization_30d  = todouble(properties.utilization.aggregates[2].value),
    expiryDate       = tostring(properties.expiryDate)
| extend utilizationStatus = case(
    utilization_30d >= 90, 'Healthy',
    utilization_30d >= 70, 'Warning',
    'Critical')
| project
    reservationName, skuName, location, reservedFor,
    utilization_30d_pct=round(utilization_30d,2),
    utilizationStatus, expiryDate
| order by utilization_30d_pct asc" \
--output table


# ============================================================
# 3. Resources Consuming Each Reservation (scope join)
# ============================================================
echo ""
echo "=== Resources Consuming Each Reservation ==="
az graph query -q "
reservationsresources
| where type =~ 'microsoft.capacity/reservationorders/reservations'
| extend
    reservationName      = tostring(name),
    reservedResourceType = tostring(properties.reservedResourceType),
    appliedScopeType     = tostring(properties.appliedScopeType),
    appliedScopes        = properties.appliedScopes,
    skuName              = tostring(sku.name),
    utilization_30d      = todouble(properties.utilization.aggregates[2].value)
| mv-expand appliedScope = appliedScopes
| extend appliedScopeStr = tolower(tostring(appliedScope))
| extend
    scopeSubscriptionId = extract('/subscriptions/([^/]+)', 1, appliedScopeStr),
    scopeResourceGroup  = extract('/resourcegroups/([^/]+)', 1, appliedScopeStr)
| join kind=leftouter (
    resources
    | extend
        resourceName   = tostring(name),
        resourceType   = tostring(type),
        resourceRG     = tolower(tostring(resourceGroup)),
        resourceSubId  = tolower(tostring(subscriptionId)),
        resourceSku    = tostring(sku.name),
        resourceRegion = tostring(location)
    | project resourceName, resourceType, resourceRG, resourceSubId, resourceSku, resourceRegion
) on \$left.scopeSubscriptionId == \$right.resourceSubId
| where isnotempty(resourceName)
| project
    reservationName, skuName, reservedResourceType,
    utilization_30d_pct=round(utilization_30d,2),
    scopeSubscriptionId, scopeResourceGroup,
    resourceName, resourceType, resourceSku, resourceRegion, resourceRG
| order by reservationName asc, resourceName asc" \
--output table


# ============================================================
# 4. Reservation Orders Summary
# ============================================================
echo ""
echo "=== Reservation Orders ==="
az graph query -q "
reservationsresources
| where type =~ 'microsoft.capacity/reservationorders'
| extend
    orderName        = tostring(name),
    displayName      = tostring(properties.displayName),
    term             = tostring(properties.term),
    billingPlan      = tostring(properties.billingPlan),
    expiryDate       = tostring(properties.expiryDate),
    requestDateTime  = tostring(properties.requestDateTime),
    reservationCount = array_length(properties.reservations)
| project orderName, displayName, term, billingPlan, reservationCount, expiryDate, requestDateTime
| order by requestDateTime desc" \
--output table


# ============================================================
# 5. Reservations Expiring Within 90 Days
# ============================================================
echo ""
echo "=== Reservations Expiring in Next 90 Days ==="
az graph query -q "
reservationsresources
| where type =~ 'microsoft.capacity/reservationorders/reservations'
| extend
    reservationName = tostring(name),
    skuName         = tostring(sku.name),
    location        = tostring(location),
    reservedFor     = tostring(properties.reservedResourceType),
    expiryDate      = todatetime(properties.expiryDate),
    quantity        = toint(properties.quantity),
    utilization_30d = todouble(properties.utilization.aggregates[2].value)
| where expiryDate >= now() and expiryDate <= now() + 90d
| extend daysUntilExpiry = datetime_diff('day', expiryDate, now())
| project
    reservationName, skuName, location, reservedFor, quantity,
    utilization_30d_pct=round(utilization_30d,2),
    expiryDate, daysUntilExpiry
| order by daysUntilExpiry asc" \
--output table


# ============================================================
# 6. Export all results to JSON (for further processing)
# ============================================================
echo ""
echo "=== Exporting full utilization data to JSON ==="
az graph query -q "
reservationsresources
| where type =~ 'microsoft.capacity/reservationorders/reservations'
| extend
    reservationName  = tostring(name),
    skuName          = tostring(sku.name),
    location         = tostring(location),
    reservedFor      = tostring(properties.reservedResourceType),
    appliedScopeType = tostring(properties.appliedScopeType),
    quantity         = toint(properties.quantity),
    expiryDate       = tostring(properties.expiryDate),
    utilization_1d   = todouble(properties.utilization.aggregates[0].value),
    utilization_7d   = todouble(properties.utilization.aggregates[1].value),
    utilization_30d  = todouble(properties.utilization.aggregates[2].value)
| extend utilizationStatus = case(
    utilization_30d >= 90, 'Healthy',
    utilization_30d >= 70, 'Warning',
    'Critical')
| project reservationName, skuName, location, reservedFor, appliedScopeType,
    quantity, expiryDate,
    utilization_1d_pct=round(utilization_1d,2),
    utilization_7d_pct=round(utilization_7d,2),
    utilization_30d_pct=round(utilization_30d,2),
    utilizationStatus" \
--output json > reservation_utilization_export.json

echo "Exported to reservation_utilization_export.json"
