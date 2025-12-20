#!/bin/bash
#
# Obsidian Vault Management Utilities
# A collection of shell functions for working with Obsidian vaults
#

set -euo pipefail

# Default vault path (override with OBSIDIAN_VAULT env var)
VAULT_PATH="${OBSIDIAN_VAULT:-$HOME/Documents/Obsidian}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[OK]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARN]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

#------------------------------------------------------------------------------
# Vault Operations
#------------------------------------------------------------------------------

# List all notes in vault
vault_list() {
    local vault="${1:-$VAULT_PATH}"

    if [[ ! -d "$vault" ]]; then
        print_error "Vault not found: $vault"
        return 1
    fi

    find "$vault" -name "*.md" -type f ! -path "*/.obsidian/*" | sort
}

# Count notes in vault
vault_count() {
    local vault="${1:-$VAULT_PATH}"

    local count
    count=$(find "$vault" -name "*.md" -type f ! -path "*/.obsidian/*" | wc -l | tr -d ' ')
    echo "Total notes: $count"
}

# Search notes by content
vault_search() {
    local query="$1"
    local vault="${2:-$VAULT_PATH}"

    if [[ -z "$query" ]]; then
        print_error "Usage: vault_search <query> [vault_path]"
        return 1
    fi

    grep -rl "$query" "$vault" --include="*.md" 2>/dev/null | grep -v ".obsidian" || true
}

# Search notes by tag
vault_find_tag() {
    local tag="$1"
    local vault="${2:-$VAULT_PATH}"

    if [[ -z "$tag" ]]; then
        print_error "Usage: vault_find_tag <tag> [vault_path]"
        return 1
    fi

    # Normalize tag (add # if missing)
    [[ "$tag" != "#"* ]] && tag="#$tag"

    grep -rl "$tag" "$vault" --include="*.md" 2>/dev/null | grep -v ".obsidian" || true
}

# List recently modified notes
vault_recent() {
    local days="${1:-7}"
    local vault="${2:-$VAULT_PATH}"

    print_info "Notes modified in last $days days:"
    find "$vault" -name "*.md" -type f -mtime "-$days" ! -path "*/.obsidian/*" -exec ls -lt {} \; | head -20
}

# Find orphan notes (no backlinks)
vault_orphans() {
    local vault="${1:-$VAULT_PATH}"

    print_info "Checking for orphan notes (may take a while)..."

    # Get all markdown files
    local files
    files=$(find "$vault" -name "*.md" -type f ! -path "*/.obsidian/*")

    while IFS= read -r file; do
        local basename
        basename=$(basename "$file" .md)

        # Check if any other file links to this one
        local links
        links=$(grep -rl "\[\[$basename" "$vault" --include="*.md" 2>/dev/null | grep -vc "$file" || echo 0)

        if [[ "$links" -eq 0 ]]; then
            echo "Orphan: $file"
        fi
    done <<< "$files"
}

#------------------------------------------------------------------------------
# Note Operations
#------------------------------------------------------------------------------

# Create a new note
note_create() {
    local name="$1"
    local content="${2:-}"
    local vault="${3:-$VAULT_PATH}"

    if [[ -z "$name" ]]; then
        print_error "Usage: note_create <name> [content] [vault_path]"
        return 1
    fi

    local filepath="$vault/$name.md"

    if [[ -f "$filepath" ]]; then
        print_warning "Note already exists: $filepath"
        return 1
    fi

    # Create directory if needed
    mkdir -p "$(dirname "$filepath")"

    # Create note with optional content
    if [[ -n "$content" ]]; then
        echo "$content" > "$filepath"
    else
        cat > "$filepath" << EOF
---
created: $(date +%Y-%m-%d)
---

# $name

EOF
    fi

    print_success "Created: $filepath"
}

# Read note content
note_read() {
    local name="$1"
    local vault="${2:-$VAULT_PATH}"

    if [[ -z "$name" ]]; then
        print_error "Usage: note_read <name> [vault_path]"
        return 1
    fi

    local filepath="$vault/$name.md"

    if [[ ! -f "$filepath" ]]; then
        # Try finding by name
        filepath=$(find "$vault" -name "$name.md" -type f ! -path "*/.obsidian/*" | head -1)
    fi

    if [[ -f "$filepath" ]]; then
        cat "$filepath"
    else
        print_error "Note not found: $name"
        return 1
    fi
}

