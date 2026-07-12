# Obsidian Plugin Development Reference

Complete guide for creating Obsidian plugins using TypeScript.

## Project Setup

### Quick Start

```bash
# Clone sample plugin
git clone https://github.com/obsidianmd/obsidian-sample-plugin.git my-plugin
cd my-plugin

# Install dependencies
npm install

# Build plugin
npm run build

# Development with hot reload
npm run dev
```

### Project Structure

```text
my-plugin/
├── src/
│   └── main.ts            # Plugin entry point
├── styles.css              # Optional CSS styles
├── manifest.json           # Plugin metadata
├── package.json            # npm configuration
├── tsconfig.json           # TypeScript configuration
├── esbuild.config.mjs      # Build configuration
├── versions.json           # Version compatibility
└── .gitignore
```

### manifest.json

```json
{
  "id": "my-plugin",
  "name": "My Plugin",
  "version": "1.0.0",
  "minAppVersion": "1.0.0",
  "description": "Description of what the plugin does",
  "author": "Your Name",
  "authorUrl": "https://github.com/username",
  "fundingUrl": "https://github.com/sponsors/username",
  "isDesktopOnly": false
}
```

### versions.json

Maps plugin versions to minimum Obsidian versions:

```json
{
  "1.0.0": "1.0.0",
  "1.1.0": "1.2.0",
  "2.0.0": "1.4.0"
}
```

### package.json Scripts

```json
{
  "scripts": {
    "dev": "node esbuild.config.mjs",
    "build": "tsc -noEmit -skipLibCheck && node esbuild.config.mjs production",
    "version": "node version-bump.mjs && git add manifest.json versions.json"
  }
}
```

## Plugin Class

### Basic Structure

```typescript
import { Plugin, Notice } from 'obsidian';

export default class MyPlugin extends Plugin {
  settings: MyPluginSettings;

  async onload() {
    // Called when plugin is enabled
    await this.loadSettings();
    this.addSettingTab(new MySettingTab(this.app, this));
  }

  onunload() {
    // Called when plugin is disabled
    // Cleanup is mostly automatic
  }

  async loadSettings() {
    this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
  }

  async saveSettings() {
    await this.saveData(this.settings);
  }
}
```

### Lifecycle Hooks

```typescript
export default class MyPlugin extends Plugin {
  // Called when plugin loads
  async onload() {
    console.log('Plugin loading');

    // Safe to access this.app here
    // Register commands, views, events
  }

  // Called when plugin unloads
  onunload() {
    console.log('Plugin unloading');

    // Automatic cleanup for:
    // - Registered events
    // - Added commands
    // - Added views
    // - Child components
  }

  // Called when vault layout is ready
  onLayoutReady() {
    // Called after workspace is fully initialized
    // Safe to access workspace leaves
  }

  // Called when external settings change
  async onExternalSettingsChange() {
    await this.loadSettings();
  }
}
```

## Commands

### Basic Command

```typescript
this.addCommand({
  id: 'my-command',
  name: 'My Command',
  callback: () => {
    new Notice('Command executed!');
  }
});
```

### Editor Command

```typescript
this.addCommand({
  id: 'insert-timestamp',
  name: 'Insert Timestamp',
  editorCallback: (editor: Editor, view: MarkdownView) => {
    const timestamp = new Date().toISOString();
    editor.replaceSelection(timestamp);
  }
});
```

### Conditional Command

```typescript
this.addCommand({
  id: 'conditional-command',
  name: 'Conditional Command',
  checkCallback: (checking: boolean) => {
    const activeView = this.app.workspace.getActiveViewOfType(MarkdownView);
    if (activeView) {
      if (!checking) {
        // Execute the command
        new Notice('Markdown view is active');
      }
      return true; // Command is available
    }
    return false; // Command is not available
  }
});
```

### Command with Hotkey

```typescript
this.addCommand({
  id: 'my-hotkey-command',
  name: 'My Hotkey Command',
  hotkeys: [
    { modifiers: ['Mod', 'Shift'], key: 'k' }
  ],
  callback: () => {
    new Notice('Hotkey pressed!');
  }
});
```

## Events

### Workspace Events

```typescript
// File opened
this.registerEvent(
  this.app.workspace.on('file-open', (file: TFile | null) => {
    if (file) {
      console.log('Opened:', file.path);
    }
  })
);

// Active leaf changed
this.registerEvent(
  this.app.workspace.on('active-leaf-change', (leaf: WorkspaceLeaf | null) => {
    console.log('Active leaf changed');
  })
);

// Layout changed
this.registerEvent(
  this.app.workspace.on('layout-change', () => {
    console.log('Layout changed');
  })
);

// Editor changed
this.registerEvent(
  this.app.workspace.on('editor-change',
    (editor: Editor, info: MarkdownView) => {
      console.log('Editor content changed');
    })
);
```

