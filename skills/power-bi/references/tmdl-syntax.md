# TMDL Syntax Reference

Tabular Model Definition Language — the text-based format for PBIP semantic models.

## File Structure

```
definition/
├── model.tmdl              # Model-level settings (culture, version)
├── tables/                 # One .tmdl per table
│   ├── _Measures.tmdl      # Dedicated measures table
│   ├── Fact_Usage.tmdl     # Fact table definitions
│   ├── Dim_Date.tmdl       # Dimension table definitions
│   └── ...
├── expressions/            # One .pq per Power Query expression
│   ├── Fact_Usage.pq
│   ├── Dim_Date.pq
│   └── ...
└── relationships.tmdl      # All relationships in one file
```

## Model Definition (model.tmdl)

```
model Model
    culture: pt-BR
    defaultPowerBIDataSourceVersion: powerBI_V3
    sourceQueryCulture: pt-BR
```

- `culture`: Locale for formatting (pt-BR, en-US, etc.)
- `defaultPowerBIDataSourceVersion`: Always `powerBI_V3` for modern models
- `sourceQueryCulture`: Affects how PQ interprets literals

## Table Definition

```
table Fact_Usage
    lineageTag: t-fact-usage

    column UsageDate
        dataType: dateTime
        lineageTag: col-usage-date
        summarizeBy: none
        sourceColumn: UsageDate

    column PretaxCost
        dataType: double
        lineageTag: col-pretax-cost
        summarizeBy: sum
        sourceColumn: PretaxCost
        formatString: R$ #,##0.00

    column ResourceGroup
        dataType: string
        lineageTag: col-rg
        summarizeBy: none
        sourceColumn: ResourceGroup

    column TagsCompletas
        dataType: boolean
        lineageTag: col-tags-completas
        summarizeBy: none
        sourceColumn: TagsCompletas

    partition Fact_Usage = m
        mode: import
        source =
            let Source = Expression.Evaluate(#"Fact_Usage", #shared) in Source
```

### Column Properties

| Property | Required | Description |
|----------|----------|-------------|
| `dataType` | Yes | string, int64, double, dateTime, boolean, decimal |
| `lineageTag` | Yes | Unique identifier across model |
| `summarizeBy` | Yes | none, sum, count, min, max, average |
| `sourceColumn` | Yes | Column name from PQ output |
| `formatString` | No | Display format (currency, percentage, etc.) |
| `isHidden` | No | Hide from report view (true/false) |
| `isKey` | No | Mark as primary key (true/false) |
| `sortByColumn` | No | Column to sort by (e.g., sort month name by month number) |
| `annotation` | No | Metadata annotations (key = value) |

### dataType Values

| dataType | Use For | PQ Equivalent |
|----------|---------|---------------|
| `string` | Text, IDs, names | type text |
| `int64` | Integers, counts | Int64.Type |
| `double` | Decimals, amounts | type number |
| `dateTime` | Dates and timestamps | type date, type datetime |
| `boolean` | True/false flags | type logical |
| `decimal` | Precise currency | Currency.Type |

## Measure Definition

```
measure 'Custo Total' =
    SUM(Fact_Usage[PretaxCost])
    formatString: R$ #,##0.00
    displayFolder: Custo
    lineageTag: m-custo-total
```

### Multi-line DAX Measure

```
measure 'Variacao MoM %' =
    VAR CustoAtual = [Custo Mes Atual]
    VAR CustoAnterior = [Custo Mes Anterior]
    RETURN
        IF(
            CustoAnterior <> 0,
            DIVIDE(CustoAtual - CustoAnterior, CustoAnterior),
            BLANK()
        )
    formatString: 0.0%;-0.0%;0.0%
    displayFolder: Variacao
    lineageTag: m-variacao-mom
```

### Measure with Annotation

```
measure 'Contagem Reservas' =
    BLANK()
    formatString: 0
    displayFolder: Reservas
    lineageTag: m-contagem-reservas
    annotation note = "Placeholder - requires Reservation Details export data"
```

### Measure Properties

| Property | Required | Description |
|----------|----------|-------------|
| `formatString` | Recommended | Display format |
| `displayFolder` | Recommended | Organize in field list |
| `lineageTag` | Yes | Unique ID with m- prefix |
| `annotation` | No | Metadata (key = "value") |

## Calculated Table Pattern (_Measures)

The dedicated measures table pattern:

```
table _Measures
    lineageTag: measures-001

    // All measures go here organized by displayFolder sections

    measure 'Custo Total' =
        SUM(Fact_Usage[PretaxCost])
        formatString: R$ #,##0.00
        displayFolder: Custo
        lineageTag: m-custo-total

    // Hidden column required for calculated table
    column MeasureColumn
        dataType: int64
        isHidden: true
        lineageTag: measures-col
        summarizeBy: none
        sourceColumn: none

    partition _Measures = calculated
        source = ROW("MeasureColumn", 0)
```

Key points:
- `partition = calculated` with `source = ROW(...)` makes it a calculated table
- Hidden column exists only to satisfy the table requirement
- `sourceColumn: none` for calculated columns

## Relationship Definition

```
relationship Fact_Usage_to_Dim_Date
    fromColumn: Fact_Usage.DateKey
    toColumn: Dim_Date.Date
    crossFilteringBehavior: oneDirection
```

### Inactive Relationship

```
relationship Fact_Marketplace_to_Dim_Date
    fromColumn: Fact_Marketplace.DateKey
    toColumn: Dim_Date.Date
    isActive: false
    crossFilteringBehavior: oneDirection
```

### Relationship Properties

| Property | Required | Values |
|----------|----------|--------|
| `fromColumn` | Yes | `TableName.ColumnName` (many side) |
| `toColumn` | Yes | `TableName.ColumnName` (one side) |
| `crossFilteringBehavior` | Yes | `oneDirection` (always for star schema) |
| `isActive` | No | `false` for inactive (default: true) |

## Partition Types

### Import from PQ Expression

```
partition Fact_Usage = m
    mode: import
    source =
        let Source = Expression.Evaluate(#"Fact_Usage", #shared) in Source
```

### Calculated Table

```
partition _Measures = calculated
    source = ROW("MeasureColumn", 0)
```

## lineageTag Convention

| Object Type | Prefix | Example |
|-------------|--------|---------|
| Table | `t-` | `t-fact-usage` |
| Measure | `m-` | `m-custo-total` |
| Column | `col-` | `col-pretax-cost` |
| Relationship | `rel-` | `rel-usage-date` |
| Special | descriptive | `measures-001`, `measures-col` |

Rules:
- Kebab-case (lowercase with hyphens)
- Must be unique across the entire model
- Descriptive but concise
- Portuguese abbreviations OK: `m-conf-executivo`, `m-variacao-mom`

## Format Strings

| Type | Format | Example |
|------|--------|---------|
| BRL Currency | `R$ #,##0.00` | R$ 1.458.793,00 |
| USD Currency | `$ #,##0.00` | $1,458,793.00 |
| EUR Currency | `€ #,##0.00` | €1,458,793.00 |
| Percentage | `0.0%;-0.0%;0.0%` | 12.5% / -3.2% / 0.0% |
| Integer | `#,##0` | 1,234 |
| Decimal | `#,##0.00` | 1,234.56 |
| Count | `0` | 42 |
| Date | `dd/MM/yyyy` | 15/04/2026 |
