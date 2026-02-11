# Obsidian Bases Reference

Bases are YAML-based `.base` files that define dynamic views of vault notes.

## Complete Schema

```yaml
filters:          # Global filters (all views)
  and: []
  or: []
  not: []

formulas:         # Computed properties
  name: 'expression'

properties:       # Display config
  property_name:
    displayName: "Display Name"
  formula.name:
    displayName: "Formula Name"

summaries:        # Custom summary formulas
  name: 'values.mean().round(3)'

views:            # One or more views
  - type: table | cards | list | map
    name: "View Name"
    limit: 10
    groupBy:
      property: property_name
      direction: ASC | DESC
    filters:      # View-specific filters
      and: []
    order:        # Properties to display
      - file.name
      - property_name
      - formula.name
    summaries:    # Property -> summary mapping
      property_name: Average
```

## Filter Syntax

### Operators

| Operator | Description |
|----------|-------------|
| `==`, `!=` | Equality |
| `>`, `<`, `>=`, `<=` | Comparison |
| `&&`, `\|\|`, `!` | Logical |

### Examples

```yaml
# Single
filters: 'status == "done"'

# AND
filters:
  and:
    - 'status == "done"'
    - 'priority > 3'

# OR
filters:
  or:
    - file.hasTag("book")
    - file.hasTag("article")

# NOT
filters:
  not:
    - file.hasTag("archived")

# Nested
filters:
  or:
    - file.hasTag("tag")
    - and:
        - file.hasTag("book")
        - file.hasLink("Textbook")
    - not:
        - file.hasTag("book")
        - file.inFolder("Required Reading")
```

## Properties

### Three Types

1. **Note properties** - From frontmatter: `author` or `note.author`
2. **File properties** - File metadata: `file.name`, `file.mtime`, etc.
3. **Formula properties** - Computed: `formula.my_formula`

### File Properties

| Property | Type | Description |
|----------|------|-------------|
| `file.name` | String | File name |
| `file.basename` | String | Name without extension |
| `file.path` | String | Full path |
| `file.folder` | String | Parent folder |
| `file.ext` | String | Extension |
| `file.size` | Number | Size in bytes |
| `file.ctime` | Date | Created time |
| `file.mtime` | Date | Modified time |
| `file.tags` | List | All tags |
| `file.links` | List | Internal links |
| `file.backlinks` | List | Files linking to this |
| `file.embeds` | List | Embeds in note |
| `file.properties` | Object | All frontmatter |

### The `this` Keyword

- In main content: refers to base file itself
- When embedded: refers to embedding file
- In sidebar: refers to active file

## Formula Syntax

```yaml
formulas:
  total: "price * quantity"
  status_icon: 'if(done, "done", "pending")'
  formatted: 'if(price, price.toFixed(2) + " dollars")'
  created: 'file.ctime.format("YYYY-MM-DD")'
  days_old: '((now() - file.ctime) / 86400000).round(0)'
```

## Functions Reference

### Global Functions

| Function | Description |
|----------|-------------|
| `date(string)` | Parse string to date |
| `duration(string)` | Parse duration |
| `now()` | Current date+time |
| `today()` | Current date (00:00) |
| `if(cond, true, false?)` | Conditional |
| `min(n1, n2, ...)` | Minimum |
| `max(n1, n2, ...)` | Maximum |
| `number(any)` | Convert to number |
| `link(path, display?)` | Create link |
| `list(element)` | Wrap in list |
| `file(path)` | Get file object |
| `image(path)` | Create image |
| `icon(name)` | Lucide icon |
| `html(string)` | Render HTML |
| `escapeHTML(string)` | Escape HTML |

### Date Functions

Fields: `.year`, `.month`, `.day`, `.hour`, `.minute`, `.second`, `.millisecond`

| Function | Description |
|----------|-------------|
| `date.format(pattern)` | Format (Moment.js) |
| `date.relative()` | Human-readable relative |
| `date.time()` | Time as string |
| `date.date()` | Remove time portion |

### Date Arithmetic

```yaml
"date + \"1M\""         # Add 1 month
"date - \"2h\""         # Subtract 2 hours
"now() + \"1 day\""     # Tomorrow
"today() + \"7d\""      # Week from today
"now() - file.ctime"    # Milliseconds since creation
```

Duration units: `y/year/years`, `M/month/months`, `d/day/days`, `w/week/weeks`, `h/hour/hours`, `m/minute/minutes`, `s/second/seconds`

### String Functions

Field: `.length`

`contains()`, `containsAll()`, `containsAny()`, `startsWith()`, `endsWith()`, `isEmpty()`, `lower()`, `title()`, `trim()`, `replace()`, `repeat()`, `reverse()`, `slice()`, `split()`

### Number Functions

`abs()`, `ceil()`, `floor()`, `round(digits?)`, `toFixed(precision)`, `isEmpty()`

### List Functions

Field: `.length`

`contains()`, `containsAll()`, `containsAny()`, `filter(expr)`, `map(expr)`, `reduce(expr, init)`, `flat()`, `join(sep)`, `reverse()`, `slice()`, `sort()`, `unique()`, `isEmpty()`

Filter/map/reduce use: `value`, `index`, `acc` (reduce only)

### File Functions

`asLink(display?)`, `hasLink(file)`, `hasTag(...tags)`, `hasProperty(name)`, `inFolder(folder)`

### Link Functions

`asFile()`, `linksTo(file)`

## View Types

### Table

```yaml
views:
  - type: table
    name: "Tasks"
    order: [file.name, status, due_date]
    summaries:
      price: Sum
```

### Cards

```yaml
views:
  - type: cards
    name: "Gallery"
    order: [cover, file.name, description]
```

### List

```yaml
views:
  - type: list
    name: "Simple"
    order: [file.name, status]
```

### Map

Requires lat/lng properties and Maps plugin.

## Default Summary Formulas

**Number**: Average, Min, Max, Sum, Range, Median, Stddev
**Date**: Earliest, Latest, Range
**Boolean**: Checked, Unchecked
**Any**: Empty, Filled, Unique

## Common Patterns

```yaml
# By tag
filters:
  and: [file.hasTag("project")]

# By folder
filters:
  and: [file.inFolder("Notes")]

# By date range
filters:
  and: ['file.mtime > now() - "7d"']

# By property
filters:
  and: ['status == "active"', 'priority >= 3']
```

## Embedding

```markdown
![[MyBase.base]]
![[MyBase.base#View Name]]
```

## YAML Quoting

- Single quotes for formulas with double quotes: `'if(done, "Yes", "No")'`
- Double quotes for simple strings: `"My View"`

## References

- [Bases Syntax](https://help.obsidian.md/bases/syntax)
- [Functions](https://help.obsidian.md/bases/functions)
- [Views](https://help.obsidian.md/bases/views)
- [Formulas](https://help.obsidian.md/formulas)
