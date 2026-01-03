# Templater Reference

## Configuration

Templates folder: `99 - Meta/00 - Templates/`

## Basic Syntax

All Templater commands use `<% %>` delimiters:

```markdown
<% tp.module.function() %>
```

Output result: `<% tp.module.function() %>`
Execute without output: `<%* code %>`
Whitespace control: `<%- %> or <% -%>`

## File Module (tp.file)

```markdown
<% tp.file.title %>                        # Filename without extension
<% tp.file.path() %>                       # Full path
<% tp.file.path(true) %>                   # Relative path
<% tp.file.folder() %>                     # Parent folder name
<% tp.file.folder(true) %>                 # Full folder path
<% tp.file.content %>                      # File content
<% tp.file.selection() %>                  # Selected text
<% tp.file.cursor(1) %>                    # Cursor position (numbered)
<% tp.file.cursor_append("text") %>        # Append at cursor

<%* tp.file.create_new(template, filename, folder) %>  # Create file
<%* tp.file.move("/new/path") %>           # Move file
<%* tp.file.rename("new-name") %>          # Rename file
<%* await tp.file.exists("path") %>        # Check if exists
```

## Date Module (tp.date)

```markdown
<% tp.date.now() %>                        # Current datetime
<% tp.date.now("YYYY-MM-DD") %>            # Formatted date
<% tp.date.now("HH:mm") %>                 # Time only
<% tp.date.now("YYYY-MM-DD", 7) %>         # 7 days from now
<% tp.date.now("YYYY-MM-DD", -1) %>        # Yesterday
<% tp.date.now("dddd") %>                  # Day name
<% tp.date.now("MMMM") %>                  # Month name

<% tp.date.yesterday("YYYY-MM-DD") %>      # Yesterday
<% tp.date.tomorrow("YYYY-MM-DD") %>       # Tomorrow
<% tp.date.weekday("YYYY-MM-DD", 0) %>     # This week's Sunday
```

### Date Format Tokens

| Token | Output |
|-------|--------|
| YYYY | 2025 |
| YY | 25 |
| MMMM | December |
| MMM | Dec |
| MM | 12 |
| M | 12 |
| dddd | Monday |
| ddd | Mon |
| DD | 09 |
| D | 9 |
| HH | 14 (24h) |
| hh | 02 (12h) |
| mm | 30 |
| ss | 45 |
| A | PM |
| a | pm |

## System Module (tp.system)

```markdown
<% tp.system.clipboard() %>                # Clipboard content
<% tp.system.prompt("Question") %>         # User input
<% tp.system.prompt("Question", "default") %>  # With default
<% tp.system.suggester(options, values) %> # Dropdown selection
```

### Suggester Examples

```markdown
<%*
const options = ["Option 1", "Option 2", "Option 3"];
const selected = await tp.system.suggester(options, options);
tR += selected;
%>

<%*
const types = {"Project": "01 - Projects", "Area": "02 - Areas"};
const selected = await tp.system.suggester(Object.keys(types), Object.values(types));
%>
```

## Frontmatter Module (tp.frontmatter)

```markdown
<% tp.frontmatter.title %>                 # Frontmatter field
<% tp.frontmatter["field-name"] %>         # Field with hyphen
<% tp.frontmatter.tags %>                  # Array field
```

## Web Module (tp.web)

```markdown
<% tp.web.daily_quote() %>                 # Random quote
<% tp.web.random_picture() %>              # Random image URL
<% tp.web.random_picture("200x200") %>     # Sized image
```

## User Scripts

Create scripts in user scripts folder and call:

```markdown
<% tp.user.my_script() %>
<% tp.user.my_script(arg1, arg2) %>
```

## JavaScript Execution

Full JavaScript support:

```markdown
<%*
const today = tp.date.now("YYYY-MM-DD");
const title = tp.file.title;

if (title.startsWith("Daily")) {
  tR += "# Daily Note\n";
} else {
  tR += "# " + title + "\n";
}
%>
```

### Variables

- `tR`: Template result string (append to output)
- `tp`: Templater object with all modules

## Template Examples

### Daily Note Template

```markdown
---
created: <% tp.date.now("YYYY-MM-DDTHH:mm") %>
updated: <% tp.date.now("YYYY-MM-DDTHH:mm") %>
title: "<% tp.file.title %>"
type: daily-note
tags:
  - daily
  - <% tp.date.now("YYYY") %>
  - <% tp.date.now("YYYY-MM") %>
aliases:
  - "<% tp.date.now("YYYY-MM-DD") %>"
---

# Daily Note - <% tp.date.now("YYYY-MM-DD") %>

## Tasks
- [ ] <% tp.file.cursor(1) %>

## Journal


## Navigation
<< [[<% tp.date.now("YYYY-MM-DD", -1) %>]] | **Today** | [[<% tp.date.now("YYYY-MM-DD", 1) %>]] >>
```

### New Note Template

```markdown
---
created: <% tp.date.now("YYYY-MM-DDTHH:mm") %>
updated: <% tp.date.now("YYYY-MM-DDTHH:mm") %>
title: "<% tp.file.title %>"
type: <%* const types = ["note", "project", "reference", "zettelkasten"]; tR += await tp.system.suggester(types, types); %>
status: draft
tags:
  - <% tp.file.cursor(2) %>
---

# <% tp.file.title %>

<% tp.file.cursor(1) %>
```

### Meeting Notes Template

```markdown
---
created: <% tp.date.now("YYYY-MM-DDTHH:mm") %>
type: meeting
attendees:
  -
project: "[[<% await tp.system.prompt("Project") %>]]"
---

# Meeting: <% await tp.system.prompt("Meeting Topic") %>

**Date**: <% tp.date.now("YYYY-MM-DD HH:mm") %>
**Attendees**:

## Agenda
1. <% tp.file.cursor(1) %>

## Notes


## Action Items
- [ ]

## Follow-up
```

### Book Notes Template

```markdown
---
created: <% tp.date.now("YYYY-MM-DDTHH:mm") %>
type: book
title: "<% await tp.system.prompt("Book Title") %>"
author: "<% await tp.system.prompt("Author") %>"
status: reading
rating: /5
---

# <% tp.frontmatter.title %>

**Author**: <% tp.frontmatter.author %>
**Started**: <% tp.date.now("YYYY-MM-DD") %>

## Summary


## Key Takeaways
1.
2.
3.

## Quotes


## Notes
<% tp.file.cursor(1) %>
```
