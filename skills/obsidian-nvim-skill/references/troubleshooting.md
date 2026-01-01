# obsidian.nvim Troubleshooting Guide

Comprehensive solutions for common issues with obsidian.nvim.

## Health Check

Always start by running the health check:

```vim
:checkhealth obsidian
```

This verifies:
- Neovim version compatibility
- Required dependencies (ripgrep, pngpaste/xclip)
- Workspace configuration
- Plugin dependencies

## Installation Issues

### Plugin Not Loading

**Symptoms:** Commands not available, no syntax highlighting

**Solutions:**

1. **Verify lazy loading trigger:**
```lua
-- Ensure ft = "markdown" is set
return {
  "obsidian-nvim/obsidian.nvim",
  ft = "markdown",  -- Required for lazy loading
  -- ...
}
```

2. **Check if in vault directory:**
```vim
:pwd
:echo expand('%:p')
```
The file must be within a configured workspace path.

3. **Force load the plugin:**
```vim
:Lazy load obsidian.nvim
```

### Workspace Not Detected

**Symptoms:** "No workspace found" errors

**Solutions:**

1. **Verify workspace paths exist:**
```lua
workspaces = {
  { name = "personal", path = vim.fn.expand("~/vaults/personal") },
}
```

2. **Check path expansion:**
```vim
:lua print(vim.fn.expand("~/vaults/personal"))
```

3. **Ensure you're editing a file inside the vault:**
```vim
:echo expand('%:p:h')
```

## Completion Issues

### Wiki Link Completion Not Working

**Symptoms:** Typing `[[` doesn't trigger completion

**Solutions:**

1. **Verify ripgrep is installed:**
```bash
which rg
rg --version
```

2. **Check completion configuration:**
```lua
completion = {
  nvim_cmp = true,  -- or blink = true
  min_chars = 2,
},
```

3. **For nvim-cmp, verify source is added:**
```lua
-- In your nvim-cmp config
sources = {
  { name = "obsidian" },
  { name = "obsidian_new" },
  { name = "obsidian_tags" },
  -- other sources...
}
```

4. **For blink.cmp:**
```lua
completion = {
  blink = true,
  nvim_cmp = false,
},
```

### Tag Completion Not Triggering

**Symptoms:** `#` doesn't show tag suggestions

**Solutions:**

1. **Check min_chars setting:**
```lua
completion = {
  min_chars = 1,  -- Lower for faster triggering
},
```

2. **Ensure tags exist in vault** - completion pulls from existing tags

3. **Verify you're in a markdown file in the vault**

## Picker Issues

### Picker Not Opening

**Symptoms:** `:Obsidian search` does nothing

**Solutions:**

1. **Verify picker plugin is installed:**
```vim
:Telescope  " or :FzfLua, etc.
```

2. **Check picker configuration:**
```lua
picker = {
  name = "telescope",  -- Must match installed picker
},
```

3. **Valid picker names:**
- `"telescope"` - nvim-telescope/telescope.nvim
- `"fzf-lua"` - ibhagwan/fzf-lua
- `"mini.pick"` - echasnovski/mini.pick
- `"snacks.picker"` - folke/snacks.nvim

### Telescope Errors

**Symptoms:** Telescope throws errors when searching

**Solutions:**

1. **Update telescope.nvim** to latest version

2. **Check for conflicting mappings:**
```vim
:verbose map <C-x>
```

3. **Verify plenary.nvim is installed:**
```lua
dependencies = {
  "nvim-lua/plenary.nvim",
  "nvim-telescope/telescope.nvim",
},
```

## Link Issues

### Links Not Following

**Symptoms:** `<CR>` or `:Obsidian follow_link` does nothing

**Solutions:**

1. **Verify cursor is on a link:**
```lua
:lua print(require("obsidian").util.cursor_on_markdown_link())
```

2. **Check link format:**
- Wiki: `[[note-name]]` or `[[note-name|display text]]`
- Markdown: `[text](note-name.md)`

3. **Verify target note exists** or allow creation:
```lua
-- In picker mappings, <C-x> creates new notes
```

4. **Check for special characters in link:**
```lua
-- Links with spaces need proper encoding
[[My Note]]  -- OK
[[my-note]]  -- OK
```

### Backlinks Not Showing

**Symptoms:** `:Obsidian backlinks` shows empty

**Solutions:**

1. **Ensure ripgrep can search vault:**
```bash
cd ~/your-vault
rg "your-note-name" --type md
```

2. **Check note ID vs filename:**
```lua
-- If using note_id_func, links use IDs not filenames
```

3. **Verify backlinks configuration:**
```lua
backlinks = {
  parse_headers = true,
},
```

## Image/Paste Issues

### Image Paste Not Working

**Symptoms:** `:Obsidian paste_img` fails

**Solutions:**

1. **macOS - Install pngpaste:**
```bash
brew install pngpaste
which pngpaste  # Verify installation
```

2. **Linux X11 - Install xclip:**
```bash
sudo apt install xclip  # Debian/Ubuntu
sudo pacman -S xclip    # Arch
```

3. **Linux Wayland - Install wl-clipboard:**
```bash
sudo apt install wl-clipboard
```

