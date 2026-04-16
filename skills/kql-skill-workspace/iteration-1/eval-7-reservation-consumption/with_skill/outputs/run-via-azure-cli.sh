#!/usr/bin/env bash
# =============================================================================
# Azure Reservations Consumption — Azure CLI Execution Guide
# =============================================================================
# Prerequisites:
#   - Azure CLI >= 2.50.0
#   - az extension: resource-graph  (`az extension add --name resource-graph`)
#   - Authenticated: `az login` (or service principal / managed identity)
#   - Role: Reader on the reservation orders OR Reservation Reader built-in role
# =============================================================================

# ---------------------------------------------------------------------------
# 0. Install the Resource Graph extension (one-time)
# ---------------------------------------------------------------------------
az extension add --name resource-graph --upgrade

# ---------------------------------------------------------------------------
# 1. Run Part 1 — Reservation inventory with utilization
#    Output the top-level reservation list with utilization % to a JSON file
# ---------------------------------------------------------------------------
QUERY_PART1='
resources
| where type =~ "microsoft.capacity/reservationorders/reservations"
| extend
    ReservationName      = tostring(name),
    ReservationId        = tostring(id),
    Sku                  = tostring(sku.name),
    Quantity             = toint(properties.quantity),
    ReservationState     = tostring(properties.provisioningState),
    ExpiryDate           = todatetime(properties.expiryDate),
    PurchaseDate         = todatetime(properties.purchaseDate),
    ReservedResourceType = tostring(properties.reservedResourceType),
    Scope                = tostring(properties.appliedScopeType),
    AppliedScopes        = tostring(properties.appliedScopes),
    UtilizationRaw       = properties.utilizationAggregates
| mv-expand UtilizationEntry = UtilizationRaw
| where tostring(UtilizationEntry.grain) =~ "P7D" or isnull(UtilizationEntry)
| extend UtilizationPct = round(todouble(UtilizationEntry.value) * 100, 2)
| extend IsUnderutilized = iff(UtilizationPct < 80, true, false)
| project ReservationName, Sku, ReservedResourceType, Quantity,
          Scope, AppliedScopes, ReservationState,
          UtilizationPct, IsUnderutilized, PurchaseDate, ExpiryDate
| sort by UtilizationPct asc
'

az graph query \
  --graph-query "$QUERY_PART1" \
  --output json \
  > reservation-inventory.json

echo "Reservation inventory written to reservation-inventory.json"

# ---------------------------------------------------------------------------
# 2. Run Part 1 from a .kql file (cleaner for CI/automation)
#    Extract just the Part 1 block from the full .kql file, or keep a
#    dedicated single-query file.
# ---------------------------------------------------------------------------
# az graph query \
#   --graph-query "$(cat reservation-inventory-only.kql)" \
#   --output json > reservation-inventory.json

# ---------------------------------------------------------------------------
# 3. Paginate large result sets (ARG returns max 1,000 rows per call)
#    Use --skip-token returned from the previous response.
# ---------------------------------------------------------------------------
FIRST_PAGE=$(az graph query \
  --graph-query "$QUERY_PART1" \
  --output json)

echo "$FIRST_PAGE" | jq '.data' > page1.json

SKIP_TOKEN=$(echo "$FIRST_PAGE" | jq -r '."$skipToken" // empty')

if [ -n "$SKIP_TOKEN" ]; then
  az graph query \
    --graph-query "$QUERY_PART1" \
    --skip-token "$SKIP_TOKEN" \
    --output json | jq '.data' >> page1.json
  echo "Additional page retrieved with skip token."
fi

# ---------------------------------------------------------------------------
# 4. Filter to a specific subscription (narrow scope)
# ---------------------------------------------------------------------------
SUBSCRIPTION_ID="<your-subscription-id>"

az graph query \
  --graph-query "$QUERY_PART1" \
  --subscriptions "$SUBSCRIPTION_ID" \
  --output table

# ---------------------------------------------------------------------------
# 5. Output as table for quick review in terminal
# ---------------------------------------------------------------------------
az graph query \
  --graph-query "$QUERY_PART1" \
  --output table

# ---------------------------------------------------------------------------
# 6. Export to CSV using jq post-processing
# ---------------------------------------------------------------------------
az graph query \
  --graph-query "$QUERY_PART1" \
  --output json \
  | jq -r '
      .data
      | (.[0] | keys_unsorted) as $cols
      | [$cols | join(",")],
        (.[] | [.[$cols[]]] | @csv)
      | .
    ' \
  > reservation-inventory.csv

