# ShellCheck Configuration Reference

Complete guide to configuring ShellCheck behavior.

## Configuration Methods

ShellCheck can be configured through multiple methods (in order of precedence):

1. **Command-line flags** - Highest precedence
2. **Inline directives** - Per-command or file-wide
3. **Configuration file** (`.shellcheckrc`) - Project or user-wide
4. **Environment variable** (`SHELLCHECK_OPTS`) - System-wide defaults

## Configuration File (.shellcheckrc)

### File Locations

ShellCheck searches for configuration in this order:

1. **Script's directory** - `.shellcheckrc` or `shellcheckrc`
2. **Parent directories** - Walking up to root
3. **Home directory** - `~/.shellcheckrc`
4. **XDG config** - `~/.config/shellcheckrc` (Unix)
5. **AppData** - `%APPDATA%/shellcheckrc` (Windows)

Only the first file found is used.

### File Format

```bash
# Comments start with #
key=value
key=value with spaces
key="quoted value"
key='single quoted'
```

### Example .shellcheckrc

```bash
# Project-wide ShellCheck configuration

# Shell dialect (sh, bash, dash, ksh, busybox)
shell=bash

# Source file handling
source-path=SCRIPTDIR
source-path=SCRIPTDIR/lib
source-path=/usr/local/lib/myproject

# Allow following source statements
external-sources=true

# Enable extended dataflow analysis
extended-analysis=true

# Enable optional checks
enable=quote-safe-variables
enable=check-unassigned-uppercase
enable=require-variable-braces
enable=deprecate-which

# Disable specific warnings
disable=SC2059  # printf format string variable
disable=SC2034  # Unused variable (false positives)
disable=SC1090  # Can't follow non-constant source
disable=SC1091  # Not following sourced file
```

### Minimal Project .shellcheckrc

```bash
# Minimum recommended configuration
shell=bash
source-path=SCRIPTDIR
external-sources=true
enable=deprecate-which
```

## Inline Directives

### Syntax

```bash
# shellcheck key=value
```

### Placement Rules

| Placement | Scope |
|-----------|-------|
| After shebang | Entire file |
| Before command | Next complete command only |
| Before function | Entire function |
| Before loop/if | Entire block |

### Available Directive Keys

#### disable

Suppress specific warnings:

```bash
# Single code
# shellcheck disable=SC2086
echo $var

# Multiple codes
# shellcheck disable=SC2086,SC2046
files=$(ls *.txt)

# Range of codes
# shellcheck disable=SC1090-SC1100

# All warnings (v0.8+)
# shellcheck disable=all
```

#### enable

Activate optional checks:

```bash
#!/bin/bash
# shellcheck enable=require-variable-braces
# shellcheck enable=quote-safe-variables
```

#### shell

Specify shell dialect:

```bash
#!/bin/sh
# shellcheck shell=bash
# Script uses bash features despite sh shebang
```

#### source

Override sourced file location:

```bash
# Skip sourcing (use /dev/null)
# shellcheck source=/dev/null
source "$CONFIG_FILE"

# Specify actual location
# shellcheck source=./lib/common.sh
source "$LIB_DIR/common.sh"

# Use script directory
# shellcheck source=SCRIPTDIR/lib/utils.sh
source "$(dirname "$0")/lib/utils.sh"
```

#### source-path

Add search paths for sourced files:

```bash
# shellcheck source-path=SCRIPTDIR
# shellcheck source-path=SCRIPTDIR/../lib
# shellcheck source-path=/usr/local/lib
```

#### external-sources

Allow following arbitrary source statements:

```bash
# Can ONLY be set in .shellcheckrc, not inline
external-sources=true
```

#### extended-analysis

Toggle dataflow analysis (for performance on large files):

```bash
# Disable for auto-generated scripts
# shellcheck extended-analysis=false
```

## Command-Line Options

### Analysis Options

```bash
# Specify shell dialect
shellcheck -s bash script.sh
shellcheck --shell=bash script.sh

# Include sourced file warnings
shellcheck -a script.sh
shellcheck --check-sourced script.sh

# Follow external sources
shellcheck -x script.sh
shellcheck --external-sources script.sh

# Source search paths
shellcheck -P ./lib:./src script.sh
shellcheck --source-path=./lib:./src script.sh
```

