# obsidian.nvim Configuration Examples

Practical configuration examples for common use cases.

## Minimal Setup

The simplest possible configuration:

```lua
-- lazy.nvim
return {
  "obsidian-nvim/obsidian.nvim",
  version = "*",
  ft = "markdown",
  opts = {
    workspaces = {
      { name = "notes", path = "~/notes" },
    },
  },
}
```

## Full-Featured Setup

Complete configuration with all common features:

```lua
return {
  "obsidian-nvim/obsidian.nvim",
  version = "*",
  lazy = true,
  ft = "markdown",
  dependencies = {
    "nvim-lua/plenary.nvim",
    "nvim-telescope/telescope.nvim",
    "hrsh7th/nvim-cmp",
  },
  opts = {
    workspaces = {
      {
        name = "personal",
        path = "~/vaults/personal",
      },
      {
        name = "work",
        path = "~/vaults/work",
        overrides = {
          notes_subdir = "notes",
        },
      },
    },

    notes_subdir = "inbox",
    new_notes_location = "notes_subdir",

    daily_notes = {
      folder = "daily",
      date_format = "%Y-%m-%d",
      alias_format = "%B %-d, %Y",
      template = "daily.md",
      default_tags = { "daily" },
      workdays_only = false,
    },

    templates = {
      folder = "templates",
      date_format = "%Y-%m-%d",
      time_format = "%H:%M",
      substitutions = {
        yesterday = function()
          return os.date("%Y-%m-%d", os.time() - 86400)
        end,
        tomorrow = function()
          return os.date("%Y-%m-%d", os.time() + 86400)
        end,
      },
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
      tag_mappings = {
        tag_note = "<C-x>",
        insert_tag = "<C-l>",
      },
    },

    preferred_link_style = "wiki",
    open_notes_in = "current",

    ui = {
      enable = true,
      update_debounce = 200,
      checkboxes = {
        [" "] = { char = "󰄱", hl_group = "ObsidianTodo" },
        ["x"] = { char = "", hl_group = "ObsidianDone" },
        [">"] = { char = "", hl_group = "ObsidianRightArrow" },
        ["~"] = { char = "󰰱", hl_group = "ObsidianTilde" },
      },
      bullets = { char = "•", hl_group = "ObsidianBullet" },
      external_link_icon = { char = "", hl_group = "ObsidianExtLinkIcon" },
    },

    statusline = {
      enabled = true,
      format = "{{backlinks}}  {{words}} words",
    },

    log_level = vim.log.levels.INFO,
  },
  keys = {
    { "<leader>oo", "<cmd>Obsidian<CR>", desc = "Obsidian commands" },
    { "<leader>ot", "<cmd>Obsidian today<CR>", desc = "Today's note" },
    { "<leader>os", "<cmd>Obsidian search<CR>", desc = "Search notes" },
    { "<leader>oq", "<cmd>Obsidian quick_switch<CR>", desc = "Quick switch" },
    { "<leader>on", "<cmd>Obsidian new<CR>", desc = "New note" },
    { "<leader>ob", "<cmd>Obsidian backlinks<CR>", desc = "Backlinks" },
  },
}
```

## With blink.cmp

Using blink.cmp instead of nvim-cmp:

```lua
return {
  "obsidian-nvim/obsidian.nvim",
  version = "*",
  ft = "markdown",
  dependencies = {
    "nvim-lua/plenary.nvim",
    "saghen/blink.cmp",
  },
  opts = {
    workspaces = {
      { name = "notes", path = "~/notes" },
    },
    completion = {
      blink = true,
      nvim_cmp = false,
      min_chars = 2,
    },
  },
}
```

## With fzf-lua

Using fzf-lua as the picker:

```lua
return {
  "obsidian-nvim/obsidian.nvim",
  version = "*",
  ft = "markdown",
  dependencies = {
    "nvim-lua/plenary.nvim",
    "ibhagwan/fzf-lua",
  },
  opts = {
    workspaces = {
      { name = "notes", path = "~/notes" },
    },
    picker = {
      name = "fzf-lua",
    },
  },
}
```

## With snacks.nvim

Using snacks.picker and snacks.image:

```lua
return {
  "obsidian-nvim/obsidian.nvim",
  version = "*",
  ft = "markdown",
  dependencies = {
    "nvim-lua/plenary.nvim",
    "folke/snacks.nvim",
  },
  opts = {
    workspaces = {
      { name = "notes", path = "~/notes" },
    },
    picker = {
      name = "snacks.picker",
    },
  },
}
```

## Zettelkasten Setup

Configuration optimized for Zettelkasten method:

