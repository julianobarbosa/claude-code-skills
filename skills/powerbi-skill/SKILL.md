---
name: powerbi-skill
description: Power BI development with PBIP format — TMDL models, Power Query (M), DAX measures, star schema design, report authoring, publishing to Power BI Service, scheduled refresh, and connector troubleshooting. USE WHEN user mentions Power BI, PBIP, TMDL, DAX measures, Power Query, semantic model, PBI report, star schema for PBI, publish to Power BI, scheduled refresh, data gateway, PBI connector, cost management connector, EA connector, Power BI template app, or any Power BI development task. Also use when editing .tmdl, .pq, .pbip, .pbir, .pbism files, or working with HyperaTheme.json.
---

# Power BI Development Skill

End-to-end Power BI project development using the PBIP (Power BI Project) format — the git-friendly, text-based format for version-controlled Power BI solutions.

## When This Skill Applies

- Creating or modifying Power BI semantic models (TMDL files)
- Writing or debugging Power Query (M) expressions (.pq files)
- Authoring DAX measures
- Designing star schema data models
- Publishing reports to Power BI Service
- Configuring scheduled refresh and data gateways
- Troubleshooting PBI connectors (especially Azure Cost Management / EA)
- Working with any .tmdl, .pq, .pbip, .pbir, .pbism files

## PBIP Project Structure

```
ProjectName/
├── ProjectName.pbip                    # Open this in PBI Desktop
├── ProjectName.Report/
│   ├── report.json                     # Report visuals (edit in PBI Desktop)
│   ├── definition.pbir                 # Report definition pointer
│   └── StaticResources/
│       └── SharedResources/BaseThemes/ # Custom themes (.json)
├── ProjectName.SemanticModel/
│   ├── definition.pbism                # Semantic model pointer
│   └── definition/
│       ├── model.tmdl                  # Model-level settings
│       ├── tables/                     # Table definitions + measures (.tmdl)
│       ├── expressions/                # Power Query scripts (.pq)
│       └── relationships.tmdl          # Star schema joins
├── scripts/                            # Python automation (optional)
└── docs/                               # Documentation
```

## Workflow Routing

| Workflow | Trigger | File |
|----------|---------|------|
| NewProject | "create PBI project", "scaffold PBIP", "new Power BI project" | `workflows/new-project.md` |
| AddTable | "add table", "new fact table", "new dimension", "add PQ source" | `workflows/add-table.md` |
| AddMeasure | "add DAX measure", "create measure", "new KPI" | `workflows/add-measure.md` |
| DataModeling | "star schema", "add relationship", "data model design" | `workflows/data-modeling.md` |
| PublishRefresh | "publish to service", "scheduled refresh", "data gateway" | `workflows/publish-refresh.md` |
| ConnectorAuth | "connector auth", "EA connector", "cost management connector", "PBI sign in failed" | `workflows/connector-auth.md` |
| Troubleshooting | "PBI error", "refresh failed", "data not loading", "type error" | `workflows/troubleshooting.md` |

## Reference Files

Read these as needed — don't load all at once:

| Reference | When to Read | File |
|-----------|-------------|------|
| TMDL Syntax | Writing or editing .tmdl files | `references/tmdl-syntax.md` |
| Power Query Patterns | Writing or editing .pq files | `references/power-query-patterns.md` |
| DAX Patterns | Writing DAX measures | `references/dax-patterns.md` |
| Star Schema Guide | Data model design decisions | `references/star-schema-guide.md` |
| PBI Service & Gateway | Publishing and refresh config | `references/pbi-service-gateway.md` |

## Tools

### File Operations (PBIP Development)

| Tool | Use For |
|------|---------|
| **Read** | Read .tmdl, .pq, .pbip, .pbir, .pbism, report.json, theme.json files |
| **Write** | Create new .tmdl, .pq, .json files for new tables, expressions, themes |
| **Edit** | Modify existing .tmdl files (add measures, columns), edit .pq expressions, update relationships.tmdl |
| **Glob** | Find files by pattern: `**/*.tmdl`, `**/*.pq`, `**/expressions/*.pq` |
| **Grep** | Search across TMDL/PQ files: find measure names, lineageTags, column references |

### Code Search & Navigation

| Tool | Use For |
|------|---------|
| **Grep** `pattern: "lineageTag"` | Verify lineageTag uniqueness across all .tmdl files |
| **Grep** `pattern: "displayFolder"` | List all measure folders for organization |
| **Grep** `pattern: "USERELATIONSHIP"` | Find measures using inactive relationships |
| **Grep** `pattern: "isActive: false"` | Find inactive relationships that need USERELATIONSHIP |
| **Glob** `pattern: "**/*.pq"` | List all Power Query expressions |
| **Glob** `pattern: "**/tables/*.tmdl"` | List all table definitions |

### Automation & Scripting

| Tool | Use For |
|------|---------|
| **Bash** | Run Python scripts: `python scripts/export_billing_data.py --period YYYYMM` |
| **Bash** | Run anomaly detection: `python scripts/detect_anomalies.py --data-folder ./data` |
| **Bash** | Git operations on PBIP files (commit, diff, branch) |
| **Bash** | Install Python dependencies: `pip install -r scripts/requirements.txt` |
| **Bash** | Azure CLI for data export auth: `az login`, `az account set` |

