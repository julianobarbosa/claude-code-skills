# Vault Organization Reference

## PARA Folder Structure

| Folder | Purpose | Note Types |
|--------|---------|------------|
| `00 - Inbox/` | Quick capture, unsorted notes | Fleeting thoughts |
| `00 - Maps of Content/` | Index notes linking topics | MOCs, dashboards |
| `01 - Projects/` | Active project documentation | Project notes |
| `02 - Areas/` | Ongoing responsibilities | Area overviews |
| `03 - Resources/` | Reference materials | Evergreen notes |
| `04 - Archive/` | Completed/inactive content | Archived projects |
| `04 - Permanent/` | Zettelkasten-style notes | Atomic ideas |
| `06 - Daily/` | Daily notes (YYYY/MM/YYYYMMDD.md) | Journal entries |
| `08 - books/` | Book notes and highlights | Reading notes |
| `10 - 1-1/` | One-on-one meeting notes | Meeting notes |

### System Folders

| Folder | Purpose |
|--------|---------|
| `_bmad/` | BMAD Core Platform |
| `_assets/` | Vault assets and media |
| `99 - Meta/` | Templates and vault metadata |
| `attachments/` | Note attachments |
| `Clippings/` | Web clips and imports |
| `Excalidraw/` | Diagram files |
| `memory-bank/` | AI memory/context storage |
| `topics/` | Topic-based organization |

## Frontmatter Schemas

### Standard Note

```yaml
---
created: YYYY-MM-DDTHH:mm
updated: YYYY-MM-DDTHH:mm
tags:
  - category/subcategory
---
```

### Daily Note

```yaml
---
created: YYYY-MM-DDTHH:mm
updated: YYYY-MM-DDTHH:mm
title: "YYYYMMDD"
type: daily-note
status: true
tags:
  - daily
  - YYYY
  - YYYY-MM
date_formatted: YYYY-MM-DD
---
```

### Project Note

```yaml
---
created: YYYY-MM-DDTHH:mm
updated: YYYY-MM-DDTHH:mm
type: project
status: active | paused | complete
priority: high | medium | low
tags:
  - project/name
---
```

### Zettelkasten Note

```yaml
---
created: YYYY-MM-DDTHH:mm
updated: YYYY-MM-DDTHH:mm
type: zettelkasten
tags:
  - permanent
  - topic
---
```

## Naming Conventions

- **Regular notes**: Descriptive titles (spaces allowed)
- **Daily notes**: `YYYYMMDD.md` in `06 - Daily/YYYY/MM/`
- **Templates**: Located in `99 - Meta/00 - Templates/`
- **BMAD files**: kebab-case

## Link Conventions

- Use `[[wikilinks]]` for all internal links
- Link to headings: `[[Note#Heading]]`
- Block references: `[[Note#^block-id]]`
- Embed notes: `![[Note]]`
- Embed images: `![[image.png]]`

## Dataview Queries

### Quick Examples

```dataview
LIST FROM "06 - Daily" WHERE file.cday = date(today) SORT file.ctime DESC
```

```dataview
TABLE status, tags FROM "01 - Projects" WHERE status != "completed"
```

```dataview
TABLE WITHOUT ID file.link AS "Note", file.mtime AS "Modified"
FROM "03 - Resources"
SORT file.mtime DESC
LIMIT 20
```

```dataview
TASK FROM "01 - Projects" WHERE !completed
```

### Common Patterns

```dataview
# Notes by tag
LIST FROM #project AND -#archived

# Recent notes in folder
TABLE file.mtime AS "Modified" FROM "02 - Areas" SORT file.mtime DESC LIMIT 10

# Notes linking to current file
LIST FROM [[]] SORT file.name ASC

# Orphan detection
LIST FROM "" WHERE length(file.inlinks) = 0 AND length(file.outlinks) = 0
```

## Templater Variables

```markdown
<% tp.file.title %>              # Current file name
<% tp.date.now("YYYY-MM-DD") %>  # Current date
<% tp.file.cursor(1) %>          # Cursor position
<% tp.system.prompt("Question") %> # User input prompt
```

## Installed Plugins

| Plugin | Purpose |
|--------|---------|
| Dataview | Query and display data from notes |
| Templater | Advanced templates with scripting |
| Auto Note Mover | Auto-organize notes by tags |
| Periodic Notes | Daily/weekly/monthly notes |
| Kanban | Kanban boards in markdown |
| Tag Wrangler | Bulk tag management |
| Advanced URI | Deep links to notes |
| Local REST API | External API access |

## Lifecycle States

Notes can move through lifecycle states for processing:

```
inbox -> active -> processed -> archived
```

- **inbox**: Raw capture, needs triage
- **active**: Being worked on
- **processed**: Reviewed, properly tagged and linked
- **archived**: No longer active, preserved for reference

## Best Practices

1. Always include `created` and `updated` timestamps in frontmatter
2. Tag notes for discoverability
3. Link to related notes bidirectionally
4. Use callouts for important information
5. Include navigation links in daily notes (`<< prev | today | next >>`)
6. Place notes in correct PARA folder based on type
7. Use descriptive filenames (avoid special characters except hyphens)
