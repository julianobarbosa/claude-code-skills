---
name: power-bi-docs
description: Auto-document Power BI semantic models by extracting metadata, generating documentation, and cataloging all model objects using pbi-cli. Invoke this skill whenever the user says "document this model", "what's in this model", "list everything", "data dictionary", "model inventory", "audit contents", "catalog", "describe the model", or wants to understand what objects exist in a semantic model.
tools: pbi-cli
---

# Power BI Documentation Skill

Generate comprehensive documentation for Power BI semantic models.

## Prerequisites

```bash
pipx install pbi-cli-tool
pbi-cli skills install
pbi connect
```

## Quick Model Overview

```bash
pbi --json model get       # Model metadata
pbi --json model stats     # Table/measure/column counts
```

## Catalog All Objects

```bash
# Tables and their structure
pbi --json table list
pbi --json table get Sales
pbi --json table schema Sales

# All measures
pbi --json measure list

# Individual measure details
pbi --json measure get "Total Revenue" --table Sales

# Columns per table
pbi --json column list --table Sales
pbi --json column list --table Products

# Relationships
pbi --json relationship list

# Security roles
pbi --json security-role list

# Hierarchies
pbi --json hierarchy list --table Date

# Calculation groups
pbi --json calc-group list

# Perspectives
pbi --json perspective list

# Named expressions (M queries)
pbi --json expression list

# Partitions
pbi --json partition list --table Sales

# Calendar/date tables
pbi --json calendar list
```

## Export Full Model as TMDL

```bash
pbi database export-tmdl ./model-docs/
```

This creates a human-readable text representation of the entire model.

## Workflow: Generate Model Documentation

Run these commands to gather all information needed for documentation:

```bash
# Step 1: Model overview
pbi --json model get > model-meta.json
pbi --json model stats > model-stats.json

# Step 2: All tables
pbi --json table list > tables.json

# Step 3: All measures
pbi --json measure list > measures.json

# Step 4: All relationships
pbi --json relationship list > relationships.json

# Step 5: Security roles
pbi --json security-role list > security-roles.json

# Step 6: Column details per table (loop through tables)
pbi --json column list --table Sales > columns-sales.json
pbi --json column list --table Products > columns-products.json

# Step 7: Full TMDL export
pbi database export-tmdl ./tmdl-export/
```

Then assemble these JSON files into markdown or HTML documentation.

## Workflow: Data Dictionary

For each table, extract columns and their types:

```bash
# Get schema for key tables
pbi --json table schema Sales
pbi --json table schema Products
pbi --json table schema Calendar
```

## Workflow: Measure Catalog

Create a complete measure inventory:

```bash
# List all measures with expressions
pbi --json measure list

# Export full model as TMDL (includes all measure definitions)
pbi database export-tmdl ./tmdl-export/
```

## Culture Management

For multi-language models:

```bash
# List cultures (locales)
pbi --json advanced culture list

# Create a culture for localization
pbi advanced culture create "fr-FR"

# Delete a culture
pbi advanced culture delete "fr-FR"
```

## Best Practices

- Always use `--json` flag for machine-readable output
- Export TMDL alongside JSON for complete documentation
- Run documentation generation as part of CI/CD pipeline
- Keep documentation in version control alongside TMDL exports
- Include relationship diagrams (generate from `pbi --json relationship list`)
- Document measure business logic, not just DAX expressions
- Tag measures by business domain using display folders

---

## Gotchas

- **`measure list` returns DAX expressions but not display formatting:** Format strings, display folders, and descriptions live on separate properties. To capture a complete measure inventory always pair `--json measure list` with a TMDL export — the JSON view alone misses metadata that authors care about.
- **`table schema` ignores calculated columns at the schema level:** They show up in `column list` but `table schema` reports only the storage-engine schema. Documenting a model from `schema` alone makes calculated columns invisible.
- **`relationship list` does not report inactive relationships' purpose:** `isActive: false` shows up but the reason (USERELATIONSHIP usage, role-playing dimension) lives in the measures that reference them. Grep `USERELATIONSHIP` across the TMDL export to find the consumers.
- **Snapshotting `--json` outputs to files captures connection-time state:** If someone edits the model between commands, your "documentation" mixes pre- and post-edit state. Wrap multi-command catalog runs in a single `pbi transaction begin` or do them after `pbi disconnect / connect` on a known model.
- **`advanced culture list` shows cultures, not which strings are translated:** A culture row in the list does not mean every label has a translation. Diff the per-culture string tables in the TMDL export to find gaps.
- **`expression list` includes both shared parameters and full M queries:** Both render as named expressions in the output. A parameter is just a single-line literal expression — easy to misclassify when generating a "data sources" section of docs.

