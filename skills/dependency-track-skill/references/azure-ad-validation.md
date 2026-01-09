# Azure AD OIDC Validation Guide

Comprehensive validation guide for Azure AD OIDC integration with Dependency-Track.

## Pre-Deployment Checklist

### Azure AD App Registration
- [ ] App created with `AzureADMyOrg` sign-in audience
- [ ] Redirect URI: `https://<domain>/static/oidc-callback.html`
- [ ] `groupMembershipClaims: SecurityGroup` configured
- [ ] Optional claims include `groups`, `email`, `preferred_username`
- [ ] API permissions: User.Read, GroupMember.Read.All, email, openid, profile
- [ ] Admin consent granted
- [ ] Client secret stored in Key Vault

### Azure AD Groups
- [ ] Groups created with naming convention: `G-Usuarios-DependencyTrack-<Role>`
- [ ] Users added to appropriate groups
- [ ] Group Object IDs documented

### Dependency-Track Configuration
- [ ] OIDC environment variables set
- [ ] Teams created matching group names
- [ ] Group-to-Team mappings configured
- [ ] Permissions assigned to Teams

---

## Validation Commands

### 1. Verify App Registration Configuration

```bash
CLIENT_ID="your-client-id"
az ad app show --id $CLIENT_ID --query '{
  displayName:displayName,
  groupMembershipClaims:groupMembershipClaims,
  web:{redirectUris:web.redirectUris},
  optionalClaims:optionalClaims
}' -o yaml
```

**Expected output:**
```yaml
displayName: DependencyTrack
groupMembershipClaims: SecurityGroup
web:
  redirectUris:
    - https://dtrack.example.com/static/oidc-callback.html
optionalClaims:
  idToken:
    - name: groups
      ...
```

### 2. Verify Azure AD Groups Exist

```bash
az ad group list --filter "startswith(displayName, 'G-Usuarios-DependencyTrack')" \
  --query "[].{name:displayName, id:id}" -o table
```

**Expected output:**
```
Name                              Id
--------------------------------  ------------------------------------
G-Usuarios-DependencyTrack-Admin  31d6daa5-5cc2-4e5f-9bf5-75ee8e09198c
G-Usuarios-DependencyTrack-Mod    d34a2ea3-34c9-4744-a031-4e4a55d72746
G-Usuarios-DependencyTrack-Audit  39d0ddb2-8a0d-47c9-bc55-1993aadf7fe8
G-Usuarios-DependencyTrack-Dev    7144c503-7934-40fe-99e2-f45f67cb383e
G-Usuarios-DependencyTrack-Read   7109c419-028e-4b7b-8246-66517d512c3c
```

### 3. Verify User Group Membership

```bash
USER_UPN="user@example.com"

# Get user's security group memberships
az ad user get-member-objects --id $USER_UPN --security-enabled-only true

# Filter for DependencyTrack groups
az ad user get-member-objects --id $USER_UPN --security-enabled-only true \
  | jq -r '.[] | select(. | test("31d6daa5|d34a2ea3|39d0ddb2|7144c503|7109c419"))'
```

### 4. Verify Dependency-Track Teams via API

```bash
export DTRACK_URL="https://dtrack.dev.cafehyna.com.br"
export API_KEY="your-api-key"

# List all teams with their OIDC group mappings
curl -s -H "X-Api-Key: ${API_KEY}" "${DTRACK_URL}/api/v1/team" | jq '[.[] | {
  name: .name,
  uuid: .uuid,
  oidcGroups: [.mappedOidcGroups[]?.group.uuid // empty]
}]'
```

**Expected output:**
```json
[
  {
    "name": "Administrators",
    "uuid": "abc123...",
    "oidcGroups": ["31d6daa5-5cc2-4e5f-9bf5-75ee8e09198c"]
  },
  ...
]
```

### 5. Verify OIDC Groups in Dependency-Track

```bash
# List all OIDC groups recognized by Dependency-Track
curl -s -H "X-Api-Key: ${API_KEY}" "${DTRACK_URL}/api/v1/oidc/group" | jq '.'
```

**Note:** Groups only appear here **after** a user from that group has authenticated.

### 6. Check User's Current Teams

```bash
# After user logs in via OIDC
curl -s -H "X-Api-Key: ${API_KEY}" "${DTRACK_URL}/api/v1/user/self" | jq '.teams'
```

### 7. Verify Team Permissions

```bash
# Get specific team's permissions
TEAM_NAME="Administrators"
curl -s -H "X-Api-Key: ${API_KEY}" "${DTRACK_URL}/api/v1/team" \
  | jq '.[] | select(.name=="'$TEAM_NAME'") | {name, permissions}'
```

---

## Expected Results Summary

| Check | Expected Result |
|-------|-----------------|
| App Registration groups claim | `SecurityGroup` |
| Azure AD groups | 4-5 groups with naming convention |
| User group membership | Returns matching group Object IDs |
| D-Track teams | 4-5 teams with `mappedOidcGroups` populated |
| OIDC groups | Shows groups after user login |
| User teams | User belongs to expected teams based on Azure AD groups |

---

## Troubleshooting

### Groups not appearing after user login

1. **Check OIDC logs:**
```bash
kubectl logs -n dependency-track deployment/dependency-track-apiserver \
  | grep -i "oidc\|group\|claim"
```

