---
name: power-bi-dax
description: Write, execute, and optimize DAX queries and measures for Power BI semantic models using pbi-cli. Invoke this skill whenever the user mentions DAX, queries data in Power BI, writes calculations, creates measures, asks about EVALUATE, SUMMARIZECOLUMNS, CALCULATE, time intelligence, or wants to analyze/aggregate data from a semantic model. Also invoke when the user asks to run a query, test a formula, or check row counts. This skill contains critical guidance on passing DAX expressions via CLI arguments -- multi-line DAX (VAR/RETURN) requires special handling.
tools: pbi-cli
---

# Power BI DAX Skill

Execute and validate DAX queries against connected Power BI models.

## Prerequisites

```bash
pipx install pbi-cli-tool
pbi-cli skills install
pbi connect
```

## Executing Queries

```bash
# Inline query
pbi dax execute "EVALUATE TOPN(10, Sales)"

# From file
pbi dax execute --file query.dax

# From stdin (piping)
cat query.dax | pbi dax execute -
echo "EVALUATE Sales" | pbi dax execute -

# With options
pbi dax execute "EVALUATE Sales" --max-rows 100
pbi dax execute "EVALUATE Sales" --timeout 300       # Custom timeout (seconds)

# JSON output for scripting
pbi --json dax execute "EVALUATE Sales"
```

## DAX Expression Limitations in CLI

When passing DAX as a `-e` argument, the shell collapses newlines into a single line. Simple expressions like `SUM(Sales[Amount])` work fine, but multi-line DAX using VAR/RETURN breaks because the DAX parser needs line breaks between those keywords.

**Why this matters:** A measure like `VAR x = [Total Sales] VAR y = [Sales PY] RETURN DIVIDE(x - y, y)` will fail with a syntax error because the engine sees it as one continuous line without statement separators.

**Workarounds (pick one):**

```bash
# Option 1: Pipe from stdin (recommended for measures)
echo 'VAR TotalSales = SUM(Sales[Amount])
VAR TotalCost = SUM(Sales[Cost])
RETURN TotalSales - TotalCost' | pbi measure create "Profit" -e - -t Sales

# Option 2: Write to a .dax file and use --file (for queries)
echo 'EVALUATE
ROW("Result",
    VAR x = SUM(Sales[Amount])
    RETURN x
)' > query.dax
pbi dax execute --file query.dax
```

**Single-line alternatives (preferred when possible):**

For simple ratio/growth measures, use inline patterns instead of VAR/RETURN:

```bash
# Instead of: VAR x = SUM(...) / VAR y = SUM(...) / RETURN DIVIDE(x, y)
# Use inline DIVIDE -- it handles division-by-zero gracefully (returns BLANK):
pbi measure create "Margin %" \
  -e "DIVIDE(SUM(Sales[Amount]) - SUM(Sales[Cost]), SUM(Sales[Amount]))" \
  -t Sales --format-string "0.0%"

# Instead of: VAR current = [Total Sales] / VAR prev = [Sales PY] / RETURN DIVIDE(...)
# Reference measures directly in DIVIDE:
pbi measure create "YoY %" \
  -e "DIVIDE([Total Sales] - [PY Sales], [PY Sales])" \
  -t Sales --format-string "0.0%"
```

## Validating Queries

```bash
pbi dax validate "EVALUATE Sales"
pbi dax validate --file query.dax
```

## Cache Management

```bash
pbi dax clear-cache    # Clear the formula engine cache
```

## Creating Measures with DAX

```bash
# Simple aggregation
pbi measure create "Total Sales" -e "SUM(Sales[Amount])" -t Sales

# Time intelligence
pbi measure create "YTD Sales" -e "TOTALYTD(SUM(Sales[Amount]), Calendar[Date])" -t Sales

# Previous year comparison
pbi measure create "PY Sales" -e "CALCULATE([Total Sales], SAMEPERIODLASTYEAR(Calendar[Date]))" -t Sales

# Year-over-year change
pbi measure create "YoY %" -e "DIVIDE([Total Sales] - [PY Sales], [PY Sales])" -t Sales --format-string "0.0%"
```

## Common DAX Patterns

