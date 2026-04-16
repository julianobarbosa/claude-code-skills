# DAX Patterns Reference

Common DAX measure patterns for Power BI, with examples from an Azure FinOps project (BRL, pt-BR).

## Measures Table Pattern

All measures in a dedicated `_Measures` calculated table:

```
table _Measures
    lineageTag: measures-001

    measure 'Custo Total' = SUM(Fact_Usage[PretaxCost])
        formatString: R$ #,##0.00
        displayFolder: Custo
        lineageTag: m-custo-total

    column MeasureColumn
        dataType: int64
        isHidden: true
        lineageTag: measures-col
        summarizeBy: none
        sourceColumn: none

    partition _Measures = calculated
        source = ROW("MeasureColumn", 0)
```

## Core Aggregation

### Simple SUM
```dax
measure 'Custo Total' = SUM(Fact_Usage[PretaxCost])
```

### CALCULATE with USERELATIONSHIP
For inactive relationships (multiple fact tables sharing a dimension):
```dax
measure 'Custo Marketplace' =
    CALCULATE(
        SUM(Fact_Marketplace[PretaxCost]),
        USERELATIONSHIP(Fact_Marketplace[DateKey], Dim_Date[Date])
    )
```

### Combining Measures
```dax
measure 'Custo Combinado' = [Custo Total] + [Custo Marketplace]
```

## Time Intelligence

### Month-to-Date
```dax
measure 'Custo Mes Atual' =
    CALCULATE([Custo Combinado], DATESMTD(Dim_Date[Date]))
```

### Previous Month
```dax
measure 'Custo Mes Anterior' =
    CALCULATE([Custo Combinado], PREVIOUSMONTH(Dim_Date[Date]))
```

### Same Period Last Year
```dax
measure 'Custo Mesmo Mes Ano Anterior' =
    CALCULATE([Custo Combinado], SAMEPERIODLASTYEAR(Dim_Date[Date]))
```

### Year-to-Date
```dax
measure 'Custo YTD' =
    CALCULATE([Custo Combinado], DATESYTD(Dim_Date[Date]))
```

### YTD vs Prior Year YTD
```dax
measure 'Custo YTD Ano Anterior' =
    CALCULATE([Custo YTD], SAMEPERIODLASTYEAR(Dim_Date[Date]))
```

## Safe Division & Variance

Always use VAR/RETURN with DIVIDE or IF for safe division:

### Month-over-Month %
```dax
measure 'Variacao MoM %' =
    VAR CustoAtual = [Custo Mes Atual]
    VAR CustoAnterior = [Custo Mes Anterior]
    RETURN
        IF(
            CustoAnterior <> 0,
            DIVIDE(CustoAtual - CustoAnterior, CustoAnterior),
            BLANK()
        )
```

### Year-over-Year %
```dax
measure 'Variacao YoY %' =
    VAR CustoAtual = [Custo Combinado]
    VAR CustoAnoAnterior = [Custo Mesmo Mes Ano Anterior]
    RETURN
        IF(
            CustoAnoAnterior <> 0,
            DIVIDE(CustoAtual - CustoAnoAnterior, CustoAnoAnterior),
            BLANK()
        )
```

### Budget Utilization %
```dax
measure 'Utilizacao Orcamento %' =
    IF([Orcamento] <> 0, DIVIDE([Custo Combinado], [Orcamento]), BLANK())
```

## Rolling Statistics

### 3-Month Moving Average
```dax
measure 'Media Movel 3M' =
    AVERAGEX(
        DATESINPERIOD(Dim_Date[Date], MAX(Dim_Date[Date]), -3, MONTH),
        CALCULATE([Custo Combinado])
    )
```

### Standard Deviation (for anomaly detection)
```dax
VAR Dates3M = DATESINPERIOD(Dim_Date[Date], MAX(Dim_Date[Date]), -3, MONTH)
VAR StdDev = STDEVX.P(Dates3M, CALCULATE([Custo Combinado]))
```

## Anomaly Detection

Flag costs that deviate significantly from the rolling average:

