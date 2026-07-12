# Obsidian Vault Manifest

> This file helps Claude Code understand your vault's structure and conventions.
> Customize the sections below to match your personal knowledge management system.

## Vault Overview

<!-- Describe your vault's purpose and organization philosophy -->

This is a personal knowledge management vault following [PARA/Zettelkasten/Johnny Decimal/Custom] methodology.

**Primary purposes:**
- Personal note-taking and journaling
- Project documentation
- Learning and research
- [Add your specific use cases]

## Folder Structure

<!-- Document your folder hierarchy -->

| Folder | Purpose | Note Types |
|--------|---------|------------|
| `Inbox/` | Quick capture, unsorted | Fleeting notes |
| `Projects/` | Active work | Project notes, tasks |
| `Areas/` | Ongoing responsibilities | Area overviews |
| `Resources/` | Reference materials | Evergreen notes |
| `Archive/` | Completed/inactive | Archived projects |
| `Daily/` | Daily notes | Journal entries |
| `Templates/` | Note templates | - |

## Frontmatter Schema

<!-- Define your standard frontmatter fields -->

### Required Fields (All Notes)

```yaml
---
created: YYYY-MM-DDTHH:mm
updated: YYYY-MM-DDTHH:mm
tags:
  - category/subcategory
---
```

### Project Notes

```yaml
---
created: YYYY-MM-DDTHH:mm
updated: YYYY-MM-DDTHH:mm
type: project
status: active | paused | complete
priority: high | medium | low
due: YYYY-MM-DD
tags:
  - project/name
---
```

### Daily Notes

```yaml
---
created: YYYY-MM-DDTHH:mm
type: daily
date: YYYY-MM-DD
mood:
energy:
tags:
  - daily
  - YYYY
  - YYYY-MM
---
```

## Naming Conventions

<!-- Document how files should be named -->

- **Regular notes**: `kebab-case-descriptive-title.md`
- **Daily notes**: `YYYY-MM-DD.md` in `Daily/YYYY/MM/` folder
- **Project notes**: `PROJECT-name.md` prefix
- **People notes**: `@firstname-lastname.md`
- **Book notes**: `BOOK-title-author.md`

## Link Conventions

<!-- How internal linking should work -->

- Use `[[wikilinks]]` for all internal links (not markdown links)
- Link to specific headings: `[[Note#Heading]]`
- Use block references: `[[Note#^block-id]]`
- Alias display text: `[[Long Note Name|Short Name]]`

## Tag Hierarchy

<!-- Your tag structure -->

```text
#type/
  ├── note
  ├── project
  ├── daily
  ├── meeting
  └── reference

#status/
  ├── active
  ├── review
  ├── paused
  └── complete

#topic/
  └── [your topics]

#source/
  ├── book
  ├── article
  ├── video
  └── conversation
```

## Important Files

<!-- Key notes Claude Code should be aware of -->

- `_index.md` - Main dashboard / Map of Content
- `project-context.md` - Current project context (if applicable)
- `_templates/` - Template files location

## Claude Code Instructions

### When Creating Notes

1. Always add required frontmatter fields
2. Place in appropriate folder based on type
3. Use proper naming convention
4. Add relevant tags
5. Include backlinks to related notes

### When Editing Notes

1. Update the `updated` timestamp
2. Preserve existing wikilinks
3. Maintain block references (`^block-id`)
4. Don't modify frontmatter `created` date

### When Organizing

1. Respect existing folder structure
2. Update all wikilinks when moving files
3. Don't delete notes without confirmation
4. Archive instead of delete when possible

### When Searching

1. Consider wikilinks and backlinks
2. Check frontmatter metadata
3. Look in appropriate folders first
4. Use tags to narrow scope

## Automation Preferences

<!-- What Claude Code should do automatically -->

### Always Do
- [ ] Fix broken wikilinks
- [ ] Add missing frontmatter to inbox notes
- [ ] Update `updated` timestamp on edits

### Ask First
- [ ] Move notes between folders
- [ ] Create new notes
- [ ] Modify tag structure
- [ ] Archive old notes

### Never Do
- [ ] Delete any notes
- [ ] Modify `.obsidian/` folder
- [ ] Change plugin settings

## Custom Commands

<!-- Common requests and expected behavior -->

| Command | Expected Behavior |
|---------|-------------------|
| "Process inbox" | Add frontmatter, suggest folders, add links |
| "Daily review" | Summarize today's note, suggest tasks |
| "Find orphans" | List unlinked notes |
| "Weekly summary" | Create summary of week's notes |

## Notes

<!-- Any additional context -->

- This vault is [private/shared/synced with X]
- Primary device: [macOS/Windows/Linux]
- Obsidian plugins in use: [Dataview, Templater, etc.]
