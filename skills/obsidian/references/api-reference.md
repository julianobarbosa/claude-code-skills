# Obsidian TypeScript API Reference

Complete reference for the Obsidian plugin API classes and interfaces.

## Core Classes

### App

Central application instance providing access to all subsystems.

```typescript
interface App {
  // Core subsystems
  keymap: Keymap;
  scope: Scope;
  workspace: Workspace;
  vault: Vault;
  metadataCache: MetadataCache;
  fileManager: FileManager;

  // UI managers
  commands: Commands;

  // Methods
  loadLocalStorage(key: string): string | null;
  saveLocalStorage(key: string, value: string | undefined): void;
}

// Access in plugin
const app = this.app;
const vault = this.app.vault;
const workspace = this.app.workspace;
```

### Vault

File system operations and event handling.

```typescript
interface Vault extends Events {
  // Properties
  configDir: string;              // Usually ".obsidian"
  adapter: DataAdapter;           // Low-level file access

  // File retrieval
  getAbstractFileByPath(path: string): TAbstractFile | null;
  getMarkdownFiles(): TFile[];
  getAllLoadedFiles(): TAbstractFile[];
  getFiles(): TFile[];

  // File operations
  create(path: string, data: string): Promise<TFile>;
  createBinary(path: string, data: ArrayBuffer): Promise<TFile>;
  createFolder(path: string): Promise<void>;
  read(file: TFile): Promise<string>;
  readBinary(file: TFile): Promise<ArrayBuffer>;
  cachedRead(file: TFile): Promise<string>;
  modify(file: TFile, data: string): Promise<void>;
  modifyBinary(file: TFile, data: ArrayBuffer): Promise<void>;
  delete(file: TAbstractFile, force?: boolean): Promise<void>;
  trash(file: TAbstractFile, system: boolean): Promise<void>;
  rename(file: TAbstractFile, newPath: string): Promise<void>;
  copy(file: TFile, newPath: string): Promise<TFile>;

  // Events
  on(name: 'create', callback: (file: TAbstractFile) => any): EventRef;
  on(name: 'modify', callback: (file: TAbstractFile) => any): EventRef;
  on(name: 'delete', callback: (file: TAbstractFile) => any): EventRef;
  on(name: 'rename', callback: (file: TAbstractFile, oldPath: string) => any): EventRef;
}
```

### Workspace

Layout and pane management.

```typescript
interface Workspace extends Events {
  // Properties
  leftSplit: WorkspaceSidedock;
  rightSplit: WorkspaceSidedock;
  leftRibbon: WorkspaceRibbon;
  rightRibbon: WorkspaceRibbon;
  activeLeaf: WorkspaceLeaf | null;

  // Leaf operations
  getLeaf(newLeaf?: boolean | PaneType): WorkspaceLeaf;
  getActiveViewOfType<T extends View>(type: Constructor<T>): T | null;
  getLeavesOfType(viewType: string): WorkspaceLeaf[];
  getLeftLeaf(split: boolean): WorkspaceLeaf;
  getRightLeaf(split: boolean): WorkspaceLeaf;
  splitActiveLeaf(direction?: SplitDirection): WorkspaceLeaf;
  createLeafInParent(parent: WorkspaceSplit, index: number): WorkspaceLeaf;

  // File operations
  openLinkText(linktext: string, sourcePath: string, newLeaf?: boolean): Promise<void>;
  getActiveFile(): TFile | null;
  activeEditor: MarkdownEditView | null;

  // Layout
  changeLayout(workspace: any): Promise<void>;
  getLayout(): any;
  requestSaveLayout(): void;

  // Events
  on(name: 'file-open',
     callback: (file: TFile | null) => any): EventRef;
  on(name: 'active-leaf-change',
     callback: (leaf: WorkspaceLeaf | null) => any): EventRef;
  on(name: 'layout-change', callback: () => any): EventRef;
  on(name: 'editor-change',
     callback: (editor: Editor, info: MarkdownView) => any): EventRef;
  on(name: 'resize', callback: () => any): EventRef;
  on(name: 'quit', callback: (tasks: Tasks) => any): EventRef;
}
```