### Vault Events

```typescript
// File created
this.registerEvent(
  this.app.vault.on('create', (file: TAbstractFile) => {
    if (file instanceof TFile) {
      console.log('File created:', file.path);
    }
  })
);

// File modified
this.registerEvent(
  this.app.vault.on('modify', (file: TAbstractFile) => {
    console.log('File modified:', file.path);
  })
);

// File deleted
this.registerEvent(
  this.app.vault.on('delete', (file: TAbstractFile) => {
    console.log('File deleted:', file.path);
  })
);

// File renamed
this.registerEvent(
  this.app.vault.on('rename', (file: TAbstractFile, oldPath: string) => {
    console.log('File renamed from', oldPath, 'to', file.path);
  })
);
```

### Metadata Events

```typescript
// Metadata cache resolved
this.registerEvent(
  this.app.metadataCache.on('resolved', () => {
    console.log('Metadata cache resolved');
  })
);

// File metadata changed
this.registerEvent(
  this.app.metadataCache.on('changed', (file: TFile) => {
    console.log('Metadata changed:', file.path);
  })
);
```

## Views

### Custom View

```typescript
import { ItemView, WorkspaceLeaf } from 'obsidian';

export const VIEW_TYPE_EXAMPLE = 'example-view';

export class ExampleView extends ItemView {
  constructor(leaf: WorkspaceLeaf) {
    super(leaf);
  }

  getViewType(): string {
    return VIEW_TYPE_EXAMPLE;
  }

  getDisplayText(): string {
    return 'Example View';
  }

  getIcon(): string {
    return 'dice';
  }

  async onOpen() {
    const container = this.containerEl.children[1];
    container.empty();
    container.createEl('h4', { text: 'Example View' });
    container.createEl('p', { text: 'Content goes here' });
  }

  async onClose() {
    // Cleanup
  }
}
```

### Register View

```typescript
async onload() {
  this.registerView(
    VIEW_TYPE_EXAMPLE,
    (leaf) => new ExampleView(leaf)
  );

  // Add ribbon icon
  this.addRibbonIcon('dice', 'Open Example View', () => {
    this.activateView();
  });
}

async activateView() {
  const { workspace } = this.app;

  let leaf = workspace.getLeavesOfType(VIEW_TYPE_EXAMPLE)[0];

  if (!leaf) {
    leaf = workspace.getRightLeaf(false);
    await leaf.setViewState({
      type: VIEW_TYPE_EXAMPLE,
      active: true,
    });
  }

  workspace.revealLeaf(leaf);
}
```

## Settings

### Settings Interface

```typescript
interface MyPluginSettings {
  mySetting: string;
  enableFeature: boolean;
  itemCount: number;
}

const DEFAULT_SETTINGS: MyPluginSettings = {
  mySetting: 'default',
  enableFeature: true,
  itemCount: 5
};
```

### Settings Tab

```typescript
import { App, PluginSettingTab, Setting } from 'obsidian';

class MySettingTab extends PluginSettingTab {
  plugin: MyPlugin;

  constructor(app: App, plugin: MyPlugin) {
    super(app, plugin);
    this.plugin = plugin;
  }

  display(): void {
    const { containerEl } = this;
    containerEl.empty();

    containerEl.createEl('h2', { text: 'My Plugin Settings' });

    new Setting(containerEl)
      .setName('Text Setting')
      .setDesc('Enter a value')
      .addText(text => text
        .setPlaceholder('Enter value')
        .setValue(this.plugin.settings.mySetting)
        .onChange(async (value) => {
          this.plugin.settings.mySetting = value;
          await this.plugin.saveSettings();
        }));

    new Setting(containerEl)
      .setName('Toggle Setting')
      .setDesc('Enable or disable feature')
      .addToggle(toggle => toggle
        .setValue(this.plugin.settings.enableFeature)
        .onChange(async (value) => {
          this.plugin.settings.enableFeature = value;
          await this.plugin.saveSettings();
        }));

    new Setting(containerEl)
      .setName('Number Setting')
      .setDesc('Set a number')
      .addSlider(slider => slider
        .setLimits(1, 10, 1)
        .setValue(this.plugin.settings.itemCount)
        .setDynamicTooltip()
        .onChange(async (value) => {
          this.plugin.settings.itemCount = value;
          await this.plugin.saveSettings();
        }));

    new Setting(containerEl)
      .setName('Dropdown Setting')
      .addDropdown(dropdown => dropdown
        .addOption('option1', 'Option 1')
        .addOption('option2', 'Option 2')
        .setValue(this.plugin.settings.mySetting)
        .onChange(async (value) => {
          this.plugin.settings.mySetting = value;
          await this.plugin.saveSettings();
        }));
  }
}
```

