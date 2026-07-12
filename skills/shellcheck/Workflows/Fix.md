# Fix Workflow

Apply ShellCheck fixes to shell scripts.

## Trigger

- "fix shellcheck errors"
- "apply shellcheck fixes"
- "auto-fix shell script"
- "fix SC2086"

## Process

### 1. Generate Diff

```bash
# Generate unified diff for all fixable issues
shellcheck -f diff script.sh > fixes.patch

# Preview changes
cat fixes.patch
```

### 2. Review Fixes

Present the diff to user for review:

```bash
# Show with color
diff -u original.sh fixed.sh | colordiff

# Or use git diff
git diff --no-index original.sh fixed.sh
```

### 3. Apply Fixes

**Option A: Apply patch**
```bash
shellcheck -f diff script.sh | patch -p1
```

**Option B: Apply with git**
```bash
shellcheck -f diff script.sh | git apply
```

**Option C: Selective application**
```bash
# Apply only specific files
shellcheck -f diff script.sh | patch -p1 --dry-run  # Preview
shellcheck -f diff script.sh | patch -p1            # Apply
```

### 4. Verify Fixes

```bash
# Re-run shellcheck to confirm
shellcheck script.sh

# Should show fewer/no issues
echo "Exit code: $?"  # 0 = clean
```

## Common Fixes

### SC2086 - Quote Variables

**Before:**
```bash
echo $variable
rm $files
```

**After:**
```bash
echo "$variable"
rm "$files"
```

### SC2046 - Quote Command Substitution

**Before:**
```bash
files=$(find . -name "*.txt")
```

**After:**
```bash
files="$(find . -name "*.txt")"
```

### SC2006 - Use $() Instead of Backticks

**Before:**
```bash
date=`date +%Y-%m-%d`
```

**After:**
```bash
date=$(date +%Y-%m-%d)
```

### SC2155 - Declare and Assign Separately

**Before:**
```bash
local output=$(command)
```

**After:**
```bash
local output
output=$(command)
```

### SC2164 - Add || exit After cd

**Before:**
```bash
cd /some/directory
rm -rf *
```

**After:**
```bash
cd /some/directory || exit 1
rm -rf ./*
```

## Batch Fix Multiple Files

```bash
#!/bin/bash
# fix-all-scripts.sh

set -euo pipefail

# Find all shell scripts
scripts=$(find . -name "*.sh" -o -name "*.bash" | grep -v ".git")

for script in $scripts; do
    echo "Fixing: $script"

    # Generate and apply fixes
    if diff=$(shellcheck -f diff "$script" 2>/dev/null); then
        if [[ -n "$diff" ]]; then
            echo "$diff" | patch -p1
            echo "  Applied fixes"
        else
            echo "  No fixes needed"
        fi
    else
        echo "  Error running shellcheck"
    fi
done

echo "Done. Re-running shellcheck..."
find . -name "*.sh" -exec shellcheck {} + || true
```

## Manual Fix Patterns

When auto-fix isn't available:

### Array Expansion

```bash
# Bad: SC2068
process ${array[@]}

# Good
process "${array[@]}"
```

### Read Without -r

```bash
# Bad: SC2162
while read line; do

# Good
while IFS= read -r line; do
```

### Test Command

```bash
# Bad: SC2070
[ -n $var ]

# Good
[[ -n $var ]]
```

## Output Format

After applying fixes, report:

```markdown
## Fixes Applied

**Script:** deploy.sh

| Line | Code | Fix Applied |
|------|------|-------------|
| 15 | SC2086 | Quoted `$variable` |
| 23 | SC2046 | Quoted command substitution |
| 45 | SC2006 | Replaced backticks with `$()` |

**Remaining Issues:**
- SC2034 (line 8): Variable appears unused - manual review needed
- SC1090 (line 3): Can't follow dynamic source - add directive

**Commands:**
```bash
# Verify fixes
shellcheck deploy.sh

# Add directive for SC1090
# shellcheck source=/dev/null
source "$CONFIG_FILE"
```
```
