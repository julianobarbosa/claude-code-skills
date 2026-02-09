# Workflow: Manage Vault

Vault health checks, orphan detection, broken link scanning, and lifecycle management.

## Steps

1. **Determine action** - health check, orphan scan, broken links, lifecycle change, or move
2. **Execute** via `Tools/VaultManager.py`
3. **Report results** with actionable suggestions

## Tool Usage

```bash
# Full health report
python Tools/VaultManager.py health --vault /path/to/vault

# Find orphan notes (no inlinks or outlinks)
python Tools/VaultManager.py orphans --vault /path/to/vault

# Find broken wikilinks
python Tools/VaultManager.py broken-links --vault /path/to/vault

# Change lifecycle state
python Tools/VaultManager.py lifecycle \
  --path "01 - Projects/old-project.md" \
  --state archived

# Move note between PARA folders
python Tools/VaultManager.py move \
  --path "00 - Inbox/unsorted-note.md" \
  --to "03 - Resources/"

# List inbox notes for triage
python Tools/VaultManager.py inbox --vault /path/to/vault
```

### Commands

| Command | Description |
|---------|-------------|
| `health` | Count notes by folder, tag stats, find empty notes, frontmatter coverage |
| `orphans` | Notes with no inlinks or outlinks |
| `broken-links` | Wikilinks pointing to non-existent notes |
| `lifecycle` | Change state: `active`, `processed`, `archived` |
| `move` | Relocate note between PARA folders |
| `inbox` | List notes in `00 - Inbox/` for triage |

### Health Report Output

```
Vault Health Report
===================
Total notes: 1,247
By folder:
  06 - Daily:        892
  03 - Resources:    128
  01 - Projects:      45
  ...

Frontmatter coverage: 89%
Notes without tags: 23
Empty notes: 5
Orphan notes: 31
Broken links: 12
```

## Context Files

- `VaultOrganization.md` - PARA structure, lifecycle states
