# Obsidian URI Scheme Reference

Complete reference for Obsidian's URI automation capabilities.

## Native URI Scheme

Obsidian registers the `obsidian://` protocol for deep linking and automation.

### Basic Format

```text
obsidian://action?param1=value1&param2=value2
```

### Actions

#### open

Opens a vault or file.

```bash
# Open vault
obsidian://open?vault=MyVault

# Open file (without .md extension)
obsidian://open?vault=MyVault&file=Notes/MyNote

# Open file with full path
obsidian://open?vault=MyVault&path=Notes/SubFolder/MyNote.md

# Open and navigate to line
obsidian://open?vault=MyVault&file=MyNote&line=10
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `vault` | Yes | Vault name |
| `file` | No | File path without extension |
| `path` | No | Full file path with extension |
| `line` | No | Line number to navigate to |

#### new

Creates a new note.

```bash
# Create note with name
obsidian://new?vault=MyVault&name=NewNote

# Create with content
obsidian://new?vault=MyVault&name=NewNote&content=Hello%20World

# Create in folder
obsidian://new?vault=MyVault&name=Folder/NewNote

# Create with template
obsidian://new?vault=MyVault&name=NewNote&template=Templates/MyTemplate

# Overwrite if exists
obsidian://new?vault=MyVault&name=NewNote&overwrite=true

# Append to existing
obsidian://new?vault=MyVault&name=NewNote&append=true
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `vault` | Yes | Vault name |
| `name` | Yes | Note name (can include path) |
| `content` | No | URL-encoded content |
| `template` | No | Template file path |
| `overwrite` | No | Replace existing file |
| `append` | No | Append to existing file |
| `silent` | No | Don't open the note |

#### search

Opens the search panel with a query.

```bash
# Simple search
obsidian://search?vault=MyVault&query=keyword

# Search with operators
obsidian://search?vault=MyVault&query=tag:%23important

# File search
obsidian://search?vault=MyVault&query=file:readme
```

| Parameter | Required | Description |
|-----------|----------|-------------|
| `vault` | Yes | Vault name |
| `query` | Yes | URL-encoded search query |

## Advanced URI Plugin

The Advanced URI plugin extends native URIs with more capabilities.

### Installation

1. Install "Advanced URI" from Community Plugins
2. Enable the plugin

### Advanced URI Format

```text
obsidian://adv-uri?param1=value1&param2=value2
```

### File Identification

```bash
# By file path
obsidian://adv-uri?vault=MyVault&filepath=Notes/MyNote.md

# By file UID (requires UID plugin)
obsidian://adv-uri?vault=MyVault&uid=abc123

# By daily note
obsidian://adv-uri?vault=MyVault&daily=true

# By periodic note
obsidian://adv-uri?vault=MyVault&periodic=weekly
```

### Content Operations

```bash
# Write content (replace)
obsidian://adv-uri?vault=MyVault&filepath=Note.md&data=New%20Content&mode=overwrite

# Append content
obsidian://adv-uri?vault=MyVault&filepath=Note.md&data=Appended%20text&mode=append

# Prepend content
obsidian://adv-uri?vault=MyVault&filepath=Note.md&data=Prepended%20text&mode=prepend

# Insert from clipboard
obsidian://adv-uri?vault=MyVault&filepath=Note.md&clipboard=true&mode=append

# Insert at heading
obsidian://adv-uri?vault=MyVault&filepath=Note.md&heading=Section&data=Content&mode=append

# Insert at block
obsidian://adv-uri?vault=MyVault&filepath=Note.md&block=block-id&data=Content&mode=append
```

| Parameter | Description |
|-----------|-------------|
| `data` | URL-encoded content to write |
| `mode` | overwrite, append, prepend, new |
| `clipboard` | Use clipboard content |
| `heading` | Target heading |
| `block` | Target block ID |

### Navigation

```bash
# Go to heading
obsidian://adv-uri?vault=MyVault&filepath=Note.md&heading=MyHeading

# Go to block
obsidian://adv-uri?vault=MyVault&filepath=Note.md&block=block-id

# Go to line
obsidian://adv-uri?vault=MyVault&filepath=Note.md&line=50

# Open in new pane
obsidian://adv-uri?vault=MyVault&filepath=Note.md&newpane=true

# Open in reading view
obsidian://adv-uri?vault=MyVault&filepath=Note.md&viewmode=preview

# Open in editing view
obsidian://adv-uri?vault=MyVault&filepath=Note.md&viewmode=source
```

### Command Execution

```bash
# Execute command by ID
obsidian://adv-uri?vault=MyVault&commandid=app:open-settings

# Execute with file context
obsidian://adv-uri?vault=MyVault&filepath=Note.md&commandid=workspace:export-pdf

# Common command IDs:
# app:open-settings
# app:open-help
# editor:toggle-fold
# workspace:export-pdf
# workspace:split-vertical
# workspace:split-horizontal
```

### Workspace Operations

```bash
# Load workspace layout
obsidian://adv-uri?vault=MyVault&workspace=MyWorkspace

# Save current workspace
obsidian://adv-uri?vault=MyVault&saveworkspace=MyWorkspace
```

### Frontmatter Manipulation

