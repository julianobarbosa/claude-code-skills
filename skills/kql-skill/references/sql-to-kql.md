# SQL to KQL Translation Reference

## Concept Mapping

| SQL | KQL | Notes |
|-----|-----|-------|
| `SELECT` | `project` | Column selection |
| `SELECT *, computed` | `extend` | Add column without dropping others |
| `SELECT DISTINCT` | `distinct` | Unique rows |
| `FROM table` | `TableName` | Table is the starting point of the pipe |
| `WHERE` | `where` | Row filtering |
| `AND` / `OR` | `and` / `or` | Boolean operators |
| `IN (...)` | `in (...)` | Value set membership |
| `LIKE '%text%'` | `contains` or `has` | Use `has` when possible (faster) |
| `LIKE 'text%'` | `startswith` | Prefix match |
| `LIKE '%text'` | `endswith` | Suffix match |
| `GROUP BY` | `summarize ... by` | Aggregation |
| `HAVING` | `where` (after summarize) | Filter aggregated results |
| `ORDER BY` | `sort by` or `order by` | Both work identically |
| `TOP N` / `LIMIT N` | `top N by ...` or `take N` | `top` sorts, `take` is random |
| `JOIN` | `join kind=inner` | Always specify join kind |
| `LEFT JOIN` | `join kind=leftouter` | Left outer join |
| `UNION ALL` | `union` | Concatenate tables |
| `UNION` (deduplicated) | `union \| distinct *` | KQL union is UNION ALL by default |
| `INSERT` | `.ingest` | ADX only |
| `CREATE TABLE` | `.create table` | ADX only |
| `CASE WHEN` | `case()` or `iff()` | `iff` for binary, `case` for multi-branch |
| `CAST(x AS type)` | `tostring()`, `toint()`, etc. | Type-specific functions |
| `COALESCE` | `coalesce()` | Same name, same behavior |
| `COUNT(DISTINCT x)` | `dcount(x)` | Approximate by default |
| `DATE_TRUNC` | `bin()` | `bin(TimeGenerated, 1h)` |
| `DATEDIFF` | `datetime_diff()` | `datetime_diff('hour', dt1, dt2)` |
| `NOW()` | `now()` | Current UTC time |
| `INTERVAL` | Timespan literal | `1h`, `7d`, `30m` |
| `SUBSTR` | `substring()` | `substring(s, start, length)` |
| `CONCAT` | `strcat()` | `strcat(a, b, c)` |
| `LOWER` / `UPPER` | `tolower()` / `toupper()` | Usually unnecessary — operators are case-insensitive |
| `NULL` | `null` | Same concept |
| `IS NULL` | `isnull()` or `isempty()` | `isempty` also catches empty strings |
| `CTE (WITH)` | `let` | `let varName = expr;` |
| `Subquery` | `let` or inline `()` | Pipe-based, not nested |
| `PIVOT` | `pivot()` plugin or `summarize` | `evaluate pivot(...)` |
| `UNPIVOT` | `mv-expand` | Expand rows |
| `EXISTS` | `join kind=leftsemi` | Semi-join checks existence |
| `NOT EXISTS` | `join kind=leftanti` | Anti-join checks absence |

## Translation Examples

### Basic SELECT + WHERE + ORDER
```sql
SELECT EventID, Account, Computer, TimeGenerated
FROM SecurityEvent
WHERE EventID = 4625 AND TimeGenerated > '2024-01-01'
ORDER BY TimeGenerated DESC
LIMIT 100;
```
```kql
SecurityEvent
| where TimeGenerated > datetime(2024-01-01)
| where EventID == 4625
| project EventID, Account, Computer, TimeGenerated
| sort by TimeGenerated desc
| take 100
```

### GROUP BY with HAVING
```sql
SELECT Account, COUNT(*) as LoginCount
FROM SecurityEvent
WHERE EventID = 4624
GROUP BY Account
HAVING COUNT(*) > 100
ORDER BY LoginCount DESC;
```
```kql
SecurityEvent
| where EventID == 4624
| summarize LoginCount=count() by Account
| where LoginCount > 100
| sort by LoginCount desc
```

### JOIN
```sql
SELECT a.UserPrincipalName, a.ResultType, b.OperationName
FROM SigninLogs a
INNER JOIN AuditLogs b ON a.CorrelationId = b.CorrelationId
WHERE a.TimeGenerated > DATEADD(hour, -1, GETUTCDATE());
```
```kql
SigninLogs
| where TimeGenerated > ago(1h)
| join kind=inner (AuditLogs | where TimeGenerated > ago(1h)) on CorrelationId
| project UserPrincipalName, ResultType, OperationName
```

### CTE / WITH
```sql
WITH FailedLogins AS (
    SELECT Account, COUNT(*) as Failures
    FROM SecurityEvent
    WHERE EventID = 4625
    GROUP BY Account
),
SuccessLogins AS (
    SELECT Account, COUNT(*) as Successes
    FROM SecurityEvent
    WHERE EventID = 4624
    GROUP BY Account
)
SELECT f.Account, f.Failures, s.Successes
FROM FailedLogins f
JOIN SuccessLogins s ON f.Account = s.Account;
```
```kql
let FailedLogins = SecurityEvent
| where EventID == 4625
| summarize Failures=count() by Account;
let SuccessLogins = SecurityEvent
| where EventID == 4624
| summarize Successes=count() by Account;
FailedLogins
| join kind=inner SuccessLogins on Account
| project Account, Failures, Successes
```

### Subquery with EXISTS
```sql
SELECT DISTINCT Account
FROM SecurityEvent s1
WHERE EventID = 4625
AND EXISTS (
    SELECT 1 FROM SecurityEvent s2
    WHERE s2.Account = s1.Account AND s2.EventID = 4624
);
```
```kql
SecurityEvent
| where EventID == 4625
| distinct Account
| join kind=leftsemi (
    SecurityEvent | where EventID == 4624 | distinct Account
) on Account
```

## Key Mindset Shifts

1. **Pipes, not nesting** — KQL flows top-to-bottom through pipes. Where SQL nests subqueries, KQL uses `let` statements or inline parenthesized expressions.
2. **Table first** — In SQL, FROM comes after SELECT. In KQL, the table name starts the query and data flows through operators.
3. **No SELECT *; use project** — Always explicitly project the columns you need for readability and performance.
4. **Time is a first-class citizen** — `ago()`, `bin()`, timespan literals, and `TimeGenerated` are central to KQL in a way that datetime handling in SQL isn't.
5. **Aggregation syntax** — `summarize AggFunc() by GroupCol` replaces `SELECT AggFunc() ... GROUP BY GroupCol`.
