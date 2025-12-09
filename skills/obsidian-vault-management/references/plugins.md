# Installed Plugins Reference

## Dataview

**Purpose**: Query notes like a database

**Config file**: `.obsidian/plugins/dataview/data.json`

**Key Settings**:
- Inline query prefix: `=`
- Inline JS prefix: `$=`
- Date format: `MMMM dd, yyyy`
- Task completion tracking: enabled

See [dataview.md](dataview.md) for query syntax.

## Templater

**Purpose**: Advanced templates with scripting

**Config file**: `.obsidian/plugins/templater-obsidian/data.json`

**Key Settings**:
- Templates folder: `99 - Meta/00 - Templates`
- Trigger on file creation: enabled
- Auto jump to cursor: enabled

See [templater.md](templater.md) for syntax.

## Auto Note Mover

**Purpose**: Automatically move notes based on tags

**Config file**: `.obsidian/plugins/auto-note-mover/data.json`

**Current Rules**:
| Tag | Destination Folder |
|-----|-------------------|
| #aks-a | 08 - books/azure/aks |
| #pwsh-a | 08 - books/PowerShell |
| #argocd-a | 08 - books/argocd |
| #fabric-a | 08 - books/fabric |
| #git-a | 08 - books/git |

## Periodic Notes

**Purpose**: Daily, weekly, monthly note management

**Config file**: `.obsidian/plugins/periodic-notes/data.json`

**Typical Settings**:
- Daily notes folder: `06 - Daily/{{date:YYYY}}/{{date:MM}}`
- Daily note format: `{{date:YYYYMMDD}}`
- Template: daily note template

## Kanban

**Purpose**: Kanban boards in markdown

**Usage**: Create a note with kanban content:

```markdown
---
kanban-plugin: basic
---

## To Do

- [ ] Task 1
- [ ] Task 2

## In Progress

- [ ] Active task

## Done

- [x] Completed task
```

## Tag Wrangler

**Purpose**: Bulk tag management

**Features**:
- Rename tags across vault
- Merge duplicate tags
- Delete unused tags
- Tag suggestions

## Table Editor

**Purpose**: Easy markdown table editing

**Features**:
- Visual table editor
- Add/remove rows/columns
- Sort columns
- Align text

## Advanced URI

**Purpose**: Deep links to notes and actions

**URI Format**:
```
obsidian://advanced-uri?vault=VAULT_NAME&filepath=path/to/note.md
obsidian://advanced-uri?vault=VAULT_NAME&daily=true
obsidian://advanced-uri?vault=VAULT_NAME&search=query
```

## Local REST API

**Purpose**: External API access to vault

**Config file**: `.obsidian/plugins/obsidian-local-rest-api/data.json`

**Endpoints** (when enabled):
- `GET /vault` - List all files
- `GET /vault/{path}` - Get file content
- `PUT /vault/{path}` - Create/update file
- `DELETE /vault/{path}` - Delete file
- `POST /search` - Search vault

## MetaEdit

**Purpose**: Edit frontmatter properties

**Features**:
- Quick property editing
- Auto-complete for values
- Kanban integration

## Note Refactor

**Purpose**: Split and refactor notes

**Features**:
- Extract selection to new note
- Split by heading
- Automatic link updates

## Update Time on Edit

**Purpose**: Auto-update timestamps

**Config file**: `.obsidian/plugins/update-time-on-edit/data.json`

**Updates** `updated` field in frontmatter on file save.

## Frontmatter Tag Suggest

**Purpose**: Tag auto-complete in frontmatter

**Features**:
- Suggests existing tags
- Works in YAML frontmatter
- Reduces typos

## Icon Folder

**Purpose**: Custom folder icons

**Features**:
- Assign icons to folders
- Custom icon packs
- Visual organization

## List Callouts

**Purpose**: Callout styling for lists

**Usage**:
```markdown
- [!] Important item
- [?] Question
- [i] Information
```

## Smart Typography

**Purpose**: Auto-replace typography

**Features**:
- Smart quotes
- Em/en dashes
- Ellipsis
- Arrows

## Style Settings

**Purpose**: Theme customization

**Features**:
- CSS variable controls
- Per-theme settings
- Live preview

## URL Into Selection

**Purpose**: Paste URLs as links

**Features**:
- Select text, paste URL
- Creates `[selected text](url)`

## Copilot (AI)

**Purpose**: AI-powered assistance

**Features**:
- Chat with notes
- Summarization
- Question answering
- Custom prompts stored in `copilot-custom-prompts/`

## Plugin Management Tips

1. **Disable unused plugins** to improve performance
2. **Check for updates** regularly
3. **Backup config** before major changes
4. **Test new plugins** in a test vault first
5. **Review settings** after updates