### MetadataCache

Parsed file metadata and link resolution.

```typescript
interface MetadataCache extends Events {
  // Get metadata
  getFileCache(file: TFile): CachedMetadata | null;
  getCache(path: string): CachedMetadata | null;
  getFirstLinkpathDest(linkpath: string, sourcePath: string): TFile | null;

  // Link resolution
  resolvedLinks: Record<string, Record<string, number>>;
  unresolvedLinks: Record<string, Record<string, number>>;

  // Events
  on(name: 'changed',
     callback: (file: TFile, data: string, cache: CachedMetadata) => any
  ): EventRef;
  on(name: 'deleted',
     callback: (file: TFile, prevCache: CachedMetadata | null) => any
  ): EventRef;
  on(name: 'resolved', callback: () => any): EventRef;
}

interface CachedMetadata {
  links?: LinkCache[];
  embeds?: EmbedCache[];
  tags?: TagCache[];
  headings?: HeadingCache[];
  sections?: SectionCache[];
  listItems?: ListItemCache[];
  frontmatter?: FrontMatterCache;
  frontmatterPosition?: Pos;
  frontmatterLinks?: FrontmatterLinkCache[];
  blocks?: Record<string, BlockCache>;
}

interface LinkCache extends ReferenceCache {
  link: string;
  original: string;
}

interface HeadingCache extends CacheItem {
  heading: string;
  level: number;
}

interface TagCache extends CacheItem {
  tag: string;
}
```

### FileManager

User-safe file operations with prompts.

```typescript
interface FileManager {
  // File operations
  createNewMarkdownFile(
    folder: TFolder,
    name: string,
    content?: string
  ): Promise<TFile>;

  renameFile(file: TAbstractFile, newPath: string): Promise<void>;

  // Frontmatter
  processFrontMatter(
    file: TFile,
    fn: (frontmatter: any) => void
  ): Promise<void>;

  // Links
  generateMarkdownLink(
    file: TFile,
    sourcePath: string,
    subpath?: string,
    alias?: string
  ): string;
}
```

## File Abstractions

### TAbstractFile

Base class for files and folders.

```typescript
abstract class TAbstractFile {
  vault: Vault;
  path: string;
  name: string;
  parent: TFolder | null;
}
```

### TFile

Represents a file.

```typescript
class TFile extends TAbstractFile {
  stat: FileStats;
  basename: string;              // Name without extension
  extension: string;             // File extension
}

interface FileStats {
  ctime: number;                 // Created time
  mtime: number;                 // Modified time
  size: number;                  // Size in bytes
}
```

### TFolder

Represents a folder.

```typescript
class TFolder extends TAbstractFile {
  children: TAbstractFile[];

  isRoot(): boolean;
}
```

## Editor

### Editor Interface

Abstract editor operations (CodeMirror-agnostic).

```typescript
interface Editor {
  // Content
  getValue(): string;
  setValue(content: string): void;
  getLine(line: number): string;
  setLine(line: number, text: string): void;
  lineCount(): number;

  // Selection
  getSelection(): string;
  setSelection(anchor: EditorPosition, head?: EditorPosition): void;
  somethingSelected(): boolean;
  replaceSelection(replacement: string, origin?: string): void;
  replaceRange(
    replacement: string,
    from: EditorPosition,
    to?: EditorPosition,
    origin?: string
  ): void;

  // Cursor
  getCursor(string?: 'from' | 'to' | 'head' | 'anchor'): EditorPosition;
  setCursor(pos: EditorPosition | number, ch?: number): void;
  offsetToPos(offset: number): EditorPosition;
  posToOffset(pos: EditorPosition): number;

  // Scroll
  scrollTo(x?: number | null, y?: number | null): void;
  scrollIntoView(range: EditorRange, center?: boolean): void;

  // Transactions
  transaction(tx: EditorTransaction): void;

  // Focus
  focus(): void;
  blur(): void;
  hasFocus(): boolean;

  // Undo
  undo(): void;
  redo(): void;

  // Word at position
  wordAt(pos: EditorPosition): EditorRange | null;

  // Exec command
  exec(command: EditorCommandName): void;
}

interface EditorPosition {
  line: number;
  ch: number;
}

interface EditorRange {
  from: EditorPosition;
  to: EditorPosition;
}
```

