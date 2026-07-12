---
name: power-bi-pages
description: >
  Manage Power BI report pages and bookmarks -- add, remove, configure, and lay
  out pages in PBIR reports using pbi-cli. Invoke this skill whenever the user
  mentions "add page", "new page", "delete page", "page layout", "page size",
  "page background", "hide page", "show page", "drillthrough", "page order",
  "page visibility", "page settings", "page navigation", "bookmark", "create
  bookmark", "save bookmark", "delete bookmark", or wants to manage bookmarks
  that capture page-level state. Also invoke when the user asks about drillthrough
  configuration or pageBinding.
tools: pbi-cli
---

# Power BI Pages Skill

Manage pages in PBIR reports. Pages are folders inside `definition/pages/`
containing a `page.json` file and a `visuals/` directory. No Power BI Desktop
connection is needed.

## Listing and Inspecting Pages

```bash
# List all pages with display names, order, and visibility
pbi report list-pages

# Get full details of a specific page
pbi report get-page page_abc123
```

`get-page` returns:
- `name`, `display_name`, `ordinal` (sort order)
- `width`, `height` (canvas size in pixels)
- `display_option` (e.g. `"FitToPage"`)
- `visual_count` -- how many visuals on the page
- `is_hidden` -- whether the page is hidden in the navigation pane
- `page_type` -- `"Default"` or `"Drillthrough"`
- `filter_config` -- page-level filter configuration (if any)
- `visual_interactions` -- custom visual interaction rules (if any)
- `page_binding` -- drillthrough parameter definition (if drillthrough page)

## Adding Pages

```bash
# Add with display name (folder name auto-generated)
pbi report add-page --display-name "Executive Overview"

# Custom folder name and canvas size
pbi report add-page --display-name "Details" --name detail_page \
    --width 1920 --height 1080
```

Default canvas size is 1280x720 (standard 16:9). Common alternatives:
- 1920x1080 -- Full HD
- 1280x960 -- 4:3
- Custom dimensions for mobile or dashboard layouts

## Deleting Pages

```bash
# Delete a page and all its visuals
pbi report delete-page page_abc123
```

This removes the entire page folder including all visual subdirectories.

## Page Background

```bash
# Set a solid background colour
pbi report set-background page_abc123 --color "#F5F5F5"
```

## Page Visibility

Control whether a page appears in the report navigation pane:

```bash
# Hide a page (useful for drillthrough or tooltip pages)
pbi report set-visibility page_abc123 --hidden

# Show a hidden page
pbi report set-visibility page_abc123 --visible
```

## Bookmarks

Bookmarks capture page-level state (filters, visibility, scroll position).
They live in `definition/bookmarks/`:

```bash
# List all bookmarks in the report
pbi bookmarks list

# Get details of a specific bookmark
pbi bookmarks get "My Bookmark"

# Add a new bookmark
pbi bookmarks add "Executive View"

# Delete a bookmark
pbi bookmarks delete "Old Bookmark"

# Toggle bookmark visibility
pbi bookmarks set-visibility "Draft View" --hidden
```

## Drillthrough Pages

Drillthrough pages have a `pageBinding` field in `page.json` that defines the
drillthrough parameter. When you call `get-page` on a drillthrough page, the
`page_binding` field returns the full binding definition including parameter
name, bound filter, and field expression. Regular pages return `null`.

To create a drillthrough page, add a page and then configure it as drillthrough
in Power BI Desktop (PBIR drillthrough configuration is not yet supported via
CLI -- the CLI can read and report on drillthrough configuration).

## Workflow: Set Up Report Pages

```bash
# 1. Add pages in order
pbi report add-page --display-name "Overview" --name overview
pbi report add-page --display-name "Sales Detail" --name sales_detail
pbi report add-page --display-name "Regional Drillthrough" --name region_drill

# 2. Hide the drillthrough page from navigation
pbi report set-visibility region_drill --hidden

# 3. Set backgrounds
pbi report set-background overview --color "#FAFAFA"

# 4. Verify the setup
pbi report list-pages
```

## Path Resolution

Page commands inherit the report path from the parent `pbi report` group:

1. Explicit: `pbi report --path ./MyReport.Report list-pages`
2. Auto-detect: walks up from CWD looking for `*.Report/definition/`
3. From `.pbip`: finds sibling `.Report` folder from `.pbip` file

## Suppressing Auto-Sync (--no-sync)

By default, every write command automatically syncs Power BI Desktop. When
setting up multiple pages in sequence, Desktop reloads after each one.

Use `--no-sync` on the `report` command group to batch all page changes, then
call `pbi report reload` once at the end:

```bash
# Suppress sync while setting up pages
pbi report --no-sync add-page --display-name "Overview" --name overview
pbi report --no-sync add-page --display-name "Details" --name details
pbi report --no-sync set-background overview --color "#F2F2F2"
pbi report --no-sync set-background details --color "#F2F2F2"

# Single reload when all page setup is done
pbi report reload
```

## JSON Output

```bash
pbi --json report list-pages
pbi --json report get-page page_abc123
pbi --json bookmarks list
```

---

## Gotchas

- **`delete-page` is irreversible and removes the entire folder including visuals:** No trash, no undo. If the page has unique visuals not duplicated elsewhere, they're gone. Always `pbi report export-tmdl` or git-commit before deleting.
- **`set-visibility --hidden` does not hide a page from a published report URL:** Anyone with the deep link `/reports/{id}/{pageId}` still loads it. For sensitive draft pages, also restrict the workspace role — visibility is a UX flag, not a security boundary.
- **Drillthrough pages with `pageBinding` shown by `get-page` cannot yet be created by the CLI:** You can read/list them but must configure the binding in Desktop. Round-tripping through Desktop sometimes reformats unrelated page settings — diff before commit.
- **`add-page` ordinals are auto-assigned from the next-highest value, not appended at the end visually:** If a previous page was deleted, the new ordinal can collide with what users perceive as the order. Use `pbi report list-pages` to confirm visible order.
- **Bookmarks capture visual state by visual ID, not by name:** Renaming a visual after a bookmark is saved leaves the bookmark pointing at a stale ID — the bookmark loads but the renamed visual ignores it. Rebuild bookmarks after any rename.
- **Default page size 1280x720 looks fine in Desktop and broken on mobile:** Desktop renders FitToPage by default; Service on phone uses the phone layout if defined, else clips. Always define a phone layout or set canvas to 1080-wide max for mobile-likely reports.

