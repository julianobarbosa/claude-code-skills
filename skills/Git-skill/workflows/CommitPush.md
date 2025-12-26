# CommitPush Workflow

Stage all changes, create a commit, and push to remote repository.

## Prerequisites

- Git repository initialized
- Remote configured (`origin`)
- Changes to commit
- Push access to remote

## Workflow Steps

### Step 1: Security Scan

**CRITICAL: Scan for sensitive data before ANY commit.**

```bash
# Check for sensitive files
git diff --cached --name-only | grep -iE '\.(env|pem|key|p12|pfx|credentials)$'
git diff --name-only | grep -iE '\.(env|pem|key|p12|pfx|credentials)$'

# Check for hardcoded secrets
git diff --cached | grep -iE '(api[_-]?key|secret|password|token|credential).*=.*["\047][a-zA-Z0-9]'
git diff | grep -iE '(api[_-]?key|secret|password|token|credential).*=.*["\047][a-zA-Z0-9]'
```

**If sensitive data found:**
1. STOP immediately
2. Report all findings to user
3. DO NOT proceed until resolved
4. Suggest `.gitignore` additions if needed

### Step 2: Verify Remote

```bash
# Confirm remote URL
git remote -v

# Confirm current branch
git branch --show-current
```

**Safety check:** Verify this is the intended repository before pushing sensitive code.

### Step 3: Review Changes

```bash
# Full status
git status

# Detailed changes
git diff
git diff --cached
```

**Review checklist:**
- [ ] No credentials or API keys
- [ ] No `.env` files
- [ ] No private keys or certificates
- [ ] No connection strings with passwords
- [ ] All changes are intentional

### Step 4: Generate Commit Message

**Conventional Commits format:**

```
<type>(<scope>): <description>

[optional body]
```

**Type selection:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting
- `refactor`: Code restructure
- `perf`: Performance
- `test`: Testing
- `build`: Build/deps
- `ci`: CI/CD
- `chore`: Maintenance

**Rules:**
- Title max 70 characters
- Imperative mood ("add" not "added")
- No period at end

### Step 5: Stage and Commit

```bash
# Stage all changes
git add -A

# Commit
git commit -m "<type>(<scope>): <description>"
```

### Step 6: Push to Remote

```bash
# Push to origin on current branch
git push origin $(git branch --show-current)
```

**If branch doesn't exist on remote:**
```bash
git push -u origin $(git branch --show-current)
```

### Step 7: Verify Push

```bash
# Confirm push succeeded
git log origin/$(git branch --show-current) -1 --oneline

# Check sync status
git status
```

## Output Format

```
Commit and push successful!

Commit:
  Hash: <commit-hash>
  Message: <commit-message>

Push:
  Remote: origin
  Branch: <branch-name>
  URL: <repository-url>

Files changed: <count>
Insertions: <count>
Deletions: <count>
```

## Error Handling

### Push Rejected - Behind Remote

```bash
# Fetch and rebase
git fetch origin
git rebase origin/<branch>

# Then push
git push origin <branch>
```

### Push Rejected - Protected Branch

```
Error: Cannot push directly to protected branch.

Options:
1. Create a feature branch and open a PR
2. Request push access from repository admin
```

### Authentication Failed

```
Error: Authentication required.

Solutions:
1. Check SSH key: ssh -T git@github.com
2. Check token: gh auth status
3. Re-authenticate: gh auth login
```

## Splitting Into Multiple Commits

If changes span multiple concerns, split them:

```bash
# First commit - features
git add src/features/*
git commit -m "feat: add new feature"

# Second commit - tests
git add tests/*
git commit -m "test: add feature tests"

# Push all commits
git push origin <branch>
```

## NEVER Do

1. **Force push to main/master** without explicit confirmation
2. **Push secrets or credentials** - always scan first
3. **Skip the security scan** - it's mandatory
4. **Add AI attribution** to commit messages
