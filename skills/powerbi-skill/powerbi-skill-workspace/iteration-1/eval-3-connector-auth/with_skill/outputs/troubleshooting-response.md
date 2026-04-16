# Diagnosis: Power BI Cost Management Connector — Access Denied

## Root Cause

Rogerio's `Cost Management Reader` (Azure RBAC) role does NOT work for the EA connector. The EA connector authenticates against the **EA Billing layer**, which is a completely separate permission system from Azure RBAC.

## Required Role

**Enterprise Administrator (read-only)** at the EA billing account level, granted through ea.azure.com.

## Fix Steps

1. An existing EA Admin signs into https://ea.azure.com
2. Navigate to **Manage** > **Enrollment** tab
3. Click **+ Add Administrator**
4. Enter Rogerio's email
5. Select **Read Only** checkbox
6. Click **Add**
7. Wait up to **30 minutes** for propagation
8. In Power BI Desktop: File > Options > Data Source Settings > **Clear Permissions**
9. Retry the connection

## Alternative

If EA Admin role cannot be granted, use **Cost Management Exports** to Azure Blob Storage + Blob connector in PBI. This only requires `Cost Management Contributor` (Azure RBAC) + storage access.

## Why RBAC Doesn't Work

| Role | Works for EA Connector? |
|------|------------------------|
| Enterprise Administrator (read-only) | YES |
| Cost Management Reader (Azure RBAC) | NO |
| Billing Reader (Azure RBAC) | NO |
| Department Administrator | NO |
| Account Owner | NO |