## Views

### View

Base class for all views.

```typescript
abstract class View extends Component {
  app: App;
  icon: IconName;
  navigation: boolean;
  leaf: WorkspaceLeaf;
  containerEl: HTMLElement;

  abstract getViewType(): string;
  abstract getDisplayText(): string;
  abstract getIcon(): IconName;

  onOpen(): Promise<void>;
  onClose(): Promise<void>;

  getState(): any;
  setState(state: any, result: ViewStateResult): Promise<void>;
}
```

### ItemView

Base for custom views.

```typescript
abstract class ItemView extends View {
  contentEl: HTMLElement;

  addAction(
    icon: IconName,
    title: string,
    callback: (evt: MouseEvent) => any
  ): HTMLElement;

  onHeaderMenu(menu: Menu): void;
}
```

### MarkdownView

Markdown file view.

```typescript
class MarkdownView extends TextFileView {
  editor: Editor;
  previewMode: MarkdownPreviewView;

  getMode(): 'source' | 'preview' | 'live';
  getViewType(): 'markdown';

  showSearch(replace?: boolean): void;
}
```

### WorkspaceLeaf

Container for views.

```typescript
class WorkspaceLeaf extends Component {
  view: View;
  parent: WorkspaceSplit;

  // Navigation
  openFile(file: TFile, openState?: OpenViewState): Promise<void>;
  open(view: View): Promise<View>;

  // State
  getViewState(): ViewState;
  setViewState(viewState: ViewState, eState?: any): Promise<void>;

  // Layout
  detach(): void;
  setGroupMember(other: WorkspaceLeaf): void;
  setGroup(group: string): void;

  // Tab
  getDisplayText(): string;
  getIcon(): IconName;

  // History
  getHistoryState(): any;
  setHistoryState(state: any): void;

  // Pin
  setPinned(pinned: boolean): void;
  togglePinned(): void;
}
```

## UI Components

### Modal

Dialog base class.

```typescript
abstract class Modal {
  app: App;
  scope: Scope;
  containerEl: HTMLElement;
  modalEl: HTMLElement;
  titleEl: HTMLElement;
  contentEl: HTMLElement;

  open(): void;
  close(): void;

  onOpen(): void;
  onClose(): void;
}
```

### SuggestModal

Modal with search suggestions.

```typescript
abstract class SuggestModal<T> extends Modal {
  inputEl: HTMLInputElement;
  resultContainerEl: HTMLElement;
  emptyStateText: string;
  limit: number;

  abstract getSuggestions(query: string): T[] | Promise<T[]>;
  abstract renderSuggestion(item: T, el: HTMLElement): void;
  abstract onChooseSuggestion(item: T, evt: MouseEvent | KeyboardEvent): void;

  selectSuggestion(value: T, evt: MouseEvent | KeyboardEvent): void;
}
```

### FuzzySuggestModal

Modal with fuzzy search.

```typescript
abstract class FuzzySuggestModal<T> extends SuggestModal<FuzzyMatch<T>> {
  abstract getItems(): T[];
  abstract getItemText(item: T): string;
  abstract onChooseItem(item: T, evt: MouseEvent | KeyboardEvent): void;
}
```

### Setting

Settings UI builder.

