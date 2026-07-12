---
name: power-bi-partitions
description: Manage Power BI table partitions, named expressions (M/Power Query data sources), and calendar table configuration using pbi-cli. Invoke this skill whenever the user mentions "partitions", "data sources", "M expressions", "Power Query", "incremental refresh", "named expressions", "connection parameters", or wants to configure how tables load data. For broader modeling tasks (measures, relationships, hierarchies), see power-bi-modeling instead.
tools: pbi-cli
---

# Power BI Partitions & Expressions Skill

Manage table partitions, named expressions (M queries), and calendar tables.

## Prerequisites

```bash
pipx install pbi-cli-tool
pbi-cli skills install
pbi connect
```

## Partitions

Partitions define how data is loaded into a table. Each table has at least one partition.

```bash
# List partitions in a table
pbi partition list --table Sales
pbi --json partition list --table Sales

# Create a partition with an M expression
pbi partition create "Sales_2024" --table Sales \
  --expression "let Source = Sql.Database(\"server\", \"db\"), Sales = Source{[Schema=\"dbo\",Item=\"Sales\"]}[Data], Filtered = Table.SelectRows(Sales, each [Year] = 2024) in Filtered" \
  --mode Import

# Create a partition with DirectQuery mode
pbi partition create "Sales_Live" --table Sales --mode DirectQuery

# Delete a partition
pbi partition delete "Sales_Old" --table Sales

# Refresh a specific partition
pbi partition refresh "Sales_2024" --table Sales
```

## Named Expressions

Named expressions are shared M/Power Query definitions used as data sources or reusable query logic.

```bash
# List all named expressions
pbi expression list
pbi --json expression list

# Get a specific expression
pbi expression get "ServerURL"
pbi --json expression get "ServerURL"

# Create a named expression (M query)
pbi expression create "ServerURL" \
  --expression '"https://api.example.com/data"' \
  --description "API endpoint for data refresh"

# Create a parameterized data source
pbi expression create "DatabaseServer" \
  --expression '"sqlserver.company.com"' \
  --description "Production database server name"

# Delete a named expression
pbi expression delete "OldSource"
```

## Calendar Tables

Calendar/date tables enable time intelligence in DAX. Mark a table as a date table to unlock functions like TOTALYTD, SAMEPERIODLASTYEAR, etc.

```bash
# List all calendar/date tables
pbi calendar list
pbi --json calendar list

# Mark a table as a calendar table
pbi calendar mark Calendar --date-column Date

# Alternative: use the table command
pbi table mark-date Calendar --date-column Date
```

## Workflow: Set Up Partitioned Table

```bash
# 1. Create a table
pbi table create Sales --mode Import

# 2. Create partitions for different date ranges
pbi partition create "Sales_2023" --table Sales \
  --expression "let Source = ... in Filtered2023" \
  --mode Import

pbi partition create "Sales_2024" --table Sales \
  --expression "let Source = ... in Filtered2024" \
  --mode Import

# 3. Refresh specific partitions
pbi partition refresh "Sales_2024" --table Sales

# 4. Verify partitions
pbi --json partition list --table Sales
```

## Workflow: Manage Data Sources

```bash
# 1. List current data source expressions
pbi --json expression list

# 2. Create shared connection parameters
pbi expression create "ServerName" \
  --expression '"prod-sql-01.company.com"' \
  --description "Production SQL Server"

pbi expression create "DatabaseName" \
  --expression '"SalesDB"' \
  --description "Production database"

# 3. Verify
pbi --json expression list
```

## Best Practices

- Use partitions for large tables to enable incremental refresh
- Refresh only the partitions that have new data (`pbi partition refresh`)
- Use named expressions for shared connection parameters (server names, URLs)
- Always mark calendar tables with `pbi calendar mark` for time intelligence
- Use `--json` output for scripted partition management
- Export model as TMDL to version-control partition definitions: `pbi database export-tmdl ./model/`

---

## Gotchas

- **Incremental refresh needs RangeStart/RangeEnd parameters with specific names and DateTime type:** The PBI service silently falls back to full refresh if the parameters are misnamed, typed as Date instead of DateTime, or missing the policy binding. The model loads fine — only the refresh metric reveals the bug, usually weeks later when storage costs spike.
- **`partition refresh` only refreshes the specified partition, but downstream calculated columns rebuild at the table level:** If a partitioned fact table has calculated columns derived from another partition, you'll see inconsistent values until a `--type Calculate` runs.
- **Named expressions used as data sources must be referenced by name, not inlined:** Inlining the connection string into multiple partitions creates separate data source records in PBI Service — each prompts for credentials separately on first refresh.
- **DirectQuery and Import partitions on the same table is illegal in Power BI:** The CLI may accept mixed-mode partition creation in some versions but the model fails to refresh with a vague "composite model" error. Composite models require explicit dual-storage configuration on the table, not per-partition.
- **`pbi expression create` with a single quoted string value silently loses outer quotes:** `--expression '"https://x.com"'` is correct (M needs quotes), but `--expression "https://x.com"` creates an invalid expression referencing an undefined identifier.
- **Calendar tables marked with `pbi calendar mark` cannot be unmarked via the CLI:** Once marked, the only way to revert is editing the TMDL `dataCategory` directly or using Desktop's UI. Watch for this when a Calendar table needs to become a regular dimension.

