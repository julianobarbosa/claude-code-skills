# Workflow: Connector Authentication

Troubleshoot and configure Power BI data source connectors, especially Azure Cost Management for EA enrollments.

## Azure Cost Management Connector (EA)

The built-in Power BI connector for Azure Cost Management has **different permission requirements** depending on the billing account type.

### EA Enrollment Connector

**Required Role:** Enterprise Administrator (read-only) at the billing account level.

This is the most common gotcha. Standard Azure RBAC roles do NOT work:

| Role | Works for EA Connector? |
|------|------------------------|
| Enterprise Administrator (read-only) | YES |
| Enterprise Administrator (full) | YES |
| Cost Management Reader (Azure RBAC) | NO |
| Billing Reader (Azure RBAC) | NO |
| Department Administrator | NO |
| Account Owner | NO |
| Subscription Contributor | NO |

### Why RBAC Doesn't Work

The EA connector uses OAuth2 against the **EA Billing layer**, which is a completely separate permission system from Azure RBAC. Granting `Cost Management Reader` at any scope does nothing for the EA connector.

### Granting EA Admin (Read-Only)

1. Sign in to https://ea.azure.com as an existing EA Admin
2. Navigate to **Manage** > **Enrollment** tab
3. Click **+ Add Administrator**
4. Enter the user's email (must be in the Entra ID tenant)
5. Select **Read Only** checkbox
6. Click **Add**
7. Wait up to **30 minutes** for propagation

### Connecting in Power BI Desktop

1. **Get Data** > **Azure** > **Azure Cost Management**
2. Choose scope: **Enrollment Number**
3. Enter enrollment ID (e.g., `53329720`)
4. Click **Connect**
5. Sign in with the account that has EA Admin role
6. For guest accounts: use **"Sign into an organization"** flow and enter the host tenant FQDN

### Common Failures

| Error | Cause | Fix |
|-------|-------|-----|
| "Access denied" or 401 | Missing EA Admin role | Grant EA Admin (read-only) |
| "Sign-in failed" for guest | Cross-tenant guest account | Use "Sign into an organization" with host tenant domain |
| "No data returned" | EA policies blocking | Enable "DA view charges" and "AO view charges" in Billing Account > Policies |
| Stale token after role change | PBI credential cache | File > Options > Data Source Settings > Clear Permissions, then reconnect |
| Works in Desktop, fails in Service | Different account or missing consent | Re-enter credentials in dataset settings with EA Admin account |

### EA Policy Prerequisites

Both of these must be enabled in the EA portal (Billing Account > Policies):

1. **DA view charges** — Department Administrators can see costs
2. **AO view charges** — Account Owners can see costs

If these are disabled, even EA Admins may see limited data.

## Alternative: Export-Based Approach

If EA Admin role cannot be granted (common in large enterprises with strict governance):

1. Use **Cost Management Exports** to Azure Blob Storage
   - Requires `Cost Management Contributor` (Azure RBAC) + storage access
   - Configure in Azure Portal > Cost Management > Exports
2. In Power BI, use **Azure Blob Storage** connector instead
   - Get Data > Azure > Azure Blob Storage
   - Enter storage account URL and key/SAS token
3. Power Query reads the exported CSVs from blob

This avoids the EA billing layer entirely and uses standard Azure RBAC.

## Other Connectors

### Azure Blob Storage
- Needs: Storage account URL + account key or SAS token
- Or: Entra ID account with `Storage Blob Data Reader` role

### SQL Database
- Needs: Server name, database name
- Auth: SQL auth (username/password) or Entra ID
- For Service: may need gateway if private endpoint

### SharePoint / OneDrive
- Needs: Site URL
- Auth: Organizational account
- Common issue: URL must be the SharePoint site URL, not the file URL

## Token Cache Management

When credentials change (role granted, password reset, etc.):

1. **Power BI Desktop**: File > Options > Data Source Settings > Clear Permissions
2. **Power BI Service**: Dataset Settings > Data source credentials > Edit credentials
3. **Browser**: Clear cookies for login.microsoftonline.com
