# Obsidian Vault Structure Reference

Complete reference for Obsidian vault organization and configuration.

## Vault Overview

A vault is a folder on your local file system containing:

- Markdown files (`.md`)
- Attachments (images, PDFs, etc.)
- Configuration folder (`.obsidian`)

## Directory Structure

```text
my-vault/
├── .obsidian/                    # Configuration folder
│   ├── app.json                  # App settings
│   ├── appearance.json           # Theme & UI settings
│   ├── backlink.json             # Backlink settings
│   ├── bookmarks.json            # Bookmarked files/searches
│   ├── canvas.json               # Canvas default settings
│   ├── command-palette.json      # Command palette config
│   ├── community-plugins.json    # Enabled community plugins list
│   ├── core-plugins.json         # Core plugin toggles
│   ├── core-plugins-migration.json
│   ├── daily-notes.json          # Daily notes settings
│   ├── graph.json                # Graph view settings
│   ├── hotkeys.json              # Custom keybindings
│   ├── templates.json            # Template settings
│   ├── workspace.json            # Current workspace layout
│   ├── workspaces.json           # Saved workspaces
│   │
│   ├── plugins/                  # Community plugin data
│   │   └── <plugin-id>/
│   │       ├── data.json         # Plugin settings
│   │       ├── main.js           # Plugin code
│   │       ├── manifest.json     # Plugin metadata
│   │       └── styles.css        # Plugin styles
│   │
│   ├── themes/                   # Custom themes
│   │   └── <theme-name>/
│   │       ├── manifest.json
│   │       └── theme.css
│   │
│   └── snippets/                 # CSS snippets
│       └── my-snippet.css
│
├── Notes/                        # User notes (customizable)
├── Attachments/                  # Media files
├── Templates/                    # Template files
└── Daily Notes/                  # Daily notes folder
```

## Configuration Files

### app.json

General application settings:

```json
{
  "legacyEditor": false,
  "livePreview": true,
  "foldHeading": true,
  "foldIndent": true,
  "showLineNumber": false,
  "showFrontmatter": false,
  "strictLineBreaks": false,
  "readableLineLength": true,
  "tabSize": 4,
  "spellcheck": true,
  "spellcheckLanguages": ["en-US"],
  "defaultViewMode": "source",
  "promptDelete": true,
  "alwaysUpdateLinks": true,
  "newFileLocation": "current",
  "newFileFolderPath": "",
  "attachmentFolderPath": "./attachments",
  "showUnsupportedFiles": false,
  "useMarkdownLinks": false
}
```

### appearance.json

Theme and visual settings:

```json
{
  "baseFontSize": 16,
  "baseFontSizeAction": true,
  "interfaceFontFamily": "",
  "textFontFamily": "",
  "monospaceFontFamily": "",
  "theme": "obsidian",
  "translucency": false,
  "cssTheme": "Minimal",
  "enabledCssSnippets": ["my-custom-styles"]
}
```

### core-plugins.json

Toggle built-in plugins:

```json
{
  "file-explorer": true,
  "global-search": true,
  "switcher": true,
  "graph": true,
  "backlink": true,
  "outgoing-link": true,
  "tag-pane": true,
  "page-preview": true,
  "daily-notes": true,
  "templates": true,
  "note-composer": true,
  "command-palette": true,
  "slash-command": false,
  "editor-status": true,
  "bookmarks": true,
  "markdown-importer": false,
  "zk-prefixer": false,
  "random-note": false,
  "outline": true,
  "word-count": true,
  "slides": false,
  "audio-recorder": false,
  "workspaces": true,
  "file-recovery": true,
  "publish": false,
  "sync": false,
  "canvas": true
}
```

### community-plugins.json

List of enabled community plugins:

```json
[
  "dataview",
  "templater-obsidian",
  "obsidian-git",
  "obsidian-advanced-uri"
]
```

### hotkeys.json

Custom keybindings:

```json
[
  {
    "key": "Mod+Shift+N",
    "modifiers": ["Mod", "Shift"],
    "command": "daily-notes"
  },
  {
    "key": "Mod+Shift+T",
    "modifiers": ["Mod", "Shift"],
    "command": "templater-obsidian:insert-templater"
  },
  {
    "key": "Mod+E",
    "modifiers": ["Mod"],
    "command": "editor:toggle-source"
  }
]
```

### workspace.json

Current workspace layout (auto-managed):

```json
{
  "main": {
    "id": "root",
    "type": "split",
    "children": [
      {
        "id": "leaf-1",
        "type": "leaf",
        "state": {
          "type": "markdown",
          "state": {
            "file": "Notes/MyNote.md",
            "mode": "source",
            "source": false
          }
        }
      }
    ],
    "direction": "vertical"
  },
  "left": { /* sidebar config */ },
  "right": { /* sidebar config */ },
  "active": "leaf-1",
  "lastOpenFiles": [
    "Notes/MyNote.md",
    "Notes/AnotherNote.md"
  ]
}
```

### daily-notes.json

Daily notes configuration:

```json
{
  "folder": "Daily Notes",
  "format": "YYYY-MM-DD",
  "template": "Templates/Daily Template",
  "autorun": true
}
```

### templates.json

Template settings:

```json
{
  "folder": "Templates",
  "dateFormat": "YYYY-MM-DD",
  "timeFormat": "HH:mm"
}
```

### graph.json

Graph view settings:

```json
{
  "search": "",
  "showTags": true,
  "showAttachments": false,
  "showOrphans": true,
  "collapse-filter": true,
  "showArrow": false,
  "textFadeMultiplier": 0,
  "nodeSizeMultiplier": 1,
  "lineSizeMultiplier": 1,
  "centerStrength": 0.5,
  "repelStrength": 10,
  "linkStrength": 1,
  "linkDistance": 250,
  "scale": 1,
  "close": true
}
```

