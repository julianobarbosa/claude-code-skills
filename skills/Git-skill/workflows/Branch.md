# Branch Workflow

Create, switch, list, and manage Git branches.

## Prerequisites

- Git repository initialized
- For remote operations: remote configured

## Operations

### List Branches

```bash
# List local branches
git branch

# List all branches (local + remote)
git branch -a

# List remote branches only
git branch -r

# List with last commit info
git branch -v

# List merged branches
git branch --merged

# List unmerged branches
git branch --no-merged
```

### Create New Branch

**From current HEAD:**
```bash
# Create branch
git branch <branch-name>

# Create and switch to branch
git checkout -b <branch-name>

# Or using switch (Git 2.23+)
git switch -c <branch-name>
```

**From specific commit/branch:**
```bash
# Create from another branch
git checkout -b <new-branch> <source-branch>

# Create from specific commit
git checkout -b <new-branch> <commit-hash>

# Create from tag
git checkout -b <new-branch> <tag-name>
```

**From remote branch:**
```bash
# Fetch first
git fetch origin

# Create tracking branch
git checkout -b <local-name> origin/<remote-branch>

# Or track with same name
git checkout --track origin/<branch-name>
```

### Switch Branches

```bash
# Switch to existing branch
git checkout <branch-name>

# Or using switch (Git 2.23+)
git switch <branch-name>

# Switch to previous branch
git checkout -
git switch -
```

**Before switching:**
```bash
# Check for uncommitted changes
git status

# If changes exist, either:
# 1. Commit them
git add -A && git commit -m "wip: save progress"

# 2. Stash them
git stash push -m "switching branches"

# 3. Discard them (CAUTION)
git checkout -- .
```

### Rename Branch

```bash
# Rename current branch
git branch -m <new-name>

# Rename specific branch
git branch -m <old-name> <new-name>

# Update remote (delete old, push new)
git push origin --delete <old-name>
git push -u origin <new-name>
```

### Delete Branch

**Local branch:**
```bash
# Safe delete (only if merged)
git branch -d <branch-name>

# Force delete (even if unmerged)
git branch -D <branch-name>
```

**Remote branch:**
```bash
# Delete remote branch
git push origin --delete <branch-name>

# Or using colon syntax
git push origin :<branch-name>
```

### Track Remote Branch

```bash
# Set upstream for current branch
git branch --set-upstream-to=origin/<branch>

# Or during push
git push -u origin <branch-name>

# Check tracking info
git branch -vv
```

## Branch Naming Conventions

| Type | Format | Example |
|------|--------|---------|
| Feature | `feature/<description>` | `feature/user-auth` |
| Bug fix | `fix/<description>` | `fix/login-error` |
| Hotfix | `hotfix/<description>` | `hotfix/security-patch` |
| Release | `release/<version>` | `release/v1.2.0` |
| Chore | `chore/<description>` | `chore/update-deps` |

**Rules:**
- Use lowercase
- Use hyphens, not underscores
- Keep names concise but descriptive
- Include ticket number if applicable: `feature/JIRA-123-user-auth`

## Common Workflows

### Start New Feature

```bash
# Ensure you're on main with latest
git checkout main
git pull origin main

# Create feature branch
git checkout -b feature/new-feature

# Work and commit...
git add -A
git commit -m "feat: add new feature"

# Push to remote
git push -u origin feature/new-feature
```

### Clean Up Merged Branches

```bash
# Delete merged local branches
git branch --merged main | grep -v "main" | xargs git branch -d

# Prune remote tracking branches
git fetch --prune

# Delete merged remote branches (careful!)
git branch -r --merged main | grep -v "main" | sed 's/origin\///' | xargs -I {} git push origin --delete {}
```

### Find Branch Containing Commit

```bash
# Find branches containing commit
git branch --contains <commit-hash>

# Find remote branches
git branch -r --contains <commit-hash>
```

## Safety Rules

1. **Check status before switching** - Don't lose uncommitted work
2. **Don't delete unmerged branches** without understanding why
3. **Be careful with remote deletes** - Others may depend on them
4. **Keep main/master protected** - Never work directly on it
5. **Prune regularly** - Clean up stale branches

## Error Handling

### Branch Already Exists

```
Error: Branch already exists.

Options:
1. Use different name
2. Delete existing: git branch -D <name>
3. Switch to it: git checkout <name>
```

### Uncommitted Changes Block Switch

```
Error: Your local changes would be overwritten.

Options:
1. Commit: git add -A && git commit -m "wip"
2. Stash: git stash
3. Discard: git checkout -- . (CAUTION)
```

### Cannot Delete Current Branch

```
Error: Cannot delete the branch you're on.

Switch to another branch first:
  git checkout main
Then delete:
  git branch -d <branch>
```
