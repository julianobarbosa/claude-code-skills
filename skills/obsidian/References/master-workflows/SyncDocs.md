# Workflow: Sync Docs

Copy project documentation from external repositories into the vault.

## Steps

1. **Identify source** - project repo path and docs to sync
2. **Determine destination** - typically `01 - Projects/[project-name]/` or `03 - Resources/`
3. **Copy files** preserving structure
4. **Add frontmatter** to each synced file
5. **Update lifecycle** - mark as active
6. **Add tags** - project name, source repo
7. **Create/update MOC** - link synced docs from project MOC

## Tool Usage

```bash
# Sync docs from a project
python Tools/VaultManager.py move \
  --path "/external/project/docs/" \
  --to "01 - Projects/my-project/docs/" \
  --sync

# Update lifecycle after sync
python Tools/VaultManager.py lifecycle \
  --path "01 - Projects/my-project/docs/" \
  --state active
```

## Sync Strategy

1. **Copy, don't move** - source files remain in original location
2. **Add vault frontmatter** - source path, sync date, tags
3. **Convert links** - external markdown links to wikilinks where possible
4. **Preserve original** - keep original formatting intact
5. **Track sync date** - record when last synced in frontmatter

### Frontmatter for Synced Notes

```yaml
---
created: YYYY-MM-DDTHH:mm
updated: YYYY-MM-DDTHH:mm
type: synced-doc
source: /path/to/original/file.md
synced_at: YYYY-MM-DDTHH:mm
tags:
  - synced
  - project/name
---
```

## Context Files

- `reference/vault-organization.md` - Destination folder conventions
