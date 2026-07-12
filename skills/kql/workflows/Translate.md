# Translate Workflow

Converts SQL or Splunk SPL queries to idiomatic KQL.

## Steps

1. **Identify the source language** — SQL or Splunk SPL. Read the query to understand its intent.

2. **Map the concepts** — Read `references/sql-to-kql.md` for the SQL mapping table. For SPL, use the mapping below.

3. **Identify the target service** — Ask which Azure service this will run on. This determines available tables and functions.

4. **Translate** — Don't do a literal 1:1 translation. Write idiomatic KQL that achieves the same result using KQL's strengths:
   - Pipe-based flow instead of nested subqueries
   - `let` statements instead of CTEs
   - `summarize` instead of GROUP BY
   - `extend` instead of computed columns in SELECT
   - `mv-expand` instead of UNNEST/LATERAL
   - Native time functions (`ago()`, `bin()`) instead of date arithmetic

5. **Output as .kql file** with the standard header. Note the original language in the description.

## SPL to KQL Quick Reference

| Splunk SPL | KQL Equivalent |
|------------|----------------|
| `index=main` | `TableName` (specify the table directly) |
| `search` | `where` |
| `stats count by field` | `summarize count() by field` |
| `stats dc(field)` | `summarize dcount(field)` |
| `eval newfield=if(cond, a, b)` | `extend newfield=iff(cond, a, b)` |
| `table field1, field2` | `project field1, field2` |
| `sort -count` | `sort by count desc` |
| `dedup field` | `summarize take_any(*) by field` |
| `top 10 field` | `top 10 by field` |
| `timechart span=1h count` | `summarize count() by bin(TimeGenerated, 1h) \| render timechart` |
| `rex field=raw "(?<name>pattern)"` | `extend name=extract("pattern", 1, raw)` |
| `lookup` | `join kind=inner` or `lookup` |
| `mvexpand field` | `mv-expand field` |
| `transaction` | `summarize` with `make_list()` + session windowing |
| `spath` | `parse_json()` + `bag_unpack()` |
| `earliest(_time)` | `min(TimeGenerated)` |
| `latest(_time)` | `max(TimeGenerated)` |
