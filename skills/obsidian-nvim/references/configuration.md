# obsidian.nvim Configuration Reference

Complete configuration options for obsidian.nvim.

## Core Configuration

### Workspaces

Required configuration for vault locations:

```lua
workspaces = {
  {
    name = "personal",
    path = "~/vaults/personal",
    -- Optional: workspace-specific overrides
    overrides = {
      notes_subdir = "notes",
    },
  },
  {
    name = "work",
    path = "~/vaults/work",
  },
},
```

### Note Location

```lua
-- Subdirectory for new notes (nil = vault root)
notes_subdir = "notes",

-- Where to create new notes
-- Options: "current_dir", "notes_subdir"
new_notes_location = "current_dir",
```

### Note ID Function

```lua
-- Default: Zettelkasten-style with timestamp
note_id_func = function(title)
  local suffix = ""
  if title ~= nil then
    suffix = title:gsub(" ", "-"):gsub("[^A-Za-z0-9-]", ""):lower()
  else
    for _ = 1, 4 do
      suffix = suffix .. string.char(math.random(65, 90))
    end
  end
  return tostring(os.time()) .. "-" .. suffix
end,

-- Simple title-based ID
note_id_func = function(title)
  if title ~= nil then
    return title:gsub(" ", "-"):gsub("[^A-Za-z0-9-]", ""):lower()
  end
  return tostring(os.time())
end,
```

### Note Path Function

```lua
note_path_func = function(spec)
  local path = spec.dir / tostring(spec.id)
  return path
end,
```

## Daily Notes

```lua
daily_notes = {
  -- Folder for daily notes (relative to vault)
  folder = "daily",

  -- Date format for filenames (strftime format)
  date_format = "%Y-%m-%d",

  -- Alias format for display
  alias_format = "%B %-d, %Y",

  -- Template file for daily notes
  template = "daily.md",

  -- Default tags for daily notes
  default_tags = { "daily-notes" },

  -- Skip weekends for yesterday/tomorrow commands
  workdays_only = true,
},
```

## Templates

```lua
templates = {
  -- Template folder (relative to vault)
  folder = "templates",

  -- Date format for {{date}} variable
  date_format = "%Y-%m-%d",

  -- Time format for {{time}} variable
  time_format = "%H:%M",

  -- Custom substitution variables
  substitutions = {
    yesterday = function()
      return os.date("%Y-%m-%d", os.time() - 86400)
    end,
    tomorrow = function()
      return os.date("%Y-%m-%d", os.time() + 86400)
    end,
    week_number = function()
      return os.date("%V")
    end,
  },

  -- Template-specific customizations
  customizations = {
    ["meeting"] = {
      notes_subdir = "meetings",
      note_id_func = function(title)
        return os.date("%Y%m%d") .. "-" .. (title or "meeting")
      end,
    },
  },
},
```

### Template Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `{{title}}` | Note title | "My Note" |
| `{{date}}` | Current date | "2024-01-15" |
| `{{time}}` | Current time | "14:30" |
| `{{id}}` | Note ID | "1705344600-my-note" |
| `{{path}}` | Note path | "notes/my-note.md" |

## Frontmatter

```lua
frontmatter = {
  -- Enable/disable frontmatter management
  enabled = true,

  -- Can be a function for conditional enabling
  -- enabled = function(fname) return not fname:match("templates/") end,

  -- Function to generate frontmatter content
  func = function(note)
    local out = {
      id = note.id,
      aliases = note.aliases,
      tags = note.tags,
    }
    -- Include custom metadata
    if note.metadata ~= nil and not vim.tbl_isempty(note.metadata) then
      for k, v in pairs(note.metadata) do
        out[k] = v
      end
    end
    return out
  end,

  -- Property sort order (list or function)
  sort = { "id", "aliases", "tags" },
  -- sort = false,  -- disable sorting
},
```

## Completion

```lua
completion = {
  -- Use nvim-cmp for completion
  nvim_cmp = true,

  -- Use blink.cmp for completion (takes precedence if both true)
  blink = false,

  -- Minimum characters to trigger completion
  min_chars = 2,

  -- Case-sensitive matching
  match_case = true,

  -- Allow creating new notes from completion
  create_new = true,
},
```

## Picker Configuration

