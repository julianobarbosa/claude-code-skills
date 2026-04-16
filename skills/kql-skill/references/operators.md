# KQL Operators & Functions Reference

## Table of Contents
- [Tabular Operators](#tabular-operators)
- [Scalar Functions](#scalar-functions)
- [Aggregation Functions](#aggregation-functions)
- [String Operators](#string-operators)
- [DateTime Functions](#datetime-functions)
- [Dynamic / JSON Functions](#dynamic--json-functions)
- [Rendering](#rendering)

## Tabular Operators

| Operator | Purpose | Example |
|----------|---------|---------|
| `where` | Filter rows | `T \| where Status == "Error"` |
| `extend` | Add computed columns | `T \| extend Duration = EndTime - StartTime` |
| `project` | Select/rename columns | `T \| project Name, Size=FileSize` |
| `project-away` | Remove columns | `T \| project-away TempCol, InternalId` |
| `project-reorder` | Reorder columns | `T \| project-reorder Name, Status, *` |
| `summarize` | Aggregate | `T \| summarize Count=count() by Category` |
| `sort by` / `order by` | Sort rows | `T \| sort by TimeGenerated desc` |
| `top` | Top N rows | `T \| top 10 by Count desc` |
| `take` / `limit` | Sample N rows | `T \| take 100` |
| `join` | Combine tables | `T1 \| join kind=inner T2 on Key` |
| `union` | Concatenate tables | `union Table1, Table2` |
| `distinct` | Unique rows | `T \| distinct Category` |
| `count` | Row count | `T \| count` |
| `search` | Full-text search | `search "error" in (Table1, Table2)` |
| `parse` | Extract from string | `T \| parse Message with "User " User " logged in"` |
| `mv-expand` | Expand arrays | `T \| mv-expand Tags` |
| `mv-apply` | Apply per element | `T \| mv-apply Tag to typeof(string) on (where Tag startswith "env")` |
| `evaluate` | Plugin invocation | `T \| evaluate autocluster()` |
| `render` | Visualize | `T \| render timechart` |
| `serialize` | Row numbering | `T \| serialize RowNum=row_number()` |
| `lookup` | Dimension lookup | `T \| lookup DimTable on Key` |
| `as` | Name subexpression | `T \| where X > 0 \| as FilteredT` |
| `fork` | Parallel branches | `T \| fork (summarize count()) (top 10 by X)` |
| `facet` | Auto-group | `T \| facet by Category` |
| `sample` | Random sample | `T \| sample 100` |
| `sample-distinct` | Distinct random sample | `T \| sample-distinct 10 of Category` |
| `getschema` | Column metadata | `T \| getschema` |

## Join Kinds

| Kind | Behavior |
|------|----------|
| `inner` | Only matching rows from both |
| `leftouter` | All left + matching right (nulls for non-matches) |
| `rightouter` | All right + matching left |
| `fullouter` | All from both |
| `leftanti` | Left rows with NO match in right |
| `rightanti` | Right rows with NO match in left |
| `leftsemi` | Left rows with a match in right (no right columns) |
| `rightsemi` | Right rows with a match in left |

## Scalar Functions

### Type Conversion
- `tostring()`, `toint()`, `tolong()`, `todouble()`, `toreal()`, `todecimal()`
- `tobool()`, `todatetime()`, `totimespan()`, `toguid()`
- `parse_json()` / `todynamic()` — parse JSON string to dynamic

### Conditional
- `iff(condition, ifTrue, ifFalse)` — ternary
- `iif(condition, ifTrue, ifFalse)` — alias for iff
- `case(cond1, val1, cond2, val2, ..., default)` — multi-branch
- `coalesce(a, b, c)` — first non-null value
- `max_of(a, b)`, `min_of(a, b)` — scalar min/max

### Null Handling
- `isempty()` / `isnotempty()` — empty string or null
- `isnull()` / `isnotnull()` — null check
- `coalesce()` — first non-null

## Aggregation Functions

| Function | Purpose |
|----------|---------|
| `count()` | Row count |
| `countif(predicate)` | Conditional count |
| `dcount(column)` | Approximate distinct count |
| `dcountif(column, predicate)` | Conditional distinct count |
| `sum(column)` | Sum |
| `sumif(column, predicate)` | Conditional sum |
| `avg(column)` | Average |
| `avgif(column, predicate)` | Conditional average |
| `min(column)`, `max(column)` | Min/max |
| `percentile(column, N)` | Nth percentile |
| `percentiles(column, N1, N2)` | Multiple percentiles |
| `stdev(column)` | Standard deviation |
| `variance(column)` | Variance |
| `make_list(column)` | Collect into array |
| `make_set(column)` | Collect unique into array |
| `make_bag(column)` | Merge dynamic objects |
| `arg_min(column, *)` | Row with min value |
| `arg_max(column, *)` | Row with max value |
| `take_any(column)` | Any value (non-deterministic) |
| `binary_all_and()`, `binary_all_or()`, `binary_all_xor()` | Bitwise aggregates |
| `hll(column)` | HyperLogLog sketch |
| `tdigest(column)` | T-Digest sketch |

## String Operators

| Operator | Case | Description |
|----------|------|-------------|
| `==` | Sensitive | Exact match |
| `=~` | Insensitive | Exact match |
| `!=` | Sensitive | Not equal |
| `!~` | Insensitive | Not equal |
| `has` | Insensitive | Contains whole term |
| `!has` | Insensitive | Doesn't contain term |
| `has_cs` | Sensitive | Contains whole term |
| `has_any` | Insensitive | Contains any term |
| `has_all` | Insensitive | Contains all terms |
| `contains` | Insensitive | Substring match (slow) |
| `!contains` | Insensitive | No substring |
| `contains_cs` | Sensitive | Substring match |
| `startswith` | Insensitive | Prefix |
| `endswith` | Insensitive | Suffix |
| `matches regex` | Sensitive | Regex match |
| `in` | Sensitive | Value in set |
| `in~` | Insensitive | Value in set |
| `!in` | Sensitive | Value not in set |
| `between` | — | Range (inclusive) |

### String Functions
- `strcat(a, b, ...)` — concatenate
- `strlen(s)` — length
- `substring(s, start, length)` — extract
- `split(s, delimiter)` — split to array
- `replace_string(s, old, new)` — replace
- `replace_regex(s, pattern, rewrite)` — regex replace
- `extract(regex, captureGroup, s)` — regex extract
- `extract_all(regex, s)` — all regex matches
- `trim(regex, s)` — trim characters
- `tolower(s)`, `toupper(s)` — case conversion
- `url_encode()`, `url_decode()` — URL encoding
- `base64_encode_tostring()`, `base64_decode_tostring()` — Base64
- `hash_sha256(s)` — SHA-256 hash

## DateTime Functions

- `ago(timespan)` — relative past (`ago(1h)`, `ago(7d)`)
- `now()` — current UTC time
- `datetime(2024-01-15)` — literal datetime
- `bin(datetime, timespan)` — round down to bin (`bin(TimeGenerated, 1h)`)
- `startofday()`, `startofweek()`, `startofmonth()`, `startofyear()` — period start
- `endofday()`, `endofweek()`, `endofmonth()`, `endofyear()` — period end
- `datetime_diff(unit, dt1, dt2)` — difference in units
- `datetime_add(unit, amount, dt)` — add to datetime
- `format_datetime(dt, format)` — format as string
- `dayofweek(dt)` — day of week (timespan)
- `getmonth(dt)`, `getyear(dt)` — extract parts

### Timespan Literals
`1d` (day), `1h` (hour), `1m` (minute), `1s` (second), `1ms`, `1tick`

## Dynamic / JSON Functions

- `parse_json(s)` / `todynamic(s)` — parse JSON string
- `bag_unpack(dynamic)` — expand bag to columns (use with `evaluate`)
- `bag_keys(dynamic)` — get keys
- `bag_has_key(dynamic, key)` — check key exists
- `bag_merge(bag1, bag2)` — merge bags
- `pack(k1, v1, k2, v2)` — create bag
- `pack_all()` — all columns into one bag
- `array_length(arr)` — array size
- `array_index_of(arr, value)` — find index
- `array_slice(arr, start, end)` — slice
- `array_concat(arr1, arr2)` — concatenate
- `array_sort_asc(arr)`, `array_sort_desc(arr)` — sort
- `set_difference(arr1, arr2)` — set operations
- `set_intersect(arr1, arr2)`, `set_union(arr1, arr2)`
- `treepath(dynamic)` — all paths in JSON

## Rendering

```kql
| render timechart          // line chart over time
| render barchart           // bar chart
| render piechart           // pie chart
| render scatterchart       // scatter plot
| render areachart          // area chart
| render stackedareachart   // stacked area
| render columnchart        // column chart
| render anomalychart       // with anomaly detection
| render ladderchart        // ladder/waterfall
| render table              // explicit table (default)
```

Rendering properties:
```kql
| render timechart with (title="CPU Usage", xtitle="Time", ytitle="Percent")
```