### Explore Model Data

```bash
# List all tables
pbi dax execute "EVALUATE INFO.TABLES()"

# List columns in a table
pbi dax execute "EVALUATE INFO.COLUMNS()"

# Preview table data
pbi dax execute "EVALUATE TOPN(10, Sales)"

# Count rows
pbi dax execute "EVALUATE ROW(\"Count\", COUNTROWS(Sales))"
```

### Aggregations

```bash
# Basic sum
pbi dax execute "EVALUATE ROW(\"Total\", SUM(Sales[Amount]))"

# Group by with aggregation
pbi dax execute "EVALUATE SUMMARIZECOLUMNS(Products[Category], \"Total\", SUM(Sales[Amount]))"

# Multiple aggregations
pbi dax execute "
EVALUATE
SUMMARIZECOLUMNS(
    Products[Category],
    \"Total Sales\", SUM(Sales[Amount]),
    \"Avg Price\", AVERAGE(Sales[UnitPrice]),
    \"Count\", COUNTROWS(Sales)
)
"
```

### Filtering

```bash
# CALCULATE with filter
pbi dax execute "
EVALUATE
ROW(\"Online Sales\", CALCULATE(SUM(Sales[Amount]), Sales[Channel] = \"Online\"))
"

# FILTER with complex condition
pbi dax execute "
EVALUATE
FILTER(
    SUMMARIZECOLUMNS(Products[Name], \"Total\", SUM(Sales[Amount])),
    [Total] > 1000
)
"
```

### Time Intelligence

```bash
# Year-to-date
pbi dax execute "
EVALUATE
ROW(\"YTD\", TOTALYTD(SUM(Sales[Amount]), Calendar[Date]))
"

# Rolling 12 months
pbi dax execute "
EVALUATE
ROW(\"R12\", CALCULATE(
    SUM(Sales[Amount]),
    DATESINPERIOD(Calendar[Date], MAX(Calendar[Date]), -12, MONTH)
))
"
```

### Ranking

```bash
# Top products by sales
pbi dax execute "
EVALUATE
TOPN(
    10,
    ADDCOLUMNS(
        VALUES(Products[Name]),
        \"Total\", CALCULATE(SUM(Sales[Amount]))
    ),
    [Total], DESC
)
"
```

## Performance Tips

- Use `--max-rows` to limit result sets during development
- Run `pbi dax clear-cache` before benchmarking
- Prefer `SUMMARIZECOLUMNS` over `SUMMARIZE` for grouping
- Use `CALCULATE` with simple filters instead of nested `FILTER`
- Avoid iterators (`SUMX`, `FILTER`) on large tables when aggregations suffice

---

## Gotchas

- **VAR/RETURN newlines die in `-e`:** Shell collapses newlines into spaces, and the DAX parser needs them as statement separators. `VAR x = ... VAR y = ... RETURN ...` on one line throws a "syntax error" with no useful pointer. Pipe from stdin or use `--file`.
- **`CALCULATE(SUM(x), ALL(table))` vs `ALLEXCEPT` vs `ALLSELECTED`:** All three return plausible numbers — only one is correct. `ALL` clears everything on that table; `ALLEXCEPT` keeps only listed columns; `ALLSELECTED` respects outer filters. The wrong choice yields silently wrong totals.
- **`SUMMARIZECOLUMNS` drops rows where every measure is BLANK:** A "missing category" in your output is often this filter, not missing data. Wrap measures in `COALESCE(measure, 0)` if the row must appear.
- **`DIVIDE([a], [b])` returns BLANK on divide-by-zero, not 0:** Blanks propagate into downstream charts as gaps rather than zeros. Pass the third arg explicitly: `DIVIDE([a], [b], 0)` when zero behavior is intended.
- **`pbi dax clear-cache` only clears the formula engine cache:** Storage engine cache survives. For an honest cold-query benchmark, also restart Desktop or re-attach the connection — repeat runs otherwise look unrealistically fast.
- **`INFO.TABLES()` returns hidden tables too:** Calculation groups, auto-date hierarchies, and translation tables show up alongside user tables. Filter `[IsHidden] = FALSE` to get just what a report author sees.

