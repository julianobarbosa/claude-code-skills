# Workflow: Add Table

Add a new fact or dimension table to the PBIP semantic model.

## Decision: Fact vs Dimension

| If the table... | It's a... |
|-----------------|-----------|
| Contains transactional/event records | Fact table |
| Contains reference/lookup data | Dimension table |
| Has numeric columns for SUM/COUNT | Fact table |
| Has descriptive columns for filtering/grouping | Dimension table |
| Grows over time (new rows each period) | Fact table |
| Relatively static or slowly changing | Dimension table |

## Step 1: Create the Power Query Expression

Create `expressions/TableName.pq` with the M expression.

**For CSV-based fact tables** — use Folder.Files pattern:
```m
let
    Source = Folder.Files(Parameter_ExportFolder),
    Filtered = Table.SelectRows(Source, each
        Text.Contains([Name], "FilePattern") and Text.EndsWith([Name], ".csv")),
    Combined = Table.Combine(
        Table.AddColumn(Filtered, "Data", each
            let
                Raw = Csv.Document([Content], [Delimiter=",", Encoding=65001]),
                Headers = Table.PromoteHeaders(Raw, [PromoteAllScalars=true])
            in Headers
        )[Data]
    ),
    Typed = Table.TransformColumnTypes(Combined, {
        {"DateColumn", type date},
        {"AmountColumn", type number}
    }),
    AddDateKey = Table.AddColumn(Typed, "DateKey", each [DateColumn], type date)
in
    AddDateKey
```

**For derived dimension tables** — extract from fact:
```m
let
    Source = FactTableName,
    Distinct = Table.Distinct(
        Table.SelectColumns(Source, {"KeyColumn", "DescColumn1", "DescColumn2"})
    )
in
    Distinct
```

**For manually maintained dimensions** (like Budget):
```m
let
    Source = #table(
        type table [Period=text, Amount=number, Category=text],
        {
            {"202601", 1000000, "Total"},
            {"202602", 1200000, "Total"}
        }
    )
in
    Source
```

## Step 2: Create the TMDL Definition

Create `tables/TableName.tmdl`:

```
table TableName
    lineageTag: t-table-name

    column ColumnName
        dataType: string
        lineageTag: col-column-name
        summarizeBy: none
        sourceColumn: ColumnName

    column AmountColumn
        dataType: double
        lineageTag: col-amount
        summarizeBy: sum
        sourceColumn: AmountColumn
        formatString: R$ #,##0.00

    column DateKey
        dataType: dateTime
        lineageTag: col-datekey
        summarizeBy: none
        sourceColumn: DateKey
        isKey: true

    partition TableName = m
        mode: import
        source =
            let
                Source = Expression.Evaluate(
                    #"TableName",
                    #shared
                )
            in
                Source
```

### Column dataType Reference

| Power Query Type | TMDL dataType | summarizeBy |
|-----------------|---------------|-------------|
| type text | string | none |
| type number | double | sum (amounts) or none (rates) |
| type date | dateTime | none |
| Int64.Type | int64 | none or sum |
| type logical | boolean | none |
| Currency.Type | decimal | sum |

## Step 3: Add Relationships

Append to `relationships.tmdl`:

```
relationship TableName_to_DimName
    fromColumn: TableName.ForeignKey
    toColumn: DimName.PrimaryKey
    crossFilteringBehavior: oneDirection
```

If the dimension already has an active relationship from another fact table, add `isActive: false` and use `USERELATIONSHIP()` in DAX measures.

## Step 4: Verify

1. Open .pbip in Power BI Desktop
2. Refresh data
3. Check table appears in model view
4. Verify relationship lines in diagram
5. Test a simple measure against the new table

## Checklist

- [ ] .pq file created in expressions/
- [ ] .tmdl file created in tables/ with all columns
- [ ] Every column has lineageTag, dataType, summarizeBy
- [ ] DateKey column added for date relationship
- [ ] Relationship added to relationships.tmdl
- [ ] Null handling in PQ (defaults for empty values)
- [ ] Type conversions explicit in PQ