2. **Decode the ID token:**
   - Open browser DevTools > Network
   - Login to Dependency-Track
   - Find request to `/api/v1/oidc/callback`
   - Copy the `id_token` from the request
   - Decode at https://jwt.io
   - Verify `groups` claim contains expected UUIDs

3. **Verify App Registration manifest:**
```bash
az ad app show --id $CLIENT_ID --query 'optionalClaims.idToken[?name==`groups`]'
```

### User not assigned to correct team

1. **Check team synchronization setting:**
```bash
kubectl get pods -n dependency-track -o jsonpath='{.items[*].spec.containers[*].env}' \
  | jq '.[] | select(.name | contains("TEAM"))'
```

2. **Manually trigger team assignment:**
   - User logs out
   - Clear browser cache/cookies
   - User logs in again

3. **Verify group-to-team mapping exists:**
```bash
curl -s -H "X-Api-Key: ${API_KEY}" "${DTRACK_URL}/api/v1/team" \
  | jq '.[] | select(.mappedOidcGroups | length > 0)'
```

---

## Creating Missing Group Mappings via API

If groups need to be manually mapped:

```bash
# Configuration
TEAM_NAME="Administrators"
AZURE_GROUP_ID="31d6daa5-5cc2-4e5f-9bf5-75ee8e09198c"

# 1. Get or create the team
TEAM_UUID=$(curl -s -H "X-Api-Key: ${API_KEY}" \
  "${DTRACK_URL}/api/v1/team" | jq -r '.[] | select(.name=="'$TEAM_NAME'") | .uuid')

# If team doesn't exist, create it
if [ -z "$TEAM_UUID" ] || [ "$TEAM_UUID" = "null" ]; then
  TEAM_UUID=$(curl -s -X PUT "${DTRACK_URL}/api/v1/team" \
    -H "X-Api-Key: ${API_KEY}" \
    -H "Content-Type: application/json" \
    -d '{"name": "'$TEAM_NAME'"}' | jq -r '.uuid')
  echo "Created team: $TEAM_UUID"
fi

# 2. Create OIDC group (required before mapping)
# Use Azure AD Group Object ID as both uuid and name
curl -X PUT "${DTRACK_URL}/api/v1/oidc/group" \
  -H "X-Api-Key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d "{\"uuid\": \"${AZURE_GROUP_ID}\", \"name\": \"${AZURE_GROUP_ID}\"}"

# 3. Get the OIDC group UUID (D-Track generates internal UUID)
OIDC_GROUP_UUID=$(curl -s -H "X-Api-Key: ${API_KEY}" \
  "${DTRACK_URL}/api/v1/oidc/group" | jq -r ".[] | select(.name==\"${AZURE_GROUP_ID}\") | .uuid")
echo "OIDC Group UUID: $OIDC_GROUP_UUID"

# 4. Create OIDC group-to-team mapping
# IMPORTANT: Use UUID strings directly, NOT objects
curl -X PUT "${DTRACK_URL}/api/v1/oidc/mapping" \
  -H "X-Api-Key: ${API_KEY}" \
  -H "Content-Type: application/json" \
  -d "{\"team\": \"${TEAM_UUID}\", \"group\": \"${OIDC_GROUP_UUID}\"}"

# 5. Assign permissions (example: full admin)
for PERMISSION in ACCESS_MANAGEMENT BOM_UPLOAD POLICY_MANAGEMENT \
  POLICY_VIOLATION_ANALYSIS PROJECT_CREATION_UPLOAD PORTFOLIO_MANAGEMENT \
  SYSTEM_CONFIGURATION VIEW_PORTFOLIO VIEW_VULNERABILITY; do
  curl -X POST "${DTRACK_URL}/api/v1/permission/${PERMISSION}/team/${TEAM_UUID}" \
    -H "X-Api-Key: ${API_KEY}"
done

# 6. Verify mapping was created
curl -s -H "X-Api-Key: ${API_KEY}" "${DTRACK_URL}/api/v1/team" \
  | jq ".[] | select(.name==\"${TEAM_NAME}\") | {name, mappedOidcGroups}"
```

> **IMPORTANT:** The `/api/v1/oidc/mapping` endpoint expects UUID **strings**, not objects.
> Using `{"team": {"uuid": "..."}, "group": {"uuid": "..."}}` returns HTTP 400 Bad Request.

---

## Reference: Standard Group Mappings

| Azure AD Group | Object ID | Dependency-Track Team | Role |
|----------------|-----------|----------------------|------|
| G-Usuarios-DependencyTrack-Admin | `31d6daa5-5cc2-4e5f-9bf5-75ee8e09198c` | Administrators | Full access |
| G-Usuarios-DependencyTrack-Moderator | `d34a2ea3-34c9-4744-a031-4e4a55d72746` | Moderators | Policy & vulnerability management |
| G-Usuarios-DependencyTrack-Auditor | `39d0ddb2-8a0d-47c9-bc55-1993aadf7fe8` | Auditors | Read-only with audit capabilities |
| G-Usuarios-DependencyTrack-Developer | `7144c503-7934-40fe-99e2-f45f67cb383e` | Developers | BOM upload, view portfolio |
| G-Usuarios-DependencyTrack-ReadOnly | `7109c419-028e-4b7b-8246-66517d512c3c` | ReadOnly | View only |
