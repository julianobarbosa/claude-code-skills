# Tooling Workflow

Automate KQL queries via Azure CLI, REST API, SDKs, and alerting integrations.

## Azure CLI

### Log Analytics Query
```bash
# Run a query against a Log Analytics workspace
az monitor log-analytics query \
  --workspace <workspace-id> \
  --analytics-query "SecurityEvent | where TimeGenerated > ago(1h) | count" \
  --output table

# From a .kql file
az monitor log-analytics query \
  --workspace <workspace-id> \
  --analytics-query "$(cat my-query.kql)" \
  --output json > results.json

# With time range
az monitor log-analytics query \
  --workspace <workspace-id> \
  --analytics-query "SecurityEvent | count" \
  --timespan P7D \
  --output table
```

### Application Insights Query
```bash
az monitor app-insights query \
  --app <app-id> \
  --analytics-query "requests | where timestamp > ago(1h) | summarize count() by resultCode"
```

### ADX Query
```bash
# Using the Kusto CLI (az kusto is for cluster management, not queries)
# For queries, use the REST API or SDK
az kusto query \
  --cluster-name <cluster> \
  --database-name <db> \
  --query "TableName | take 10"
```

## REST API

### Log Analytics
```
POST https://api.loganalytics.io/v1/workspaces/{workspace-id}/query
Authorization: Bearer {token}
Content-Type: application/json

{
  "query": "SecurityEvent | where TimeGenerated > ago(1h) | count",
  "timespan": "PT1H"
}
```

### ADX
```
POST https://{cluster}.{region}.kusto.windows.net/v1/rest/query
Authorization: Bearer {token}
Content-Type: application/json

{
  "db": "database-name",
  "csl": "TableName | take 10"
}
```

## Python SDK

```python
from azure.monitor.query import LogsQueryClient
from azure.identity import DefaultAzureCredential
from datetime import timedelta

credential = DefaultAzureCredential()
client = LogsQueryClient(credential)

response = client.query_workspace(
    workspace_id="<workspace-id>",
    query="SecurityEvent | where TimeGenerated > ago(1h) | count",
    timespan=timedelta(hours=1)
)

for table in response.tables:
    for row in table.rows:
        print(row)
```

## Query Validation

Before running in production, validate queries:

1. **Syntax check** — Run with `| take 0` appended to verify parsing without returning data
2. **Row estimate** — Run with `| count` first to gauge result size
3. **Time-bound** — Always include a time filter; without one, queries scan the full retention period
4. **Column check** — Use `| getschema` to verify expected columns exist in the table

## Alert Rule Integration

### Create a scheduled alert rule (Log Analytics)
```bash
az monitor scheduled-query create \
  --name "High Failed Logins" \
  --resource-group <rg> \
  --scopes "/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.OperationalInsights/workspaces/<ws>" \
  --condition "count > 50" \
  --condition-query "SigninLogs | where ResultType != 0 | summarize count() by bin(TimeGenerated, 5m)" \
  --evaluation-frequency 5m \
  --window-size 5m \
  --severity 2 \
  --action-groups "/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.Insights/actionGroups/<ag>"
```

## Export Patterns

```bash
# JSON export
az monitor log-analytics query --workspace <id> --analytics-query "$(cat query.kql)" -o json > output.json

# CSV export (via jq)
az monitor log-analytics query --workspace <id> --analytics-query "$(cat query.kql)" -o json \
  | jq -r '.[0] | (.[0] | keys_unsorted) as $cols | $cols, (.[] | [.[$cols[]]] | @csv)' > output.csv

# PowerShell export
Invoke-AzOperationalInsightsQuery -WorkspaceId <id> -Query (Get-Content query.kql -Raw) |
  Select-Object -ExpandProperty Results |
  Export-Csv -Path output.csv -NoTypeInformation
```
