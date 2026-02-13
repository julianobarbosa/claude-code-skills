# Search Reference

Complete reference for Atuin's search capabilities — CLI flags, TUI shortcuts, search syntax, and practical patterns.

## CLI Search

```bash
atuin search [OPTIONS] [QUERY]...
```

### Flags

| Flag | Short | Description |
|------|-------|-------------|
| `--cwd <DIR>` | `-c` | Filter by directory (`.` for current) |
| `--exclude-cwd <DIR>` | | Exclude directory |
| `--exit <CODE>` | `-e` | Filter by exit code |
| `--exclude-exit <CODE>` | | Exclude exit code |
| `--before <TIME>` | `-b` | Before timestamp |
| `--after <TIME>` | | After timestamp |
| `--limit <N>` | | Max results |
| `--offset <N>` | | Skip N results |
| `--interactive` | `-i` | Open TUI |
| `--filter-mode <MODE>` | | Override filter mode |
| `--search-mode <MODE>` | | Override search mode |
| `--keymap-mode <MODE>` | | Override keymap |
| `--human` | | Human-readable timestamps |
| `--cmd-only` | | Command text only |
| `--print0` | | Null-terminate output |
| `--delete` | | Delete matching entries |
| `--delete-it-all` | | Delete ALL history |
| `--reverse` | `-r` | Oldest first |
| `--timezone <TZ>` | | Display timezone |
| `--format <FMT>` | `-f` | Custom format string |
| `--inline-height <N>` | | Max TUI lines |
| `--include-duplicates` | | Include duplicate commands |

### Format Variables

Use with `--format` / `-f`:

| Variable | Description |
|----------|-------------|
| `{command}` | The command text |
| `{directory}` | Working directory |
| `{duration}` | Execution duration |
| `{user}` | Username |
| `{host}` | Hostname |
| `{time}` | Timestamp |
| `{exit}` | Exit code |
| `{relativetime}` | Relative time (e.g., "5m ago") |
| `{session}` | Session ID |
| `{uuid}` | Entry UUID |

### Time Expressions

The `--before` and `--after` flags accept natural language:

```bash
"yesterday 3pm"
"last friday"
"2024-04-01"
"April 1"
"01/04/22"          # US=Jan 4, UK=Apr 1 (depends on dialect setting)
"last thursday 3pm"
```

## TUI Keyboard Shortcuts

### Navigation

| Key | Action |
|-----|--------|
| `Up` / `Down` | Navigate results |
| `Page Up` / `Page Down` | Scroll by page |
| `Home` / `End` | Jump to start/end of input |

### Actions

| Key | Action |
|-----|--------|
| `Enter` | Execute selected command (if `enter_accept = true`) |
| `Tab` | Insert into shell for editing |
| `Ctrl+R` | Cycle filter modes (global -> host -> session -> directory -> workspace) |
| `Ctrl+S` | Cycle search modes (fuzzy -> prefix -> fulltext -> skim) |
| `Alt+1`-`Alt+9` | Quick select by number |
| `Ctrl+Y` | Copy to clipboard |
| `Ctrl+O` | Open inspector |
| `Ctrl+U` | Clear search line |
| `Ctrl+C` / `Ctrl+D` / `Esc` | Exit TUI |

### Inspector Mode

| Key | Action |
|-----|--------|
| `Ctrl+O` | Enter inspector |
| `Arrow keys` / `j`/`k` | Navigate metadata |
| `Ctrl+D` | Delete inspected entry |
| `Esc` | Exit inspector |

### Vim Mode (when `keymap_mode = "vim-normal"`)

| Key | Action |
|-----|--------|
| `k` / `j` | Navigate up/down |
| `h` / `l` | Cursor left/right |
| `0` / `$` | Start/end of line |
| `w` / `b` / `e` | Word navigation |
| `dd` / `D` / `C` | Delete operations |
| `gg` / `G` | Jump to top/bottom |
| `Ctrl+u` / `Ctrl+d` | Half page up/down |
| `Ctrl+b` / `Ctrl+f` | Full page up/down |
| `H` / `M` / `L` | High/middle/low in viewport |

## Practical Search Patterns

### Find Successful Commands

```bash
atuin search --exit 0 make
atuin search --exit 0 --after "yesterday 3pm" cargo build
```

### Find Failed Commands

```bash
atuin search --exclude-exit 0 --cwd .
atuin search --exit 1 "docker build"
```

### Directory-Scoped Search

```bash
atuin search --cwd /path/to/project git
atuin search --exclude-cwd /tmp
```

### Custom Output Formats

```bash
atuin search -f "{time} [{duration}] [{exit}] {directory}\t{command}" git
atuin search --cmd-only docker
atuin search --cmd-only --print0 "npm run" | xargs -0 echo
```

### History Maintenance

```bash
atuin search --delete "^rm -rf /"
atuin search --delete "password="
atuin search --limit 1 --reverse ""    # Oldest command
atuin history dedup
atuin history prune --dry-run
atuin history prune
```

### History Listing

```bash
atuin history list --human
atuin history list --cwd
atuin history list --session
atuin history list -f "{time} {duration} {command}"
atuin history last
```

### Statistics

```bash
atuin stats
atuin stats -c 20
atuin stats "last week"
atuin stats "last friday"
atuin stats -n 2    # N-gram pairs
atuin stats -n 3    # N-gram triplets
```

## Wildcard Search

Atuin supports `*` and `%` as wildcards in search queries. Prefix search mode auto-appends a wildcard.
