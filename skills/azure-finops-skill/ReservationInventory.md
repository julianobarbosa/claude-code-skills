# Reservation Inventory SOP

Standard operating procedure for interpreting Azure reservation data and matching SKUs.

## Order vs Reservation Distinction

- **Reservation Order:** The purchase container. Has an order ID, created date, billing plan.
- **Reservation:** The actual capacity commitment within an order. Has SKU, quantity, location, term.
- One order can contain multiple reservations (rare but possible).
- Always drill from order → reservation to get the actual SKU details.

## SKU Matching Rules

### Exact Match

The reservation SKU exactly matches the billing line item SKU.

```
Billing: Standard_D32s_v5
Reservation: Standard_D32s_v5
Result: COVERED
```

### Instance Size Flexibility

Azure VM reservations within the same series/family can cover different sizes:
- A D16s_v5 reservation covers 2x D8s_v5 or 0.5x D32s_v5
- Flexibility applies ONLY within the same series and region
- Check the instance size flexibility ratio table for exact mappings

### Common Mismatch Patterns

| Billing Line | Reservation SKU | Covered? | Why |
|-------------|----------------|----------|-----|
| SQL Server Enterprise VM License | SQLDB_GP_Compute_Gen5 | NO | IaaS VM license vs PaaS SQL Database |
| Block Blob Hot RA-GRS | Block Blob Cool LRS | NO | Different tier AND redundancy |
| Fabric Compute CU | (none) | NO | No Fabric reservations exist in most tenants |
| Premium SSD P50 | (cancelled reservation) | NO | Cancelled reservations provide zero coverage |
| VM MSv2 M416ms_v2 | Standard_D-series | NO | Different VM family entirely |

### PaaS vs IaaS Distinction

This is the most common source of false "covered" assessments:

- **IaaS SQL:** VM running SQL Server → needs VM reservation + SQL license (or AHB)
- **PaaS SQL:** Azure SQL Database → needs SQLDB reservation (different SKU family)
- A SQLDB reservation NEVER covers an IaaS SQL VM license cost

### Reservation State Interpretation

| State | Meaning |
|-------|---------|
| `Succeeded` | Active and providing coverage |
| `Cancelled` | No longer provides coverage (even if not yet expired) |
| `Expired` | Term ended, no coverage |
| `Processing` | Being provisioned, not yet active |

### Billing Plan Impact

| Plan | How It Appears in Cost Management |
|------|----------------------------------|
| Monthly | Recurring charge each month — looks like regular PAYG |
| Upfront | Large one-time charge in purchase month — easy to spot |
| Mixed | Some upfront + monthly remainder |

Monthly billing reservations are the hardest to distinguish from PAYG in Cost Management views. Always cross-reference against reservation order list.

## Verification Checklist

When asked "is service X covered by a reservation?":

1. List all reservation orders: `az reservations reservation-order list`
2. For each order, get reservation details: `az reservations reservation list`
3. Match the billing SKU against reservation SKUs using rules above
4. Check reservation state is `Succeeded`
5. Check reservation region matches resource region
6. Check reservation quantity vs resource count
7. Report: COVERED / PARTIAL / NOT COVERED with evidence
