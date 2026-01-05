# MCP Integration Reference

## Model Context Protocol Overview

MCP (Model Context Protocol) enables real-time bidirectional communication between
Claude Code and Obsidian. The obsidian-claude-code-mcp plugin implements an MCP
server inside Obsidian that Claude Code can connect to.

## Architecture

```text
┌─────────────────┐     WebSocket      ┌─────────────────┐
│   Claude Code   │◄──────────────────►│    Obsidian     │
│   (MCP Client)  │     Port 22360     │   (MCP Server)  │
└─────────────────┘                    └─────────────────┘
        │                                      │
        │                                      │
        ▼                                      ▼
   AI Processing                         Vault Access
   - Read notes                          - File I/O
   - Edit content                        - Metadata cache
   - Search vault                        - Link resolution
```

## Installation

### From Community Plugins

1. Open Obsidian Settings
2. Navigate to Community Plugins
3. Disable Safe Mode if prompted
4. Click Browse and search for "claude-code-mcp"
5. Install and Enable

### Manual Installation

```bash
# Clone the plugin repository
git clone https://github.com/iansinnott/obsidian-claude-code-mcp.git

# Copy to Obsidian plugins folder
cp -r obsidian-claude-code-mcp /path/to/vault/.obsidian/plugins/

# Restart Obsidian and enable the plugin
```

## Configuration

### Plugin Settings

| Setting | Default | Description |
|---------|---------|-------------|
| Port | 22360 | WebSocket server port |
| Auto-start | true | Start server on plugin load |
| Debug mode | false | Verbose logging |

### Claude Code Configuration

If auto-discovery fails, add to Claude Code settings:

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

## MCP Protocol Messages

### read_note

Read a note's content and metadata.

```json
{
  "method": "read_note",
  "params": {
    "path": "Notes/MyNote.md"
  }
}
```

Response:

```json
{
  "content": "# My Note\n\nContent here...",
  "frontmatter": {
    "created": "2025-01-05",
    "tags": ["tag1", "tag2"]
  },
  "links": ["[[Other Note]]", "[[Reference]]"],
  "backlinks": ["[[Linking Note]]"]
}
```

### write_note

Create or update a note.

```json
{
  "method": "write_note",
  "params": {
    "path": "Notes/NewNote.md",
    "content": "# New Note\n\nContent...",
    "createFolders": true
  }
}
```

### search

Search vault content.

```json
{
  "method": "search",
  "params": {
    "query": "search term",
    "limit": 20
  }
}
```

Response:

```json
{
  "results": [
    {
      "path": "Notes/Match1.md",
      "score": 0.95,
      "matches": ["...context with **search term**..."]
    }
  ]
}
```

### list_notes

Browse vault structure.

```json
{
  "method": "list_notes",
  "params": {
    "folder": "Projects",
    "recursive": true
  }
}
```

### get_backlinks

Find notes linking to a file.

```json
{
  "method": "get_backlinks",
  "params": {
    "path": "Notes/Topic.md"
  }
}
```

### get_tags

List all tags in vault.

```json
{
  "method": "get_tags",
  "params": {}
}
```

Response:

```json
{
  "tags": [
    {"name": "#project", "count": 15},
    {"name": "#project/active", "count": 8},
    {"name": "#reference", "count": 42}
  ]
}
```

## Error Handling

### Connection Errors

```text
Error: WebSocket connection failed
├── Cause: Obsidian not running
│   └── Fix: Launch Obsidian
├── Cause: Plugin not enabled
│   └── Fix: Enable obsidian-claude-code-mcp plugin
├── Cause: Port conflict
│   └── Fix: Change port in plugin settings
└── Cause: Firewall blocking
    └── Fix: Allow localhost:22360
```

### File Errors

```text
Error: Note not found
├── Cause: Path incorrect
│   └── Fix: Use relative path from vault root
├── Cause: File moved/renamed
│   └── Fix: Use search to find new location
└── Cause: Case sensitivity
    └── Fix: Match exact case on Linux/macOS
```

## Advanced Usage

### Combining with Direct Access

MCP and direct file access can work together:

```text
MCP for:
- Real-time semantic search
- Backlink resolution
- Metadata access

Direct access for:
- Bulk file operations
- Complex refactoring
- Performance-critical reads
```

### Custom MCP Commands

The plugin supports custom commands via Obsidian's command palette:

```json
{
  "method": "execute_command",
  "params": {
    "id": "daily-notes:open-daily-note"
  }
}
```

## Performance Considerations

1. **Large vaults**: MCP indexes incrementally; initial sync may take time
2. **Many connections**: Single WebSocket per vault recommended
3. **Concurrent edits**: Obsidian handles conflicts; review before saving
4. **Memory usage**: MCP server runs in Obsidian's renderer process

## Debugging

### Enable Debug Mode

1. Open plugin settings
2. Enable "Debug mode"
3. Open developer console (Ctrl+Shift+I)
4. Watch for MCP protocol messages

### Connection Test

```bash
# Using websocat
websocat ws://localhost:22360

# Send test message
{"method": "list_notes", "params": {}}
```

### Common Issues

| Issue | Solution |
|-------|----------|
| No auto-discovery | Add manual config to Claude Code settings |
| Slow search | Reduce vault size or use folder filters |
| Stale data | Trigger vault refresh in Obsidian |
| Connection drops | Check network stability, increase timeout |
