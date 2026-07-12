---
name: power-bi-filters
description: >
  Add, remove, and manage page-level and visual-level filters on Power BI PBIR
  reports using pbi-cli. Invoke this skill whenever the user mentions "filter",
  "TopN filter", "top 10", "bottom 5", "relative date filter", "last 30 days",
  "categorical filter", "include values", "exclude values", "clear filters",
  "slicer filter", "page filter", "visual filter", or wants to restrict which
  data appears on a page or in a specific visual.
tools: pbi-cli
---

# Power BI Filters Skill

Add and manage filters on PBIR report pages and visuals. Filters are stored
in the `filterConfig` section of `page.json` (page-level) or `visual.json`
(visual-level). No Power BI Desktop connection is needed.

## Listing Filters

```bash
# List all filters on a page
pbi filters list --page page_abc123

# List filters on a specific visual
pbi filters list --page page_abc123 --visual visual_def456
```

Returns each filter's name, type, field, and scope (page or visual).

## Categorical Filters

Include or exclude specific values from a column:

```bash
# Include only East and West regions
pbi filters add-categorical --page page1 \
    --table Sales --column Region \
    --values "East" "West"
```

The filter appears in the page's `filterConfig.filters` array. Power BI
evaluates it as an IN-list against the specified column.

## TopN Filters

Show only the top (or bottom) N items ranked by a measure:

```bash
# Top 10 products by revenue
pbi filters add-topn --page page1 \
    --table Product --column Name \
    --n 10 \
    --order-by-table Sales --order-by-column Revenue

# Bottom 5 by quantity (ascending)
pbi filters add-topn --page page1 \
    --table Product --column Name \
    --n 5 \
    --order-by-table Sales --order-by-column Quantity \
    --direction Bottom
```

The `--table` and `--column` define which dimension to filter (the rows you
want to keep). The `--order-by-table` and `--order-by-column` define the
measure used for ranking. These can be different tables -- for example,
filtering Product names by Sales revenue.

Direction defaults to `Top` (descending -- highest N). Use `--direction Bottom`
for ascending (lowest N).

## Relative Date Filters

Filter by a rolling window relative to today:

```bash
# Last 30 days
pbi filters add-relative-date --page page1 \
    --table Calendar --column Date \
    --period days --count 30 --direction last

# Next 7 days
pbi filters add-relative-date --page page1 \
    --table Calendar --column Date \
    --period days --count 7 --direction next
```

Period options: `days`, `weeks`, `months`, `quarters`, `years`.
Direction: `last` (past) or `next` (future).

## Visual-Level Filters

Add a filter to a specific visual instead of the whole page by including
`--visual`:

```bash
pbi filters add-categorical --page page1 --visual vis_abc \
    --table Sales --column Channel \
    --values "Online"
```

## Removing Filters

```bash
# Remove a specific filter by name
pbi filters remove --page page1 --name filter_abc123

# Clear ALL filters from a page
pbi filters clear --page page1
```

Filter names are auto-generated unique IDs. Use `pbi filters list` to find
the name of the filter you want to remove.

## Workflow: Set Up Dashboard Filters

```bash
# 1. Add a date filter to the overview page
pbi filters add-relative-date --page overview \
    --table Calendar --column Date \
    --period months --count 12 --direction last

# 2. Add a TopN filter to show only top customers
pbi filters add-topn --page overview \
    --table Customer --column Name \
    --n 20 \
    --order-by-table Sales --order-by-column Revenue

# 3. Verify
pbi filters list --page overview
```

## Suppressing Auto-Sync (--no-sync)

By default, every write command automatically syncs Power BI Desktop. When
applying filters to multiple pages or visuals in sequence, Desktop reloads
after each command.

Use `--no-sync` on the `filters` command group to batch all filter changes,
then call `pbi report reload` once at the end:

```bash
# Suppress sync while applying filters
pbi filters --no-sync add-categorical --page overview --table "Calendar Lookup" --column "Year" --values "2024"
pbi filters --no-sync add-categorical --page details --table "Product Lookup" --column "Category" --values "Bikes"

# Single reload when all filters are done
pbi report reload
```

## JSON Output

```bash
pbi --json filters list --page page1
```

---

## Gotchas

- **TopN filter `--table`/`--column` is what you KEEP, `--order-by-*` is what you RANK BY:** Swapping the two compiles fine but ranks the wrong dimension — you'll see "top 10 dates" instead of "top 10 products". The CLI cannot catch the mismatch because both pairs are valid `Table[Column]` references.
- **Relative date filters anchor to the user's local time in Service, not the model timezone:** A "last 7 days" filter shifts at midnight per-viewer. For audit reports this produces different totals for users in different timezones — use an absolute date range instead.
- **`filters clear` removes EVERYTHING including the page-level filters set by a previous bookmark:** Bookmarks captured against the pre-clear state still reference filter IDs that no longer exist and silently behave as "no filter applied" when activated.
- **Auto-generated filter names contain GUIDs that change on every TMDL/PBIR re-export:** Scripting `filters remove --name filter_abc123` against an exported snapshot is fragile. Always re-list before removing in a script, or filter by `--table`/`--column` if the CLI supports it.
- **Visual-level filters override page-level filters silently:** A page filter for `Region = East` plus a visual filter for `Region = West` yields an empty visual, not a "conflict" warning. Use `pbi filters list --page X --visual Y` to inspect both scopes when a visual shows no data.
- **`--no-sync` plus omitted final `pbi report reload` leaves Desktop showing stale state:** The PBIR files are correct on disk, but Desktop's in-memory model is out of date — the next manual edit there can overwrite your filter changes.

