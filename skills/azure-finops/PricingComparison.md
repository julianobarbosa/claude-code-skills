# Pricing Comparison Methodology

Standard methodology for comparing Pay-As-You-Go (PAYG) vs Reserved Instance (RI) pricing.

## Using mcp__azure__pricing

```
mcp__azure__pricing → pricing_get
  Parameters:
    service_name: "Virtual Machines" | "SQL Database" | "Storage" | etc.
    sku_name: "Standard_D32s_v5" | "P50" | etc.
    region: "eastus" | "brazilsouth" | etc.
    currency: "BRL" | "USD"
```

Always request pricing in BRL for Brazilian stakeholders. Include USD for reference if needed.

## Savings Calculation Formula

```
Monthly PAYG Cost = hourly_rate * 730 (hours/month)
Monthly 1yr RI Cost = annual_price / 12
Monthly 3yr RI Cost = triennial_price / 36

Monthly Savings (1yr) = Monthly PAYG - Monthly 1yr RI
Monthly Savings (3yr) = Monthly PAYG - Monthly 3yr RI
Savings Percentage = (Monthly Savings / Monthly PAYG) * 100
Annual Savings = Monthly Savings * 12
```

## Typical RI Savings by Service Type

| Service | 1-Year RI Savings | 3-Year RI Savings | Notes |
|---------|-------------------|-------------------|-------|
| Virtual Machines (general) | 20-40% | 50-72% | Varies heavily by series |
| VM MSv2 (SAP HANA) | ~42% | ~72% | High absolute savings due to cost |
| Microsoft Fabric | ~40% | — | Check current availability |
| Azure SQL Database | 25-40% | 50-65% | PaaS only |
| Premium SSD Managed Disks | ~5% | — | Low savings, consider right-sizing |
| Blob Storage Reserved Capacity | 20-26% | 30-38% | Tiered by commitment size (1TB/10TB/100TB) |
| Azure Files | 20-36% | 29-36% | Depends on tier and redundancy |
| App Service | 30-55% | 50-65% | Premium v3 plans |

## Pricing Report Format

For each service analyzed, present:

```markdown
| Attribute | Value |
|-----------|-------|
| Service | {service name and SKU} |
| Region | {region} |
| Monthly PAYG | BRL {amount} |
| Monthly 1yr RI | BRL {amount} ({savings_pct}% savings) |
| Monthly 3yr RI | BRL {amount} ({savings_pct}% savings) |
| Recommended Term | {1yr or 3yr} — {reasoning} |
| Annual Savings | BRL {amount} |
```

## When to Recommend Each Term

| Signal | Recommended Term |
|--------|-----------------|
| Workload stable for 3+ years (SAP, core infra) | 3-year RI |
| Workload stable but uncertain long-term | 1-year RI |
| Variable/seasonal workload | Savings Plan or no RI |
| Workload being migrated/decommissioned | No RI |
| Disk with potential right-sizing opportunity | Right-size first, then RI |

## Common Pricing Pitfalls

1. **Comparing wrong SKU:** Ensure the pricing SKU matches exactly what billing shows
2. **Region mismatch:** Prices vary significantly by region (brazilsouth often 20-40% more than eastus)
3. **Currency fluctuation:** BRL prices change with exchange rates — always use current pricing
4. **Instance size flexibility:** A reservation for a larger VM can cover multiple smaller ones at ratio
5. **Cancelled reservations:** Former reservations that were cancelled still show in order history but provide zero savings
