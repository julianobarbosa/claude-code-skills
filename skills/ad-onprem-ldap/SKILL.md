---
name: ad-onprem-ldap
description: Manage on-premises Active Directory users and groups from macOS or Linux over LDAPS with a bun CLI, with no PowerShell, no RSAT and no Windows host. USE WHEN finding an AD user or group, listing group members (including nested), listing a user's groups, checking whether an account is disabled, locked or has an expired password, adding or removing group members, creating users or groups, disabling, enabling or unlocking accounts, moving objects between OUs, resetting an AD password, or changing a group's scope; also when someone asks for the Get-ADUser / Add-ADGroupMember / Set-ADAccountPassword equivalent on a Mac. NOT FOR Entra ID / Microsoft Graph objects (cloud-only users, SOA-converted groups), Azure RBAC, or deleting AD objects.
---

# ad-onprem-ldap

One CLI, `Tools/Ad.ts`, speaks LDAP over TLS straight to the domain controllers. It does what the
RSAT `ActiveDirectory` cmdlets do for users and groups, and it works anywhere bun runs.

## Setup

- Network path to a DC on 636/TCP (usually the corporate VPN) and DNS that resolves the domain.
- `bun install` inside `Tools/`.
- `op` (1Password CLI) signed in. The bind password is read with `op read` into memory only.
- A config at `~/.config/ad-onprem/config.json` (or `AD_ONPREM_CONFIG`), shaped like
  `config.example.json`. It holds the domain, base DN, DCs, bind account, secret reference,
  CA bundle path and the OU allowlist for creates and moves. It never belongs in a repo.
- The CA bundle (root, then any issuing CA) that signed the DC certificates, in PEM.
  Confirm the root fingerprint with the directory team before trusting it.

## Commands

| Command | Does |
|---|---|
| `find-user <id>` / `find-user --prefix <text>` | One user by sAMAccountName, UPN or DN, or up to 50 by prefix |
| `find-group <id>` | Group, decoded scope and type, direct member count |
| `group-members <group> [--recursive]` | Direct members (ranged, complete), or the nested closure |
| `user-groups <user> [--recursive]` | Direct `memberOf`, or every group reached through nesting |
| `user-status <user>` | Enabled, locked, password expired, last logon, bad password count |
| `add-member` / `remove-member <group> <member>...` | Change membership (members may be users, groups or computers) |
| `create-user <sam> --ou --given --sn [--display] [--upn]` | New user, created **disabled** |
| `create-group <sam> --ou [--scope] [--type] [--description]` | New group, global security by default |
| `disable` / `enable` / `unlock <user>` | Account state |
| `move <object> --to <ou>` | Move to another OU |
| `reset-password <user> [--must-change] [--vault]` | New random password, stored in 1Password; only the `op://` ref is printed |
| `set-group-scope <group> --scope <scope>` | Scope change; refuses global <-> domain local, which AD only allows via universal |

Run as `bun Tools/Ad.ts <command> ...`. Output is JSON. Exit codes: 0 ok, 1 failed, 2 usage or
config, 3 no DC reachable, 4 not found or ambiguous, 5 refused by a safety gate.

## Write contract

- Every write prints a dry-run plan (target DN, exact change, current state) and changes
  nothing until it is re-run with `--apply`. Show the plan to the principal and get a yes
  before applying.
- Applied writes read the result back over the same connection (same DC, so replication lag
  cannot fake success) and append one line to `~/.local/state/ad-onprem/audit.jsonl`.
- Creates and moves only land inside `writeOuAllowlist`.
- Objects with `adminCount=1` (privileged, AdminSDHolder-protected) are refused unless
  `--allow-protected` is passed.
- Delete is deliberately not implemented. Disable and move to a holding OU instead.
- New users start disabled: `create-user`, then `reset-password`, then `enable`.

## Gotchas

- **LDAPS only.** AD refuses `unicodePwd` writes over plain 389, and a simple bind on 389 sends
  the password in clear. The config rejects port 389. Never set `rejectUnauthorized: false`;
  fix the CA bundle instead.
- **A wrong bind password is never retried on another DC.** Each attempt counts toward the
  lockout threshold of the bind account.
- **The bind name and the stored UPN can differ.** AD accepts `sAMAccountName@domain` at bind
  time even when `userPrincipalName` is something else, so look the account up by
  sAMAccountName when a UPN search returns nothing.
- **`lockoutTime > 0` does not mean locked.** The lockout may already have expired. `user-status`
  reads the constructed `msDS-User-Account-Control-Computed`, which AD returns only on a
  base-scope read of the object.
- **`member` and `memberOf` omit the primary group** (normally Domain Users, via `primaryGroupID`).
  `group-members` and `user-groups` add it back; a hand-rolled `ldapsearch` will not.
- **Bit flags are swapped, not replaced.** `disable`, `enable` and `set-group-scope` delete the
  value they read and add the new one in a single modify, so AD refuses the write if someone
  changed the attribute in between. Re-run on that error; nothing was overwritten.
- **After `--apply`, the write is audited before it is read back.** A failed read-back shows up
  as `after.readBackError` with `mode: applied`, never as a failed command.
- **Large groups truncate `member` silently** past MaxValRange (1500 values by default).
  `group-members` uses ranged retrieval; a hand-rolled `ldapsearch` must too.
- **Scope changes go through universal.** Global and domain local never convert directly.
- **Synced objects lag in Entra.** A change made here shows up in Entra ID only after the next
  directory sync cycle, so don't verify it through Microsoft Graph right away.
- **No DC reachable (exit 3)** almost always means the VPN dropped or the resolver in use does
  not serve the AD domain. Check DNS for the DC names before debugging TLS.

## References

- `References/LdapMapping.md`: cmdlet to LDAP mapping, attributes, and raw `ldapsearch` recipes.