### Anomaly Flag (>2 std dev)
```dax
measure 'Eh Anomalia' =
    VAR CurrentCost = [Custo Combinado]
    VAR AvgCost = [Media Movel 3M]
    VAR Dates3M = DATESINPERIOD(Dim_Date[Date], MAX(Dim_Date[Date]), -3, MONTH)
    VAR StdDev = STDEVX.P(Dates3M, CALCULATE([Custo Combinado]))
    RETURN
        IF(AND(StdDev > 0, ABS(CurrentCost - AvgCost) > 2 * StdDev), 1, 0)
```

### Severe Anomaly (>3 std dev)
Same pattern but `> 3 * StdDev`.

### Anomaly Impact
```dax
measure 'Impacto Anomalia' =
    IF([Eh Anomalia] = 1, [Custo Combinado] - [Media Movel 3M], BLANK())
```

## Budget Measures

### Budget with USERELATIONSHIP
```dax
measure 'Orcamento' =
    CALCULATE(
        SUM(Dim_Budget[BudgetAmount]),
        USERELATIONSHIP(Dim_Budget[BillingDate], Dim_Date[Date])
    )
```

### Budget Variance
```dax
measure 'Variancia Orcamento' = [Orcamento] - [Custo Combinado]
```

## Tag Compliance

### Percentage of compliant resources
```dax
measure 'Recursos Tagueados %' =
    DIVIDE(
        COUNTROWS(FILTER(Dim_ResourceGroup, Dim_ResourceGroup[TagsCompletas] = TRUE())),
        COUNTROWS(Dim_ResourceGroup)
    )
```

### Cost of non-compliant resources
```dax
measure 'Custo Sem Tag' =
    CALCULATE([Custo Total], FILTER(Dim_ResourceGroup, Dim_ResourceGroup[TagsCompletas] = FALSE()))
```

### Per-tag compliance
```dax
measure 'Conformidade Executivo %' =
    DIVIDE(
        COUNTROWS(FILTER(Dim_ResourceGroup, Dim_ResourceGroup[TemTagExecutivo] = TRUE())),
        COUNTROWS(Dim_ResourceGroup)
    )
```

## Projection / Forecasting

### Daily Average (current month)
```dax
measure 'Media Diaria Mes' =
    VAR TotalCost = [Custo Mes Atual]
    VAR DaysElapsed = COUNTROWS(
        FILTER(DATESMTD(Dim_Date[Date]), Dim_Date[Date] <= TODAY())
    )
    RETURN DIVIDE(TotalCost, DaysElapsed)
```

### End-of-Month Projection
```dax
measure 'Projecao Fim Mes' =
    VAR DailyAvg = [Media Diaria Mes]
    VAR DaysInMonth = DAY(EOMONTH(MAX(Dim_Date[Date]), 0))
    RETURN DailyAvg * DaysInMonth
```

## Conditional Formatting Helpers

Return hex colors for visual formatting:

```dax
measure 'Cor Variacao' =
    IF([Variacao MoM %] > 0.05, "#E74C3C",
    IF([Variacao MoM %] < -0.05, "#27AE60",
    "#F39C12"))
```

- Red (#E74C3C): Cost increased >5%
- Green (#27AE60): Cost decreased >5%
- Yellow (#F39C12): Stable (within 5%)

## Balance Measures (EA Commitment)

```dax
measure 'Saldo Compromisso EA' =
    CALCULATE(
        MAX(Fact_Balance[EndingBalance]),
        USERELATIONSHIP(Fact_Balance[BillingDate], Dim_Date[Date]),
        LASTDATE(Dim_Date[Date])
    )
```

## Placeholder Measures

For features not yet implemented:

```dax
measure 'Cobertura RI %' =
    BLANK()
    formatString: 0.0%
    displayFolder: Reservas
    lineageTag: m-cobertura-ri
    annotation note = "Placeholder - requires Reservation Details export data"
```

## Format String Reference

| Type | Format | Output Example |
|------|--------|---------------|
| BRL | `R$ #,##0.00` | R$ 1.458.793,00 |
| Percentage | `0.0%;-0.0%;0.0%` | 12.5% / -3.2% / 0.0% |
| Integer | `#,##0` | 1,234 |
| Count | `0` | 42 |
| Decimal | `#,##0.00` | 1,234.56 |

Three-part percentage format: `positive;negative;zero` — handles all cases.
