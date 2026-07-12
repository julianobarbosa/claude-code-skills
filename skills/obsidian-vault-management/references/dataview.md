# Dataview Query Reference

## Query Types

### LIST Query

```dataview
LIST
FROM "folder"
WHERE condition
SORT field ASC/DESC
LIMIT 10
```

### TABLE Query

```dataview
TABLE col1, col2, col3
FROM "folder"
WHERE condition
SORT field DESC
```

### TASK Query

```dataview
TASK
FROM "folder"
WHERE !completed
GROUP BY file.link
```

### CALENDAR Query

```dataview
CALENDAR file.cday
FROM "06 - Daily"
```

## Source Selection (FROM)

```dataview
FROM "folder"                    # Specific folder
FROM #tag                        # Notes with tag
FROM [[Note]]                    # Notes linking to Note
FROM outgoing([[Note]])          # Notes linked from Note
FROM "folder" AND #tag           # Combine with AND
FROM "folder" OR "other"         # Combine with OR
FROM -"excluded"                 # Exclude folder
```

## Field Access

### Implicit Fields (automatic)

| Field | Description |
|-------|-------------|
| `file.name` | Filename without extension |
| `file.path` | Full path |
| `file.folder` | Parent folder |
| `file.link` | Link to file |
| `file.size` | File size in bytes |
| `file.ctime` | Creation time |
| `file.cday` | Creation date |
| `file.mtime` | Modified time |
| `file.mday` | Modified date |
| `file.tags` | All tags |
| `file.etags` | Explicit tags only |
| `file.inlinks` | Incoming links |
| `file.outlinks` | Outgoing links |
| `file.tasks` | All tasks |
| `file.lists` | All list items |

### Frontmatter Fields

Access YAML frontmatter directly:

```dataview
TABLE status, created, tags
FROM "01 - Projects"
```

### Inline Fields

Define inline fields in notes:

```markdown
Key:: Value
[Key:: Value]
(Key:: Value)
```

Access in queries: `WHERE key = "value"`

## WHERE Conditions

```dataview
WHERE file.name = "exact"
WHERE contains(file.name, "partial")
WHERE startswith(file.name, "prefix")
WHERE endswith(file.name, "suffix")
WHERE file.cday = date(today)
WHERE file.cday >= date(today) - dur(7 days)
WHERE contains(tags, "#important")
WHERE status != "completed"
WHERE !completed                  # For tasks
WHERE length(file.tags) > 2
WHERE any(file.tags, (t) => startswith(t, "#project"))
```

## SORT Options

```dataview
SORT file.name ASC
SORT file.mtime DESC
SORT status ASC, priority DESC   # Multiple fields
```

## GROUP BY

```dataview
TABLE rows.file.link
FROM "folder"
GROUP BY status
```

## Date Functions

```dataview
date(today)                      # Today
date(now)                        # Current datetime
date(tomorrow)                   # Tomorrow
date(yesterday)                  # Yesterday
date("2025-12-09")               # Specific date
dur(7 days)                      # Duration
dur(1 week)                      # Duration
file.cday.year                   # Extract year
file.cday.month                  # Extract month
file.cday.day                    # Extract day
```

## String Functions

```dataview
contains(string, "search")
startswith(string, "prefix")
endswith(string, "suffix")
replace(string, "old", "new")
lower(string)
upper(string)
length(string)
split(string, ",")
join(list, ", ")
```

## List Functions

```dataview
length(list)
contains(list, item)
all(list, condition)
any(list, condition)
filter(list, condition)
map(list, function)
sort(list)
reverse(list)
flat(nested-list)
```

## Inline Queries

Use prefix `=` for inline queries (configured in vault):

```markdown
Today is `= date(today)`
File count: `= length(filter(file.tasks, (t) => !t.completed))`
```

## DataviewJS

For complex queries, use dataviewjs code blocks:

```dataviewjs
const pages = dv.pages('"06 - Daily"')
  .where(p => p.file.cday >= dv.date('2025-01-01'))
  .sort(p => p.file.cday, 'desc');

dv.table(
  ["Date", "Tasks"],
  pages.map(p => [p.file.link, p.file.tasks.length])
);
```

## Common Patterns

### Recent Daily Notes

```dataview
LIST
FROM "06 - Daily"
WHERE file.cday >= date(today) - dur(7 days)
SORT file.cday DESC
```

### Incomplete Tasks by Project

```dataview
TASK
FROM "01 - Projects"
WHERE !completed
GROUP BY file.link
```

### Notes Modified Today

```dataview
TABLE file.mtime as "Modified"
WHERE file.mday = date(today)
SORT file.mtime DESC
```

### Tag Overview

```dataview
TABLE length(rows) as "Count"
FROM "vault"
FLATTEN file.tags as tag
GROUP BY tag
SORT length(rows) DESC
```

### Notes Created This Month

```dataview
LIST
WHERE file.cday.year = date(today).year
WHERE file.cday.month = date(today).month
SORT file.cday DESC
```