### Filtering Options

```bash
# Exclude codes
shellcheck -e SC2086,SC2046 script.sh
shellcheck --exclude=SC2086,SC2046 script.sh

# Include only specific codes
shellcheck -i SC2086 script.sh
shellcheck --include=SC2086 script.sh

# Enable optional checks
shellcheck -o require-variable-braces script.sh
shellcheck --enable=require-variable-braces script.sh
shellcheck -o all script.sh  # Enable all optional

# Minimum severity
shellcheck -S error script.sh      # Only errors
shellcheck -S warning script.sh    # Errors + warnings
shellcheck -S info script.sh       # Errors + warnings + info
shellcheck -S style script.sh      # All (default)
shellcheck --severity=warning script.sh
```

### Output Options

```bash
# Output format
shellcheck -f tty script.sh        # Human-readable (default)
shellcheck -f gcc script.sh        # GCC format for editors
shellcheck -f checkstyle script.sh # XML for CI tools
shellcheck -f diff script.sh       # Unified diff for auto-fix
shellcheck -f json script.sh       # JSON (legacy)
shellcheck -f json1 script.sh      # JSON (compact)
shellcheck -f quiet script.sh      # Exit code only
shellcheck --format=gcc script.sh

# Color control
shellcheck -C always script.sh
shellcheck -C never script.sh
shellcheck -C auto script.sh
shellcheck --color=always script.sh

# Wiki links
shellcheck -W 3 script.sh          # Show 3 wiki links
shellcheck -W 0 script.sh          # Disable wiki links
shellcheck --wiki-link-count=3 script.sh
```

### Configuration Options

```bash
# Skip .shellcheckrc
shellcheck --norc script.sh

# Use specific config file
shellcheck --rcfile=./custom.shellcheckrc script.sh

# Extended analysis control
shellcheck --extended-analysis=true script.sh
shellcheck --extended-analysis=false script.sh

# List optional checks
shellcheck --list-optional
```

## Environment Variable

Set default options via `SHELLCHECK_OPTS`:

```bash
# In ~/.bashrc or ~/.zshrc
export SHELLCHECK_OPTS='--shell=bash --exclude=SC2016 --enable=deprecate-which'

# One-time override
SHELLCHECK_OPTS='-x -S warning' shellcheck script.sh
```

## Optional Checks

List available with `shellcheck --list-optional`:

| Check Name | Description |
|------------|-------------|
| `add-default-case` | Suggest default `*)` in case statements |
| `avoid-negated-conditions` | Suggest removing unnecessary negations |
| `avoid-nullary-conditions` | Explicitly use `-n` in conditions |
| `check-extra-masked-returns` | More masked return value checks |
| `check-set-e-suppressed` | Warn when `set -e` is suppressed |
| `check-unassigned-uppercase` | Warn about uninitialized uppercase vars |
| `deprecate-which` | Suggest `command -v` over `which` |
| `quote-safe-variables` | Suggest quoting even safe variables |
| `require-double-brackets` | Require `[[` over `[` in Bash |
| `require-variable-braces` | Require `${var}` over `$var` |

### Enabling Optional Checks

```bash
# Command line
shellcheck -o deprecate-which,require-variable-braces script.sh
shellcheck -o all script.sh  # Enable all

# .shellcheckrc
enable=deprecate-which
enable=require-variable-braces

# Inline (file-wide only)
#!/bin/bash
# shellcheck enable=require-variable-braces
```

## Platform-Specific Notes

### Snap Users

The Snap sandbox blocks hidden files. Use `shellcheckrc` (no dot):

```bash
# Instead of .shellcheckrc
mv .shellcheckrc shellcheckrc
```

### Docker Users

Mount config files explicitly:

```bash
docker run --rm \
  -v "$PWD:/mnt" \
  -v "$HOME/.shellcheckrc:/root/.shellcheckrc:ro" \
  koalaman/shellcheck /mnt/script.sh
```

Or use environment variable:

```bash
docker run --rm \
  -e SHELLCHECK_OPTS='--shell=bash' \
  -v "$PWD:/mnt" \
  koalaman/shellcheck /mnt/script.sh
```
