# Workflow: Troubleshooting

Common Power BI issues and their solutions.

## Data Loading Issues

| Problem | Diagnosis | Solution |
|---------|-----------|---------|
| "Cannot find folder" | Parameter_ExportFolder wrong | Transform Data > Edit Parameters > fix path |
| No data after refresh | CSV naming doesn't match PQ filter | Check `Text.Contains` filter in .pq matches actual filenames |
| Marketplace table empty | 2-header-row CSV not handled | PQ should skip first row + promote second as headers |
| Type conversion error | CSV has unexpected format | Verify UTF-8 encoding, check decimal separators (comma vs period) |
| Balance shows zeros | Balance CSV edited/corrupted | Re-export from EA portal, don't edit manually |
| Tags not parsed | Invalid JSON in Tags column | Verify Tags column contains valid JSON (not escaped strings) |
| Duplicate rows | Multiple CSVs for same period | Remove duplicate CSV files from export folder |
| Slow refresh | Large UsageDetails (>1M rows) | Filter by date range in PQ, or use incremental refresh |

## TMDL Errors

| Problem | Diagnosis | Solution |
|---------|-----------|---------|
| "Duplicate lineageTag" | Two objects share same tag | Search all .tmdl files, make tags unique |
| "Column not found" | PQ output changed but TMDL not updated | Sync column names between .pq and .tmdl |
| "Invalid relationship" | FK column doesn't exist or type mismatch | Verify column names and types match in both tables |
| "Circular dependency" | Bidirectional or chained relationships | Remove bidirectional, flatten snowflake chains |
| Model won't load | Syntax error in TMDL | Check indentation (TMDL is whitespace-sensitive for measures) |

## DAX Errors

| Problem | Diagnosis | Solution |
|---------|-----------|---------|
| "Circular dependency detected" | Measure references itself | Break the cycle, use intermediate measure |
| "Column not found" | Wrong table prefix or column name | Use `TableName[ColumnName]` format |
| Division by zero | Missing DIVIDE() or BLANK() check | Use `DIVIDE(num, denom)` or `IF(denom <> 0, ...)` |
| Wrong totals | Missing USERELATIONSHIP | Check if the relationship is inactive → add USERELATIONSHIP |
| Time intelligence wrong | Dim_Date not continuous | Ensure calendar has every date (no gaps) |
| SAMEPERIODLASTYEAR empty | No data for prior year | Extend Dim_Date range and verify data exists |

## Power Query Debugging

### Check PQ Output Before TMDL

1. Open .pbip in Power BI Desktop
2. Transform Data (Power Query Editor)
3. Click on the table name
4. Check Applied Steps — click each step to see intermediate results
5. Verify column names, types, and row counts

### Common PQ Patterns That Break

```m
// BAD: This silently returns empty if no files match
Table.SelectRows(Source, each Text.Contains([Name], "ExactWrongName"))

// GOOD: Add error handling or log
Table.SelectRows(Source, each
    Text.Contains([Name], "UsageDetails", Comparer.OrdinalIgnoreCase))
```

### Encoding Issues

- EA portal exports are UTF-8 with BOM
- Python exports should use `encoding="utf-8"`
- In PQ: `Csv.Document(content, [Encoding=65001])` for UTF-8

## Relationship Debugging

### Symptom: Slicer Doesn't Filter Visuals

1. Check relationship exists in relationships.tmdl
2. Check cross-filtering direction (should be oneDirection from fact to dim)
3. Check if relationship is active (`isActive: false` means it won't auto-filter)
4. If inactive, the measure must use USERELATIONSHIP

### Symptom: Numbers Don't Add Up

1. Check for many-to-many relationships (should be M:1)
2. Check for bidirectional cross-filtering (should be one-direction)
3. Check if measure uses wrong relationship path
4. Verify DateKey in fact matches Date in Dim_Date (type and format)

## Git / PBIP Issues

| Problem | Solution |
|---------|---------|
| report.json merge conflict | Accept one version, open in Desktop, re-save |
| .tmdl merge conflict | Manually merge (text-based, clean diffs) |
| PBI Desktop can't open .pbip | Check all referenced files exist, validate JSON |
| Changes lost after Desktop edit | Desktop may overwrite manual edits — close Desktop before editing files |

## Performance

| Symptom | Fix |
|---------|-----|
| Slow refresh (>5 min) | Filter data in PQ (date range), reduce columns |
| Slow visuals | Reduce cardinality, avoid DISTINCTCOUNT on high-cardinality |
| Large file size | Remove unused columns in PQ, don't import raw JSON |
| Memory pressure | Split large fact tables by year, use aggregation tables |