### Browser Automation (Power BI Service)

| Tool | Use For |
|------|---------|
| **Browser tools** (mcp__claude-in-chrome__*) | Navigate Power BI Service web UI |
| **navigate** | Open Power BI workspaces, dataset settings, refresh history |
| **form_input** | Configure scheduled refresh, data source credentials, parameters |
| **get_page_text** / **read_page** | Read refresh history, error messages, dataset settings |
| **javascript_tool** | Interact with PBI Service UI elements |
| **tabs_create_mcp** | Open new tabs for PBI Service pages |
| **gif_creator** | Record multi-step PBI Service configuration for documentation |

### Research & Documentation

| Tool | Use For |
|------|---------|
| **WebSearch** | Look up DAX functions, TMDL syntax changes, PBI release notes |
| **WebFetch** | Fetch Microsoft Learn docs for PBI/DAX/M reference |
| **microsoft_docs_search** (MCP) | Search official Microsoft PBI documentation |
| **microsoft_docs_fetch** (MCP) | Fetch full PBI documentation pages |
| **microsoft_code_sample_search** (MCP) | Find DAX/M code samples from Microsoft docs |
| **context7** (MCP) | Fetch current library docs for Azure SDK, PBI REST API |

### Data Inspection

| Tool | Use For |
|------|---------|
| **Read** | Inspect CSV billing exports (preview first rows) |
| **Bash** `wc -l` | Count rows in large CSV files |
| **Bash** `head -5` | Preview CSV headers and first rows |
| **Grep** on CSV | Search for specific resource groups, subscriptions, or cost values |

### Common Tool Sequences

**Adding a new measure:**
1. `Grep` for existing lineageTags → ensure uniqueness
2. `Read` _Measures.tmdl → understand patterns
3. `Edit` _Measures.tmdl → add the new measure

**Adding a new table:**
1. `Write` expressions/NewTable.pq → create PQ expression
2. `Write` tables/NewTable.tmdl → create table definition
3. `Edit` relationships.tmdl → add relationship
4. `Grep` for lineageTags → verify no conflicts

**Troubleshooting connector auth:**
1. `Read` workflows/connector-auth.md → get diagnosis steps
2. Browser tools → navigate to EA portal or PBI Service settings
3. `Read` project memory → check known EA enrollment details

**Publishing and refresh:**
1. Browser tools → navigate to PBI Service workspace
2. `read_page` → check current dataset settings
3. `form_input` → configure refresh schedule
4. `get_page_text` → verify refresh history

## Critical Rules

1. **PBIP format only** — Never suggest .pbix for version-controlled projects. PBIP is the git-friendly format (TMDL = text, PQ = text, clean diffs).

2. **Localization awareness** — Ask the user what language their labels should be in. For Brazilian projects, use pt-BR labels, BRL currency format (`R$ #,##0.00`), and Portuguese month names.

3. **Star schema discipline** — All relationships must be M:1 from fact to dimension tables. Use `crossFilteringBehavior: oneDirection`. Use `isActive: false` + `USERELATIONSHIP()` in DAX for ambiguous paths (e.g., multiple date relationships).

4. **Measures table pattern** — All DAX measures go in a dedicated `_Measures` table (calculated table with `ROW("MeasureColumn", 0)`). Organize measures into `displayFolder` groups.

5. **Power Query parameter** — Use a `Parameter_ExportFolder` parameter for folder-based CSV ingestion. This makes the data source path configurable without editing PQ code.

6. **lineageTag convention** — Every table, measure, column, and relationship needs a unique `lineageTag`. Use descriptive kebab-case: `m-custo-total`, `t-fact-usage`, `rel-usage-date`.

7. **Format strings** — Currency: `R$ #,##0.00` (or locale-appropriate). Percentage: `0.0%;-0.0%;0.0%`. Integer: `#,##0`. Use the three-part format for percentages to handle negative values.

8. **EA connector vs Azure RBAC** — The PBI Cost Management connector for EA enrollments requires **Enterprise Administrator (read-only)** role at the billing account level. Standard Azure RBAC roles (Cost Management Reader, Billing Reader) do NOT work. See `workflows/connector-auth.md`.

## Quick Examples

### TMDL Measure
```
measure 'Custo Total' =
    SUM(Fact_Usage[PretaxCost])
    formatString: R$ #,##0.00
    displayFolder: Custo
    lineageTag: m-custo-total
```

### TMDL Relationship
```
relationship Fact_Usage_to_Dim_Date
    fromColumn: Fact_Usage.DateKey
    toColumn: Dim_Date.Date
    crossFilteringBehavior: oneDirection
```

### Power Query — Folder-based CSV ingestion
```m
let
    Source = Folder.Files(Parameter_ExportFolder),
    Filtered = Table.SelectRows(Source, each
        Text.Contains([Name], "UsageDetails") and Text.EndsWith([Name], ".csv")),
    Combined = Table.Combine(
        Table.AddColumn(Filtered, "Data", each
            Csv.Document([Content], [Delimiter=",", Encoding=65001])
        )[Data]
    )
in
    Combined
```

### DAX — Month-over-Month variance with safe division
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
    formatString: 0.0%;-0.0%;0.0%
    displayFolder: Variacao
```
