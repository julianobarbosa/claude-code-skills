# Workflow: Create Note

Create notes with proper frontmatter, PARA placement, and wikilinks.

## Steps

1. **Determine note type** - project, zettelkasten, concept, howto, adr, meeting, moc, or generic
2. **Select PARA folder** based on type:
   - Project -> `01 - Projects/`
   - Zettelkasten/Concept -> `04 - Permanent/`
   - How-To/Resource -> `03 - Resources/`
   - Meeting -> `10 - 1-1/` or project folder
   - MOC -> `00 - Maps of Content/`
   - Generic -> `00 - Inbox/` (for later triage)
3. **Apply template** from `KnowledgeCapturePatterns.md` or `VaultOrganization.md`
4. **Generate frontmatter** with `created`, `updated`, `tags`, `type`
5. **Scan for related notes** and insert `[[wikilinks]]`
6. **Create file** using `Tools/NoteCreator.py create`

## Tool Usage

```bash
python Tools/NoteCreator.py create \
  --title "Note Title" \
  --template concept \
  --folder permanent \
  --tags "topic,subtopic" \
  --content "Optional body content"
```

### Options

| Flag | Values | Default |
|------|--------|---------|
| `--template` | `concept`, `adr`, `howto`, `meeting`, `project`, `daily`, `moc`, `generic` | `generic` |
| `--folder` | `inbox`, `projects`, `areas`, `resources`, `archive`, `permanent`, `moc`, `daily` | `inbox` |
| `--tags` | Comma-separated | From template |
| `--dry-run` | Preview without creating | `false` |
| `--vault` | Vault path | Auto-detect |

## Context Files

- `VaultOrganization.md` - Folder structure, frontmatter schemas
- `KnowledgeCapturePatterns.md` - Templates for each note type
- `MarkdownReference.md` - Obsidian markdown syntax
