# WriteQuery Workflow

## Steps

1. **Identify the target service** — Ask or infer: Log Analytics, Sentinel, ADX, or Application Insights? This determines available tables and syntax.

2. **Identify tables** — Read `references/service-tables.md` if unsure which tables hold the data the user needs. Pick the narrowest table that covers the requirement.

3. **Check for similar samples** — Look in `samples/` for queries targeting the same service/domain. Reuse patterns rather than starting from scratch.

4. **Write the query** using these KQL best practices:
   - Start with `let` declarations for parameters (time range, thresholds, resource filters)
   - Filter with `where` as early as possible — push time filters and equality checks first
   - Use `has` instead of `contains` for whole-token string matching (10x faster)
   - Use `in` instead of chained `or` for multiple value checks
   - Project only needed columns with `project` or `project-away` to reduce data transfer
   - For joins, put the smaller table on the right side
   - Add `| take 100` or `| limit 100` during development to preview results

5. **Format as a .kql file** following the output format in the main SKILL.md — include the comment header block with title, service, tables, description, parameters, and complexity.

6. **Explain the query** — After the code block, provide a brief walkthrough of what each major step does, especially for intermediate/advanced queries. Mention any gotchas or service-specific behaviors.

## Common Query Patterns

### Aggregation with time bins
```kql
let timeRange = 24h;
TableName
| where TimeGenerated > ago(timeRange)
| summarize Count=count() by bin(TimeGenerated, 1h), ColumnName
| render timechart
```

### Top-N analysis
```kql
TableName
| where TimeGenerated > ago(7d)
| summarize Count=count() by ColumnName
| top 10 by Count desc
```

### Join pattern (small right table)
```kql
let lookupTable = materialize(
    SmallTable | where Condition | project Key, Value
);
LargeTable
| where TimeGenerated > ago(1d)
| join kind=inner lookupTable on Key
```

### Multi-value expansion
```kql
TableName
| mv-expand parse_json(JsonColumn)
| evaluate bag_unpack(JsonColumn)
```
