---
name: power-bi-diagnostics
description: Troubleshoot Power BI model performance, trace query execution, manage caches, and verify the pbi-cli environment using pbi-cli. Invoke this skill whenever the user says "pbi not working", "setup issues", "connection failed", "slow query", "performance", "profiling", "tracing", "health check", "model audit", "pbi setup", or encounters any pbi-cli error. This is the first skill to check when something goes wrong with pbi-cli.
tools: pbi-cli
---

# Power BI Diagnostics Skill

Troubleshoot performance, trace queries, and verify the pbi-cli environment.

## Prerequisites

```bash
pipx install pbi-cli-tool
pbi-cli skills install
pbi connect
```

## Environment Check

```bash
# Verify pythonnet and .NET DLLs are installed
pbi setup

# Show detailed environment info (version, DLL paths, pythonnet status)
pbi setup --info
pbi --json setup --info

# Check CLI version
pbi --version
```

## Quick Troubleshooting

If pbi-cli isn't working, run these checks in order:

```bash
# 1. Is pbi-cli installed correctly?
pbi --version
pbi setup --info

# 2. Is Power BI Desktop running with a model open?
pbi connect

# 3. Is the connection still alive?
pbi connections last

# 4. Can you query the model?
pbi dax execute "EVALUATE ROW(\"test\", 1)"
```

## Model Health Check

```bash
# Quick model overview
pbi --json model get

# Object counts (tables, columns, measures, relationships, partitions)
pbi --json model stats

# List all tables with column/measure counts
pbi --json table list
```

## Query Tracing

Capture diagnostic events during DAX query execution:

```bash
# Start a trace
pbi trace start

# Execute the query you want to profile
pbi dax execute "EVALUATE SUMMARIZECOLUMNS(Products[Category], \"Total\", SUM(Sales[Amount]))"

# Stop the trace
pbi trace stop

# Fetch captured trace events
pbi --json trace fetch

# Export trace events to a file
pbi trace export ./trace-output.json
```

## Cache Management

```bash
# Clear the formula engine cache (do this before benchmarking)
pbi dax clear-cache
```

## Connection Diagnostics

```bash
# List all saved connections
pbi connections list
pbi --json connections list

# Show the last-used connection
pbi connections last

# Reconnect to a specific data source
pbi connect -d localhost:54321

# Disconnect
pbi disconnect
```

## Workflow: Profile a Slow Query

```bash
# 1. Clear cache for a clean benchmark
pbi dax clear-cache

# 2. Start tracing
pbi trace start

# 3. Run the slow query
pbi dax execute "EVALUATE SUMMARIZECOLUMNS(Products[Category], \"Total\", SUM(Sales[Amount]))" --timeout 300

# 4. Stop tracing
pbi trace stop

# 5. Export trace for analysis
pbi trace export ./slow-query-trace.json

# 6. Review trace events
pbi --json trace fetch
```

## Workflow: Model Health Audit

```bash
# 1. Model overview
pbi --json model get
pbi --json model stats

# 2. Check table sizes and structure
pbi --json table list

# 3. Review relationships
pbi --json relationship list

# 4. Check security roles
pbi --json security-role list

# 5. Export full model for offline review
pbi database export-tmdl ./audit-export/
```

## Best Practices

- Clear cache before benchmarking: `pbi dax clear-cache`
- Use `--timeout` for long-running queries to avoid premature cancellation
- Export traces to files for sharing with teammates
- Run `pbi setup --info` first when troubleshooting environment issues
- Use `--json` output for automated monitoring scripts
- Use `pbi repl` for interactive debugging sessions with persistent connection

---

## Gotchas

- **`pbi connect` succeeds even against a stale port:** Desktop reassigns its local Analysis Services port on every restart. Connection from the previous session may bind to a port now occupied by a different model — queries return data from the wrong file. After Desktop restart, always `pbi connect` again rather than reusing the saved connection.
- **`pbi setup --info` reports pythonnet status, not runtime health:** A green `pythonnet: ok` line means the DLL loaded — it does NOT verify the AdomdClient can talk to your model. Confirm with a smoke query like `EVALUATE ROW("test", 1)` before assuming the environment is healthy.
- **Trace events arrive asynchronously:** `pbi trace fetch` immediately after `trace stop` may return an empty list. Wait 1-2 seconds or call fetch in a short retry loop — events buffer in the AS server before flushing.
- **Clearing formula engine cache leaves storage engine cache intact:** Repeat-running a benchmark query after `clear-cache` still hits cached VertiPaq segments. For a true cold benchmark, restart Desktop or reconnect.
- **`model stats` counts hidden objects too:** Calculation groups, auto-date hierarchies, and translation tables inflate the table count vs. what a user sees in the field list. Cross-check with `table list` filtered on visibility.
- **`--timeout` is in seconds, not milliseconds:** Easy slip — `--timeout 300` is 5 minutes, not 0.3 seconds. Default is 60s, which silently kills any moderately-complex query on a cold cache.