```lua
picker = {
  -- Picker backend: "telescope", "fzf-lua", "mini.pick", "snacks.picker"
  name = "telescope",

  -- Mappings in note picker
  note_mappings = {
    -- Create new note
    new = "<C-x>",
    -- Insert link to selected note
    insert_link = "<C-l>",
  },

  -- Mappings in tag picker
  tag_mappings = {
    -- Create note from tag
    tag_note = "<C-x>",
    -- Insert tag
    insert_tag = "<C-l>",
  },
},
```

## Search Options

```lua
search = {
  -- Sort by: "modified", "created", "path"
  sort_by = "modified",

  -- Reverse sort order
  sort_reversed = true,

  -- Maximum lines to search per file
  max_lines = 1000,
},
```

## Link Style

```lua
-- Preferred link style: "wiki" or "markdown"
preferred_link_style = "wiki",

-- Wiki link format function
wiki_link_func = function(opts)
  if opts.id == opts.label then
    return string.format("[[%s]]", opts.label)
  else
    return string.format("[[%s|%s]]", opts.id, opts.label)
  end
end,

-- Markdown link format function
markdown_link_func = function(opts)
  return string.format("[%s](%s)", opts.label, opts.path)
end,
```

## UI Configuration

```lua
ui = {
  -- Enable/disable UI features
  enable = true,

  -- Suppress conceallevel warning
  ignore_conceal_warn = false,

  -- Debounce time for UI updates (ms)
  update_debounce = 200,

  -- Disable UI for files larger than this
  max_file_length = 5000,

  -- Checkbox styles
  checkboxes = {
    [" "] = { char = "󰄱", hl_group = "ObsidianTodo" },
    ["~"] = { char = "󰰱", hl_group = "ObsidianTilde" },
    ["!"] = { char = "", hl_group = "ObsidianImportant" },
    [">"] = { char = "", hl_group = "ObsidianRightArrow" },
    ["x"] = { char = "", hl_group = "ObsidianDone" },
  },

  -- Bullet point style
  bullets = { char = "•", hl_group = "ObsidianBullet" },

  -- External link icon
  external_link_icon = { char = "", hl_group = "ObsidianExtLinkIcon" },

  -- Reference text style
  reference_text = { hl_group = "ObsidianRefText" },

  -- Highlighted text style
  highlight_text = { hl_group = "ObsidianHighlightText" },

  -- Tag style
  tags = { hl_group = "ObsidianTag" },

  -- Block ID style
  block_ids = { hl_group = "ObsidianBlockID" },

  -- Custom highlight groups
  hl_groups = {
    ObsidianTodo = { bold = true, fg = "#f78c6c" },
    ObsidianDone = { bold = true, fg = "#89ddff" },
    ObsidianRightArrow = { bold = true, fg = "#f78c6c" },
    ObsidianTilde = { strikethrough = true, fg = "#89ddff" },
    ObsidianImportant = { bold = true, fg = "#d73128" },
    ObsidianBullet = { bold = true, fg = "#89ddff" },
    ObsidianRefText = { underline = true, fg = "#c792ea" },
    ObsidianExtLinkIcon = { fg = "#c792ea" },
    ObsidianTag = { italic = true, fg = "#89ddff" },
    ObsidianBlockID = { italic = true, fg = "#89ddff" },
    ObsidianHighlightText = { bg = "#75662e" },
  },
},
```

## Statusline

```lua
statusline = {
  -- Enable statusline component
  enabled = true,

  -- Format string with placeholders
  format = "{{backlinks}} backlinks  {{properties}} properties  {{words}} words  {{chars}} chars",
},
```

## Backlinks

```lua
backlinks = {
  -- Parse headers in backlink display
  parse_headers = true,
},
```

## Attachments

Configure image and file attachment handling:

```lua
attachments = {
  -- Folder for images/attachments (relative to vault)
  img_folder = "assets/imgs",

  -- Confirm before creating new attachments folder
  confirm_img_paste = true,

  -- Function to generate image filename
  img_name_func = function()
    return string.format("%s-", os.time())
  end,

  -- Function to generate image text/link
  img_text_func = function(client, path)
    path = client:vault_relative_path(path) or path
    return string.format("![%s](%s)", path.name, path)
  end,
},
```

### Image Name Patterns

