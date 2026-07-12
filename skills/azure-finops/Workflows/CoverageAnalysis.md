# CoverageAnalysis Workflow

Full reservation gap analysis with savings projections for uncovered Azure services.

## Prerequisites

- Read `../AzureToolReference.md` for tool invocation patterns
- Read `../ReservationInventory.md` for SKU matching rules
- Read `../PricingComparison.md` for savings calculation methodology

## Steps

### 1. Identify High-Cost Uncovered Services

Source from either:
- User-provided service list
- Output of ValidateCosts workflow (services marked "NO" coverage)
- Cost Management top-N spenders

### 2. List Active Reservations

```bash
az reservations reservation-order list
az reservations reservation list --reservation-order-id <ORDER_ID>
```

Build complete reservation inventory with SKU, quantity, region, state, term.

### 3. Check Each Service for Coverage

For each high-cost service:
- Match against reservation inventory using `ReservationInventory.md` rules
- Classify: COVERED / PARTIAL / NOT COVERED
- For PARTIAL: explain the gap (wrong SKU, wrong tier, insufficient quantity)

### 4. Query Azure Advisor Recommendations

```
mcp__azure__advisor → advisor_recommendation_list
  Filter: category = "Cost"
```

Advisor may recommend specific RI purchases — capture these as independent validation.

### 5. Get PAYG vs RI Pricing

For each uncovered service:

```
mcp__azure__pricing → pricing_get
  Parameters: service_name, sku_name, region, currency="BRL"
```

Calculate savings using formulas from `PricingComparison.md`.

### 6. Locate Actual Resources

Verify resources exist and are active to confirm the spend is real:

```
mcp__azure__compute → compute_vm_list (for VMs)
mcp__azure__sql → sql_server_list (for SQL)
mcp__azure__storage → storage_account_list (for storage)
```

### 7. Present Prioritized Coverage Report

Output format — prioritized by monthly savings (highest first):

```markdown
## Reservation Coverage Analysis

| # | Service | Monthly (BRL) | Coverage | Savings (1yr) | Savings (3yr) |
|---|---------|--------------|----------|---------------|---------------|
| 1 | {service} | {amount} | NO | {amount} ({pct}%) | {amount} ({pct}%) |

## Recommended Actions (Priority Order)

1. **{Service}** — {term} RI saves ~BRL {amount}/month. {reasoning}.
2. ...

## Summary

| Metric | Value |
|--------|-------|
| Total unprotected monthly spend | BRL {amount} |
| Estimated monthly savings (full RI) | BRL {amount} |
| Estimated annual savings | BRL {amount} |
```

## Output

- Per-service coverage status with pricing evidence
- Prioritized reservation purchase recommendations
- Total savings projection (monthly and annual)
- Advisor recommendations cross-referenced against findings