```typescript
class Setting {
  settingEl: HTMLElement;
  infoEl: HTMLElement;
  nameEl: HTMLElement;
  descEl: HTMLElement;
  controlEl: HTMLElement;

  constructor(containerEl: HTMLElement);

  setName(name: string | DocumentFragment): this;
  setDesc(desc: string | DocumentFragment): this;
  setClass(cls: string): this;
  setTooltip(tooltip: string, options?: TooltipOptions): this;
  setHeading(): this;
  setDisabled(disabled: boolean): this;

  // Controls
  addButton(cb: (component: ButtonComponent) => any): this;
  addExtraButton(cb: (component: ExtraButtonComponent) => any): this;
  addToggle(cb: (component: ToggleComponent) => any): this;
  addText(cb: (component: TextComponent) => any): this;
  addTextArea(cb: (component: TextAreaComponent) => any): this;
  addMomentFormat(cb: (component: MomentFormatComponent) => any): this;
  addDropdown(cb: (component: DropdownComponent) => any): this;
  addSlider(cb: (component: SliderComponent) => any): this;
  addSearch(cb: (component: SearchComponent) => any): this;
  addColorPicker(cb: (component: ColorComponent) => any): this;
}
```

### Menu

Context menu builder.

```typescript
class Menu extends Component {
  addItem(cb: (item: MenuItem) => any): this;
  addSeparator(): this;
  showAtMouseEvent(event: MouseEvent): this;
  showAtPosition(position: MenuPositionDef, doc?: Document): this;
  hide(): this;
  onHide(callback: () => any): void;
}

class MenuItem {
  setTitle(title: string | DocumentFragment): this;
  setIcon(icon: IconName | null): this;
  setChecked(checked: boolean | null): this;
  setDisabled(disabled: boolean): this;
  setSection(section: string): this;
  setIsLabel(isLabel: boolean): this;
  onClick(callback: (evt: MouseEvent | KeyboardEvent) => any): this;
  setSubmenu(): Menu;
}
```

## Component Lifecycle

### Component

Base class with lifecycle management.

```typescript
class Component {
  load(): void;
  onload(): void;

  unload(): void;
  onunload(): void;

  // Child components
  addChild<T extends Component>(component: T): T;
  removeChild<T extends Component>(component: T): T;

  // Event registration
  registerEvent(eventRef: EventRef): void;

  // Interval/timeout
  registerInterval(id: number): number;

  // DOM events
  registerDomEvent<K extends keyof WindowEventMap>(
    el: Window,
    type: K,
    callback: (this: HTMLElement, ev: WindowEventMap[K]) => any,
    options?: boolean | AddEventListenerOptions
  ): void;

  registerDomEvent<K extends keyof DocumentEventMap>(
    el: Document,
    type: K,
    callback: (this: HTMLElement, ev: DocumentEventMap[K]) => any,
    options?: boolean | AddEventListenerOptions
  ): void;

  registerDomEvent<K extends keyof HTMLElementEventMap>(
    el: HTMLElement,
    type: K,
    callback: (this: HTMLElement, ev: HTMLElementEventMap[K]) => any,
    options?: boolean | AddEventListenerOptions
  ): void;

  // Cleanup callback
  register(cb: () => any): void;
}
```

### Plugin

Plugin base class.

```typescript
abstract class Plugin extends Component {
  app: App;
  manifest: PluginManifest;

  // Data persistence
  loadData(): Promise<any>;
  saveData(data: any): Promise<void>;

  // Commands
  addCommand(command: Command): Command;

  // Ribbon
  addRibbonIcon(
    icon: IconName, title: string,
    callback: (evt: MouseEvent) => any
  ): HTMLElement;

  // Status bar
  addStatusBarItem(): HTMLElement;

  // Settings tab
  addSettingTab(settingTab: PluginSettingTab): void;

  // Views
  registerView(type: string, viewCreator: ViewCreator): void;

  // Extensions
  registerExtensions(extensions: string[], viewType: string): void;

  // Markdown processors
  registerMarkdownPostProcessor(
    postProcessor: MarkdownPostProcessor,
    sortOrder?: number
  ): MarkdownPostProcessor;

  registerMarkdownCodeBlockProcessor(
    language: string,
    handler: (
      source: string, el: HTMLElement,
      ctx: MarkdownPostProcessorContext
    ) => Promise<any> | void,
    sortOrder?: number
  ): MarkdownPostProcessor;

  // Events
  registerObsidianProtocolHandler(
    action: string,
    handler: ObsidianProtocolHandler
  ): void;

  registerEditorExtension(extension: Extension): void;

  registerEditorSuggest(editorSuggest: EditorSuggest<any>): void;

  registerHoverLinkSource(id: string, info: HoverLinkSource): void;
}
```

