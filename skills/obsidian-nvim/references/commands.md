# obsidian.nvim Commands Reference

Complete reference for all obsidian.nvim commands.

## Command Entry Point

The main command is `:Obsidian` with subcommands:

```vim
:Obsidian                    " Open command picker
:Obsidian <Tab>              " Tab-complete subcommands
:Obsidian <subcommand>       " Execute specific subcommand
```

## Workspace Commands

### workspace

Switch between configured workspaces or check current workspace.

```vim
:Obsidian workspace          " Show current workspace
:Obsidian workspace personal " Switch to 'personal' workspace
:Obsidian workspace work     " Switch to 'work' workspace
```

## Daily Notes Commands

### today

Open or create today's daily note.

```vim
:Obsidian today              " Open today's daily note
:Obsidian today -1           " Open yesterday's daily note
:Obsidian today 1            " Open tomorrow's daily note
:Obsidian today -7           " Open note from 7 days ago
```

**Note:** Unlike `yesterday` and `tomorrow`, this does not skip weekends.

### yesterday

Open the daily note for the previous working day (skips weekends by default).

```vim
:Obsidian yesterday
```

### tomorrow

Open the daily note for the next working day (skips weekends by default).

```vim
:Obsidian tomorrow
```

### dailies

Browse daily notes with a picker.

```vim
:Obsidian dailies            " List all daily notes
:Obsidian dailies -7 0       " List notes from past week to today
:Obsidian dailies -2 1       " List from 2 days ago to tomorrow
```

## Note Creation Commands

### new

Create a new note with optional title.

```vim
:Obsidian new                " Create note (prompts for title)
:Obsidian new My New Note    " Create note with title
```

### new_from_template

Create a new note from a template.

```vim
:Obsidian new_from_template                    " Select both from picker
:Obsidian new_from_template "My Note"          " Note title, select template
:Obsidian new_from_template "My Note" meeting  " Specify both
```

## Navigation Commands

### quick_switch

Fuzzy find and switch to another note.

```vim
:Obsidian quick_switch
```

### follow_link

Follow a reference or link under the cursor.

```vim
:Obsidian follow_link                " Open in current window
:Obsidian follow_link vsplit         " Open in vertical split
:Obsidian follow_link hsplit         " Open in horizontal split
:Obsidian follow_link vsplit_force   " Force vertical split (new window)
:Obsidian follow_link hsplit_force   " Force horizontal split (new window)
```

### open

Open a note in the Obsidian app.

```vim
:Obsidian open               " Open current note
:Obsidian open query         " Open note matching query
```

## Search Commands

### search

Search for notes using ripgrep.

```vim
:Obsidian search             " Open search picker
:Obsidian search query       " Search for 'query'
```

### tags

Find notes with specific tags.

```vim
:Obsidian tags               " Show all tags
:Obsidian tags daily-notes   " Find notes with #daily-notes
:Obsidian tags work project  " Find notes with #work or #project
```

## Note Information Commands

### backlinks

Show references to the current note.

```vim
:Obsidian backlinks
```

Alternative: `grr` or `vim.lsp.buf.references()` for quickfix list.

### links

List all links in the current note.

```vim
:Obsidian links
```

### toc

Show table of contents for current note.

```vim
:Obsidian toc
```

## Template Commands

### template

Insert a template at cursor position.

```vim
:Obsidian template           " Select template from picker
:Obsidian template daily     " Insert specific template
```

## Link Commands (Normal Mode)

### rename

Rename current note and update all backlinks.

```vim
:Obsidian rename             " Prompt for new name
:Obsidian rename "New Name"  " Rename to specific name
```

**Important:**
- Runs `:wa` before renaming
- Loads all affected notes into buffer list
- Run `:wa` again after renaming

Alternative: `grn` or `vim.lsp.buf.rename()`

## Link Commands (Visual Mode)

### link

Link selected text to an existing note.

```vim
:'<,'>Obsidian link          " Search for note
:'<,'>Obsidian link query    " Link to note matching query
```

### link_new

Create a new note and link the selected text to it.

```vim
:'<,'>Obsidian link_new             " Use selection as title
:'<,'>Obsidian link_new "New Title" " Specify title
```

### extract_note

Extract selected text to a new note and replace with link.

```vim
:'<,'>Obsidian extract_note             " Prompt for title
:'<,'>Obsidian extract_note "Extracted" " Specify title
```

## Checkbox Commands

### toggle_checkbox

Cycle through checkbox states.

```vim
:Obsidian toggle_checkbox
```

Cycles through: `[ ]` -> `[x]` -> `[~]` -> `[!]` -> `[>]` -> `[ ]`

Supports range selection for multiple lines.

## Image Commands

### paste_img

Paste an image from clipboard into the note.

```vim
:Obsidian paste_img          " Auto-generate filename
:Obsidian paste_img myimage  " Specify filename
```

**Requirements:**
- macOS: `pngpaste` (`brew install pngpaste`)
- Linux: `xclip` (X11) or `wl-clipboard` (Wayland)