# Append to note
note_append() {
    local name="$1"
    local content="$2"
    local vault="${3:-$VAULT_PATH}"

    if [[ -z "$name" || -z "$content" ]]; then
        print_error "Usage: note_append <name> <content> [vault_path]"
        return 1
    fi

    local filepath="$vault/$name.md"

    if [[ ! -f "$filepath" ]]; then
        filepath=$(find "$vault" -name "$name.md" -type f ! -path "*/.obsidian/*" | head -1)
    fi

    if [[ -f "$filepath" ]]; then
        echo "" >> "$filepath"
        echo "$content" >> "$filepath"
        print_success "Appended to: $filepath"
    else
        print_error "Note not found: $name"
        return 1
    fi
}

# Get note frontmatter
note_frontmatter() {
    local name="$1"
    local vault="${2:-$VAULT_PATH}"

    if [[ -z "$name" ]]; then
        print_error "Usage: note_frontmatter <name> [vault_path]"
        return 1
    fi

    local filepath="$vault/$name.md"

    if [[ ! -f "$filepath" ]]; then
        filepath=$(find "$vault" -name "$name.md" -type f ! -path "*/.obsidian/*" | head -1)
    fi

    if [[ -f "$filepath" ]]; then
        # Extract frontmatter between --- markers
        sed -n '/^---$/,/^---$/p' "$filepath" | tail -n +2 | head -n -1
    else
        print_error "Note not found: $name"
        return 1
    fi
}

#------------------------------------------------------------------------------
# Daily Notes
#------------------------------------------------------------------------------

# Create or open today's daily note
daily_note() {
    local vault="${1:-$VAULT_PATH}"
    local folder="${2:-Daily Notes}"
    local format="${3:-%Y-%m-%d}"

    local date
    date=$(date +"$format")

    local filepath="$vault/$folder/$date.md"

    if [[ ! -f "$filepath" ]]; then
        mkdir -p "$vault/$folder"
        cat > "$filepath" << EOF
---
date: $(date +%Y-%m-%d)
type: daily
---

# $(date +"%A, %B %d, %Y")

## Tasks
- [ ]

## Notes

## Journal

EOF
        print_success "Created daily note: $filepath"
    else
        print_info "Daily note exists: $filepath"
    fi

    echo "$filepath"
}

# List daily notes for a date range
daily_list() {
    local days="${1:-7}"
    local vault="${2:-$VAULT_PATH}"
    local folder="${3:-Daily Notes}"

    print_info "Daily notes from last $days days:"
    find "$vault/$folder" -name "*.md" -type f -mtime "-$days" | sort -r
}

#------------------------------------------------------------------------------
# URI Operations
#------------------------------------------------------------------------------

# Open note in Obsidian
obsidian_open() {
    local note="$1"
    local vault="${2:-}"

    if [[ -z "$note" ]]; then
        print_error "Usage: obsidian_open <note> [vault_name]"
        return 1
    fi

    local uri="obsidian://open?"
    [[ -n "$vault" ]] && uri+="vault=$(urlencode "$vault")&"
    uri+="file=$(urlencode "$note")"

    open_uri "$uri"
}

# Create note via URI
obsidian_new() {
    local name="$1"
    local content="${2:-}"
    local vault="${3:-}"

    if [[ -z "$name" ]]; then
        print_error "Usage: obsidian_new <name> [content] [vault_name]"
        return 1
    fi

    local uri="obsidian://new?"
    [[ -n "$vault" ]] && uri+="vault=$(urlencode "$vault")&"
    uri+="name=$(urlencode "$name")"
    [[ -n "$content" ]] && uri+="&content=$(urlencode "$content")"

    open_uri "$uri"
}

# Search in Obsidian
obsidian_search() {
    local query="$1"
    local vault="${2:-}"

    if [[ -z "$query" ]]; then
        print_error "Usage: obsidian_search <query> [vault_name]"
        return 1
    fi

    local uri="obsidian://search?"
    [[ -n "$vault" ]] && uri+="vault=$(urlencode "$vault")&"
    uri+="query=$(urlencode "$query")"

    open_uri "$uri"
}