```lua
return {
  "obsidian-nvim/obsidian.nvim",
  version = "*",
  ft = "markdown",
  opts = {
    workspaces = {
      { name = "zettelkasten", path = "~/zettelkasten" },
    },

    -- Zettelkasten-style note IDs with timestamp
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

    -- All notes in flat structure
    notes_subdir = nil,
    new_notes_location = "current_dir",

    -- Minimal frontmatter
    frontmatter = {
      enabled = true,
      func = function(note)
        return {
          id = note.id,
          tags = note.tags,
          created = os.date("%Y-%m-%d %H:%M"),
        }
      end,
    },

    -- Wiki links for internal linking
    preferred_link_style = "wiki",
  },
}
```

## PARA Method Setup

Configuration for PARA organization (Projects, Areas, Resources, Archive):

```lua
return {
  "obsidian-nvim/obsidian.nvim",
  version = "*",
  ft = "markdown",
  opts = {
    workspaces = {
      { name = "para", path = "~/para" },
    },

    -- Human-readable note IDs
    note_id_func = function(title)
      if title ~= nil then
        return title:gsub(" ", "-"):gsub("[^A-Za-z0-9-]", ""):lower()
      end
      return "note-" .. os.date("%Y%m%d%H%M%S")
    end,

    -- Notes in inbox for processing
    notes_subdir = "inbox",
    new_notes_location = "notes_subdir",

    daily_notes = {
      folder = "areas/daily",
      date_format = "%Y-%m-%d",
    },

    templates = {
      folder = "resources/templates",
      customizations = {
        project = {
          notes_subdir = "projects",
        },
        area = {
          notes_subdir = "areas",
        },
        resource = {
          notes_subdir = "resources",
        },
      },
    },
  },
}
```

## Multiple Vaults with Overrides

Managing multiple vaults with different settings:

```lua
return {
  "obsidian-nvim/obsidian.nvim",
  version = "*",
  ft = "markdown",
  opts = {
    workspaces = {
      {
        name = "personal",
        path = "~/vaults/personal",
        overrides = {
          notes_subdir = "notes",
          daily_notes = {
            folder = "journal",
            date_format = "%Y/%m/%Y-%m-%d",
            template = "journal.md",
          },
        },
      },
      {
        name = "work",
        path = "~/vaults/work",
        overrides = {
          notes_subdir = "notes",
          daily_notes = {
            folder = "standup",
            date_format = "%Y-%m-%d",
            template = "standup.md",
            workdays_only = true,
          },
          templates = {
            folder = "templates",
            customizations = {
              meeting = {
                notes_subdir = "meetings",
              },
            },
          },
        },
      },
    },
  },
}
```

## Custom Keymaps

Complete keymap configuration:

```lua
return {
  "obsidian-nvim/obsidian.nvim",
  version = "*",
  ft = "markdown",
  opts = {
    workspaces = {
      { name = "notes", path = "~/notes" },
    },
  },
  keys = {
    -- Command picker
    { "<leader>oo", "<cmd>Obsidian<CR>", desc = "Commands" },

    -- Daily notes
    { "<leader>ot", "<cmd>Obsidian today<CR>", desc = "Today" },
    { "<leader>oy", "<cmd>Obsidian yesterday<CR>", desc = "Yesterday" },
    { "<leader>om", "<cmd>Obsidian tomorrow<CR>", desc = "Tomorrow" },
    { "<leader>od", "<cmd>Obsidian dailies<CR>", desc = "Daily notes" },

    -- Notes
    { "<leader>on", "<cmd>Obsidian new<CR>", desc = "New note" },
    { "<leader>oN", "<cmd>Obsidian new_from_template<CR>", desc = "New from template" },
    { "<leader>os", "<cmd>Obsidian search<CR>", desc = "Search" },
    { "<leader>oq", "<cmd>Obsidian quick_switch<CR>", desc = "Quick switch" },
    { "<leader>og", "<cmd>Obsidian tags<CR>", desc = "Tags" },

    -- Current note
    { "<leader>ob", "<cmd>Obsidian backlinks<CR>", desc = "Backlinks" },
    { "<leader>ol", "<cmd>Obsidian links<CR>", desc = "Links" },
    { "<leader>oc", "<cmd>Obsidian toc<CR>", desc = "TOC" },
    { "<leader>oi", "<cmd>Obsidian template<CR>", desc = "Insert template" },
    { "<leader>or", "<cmd>Obsidian rename<CR>", desc = "Rename" },
    { "<leader>ox", "<cmd>Obsidian toggle_checkbox<CR>", desc = "Toggle checkbox" },
    { "<leader>op", "<cmd>Obsidian paste_img<CR>", desc = "Paste image" },

    -- Visual mode
    { "<leader>ol", "<cmd>Obsidian link<CR>", mode = "v", desc = "Link selection" },
    { "<leader>oL", "<cmd>Obsidian link_new<CR>", mode = "v", desc = "Link to new" },
    { "<leader>oe", "<cmd>Obsidian extract_note<CR>", mode = "v", desc = "Extract note" },

    -- Workspace
    { "<leader>ow", "<cmd>Obsidian workspace<CR>", desc = "Workspace" },
  },
  config = function(_, opts)
    require("obsidian").setup(opts)

    -- Smart enter key
    vim.keymap.set("n", "<CR>", function()
      local obsidian = require("obsidian")
      if obsidian.util.cursor_on_markdown_link() then
        return "<cmd>Obsidian follow_link<CR>"
      else
        return "<CR>"
      end
    end, { expr = true, buffer = true })

    -- Navigate links
    vim.keymap.set("n", "[o", function()
      require("obsidian").util.nav_link("prev")
    end, { buffer = true, desc = "Previous link" })
    vim.keymap.set("n", "]o", function()
      require("obsidian").util.nav_link("next")
    end, { buffer = true, desc = "Next link" })
  end,
}
```