## Utility Commands

### check

Check for issues in your vault.

```vim
:Obsidian check
```

Also available via `:checkhealth obsidian`

## Legacy Commands

If `legacy_commands = true` is set, these commands are also available:

| Legacy Command | New Command |
|----------------|-------------|
| `:ObsidianToday` | `:Obsidian today` |
| `:ObsidianYesterday` | `:Obsidian yesterday` |
| `:ObsidianTomorrow` | `:Obsidian tomorrow` |
| `:ObsidianDailies` | `:Obsidian dailies` |
| `:ObsidianNew` | `:Obsidian new` |
| `:ObsidianOpen` | `:Obsidian open` |
| `:ObsidianBacklinks` | `:Obsidian backlinks` |
| `:ObsidianTags` | `:Obsidian tags` |
| `:ObsidianSearch` | `:Obsidian search` |
| `:ObsidianTemplate` | `:Obsidian template` |
| `:ObsidianNewFromTemplate` | `:Obsidian new_from_template` |
| `:ObsidianQuickSwitch` | `:Obsidian quick_switch` |
| `:ObsidianLinkNew` | `:Obsidian link_new` |
| `:ObsidianLink` | `:Obsidian link` |
| `:ObsidianLinks` | `:Obsidian links` |
| `:ObsidianFollowLink` | `:Obsidian follow_link` |
| `:ObsidianToggleCheckbox` | `:Obsidian toggle_checkbox` |
| `:ObsidianWorkspace` | `:Obsidian workspace` |
| `:ObsidianRename` | `:Obsidian rename` |
| `:ObsidianPasteImg` | `:Obsidian paste_img` |
| `:ObsidianExtractNote` | `:Obsidian extract_note` |
| `:ObsidianTOC` | `:Obsidian toc` |

## Command Mappings

### Recommended Keymaps

```lua
-- Daily notes
vim.keymap.set("n", "<leader>ot", "<cmd>Obsidian today<CR>", { desc = "Today's note" })
vim.keymap.set("n", "<leader>oy", "<cmd>Obsidian yesterday<CR>", { desc = "Yesterday's note" })
vim.keymap.set("n", "<leader>om", "<cmd>Obsidian tomorrow<CR>", { desc = "Tomorrow's note" })
vim.keymap.set("n", "<leader>od", "<cmd>Obsidian dailies<CR>", { desc = "Daily notes" })

-- Note operations
vim.keymap.set("n", "<leader>on", "<cmd>Obsidian new<CR>", { desc = "New note" })
vim.keymap.set("n", "<leader>os", "<cmd>Obsidian search<CR>", { desc = "Search notes" })
vim.keymap.set("n", "<leader>oq", "<cmd>Obsidian quick_switch<CR>", { desc = "Quick switch" })
vim.keymap.set("n", "<leader>ob", "<cmd>Obsidian backlinks<CR>", { desc = "Backlinks" })
vim.keymap.set("n", "<leader>ol", "<cmd>Obsidian links<CR>", { desc = "Links" })
vim.keymap.set("n", "<leader>oc", "<cmd>Obsidian toc<CR>", { desc = "Table of contents" })

-- Templates
vim.keymap.set("n", "<leader>oi", "<cmd>Obsidian template<CR>", { desc = "Insert template" })
vim.keymap.set("n", "<leader>oN", "<cmd>Obsidian new_from_template<CR>", { desc = "New from template" })

-- Visual mode
vim.keymap.set("v", "<leader>ol", "<cmd>Obsidian link<CR>", { desc = "Link selection" })
vim.keymap.set("v", "<leader>oL", "<cmd>Obsidian link_new<CR>", { desc = "Link new" })
vim.keymap.set("v", "<leader>oe", "<cmd>Obsidian extract_note<CR>", { desc = "Extract note" })

-- Checkbox
vim.keymap.set("n", "<leader>ox", "<cmd>Obsidian toggle_checkbox<CR>", { desc = "Toggle checkbox" })

-- Smart action (follow link or toggle checkbox)
vim.keymap.set("n", "<CR>", function()
  local obsidian = require("obsidian")
  if obsidian.util.cursor_on_markdown_link() then
    return "<cmd>Obsidian follow_link<CR>"
  else
    return "<CR>"
  end
end, { expr = true })
```

## Context-Sensitive Commands

Commands are context-aware:
- Some commands only appear when in a note (markdown file)
- Some commands only appear in visual mode
- Tab completion filters by context

### Note Commands (require being in a note)

- `backlinks`
- `follow_link`
- `links`
- `paste_img`
- `rename`
- `template`
- `toc`
- `toggle_checkbox`

### Visual Mode Commands

- `extract_note`
- `link`
- `link_new`

### Always Available Commands

- `check`
- `dailies`
- `new`
- `new_from_template`
- `open`
- `quick_switch`
- `search`
- `tags`
- `today`
- `tomorrow`
- `workspace`
- `yesterday`
