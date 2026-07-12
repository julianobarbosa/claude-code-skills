# Undo Workflow

Undo changes, reset commits, and revert modifications.

## Prerequisites

- Git repository initialized
- Understanding of what you want to undo

## Safety Classification

| Operation | Destructive | Recoverable |
|-----------|-------------|-------------|
| `checkout -- file` | YES | NO* |
| `reset --soft` | NO | YES |
| `reset --mixed` | NO | YES |
| `reset --hard` | YES | Partial** |
| `revert` | NO | YES |
| `clean -fd` | YES | NO |

*Uncommitted changes lost permanently
**Commits recoverable via reflog for ~30 days

## Undo Uncommitted Changes

### Discard Changes in File

```bash
# Discard changes in specific file
git checkout -- <file>

# Or using restore (Git 2.23+)
git restore <file>

# Discard all unstaged changes
git checkout -- .
git restore .
```

**WARNING:** This permanently deletes uncommitted changes.

### Unstage Files

```bash
# Unstage specific file
git reset HEAD <file>

# Or using restore
git restore --staged <file>

# Unstage all files
git reset HEAD
git restore --staged .
```

Changes remain in working directory.

### Discard All Changes

```bash
# Unstaged changes
git checkout -- .

# Staged and unstaged
git reset --hard HEAD

# Including untracked files (DANGER)
git clean -fd
```

## Undo Commits

### Undo Last Commit (Keep Changes)

```bash
# Uncommit but keep changes staged
git reset --soft HEAD~1

# Uncommit and unstage (keep in working dir)
git reset HEAD~1
# or
git reset --mixed HEAD~1
```

### Undo Last Commit (Discard Changes)

```bash
# Remove commit AND changes (DANGER)
git reset --hard HEAD~1
```

### Undo Multiple Commits

```bash
# Undo last 3 commits (keep changes)
git reset HEAD~3

# Undo to specific commit
git reset <commit-hash>
```

### Undo Pushed Commit (Safe)

```bash
# Create new commit that undoes changes
git revert <commit-hash>
git push origin <branch>
```

This is safe for shared branches.

### Undo Pushed Commit (Rewrite History)

```bash
# DANGER: Only for personal branches
git reset --hard HEAD~1
git push --force-with-lease origin <branch>
```

**NEVER do this on main/master or shared branches.**

## Undo Merge

### Undo Unpushed Merge

```bash
# If you haven't committed merge yet
git merge --abort

# If merge is committed
git reset --hard HEAD~1
```

### Undo Pushed Merge

```bash
# Revert the merge commit
git revert -m 1 <merge-commit-hash>
git push origin <branch>
```

`-m 1` means keep parent 1 (the branch you merged into).

## Undo Rebase

### During Rebase

```bash
# Abort rebase in progress
git rebase --abort
```

### After Rebase

```bash
# Use reflog to find pre-rebase state
git reflog

# Reset to before rebase
git reset --hard HEAD@{2}
```

## Recovery with Reflog

```bash
# Show recent HEAD positions
git reflog

# Output:
# abc1234 HEAD@{0}: reset: moving to HEAD~1
# def5678 HEAD@{1}: commit: some work
# ghi9012 HEAD@{2}: commit: earlier work

# Recover to specific point
git reset --hard HEAD@{1}
```

## Workflow Steps

### Step 1: Understand What to Undo

```bash
# Check current state
git status

# Check recent commits
git log --oneline -10

# Check reflog
git reflog -10
```

### Step 2: Choose Undo Method

| What to Undo | Method |
|--------------|--------|
| Unstaged file changes | `git checkout -- <file>` |
| Staged files | `git reset HEAD <file>` |
| Last commit (keep changes) | `git reset HEAD~1` |
| Last commit (discard) | `git reset --hard HEAD~1` |
| Pushed commit | `git revert <hash>` |
| Merge | `git revert -m 1 <hash>` |
| Rebase | `git reflog` + `git reset` |

### Step 3: Execute with Confirmation

**Always confirm destructive operations:**

```
WARNING: This will permanently delete uncommitted changes.
Proceed? [y/N]
```

### Step 4: Verify Result

```bash
# Check status
git status

# Check commit history
git log --oneline -5

# Check file contents
git diff
```

## Common Scenarios

### Accidentally Staged Wrong File

```bash
git restore --staged wrong-file.js
# File is now unstaged but changes preserved
```

### Committed to Wrong Branch

```bash
# On wrong branch, move commit to correct branch
git checkout correct-branch
git cherry-pick <commit-hash>

# Remove from wrong branch
git checkout wrong-branch
git reset --hard HEAD~1
```

### Need to Edit Last Commit

```bash
# Add forgotten changes
git add forgotten-file.js
git commit --amend --no-edit

# Or change the message
git commit --amend -m "new message"
```

**Only if not pushed yet.**

### Accidentally Deleted File

```bash
# If still uncommitted
git checkout -- deleted-file.js

# If committed
git checkout HEAD~1 -- deleted-file.js
```

### Reset Too Far

```bash
# Find the commit you need
git reflog

# Restore to that point
git reset --hard <hash>
```

## Error Handling

### Cannot Reset - Changes Would Be Overwritten

```
Error: Your local changes would be overwritten.

Options:
1. Stash: git stash
2. Commit: git commit -am "wip"
3. Discard: git checkout -- .
```

### Cannot Revert - Conflicts

```
Error: Conflict during revert.

Resolution:
1. Resolve conflicts
2. git add <files>
3. git revert --continue
```

### Reflog Entry Not Found

```
Error: Cannot find HEAD@{n}

Reflog entries expire after ~30 days.
Commits may be recoverable with:
  git fsck --lost-found
```

## Safety Checklist

Before any undo operation:

- [ ] Do I understand what will be lost?
- [ ] Have I backed up important changes?
- [ ] Is this a shared branch? (If yes, use `revert`)
- [ ] Have I checked the reflog for recovery options?
