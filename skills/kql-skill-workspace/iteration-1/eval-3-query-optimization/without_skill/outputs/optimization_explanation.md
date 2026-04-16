# KQL Query Optimization Explanation

## Original Query

```kql
SecurityEvent
| where EventID == 4625
| where tolower(Account) contains "admin"
| join kind=inner SigninLogs on $left.Account == $right.UserPrincipalName
| summarize count() by Account, Computer
| where count_ > 5
| sort by count_ desc
```

## Optimized Query

```kql
let SuspectAccounts =
    SecurityEvent
    | where TimeGenerated > ago(1d)
    | where EventID == 4625
    | where Account has "admin"
    | summarize FailedLogins = count() by Account, Computer
    | where FailedLogins > 5;

SuspectAccounts
| join kind=inner (
    SigninLogs
    | where TimeGenerated > ago(1d)
    | project UserPrincipalName
) on $left.Account == $right.UserPrincipalName
| project Account, Computer, FailedLogins
| sort by FailedLogins desc
```

## Changes and Rationale

### 1. Add a Time Bound (`TimeGenerated > ago(1d)`)
**Problem:** The original query has no time filter, forcing Sentinel to scan the full table history.  
**Fix:** Adding `where TimeGenerated > ago(1d)` (or your desired window) dramatically reduces scanned rows. `TimeGenerated` is a partitioning key in Log Analytics — this is the single highest-impact optimization possible.

### 2. Replace `tolower(Account) contains "admin"` with `Account has "admin"`
**Problem:** `tolower()` + `contains` is a full string transformation followed by a substring scan. Neither is index-friendly, and `contains` performs a regex-style linear scan on every row.  
**Fix:** `has` is case-insensitive by default in KQL and uses term-level indexing, making it significantly faster for token-based lookups.

### 3. Summarize and Filter *Before* the Join
**Problem:** The original query joins all matching `SecurityEvent` rows against the entirety of `SigninLogs` before aggregating and filtering. Joins are the most expensive operation — feeding them large inputs is the main cause of slowness.  
**Fix:** Move `summarize` and `where count_ > 5` before the join. This reduces the left-side dataset to only accounts with more than 5 failures, potentially shrinking the join input by orders of magnitude.

### 4. Project Only Needed Columns in `SigninLogs`
**Problem:** The original join pulls every column from `SigninLogs` into memory during the join operation.  
**Fix:** Use `| project UserPrincipalName` inside the join subquery to pass only the column needed for the join key, reducing memory pressure and data shuffling.

### 5. Rename `count_` to `FailedLogins`
This is a readability improvement. The auto-generated column name `count_` is fragile (it changes if you rename the aggregation) and less descriptive.

## Summary of Impact

| Issue | Original | Optimized |
|---|---|---|
| Table scan scope | Full history | Time-bounded (e.g., last 1 day) |
| String matching | `tolower()+contains` (no index) | `has` (term index) |
| Join input size | All filtered rows | Pre-aggregated + pre-filtered rows |
| SigninLogs columns in join | All columns | Only `UserPrincipalName` |
| Readability | `count_` | `FailedLogins` |
