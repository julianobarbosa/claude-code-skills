# Analyze Workflow

Analyze shell scripts with ShellCheck and present findings.

## Trigger

- "shellcheck this script"
- "lint my shell script"
- "check for shell errors"
- "analyze bash script"

## Process

### 1. Identify Scripts

Find shell scripts to analyze:

```bash
# Single file provided
shellcheck "$FILE"

# Find all scripts in directory
find . -type f \( -name "*.sh" -o -name "*.bash" -o -name "*.zsh" \) ! -path "./.git/*"

# Or detect by shebang
find . -type f ! -path "./.git/*" -exec sh -c '
    head -1 "$1" | grep -qE "^#!.*(bash|sh|zsh|ksh)" && echo "$1"
' _ {} \;
```

### 2. Run ShellCheck

```bash
# JSON output for parsing
shellcheck -f json "$SCRIPTS" 2>/dev/null

# GCC format for quick viewing
shellcheck -f gcc "$SCRIPTS"

# With all optional checks enabled
shellcheck -o all -f json "$SCRIPTS"
```

### 3. Parse and Present Results

Group findings by severity:

```bash
# Count by severity
shellcheck -f json script.sh | jq 'group_by(.level) | map({level: .[0].level, count: length})'
```

### 4. Output Format

Present findings in structured format:

```markdown
## ShellCheck Analysis: script.sh

### Summary
- **Errors:** 2
- **Warnings:** 5
- **Info:** 3
- **Style:** 1

### Findings

#### Errors (Must Fix)

**SC2086** (line 15): Double quote to prevent globbing and word splitting.
```bash
# Line 15
echo $variable
# Fix
echo "$variable"
```
[Wiki: SC2086](https://www.shellcheck.net/wiki/SC2086)

#### Warnings

**SC2046** (line 23): Quote this to prevent word splitting.
```bash
# Line 23
files=$(ls *.txt)
# Fix
files="$(ls *.txt)"
```
[Wiki: SC2046](https://www.shellcheck.net/wiki/SC2046)

### Quick Fixes

Apply auto-fixes with:
```bash
shellcheck -f diff script.sh | patch -p1
```
```

## Example Invocations

```bash
# Basic analysis
shellcheck script.sh

# Strict analysis (all checks)
shellcheck -o all -S warning script.sh

# Check multiple files
shellcheck scripts/*.sh

# Recursive directory
find . -name "*.sh" -exec shellcheck {} +

# With specific shell
shellcheck -s bash script.sh
```

## Integration with Workflows

After analysis, suggest:

1. **Auto-fix available issues:**
   ```bash
   shellcheck -f diff script.sh | patch -p1
   ```

2. **Configure suppressions** for false positives

3. **Set up pre-commit hook** for continuous validation