```bash
# Update frontmatter field
obsidian://adv-uri?vault=MyVault&filepath=Note.md&frontmatterkey=status&frontmattervalue=done

# Multiple fields (JSON)
obsidian://adv-uri?vault=MyVault&filepath=Note.md&updatepluginid=adv-uri&updatekeys=status,priority&updatevalues=done,high
```

### Search and Replace

```bash
# Search and replace in file
obsidian://adv-uri?vault=MyVault&filepath=Note.md&search=old%20text&replace=new%20text

# Regex search
obsidian://adv-uri?vault=MyVault&filepath=Note.md&searchregex=%5Cbold%5Cb&replace=new
```

### Advanced Parameters

| Parameter | Description |
|-----------|-------------|
| `newpane` | Open in new pane (true/false) |
| `viewmode` | source, preview, live |
| `openmode` | tab, split, window, hover |
| `focus` | Focus after opening (true/false) |
| `line` | Jump to line number |
| `column` | Jump to column |
| `settingid` | Open specific settings tab |
| `eval` | Execute JavaScript (requires explicit enable) |
| `x-success` | Callback URL on success |
| `x-error` | Callback URL on error |

## Actions URI Plugin

Adds x-callback-url support with standardized actions.

### Format

```text
obsidian://actions-uri/action/subaction?params
```

### Note Actions

```bash
# Get note content
obsidian://actions-uri/note/get?vault=MyVault&file=Note.md&x-success=callback://

# Create note
obsidian://actions-uri/note/create?vault=MyVault&file=Note.md&content=Hello

# Append to note
obsidian://actions-uri/note/append?vault=MyVault&file=Note.md&content=Appended

# Prepend to note
obsidian://actions-uri/note/prepend?vault=MyVault&file=Note.md&content=Prepended

# Search and replace
obsidian://actions-uri/note/search-replace?vault=MyVault&file=Note.md&search=old&replace=new
```

### Daily Note Actions

```bash
# Get today's note
obsidian://actions-uri/daily-note/get-current?vault=MyVault&x-success=callback://

# Get specific date
obsidian://actions-uri/daily-note/get?vault=MyVault&date=2024-01-15

# Append to daily note
obsidian://actions-uri/daily-note/append?vault=MyVault&content=Added%20item
```

### Navigation Actions

```bash
# Open file
obsidian://actions-uri/open?vault=MyVault&file=Note.md

# Open in new tab
obsidian://actions-uri/open/new-tab?vault=MyVault&file=Note.md

# Open in split
obsidian://actions-uri/open/split?vault=MyVault&file=Note.md
```

## URL Encoding

Special characters must be URL-encoded:

| Character | Encoded |
|-----------|---------|
| Space | `%20` or `+` |
| `/` | `%2F` |
| `#` | `%23` |
| `&` | `%26` |
| `=` | `%3D` |
| `?` | `%3F` |
| `%` | `%25` |
| `[` | `%5B` |
| `]` | `%5D` |
| `\|` | `%7C` |
| Newline | `%0A` |

### Encoding Examples

```bash
# File with spaces
obsidian://open?vault=My%20Vault&file=My%20Note

# Content with newlines
obsidian://new?vault=MyVault&name=Note&content=Line%201%0ALine%202

# Heading with special chars
obsidian://adv-uri?vault=MyVault&filepath=Note.md&heading=Section%20%231
```

## Shell Integration

### macOS

```bash
# Open URI
open "obsidian://open?vault=MyVault"

# From AppleScript
osascript -e 'open location "obsidian://open?vault=MyVault"'
```

### Linux

```bash
# Open URI
xdg-open "obsidian://open?vault=MyVault"

# Or with gio
gio open "obsidian://open?vault=MyVault"
```

### Windows

```powershell
# Open URI
Start-Process "obsidian://open?vault=MyVault"

# Or via cmd
start "" "obsidian://open?vault=MyVault"
```

## Integration Examples

### Alfred Workflow

```bash
# Create quick capture note
obsidian://new?vault=MyVault&name=Inbox/{date}&content={query}&append=true
```

### iOS Shortcuts

```text
URL: obsidian://adv-uri?vault=MyVault&daily=true&data=[Shortcut Input]&mode=append
```

### Raycast Extension

```bash
# Open daily note
obsidian://adv-uri?vault=MyVault&daily=true
```

### Keyboard Maestro

```applescript
do shell script "open 'obsidian://adv-uri?vault=MyVault&daily=true&clipboard=true&mode=append'"
```

## Common Use Cases

### Quick Capture

```bash
# Append clipboard to inbox
obsidian://adv-uri?vault=MyVault&filepath=Inbox.md&clipboard=true&mode=append
```

### Daily Journal Entry

```bash
# Add timestamped entry to daily note
obsidian://adv-uri?vault=MyVault&daily=true&data=%0A##%20$(date +%H:%M)%0A{input}&mode=append
```

### Project Quick Access

```bash
# Open project note and split with tasks
obsidian://adv-uri?vault=Work&filepath=Projects/CurrentProject.md&commandid=workspace:split-vertical
```

### Meeting Notes

```bash
# Create meeting note from template
obsidian://new?vault=Work&name=Meetings/$(date +%Y-%m-%d)-Meeting&template=Templates/Meeting
```