## Modals

### Basic Modal

```typescript
import { Modal, App } from 'obsidian';

class MyModal extends Modal {
  result: string;
  onSubmit: (result: string) => void;

  constructor(app: App, onSubmit: (result: string) => void) {
    super(app);
    this.onSubmit = onSubmit;
  }

  onOpen() {
    const { contentEl } = this;
    contentEl.createEl('h2', { text: 'Modal Title' });

    new Setting(contentEl)
      .setName('Input')
      .addText((text) => text
        .onChange((value) => {
          this.result = value;
        }));

    new Setting(contentEl)
      .addButton((btn) => btn
        .setButtonText('Submit')
        .setCta()
        .onClick(() => {
          this.close();
          this.onSubmit(this.result);
        }));
  }

  onClose() {
    const { contentEl } = this;
    contentEl.empty();
  }
}
```

### Suggest Modal

```typescript
import { SuggestModal, App } from 'obsidian';

interface Book {
  title: string;
  author: string;
}

class BookSuggestModal extends SuggestModal<Book> {
  books: Book[];
  onChoose: (book: Book) => void;

  constructor(app: App, books: Book[], onChoose: (book: Book) => void) {
    super(app);
    this.books = books;
    this.onChoose = onChoose;
  }

  getSuggestions(query: string): Book[] {
    return this.books.filter((book) =>
      book.title.toLowerCase().includes(query.toLowerCase())
    );
  }

  renderSuggestion(book: Book, el: HTMLElement) {
    el.createEl('div', { text: book.title });
    el.createEl('small', { text: book.author });
  }

  onChooseSuggestion(book: Book, evt: MouseEvent | KeyboardEvent) {
    this.onChoose(book);
  }
}
```

### Fuzzy Suggest Modal

```typescript
import { FuzzySuggestModal, App, TFile } from 'obsidian';

class FileSuggestModal extends FuzzySuggestModal<TFile> {
  files: TFile[];
  onChoose: (file: TFile) => void;

  constructor(app: App, onChoose: (file: TFile) => void) {
    super(app);
    this.files = app.vault.getMarkdownFiles();
    this.onChoose = onChoose;
  }

  getItems(): TFile[] {
    return this.files;
  }

  getItemText(file: TFile): string {
    return file.path;
  }

  onChooseItem(file: TFile, evt: MouseEvent | KeyboardEvent) {
    this.onChoose(file);
  }
}
```

## File Operations

### Reading Files

```typescript
// Get file by path
const file = this.app.vault.getAbstractFileByPath('Notes/MyNote.md');
if (file instanceof TFile) {
  const content = await this.app.vault.read(file);
  console.log(content);
}

// Get all markdown files
const files = this.app.vault.getMarkdownFiles();

// Get cached content
const file = this.app.vault.getAbstractFileByPath('Notes/MyNote.md');
if (file instanceof TFile) {
  const cache = this.app.vault.cachedRead(file);
}
```

### Writing Files

```typescript
// Create file
await this.app.vault.create('Notes/NewNote.md', 'Content here');

// Modify file
const file = this.app.vault.getAbstractFileByPath('Notes/MyNote.md');
if (file instanceof TFile) {
  await this.app.vault.modify(file, 'New content');
}

// Append to file
const file = this.app.vault.getAbstractFileByPath('Notes/MyNote.md');
if (file instanceof TFile) {
  const content = await this.app.vault.read(file);
  await this.app.vault.modify(file, content + '\nAppended text');
}
```

### File Management

```typescript
// Rename file
const file = this.app.vault.getAbstractFileByPath('Notes/OldName.md');
if (file) {
  await this.app.fileManager.renameFile(file, 'Notes/NewName.md');
}

// Delete file
const file = this.app.vault.getAbstractFileByPath('Notes/ToDelete.md');
if (file) {
  await this.app.vault.delete(file);
}

// Move file
const file = this.app.vault.getAbstractFileByPath('Notes/MyNote.md');
if (file) {
  await this.app.fileManager.renameFile(file, 'Archive/MyNote.md');
}
```

### Folder Operations

```typescript
// Create folder
await this.app.vault.createFolder('NewFolder');

// List folder contents
const folder = this.app.vault.getAbstractFileByPath('Notes');
if (folder instanceof TFolder) {
  for (const child of folder.children) {
    console.log(child.path);
  }
}
```

## Frontmatter

### Process Frontmatter

```typescript
const file = this.app.vault.getAbstractFileByPath('Notes/MyNote.md');
if (file instanceof TFile) {
  await this.app.fileManager.processFrontMatter(file, (frontmatter) => {
    frontmatter.status = 'done';
    frontmatter.updated = new Date().toISOString();
    // Return value is ignored, modify in place
  });
}
```

