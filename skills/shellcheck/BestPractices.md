# ShellCheck Best Practices

Comprehensive guide to writing clean, maintainable shell scripts.

## The Top 10 Rules

### 1. Always Quote Variables

```bash
# Bad - word splitting and globbing
echo $filename
rm $file

# Good - prevents issues
echo "$filename"
rm "$file"

# Exception: inside [[ ]] for pattern matching
[[ $string == pattern* ]]
```

### 2. Use `$()` Instead of Backticks

```bash
# Bad - hard to nest, hard to read
files=`ls`
date=`date +%Y-\`date +%m\``

# Good - clear nesting
files=$(ls)
date=$(date +%Y-$(date +%m))
```

### 3. Use `[[` Instead of `[` in Bash

```bash
# Bad - quoting required, no pattern matching
[ "$var" = "value" ]
[ -n "$var" -a -f "$file" ]

# Good - safer, more features
[[ $var == "value" ]]
[[ -n $var && -f $file ]]
[[ $string =~ ^[0-9]+$ ]]  # Regex support
```

### 4. Use `set -euo pipefail`

```bash
#!/bin/bash
set -euo pipefail

# -e: Exit on error
# -u: Error on unset variables
# -o pipefail: Pipeline fails if any command fails
```

### 5. Declare and Assign Separately

```bash
# Bad - masks return value
local output=$(command_that_might_fail)

# Good - captures return value
local output
output=$(command_that_might_fail) || handle_error
```

### 6. Use Arrays for Lists

```bash
# Bad - word splitting issues
files="file1.txt file2.txt file with spaces.txt"
for f in $files; do
    process "$f"
done

# Good - proper array handling
files=("file1.txt" "file2.txt" "file with spaces.txt")
for f in "${files[@]}"; do
    process "$f"
done
```

### 7. Use `"$@"` for Arguments

```bash
# Bad - loses quoting
wrapper() {
    command $@
}

# Good - preserves quoting
wrapper() {
    command "$@"
}
```

### 8. Handle Errors Explicitly

```bash
# Bad - continues on failure
cd /some/directory
rm -rf *

# Good - explicit error handling
cd /some/directory || { echo "cd failed" >&2; exit 1; }
rm -rf ./*

# Or with trap
trap 'echo "Error on line $LINENO" >&2' ERR
```

### 9. Use `command -v` Instead of `which`

```bash
# Bad - non-standard, varies by system
if which git > /dev/null; then
    ...
fi

# Good - POSIX compliant
if command -v git > /dev/null 2>&1; then
    ...
fi
```

### 10. Use Parameter Expansion

```bash
# Bad - external commands
filename=$(basename "$path")
dirname=$(dirname "$path")
extension=$(echo "$file" | sed 's/.*\.//')

# Good - built-in parameter expansion
filename=${path##*/}
dirname=${path%/*}
extension=${file##*.}
```

## Common Anti-Patterns

### Parsing `ls` Output

```bash
# Bad - breaks on special characters
for file in $(ls); do
    process "$file"
done

# Good - use globs
for file in *; do
    [[ -f $file ]] && process "$file"
done

# Or find with -print0
while IFS= read -r -d '' file; do
    process "$file"
done < <(find . -type f -print0)
```

### Using `cat` Unnecessarily

```bash
# Bad - useless use of cat (UUOC)
cat file | grep pattern
cat file | wc -l

# Good - direct input
grep pattern file
wc -l < file
```

### Testing with `$?`

```bash
# Bad - indirect check
command
if [ $? -eq 0 ]; then
    echo "success"
fi

# Good - direct check
if command; then
    echo "success"
fi
```

### Unquoted Variables in Tests

```bash
# Bad - breaks if empty
if [ -n $var ]; then
    ...
fi

# Good - properly quoted
if [[ -n $var ]]; then
    ...
fi
```

### Read Without `-r`

```bash
# Bad - backslashes interpreted
while read line; do
    echo "$line"
done < file

# Good - raw read
while IFS= read -r line; do
    echo "$line"
done < file
```

## Script Template

```bash
#!/usr/bin/env bash
#
# Script: myscript.sh
# Description: Brief description
# Usage: myscript.sh [options] <arguments>
#

set -euo pipefail

# Constants
readonly SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_NAME="$(basename "${BASH_SOURCE[0]}")"

# Default values
VERBOSE=${VERBOSE:-false}
DRY_RUN=${DRY_RUN:-false}

# Colors (if terminal)
if [[ -t 1 ]]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[0;33m'
    NC='\033[0m'
else
    RED=''
    GREEN=''
    YELLOW=''
    NC=''
fi

# Logging functions
log_info() { echo -e "${GREEN}[INFO]${NC} $*"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $*" >&2; }
log_error() { echo -e "${RED}[ERROR]${NC} $*" >&2; }
die() { log_error "$*"; exit 1; }

# Usage/help
usage() {
    cat << EOF
Usage: $SCRIPT_NAME [options] <arguments>

Description of what this script does.

Options:
    -h, --help      Show this help message
    -v, --verbose   Enable verbose output
    -n, --dry-run   Show what would be done

Examples:
    $SCRIPT_NAME --verbose /path/to/file
    $SCRIPT_NAME -n

EOF
}

# Parse arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                usage
                exit 0
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -n|--dry-run)
                DRY_RUN=true
                shift
                ;;
            --)
                shift
                break
                ;;
            -*)
                die "Unknown option: $1"
                ;;
            *)
                break
                ;;
        esac
    done

    # Remaining arguments
    ARGS=("$@")
}

# Cleanup function
cleanup() {
    # Remove temp files, restore state, etc.
    :
}

# Main function
main() {
    trap cleanup EXIT

    parse_args "$@"

    [[ $VERBOSE == true ]] && log_info "Verbose mode enabled"
    [[ $DRY_RUN == true ]] && log_warn "Dry-run mode - no changes will be made"

    # Your main logic here
    if [[ ${#ARGS[@]} -eq 0 ]]; then
        die "No arguments provided"
    fi

    for arg in "${ARGS[@]}"; do
        log_info "Processing: $arg"
    done
}

main "$@"
```

## Quoting Reference

| Context | Quote? | Example |
|---------|--------|---------|
| Variable assignment | No | `var=$other` |
| Variable in string | Yes | `echo "Hello $name"` |
| Variable as argument | Yes | `command "$var"` |
| Array element | Yes | `"${array[0]}"` |
| All array elements | Yes | `"${array[@]}"` |
| Command substitution | Yes | `var="$(command)"` |
| Arithmetic | No | `$((x + 1))` |
| Inside `[[ ]]` | Usually no | `[[ $var == pattern ]]` |
| Inside `[ ]` | Yes | `[ "$var" = "value" ]` |
| Glob patterns | No | `for f in *.txt` |

## Parameter Expansion Cheat Sheet

| Expansion | Description |
|-----------|-------------|
| `${var:-default}` | Use default if unset/null |
| `${var:=default}` | Set to default if unset/null |
| `${var:?error}` | Error if unset/null |
| `${var:+alt}` | Use alt if set |
| `${#var}` | String length |
| `${var#pattern}` | Remove shortest prefix match |
| `${var##pattern}` | Remove longest prefix match |
| `${var%pattern}` | Remove shortest suffix match |
| `${var%%pattern}` | Remove longest suffix match |
| `${var/pat/rep}` | Replace first match |
| `${var//pat/rep}` | Replace all matches |
| `${var^}` | Uppercase first char |
| `${var^^}` | Uppercase all |
| `${var,}` | Lowercase first char |
| `${var,,}` | Lowercase all |
| `${var:pos:len}` | Substring |

## Test Operators Cheat Sheet

### File Tests

| Test | Description |
|------|-------------|
| `-e file` | Exists |
| `-f file` | Regular file |
| `-d file` | Directory |
| `-L file` | Symbolic link |
| `-r file` | Readable |
| `-w file` | Writable |
| `-x file` | Executable |
| `-s file` | Size > 0 |
| `f1 -nt f2` | f1 newer than f2 |
| `f1 -ot f2` | f1 older than f2 |

### String Tests

| Test | Description |
|------|-------------|
| `-z string` | Empty |
| `-n string` | Not empty |
| `s1 = s2` | Equal |
| `s1 != s2` | Not equal |
| `s1 < s2` | Less than (lexical) |
| `s1 > s2` | Greater than (lexical) |

### Numeric Tests

| Test | Description |
|------|-------------|
| `n1 -eq n2` | Equal |
| `n1 -ne n2` | Not equal |
| `n1 -lt n2` | Less than |
| `n1 -le n2` | Less or equal |
| `n1 -gt n2` | Greater than |
| `n1 -ge n2` | Greater or equal |

## ShellCheck Workflow

### Development Phase

1. **Write code** with editor integration (real-time feedback)
2. **Run shellcheck** before committing
3. **Fix issues** or add justified suppressions

### CI Phase

1. **Pre-commit hook** catches issues before push
2. **CI pipeline** enforces standards
3. **Quality gates** prevent merging broken scripts

### Suppression Guidelines

Only suppress when:
- False positive (rare)
- Intentional behavior (document why)
- External variable (sourced from elsewhere)

Always add a comment:

```bash
# shellcheck disable=SC2034 # Variable used by sourced scripts
readonly CONFIG_PATH="/etc/myapp"

# Intentionally unquoted for word splitting
# shellcheck disable=SC2086
flags=$USER_FLAGS
```

## Resources

- [ShellCheck Wiki](https://www.shellcheck.net/wiki/)
- [Google Shell Style Guide](https://google.github.io/styleguide/shellguide.html)
- [Bash Pitfalls](https://mywiki.wooledge.org/BashPitfalls)
- [Pure Bash Bible](https://github.com/dylanaraps/pure-bash-bible)
