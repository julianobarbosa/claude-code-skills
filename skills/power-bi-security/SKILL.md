---
name: power-bi-security
description: Configure row-level security (RLS) roles, object-level security, and perspectives for Power BI semantic models using pbi-cli. Invoke this skill whenever the user mentions "security", "RLS", "row-level security", "access control", "data restrictions", "who can see", "filter by user", "perspectives", "limit visibility", or wants to restrict data access by role.
tools: pbi-cli
---

# Power BI Security Skill

Manage row-level security (RLS) and perspectives for Power BI models.

## Prerequisites

```bash
pipx install pbi-cli-tool
pbi-cli skills install
pbi connect
```

## Security Roles (RLS)

```bash
# List all security roles
pbi security-role list

# Get role details
pbi security-role get "Regional Manager"

# Create a new role
pbi security-role create "Regional Manager" \
  --description "Restricts data to user's region"

# Delete a role
pbi security-role delete "Regional Manager"
```

## Perspectives

Perspectives control which tables and columns are visible to users:

```bash
# List all perspectives
pbi perspective list

# Create a perspective
pbi perspective create "Sales View"

# Delete a perspective
pbi perspective delete "Sales View"
```

## Workflow: Set Up RLS

```bash
# 1. Create roles
pbi security-role create "Sales Team" --description "Sales data only"
pbi security-role create "Finance Team" --description "Finance data only"

# 2. Verify roles were created
pbi --json security-role list

# 3. Export full model for version control (includes roles)
pbi database export-tmdl ./model-backup/
```

## Workflow: Create User-Focused Perspectives

```bash
# 1. Create perspectives for different audiences
pbi perspective create "Executive Dashboard"
pbi perspective create "Sales Detail"
pbi perspective create "Finance Overview"

# 2. Verify
pbi --json perspective list
```

## Common RLS Patterns

### Region-Based Security

Create a role that filters by the authenticated user's region:

```bash
pbi security-role create "Region Filter" \
  --description "Users see only their region's data"
```

Then define table permissions with DAX filter expressions in the model (via TMDL or Power BI Desktop).

### Department-Based Security

```bash
pbi security-role create "Department Filter" \
  --description "Users see only their department's data"
```

### Manager Hierarchy

```bash
pbi security-role create "Manager View" \
  --description "Managers see their direct reports' data"
```

## Best Practices

- Create roles with clear, descriptive names
- Always add descriptions explaining the access restriction
- Export model as TMDL for version control (`pbi database export-tmdl`)
- Test RLS thoroughly before publishing to production
- Use perspectives to simplify the model for different user groups
- Document role-to-group mappings externally (RLS roles map to Azure AD groups in Power BI Service)
- Use `--json` output for automated security audits: `pbi --json security-role list`

---

## Gotchas

- **`USERPRINCIPALNAME()` returns different values in Desktop vs Service:** Desktop returns the AAD UPN of the signed-in user; Service returns the embedded token UPN, which can differ for guest users or B2B identities. RLS that passes local tests can silently fail in Service.
- **`security-role create` only creates the role envelope — table filter expressions must be added via TMDL or Desktop:** A role with no filter expressions appears in Service as "applied" but returns ALL rows. Always export TMDL after creating and verify each table has the expected `tablePermission` block.
- **Object-level security and perspectives are NOT the same:** Perspectives only hide objects in the field list; users can still query hidden tables/columns via DAX. For actual security, use OLS (encoded in TMDL as `metadataPermissions`) — perspectives are UX only.
- **RLS roles map to AAD groups in Service, not individual users:** Adding `user@x.com` directly to a role works in Desktop but is brittle in Service when the user leaves the org. Always bind to groups; document the role-to-group mapping externally since the TMDL only knows about role names.
- **Dynamic RLS using `LOOKUPVALUE` on a user-mapping table is vulnerable to refresh staleness:** If a new user is added to the mapping table but the dataset has not refreshed, they see zero rows with no error. Refresh schedule must align with onboarding cadence.
- **`security-role delete` removes the role and all its filter expressions atomically:** No partial cleanup, no warning if reports depend on it. Always export TMDL first — restoring a complex multi-table role from memory is painful.

