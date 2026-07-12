---
name: azure-cost-management-app
description: >
  Install and connect the Azure Cost Management App (by Microsoft Corporation) in Power BI Service
  via browser automation. Use this skill whenever the user mentions installing, deploying, connecting,
  or configuring the Azure Cost Management template app in Power BI, or when they want to connect
  Power BI to their EA (Enterprise Agreement) enrollment for cost visibility. Also triggers when the
  user says "connect your data" on the Cost Management App, wants to set up EA cost data in Power BI,
  or needs to link an enrollment number to a Power BI cost report.
---

# Azure Cost Management App — Install & Connect Skill

End-to-end browser automation for deploying and connecting the Microsoft Azure Cost Management App
in Power BI Service, targeting a specific workspace and EA enrollment.

## When This Skill Applies

- User wants to install the Azure Cost Management App from AppSource into Power BI
- User wants to connect an existing Cost Management App installation to real EA data
- User mentions enrollment number, EA connector, or "connect your data" on the Cost Management App
- User wants Azure cost data visible in Power BI Service (not Power BI Desktop)

## Key Facts (Read Before Starting)

**Template app workspace behavior:**
Power BI template apps (like this one) always create their own auto-named workspace — you cannot
install them directly into an arbitrary existing workspace like `devops-team`. What "deploying to
a workspace" actually means in practice is one of:
1. Connect the existing auto-created `AzureCostManagementApp` workspace to real EA data (most common)
2. Use a Deployment Pipeline to promote content into another workspace after install

**EA connector authentication:**
The Azure Cost Management connector for EA enrollments requires **Enterprise Administrator (read-only)**
role at the billing account level. Standard Azure RBAC roles (Cost Management Reader, Billing Reader)
do NOT work and will produce auth errors.

**App source:**
Always install from Microsoft Corporation (not community copies). In the AppSource gallery, the
Microsoft-published app appears further down — scroll past user-shared copies that show internal
user names as publisher.

## Workflow

### Step 1: Check Existing Installations

Before installing a new copy, check the Apps list:

1. Navigate to `https://app.powerbi.com/groups/me/apps`
2. Look for existing **Azure Cost Management App** entries
3. If one already exists (especially one showing "sample data"), the user likely just needs to
   **connect it to EA data** — not install a new copy. Ask to confirm intent before proceeding.

Key question to ask: "There's already an installation showing sample data. Would you like to connect
that one to your EA data, or install a fresh copy?"

### Step 2: Find and Install from AppSource (if fresh install needed)

1. Click **Get apps** (top right of the Apps page)
2. Search for "Cost Management" in the gallery search bar
3. **Scroll down** — the Microsoft Corporation version appears below user-shared copies
4. Identify by: publisher = "Microsoft Corporation", rating ~2.3 stars (73 reviews), Version 1006
5. Click the app card → click **Get It Now**
6. Confirm the "Confirm to continue" dialog → click **Get it now**

**Install dialog options:**
- "Update the workspace and the app" → updates existing installation (overwrites settings)
- "Update only workspace content without updating the app" → content only
- "Install another copy of the app into a new workspace" → creates a new auto-named workspace; requires typing a workspace name

Choose based on user intent. For connecting to EA data on an existing install, go to Step 3 directly.

### Step 3: Connect to EA Data ("Connect your data")

Navigate to the installed app report (left sidebar → `AzureCostManagementApp` workspace icon, or
via the Apps list). The "Getting Started" page shows a banner: **"You're viewing this app with
sample data. Connect your data"**.

Click **Connect your data** and fill in the Parameters dialog:

| Field | Value | Notes |
|-------|-------|-------|
| BillingProfileIdOrEnrollmentNumber | `<enrollment number>` | e.g. `53329720` |
| NumberOfMonths | `<integer>` | e.g. `12` for 12 months of history |
| Scope | `Enrollment Number` | Literal text — this is the scope type identifier |

Click **Next**.

