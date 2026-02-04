# Explain Workflow

Explain ShellCheck error codes and provide context-specific guidance.

## Trigger

- "explain SC2086"
- "what does SC2086 mean"
- "shellcheck error SC2046"
- "help with SC code"

## Process

### 1. Parse Error Code

Extract the SC code from user input:
- `SC2086`
- `2086`
- `shellcheck SC2086`

### 2. Fetch Documentation

Reference the wiki URL:
```
https://www.shellcheck.net/wiki/SCXXXX
```

### 3. Provide Explanation

Structure the response:

1. **What it means** - Plain language explanation
2. **Why it matters** - The actual problem it catches
3. **How to fix** - Code examples
4. **When to suppress** - Legitimate exceptions

## Common Error Explanations

### SC2086 - Double quote to prevent globbing and word splitting

**What it means:**
Variable is unquoted, which allows word splitting and glob expansion.

**Why it matters:**
```bash
# If filename contains spaces or glob characters
filename="my file*.txt"

# Bad - expands to multiple arguments or matches files
rm $filename

# Could become:
rm my file*.txt  # 3 separate args!
# Or expand globs to match actual files
```

**How to fix:**
```bash
rm "$filename"
```

**When to suppress:**
- Intentionally splitting a variable: `# shellcheck disable=SC2086`
- Variable contains intentional glob pattern

---

### SC2046 - Quote this to prevent word splitting

**What it means:**
Command substitution output is unquoted.

**Why it matters:**
```bash
# Bad - output split on whitespace
files=$(find . -name "*.txt")
for f in $files; do  # Breaks on spaces in filenames
    process "$f"
done
```

**How to fix:**
```bash
# Use arrays
mapfile -t files < <(find . -name "*.txt")
for f in "${files[@]}"; do
    process "$f"
done

# Or use while read
find . -name "*.txt" -print0 | while IFS= read -r -d '' f; do
    process "$f"
done
```

---

### SC2034 - Variable appears unused

**What it means:**
A variable is assigned but never used in the script.

**Why it matters:**
- Dead code that should be removed
- Possible typo in variable name
- Variable meant for external use

**How to fix:**
```bash
# If truly unused, remove it
# readonly UNUSED_VAR="value"  # Delete

# If used externally, export it
export CONFIG_PATH="/etc/myapp"

# If false positive, disable with explanation
# shellcheck disable=SC2034 # Used by sourced scripts
readonly LIB_VERSION="1.0.0"
```

---

### SC2154 - Variable is referenced but not assigned

**What it means:**
Using a variable that was never set.

**Why it matters:**
- Typo in variable name
- Missing assignment
- Variable expected from environment/sourced file

**How to fix:**
```bash
# Ensure assignment
MY_VAR="value"
echo "$MY_VAR"

# For environment variables, check existence
if [[ -z ${ENV_VAR:-} ]]; then
    echo "ENV_VAR not set" >&2
    exit 1
fi

# For sourced files, add directive
# shellcheck source=./config.sh
source "$CONFIG_FILE"
```

---

### SC2155 - Declare and assign separately

**What it means:**
`local` declaration combined with command substitution masks the exit code.

**Why it matters:**
```bash
# Bad - exit code of 'command' is lost
local output=$(command_that_might_fail)
# $? is always 0 (from successful 'local')

# If command_that_might_fail returns 1, you won't know
```

**How to fix:**
```bash
# Declare separately
local output
output=$(command_that_might_fail) || return 1
```

---

### SC2164 - Use 'cd ... || exit' in case cd fails

**What it means:**
`cd` can fail, and subsequent commands would run in wrong directory.

**Why it matters:**
```bash
# Dangerous!
cd /some/directory
rm -rf *  # If cd failed, deletes from current directory!
```

**How to fix:**
```bash
cd /some/directory || exit 1
rm -rf ./*

# Or with error handling
cd /some/directory || {
    echo "Failed to cd to /some/directory" >&2
    exit 1
}
```

---

### SC1090 - Can't follow non-constant source

**What it means:**
ShellCheck can't analyze a dynamically sourced file.

**Why it matters:**
ShellCheck needs to know what's being sourced to check for issues.

**How to fix:**
```bash
# Tell ShellCheck where to find the file
# shellcheck source=./lib/common.sh
source "$LIB_DIR/common.sh"

# Or skip if file doesn't exist at check time
# shellcheck source=/dev/null
source "$DYNAMIC_CONFIG"
```

---

### SC2006 - Use $(...) instead of backticks

**What it means:**
Using legacy backtick syntax for command substitution.

**Why it matters:**
- Backticks are harder to read
- Can't be nested easily
- Quoting rules are confusing

**How to fix:**
```bash
# Bad
date=`date +%Y-%m-%d`
nested=`echo \`hostname\``

# Good
date=$(date +%Y-%m-%d)
nested=$(echo "$(hostname)")
```

---

### SC2162 - read without -r will mangle backslashes

**What it means:**
`read` interprets backslashes as escape sequences without `-r`.

**Why it matters:**
```bash
# Bad
echo "path\to\file" | read line
echo "$line"  # Outputs: pathoile (backslashes interpreted)
```

**How to fix:**
```bash
# Use -r for raw input
while IFS= read -r line; do
    echo "$line"
done < file
```

## Output Template

```markdown
## SC{CODE}: {Title}

### Explanation
{Plain language explanation}

### Why This Matters
{Real-world consequences}

### Before (Problematic)
```bash
{bad code}
```

### After (Fixed)
```bash
{fixed code}
```

### When to Suppress
{Legitimate exceptions with example}

```bash
# shellcheck disable=SC{CODE}
# Reason: {justification}
{code}
```

### Related Codes
- SC{related1}: {description}
- SC{related2}: {description}

### Resources
- [Wiki: SC{CODE}](https://www.shellcheck.net/wiki/SC{CODE})
```
