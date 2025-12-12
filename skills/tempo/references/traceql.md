# TraceQL Query Language Reference

TraceQL is Tempo's powerful query language for distributed traces, inspired by PromQL and LogQL.

## Query Types

### Trace Queries

Filter and return matching traces based on span attributes.

### Metrics Queries

Extract time-series metrics from trace data.

## Trace Structure

### Intrinsic Fields (colon separator `:`)

Fundamental built-in fields defined by OpenTelemetry:

| Field | Description | Values |
|-------|-------------|--------|
| `span:name` | Operation/span name | String |
| `span:duration` | Elapsed time | Duration (e.g., "10ms", "1.5s") |
| `span:status` | Span status | `ok`, `error`, `unset` |
| `span:kind` | Operation type | `server`, `client`, `producer`, `consumer`, `internal`, `unspecified` |
| `span:parentID` | Parent span ID | String (Tempo 2.8+) |

### Trace-Level Intrinsics

| Field | Description |
|-------|-------------|
| `trace:duration` | Total trace duration (max end - min start) |
| `trace:rootName` | Root span name |
| `trace:rootService` | Root span service |
| `trace:id` | Unique trace identifier |

### Event Intrinsics

| Field | Description |
|-------|-------------|
| `event:name` | Event identifier |

### Attribute Scopes (period separator `.`)

| Scope | Prefix | Example | Description |
|-------|--------|---------|-------------|
| Span | `span.` | `span.http.method` | Operation-specific attributes |
| Resource | `resource.` | `resource.service.name` | Entity/process attributes |
| Event | `event.` | `event.exception.message` | Event attributes |
| Link | `link.` | `link.traceID` | Link attributes |
| Instrumentation | `instrumentation_scope.` | `instrumentation_scope.name` | Library metadata |

### Common Attributes

**HTTP:**

- `span.http.method` - GET, POST, etc.
- `span.http.status_code` - 200, 404, 500, etc.
- `span.http.url` - Full URL
- `span.http.target` - URL path
- `span.http.response.size` - Response size in bytes

**Database:**

- `span.db.system` - postgresql, mysql, etc.
- `span.db.operation` - SELECT, INSERT, etc.
- `span.db.statement` - SQL query

**Kubernetes:**

- `resource.k8s.cluster.name`
- `resource.k8s.namespace.name`
- `resource.k8s.pod.name`
- `resource.k8s.container.name`

**Service:**

- `resource.service.name`
- `resource.service.version`
- `resource.service.instance.id`

## Comparison Operators

### String Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `=` | Equals | `{span.http.method = "GET"}` |
| `!=` | Not equal | `{span:status != "ok"}` |
| `=~` | Regex match | `{span:name =~ "GET.*"}` |
| `!~` | Regex not match | `{resource.service.name !~ "test-.*"}` |

### Numeric Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `>` | Greater than | `{span:duration > 500ms}` |
| `>=` | Greater or equal | `{span.http.status_code >= 400}` |
| `<` | Less than | `{span:duration < 1s}` |
| `<=` | Less or equal | `{span.http.status_code <= 299}` |

### Duration Values

```traceql
# Valid duration formats
{ span:duration > 10ms }
{ span:duration > 1.5s }
{ span:duration > 500us }
{ span:duration > 2m }
```

## Logical Operators

| Operator | Description | Example |
|----------|-------------|---------|
| `&&` | AND (same span) | `{span.http.method = "GET" && span:status = error}` |
| `\|\|` | OR | `{span:status = error \|\| span:duration > 1s}` |

## Structural Operators

Query traces based on span relationships:

| Operator | Description | Example |
|----------|-------------|---------|
| `>` | Direct child | `{parent} > {child}` |
| `<` | Direct parent | `{child} < {parent}` |
| `>>` | Descendant (ancestor→descendant) | `{ancestor} >> {descendant}` |
| `<<` | Ancestor (descendant→ancestor) | `{descendant} << {ancestor}` |
| `~` | Sibling (same parent) | `{sibling1} ~ {sibling2}` |
| `&>>` | Union descendant | Returns both sides |
| `&<<` | Union ancestor | Returns both sides |

### Structural Examples

```traceql
# Find HTTP requests that call databases
{span.http.url = "/api/products"} >> {span.db.system = "postgresql"}

# Find frontend calling API
{resource.service.name = "frontend"} > {resource.service.name = "api"}

# Find slow database calls under HTTP requests
{span:name = "HTTP GET"} >> {span.db.system != "" && span:duration > 100ms}
```

## Aggregation Functions

Apply to spans within a trace:

| Function | Description | Example |
|----------|-------------|---------|
| `count()` | Number of spans | `{ } \| count() > 10` |
| `avg()` | Average value | `{ } \| avg(span:duration) > 100ms` |
| `max()` | Maximum value | `{ } \| max(span:duration)` |
| `min()` | Minimum value | `{ } \| min(span:duration)` |
| `sum()` | Sum of values | `{ } \| sum(span.http.response.size)` |

### Aggregation Examples

```traceql
# Traces with more than 3 database operations
{span.db.operation = "SELECT"} | count() > 3

# Traces with average span duration over 100ms
{ } | avg(span:duration) > 100ms

# Traces with max duration over 5 seconds
{resource.service.name = "api"} | max(span:duration) > 5s
```

## Metrics Functions

Generate time-series from traces:

