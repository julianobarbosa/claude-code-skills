# Workflow: Add DAX Measure

Add a new DAX measure to the _Measures table.

## Step 1: Identify the Measure Category

Choose a displayFolder:

| Category | Folder Name | Typical Measures |
|----------|------------|------------------|
| Cost aggregation | Custo | SUM, CALCULATE with filters |
| Variance/comparison | Variacao | MoM %, YoY %, period comparisons |
| Budget | Orcamento | Budget vs actual, utilization % |
| Analytics | Analytics | Moving averages, projections, trends |
| Anomaly detection | Anomalias | Statistical outlier flags |
| Balance/commitment | Balance | EA balance, overage amounts |
| Compliance | Conformidade Tags | Tag coverage percentages |
| Reservation | Reservas | RI utilization, coverage, savings |
| Internal helpers | _Helpers | Conditional formatting, row counts |

## Step 2: Write the Measure

Add to `tables/_Measures.tmdl` under the appropriate section.

### Template

```
measure 'Measure Name' =
    <DAX expression>
    formatString: <format>
    displayFolder: <folder>
    lineageTag: m-measure-name-kebab
```

### Common Patterns

**Simple aggregation:**
```
measure 'Total Cost' =
    SUM(Fact_Usage[PretaxCost])
    formatString: R$ #,##0.00
    displayFolder: Custo
    lineageTag: m-total-cost
```

**With USERELATIONSHIP (for inactive relationships):**
```
measure 'Marketplace Cost' =
    CALCULATE(
        SUM(Fact_Marketplace[PretaxCost]),
        USERELATIONSHIP(Fact_Marketplace[DateKey], Dim_Date[Date])
    )
    formatString: R$ #,##0.00
    displayFolder: Custo
    lineageTag: m-marketplace-cost
```

**Safe percentage with VAR/RETURN:**
```
measure 'Variance %' =
    VAR Current = [Current Measure]
    VAR Previous = [Previous Measure]
    RETURN
        IF(
            Previous <> 0,
            DIVIDE(Current - Previous, Previous),
            BLANK()
        )
    formatString: 0.0%;-0.0%;0.0%
    displayFolder: Variacao
    lineageTag: m-variance-pct
```

**Time intelligence:**
```
measure 'MTD Cost' =
    CALCULATE([Combined Cost], DATESMTD(Dim_Date[Date]))
    formatString: R$ #,##0.00
    displayFolder: Custo
    lineageTag: m-mtd-cost
```

**Counting with filter:**
```
measure 'Non-Compliant Count' =
    COUNTROWS(FILTER(Dim_ResourceGroup, Dim_ResourceGroup[TagsCompletas] = FALSE()))
    formatString: 0
    displayFolder: Conformidade Tags
    lineageTag: m-non-compliant-count
```

**Placeholder (data not yet available):**
```
measure 'RI Coverage %' =
    BLANK()
    formatString: 0.0%
    displayFolder: Reservas
    lineageTag: m-ri-coverage
    annotation note = "Placeholder - requires Reservation Details export data"
```

## Step 3: Format String Reference

| Data Type | Format String | Example Output |
|-----------|--------------|----------------|
| BRL currency | `R$ #,##0.00` | R$ 1.458.793,00 |
| USD currency | `$ #,##0.00` | $ 1,458,793.00 |
| Percentage | `0.0%;-0.0%;0.0%` | 12.5% / -3.2% / 0.0% |
| Integer | `#,##0` | 1,234 |
| Count | `0` | 42 |
| Decimal | `#,##0.00` | 1,234.56 |

The three-part percentage format handles positive, negative, and zero values.

## Step 4: lineageTag Convention

- Prefix: `m-` for all measures
- Kebab-case: `m-custo-total`, `m-variacao-mom`, `m-conf-executivo`
- Must be unique across the entire model
- Keep it descriptive but concise

## Checklist

- [ ] Measure added to _Measures.tmdl
- [ ] Correct formatString for the data type
- [ ] displayFolder assigned
- [ ] Unique lineageTag with m- prefix
- [ ] Uses DIVIDE() instead of / for safe division
- [ ] Uses USERELATIONSHIP() if accessing inactive relationship
- [ ] VAR/RETURN pattern for multi-step calculations
- [ ] BLANK() returned for edge cases (not 0 or error)
