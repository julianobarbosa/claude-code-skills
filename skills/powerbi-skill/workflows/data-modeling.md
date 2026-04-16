# Workflow: Data Modeling (Star Schema)

Design and implement a star schema data model in PBIP.

## Step 1: Identify Fact Tables

Each fact table represents a business process or measurement:

| Question | Answer → Fact Table |
|----------|-------------------|
| What are we measuring? | Usage costs → Fact_Usage |
| What are the marketplace charges? | 3P costs → Fact_Marketplace |
| What is the EA commitment balance? | Monthly summary → Fact_Balance |

**Grain**: Define the finest level of detail. E.g., "one row per meter per resource per day."

## Step 2: Identify Dimensions

For each fact table, identify the axes of analysis:

| Axis | Dimension | Key Column |
|------|-----------|-----------|
| When? | Dim_Date | Date/DateKey |
| Which subscription? | Dim_Subscription | SubscriptionGuid |
| Which resource group? | Dim_ResourceGroup | ResourceGroup |
| Which service? | Dim_Service | MeterCategory |
| Which publisher? | Dim_Publisher | PublisherName |
| What budget? | Dim_Budget | BillingDate |

## Step 3: Define Relationships

All relationships must be **Many-to-One (M:1)** from fact to dimension.

### Rules

1. **One-direction cross-filtering** — always `crossFilteringBehavior: oneDirection`
2. **One active relationship per path** — if two fact tables share Dim_Date, only one can be active. The other uses `isActive: false`.
3. **USERELATIONSHIP in DAX** — measures that need inactive relationships use `CALCULATE(..., USERELATIONSHIP(Fact.FK, Dim.PK))`

### Active vs Inactive Decision

When multiple fact tables share a dimension:

```
Fact_Usage → Dim_Date     (ACTIVE)
Fact_Marketplace → Dim_Date (INACTIVE — use USERELATIONSHIP)
Fact_Balance → Dim_Date    (INACTIVE — use USERELATIONSHIP)
Dim_Budget → Dim_Date      (INACTIVE — use USERELATIONSHIP)
```

The most frequently queried fact table gets the active relationship.

## Step 4: Write relationships.tmdl

```
// Star Schema Relationships

// === Fact_Usage (active relationships) ===
relationship Fact_Usage_to_Dim_Date
    fromColumn: Fact_Usage.DateKey
    toColumn: Dim_Date.Date
    crossFilteringBehavior: oneDirection

relationship Fact_Usage_to_Dim_Subscription
    fromColumn: Fact_Usage.SubscriptionGuid
    toColumn: Dim_Subscription.SubscriptionGuid
    crossFilteringBehavior: oneDirection

// === Fact_Marketplace (inactive — use USERELATIONSHIP) ===
relationship Fact_Marketplace_to_Dim_Date
    fromColumn: Fact_Marketplace.DateKey
    toColumn: Dim_Date.Date
    isActive: false
    crossFilteringBehavior: oneDirection
```

## Step 5: Shared Dimensions

When the same dimension serves multiple fact tables:

1. Create the dimension once (derived from the primary fact table)
2. Ensure the FK column exists in all fact tables that reference it
3. Make the PQ expression source the primary fact for derivation
4. Add relationships from each fact table to the shared dimension

## Step 6: Calendar Table (Dim_Date)

Every model needs a calendar table. Generate it in PQ covering the full date range:

- Start: earliest date in data (or a fixed start like 2024-01-01)
- End: latest date in data + 1 year
- Include: Year, Month, MonthName, Quarter, DayOfWeek, IsBusinessDay
- Localize: Portuguese month/day names for Brazilian projects

Mark the Date column as `isKey: true` in the TMDL.

## Validation Checklist

- [ ] All relationships are M:1 (from fact to dimension)
- [ ] Cross-filtering is one-direction everywhere
- [ ] Only one active relationship per dimension-to-fact path
- [ ] Inactive relationships have corresponding USERELATIONSHIP measures
- [ ] Every fact table has a DateKey → Dim_Date relationship
- [ ] Dim_Date covers the full date range of all fact tables
- [ ] No circular relationships
- [ ] No bidirectional cross-filtering
- [ ] No snowflake chains (dimension → dimension)
