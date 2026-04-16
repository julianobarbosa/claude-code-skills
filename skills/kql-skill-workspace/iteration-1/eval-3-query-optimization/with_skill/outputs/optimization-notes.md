# Query Optimization Notes

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

## Issues Found

### 1. Missing Time Filter (Critical — Full Table Scan)
**Problem:** No `TimeGenerated` filter means every query scans the full retention window (90+ days by default in Sentinel). On a busy environment, `SecurityEvent` can hold hundreds of millions of rows.

**Fix:** Add `| where TimeGenerated > ago(1d)` as the very first `where` clause. This leverages the time-range index and drastically reduces data scanned.

---

### 2. Unnecessary `tolower()` (Performance)
**Problem:** `tolower(Account) contains "admin"` is slow for two reasons:
- `tolower()` forces a per-row string transformation before comparison.
- KQL string operators (`contains`, `has`, `==`, etc.) are **case-insensitive by default**. The `tolower()` call is redundant and wastes CPU.

**Fix:** Remove `tolower()`.

---

### 3. `contains` Instead of `has` (Performance — ~10x slower)
**Problem:** `contains` performs an O(n) substring scan across every row value. It cannot use the term index.

`has` uses the inverted term index (O(1) lookup) and is approximately 10x faster. The difference: `has` matches on whole token boundaries, while `contains` matches any substring position.

**Fix:** Use `| where Account has "admin"` — this correctly matches accounts like `CORP\admin`, `CORP\administrator`, `local_admin`, etc.

---

### 4. Join Without Pre-filtering SigninLogs (Performance)
**Problem:** `SigninLogs` is joined with no time filter or column projection applied. This causes the engine to load the full `SigninLogs` table into memory before joining.

**Fix:** Wrap the right side of the join in a subquery that applies the same `TimeGenerated` filter and a `project` to only the needed columns:
```kql
| join kind=inner (
    SigninLogs
    | where TimeGenerated > ago(1d)
    | project UserPrincipalName, SigninTime = TimeGenerated, ResultType, IPAddress
) on ...
```

---

### 5. Join Key Mismatch — Logic Bug (Correctness)
**Problem:** `$left.Account == $right.UserPrincipalName` compares two incompatible formats:
- `SecurityEvent.Account` is typically in `DOMAIN\username` format (e.g., `CORP\jsmith`).
- `SigninLogs.UserPrincipalName` is in UPN/email format (e.g., `jsmith@corp.com`).

These will almost never match directly, making the join return near-zero results silently.

**Fix:** Extract just the username portion from each side before joining:
```kql
| extend AccountUsername = tolower(tostring(split(Account, "\\")[1]))
```
and on the SigninLogs side:
```kql
| extend AccountUsername = tolower(tostring(split(UserPrincipalName, "@")[0]))
```
Then join on `AccountUsername`.

---

### 6. No Column Projection Before Join (Performance)
**Problem:** `SecurityEvent` carries 50+ columns through the pipeline into the join. Only `Account` and `Computer` are ultimately used.

**Fix:** Add `| project TimeGenerated, Account, Computer` before the `summarize` to reduce the data volume shuffled into the join.

---

### 7. Join Hint for Large Tables (Performance — Optional)
**Fix:** Add `hint.strategy = shuffle` to the join. This distributes the join computation across nodes rather than concentrating it, beneficial when `SigninLogs` is large.

---

## Summary of Changes

| Issue | Original | Optimized |
|-------|----------|-----------|
| Time filter | Missing | `TimeGenerated > ago(lookback)` added first |
| `tolower()` | Present (unnecessary) | Removed |
| String match | `contains` (O(n) scan) | `has` (indexed, ~10x faster) |
| SigninLogs filter | None | Time-bounded + projected |
| Join key | Direct field mismatch | Username extracted from both sides |
| Column projection | Missing | `project` added before join |
| Join hint | None | `hint.strategy = shuffle` added |
| Parameterization | Hardcoded | `let` statements for lookback, threshold, keyword |
