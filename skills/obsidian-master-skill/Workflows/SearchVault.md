# Workflow: Search Vault

Search vault using DQL (Dataview Query Language), content search, or tag filtering.

## Steps

1. **Determine search type** based on intent:
   - Structured query (table, list) -> DQL/Dataview
   - Text content search -> Content (grep-like)
   - Tag/property filter -> JsonLogic
2. **Build query** using appropriate syntax
3. **Execute search** via `Tools/SearchVault.py search`
4. **Format results** as table, JSON, or text

## Tool Usage

```bash
# Check if Obsidian REST API is available
python Tools/SearchVault.py status

# Dataview query
python Tools/SearchVault.py search --type dataview \
  "TABLE status, tags FROM \"01 - Projects\" WHERE status != \"completed\""

# Content search (grep-like)
python Tools/SearchVault.py search --type content \
  --query "kubernetes deployment" \
  --folder "03 - Resources"

# JsonLogic search
python Tools/SearchVault.py search --type jsonlogic \
  --filter '{"and": [{"glob": ["01 - Projects/**", {"var": "path"}]}]}'

# Output formats
python Tools/SearchVault.py search --type content --query "topic" --json
python Tools/SearchVault.py search --type content --query "topic" --table
```

### Search Types

| Type | When to Use | Example |
|------|------------|---------|
| `dataview` | Structured queries with TABLE/LIST/TASK | `TABLE status FROM "01 - Projects"` |
| `content` | Full-text search across files | `--query "search term"` |
| `jsonlogic` | Complex property/path filtering | JSON filter object |

### Options

| Flag | Description |
|------|-------------|
| `--type` | `dataview`, `content`, `jsonlogic` |
| `--query` | Search text (for content type) |
| `--folder` | Limit to folder |
| `--tags` | Filter by tags |
| `--json` | JSON output |
| `--table` | Table output |
| `--limit` | Max results |

## Fallback Behavior

When Obsidian REST API is unavailable:
- Content search falls back to direct file grep via `pathlib` + regex
- DQL queries are not available (requires Dataview plugin running)
- JsonLogic is not available (requires REST API)

## Context Files

- `RestApiReference.md` - API endpoints, DQL syntax
- `VaultOrganization.md` - Folder structure for scoping searches
