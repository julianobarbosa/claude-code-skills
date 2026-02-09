# Workflow: Process Inbox

Triage notes in `00 - Inbox/` into proper PARA folders.

## Steps

1. **List inbox** - Get all notes in `00 - Inbox/` via `Tools/VaultManager.py inbox`
2. **For each note**:
   a. Read content and any existing frontmatter
   b. Determine note type (project, resource, permanent, etc.)
   c. Suggest PARA destination folder
   d. Add/fix frontmatter (created, updated, tags, type)
   e. Add wikilinks to related notes
   f. Move to destination folder
3. **Report** - Summary of actions taken

## Tool Usage

```bash
# List inbox notes
python Tools/VaultManager.py inbox --vault /path/to/vault

# Move a processed note
python Tools/VaultManager.py move \
  --path "00 - Inbox/kubernetes-notes.md" \
  --to "03 - Resources/"

# Change lifecycle state after processing
python Tools/VaultManager.py lifecycle \
  --path "03 - Resources/kubernetes-notes.md" \
  --state processed
```

## PARA Destination Rules

| Content Signal | Destination |
|---------------|-------------|
| Active work with deadline | `01 - Projects/` |
| Ongoing responsibility | `02 - Areas/` |
| Reference material | `03 - Resources/` |
| Atomic insight/idea | `04 - Permanent/` |
| Completed/no longer relevant | `04 - Archive/` |
| Book notes | `08 - books/` |

## Frontmatter Fixes

When processing inbox notes:
- Add `created` if missing (use file creation time)
- Add `updated` with current timestamp
- Add `tags` based on content analysis
- Add `type` based on destination
- Preserve any existing frontmatter fields

## Context Files

- `VaultOrganization.md` - PARA folders, frontmatter schemas
- `KnowledgeCapturePatterns.md` - Templates for different note types
