# ValidateCosts Workflow

Cross-reference billing costs against active reservations to determine PAYG vs RI coverage.

## Prerequisites

- Read `../AzureToolReference.md` for tool invocation patterns
- Read `../ReservationInventory.md` for SKU matching rules

## Steps

### 1. Parse Target Services

Extract the services/SKUs the user wants validated from their request or from Cost Management data.

### 2. List All Subscriptions

```
mcp__azure__subscription_list → subscription_list
```

Note all subscription IDs for subsequent queries.

### 3. List Active Reservation Orders

```bash
az reservations reservation-order list \
  --query "[].{orderId:name, displayName:displayName, created:createdDateTime}" \
  -o table
```

### 4. Get Reservation Details Per Order

For each reservation order:

```bash
az reservations reservation list \
  --reservation-order-id <ORDER_ID> \
  --query "[].{name:name, sku:sku.name, quantity:quantity, location:location, state:provisioningState, term:properties.term}" \
  -o table
```

### 5. Cross-Reference SKUs

For each target service from step 1:
- Find matching reservation using SKU matching rules from `ReservationInventory.md`
- Check for exact match, instance size flexibility, and common mismatches
- Check reservation state is `Succeeded`
- Check region alignment

### 6. Explain Billing Discrepancies

Common explanations for unexpected costs:
- **Partial month:** New resource provisioned mid-month — first bill is prorated
- **View filter:** Cost Management showing "Actual Cost" vs "Amortized Cost" produces different numbers
- **Monthly billing RI:** Reserved instances with monthly billing look identical to PAYG in cost views
- **Renewal batch:** Multiple reservation renewals processed on same day create a spending spike

### 7. Present Coverage Table

Output format:

```markdown
| # | Service | Monthly (BRL) | RI Coverage | Notes |
|---|---------|--------------|-------------|-------|
| 1 | {service} | {amount} | COVERED / PARTIAL / NO | {explanation} |
```

## Output

- Per-service coverage table with evidence
- Explanation of any billing anomalies
- List of services with no reservation coverage (candidates for CoverageAnalysis workflow)
