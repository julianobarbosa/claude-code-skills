---
name: power-bi-modeling
description: Create and manage Power BI semantic model structure using pbi-cli -- tables, columns, measures, relationships, hierarchies, calculation groups, and date/calendar tables. Invoke this skill whenever the user says "create table", "add measure", "add column", "create relationship", "date table", "calendar table", "star schema", "mark as date table", "add hierarchy", "calculation group", or any model-building task. Also invoke when creating multiple measures at once -- the skill contains critical guidance on multi-line DAX expression handling.
tools: pbi-cli
---

# Power BI Modeling Skill

Use pbi-cli to manage semantic model structure. Requires `pipx install pbi-cli-tool`, `pbi-cli skills install`, and `pbi connect`.

## Prerequisites

```bash
pipx install pbi-cli-tool
pbi-cli skills install
pbi connect
```

## Tables

```bash
pbi table list                                    # List all tables
pbi table get Sales                               # Get table details
pbi table create Sales --mode Import              # Create table
pbi table delete OldTable                         # Delete table
pbi table rename OldName NewName                  # Rename table
pbi table refresh Sales --type Full               # Refresh table data
pbi table schema Sales                            # Get table schema
pbi table mark-date Calendar --date-column Date   # Mark as date table
```

## Columns

```bash
pbi column list --table Sales                                       # List columns
pbi column get Amount --table Sales                                 # Get column details
pbi column create Revenue --table Sales --data-type double --source-column Revenue  # Data column
pbi column create Profit --table Sales --expression "[Revenue]-[Cost]"              # Calculated
pbi column delete OldCol --table Sales                              # Delete column
pbi column rename OldName NewName --table Sales                     # Rename column
```

## Measures

```bash
pbi measure list                                                    # List all measures
pbi measure list --table Sales                                      # Filter by table
pbi measure get "Total Revenue" --table Sales                       # Get details
pbi measure create "Total Revenue" -e "SUM(Sales[Revenue])" -t Sales                        # Basic
pbi measure create "Revenue $" -e "SUM(Sales[Revenue])" -t Sales --format-string "\$#,##0"  # Formatted
pbi measure create "KPI" -e "..." -t Sales --folder "Key Measures" --description "Main KPI" # With metadata
pbi measure update "Total Revenue" -t Sales -e "SUMX(Sales, Sales[Qty]*Sales[Price])"       # Update expression
pbi measure delete "Old Measure" -t Sales                           # Delete
pbi measure rename "Old" "New" -t Sales                             # Rename
pbi measure move "Revenue" -t Sales --to-table Finance              # Move to another table
```

**Multi-line DAX in measure expressions:** The `-e` flag passes DAX as a shell argument, which collapses newlines. For simple expressions like `SUM(Sales[Amount])` or `DIVIDE([A] - [B], [B])` this works fine. For complex expressions using VAR/RETURN, pipe from stdin instead:

```bash
echo 'VAR TotalSales = SUM(Sales[Amount])
VAR TotalCost = SUM(Sales[Cost])
RETURN TotalSales - TotalCost' | pbi measure create "Profit" -e - -t Sales
```

See the **power-bi-dax** skill for the full explanation and more workarounds.

## Relationships

```bash
pbi relationship list                              # List all relationships
pbi relationship get RelName                       # Get details
pbi relationship create \
  --from-table Sales --from-column ProductKey \
  --to-table Products --to-column ProductKey       # Create relationship
pbi relationship delete RelName                    # Delete
pbi relationship find --table Sales                # Find relationships for a table
pbi relationship activate RelName                  # Activate
pbi relationship deactivate RelName                # Deactivate
```

## Hierarchies

```bash
pbi hierarchy list --table Date                    # List hierarchies
pbi hierarchy get "Calendar" --table Date          # Get details
pbi hierarchy create "Calendar" --table Date       # Create
pbi hierarchy delete "Calendar" --table Date       # Delete
```

## Calculation Groups