```lua
-- Timestamp-based (default)
img_name_func = function()
  return string.format("%s-", os.time())
end,

-- UUID-based
img_name_func = function()
  local uuid = ""
  for _ = 1, 8 do
    uuid = uuid .. string.format("%x", math.random(0, 15))
  end
  return uuid .. "-"
end,

-- Date-based with description prompt
img_name_func = function()
  local desc = vim.fn.input("Image description: ")
  local date = os.date("%Y%m%d")
  if desc ~= "" then
    return date .. "-" .. desc:gsub(" ", "-"):lower() .. "-"
  end
  return date .. "-"
end,
```

## Callbacks

Lifecycle hooks for custom behavior:

```lua
callbacks = {
  -- Called after obsidian.nvim is fully initialized
  post_setup = function(client)
    -- Example: Set up additional keymaps
    vim.notify("Obsidian workspace: " .. client.current_workspace.name)
  end,

  -- Called when entering a note buffer
  enter_note = function(client, note)
    -- Example: Update statusline, log access
    vim.b.obsidian_note_id = note.id
  end,

  -- Called when leaving a note buffer
  leave_note = function(client, note)
    -- Example: Auto-save, cleanup
  end,

  -- Called before writing/saving a note
  pre_write_note = function(client, note)
    -- Example: Update modified timestamp in frontmatter
    note.metadata = note.metadata or {}
    note.metadata.modified = os.date("%Y-%m-%d %H:%M")
  end,

  -- Called after switching workspaces
  post_set_workspace = function(client, workspace)
    vim.notify("Switched to workspace: " .. workspace.name)
  end,
},
```

### Callback Use Cases

```lua
-- Auto-update modified date
callbacks = {
  pre_write_note = function(client, note)
    if note.metadata then
      note.metadata.modified = os.date("%Y-%m-%d %H:%M")
    end
  end,
},

-- Log note access for analytics
callbacks = {
  enter_note = function(client, note)
    local log_file = client.dir / ".note_access.log"
    local f = io.open(tostring(log_file), "a")
    if f then
      f:write(os.date("%Y-%m-%d %H:%M") .. " " .. note.id .. "\n")
      f:close()
    end
  end,
},

-- Workspace-specific settings
callbacks = {
  post_set_workspace = function(client, workspace)
    if workspace.name == "work" then
      vim.opt_local.spell = true
      vim.opt_local.spelllang = "en_us"
    end
  end,
},
```

## Note Opening

```lua
-- How to open notes: "current", "vsplit", "hsplit"
open_notes_in = "current",

-- Function to handle URL following
follow_url_func = vim.ui.open,

-- Function to handle image following
follow_img_func = vim.ui.open,
```

## Logging

```lua
-- Log level: vim.log.levels.DEBUG, INFO, WARN, ERROR
log_level = vim.log.levels.INFO,
```

## Legacy Commands

```lua
-- Enable legacy :ObsidianXXX commands (deprecated, will be removed)
legacy_commands = false,
```

## Complete Example

```lua
require("obsidian").setup({
  workspaces = {
    { name = "personal", path = "~/vaults/personal" },
    { name = "work", path = "~/vaults/work" },
  },

  notes_subdir = "notes",
  new_notes_location = "notes_subdir",

  daily_notes = {
    folder = "daily",
    date_format = "%Y-%m-%d",
    alias_format = "%B %-d, %Y",
    template = "daily.md",
    default_tags = { "daily-notes" },
    workdays_only = true,
  },

  templates = {
    folder = "templates",
    date_format = "%Y-%m-%d",
    time_format = "%H:%M",
    substitutions = {},
  },

  frontmatter = {
    enabled = true,
    sort = { "id", "aliases", "tags" },
  },

  completion = {
    nvim_cmp = true,
    min_chars = 2,
  },

  picker = {
    name = "telescope",
    note_mappings = {
      new = "<C-x>",
      insert_link = "<C-l>",
    },
  },

  preferred_link_style = "wiki",
  open_notes_in = "current",

  ui = {
    enable = true,
    checkboxes = {
      [" "] = { char = "󰄱", hl_group = "ObsidianTodo" },
      ["x"] = { char = "", hl_group = "ObsidianDone" },
    },
  },

  log_level = vim.log.levels.INFO,
})
```
