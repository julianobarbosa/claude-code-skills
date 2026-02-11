# Integration Patterns Reference

## Overview

An Obsidian vault is a codebase of markdown files. Claude Code navigates file structures and makes surgical edits natively.

## Pattern Decision Tree

```text
What integration level?
├── Minimal (just works)?       -> Pattern A: Direct Access
├── Enhanced discovery?         -> Pattern B: Manifest-Based (CLAUDE.md)
├── Real-time bidirectional?    -> Pattern C: MCP Plugin
├── Self-evolving PKM?          -> Pattern D: COG Pattern
└── Pre-configured structure?   -> Pattern E: Claudesidian
```

## Pattern A: Direct Access (Zero Setup)

Claude Code reads/edits vault files directly. No configuration needed.

```bash
cd /path/to/vault && claude
# "Read my daily note from today"
# "Find all notes mentioning project X"
# "Add backlinks to people mentioned in this note"
```

| Task | Capability |
|------|-----------|
| Read/edit notes | Direct file access |
| Add backlinks | Find references, insert wikilinks |
| Create notes | Write files with frontmatter |
| Search content | Grep across markdown |
| Refactor structure | Move files, update references |

## Pattern B: Manifest-Based (CLAUDE.md)

Add `CLAUDE.md` at vault root to describe structure, conventions, and rules.

Key sections: Vault Overview, Folder Structure, Conventions (frontmatter, links, tags, dates), Important Files, When Creating/Editing Notes.

## Pattern C: MCP Plugin

Real-time bidirectional via Model Context Protocol.

```json
{
  "mcpServers": {
    "obsidian": {
      "transport": "websocket",
      "url": "ws://localhost:22360"
    }
  }
}
```

Capabilities: `read_note`, `write_note`, `search`, `list_notes`, `get_backlinks`, `get_outlinks`, `get_tags`

Plugin: `obsidian-claude-code-mcp` (Community Plugins)

## Pattern D: COG Self-Evolving

Git-based with auto-organization and self-healing.

```text
vault/
├── .git/
├── CLAUDE.md
├── _meta/
│   ├── patterns.md          # Learned patterns
│   ├── conventions.md       # Auto-discovered rules
│   └── maintenance-log.md   # Self-healing log
├── notes/
└── daily/
```

### Self-Healing Features

1. **Auto cross-references**: Updates links on note moves
2. **Pattern learning**: Discovers and applies conventions
3. **Orphan detection**: Identifies unlinked notes
4. **Consistency checks**: Validates frontmatter, tags

### Git Hooks

```bash
# .git/hooks/post-commit
#!/bin/bash
claude --print "Check for broken links and orphan notes.
Fix issues and update _meta/maintenance-log.md."
```

## Pattern E: Claudesidian

Pre-configured vault structure optimized for AI interaction.

```text
vault/
├── CLAUDE.md
├── Inbox/
├── Projects/
├── Knowledge/
├── Journal/
├── Templates/
└── _meta/
    ├── prompts/
    ├── contexts/
    └── exports/
```

## Comparison

| Feature | Direct | Manifest | MCP | COG | Claudesidian |
|---------|--------|----------|-----|-----|--------------|
| Setup | None | Minimal | Plugin | Git+hooks | Structure |
| Real-time | No | No | Yes | No | No |
| Semantic Search | Basic | Basic | Yes | Basic | Basic |
| Self-Healing | No | No | No | Yes | Partial |
| Vendor Lock-in | None | None | Low | None | Structure |

## Common Workflows

### Auto-Linking Entities

1. Read note content
2. Extract entity mentions (people, places, books)
3. Search vault for existing notes
4. Create new notes if needed
5. Insert `[[wikilinks]]` throughout

### Knowledge Graph Maintenance

1. Identify orphan notes (no in/out links)
2. Analyze content for potential connections
3. Suggest or create links
4. Update MOCs

### Research Synthesis

1. Search for relevant notes by topic
2. Extract key insights
3. Create structured summary note
4. Link back to source notes

### Daily Note Enhancement

1. Read raw daily capture
2. Add proper frontmatter
3. Identify tasks -> add checkboxes
4. Identify mentions -> add wikilinks
5. Suggest tags based on content

## Neovim Integration (obsidian.nvim)

For Neovim users, `obsidian.nvim` provides vault management inside the editor.

### Minimal Setup (lazy.nvim)

```lua
return {
  "obsidian-nvim/obsidian.nvim",
  version = "*",
  ft = "markdown",
  opts = {
    workspaces = {
      { name = "personal", path = "~/vaults/personal" },
    },
  },
}
```

### Key Commands

| Command | Description |
|---------|-------------|
| `:Obsidian today` | Open/create daily note |
| `:Obsidian new [TITLE]` | Create new note |
| `:Obsidian search` | Search vault |
| `:Obsidian quick_switch` | Fuzzy find notes |
| `:Obsidian backlinks` | Show backlinks |
| `:Obsidian template` | Insert template |

### Completion Triggers

- `[[` - Wiki link completion
- `[` - Markdown link completion
- `#` - Tag completion

### Template Variables

| Variable | Description |
|----------|-------------|
| `{{title}}` | Note title |
| `{{date}}` | Current date |
| `{{time}}` | Current time |
| `{{id}}` | Note ID |

Requires: Neovim >= 0.10.0, ripgrep

## Best Practices

1. Keep vault in version control (git rollback + change tracking)
2. Use consistent frontmatter across note types
3. Maintain CLAUDE.md manifest with conventions
4. Regular maintenance (orphan detection, broken link scan)
5. Review AI changes via git diff before committing
6. Document exceptions in manifest

## References

- [obsidian-claude-code-mcp](https://github.com/iansinnott/obsidian-claude-code-mcp)
- [COG-second-brain](https://github.com/huytieu/COG-second-brain)
- [Claudesidian](https://github.com/heyitsnoah/claudesidian)
- [obsidian.nvim](https://github.com/obsidian-nvim/obsidian.nvim)
