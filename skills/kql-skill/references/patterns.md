# KQL Patterns & Anti-patterns

## Table of Contents
- [Performance Patterns](#performance-patterns)
- [Anti-patterns](#anti-patterns)
- [Security Hunting Patterns](#security-hunting-patterns)
- [Time-series Patterns](#time-series-patterns)
- [Data Enrichment Patterns](#data-enrichment-patterns)

---

## Performance Patterns

### 1. Filter Early, Filter Hard
```kql
// GOOD — time filter + equality first, then expensive operations
SecurityEvent
| where TimeGenerated > ago(1h)
| where EventID == 4625
| where AccountType == "User"
| summarize FailCount=count() by Account, Computer

// BAD — summarize all, then filter
SecurityEvent
| summarize FailCount=count() by Account, Computer, EventID
| where EventID == 4625
```

### 2. Use `has` Over `contains`
`has` uses the term index (O(1) lookup). `contains` does a substring scan (O(n)).
```kql
// GOOD — 10x faster for whole-word matches
Syslog | where SyslogMessage has "error"

// BAD — substring scan, no index
Syslog | where SyslogMessage contains "error"
```

Use `contains` only when you need true substring matching (e.g., "err" matching "error").

### 3. Materialize Shared Subqueries
```kql
// GOOD — computed once, reused twice
let activeUsers = materialize(
    SigninLogs
    | where TimeGenerated > ago(1d)
    | distinct UserPrincipalName
);
let userCount = activeUsers | count;
let topUsers = activeUsers
| join kind=inner SigninLogs on UserPrincipalName
| summarize count() by UserPrincipalName
| top 10 by count_;
```

### 4. Efficient Joins
```kql
// GOOD — smaller table on the right, specific join kind
LargeTable
| where TimeGenerated > ago(1h)
| join kind=leftsemi SmallLookup on CommonKey

// BAD — no kind specified (defaults to innerunique, which deduplicates left), large table on right
SmallLookup
| join LargeTable on CommonKey
```

### 5. Use `in` for Multiple Values
```kql
// GOOD
SecurityEvent | where EventID in (4624, 4625, 4634, 4648)

// BAD
SecurityEvent | where EventID == 4624 or EventID == 4625 or EventID == 4634 or EventID == 4648
```

### 6. Limit Columns Early
```kql
// GOOD — project before expensive operations
SecurityEvent
| where TimeGenerated > ago(1d)
| project TimeGenerated, Account, Computer, EventID
| summarize count() by Account

// BAD — carries all 50+ columns through the pipeline
SecurityEvent
| where TimeGenerated > ago(1d)
| summarize count() by Account
```

---

## Anti-patterns

### 1. Missing Time Filter
```kql
// BAD — scans entire retention (90 days+)
SecurityEvent | where EventID == 4625 | count

// GOOD
SecurityEvent | where TimeGenerated > ago(24h) | where EventID == 4625 | count
```

### 2. Unnecessary Case Conversion
```kql
// BAD — tolower is expensive and unnecessary
SigninLogs | where tolower(UserPrincipalName) == "user@company.com"

// GOOD — =~ is case-insensitive
SigninLogs | where UserPrincipalName =~ "user@company.com"
```

### 3. `search *` for Known Tables
```kql
// BAD — searches every table in the workspace
search "malware"

// GOOD — target specific tables
union SecurityEvent, SecurityAlert
| where * has "malware"
```

### 4. `distinct` + `count` Instead of `dcount`
```kql
// BAD — materializes all distinct values, then counts
SigninLogs | distinct UserPrincipalName | count

// GOOD — approximate count, much faster
SigninLogs | summarize dcount(UserPrincipalName)
```

### 5. Regex When Simpler Operators Work
```kql
// BAD — regex is expensive
Syslog | where SyslogMessage matches regex "^Failed"

// GOOD — startswith uses the index
Syslog | where SyslogMessage startswith "Failed"
```

### 6. Joining Without Filtering First
```kql
// BAD — joins full tables
SigninLogs | join AuditLogs on CorrelationId

// GOOD — filter both sides first
SigninLogs
| where TimeGenerated > ago(1h)
| where ResultType != 0
| join kind=inner (
    AuditLogs
    | where TimeGenerated > ago(1h)
    | where OperationName has "password"
) on CorrelationId
```

---

## Security Hunting Patterns

### Anomaly Detection — Rare Events
```kql
// Find processes that ran on only 1 machine (potential lateral movement)
let timeRange = 7d;
DeviceProcessEvents
| where Timestamp > ago(timeRange)
| summarize MachineCount=dcount(DeviceName) by FileName
| where MachineCount == 1
| join kind=inner (
    DeviceProcessEvents | where Timestamp > ago(timeRange)
) on FileName
| project Timestamp, DeviceName, FileName, ProcessCommandLine
```

### Baseline Deviation
```kql
// Alert when login count exceeds 3x the 7-day average
let baseline = SigninLogs
| where TimeGenerated between (ago(8d) .. ago(1d))
| summarize AvgLogins=avg(count_) by UserPrincipalName
    | summarize AvgLogins=count() by UserPrincipalName;
let recent = SigninLogs
| where TimeGenerated > ago(1d)
| summarize RecentLogins=count() by UserPrincipalName;
recent
| join kind=inner baseline on UserPrincipalName
| where RecentLogins > AvgLogins * 3
| project UserPrincipalName, RecentLogins, AvgLogins, Ratio=round(RecentLogins * 1.0 / AvgLogins, 2)
```

### IOC Matching
```kql
// Match network events against threat intelligence
let iocs = ThreatIntelligenceIndicator
| where Active == true
| where ExpirationDateTime > now()
| where isnotempty(NetworkIP)
| distinct NetworkIP;
CommonSecurityLog
| where TimeGenerated > ago(1d)
| where DestinationIP in (iocs) or SourceIP in (iocs)
| project TimeGenerated, SourceIP, DestinationIP, DeviceAction, Activity
```

### Impossible Travel
```kql
SigninLogs
| where TimeGenerated > ago(1d)
| where ResultType == 0
| project TimeGenerated, UserPrincipalName, Location=tostring(LocationDetails.city),
          Lat=todouble(LocationDetails.geoCoordinates.latitude),
          Lon=todouble(LocationDetails.geoCoordinates.longitude)
| sort by UserPrincipalName, TimeGenerated asc
| serialize
| extend PrevTime=prev(TimeGenerated), PrevLat=prev(Lat), PrevLon=prev(Lon), PrevUser=prev(UserPrincipalName)
| where UserPrincipalName == PrevUser
| extend TimeDiffHours = datetime_diff('hour', TimeGenerated, PrevTime)
| extend DistanceKm = geo_distance_2points(Lon, Lat, PrevLon, PrevLat) / 1000
| where TimeDiffHours > 0
| extend SpeedKmH = DistanceKm / TimeDiffHours
| where SpeedKmH > 1000  // faster than commercial flight
| project TimeGenerated, UserPrincipalName, Location, DistanceKm=round(DistanceKm, 0), TimeDiffHours, SpeedKmH=round(SpeedKmH, 0)
```

---

## Time-series Patterns

### Binned Aggregation
```kql
Perf
| where TimeGenerated > ago(24h)
| where CounterName == "% Processor Time"
| summarize AvgCPU=avg(CounterValue) by bin(TimeGenerated, 15m), Computer
| render timechart
```

### Rolling Window
```kql
let data = SecurityEvent
| where TimeGenerated > ago(7d)
| summarize EventCount=count() by bin(TimeGenerated, 1h);
data
| order by TimeGenerated asc
| serialize
| extend Rolling4h = row_window_session(TimeGenerated, 4h, 4h)
```

### Anomaly Detection with `series_decompose_anomalies`
```kql
let startTime = ago(14d);
let endTime = now();
SecurityEvent
| where TimeGenerated between (startTime .. endTime)
| where EventID == 4625
| make-series FailedLogins=count() on TimeGenerated from startTime to endTime step 1h
| extend (anomalies, score, baseline) = series_decompose_anomalies(FailedLogins, 1.5, -1, 'linefit')
| render anomalychart with (anomalycolumns=anomalies)
```

---

## Data Enrichment Patterns

### GeoIP Enrichment
```kql
SigninLogs
| where TimeGenerated > ago(1d)
| extend City = tostring(LocationDetails.city),
         State = tostring(LocationDetails.state),
         Country = tostring(LocationDetails.countryOrRegion),
         Lat = todouble(LocationDetails.geoCoordinates.latitude),
         Lon = todouble(LocationDetails.geoCoordinates.longitude)
```

### JSON Parsing
```kql
AzureActivity
| where TimeGenerated > ago(1d)
| extend Props = parse_json(Properties)
| extend StatusCode = tostring(Props.statusCode),
         Resource = tostring(Props.resource)
```

### External Data (ADX only)
```kql
let ipRanges = externaldata(CIDR:string, Owner:string, Description:string)
[@"https://raw.githubusercontent.com/org/repo/main/ip-ranges.csv"]
with (format="csv", ignoreFirstRecord=true);
CommonSecurityLog
| where TimeGenerated > ago(1h)
| evaluate ipv4_lookup(ipRanges, SourceIP, CIDR)
```
