---
name: power-bi-deployment
description: Import and export TMDL/TMSL formats, manage model lifecycle with transactions, and version-control Power BI semantic models using pbi-cli. Invoke this skill whenever the user mentions "deploy", "export", "import", "TMDL", "TMSL", "version control", "git", "backup", "migrate", "transaction", "commit changes", "rollback", or wants to save/restore model state.
tools: pbi-cli
---

# Power BI Deployment Skill

Manage model lifecycle with TMDL export/import, transactions, and version control.

## Prerequisites

```bash
pipx install pbi-cli-tool
pbi-cli skills install
pbi connect
```

## Connecting to Targets

```bash
# Local Power BI Desktop (auto-detects port)
pbi connect

# Local with explicit port
pbi connect -d localhost:54321

# Named connections for switching
pbi connect -d localhost:54321 --name dev
pbi connections list
pbi connections last
pbi disconnect
```

## TMDL Export and Import

TMDL (Tabular Model Definition Language) is the text-based format for version-controlling Power BI models.

```bash
# Export entire model to TMDL folder
pbi database export-tmdl ./model-tmdl/

# Import TMDL folder into connected model
pbi database import-tmdl ./model-tmdl/
```

## TMSL Export

```bash
# Export as TMSL JSON (for SSAS/AAS compatibility)
pbi database export-tmsl
```

## TMDL Diff (Compare Snapshots)

Compare two TMDL export folders to see what changed between snapshots.
Useful for CI/CD pipelines ("what did this PR change in the model?").

```bash
# Compare two exports
pbi database diff-tmdl ./model-before/ ./model-after/

# JSON output for CI/CD scripting
pbi --json database diff-tmdl ./baseline/ ./current/
```

Returns a structured summary:
- **tables**: added, removed, and changed tables with per-table entity diffs
  (measures, columns, partitions, hierarchies added/removed/changed)
- **relationships**: added, removed, and changed relationships
- **model**: changed model-level properties (e.g. culture, default power bi dataset version)
- **summary**: total counts of all changes

LineageTag-only changes (GUID regeneration without real edits) are automatically
filtered out to avoid false positives.

No connection to Power BI Desktop is needed -- works on exported folders.

## Database Operations

```bash
# List databases on the connected server
pbi database list
```

## Transaction Management

Use transactions for atomic multi-step changes:

```bash
# Begin a transaction
pbi transaction begin

# Make changes
pbi measure create "New KPI" -e "SUM(Sales[Amount])" -t Sales
pbi measure create "Another KPI" -e "COUNT(Sales[OrderID])" -t Sales

# Commit all changes atomically
pbi transaction commit

# Or rollback if something went wrong
pbi transaction rollback
```

## Table Refresh

```bash
# Refresh individual tables
pbi table refresh Sales --type Full
pbi table refresh Sales --type Automatic
pbi table refresh Sales --type Calculate
pbi table refresh Sales --type DataOnly
```

## Workflow: Version Control with Git

```bash
# 1. Export model to TMDL
pbi database export-tmdl ./model/

# 2. Commit to git
cd model/
git add .
git commit -m "feat: add new revenue measures"

# 3. Later, import back into Power BI Desktop
pbi connect
pbi database import-tmdl ./model/
```

## Workflow: Inspect Model Before Deploy

```bash
# Get model metadata
pbi --json model get

# Check model statistics
pbi --json model stats

# List all objects
pbi --json table list
pbi --json measure list
pbi --json relationship list
```

## Best Practices

- Always export TMDL before making changes (backup)
- Use transactions for multi-object changes
- Test changes in dev before deploying to production
- Use `--json` for scripted deployments
- Store TMDL in git for version history
- Use named connections (`--name`) to avoid accidental changes to wrong environment

---

## Gotchas

- **`import-tmdl` is not atomic across the whole folder:** If one file fails to parse mid-import, partially-applied changes stick in the connected model. Always `pbi transaction begin` around `import-tmdl`, or export a backup first so rollback is just a re-import.
- **`diff-tmdl` filters out lineageTag-only changes by design:** Helpful for noise but it also masks legitimate re-tagging that downstream Power BI Service references depend on (deployment pipelines, perspectives, datamarts). Diff the raw folders with `git diff` when investigating broken references in Service.
- **Named connections persist across pbi-cli sessions:** `--name prod` survives even after you've closed Desktop. Running a destructive `import-tmdl` thinking you're on `dev` is the classic foot-gun. Always `pbi connections last` before mutating commands.
- **`table refresh --type Full` rebuilds calculated columns and relationships:** On large tables this triggers a long re-process and locks the model. Prefer `--type DataOnly` for production refreshes; reserve `Full` for schema changes.
- **TMSL export is JSON; TMDL export is folders of text:** The two formats are NOT interchangeable for git diffs — TMSL collapses all measures into one large JSON, killing clean diffs. Use TMDL for version control and reserve TMSL for SSAS/AAS compatibility.
- **`transaction rollback` only reverts metadata changes, not data refreshes:** If you ran `table refresh` inside the transaction, the refreshed data stays after rollback. Refreshes commit out-of-band.

