# Workflow: Automated Password Rotation

Configure scheduled, automated password rotation for credentials managed by senhasegura.

## Prerequisites
- Senhasegura console access with Executions module permissions
- Target hosts reachable from senhasegura with required protocol (SSH/WinRM/etc.)
- Notification email (or webhook) for rotation outcomes

## Steps

### 1. Configure an Execution Template

**Console:** Executions → Templates → New

- **Name:** `Linux Password Change`
- **Executor:** SSH
- **Plugin:** Linux
- **Credential type:** Local User
- **Commands (example):**
  ```
  echo '[#NEW_PASSWORD#]' | passwd --stdin [#USERNAME#]
  ```
- **Verification:** SSH login test with the new password

`[#NEW_PASSWORD#]` and `[#USERNAME#]` are senhasegura placeholders, substituted at execution time.

### 2. Create an Execution Policy

**Console:** Executions → Policies → New

- **Name:** `Monthly Linux Password Rotation`
- **Status:** Active
- **Credentials:** filter by `tag:linux-servers` (or any tag/group expression)
- **Template:** `Linux Password Change`
- **Schedule:** Frequency `Monthly`, Day `1`, Time `02:00 AM` (use a quiet window)
- **Notifications:** email `security@example.com` on Success, Failure

### 3. Test rotation manually

**Via console:** PAM Core → Credentials → `<credential>` → Actions → Rotate.

**Via API:**

```bash
curl -X POST "$SENHASEGURA_URL/api/pam/credential/123/rotate" \
  -H "Authorization: Bearer $TOKEN"
```

Verify:

- Executions → History shows a successful run for the credential
- A login test against the host with the new password succeeds

### 4. Monitor execution history

**Console:** Executions → History — filter by date or status. Watch for:

- Connection timeouts → check network/firewall reachability
- Authentication failures → senhasegura's stored password drifted from reality
- Command failures → review template syntax against the host's shell

### 5. Roll out across the fleet

After one credential proves stable, expand the tag/filter to cover the rest. Stage in waves; do not flip every host the same night.

## Tips

- Rotate during a low-traffic window — application restarts may follow.
- Pair rotation with consumer hot-reload (External Secrets Operator + a controller that watches `Secret` for change), so apps don't go stale.
- Audit: keep `Executions → History` retention long enough to satisfy compliance.

## Next workflows

- Pull rotated credentials in CI/CD → `Workflows/InjectCiCdSecrets.md`
- Mirror rotated credentials into Kubernetes → `Workflows/SyncKubernetesSecrets.md`