## Custom Template Substitutions

Advanced template variable customizations:

```lua
return {
  "obsidian-nvim/obsidian.nvim",
  version = "*",
  ft = "markdown",
  opts = {
    workspaces = {
      { name = "notes", path = "~/notes" },
    },
    templates = {
      folder = "templates",
      date_format = "%Y-%m-%d",
      time_format = "%H:%M",
      substitutions = {
        -- Previous/next days
        yesterday = function()
          return os.date("%Y-%m-%d", os.time() - 86400)
        end,
        tomorrow = function()
          return os.date("%Y-%m-%d", os.time() + 86400)
        end,

        -- Week info
        week_number = function()
          return os.date("%V")
        end,
        week_start = function()
          local today = os.time()
          local wday = os.date("*t", today).wday
          local days_since_monday = (wday + 5) % 7
          return os.date("%Y-%m-%d", today - days_since_monday * 86400)
        end,
        week_end = function()
          local today = os.time()
          local wday = os.date("*t", today).wday
          local days_until_sunday = (7 - wday) % 7
          return os.date("%Y-%m-%d", today + days_until_sunday * 86400)
        end,

        -- Month info
        month_name = function()
          return os.date("%B")
        end,
        month_start = function()
          return os.date("%Y-%m-01")
        end,
        month_end = function()
          local t = os.date("*t")
          t.month = t.month + 1
          t.day = 0
          return os.date("%Y-%m-%d", os.time(t))
        end,

        -- Random quote (example)
        random_quote = function()
          local quotes = {
            "The only way to do great work is to love what you do.",
            "Stay hungry, stay foolish.",
            "Think different.",
          }
          return quotes[math.random(#quotes)]
        end,
      },
    },
  },
}
```

## Custom Frontmatter

Advanced frontmatter customization:

```lua
return {
  "obsidian-nvim/obsidian.nvim",
  version = "*",
  ft = "markdown",
  opts = {
    workspaces = {
      { name = "notes", path = "~/notes" },
    },
    frontmatter = {
      enabled = true,
      func = function(note)
        local out = {
          id = note.id,
          aliases = note.aliases,
          tags = note.tags,
          created = note.metadata.created or os.date("%Y-%m-%d %H:%M"),
          modified = os.date("%Y-%m-%d %H:%M"),
        }

        -- Preserve existing metadata
        if note.metadata then
          for k, v in pairs(note.metadata) do
            if out[k] == nil then
              out[k] = v
            end
          end
        end

        return out
      end,
      sort = { "id", "aliases", "tags", "created", "modified" },
    },
  },
}
```

## Template Files

### Daily Note Template (`templates/daily.md`)

```markdown
---
id: {{id}}
aliases:
  - {{date}}
tags:
  - daily
created: {{date}} {{time}}
---

# {{title}}

## Morning

- [ ] Review calendar
- [ ] Check emails
- [ ] Plan priorities

## Tasks

- [ ]

## Notes

## Evening Review

### What went well?

### What could improve?

### Tomorrow's focus

---

[[{{yesterday}}|← Yesterday]] | [[{{tomorrow}}|Tomorrow →]]
```

### Meeting Template (`templates/meeting.md`)

```markdown
---
id: {{id}}
aliases: []
tags:
  - meeting
created: {{date}} {{time}}
attendees: []
---

# {{title}}

**Date:** {{date}}
**Time:** {{time}}
**Attendees:**

## Agenda

1.

## Notes

## Action Items

- [ ]

## Follow-up
```

### Project Template (`templates/project.md`)

```markdown
---
id: {{id}}
aliases: []
tags:
  - project
status: active
created: {{date}}
---

# {{title}}

## Overview

## Goals

-

## Tasks

- [ ]

## Resources

## Notes

## Timeline

| Milestone | Target Date | Status |
|-----------|-------------|--------|
|           |             |        |
```