### Read Frontmatter from Cache

```typescript
const file = this.app.vault.getAbstractFileByPath('Notes/MyNote.md');
if (file instanceof TFile) {
  const cache = this.app.metadataCache.getFileCache(file);
  if (cache?.frontmatter) {
    console.log(cache.frontmatter.title);
    console.log(cache.frontmatter.tags);
  }
}
```

## Editor Operations

### Get Editor

```typescript
const activeView = this.app.workspace.getActiveViewOfType(MarkdownView);
if (activeView) {
  const editor = activeView.editor;
  // Use editor
}
```

### Editor Methods

```typescript
// Get content
const content = editor.getValue();
const line = editor.getLine(0);
const selection = editor.getSelection();

// Set content
editor.setValue('New content');
editor.replaceSelection('Inserted text');
editor.replaceRange('text', { line: 0, ch: 0 }, { line: 0, ch: 5 });

// Cursor
const cursor = editor.getCursor();
editor.setCursor({ line: 5, ch: 0 });

// Selection
editor.setSelection({ line: 0, ch: 0 }, { line: 2, ch: 10 });

// Line operations
const lineCount = editor.lineCount();
editor.setLine(0, 'New line content');

// Transactions
editor.transaction({
  changes: [
    { from: { line: 0, ch: 0 }, to: { line: 0, ch: 5 }, text: 'new' }
  ]
});
```

## CSS Styling

### styles.css

```css
/* Plugin container */
.my-plugin-container {
  padding: 10px;
}

/* Theme-aware colors */
.my-plugin-text {
  color: var(--text-normal);
  background-color: var(--background-primary);
}

/* Interactive elements */
.my-plugin-button {
  background-color: var(--interactive-accent);
  color: var(--text-on-accent);
}

.my-plugin-button:hover {
  background-color: var(--interactive-accent-hover);
}

/* Obsidian CSS variables include:
 * --text-normal, --text-muted, --text-faint
 * --background-primary, --background-secondary
 * --interactive-accent, --interactive-accent-hover
 * --text-on-accent
 * --border-width, --radius-s, --radius-m
 */
```

### Register Styles

Styles in `styles.css` are automatically loaded. For dynamic styles:

```typescript
// Add dynamic styles
this.registerMarkdownPostProcessor((el, ctx) => {
  el.querySelectorAll('.my-class').forEach((elem) => {
    elem.addClass('processed');
  });
});
```

## Best Practices

### Performance

```typescript
// Debounce frequent operations
import { debounce } from 'obsidian';

this.registerEvent(
  this.app.workspace.on('editor-change', debounce(
    (editor: Editor) => {
      // Process change
    },
    300,
    true
  ))
);

// Use cached reads when possible
const content = await this.app.vault.cachedRead(file);

// Batch DOM operations
const fragment = document.createDocumentFragment();
items.forEach(item => {
  fragment.appendChild(createEl('div', { text: item }));
});
container.appendChild(fragment);
```

### Error Handling

```typescript
try {
  await this.app.vault.create('path/to/file.md', 'content');
} catch (error) {
  new Notice(`Failed to create file: ${error.message}`);
  console.error('Plugin error:', error);
}
```

### Cleanup

```typescript
// Use registerEvent for automatic cleanup
this.registerEvent(
  this.app.workspace.on('file-open', handler)
);

// Use register for custom cleanup
this.register(() => {
  // Custom cleanup code
  externalService.disconnect();
});

// Use addChild for component cleanup
this.addChild(childComponent);
```

## Testing

### Development Vault

1. Create a separate vault for development
2. Enable "Safe mode" off in Settings > Community plugins
3. Install hot-reload plugin for faster iteration

### BRAT Plugin

Use BRAT (Beta Reviewers Auto-update Tester) for beta testing:

1. Install BRAT plugin
2. Add your plugin's GitHub repo
3. BRAT will install and update from GitHub

### Console Debugging

```typescript
// Use Obsidian's developer console
// Ctrl+Shift+I (Cmd+Option+I on Mac)

console.log('Debug:', data);
console.table(arrayData);
console.group('Group');
console.log('Nested');
console.groupEnd();
```

## Publishing

### Submission Checklist

1. Update manifest.json version
2. Update versions.json
3. Create GitHub release with tag matching version
4. Include main.js, manifest.json, styles.css (if any) in release
5. Submit PR to obsidian-releases repo

### Release Files

```bash
# Files required in GitHub release
main.js
manifest.json
styles.css  # Optional
```

### Automated Release

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    tags:
      - '*'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18
      - run: npm install
      - run: npm run build
      - uses: softprops/action-gh-release@v1
        with:
          files: |
            main.js
            manifest.json
            styles.css
```
