---
name: tldr
description: >-
  Save, read, update, or delete conversation summaries in the vault.
  USE WHEN tldr, save summary, session summary, what did we do,
  recap session, conversation summary, update tldr, delete tldr.
---

# tldr-skill

Manage conversation summaries (tldrs) in the Obsidian vault. Each tldr captures decisions, key things to remember, and next actions.

**Vault root: `~/.obsidian/vaults/.obsidian-barbosa-0/`.** All paths below are relative to this vault root. Always resolve to absolute paths when reading or writing files — never use the current working directory.

## Operations

| Command | Operation | Description |
|---------|-----------|-------------|
| `/tldr` | **Create** | Summarize session → prompt for project → save |
| `/tldr read {project}` | **Read** | Show latest tldr for a project |
| `/tldr update {project}` | **Update** | Append to or revise existing tldr |
| `/tldr delete {project}` | **Delete** | Remove a tldr (with confirmation) |

## File Naming

```
01 - Projects/{project-name}/YYYY-MM-DD-HH-mm-{project-name}-tldr.md
```

Example: `01 - Projects/vault-setup-skill/2026-03-19-12-03-vault-setup-skill-tldr.md`

## Create (default operation)

This is the primary operation when `/tldr` is invoked with no arguments.

### Step 1 — Identify Project

Ask the user:

> **Which project is this for?**
>
> Suggest: `{inferred project name from conversation context}`

Use the conversation topic to suggest a project name. The user confirms or provides a different name. Kebab-case the name for the filename.

### Step 2 — Summarize

Extract from the conversation:

1. **What was done** — concrete actions taken, files changed
2. **What was decided** — design choices, trade-offs, rationale
3. **Key things to remember** — gotchas, patterns, non-obvious details
4. **Next actions** — if any remain

### Step 3 — Save

Write to `01 - Projects/{project-name}/YYYY-MM-DD-HH-mm-{project-name}-tldr.md` using current time.

If the project subfolder doesn't exist, create it.

Template:

```markdown
---
created: YYYY-MM-DDTHH:mm
tags:
  - project/{project-name}
  - tldr
status: complete
---

# YYYY-MM-DD — {Project Name}

## What Was Done
[concrete actions, files changed]

## Decisions
[design choices with rationale]

## Key Things to Remember
[gotchas, patterns, non-obvious details]

## Next Actions
- [ ] [action items, if any]
- None — work is complete
```

### Step 4 — Update Memory

Read `memory.md` at vault root (`~/.obsidian/vaults/.obsidian-barbosa-0/memory.md`). Append any new:
- Session log entry (one line: date + project + what happened)
- Preferences discovered during the session

Do NOT duplicate existing entries.

## Read

```
/tldr read {project-name}
```

Search `01 - Projects/{project-name}/` for files matching `*-{project-name}-tldr.md`. Show the most recent one (by filename timestamp). If multiple exist, list them and ask which to show.

## Update

```
/tldr update {project-name}
```

Find the most recent tldr for the project. Read it. Ask the user what to add or change. Edit the file — append new sections or revise existing ones. Update the `updated` frontmatter field.

## Delete

```
/tldr delete {project-name}
```

Find tldrs matching the project name. List them with dates. Ask for confirmation before deleting:

> **Delete `01 - Projects/vault-setup-skill/2026-03-19-12-03-vault-setup-skill-tldr.md`?** This cannot be undone.

Only delete after explicit "yes" or "delete it" confirmation.

## Folder Routing

The default destination is `01 - Projects/{project-name}/`. However, route differently when the conversation topic clearly fits another folder:

| Topic | Destination | Example |
|-------|-------------|---------|
| Project work (default) | `01 - Projects/{project-name}/` | Most sessions |
| Client-specific work | `02 - Areas/{client-name}/` | Work for a specific client |
| Research / evaluation | `03 - Resources/` | Tool evals, investigations |
| General / no project | `06 - Daily/` | Quick chats, no clear project |

When routing to a non-projects folder, the filename pattern stays the same: `YYYY-MM-DD-HH-mm-{topic}-tldr.md`
