---
name: ShellCheck
description: Shell script static analysis and linting. USE WHEN shellcheck, lint shell, bash lint, sh lint, script analysis, shell errors, SC codes, shell best practices. Comprehensive shell script validation with CI/CD integration.
---

# ShellCheck - Shell Script Static Analysis

**Auto-routes when user mentions shellcheck, shell linting, bash script analysis, or SC error codes.**

## Overview

ShellCheck is a GPLv3-licensed static analysis tool that identifies bugs in bash/sh shell scripts. It detects:
- Syntax errors and parsing issues
- Semantic problems causing unexpected behavior
- Quoting issues and word splitting bugs
- POSIX compatibility warnings
- Style and best practice violations

## Voice Notification

**When executing a workflow, do BOTH:**

1. **Send voice notification**:
   ```bash
   curl -s -X POST http://localhost:8888/notify \
     -H "Content-Type: application/json" \
     -d '{"message": "Running the WORKFLOWNAME workflow from the ShellCheck skill"}' \
     > /dev/null 2>&1 &
   ```

2. **Output text notification**:
   ```
   Running the **WorkflowName** workflow from the **ShellCheck** skill...
   ```

## Workflow Routing

| Workflow | Trigger | File |
|----------|---------|------|
| **Analyze** | "shellcheck this", "lint script", "check shell" | `Workflows/Analyze.md` |
| **Fix** | "fix shell errors", "apply shellcheck fixes" | `Workflows/Fix.md` |
| **Setup** | "setup shellcheck", "configure shellcheck" | `Workflows/Setup.md` |
| **Explain** | "explain SC2086", "what is SC code" | `Workflows/Explain.md` |

## Quick Reference

### Basic Usage

```bash
# Check a script
shellcheck myscript.sh

# Specify shell dialect
shellcheck -s bash myscript.sh

# Exclude specific codes
shellcheck -e SC2086,SC2046 myscript.sh

# Output formats
shellcheck -f gcc myscript.sh      # Editor integration
shellcheck -f json myscript.sh     # Machine readable
shellcheck -f diff myscript.sh     # Auto-fix patches
```

### Common SC Codes

| Code | Issue | Fix |
|------|-------|-----|
| SC2086 | Unquoted variable | `"$var"` |
| SC2046 | Unquoted command substitution | `"$(cmd)"` |
| SC2034 | Unused variable | Remove or export |
| SC2154 | Unassigned variable | Assign or disable |
| SC2155 | Declare and assign separately | Split declaration |

### Inline Directives

```bash
# Disable for next command
# shellcheck disable=SC2086
echo $var

# Disable for entire file (after shebang)
#!/bin/bash
# shellcheck disable=SC2086,SC2046
```

## Full Documentation

- Error Codes: `SkillSearch('shellcheck error codes')` -> loads ErrorCodes.md
- Configuration: `SkillSearch('shellcheck config')` -> loads Configuration.md
- CI/CD Integration: `SkillSearch('shellcheck ci')` -> loads Integration.md
- Best Practices: `SkillSearch('shellcheck practices')` -> loads BestPractices.md

## Examples

**Example 1: Analyze a script**
```
User: "shellcheck my deploy script"
-> Invokes Analyze workflow
-> Runs shellcheck with JSON output
-> Presents findings grouped by severity
-> Suggests fixes with wiki links
```

**Example 2: Fix common issues**
```
User: "fix the shellcheck errors in scripts/"
-> Invokes Fix workflow
-> Generates diff output
-> Applies fixes interactively
-> Re-runs validation
```

**Example 3: Setup for project**
```
User: "setup shellcheck for this repo"
-> Invokes Setup workflow
-> Creates .shellcheckrc
-> Adds pre-commit hook
-> Configures CI workflow
```

**Example 4: Explain an error code**
```
User: "what does SC2086 mean?"
-> Invokes Explain workflow
-> Fetches wiki documentation
-> Shows examples and fixes
-> Provides context-specific guidance
```
