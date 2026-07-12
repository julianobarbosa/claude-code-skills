# Workflow: Publish & Scheduled Refresh

Publish a PBIP report to Power BI Service and configure automated refresh.

## Step 1: Publish from Desktop

1. Open the .pbip in Power BI Desktop
2. Verify data is refreshed and report looks correct
3. **Home** > **Publish**
4. Select destination workspace
5. If replacing existing, confirm overwrite

## Step 2: Configure Data Gateway (for local/file data sources)

If the data source is local files (CSV folder), a network share, or on-prem database, you need the On-premises Data Gateway.

### Install Gateway

1. Download from https://powerbi.microsoft.com/gateway/
2. Install on a server that:
   - Has access to the data source (CSV folder, file share, database)
   - Is always on (not a laptop)
   - Has reliable internet connection
3. Sign in with Power BI account during setup
4. Register the gateway in the Power BI Service tenant

### Add Data Source to Gateway

1. Power BI Service > **Settings** (gear icon) > **Manage gateways**
2. Select your gateway > **Add data source**
3. For folder-based CSV:
   - Data source type: **Folder**
   - Path: the full path to the CSV folder (as seen from the gateway machine)
4. Configure credentials (Windows auth or organizational account)

## Step 3: Configure Dataset in Service

1. Go to the workspace in Power BI Service
2. Find the dataset (semantic model) > **Settings** (gear icon)
3. Under **Gateway connection**:
   - Map each data source to the gateway data source
   - The folder parameter must match the gateway data source path
4. Under **Data source credentials**:
   - Verify each source has valid credentials
   - For Azure Cost Management connector: use organizational account with EA Admin role
5. Under **Parameters**:
   - Verify `Parameter_ExportFolder` value matches the gateway machine path

## Step 4: Schedule Refresh

1. In dataset settings > **Scheduled refresh**
2. Toggle **Keep your data up to date** to ON
3. Set refresh frequency:
   - **Daily** at 08:00 (typical for FinOps — after overnight export scripts run)
   - Or multiple times per day if data changes frequently
4. Set timezone
5. Enable **Send refresh failure notification** to dataset owner
6. **Apply**

## Step 5: Verify First Refresh

1. Trigger a manual refresh: dataset > **Refresh now**
2. Check **Refresh history** for success/failure
3. If failed, check error details:
   - Gateway connectivity issues
   - Credential problems
   - Data source path mismatches
   - Query timeout

## Alternative: Direct API Connection (No Gateway)

If using the Azure Cost Management connector or other cloud connectors:

1. No gateway needed — PBI Service connects directly
2. In dataset settings, configure **Data source credentials** with OAuth2
3. The account must have appropriate Azure roles (EA Admin for EA connector)
4. Schedule refresh as above

## Refresh Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| Gateway offline | Gateway service stopped | Restart on host machine |
| Credential expired | OAuth token expired | Re-enter credentials in dataset settings |
| File not found | Path mismatch | Verify Parameter_ExportFolder = gateway data source path |
| Query timeout | Large dataset or slow PQ | Optimize PQ queries, reduce date range |
| Access denied | Insufficient permissions | Verify credentials have read access to source |
| Parameter mismatch | Desktop vs Service parameter values | Update parameter value in Service dataset settings |

## Automation with Python

Trigger refresh programmatically via Power BI REST API:

```bash
# Trigger refresh
curl -X POST \
  "https://api.powerbi.com/v1.0/myorg/groups/{workspace-id}/datasets/{dataset-id}/refreshes" \
  -H "Authorization: Bearer {access-token}" \
  -H "Content-Type: application/json"
```

Or use the `export_billing_data.py` script to export fresh CSVs, then let the scheduled refresh pick them up.