# Open daily note in Obsidian (requires Daily Notes plugin)
obsidian_daily() {
    local vault="${1:-}"

    local uri="obsidian://daily?"
    [[ -n "$vault" ]] && uri+="vault=$(urlencode "$vault")"

    open_uri "$uri"
}

#------------------------------------------------------------------------------
# Configuration
#------------------------------------------------------------------------------

# Backup vault configuration
config_backup() {
    local vault="${1:-$VAULT_PATH}"
    local backup_dir="${2:-$HOME/obsidian-backup}"

    local timestamp
    timestamp=$(date +%Y%m%d_%H%M%S)
    local backup_path="$backup_dir/config_$timestamp"

    mkdir -p "$backup_path"
    cp -r "$vault/.obsidian" "$backup_path/"

    print_success "Configuration backed up to: $backup_path"
}

# List installed plugins
plugins_list() {
    local vault="${1:-$VAULT_PATH}"
    local config="$vault/.obsidian/community-plugins.json"

    if [[ -f "$config" ]]; then
        print_info "Installed community plugins:"
        cat "$config" | tr -d '[]"' | tr ',' '\n' | sed '/^$/d' | sort
    else
        print_warning "No community plugins file found"
    fi
}

# List enabled core plugins
core_plugins() {
    local vault="${1:-$VAULT_PATH}"
    local config="$vault/.obsidian/core-plugins.json"

    if [[ -f "$config" ]]; then
        print_info "Enabled core plugins:"
        grep -o '"[^"]*": *true' "$config" | sed 's/": *true//' | tr -d '"' | sort
    else
        print_warning "No core plugins file found"
    fi
}

#------------------------------------------------------------------------------
# Helper Functions
#------------------------------------------------------------------------------

# URL encode string
urlencode() {
    local string="$1"
    python3 -c "import urllib.parse; print(urllib.parse.quote('$string', safe=''))"
}

# Open URI (cross-platform)
open_uri() {
    local uri="$1"

    case "$(uname)" in
        Darwin)
            open "$uri"
            ;;
        Linux)
            xdg-open "$uri" 2>/dev/null || gio open "$uri"
            ;;
        MINGW*|MSYS*|CYGWIN*)
            start "" "$uri"
            ;;
        *)
            print_error "Unsupported platform"
            return 1
            ;;
    esac
}

#------------------------------------------------------------------------------
# Main / Help
#------------------------------------------------------------------------------

show_help() {
    cat << EOF
Obsidian Vault Management Utilities

Usage: source obsidian-vault.sh

Environment Variables:
  OBSIDIAN_VAULT    Default vault path (default: ~/Documents/Obsidian)

Vault Operations:
  vault_list [path]              List all notes in vault
  vault_count [path]             Count notes in vault
  vault_search <query> [path]    Search notes by content
  vault_find_tag <tag> [path]    Find notes with tag
  vault_recent [days] [path]     List recently modified notes
  vault_orphans [path]           Find orphan notes

Note Operations:
  note_create <name> [content]   Create new note
  note_read <name>               Read note content
  note_append <name> <content>   Append to note
  note_frontmatter <name>        Extract frontmatter

Daily Notes:
  daily_note [path] [folder]     Create/get today's daily note
  daily_list [days] [path]       List recent daily notes

URI Operations:
  obsidian_open <note> [vault]   Open note in Obsidian
  obsidian_new <name> [content]  Create note via URI
  obsidian_search <query>        Search in Obsidian
  obsidian_daily [vault]         Open daily note

Configuration:
  config_backup [path]           Backup vault configuration
  plugins_list [path]            List installed plugins
  core_plugins [path]            List enabled core plugins

Examples:
  vault_list ~/MyVault
  vault_search "meeting notes"
  vault_find_tag project
  note_create "Projects/NewProject" "# New Project"
  obsidian_open "MyNote" "MyVault"
  daily_note

EOF
}

# Run help if executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    show_help
fi
