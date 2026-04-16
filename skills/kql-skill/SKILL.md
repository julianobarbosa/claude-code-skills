---
name: kql-skill
description: Kusto Query Language authoring, debugging, optimization, translation, and tooling for Azure Monitor, Sentinel, ADX, and Application Insights. USE WHEN user mentions 'KQL', 'Kusto', 'Log Analytics query', 'Sentinel query', 'hunting query', 'ADX query', 'Application Insights query', 'translate SQL to KQL', 'Splunk to KQL', 'optimize query', 'KQL performance', '.kql file', 'detection rule', 'analytics rule', 'threat hunting', 'Azure monitor query', 'log query', 'summarize operator', 'where TimeGenerated', OR any request involving querying Azure log/telemetry data. Even if the user doesn't say "KQL" explicitly — if they're asking about querying Azure logs, security events, or telemetry data, this skill applies.
---

# KQL Skill

Write, debug, optimize, translate, and automate KQL queries across Azure data platforms.

## Workflow Routing

| Workflow | Trigger | File |
|----------|---------|------|
| WriteQuery | "write a query", "create KQL", "query for", "find events where", "show me" | `workflows/WriteQuery.md` |
| DebugOptimize | "optimize", "slow query", "fix this KQL", "improve performance", "debug query" | `workflows/DebugOptimize.md` |
| Translate | "SQL to KQL", "Splunk to KQL", "SPL to KQL", "convert this query" | `workflows/Translate.md` |
| Tooling | "validate KQL", "run query via CLI", "automate query", "schedule alert", "REST API" | `workflows/Tooling.md` |

If no specific workflow matches, default to **WriteQuery**.

## Reference Files

Read these as needed — don't load everything upfront:

| Reference | When to Read | File |
|-----------|-------------|------|
| Operators & Functions | Writing or reviewing any query | `references/operators.md` |
| Service Tables | Need to know available tables for a specific service | `references/service-tables.md` |
| Patterns & Anti-patterns | Optimizing queries or reviewing for best practices | `references/patterns.md` |
| SQL-to-KQL Map | Translating from SQL | `references/sql-to-kql.md` |

## Sample Queries

The `samples/` directory contains production-ready `.kql` files organized by service. Reference these when writing similar queries — they demonstrate the expected file format and conventions.

## Output Format

Every generated query MUST use this `.kql` file format:

```kql
// ============================================================
// Title: <descriptive title>
// Service: <Log Analytics | Sentinel | ADX | App Insights>
// Tables: <comma-separated list of tables used>
// Description: <what this query does and when to use it>
// Parameters: <any variables the user should customize>
// Complexity: <Beginner | Intermediate | Advanced>
// ============================================================

// <the query, with inline comments for non-obvious logic>
```

## File Naming

Use kebab-case: `failed-sign-ins-by-location.kql`, `high-cpu-vms-last-24h.kql`

## Core Principles

1. **Always specify the target service** — KQL varies across Azure services. A query for Sentinel won't necessarily work in ADX.
2. **Time-bound by default** — Include `TimeGenerated` filters (or equivalent) to prevent full-table scans. Default to last 24 hours unless the user specifies otherwise.
3. **Performance first** — Filter early (`where` before `join`/`summarize`), use `has` over `contains` for string matching, avoid `*` projections on wide tables.
4. **Parameterize** — Use `let` statements for values the user will customize (time ranges, thresholds, resource names).
5. **Explain the query** — Add inline comments for non-trivial logic, especially `mv-expand`, `parse`, regex, and complex `summarize` expressions.

## Service-Specific Notes

- **Log Analytics**: No management commands (`.create`, `.alter`). Tables like `Heartbeat`, `Perf`, `Event`, `Syslog`, `AzureActivity`.
- **Sentinel**: Extends Log Analytics with `SecurityEvent`, `SecurityAlert`, `SigninLogs`, `ThreatIntelligenceIndicator`, plus custom analytics rule functions.
- **ADX**: Full KQL engine — supports management commands, materialized views, continuous exports, external tables. Most powerful but queries may not be portable.
- **Application Insights**: Shares Log Analytics engine. Key tables: `requests`, `dependencies`, `exceptions`, `traces`, `customEvents`, `performanceCounters`.

## Examples

**Example 1 — Write Query:**
> "Write a KQL query to find failed sign-ins from outside the US in the last 7 days"
> Routes to: `workflows/WriteQuery.md` → targets Sentinel/Log Analytics, uses `SigninLogs`

**Example 2 — Optimize:**
> "This query takes forever to run, can you make it faster?" (pastes KQL)
> Routes to: `workflows/DebugOptimize.md`

**Example 3 — Translate:**
> "Convert this SQL query to KQL: SELECT * FROM events WHERE severity > 3 GROUP BY source"
> Routes to: `workflows/Translate.md`

**Example 4 — Tooling:**
> "How do I run this query from Azure CLI and export to CSV?"
> Routes to: `workflows/Tooling.md`