4. **Verify image is in clipboard:**
```bash
# macOS
pngpaste - > /dev/null && echo "Image in clipboard"

# Linux X11
xclip -selection clipboard -t image/png -o > /dev/null 2>&1 && echo "Image in clipboard"
```

5. **Check attachments folder exists:**
```lua
attachments = {
  img_folder = "assets/imgs",
  confirm_img_paste = true,  -- Will prompt to create
},
```

### Images Not Displaying

**Symptoms:** Image links appear but no preview

**Note:** obsidian.nvim doesn't render images inline. For image preview:
- Use Obsidian app alongside
- Install image.nvim or similar
- Use snacks.nvim image feature

## UI Issues

### Checkboxes Not Rendering

**Symptoms:** `- [ ]` shows as plain text

**Solutions:**

1. **Enable UI features:**
```lua
ui = {
  enable = true,
  checkboxes = {
    [" "] = { char = "󰄱", hl_group = "ObsidianTodo" },
    ["x"] = { char = "", hl_group = "ObsidianDone" },
  },
},
```

2. **Check conceallevel:**
```vim
:set conceallevel?
" Should be 1 or 2 for concealment
:set conceallevel=2
```

3. **Verify font supports icons** - Nerd Font required

4. **Suppress conceallevel warning:**
```lua
ui = {
  enable = true,
  ignore_conceal_warn = true,
},
```

### Highlight Groups Missing

**Symptoms:** No colors for tags, links, etc.

**Solutions:**

1. **Define highlight groups:**
```lua
ui = {
  hl_groups = {
    ObsidianTodo = { bold = true, fg = "#f78c6c" },
    ObsidianDone = { bold = true, fg = "#89ddff" },
    ObsidianTag = { italic = true, fg = "#89ddff" },
    -- Add more as needed
  },
},
```

2. **Check colorscheme compatibility** - Some colorschemes override highlights

3. **Apply after colorscheme loads:**
```lua
vim.api.nvim_create_autocmd("ColorScheme", {
  callback = function()
    -- Re-apply obsidian highlights
  end,
})
```

## Template Issues

### Templates Not Found

**Symptoms:** `:Obsidian template` shows empty list

**Solutions:**

1. **Verify template folder path:**
```lua
templates = {
  folder = "templates",  -- Relative to vault root
},
```

2. **Check templates exist:**
```bash
ls ~/your-vault/templates/
```

3. **Ensure templates are .md files**

### Template Variables Not Substituting

**Symptoms:** `{{date}}` appears literally in note

**Solutions:**

1. **Check variable syntax:** Must be `{{variable}}` with double braces

2. **Verify substitution is defined:**
```lua
templates = {
  date_format = "%Y-%m-%d",
  time_format = "%H:%M",
  substitutions = {
    -- Custom variables here
  },
},
```

3. **Built-in variables:**
- `{{title}}` - Note title
- `{{date}}` - Current date
- `{{time}}` - Current time
- `{{id}}` - Note ID

## Daily Notes Issues

### Daily Notes in Wrong Location

**Symptoms:** Daily notes created in vault root

**Solutions:**

1. **Configure daily notes folder:**
```lua
daily_notes = {
  folder = "daily",  -- Creates ~/vault/daily/
  date_format = "%Y-%m-%d",
},
```

2. **For nested folders:**
```lua
daily_notes = {
  folder = "journal/daily",
  date_format = "%Y/%m/%Y-%m-%d",  -- Creates year/month subfolders
},
```

### Yesterday/Tomorrow Skipping Wrong Days

**Symptoms:** Weekend handling unexpected

**Solutions:**

```lua
daily_notes = {
  workdays_only = false,  -- Include weekends
  -- or
  workdays_only = true,   -- Skip Sat/Sun
},
```

## Performance Issues

### Slow Startup

**Solutions:**

1. **Use lazy loading:**
```lua
return {
  "obsidian-nvim/obsidian.nvim",
  lazy = true,
  ft = "markdown",
  event = {
    "BufReadPre " .. vim.fn.expand("~") .. "/vaults/**.md",
  },
},
```

2. **Limit UI processing:**
```lua
ui = {
  max_file_length = 5000,
  update_debounce = 200,
},
```

### Slow Completion

**Solutions:**

1. **Increase min_chars:**
```lua
completion = {
  min_chars = 3,
},
```

2. **Ensure ripgrep is optimized:**
```bash
# Add to .rgignore in vault
.git
.obsidian
node_modules
```

## Debug Mode

Enable verbose logging for troubleshooting:

```lua
log_level = vim.log.levels.DEBUG,
```

View logs:
```vim
:messages
" or check Neovim log file
```

## Getting Help

1. **GitHub Issues:** https://github.com/obsidian-nvim/obsidian.nvim/issues
2. **Wiki:** https://github.com/obsidian-nvim/obsidian.nvim/wiki
3. **Discussions:** https://github.com/obsidian-nvim/obsidian.nvim/discussions

When reporting issues, include:
- Neovim version: `:version`
- Plugin version
- Minimal reproduction config
- Health check output: `:checkhealth obsidian`
