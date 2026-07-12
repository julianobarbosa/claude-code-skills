# Workflow: Daily Note

Create or enhance daily notes at `06 - Daily/YYYY/MM/YYYYMMDD.md`.

## Steps

### Create Daily Note

1. **Calculate date** - today or specified date
2. **Build path** - `06 - Daily/YYYY/MM/YYYYMMDD.md`
3. **Generate frontmatter** with daily note schema
4. **Add navigation** - prev/next links
5. **Create file** via `Tools/NoteCreator.py daily`

### Enhance Existing Daily Note

1. **Read existing note**
2. **Add structure** - headings, task checkboxes
3. **Add wikilinks** - link mentioned people, projects, concepts
4. **Suggest tags** based on content
5. **Update frontmatter** - update `updated` timestamp

## Tool Usage

```bash
# Create today's daily note
python Tools/NoteCreator.py daily

# Create for specific date
python Tools/NoteCreator.py daily --date 2026-02-09

# Append content to today's note
python Tools/NoteCreator.py daily --append "Met with team about API redesign"

# Create with initial content
python Tools/NoteCreator.py daily --content "## Focus\n- API redesign\n- Code review"
```

### Daily Note Format

```yaml
---
created: 2026-02-09T09:00
updated: 2026-02-09T09:00
title: "20260209"
type: daily-note
status: true
tags:
  - daily
  - 2026
  - 2026-02
date_formatted: 2026-02-09
---

# Daily Note - 2026-02-09

### Tasks
- [ ] Task 1

### Journal


### Navigation
<< [[20260208]] | **Today** | [[20260210]] >>
```

## Context Files

- `reference/vault-organization.md` - Daily note frontmatter schema, naming conventions
- `reference/markdown.md` - Wikilink and callout syntax
