# DebugOptimize Workflow

## Steps

1. **Read the query** — Understand what it's trying to do before changing anything. Identify the target service.

2. **Check for common issues** — Read `references/patterns.md` for the anti-patterns checklist. Look for:
   - Missing time filters (full table scan)
   - `contains` where `has` would work (10x slower)
   - `*` in project (unnecessary column transfer)
   - Late filtering (WHERE after JOIN or SUMMARIZE)
   - Unnecessary `tolower()`/`toupper()` — KQL string operators are case-insensitive by default
   - `search *` instead of querying specific tables
   - Cartesian joins (missing `kind=` specification)
   - `distinct` + `count` instead of `dcount()`

3. **Identify the bottleneck** — Is it:
   - **Data volume**: needs tighter time/column filters
   - **Join explosion**: wrong join kind or missing key
   - **Serialization**: unnecessary `serialize` or `prev()`/`next()` on large datasets
   - **Regex overuse**: replace `matches regex` with `has`/`startswith`/`endswith` where possible

4. **Apply fixes** — Make the minimum changes needed. Show before/after with inline comments explaining each change.

5. **Suggest query hints** if applicable:
   - `hint.strategy=shuffle` for large joins
   - `hint.num_partitions=N` for parallel execution
   - `hint.materialized=true` for reused subqueries
   - `materialize()` to avoid recomputation of shared expressions

## Performance Rules of Thumb

| Operator | Fast | Slow |
|----------|------|------|
| String match | `has`, `has_any`, `startswith` | `contains`, `matches regex` |
| Case handling | Default (case-insensitive) | `tolower()`, `toupper()` |
| Existence check | `isnotempty()`, `isnotnull()` | `!= ""`, `!= null` |
| Count distinct | `dcount()` | `distinct \| count` |
| Multi-table | `union` with specific tables | `search *` |
| Projection | `project` needed columns | `project *` or no project |
| Time filter | First `where` clause | After joins/aggregations |
