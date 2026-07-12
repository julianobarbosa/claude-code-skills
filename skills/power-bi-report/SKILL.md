---
name: power-bi-report
description: >
  Scaffold, validate, preview, and manage Power BI PBIR report projects using
  pbi-cli. Invoke this skill whenever the user mentions "create report", "new
  report", "PBIR", "scaffold", "validate report", "report structure", "preview
  report", "report info", "reload Desktop", "convert report", ".pbip project",
  "report project", or wants to understand the PBIR folder format, set up a new
  report from scratch, or work with the report as a whole. For specific tasks,
  see also: power-bi-visuals (charts, binding), power-bi-pages (page management),
  power-bi-themes (themes, formatting), power-bi-filters (page/visual filters).
tools: pbi-cli
---

# Power BI Report Skill

Manage Power BI PBIR report projects at the top level -- scaffolding, validation,
preview, and Desktop integration. No connection to Power BI Desktop is needed
for most operations.

## PBIR Format

PBIR (Enhanced Report Format) stores reports as a folder of JSON files:

```
MyReport.Report/
  definition.pbir            # dataset reference
  definition/
    version.json             # PBIR version
    report.json              # report settings, theme
    pages/
      pages.json             # page order
      page_abc123/
        page.json            # page settings
        visuals/
          visual_def456/
            visual.json      # visual type, position, bindings
```

Each file has a public JSON schema from Microsoft for validation.
PBIR is GA as of January 2026 and the default format in Desktop since March 2026.

## Creating a Report

```bash
# Scaffold a new report project
pbi report create ./MyProject --name "Sales Report"

# With dataset reference
pbi report create ./MyProject --name "Sales" --dataset-path "../Sales.Dataset"
```

This creates the full folder structure with `definition.pbir`, `report.json`,
`version.json`, and an empty `pages/` directory.

## Report Info and Validation

```bash
# Show report metadata summary (pages, theme, dataset)
pbi report info
pbi report info --path ./MyReport.Report

# Validate report structure and JSON files
pbi report validate
```

Validation checks:
- Required files exist (`definition.pbir`, `report.json`, `version.json`)
- All JSON files parse without errors
- Schema URLs are present and consistent
- Page references in `pages.json` match actual page folders

## Preview

Start a live HTML preview of the report layout:

```bash
pbi report preview
```

Opens a browser showing all pages with visual placeholders, types, positions,
and data bindings. The preview auto-refreshes when files change.

Requires the `preview` optional dependency: `pip install pbi-cli-tool[preview]`

## Desktop Integration

```bash
# Trigger Power BI Desktop to reload the current report
pbi report reload
```

Power BI Desktop's Developer Mode auto-detects TMDL changes but not PBIR
changes. This command sends a keyboard shortcut to the Desktop window to
trigger a reload. Requires the `reload` optional dependency: `pip install pbi-cli-tool[reload]`

## Suppressing Auto-Sync (--no-sync)

By default, every write command (`add-page`, `delete-page`, `set-background`,
`set-theme`, etc.) automatically syncs Power BI Desktop after each operation.
When building a report in multiple steps, this causes Desktop to reload after
every single command.

Use `--no-sync` on the `report` command group to suppress per-command syncs,
then call `pbi report reload` once at the end:

```bash
# BAD: Desktop reloads after every command
pbi report add-page --display-name "Overview" --name overview
pbi report set-background overview --color "#F2F2F2"

# GOOD: suppress sync during build, reload once at the end
pbi report --no-sync add-page --display-name "Overview" --name overview
pbi report --no-sync set-background overview --color "#F2F2F2"
pbi report reload
```

`--no-sync` is available on: `report`, `visual`, `filters`, and `bookmarks`
command groups.

## Convert

```bash
# Convert a .Report folder into a distributable .pbip project
pbi report convert ./MyReport.Report --output ./distributable/
```

## Path Resolution

All report commands auto-detect the `.Report` folder:

1. Explicit: `pbi report --path ./MyReport.Report info`
2. Auto-detect: walks up from CWD looking for `*.Report/definition/`
3. From `.pbip`: finds sibling `.Report` folder from `.pbip` file

## Workflow: Build a Complete Report

This workflow uses commands from multiple skills:

```bash
# 1. Scaffold report (this skill)
pbi report create . --name "SalesDashboard" --dataset-path "../SalesModel.Dataset"

# 2. Add pages (power-bi-pages skill)
pbi report add-page --display-name "Overview" --name overview
pbi report add-page --display-name "Details" --name details

# 3. Add visuals (power-bi-visuals skill)
pbi visual add --page overview --type card --name revenue_card
pbi visual add --page overview --type bar --name sales_by_region

# 4. Bind data (power-bi-visuals skill)
pbi visual bind revenue_card --page overview --field "Sales[Total Revenue]"
pbi visual bind sales_by_region --page overview \
    --category "Geo[Region]" --value "Sales[Amount]"

# 5. Apply theme (power-bi-themes skill)
pbi report set-theme --file brand-colors.json

# 6. Validate (this skill)
pbi report validate
```

## Combining Model and Report

pbi-cli covers both the semantic model layer and the report layer:

```bash
# Model layer (requires pbi connect)
pbi connect
pbi measure create Sales "Total Revenue" "SUM(Sales[Amount])"

# Report layer (no connection needed)
pbi report create . --name "Sales"
pbi visual add --page overview --type card --name rev_card
pbi visual bind rev_card --page overview --field "Sales[Total Revenue]"
```

## Related Skills

| Skill | When to use |
|-------|-------------|
| **power-bi-visuals** | Add, bind, update, delete visuals |
| **power-bi-pages** | Add, remove, configure pages and bookmarks |
| **power-bi-themes** | Themes, conditional formatting |
| **power-bi-filters** | Page and visual filters |

## JSON Output

```bash
pbi --json report info
pbi --json report validate
```

---

## Gotchas

- **`report validate` passes a PBIR that Desktop refuses to open:** Validation only checks JSON structure and required files — it does not verify dataset binding, schema-URL versions, or visual `queryState` consistency. A clean validate followed by a Desktop "cannot open report" is a known footgun.
- **`--dataset-path` is relative to the `.Report` folder, not the CWD:** A `../Sales.Dataset` argument resolves correctly at create time, but if you later move the `.Report` folder the binding silently breaks. Use a stable workspace layout or absolute paths in CI.
- **`pbi report reload` sends keyboard shortcuts to whatever window has focus:** If the user is typing in another app when the reload fires, keystrokes land in that app instead. Run reload only at the end of a batch and tell the user not to context-switch.
- **`report convert` to `.pbip` does not bundle the semantic model:** It produces a `.pbip` shell referencing the dataset by path. Distributing the resulting folder without also packaging the `.SemanticModel` directory yields a "dataset not found" error on open.
- **PBIR schema versions are pinned per file, not per project:** Mixing files written by different Desktop versions (e.g. one page edited in March-2026 build, another in January-2026 build) can fail validation in one and pass in another. Always upgrade the whole project together.
- **`--no-sync` only applies to the command group it's on:** `pbi visual --no-sync add ...` followed by `pbi report set-background ...` will still sync after the second command. Set `--no-sync` on every group involved in the batch.