## Plugin Data

### Plugin Folder Structure

Each community plugin has its own folder:

```text
.obsidian/plugins/<plugin-id>/
├── data.json       # Plugin settings (varies by plugin)
├── main.js         # Compiled plugin code
├── manifest.json   # Plugin metadata
└── styles.css      # Plugin styles (optional)
```

### Plugin manifest.json

```json
{
  "id": "my-plugin",
  "name": "My Plugin",
  "version": "1.2.3",
  "minAppVersion": "1.0.0",
  "description": "Plugin description",
  "author": "Author Name",
  "authorUrl": "https://example.com",
  "isDesktopOnly": false
}
```

## Themes

### Theme Structure

```text
.obsidian/themes/<theme-name>/
├── manifest.json
└── theme.css
```

### Theme manifest.json

```json
{
  "name": "My Theme",
  "version": "1.0.0",
  "minAppVersion": "1.0.0"
}
```

## CSS Snippets

Custom CSS can be added as snippets:

```text
.obsidian/snippets/
├── custom-fonts.css
├── hide-sidebars.css
└── table-styles.css
```

Enable snippets in Settings > Appearance > CSS Snippets.

### Example Snippet

```css
/* custom-fonts.css */
.markdown-source-view,
.markdown-preview-view {
  font-family: 'JetBrains Mono', monospace;
}

/* Hide certain UI elements */
.nav-folder.mod-root > .nav-folder-title {
  display: none;
}

/* Custom callout style */
.callout[data-callout="custom"] {
  --callout-color: 100, 50, 200;
  --callout-icon: lucide-star;
}
```

## File Formats

### Markdown Files

Standard markdown with Obsidian extensions:

```markdown
---
title: Note Title
date: 2024-01-15
tags:
  - tag1
  - tag2
aliases:
  - Alternate Name
cssclass: custom-class
---

# Heading

Regular markdown content with [[Internal Links]].

![[Embedded Note]]

> [!note] Callout
> Callout content
```

### Canvas Files (.canvas)

JSON-based canvas format:

```json
{
  "nodes": [
    {
      "id": "abc123",
      "type": "text",
      "text": "Text content",
      "x": 0,
      "y": 0,
      "width": 250,
      "height": 60
    },
    {
      "id": "def456",
      "type": "file",
      "file": "Notes/MyNote.md",
      "x": 300,
      "y": 0,
      "width": 400,
      "height": 400
    }
  ],
  "edges": [
    {
      "id": "edge1",
      "fromNode": "abc123",
      "fromSide": "right",
      "toNode": "def456",
      "toSide": "left"
    }
  ]
}
```

## Sync Considerations

### Files to Sync

For syncing between devices:

```text
.obsidian/
├── app.json              # Sync
├── appearance.json       # Sync
├── community-plugins.json # Sync
├── core-plugins.json     # Sync
├── hotkeys.json          # Sync
├── templates.json        # Sync
├── daily-notes.json      # Sync
├── graph.json            # Sync
├── plugins/              # Sync (without main.js for size)
├── themes/               # Sync
├── snippets/             # Sync
└── workspace.json        # Usually don't sync
```

### Files to Exclude

```text
.obsidian/
├── workspace.json        # Device-specific layout
├── workspaces.json       # Device-specific
├── cache/                # Temporary cache
└── plugins/*/main.js     # Can be re-downloaded
```

### .gitignore for Vaults

```gitignore
# Obsidian
.obsidian/workspace.json
.obsidian/workspaces.json
.obsidian/workspace-mobile.json
.obsidian/cache/
.obsidian/.obsidian

# Plugin binaries (can be re-downloaded)
.obsidian/plugins/*/main.js
.obsidian/plugins/*/.hotreload

# Theme binaries
.obsidian/themes/*/theme.css

# OS files
.DS_Store
Thumbs.db
```

## Custom Configuration Location

Override the default `.obsidian` folder:

1. Open Settings > Files and Links
2. Set "Override config folder" to custom name
3. Use `.obsidian-custom` or similar

Useful for:

- Multiple configurations in same vault
- Testing different settings
- Sync service conflicts

## Backup and Migration

### Backup Important Files

```bash
# Backup config
cp -r .obsidian .obsidian-backup

# Backup specific settings
cp .obsidian/hotkeys.json ./hotkeys-backup.json
cp .obsidian/community-plugins.json ./plugins-backup.json
```

### Migrate to New Vault

```bash
# Copy config to new vault
cp -r old-vault/.obsidian new-vault/.obsidian

# Or selective copy
cp old-vault/.obsidian/hotkeys.json new-vault/.obsidian/
cp old-vault/.obsidian/appearance.json new-vault/.obsidian/
cp -r old-vault/.obsidian/snippets new-vault/.obsidian/
```

### Reset Configuration

```bash
# Remove all config (caution!)
rm -rf .obsidian

# Obsidian will recreate default config on next open
```

## Vault Management Commands

### CLI Operations

```bash
# Open vault
open "obsidian://open?vault=MyVault"

# List vault files
find . -name "*.md" -type f

# Count notes
find . -name "*.md" | wc -l

# Find orphan files (no links)
# Requires additional tooling

# Search in vault
grep -r "search term" --include="*.md"

# List recently modified
find . -name "*.md" -mtime -7
```

### Validate Configuration

```bash
# Check if valid JSON
jq . .obsidian/app.json
jq . .obsidian/community-plugins.json

# List enabled plugins
jq '.[]' .obsidian/community-plugins.json

# List hotkeys
jq '.[] | .command' .obsidian/hotkeys.json
```
