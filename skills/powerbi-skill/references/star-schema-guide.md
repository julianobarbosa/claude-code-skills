# Star Schema Guide for Power BI

## Why Star Schema

Power BI's DAX engine is optimized for star schemas:
- **Performance**: Columnar storage + star schema = fast aggregations
- **DAX simplicity**: Time intelligence, CALCULATE filters, and USERELATIONSHIP all assume M:1 relationships
- **Slicer behavior**: One-direction cross-filtering from dimension to fact works naturally
- **Maintainability**: Clear separation of "what happened" (facts) vs "how to slice it" (dimensions)

## Fact Table Design

Facts store measurements — things you count, sum, or average.

### Grain Definition
Define the finest level of detail before designing:
- Fact_Usage: "One row per meter per resource per day"
- Fact_Marketplace: "One row per marketplace meter per day"
- Fact_Balance: "One row per billing period (monthly)"

### Required Elements
- **Foreign keys** to each dimension (DateKey, SubscriptionGuid, ResourceGroup, etc.)
- **Numeric columns** for aggregation (PretaxCost, ConsumedQuantity)
- **DateKey column** for the Dim_Date relationship

### Anti-patterns
- Don't store descriptive text in facts (put it in dimensions)
- Don't pre-aggregate (keep the finest grain)
- Don't duplicate dimension attributes in facts

## Dimension Table Design

Dimensions store descriptive attributes for filtering and grouping.

### Derivation Patterns

**From fact table** (most common):
```m
Table.Distinct(Table.SelectColumns(Fact_Usage, {"SubscriptionGuid", "SubscriptionName"}))
```

**Generated** (calendar):
```m
// Generate date range with locale-specific attributes
List.Dates(#date(2024,1,1), DayCount, #duration(1,0,0,0))
```

**Manual** (budget, targets):
```m
#table(type table [Period=text, Amount=number], {{"202601", 1000000}})
```

**Enriched** (tags, classification):
```m
// Derive from fact, then add parsed tags and compliance flags
Table.Distinct(...) → AddTag → AddCompliance
```

### Key Decisions
- Use natural keys (SubscriptionGuid) when they're stable and unique
- Use surrogate keys (integer) when natural keys are long or composite
- Always have a "missing" row for orphaned fact records: `"(sem grupo)"`, `"(nao atribuido)"`

## Relationship Rules

```
                    ┌──────────────┐
                    │  Dim_Date    │
                    │  (Calendar)  │
                    └──────┬───────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
┌───────┴────────┐  ┌──────┴────────┐  ┌──────┴──────────┐
│  Fact_Usage    │  │Fact_Marketplace│  │  Fact_Balance   │
│  (ACTIVE→Date) │  │ (INACTIVE)    │  │  (INACTIVE)     │
└───────┬────────┘  └──────┬────────┘  └─────────────────┘
        │                  │
   ┌────┴────┐        ┌───┴────┐
   │         │        │        │
┌──┴─────┐┌──┴────┐┌──┴──────┐│
│Dim_Sub ││Dim_RG ││Dim_Pub  ││
│        ││       ││lisher   ││
└────────┘└───┬───┘└─────────┘│
              │               │
         ┌────┴────┐          │
         │Dim_Svc  │          │
         └─────────┘     ┌────┴─────┐
                         │Dim_Budget│
                         └──────────┘
```

### Rule 1: All M:1 from Fact to Dimension

```
// CORRECT
relationship Fact_Usage_to_Dim_Date
    fromColumn: Fact_Usage.DateKey       // Many side
    toColumn: Dim_Date.Date              // One side
    crossFilteringBehavior: oneDirection
```

### Rule 2: One Active Relationship Per Path

When multiple fact tables share Dim_Date:
- Fact_Usage → Dim_Date: **ACTIVE** (most queried)
- Fact_Marketplace → Dim_Date: **INACTIVE** (`isActive: false`)
- Fact_Balance → Dim_Date: **INACTIVE**
- Dim_Budget → Dim_Date: **INACTIVE**

### Rule 3: USERELATIONSHIP for Inactive

Every measure touching an inactive relationship must wrap in CALCULATE:

```dax
measure 'Custo Marketplace' =
    CALCULATE(
        SUM(Fact_Marketplace[PretaxCost]),
        USERELATIONSHIP(Fact_Marketplace[DateKey], Dim_Date[Date])
    )
```

### Rule 4: One-Direction Cross-Filtering

Always `crossFilteringBehavior: oneDirection`. Bidirectional cross-filtering:
- Causes ambiguous filter propagation
- Can produce incorrect totals
- Breaks DAX expectations

## Multiple Fact Tables

When facts share dimensions:

1. Create the dimension once (derive from the primary fact)
2. Add FK columns to all fact tables that reference it
3. Make the primary fact's relationship active, others inactive
4. Write USERELATIONSHIP measures for inactive paths

Shared dimensions in a FinOps model:
- **Dim_Date**: shared by Fact_Usage (active), Fact_Marketplace, Fact_Balance, Dim_Budget (all inactive)
- **Dim_Subscription**: shared by Fact_Usage (active), Fact_Marketplace (inactive)
- **Dim_ResourceGroup**: shared by Fact_Usage (active), Fact_Marketplace (inactive)

## Calendar Table (Dim_Date)

Every model needs one. Requirements:
- Continuous dates (no gaps) covering the full data range
- isKey: true on the Date column
- Sort columns: AnoMes (YYYYMM) for proper month ordering
- Localized: month names, day names, quarter labels in the project language

## Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| Snowflaking | Dim → Dim chains break DAX filter context | Flatten into single dimension |
| Bidirectional cross-filter | Ambiguous paths, wrong totals | Always oneDirection |
| Many-to-Many without bridge | Duplicated rows in aggregation | Add bridge table or redesign |
| Calculated columns for measures | Wastes memory, can't be filtered | Use DAX measures instead |
| Multiple active paths to same dim | TMDL error / ambiguous | Only one active per path |
| Dates in fact without calendar | No time intelligence | Always add Dim_Date |
| Pre-aggregated facts | Lose detail, can't drill down | Keep finest grain |