## Command Interface

```typescript
interface Command {
  id: string;
  name: string;
  icon?: IconName;

  // Callbacks (use one)
  callback?: () => any;
  checkCallback?: (checking: boolean) => boolean | void;
  editorCallback?: (
    editor: Editor, ctx: MarkdownView | MarkdownFileInfo
  ) => any;
  editorCheckCallback?: (
    checking: boolean, editor: Editor,
    ctx: MarkdownView | MarkdownFileInfo
  ) => boolean | void;

  // Hotkeys
  hotkeys?: Hotkey[];

  // Flags
  mobileOnly?: boolean;
  repeatable?: boolean;
}

interface Hotkey {
  modifiers: Modifier[];  // 'Mod' | 'Ctrl' | 'Meta' | 'Shift' | 'Alt'
  key: string;
}
```

## Utility Functions

### Notice

Display notifications.

```typescript
class Notice {
  constructor(message: string | DocumentFragment, timeout?: number);
  setMessage(message: string | DocumentFragment): this;
  hide(): void;
}

// Usage
new Notice('Operation complete!');
new Notice('Error occurred', 5000);  // 5 second timeout
```

### requestUrl

HTTP requests.

```typescript
function requestUrl(request: RequestUrlParam | string): Promise<RequestUrlResponse>;

interface RequestUrlParam {
  url: string;
  method?: string;
  contentType?: string;
  body?: string | ArrayBuffer;
  headers?: Record<string, string>;
}

interface RequestUrlResponse {
  status: number;
  headers: Record<string, string>;
  arrayBuffer: ArrayBuffer;
  json: any;
  text: string;
}
```

### debounce

Debounce function calls.

```typescript
function debounce<T extends unknown[]>(
  cb: (...args: T) => any,
  timeout?: number,
  resetTimer?: boolean
): (...args: T) => void;

// Usage
const debouncedSave = debounce(saveData, 300);
```

### normalizePath

Normalize file paths.

```typescript
function normalizePath(path: string): string;

// Usage
const path = normalizePath('folder//file.md');
// Returns: 'folder/file.md'
```

### moment

Date/time handling (bundled with Obsidian).

```typescript
// Access global moment
declare const moment: typeof import('moment');

// Usage
const now = moment();
const formatted = moment().format('YYYY-MM-DD');
```

## Type Definitions

### Icons

```typescript
type IconName =
  | 'lucide-file'
  | 'lucide-folder'
  | 'lucide-search'
  | 'lucide-settings'
  | 'lucide-star'
  // ... many more Lucide icons
  ;
```

### Events

```typescript
interface Events {
  on(name: string, callback: (...data: any) => any, ctx?: any): EventRef;
  off(name: string, callback: (...data: any) => any): void;
  offref(ref: EventRef): void;
  trigger(name: string, ...data: any[]): void;
  tryTrigger(evt: EventRef, args: any[]): void;
}
```

## Common Patterns

### Getting Active File

```typescript
const activeFile = this.app.workspace.getActiveFile();
if (activeFile) {
  const content = await this.app.vault.read(activeFile);
}
```

### Getting Active Editor

```typescript
const view = this.app.workspace.getActiveViewOfType(MarkdownView);
if (view) {
  const editor = view.editor;
  const selection = editor.getSelection();
}
```

### Processing All Files

```typescript
for (const file of this.app.vault.getMarkdownFiles()) {
  const cache = this.app.metadataCache.getFileCache(file);
  if (cache?.frontmatter?.status === 'active') {
    // Process file
  }
}
```

### Registering Events Safely

```typescript
// Always use registerEvent for automatic cleanup
this.registerEvent(
  this.app.workspace.on('file-open', (file) => {
    // Handler
  })
);
```

### Creating Modals

```typescript
const modal = new MyModal(this.app, (result) => {
  console.log('User submitted:', result);
});
modal.open();
```
