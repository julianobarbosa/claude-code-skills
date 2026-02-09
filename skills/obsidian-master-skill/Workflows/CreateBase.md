# Workflow: Create Base

Create and edit Obsidian `.base` database view files.

## Steps

1. **Define purpose** - What data to view? (tasks, projects, reading list, etc.)
2. **Design filters** - Which notes to include (tags, folders, properties)
3. **Design formulas** - Computed columns needed
4. **Choose view type** - table, cards, list, or map
5. **Generate .base YAML** via `Tools/BaseBuilder.py create`
6. **Validate** the generated YAML
7. **Place file** in appropriate folder

## Tool Usage

```bash
# Create a project tracker base
python Tools/BaseBuilder.py create \
  --name "Active Projects" \
  --filter 'file.inFolder("01 - Projects") && status != "completed"' \
  --view table \
  --columns "file.name,status,priority,due" \
  --output "01 - Projects/projects.base"

# Create with formulas
python Tools/BaseBuilder.py create \
  --name "Task Dashboard" \
  --filter 'file.hasTag("task")' \
  --view table \
  --formula 'days_until_due=if(due, ((date(due) - today()) / 86400000).round(0), "")' \
  --formula 'priority_label=if(priority == 1, "High", if(priority == 2, "Medium", "Low"))' \
  --columns "file.name,status,formula.priority_label,due,formula.days_until_due"

# Validate existing base file
python Tools/BaseBuilder.py validate \
  --path "01 - Projects/projects.base"

# Preview (dry run)
python Tools/BaseBuilder.py preview \
  --filter 'file.hasTag("book")' \
  --view cards \
  --columns "cover,file.name,author,status"
```

### Options

| Flag | Description |
|------|-------------|
| `--name` | View name |
| `--filter` | Filter expression (can use `&&`, `\|\|`) |
| `--view` | `table`, `cards`, `list`, `map` |
| `--columns` | Comma-separated property list |
| `--formula` | `name=expression` (repeatable) |
| `--group-by` | Property to group by |
| `--sort` | Sort direction: `ASC`, `DESC` |
| `--limit` | Max results |
| `--summary` | `property=SummaryType` (repeatable) |
| `--output` | Output file path |

## Context Files

- `BasesReference.md` - Complete .base schema, filters, formulas, functions