| Function | Description | Syntax |
|----------|-------------|--------|
| `rate()` | Spans per second | `{ condition } \| rate()` |
| `count_over_time()` | Count per interval | `{ condition } \| count_over_time()` |
| `avg_over_time()` | Average per interval | `{ } \| avg_over_time(attr)` |
| `min_over_time()` | Minimum per interval | `{ } \| min_over_time(attr)` |
| `max_over_time()` | Maximum per interval | `{ } \| max_over_time(attr)` |
| `sum_over_time()` | Sum per interval | `{ } \| sum_over_time(attr)` |
| `quantile_over_time()` | Percentile per interval | `{ } \| quantile_over_time(attr, percentile)` |
| `histogram_over_time()` | Distribution per interval | `{ } \| histogram_over_time(attr)` |
| `compare()` | Compare time periods | `{ } \| compare({filters}, topN, start, end)` |
| `topk(n)` | Top N results | `{ } \| rate() by (attr) \| topk(10)` |
| `bottomk(n)` | Bottom N results | `{ } \| rate() by (attr) \| bottomk(10)` |

### Metrics Examples

```traceql
# Error rate
{span:status = error} | rate()

# Error rate by service
{span:status = error} | rate() by(resource.service.name)

# P99 latency
{span:name = "GET /api/orders"} | quantile_over_time(span:duration, .99)

# P99 latency by endpoint
{resource.service.name = "api"} | quantile_over_time(span:duration, .99) by(span.http.target)

# Count over time
{span:name = "database-query"} | count_over_time()

# Response size sum by service
{ } | sum_over_time(span.http.response.size) by(resource.service.name)

# Top 10 services by error rate
{span:status = error} | rate() by(resource.service.name) | topk(10)

# Top 10 slowest endpoints
{span.http.target != ""} | avg_over_time(span:duration) by(span.http.target) | topk(10)
```

## Grouping with by()

Organize results by attributes:

```traceql
# Group by service
{span:status = error} | rate() by(resource.service.name)

# Group by multiple attributes
{span:status = error} | rate() by(resource.service.name, span.http.target)

# Without grouping - single aggregated value
{span:status = error} | rate()
```

## Select Operation

Extract specific attributes:

```traceql
{status = error} | select(span.http.status_code, span.http.url)
```

## Sampling Options

Optimize performance for large datasets:

```traceql
# Dynamic sampling (auto-optimize)
{ } with(sample=true)

# Span-level sampling (10% of spans)
{span:status = error} | count_over_time() with(span_sample=0.1)

# Trace-level sampling (10% of traces)
{span:status = error} | count_over_time() with(trace_sample=0.1)
```

## Most Recent Hint

Get deterministic newest results (Tempo 2.8+):

```traceql
{ } with(most_recent=true)
```

Without this, Tempo returns first N matching traces (may not be newest).

## Common Query Patterns

### Error Analysis

```traceql
# All errors
{span:status = error}

# Error rate by service
{span:status = error} | rate() by(resource.service.name)

# HTTP 5xx errors
{span.http.status_code >= 500}

# Error percentage
# (requires external calculation with total rate)

# Top error messages
{span:status = error} | count_over_time() by(span.exception.message) | topk(10)
```

### Latency Analysis

```traceql
# Slow requests (>1s)
{span:duration > 1s}

# P99 latency by endpoint
{span.http.target != ""} | quantile_over_time(span:duration, .99) by(span.http.target)

# P95 latency
{resource.service.name = "api"} | quantile_over_time(span:duration, .95)

# Average latency over time
{span:name = "GET /api/orders"} | avg_over_time(span:duration)
```

### Database Analysis

```traceql
# All database operations
{span.db.system != ""}

# Slow database queries
{span.db.system != "" && span:duration > 500ms}

# Database calls per service
{span.db.system != ""} | rate() by(resource.service.name, span.db.system)

# Top slow queries
{span.db.statement != ""} | avg_over_time(span:duration) by(span.db.statement) | topk(10)
```

### HTTP Analysis

```traceql
# All HTTP requests
{span.http.method != ""}

# HTTP errors by endpoint
{span.http.status_code >= 400} | rate() by(span.http.target)

# Request rate by method
{span.http.method != ""} | rate() by(span.http.method)

# Response size distribution
{ } | histogram_over_time(span.http.response.size) by(span.http.target)
```

### Service Dependency Analysis

```traceql
# Frontend to backend calls
{resource.service.name = "frontend"} >> {resource.service.name = "backend"}

# Service calling database
{resource.service.name = "user-service"} >> {span.db.system = "postgresql"}

# External API calls from service
{resource.service.name = "order-service"} >> {span:kind = "client"}
```

### Kubernetes Analysis

```traceql
# Traces from specific namespace
{resource.k8s.namespace.name = "production"}

# Traces from specific pod
{resource.k8s.pod.name =~ "api-.*"}

# Cross-namespace calls
{resource.k8s.namespace.name = "frontend"} >> {resource.k8s.namespace.name = "backend"}
```

## Query Optimization Tips

1. **Use scoped attributes** - `span.http` is faster than unscoped searches
2. **Prefer trace-level intrinsics** - `trace:rootName` is faster than `span:name`
3. **Use specific filters first** - Start with service/operation before duration
4. **Always specify time ranges** - Smaller ranges = faster queries
5. **Use `topk()`/`bottomk()`** - Limit results instead of pulling everything
6. **Use `with(most_recent=true)`** - For debugging recent issues
7. **Use sampling** - For large result sets, use `span_sample` or `trace_sample`

## API Query Parameters

```bash
# Range query
GET /api/search?q={job="api"}&start=<timestamp>&end=<timestamp>&limit=100

# With step parameter for metrics
GET /api/search?q={job="api"}|rate()&start=<timestamp>&end=<timestamp>&step=30s

# Instant query
GET /api/traces/<traceID>
```

## Regex Notes

- Uses Golang regular expressions
- Fully anchored at both ends (implicit `^...$`)
- Validate at <https://regex101.com/> (select Go flavor)

```traceql
# Match paths starting with /api/
{span.http.target =~ "/api/.*"}

# Match service names containing "user"
{resource.service.name =~ ".*user.*"}
```