echo "CSV exported to reservation-inventory.csv"

# ---------------------------------------------------------------------------
# 7. Run Part 2 — Resources consuming each reservation
#    (Shared-scope example: all VMs in tenant)
# ---------------------------------------------------------------------------
QUERY_PART2='
let reservations = materialize(
    resources
    | where type =~ "microsoft.capacity/reservationorders/reservations"
    | extend
        ReservationName      = tostring(name),
        ReservationId        = tostring(id),
        ReservedResourceType = tostring(properties.reservedResourceType),
        Sku                  = tostring(sku.name),
        Quantity             = toint(properties.quantity),
        Scope                = tostring(properties.appliedScopeType),
        AppliedScopes        = tostring(properties.appliedScopes),
        UtilizationRaw       = properties.utilizationAggregates
    | mv-expand UtilizationEntry = UtilizationRaw
    | where tostring(UtilizationEntry.grain) =~ "P7D" or isnull(UtilizationEntry)
    | extend UtilizationPct = round(todouble(UtilizationEntry.value) * 100, 2)
    | project ReservationName, ReservationId, ReservedResourceType, Sku,
              Quantity, Scope, AppliedScopes, UtilizationPct
);
let typeMap = datatable(ReservedResourceType:string, ArmType:string) [
    "VirtualMachines", "microsoft.compute/virtualmachines",
    "SqlDatabases",    "microsoft.sql/servers/databases",
    "SqlManagedInstances", "microsoft.sql/managedinstances",
    "CosmosDb",        "microsoft.documentdb/databaseaccounts"
];
reservations
| join kind=inner typeMap on ReservedResourceType
| join kind=leftouter (
    resources
    | project ResourceId=tolower(id), ResourceName=tostring(name),
              ResourceType=tolower(type), ResourceLocation=tostring(location),
              ResourceGroup=tostring(resourceGroup), SubscriptionId=tostring(subscriptionId)
    | extend ArmType=ResourceType
) on ArmType
| where Scope =~ "Shared"
    or (Scope =~ "Single" and SubscriptionId =~ extract("/subscriptions/([^/]+)", 1, AppliedScopes))
| project ReservationName, ReservationId, ReservedResourceType,
          ReservationSku=Sku, ReservationQuantity=Quantity, UtilizationPct,
          ConsumingResource=ResourceName, ConsumingResourceId=ResourceId,
          ResourceType, ResourceLocation, ResourceGroup, SubscriptionId
| sort by ReservationName asc, ConsumingResource asc
'

az graph query \
  --graph-query "$QUERY_PART2" \
  --output json \
  > reservation-consumers.json

echo "Reservation consumer mapping written to reservation-consumers.json"

# ---------------------------------------------------------------------------
# 8. Validate query syntax before running at scale
#    Append "| take 0" to check parsing without data transfer
# ---------------------------------------------------------------------------
az graph query \
  --graph-query 'resources | where type =~ "microsoft.capacity/reservationorders/reservations" | take 0' \
  --output json

# ---------------------------------------------------------------------------
# 9. Get utilization via the Consumption API (exact per-reservation usage)
#    This is more precise than ARG for billing-grade consumption data.
# ---------------------------------------------------------------------------
RESERVATION_ORDER_ID="<reservation-order-id>"
RESERVATION_ID="<reservation-id>"

# List reservation summaries (daily grain)
az consumption reservation summary list \
  --reservation-order-id "$RESERVATION_ORDER_ID" \
  --reservation-id "$RESERVATION_ID" \
  --grain daily \
  --output table

# List reservation details (per-instance consumption)
az consumption reservation detail list \
  --reservation-order-id "$RESERVATION_ORDER_ID" \
  --reservation-id "$RESERVATION_ID" \
  --start-date "$(date -u -v-7d +%Y-%m-%d)" \
  --end-date "$(date -u +%Y-%m-%d)" \
  --output json > reservation-details.json

echo "Reservation details (per-resource usage) written to reservation-details.json"

# ---------------------------------------------------------------------------
# 10. List all reservation orders in the tenant
# ---------------------------------------------------------------------------
az reservations reservation-order list --output table

# List reservations within an order
az reservations reservation list \
  --reservation-order-id "$RESERVATION_ORDER_ID" \
  --output table
