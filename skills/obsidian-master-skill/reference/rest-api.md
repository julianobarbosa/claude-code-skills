# Obsidian REST API & URI Scheme Reference

## Local REST API Plugin

The Local REST API plugin provides HTTP endpoints for programmatic vault access.

### Setup

1. Install "Local REST API" from Community Plugins
2. Enable the plugin
3. Configure API key in plugin settings
4. Default endpoint: `https://127.0.0.1:27124`

### Authentication

```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     https://127.0.0.1:27124/vault/
```

Environment variables: `OBSIDIAN_API_KEY`, `OBSIDIAN_BASE_URL`

### Endpoints

```bash
# File Operations
GET    /vault/                    # List all files
GET    /vault/{path}              # Get file content
PUT    /vault/{path}              # Create/update file (Content-Type: text/markdown)
DELETE /vault/{path}              # Delete file
PATCH  /vault/{path}              # Append/prepend to file

# Search
POST   /search/simple/           # Simple text search
POST   /search/                   # Dataview query (DQL)
POST   /search/jsonlogic/        # JsonLogic search

# Active File
GET    /active/                   # Get active file info
PUT    /active/                   # Set active file content

# Commands
POST   /commands/{command-id}     # Execute Obsidian command
GET    /commands/                  # List available commands

# Open
POST   /open/{path}               # Open file in Obsidian
```

### Search Examples

```bash
# Simple text search
curl -X POST https://127.0.0.1:27124/search/simple/ \
  -H "Authorization: Bearer $OBSIDIAN_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "search term"}'

# Dataview query (DQL)
curl -X POST https://127.0.0.1:27124/search/ \
  -H "Authorization: Bearer $OBSIDIAN_API_KEY" \
  -H "Content-Type: application/vnd.olrapi.dataview.dql+txt" \
  -d 'TABLE status, tags FROM "01 - Projects" WHERE status != "completed"'

# JsonLogic query
curl -X POST https://127.0.0.1:27124/search/jsonlogic/ \
  -H "Authorization: Bearer $OBSIDIAN_API_KEY" \
  -H "Content-Type: application/vnd.olrapi.jsonlogic+json" \
  -d '{"and": [{"glob": ["01 - Projects/**", {"var": "path"}]}, {"!==": [{"var": "frontmatter.status"}, "completed"]}]}'
```

### Python Client (httpx)

```python
import httpx
import os

class ObsidianAPI:
    def __init__(self):
        self.base_url = os.getenv("OBSIDIAN_BASE_URL", "https://127.0.0.1:27124")
        self.api_key = os.getenv("OBSIDIAN_API_KEY", "")
        self.client = httpx.Client(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            verify=False,  # Self-signed cert
            timeout=30.0,
        )

    def list_files(self, path: str = "") -> list:
        r = self.client.get(f"/vault/{path}")
        r.raise_for_status()
        return r.json()["files"]

    def read_file(self, path: str) -> str:
        r = self.client.get(f"/vault/{path}", headers={"Accept": "text/markdown"})
        r.raise_for_status()
        return r.text

    def write_file(self, path: str, content: str) -> bool:
        r = self.client.put(
            f"/vault/{path}",
            content=content.encode("utf-8"),
            headers={"Content-Type": "text/markdown"},
        )
        return r.status_code == 204

    def search_simple(self, query: str) -> list:
        r = self.client.post("/search/simple/", json={"query": query})
        r.raise_for_status()
        return r.json()

    def search_dataview(self, dql: str) -> list:
        r = self.client.post(
            "/search/",
            content=dql.encode("utf-8"),
            headers={"Content-Type": "application/vnd.olrapi.dataview.dql+txt"},
        )
        r.raise_for_status()
        return r.json()

    def search_jsonlogic(self, logic: dict) -> list:
        r = self.client.post(
            "/search/jsonlogic/",
            json=logic,
            headers={"Content-Type": "application/vnd.olrapi.jsonlogic+json"},
        )
        r.raise_for_status()
        return r.json()

    def open_file(self, path: str) -> bool:
        r = self.client.post(f"/open/{path}")
        return r.status_code == 200
```

## URI Scheme

Native `obsidian://` protocol for automation:

```bash
obsidian://open?vault=MyVault                    # Open vault
obsidian://open?vault=MyVault&file=Notes/MyNote  # Open file
obsidian://new?vault=MyVault&name=NewNote&content=Hello  # Create note
obsidian://search?vault=MyVault&query=keyword    # Search
obsidian://daily?vault=MyVault                   # Open daily note
```

### URI Parameters

| Parameter | Description |
|-----------|-------------|
| `vault` | Vault name (required) |
| `file` | File path without `.md` extension |
| `path` | Full file path including folders |
| `name` | Note name for creation |
| `content` | Content to insert |
| `query` | Search query |
| `heading` | Navigate to heading |
| `block` | Navigate to block reference |

Note: URL-encode spaces as `%20`, slashes as `%2F`, ampersands as `%26`.

## Plugin Development API

### Core API Classes

| Class | Purpose | Access |
|-------|---------|--------|
| `App` | Central application instance | `this.app` |
| `Vault` | File system operations | `this.app.vault` |
| `Workspace` | Pane and layout management | `this.app.workspace` |
| `MetadataCache` | File metadata indexing | `this.app.metadataCache` |
| `FileManager` | User-safe file operations | `this.app.fileManager` |

### Plugin Template

```typescript
import { Plugin, Notice, MarkdownView } from 'obsidian';

export default class MyPlugin extends Plugin {
  async onload() {
    this.addCommand({
      id: 'my-command',
      name: 'My Command',
      callback: () => new Notice('Hello!'),
    });

    this.addCommand({
      id: 'my-editor-command',
      name: 'Insert Text',
      editorCallback: (editor, view: MarkdownView) => {
        editor.replaceSelection('Inserted text');
      },
    });

    this.registerEvent(
      this.app.workspace.on('file-open', (file) => {
        if (file) console.log('Opened:', file.path);
      })
    );
  }

  onunload() {}
}
```

### Plugin Structure

```text
my-plugin/
├── main.ts           # Entry point
├── manifest.json     # Metadata (id, name, version, minAppVersion)
├── package.json
├── styles.css
├── tsconfig.json
└── esbuild.config.mjs
```

## CLI Tools

```bash
# Go CLI (Yakitrak)
obsidian-cli open "Note Name"
obsidian-cli search "query"
obsidian-cli create "New Note"
obsidian-cli daily
obsidian-cli list

# Python CLI
obs vault list
obs vault create <name>
obs note search <query>
```

## References

- [Local REST API Plugin](https://github.com/coddingtonbear/obsidian-local-rest-api)
- [Advanced URI Plugin](https://vinzent03.github.io/obsidian-advanced-uri/)
- [Obsidian Developer Docs](https://docs.obsidian.md/)
- [Obsidian API Types](https://github.com/obsidianmd/obsidian-api)
