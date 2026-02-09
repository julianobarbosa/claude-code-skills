---
name: ObsidianMaster
description: >-
  Comprehensive Obsidian vault management. USE WHEN obsidian, vault, note, daily note,
  PARA, inbox, knowledge capture, dataview, DQL, search vault, .base, bases, wikilink,
  frontmatter, second brain, markdown syntax, obsidian.nvim, OR obsidian API.
  Python-powered tools for search, creation, and vault health.
---

# ObsidianMaster

Unified skill for all Obsidian vault operations. Routes to workflows and context files.

## Workflow Routing

| Intent | Workflow | Tool |
|--------|----------|------|
| Create a note (any type) | `Workflows/CreateNote.md` | `Tools/NoteCreator.py` |
| Search vault (DQL, content, tags) | `Workflows/SearchVault.md` | `Tools/SearchVault.py` |
| Vault health, orphans, broken links | `Workflows/ManageVault.md` | `Tools/VaultManager.py` |
| Extract knowledge from conversation | `Workflows/CaptureKnowledge.md` | `Tools/NoteCreator.py` |
| Create/edit .base database views | `Workflows/CreateBase.md` | `Tools/BaseBuilder.py` |
| Daily note create/enhance | `Workflows/DailyNote.md` | `Tools/NoteCreator.py` |
| Process inbox notes into PARA | `Workflows/ProcessInbox.md` | `Tools/VaultManager.py` |
| Sync project docs to vault | `Workflows/SyncDocs.md` | `Tools/VaultManager.py` |

## Context Files

| File | Content |
|------|---------|
| `MarkdownReference.md` | Obsidian Flavored Markdown: wikilinks, embeds, callouts, properties, math, mermaid |
| `RestApiReference.md` | Local REST API endpoints, URI scheme, plugin API classes, Python client |
| `VaultOrganization.md` | PARA folders, frontmatter schemas, naming conventions, Dataview queries |
| `BasesReference.md` | .base YAML schema, filters, formulas, functions, view types |
| `IntegrationPatterns.md` | Claude Code integration patterns (Direct, Manifest, MCP, COG, Claudesidian) |
| `KnowledgeCapturePatterns.md` | ADR, concept, how-to, meeting note templates for knowledge extraction |

## Examples

```
"Create a new project note for API redesign"     -> Workflows/CreateNote.md
"Search my vault for notes about Kubernetes"      -> Workflows/SearchVault.md
"Find orphan notes and suggest connections"       -> Workflows/ManageVault.md
"Save what we just discussed as an ADR"           -> Workflows/CaptureKnowledge.md
"Create a base view of all active projects"       -> Workflows/CreateBase.md
"Create today's daily note"                       -> Workflows/DailyNote.md
"Process my inbox"                                -> Workflows/ProcessInbox.md
"What's the Obsidian markdown syntax for X?"      -> MarkdownReference.md (context only)
"How do I use the REST API?"                      -> RestApiReference.md (context only)
"How do bases formulas work?"                     -> BasesReference.md (context only)
```

## Tools (Python)

All tools use `click` CLI, `httpx` for REST API, `pyyaml` for frontmatter, `pathlib` for direct file access.
Dual mode: REST API when Obsidian running, direct file fallback otherwise.

| Tool | Commands |
|------|----------|
| `Tools/SearchVault.py` | `status`, `auth`, `search --type dataview\|content\|jsonlogic` |
| `Tools/VaultManager.py` | `health`, `orphans`, `broken-links`, `lifecycle`, `move`, `inbox` |
| `Tools/NoteCreator.py` | `create`, `daily`, `capture` |
| `Tools/BaseBuilder.py` | `create`, `validate`, `preview` |

## Neovim Reference

For obsidian.nvim configuration, see `IntegrationPatterns.md` section on Neovim integration.
