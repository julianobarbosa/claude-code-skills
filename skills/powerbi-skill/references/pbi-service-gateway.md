# Power BI Service & Gateway Reference

## Publishing from Desktop

1. Open .pbip in Power BI Desktop
2. **Home** > **Publish**
3. Select workspace (or create new)
4. If replacing existing: confirm overwrite
5. Dataset and report are published as separate items

After publishing, the dataset (semantic model) and report are independent — you can update one without the other.

## On-Premises Data Gateway

### When Needed

- Data source is local files (CSV folder, Excel)
- Data source is on-premises database (SQL Server, Oracle)
- Data source is on a network share
- Data source requires VPN or private network

### Not Needed

- Cloud data sources (Azure SQL, Azure Blob Storage, Dataverse)
- Azure Cost Management connector
- SharePoint Online / OneDrive

### Installation

1. Download: https://powerbi.microsoft.com/gateway/
2. Install on a server (not a laptop):
   - Always-on, reliable internet
   - Access to all data sources
   - .NET Framework 4.7.2+
3. Sign in with Power BI account
4. Register gateway name in tenant

### Gateway Modes

| Mode | Use Case |
|------|---------|
| Standard | Shared across users, managed centrally |
| Personal | Single user only, lighter weight |

For enterprise: always Standard.

### Adding Data Sources

1. Power BI Service > Settings > Manage gateways
2. Select gateway > Add data source
3. Configure source type (Folder, SQL Server, etc.)
4. Set credentials
5. Test connection

## Scheduled Refresh

### Setup

1. Power BI Service > Workspace > Dataset > Settings
2. **Gateway connection**: map each source to gateway data source
3. **Scheduled refresh**: toggle ON
4. Set frequency: Daily at 08:00 (typical for FinOps)
5. Set timezone
6. Enable failure notifications
7. Apply

### Refresh Limits

| License | Max Refreshes/Day |
|---------|-------------------|
| Pro | 8 |
| Premium Per User | 48 |
| Premium Capacity | 48 (configurable higher) |

### Refresh History

Dataset > Refresh history — shows last N refreshes with:
- Start time, duration
- Status (success/failure)
- Error details for failures

## Power BI Template Apps

Template apps are pre-built PBI solutions that connect to specific services.

### Azure Cost Management Template App

1. Power BI Service > Apps > Get apps
2. Search "Azure Cost Management"
3. Install > Connect
4. Enter parameters:
   - Scope: Enrollment Number
   - Enrollment ID: `53329720`
   - Number of months: 13 (or desired range)
5. Sign in with organizational account (needs EA Admin role)
6. Wait for initial data load

### Template App vs Custom PBIP

| Aspect | Template App | Custom PBIP |
|--------|-------------|-------------|
| Setup time | Minutes | Days |
| Customization | Limited | Full control |
| Version control | No | Git-friendly |
| Data model | Fixed | Custom star schema |
| Measures | Pre-defined | Custom DAX |

## Dataset Settings

### Parameters
- View and update parameter values (e.g., Parameter_ExportFolder)
- Must match gateway data source path

### Data Source Credentials
- **OAuth2**: organizational account (Azure AD)
- **Key**: account key or SAS token (storage)
- **Basic**: username/password (SQL)

### Endorsement
- Promoted: recommended dataset
- Certified: verified by admin

## Workspace Roles

| Role | Publish | Edit | View | Admin |
|------|---------|------|------|-------|
| Admin | Yes | Yes | Yes | Yes |
| Member | Yes | Yes | Yes | No |
| Contributor | Yes | Yes | Yes | No |
| Viewer | No | No | Yes | No |

Key differences:
- **Admin**: manage workspace settings, add/remove members
- **Member**: publish content, share items
- **Contributor**: publish content (cannot share)
- **Viewer**: consume only

## REST API Quick Reference

### Trigger Refresh
```bash
POST https://api.powerbi.com/v1.0/myorg/groups/{workspace-id}/datasets/{dataset-id}/refreshes
Authorization: Bearer {token}
```

### Get Dataset Info
```bash
GET https://api.powerbi.com/v1.0/myorg/groups/{workspace-id}/datasets/{dataset-id}
```

### Get Refresh History
```bash
GET https://api.powerbi.com/v1.0/myorg/groups/{workspace-id}/datasets/{dataset-id}/refreshes
```

## Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| Gateway offline | Service stopped on host | Restart Windows service |
| Credential expired | OAuth token expired | Re-enter in dataset settings |
| File not found | Path mismatch Desktop vs Gateway | Match Parameter_ExportFolder to gateway source |
| Query timeout | Large dataset, slow PQ | Optimize queries, reduce scope |
| Access denied | Insufficient permissions | Check credentials have read access |
| "Data source not found" | Gateway source not configured | Add data source in gateway management |
