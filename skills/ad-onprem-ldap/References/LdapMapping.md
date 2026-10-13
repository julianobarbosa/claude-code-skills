# AD cmdlets to LDAP

| RSAT cmdlet | `Ad.ts` | LDAP operation |
|---|---|---|
| `Get-ADUser` | `find-user`, `user-status` | search `(&(objectCategory=person)(objectClass=user)(sAMAccountName=…))` |
| `Get-ADGroup` | `find-group` | search `(&(objectClass=group)(sAMAccountName=…))` |
| `Get-ADGroupMember [-Recursive]` | `group-members [--recursive]` | base read of `member;range=N-*`; recursive: `(memberOf:1.2.840.113556.1.4.1941:=<groupDN>)` |
| `Get-ADPrincipalGroupMembership` | `user-groups [--recursive]` | `memberOf`; recursive: `(member:1.2.840.113556.1.4.1941:=<userDN>)` |
| `Add-ADGroupMember` / `Remove-ADGroupMember` | `add-member` / `remove-member` | modify group, add/delete `member` |
| `New-ADUser` | `create-user` | add with objectClass `user`, `userAccountControl=514` |
| `New-ADGroup` | `create-group` | add with objectClass `group`, `groupType` |
| `Disable-ADAccount` / `Enable-ADAccount` | `disable` / `enable` | replace `userAccountControl`, bit `0x2` |
| `Unlock-ADAccount` | `unlock` | replace `lockoutTime` with `0` |
| `Move-ADObject` | `move` | modifyDN with `newSuperior` |
| `Set-ADAccountPassword -Reset` | `reset-password` | replace `unicodePwd` with `"password"` as UTF-16LE (LDAPS only); `pwdLastSet=0` forces a change at next logon |
| `Set-ADGroup -GroupScope` | `set-group-scope` | replace `groupType` |
| `Remove-ADUser` / `Remove-ADGroup` | not implemented | |

## Bit fields

| Attribute | Bit | Meaning |
|---|---|---|
| `userAccountControl` | `0x2` | account disabled |
| `userAccountControl` | `0x200` | normal account (512; 514 = normal + disabled) |
| `userAccountControl` | `0x10000` | password never expires |
| `msDS-User-Account-Control-Computed` | `0x10` | locked out now |
| `msDS-User-Account-Control-Computed` | `0x800000` | password expired |
| `groupType` | `0x2` / `0x4` / `0x8` | global / domain local / universal |
| `groupType` | `0x80000000` | security (stored signed, so security groups are negative) |

`pwdLastSet`, `lockoutTime`, `lastLogonTimestamp` and `accountExpires` are FILETIME values:
100 ns ticks since 1601-01-01 UTC. `0` and `9223372036854775807` mean "never".
`lastLogonTimestamp` replicates only every 9 to 14 days, so treat it as approximate.

## Escaping

- Filter values follow RFC 4515: `*` `(` `)` `\` NUL become `\2a` `\28` `\29` `\5c` `\00`.
  A DN used inside a filter needs this too, because DNs carry `\,`.
- RDN values follow RFC 4514: `, + " \ < > ; =` get a backslash, as do a leading `#` or space
  and a trailing space.

## Raw OpenLDAP recipes (read only)

Point OpenLDAP at the CA bundle and read the password from 1Password without putting it on the
command line (`-y` reads it from a file descriptor):

```bash
export LDAPTLS_CACERT=~/.config/ad-onprem/ca-bundle.pem
ldapsearch -H ldaps://dc01.corp.example.com -x \
  -D 'admin.account@corp.example.com' -y <(op read --no-newline 'op://<vault>/<item>/password') \
  -b 'DC=corp,DC=example,DC=com' -E pr=500/noprompt \
  '(&(objectCategory=person)(sAMAccountName=jdoe))' sAMAccountName userAccountControl memberOf
```

`-E pr=500/noprompt` pages past the server's 1000-entry size limit. A quick reachability
check before blaming credentials: `nc -z -G 3 dc01.corp.example.com 636`.

## Getting the CA bundle

A DC presents its certificate chain during the TLS handshake:
`openssl s_client -connect dc01.corp.example.com:636 -showcerts </dev/null`. The leaf's AIA
extension names the issuing CA's URL. Keep root plus issuing CA in one PEM, root first, and
verify the root's SHA-256 fingerprint (`openssl x509 -noout -fingerprint -sha256`) against a
value the directory team gives you over a separate channel.
