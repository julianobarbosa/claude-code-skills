# Commit Workflow

Stage all changes and create a commit locally (NO push to remote).

## Prerequisites

- Git repository initialized
- Changes to commit (staged or unstaged)

## Workflow Steps

### Step 1: Security Scan

**CRITICAL: Scan for sensitive data before ANY commit.**

```bash
# Check for sensitive files in staged changes
git diff --cached --name-only | grep -iE '\.(env|pem|key|p12|pfx|credentials)$'

# Check for hardcoded secrets in staged content
git diff --cached | grep -iE '(api[_-]?key|secret|password|token|credential).*=.*["\047][a-zA-Z0-9]'
```

**If sensitive data found:**
1. STOP immediately
2. Report findings to user
3. Suggest using `.gitignore` or removing secrets
4. DO NOT proceed until resolved

### Step 2: Review Changes

```bash
# Show current status
git status

# Show detailed diff of all changes
git diff
git diff --cached
```

**Review checklist:**
- [ ] No sensitive data (credentials, API keys, tokens)
- [ ] No `.env` files or variants
- [ ] No private keys or certificates
- [ ] No database connection strings with passwords
- [ ] Changes are intentional and complete

### Step 3: Generate Commit Message

**Follow Conventional Commits format:**

```
<type>(<scope>): <short description>

<optional body with details>
```

**Type Selection Guide:**

| Changes Include | Type |
|----------------|------|
| New feature or capability | `feat` |
| Bug fix | `fix` |
| Documentation only | `docs` |
| Code formatting/style | `style` |
| Code restructure | `refactor` |
| Performance improvement | `perf` |
| Test changes | `test` |
| Build/dependency changes | `build` |
| CI/CD changes | `ci` |
| Maintenance/chores | `chore` |

**Rules:**
- Title: Max 70 characters, imperative mood, no period
- Scope: Optional, describes affected area (e.g., `api`, `ui`, `auth`)
- Body: Explain what and why, not how

### Step 4: Stage and Commit

```bash
# Stage all changes
git add -A

# Or stage specific files
git add <file1> <file2>

# Commit with message
git commit -m "<type>(<scope>): <description>"
```

**For multi-line commit messages:**
```bash
git commit -m "<title>" -m "<body paragraph>"
```

### Step 5: Verify Success

```bash
# Show the new commit
git log -1 --oneline

# Confirm clean working directory (or remaining changes)
git status
```

## Output Format

```
Commit successful!

Hash: <commit-hash>
Message: <commit-message>
Files changed: <count>
Insertions: <count>
Deletions: <count>

Working directory: [clean | <remaining changes>]
```

## Special Cases

### Splitting Changes Into Multiple Commits

If changes span multiple concerns:

1. Stage related files together
2. Commit with appropriate type
3. Repeat for remaining changes

```bash
# Commit feature files
git add src/feature/*
git commit -m "feat(feature): add new capability"

# Commit test files
git add tests/feature/*
git commit -m "test(feature): add tests for new capability"
```

### Amending Previous Commit

**Only if NOT pushed to remote:**

```bash
# Add changes to previous commit
git add <files>
git commit --amend --no-edit

# Or update the message
git commit --amend -m "new message"
```

## IMPORTANT

**This workflow does NOT push to remote.**

To push after committing, use the `CommitPush` workflow or run:
```bash
git push origin <branch>
```