```bash
pbi calc-group list                                # List calculation groups
pbi calc-group create "Time Intelligence" --description "Time calcs"  # Create group
pbi calc-group items "Time Intelligence"           # List items
pbi calc-group create-item "YTD" \
  --group "Time Intelligence" \
  --expression "CALCULATE(SELECTEDMEASURE(), DATESYTD(Calendar[Date]))"  # Add item
pbi calc-group delete "Time Intelligence"          # Delete group
```

## Creating a Date/Calendar Table

Date tables are essential for time intelligence functions (TOTALYTD, SAMEPERIODLASTYEAR, DATEADD, etc.).

```bash
# Create a calculated date table with DAX (covers full calendar years)
pbi table create Calendar \
  --dax-expression "ADDCOLUMNS(CALENDAR(DATE(2023,1,1), DATE(2024,12,31)), \"Year\", YEAR([Date]), \"MonthNumber\", MONTH([Date]), \"MonthName\", FORMAT([Date], \"MMMM\"), \"Quarter\", \"Q\" & FORMAT([Date], \"Q\"))"

# Mark it as a date table (required for time intelligence)
pbi table mark-date Calendar --date-column Date

# Verify it's recognized as a date table
pbi calendar list
```

## Workflow: Create a Star Schema

```bash
# 1. Create fact table
pbi table create Sales --mode Import

# 2. Create dimension tables
pbi table create Products --mode Import
pbi table create Calendar --mode Import

# 3. Create relationships
pbi relationship create --from-table Sales --from-column ProductKey --to-table Products --to-column ProductKey
pbi relationship create --from-table Sales --from-column DateKey --to-table Calendar --to-column DateKey

# 4. Mark date table
pbi table mark-date Calendar --date-column Date

# 5. Add measures
pbi measure create "Total Revenue" -e "SUM(Sales[Revenue])" -t Sales --format-string "\$#,##0"
pbi measure create "Total Qty" -e "SUM(Sales[Quantity])" -t Sales --format-string "#,##0"
pbi measure create "Avg Price" -e "AVERAGE(Sales[UnitPrice])" -t Sales --format-string "\$#,##0.00"

# 6. Verify
pbi table list
pbi measure list
pbi relationship list
```

## Best Practices

- Use format strings for currency (`$#,##0`), percentage (`0.0%`), and integer (`#,##0`) measures
- Organize measures into display folders by business domain
- Always mark calendar tables with `mark-date` for time intelligence
- Use `--json` flag when scripting: `pbi --json measure list`
- Export TMDL for version control: `pbi database export-tmdl ./model/`

---

## Gotchas

- **`mark-date` requires a contiguous date column with no gaps:** A calendar table missing a single day (leap year, manual filter) accepts `mark-date` without error but silently fails time-intelligence functions like `SAMEPERIODLASTYEAR` — they return BLANK with no diagnostic.
- **`relationship create` defaults to bidirectional in some pbi-cli versions:** Always inspect with `pbi --json relationship get RelName` immediately after creation. Bidirectional joins between a fact and a small dimension table will silently destroy filter context propagation in unrelated measures.
- **Calculated tables created via `--dax-expression` do not refresh on data refresh:** They re-evaluate at process-recalc time only. Edits to underlying tables won't propagate until a `Full` or `Calculate` refresh — easy to miss in a partial-refresh pipeline.
- **`measure move --to-table` updates the home table but NOT references in DAX:** Existing measures referencing `Sales[Margin]` still work because measures are model-scoped, but the visual `report.json` may keep the old table reference and break when the source table is later renamed.
- **`format-string` with literal `$` needs shell escaping:** `--format-string "$#,##0"` becomes `#,##0` after shell variable expansion. Use `--format-string "\$#,##0"` or wrap in single quotes — the resulting measure looks "wrong" with no error.
- **Calculation group creation order matters for sort:** The first item created becomes ordinal 0 and is the default. Add a "No Time Calc" placeholder first or measures will silently apply YTD when nothing is selected.