### Step 4: Authenticate Data Sources (2 steps)

**Step 1 of 2 — Blob storage endpoint (Anonymous):**
- URL: `https://ccmstorageprod.blob.core.windows.net/...`
- Authentication method: `Anonymous`
- Privacy level: `None`
- Click **Sign in and continue** (no credentials needed here)

**Step 2 of 2 — EA Cost Management connector (OAuth2):**
- ExtensionDataSourceKind: `AzureCostManagement`
- ExtensionDataSourcePath: `Enrollment Number;<enrollment-number>` (auto-populated)
- Authentication method: `OAuth2`
- Privacy level: `Organizational`
- Click **Sign in and connect** → an OAuth2 popup opens for the EA admin to authenticate

**Important:** The OAuth2 popup opens as a separate browser window outside the automation session.
The user must complete the EA Enterprise Administrator sign-in manually in that popup.
After they confirm, tell them to come back and say "done" so you can verify the connection.

### Step 5: Verify the Connection

After auth completes, navigate to the workspace content list:
`https://app.powerbi.com/groups/<workspace-group-id>/list`

Success indicators:
- Banner changes to: **"You're viewing this app with sample data. Refresh is in progress."**
- Semantic model row shows a next refresh date (schedule auto-configured)
- The workspace name in the header is `Azure Cost Management App <timestamp>`

The first refresh runs automatically after auth. It may take several minutes. The app will show
real EA data once the first refresh completes.

## Parameters to Collect from User

Before starting, collect these if not already provided:

| Parameter | Description | Example |
|-----------|-------------|---------|
| EA Enrollment Number | The billing account enrollment number | `53329720` |
| Number of months | How many months of cost history to load | `12` |
| Target workspace | Where they want the app to live | `devops-team` (note: template apps create their own workspace) |

## Tools

Use `mcp__claude-in-chrome__*` browser automation tools throughout:

- `tabs_context_mcp` — always call first to get existing tab IDs
- `navigate` — go to Power BI URLs
- `computer` (screenshot, left_click, type, wait, scroll, zoom) — interact with the UI
- `browser_batch` — batch independent sequential actions for speed
- `find` — locate form elements by natural language description
- `form_input` — set dropdown values by ref

**Use the already-authenticated tab** (`app.powerbi.com`) rather than creating a new tab, since
new tabs will redirect to the Microsoft login page.

## Common Issues

**"Sign in and connect" does nothing / stays on step 2:**
The OAuth2 popup may have opened in a separate window behind Power BI. Ask the user to check for
a Microsoft sign-in popup and complete the EA admin login there.

**Privacy level dropdown is blank:**
Set it to `Organizational` before clicking "Sign in and connect". An empty privacy level can
cause the connection to hang.

**Refresh fails after auth:**
The EA connector requires Enterprise Administrator (read-only). If the signed-in account doesn't
have that role, the refresh will fail. Check the semantic model settings → Refresh history for
the error details.

**App still shows sample data after auth:**
This is normal — the first refresh takes several minutes. Navigate to the workspace list and
check if "Refresh is in progress" appears in the banner.

**Multiple Azure Cost Management App entries in Apps list:**
These may be copies installed by different users. Check the Owner column. The one owned by the
current user is the one we can configure. Ask the user which one to connect.

---

## Gotchas

- **EA connector needs Enterprise Admin (read-only) at billing-account level — NOT Azure RBAC.** Cost Management Reader at subscription scope silently returns zero rows.
- **30-min propagation delay** after granting EA Admin role — failures during the window look like auth issues; wait before debugging.
- **Template app workspace deploys to a fixed workspace name** — re-installing in the same tenant errors on name conflict; uninstall first.
- **Currency conversion**: EA data is USD; the app converts to default currency from Office settings, which may differ from the tenant's billing currency.
- **OAuth2 popup blocked silently in some browser configs** — first-time install on locked-down browsers needs popup whitelist; failure mode is endless spinner.
