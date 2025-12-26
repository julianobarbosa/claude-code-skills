# Stash Workflow

Temporarily save uncommitted changes.

## Prerequisites

- Git repository initialized
- Uncommitted changes to stash

## Understanding Stash

Stash saves your working directory and index state without committing, letting you switch context and return later.

**Use cases:**
- Switch branches with uncommitted work
- Pull changes without committing WIP
- Temporarily set aside experiments
- Save partial work before meetings

## Basic Operations

### Save to Stash

```bash
# Stash all tracked changes
git stash

# Stash with message
git stash push -m "description of changes"

# Stash including untracked files
git stash push -u -m "including new files"

# Stash including ignored files
git stash push -a -m "everything"
```

### List Stashes

```bash
# Show all stashes
git stash list

# Output format:
# stash@{0}: WIP on main: abc1234 Last commit message
# stash@{1}: On feature: def5678 Another commit
```

### Apply Stash

```bash
# Apply most recent stash (keep in stash)
git stash apply

# Apply specific stash
git stash apply stash@{2}

# Apply and remove from stash
git stash pop

# Pop specific stash
git stash pop stash@{1}
```

### View Stash Contents

```bash
# Show changes in most recent stash
git stash show

# Show with diff
git stash show -p

# Show specific stash
git stash show -p stash@{1}
```

### Delete Stash

```bash
# Drop most recent stash
git stash drop

# Drop specific stash
git stash drop stash@{2}

# Clear all stashes
git stash clear
```

## Stash Workflow Steps

### Step 1: Identify What to Stash

```bash
# Check current state
git status

# See what will be stashed
git diff
git diff --cached
```

### Step 2: Stash Changes

```bash
# With descriptive message
git stash push -m "WIP: feature implementation"

# For new files too
git stash push -u -m "WIP: new feature with new files"
```

### Step 3: Verify Stash

```bash
# Confirm stash created
git stash list

# Confirm working directory clean
git status
```

### Step 4: Do Other Work

```bash
# Switch branches, pull, etc.
git checkout other-branch
git pull origin main
```

### Step 5: Restore Stash

```bash
# Return to original branch
git checkout original-branch

# Apply stash
git stash pop
```

## Advanced Stash Operations

### Stash Specific Files

```bash
# Stash only certain files
git stash push -m "partial stash" -- file1.js file2.js

# Stash everything except certain files
git stash push -m "most changes" -- . ':(exclude)keep-this.js'
```

### Create Branch from Stash

```bash
# Create new branch with stash applied
git stash branch new-feature-branch stash@{0}
```

Useful when stash conflicts with current branch.

### Stash Staged Only

```bash
# Keep unstaged, stash only staged
git stash push --staged -m "staged changes only"
```

### Stash Keep Index

```bash
# Stash but keep staged changes in index
git stash push --keep-index -m "unstaged only"
```

### Interactive Stash

```bash
# Interactively select hunks to stash
git stash push -p -m "selected changes"
```

## Common Scenarios

### Quick Context Switch

```bash
# Working on feature, need to check something on main
git stash push -m "feature WIP"
git checkout main
# ... do stuff ...
git checkout feature-branch
git stash pop
```

### Pull with Local Changes

```bash
# Can't pull with uncommitted changes
git stash push -m "before pull"
git pull origin main
git stash pop
# Resolve any conflicts
```

### Try Something Experimental

```bash
# Save current work
git stash push -m "stable version"

# Experiment
# ... make risky changes ...

# If it fails, restore
git checkout -- .
git stash pop

# If it works, commit and drop stash
git add -A && git commit -m "feat: experimental change"
git stash drop
```

### Recover Dropped Stash

```bash
# Find the stash SHA
git fsck --unreachable | grep commit

# Or from reflog
git reflog

# Apply by SHA
git stash apply <commit-sha>
```

## Stash vs Commit

| Stash | Commit |
|-------|--------|
| Temporary | Permanent |
| Not shared | Pushed to remote |
| No message required | Message required |
| Quick context switch | Logical checkpoint |
| Stack based (LIFO) | Linear history |

**Rule of thumb:**
- Stash: "I need to do something else quickly"
- Commit: "This is a meaningful unit of work"

## Error Handling

### No Local Changes to Stash

```
No local changes to save.

Working directory is already clean.
```

### Conflicts When Applying

```
CONFLICT: Merge conflict in <file>

Resolution:
1. Resolve conflicts in files
2. git add <resolved-files>
3. Continue work (stash is not dropped if using apply)
```

### Stash Index Out of Range

```
Error: stash@{5} is not a valid reference

Check available stashes: git stash list
```

## Best Practices

1. **Always add messages** - Future you will thank you
2. **Don't stash for too long** - Commit or branch instead
3. **Check stash list regularly** - Clean up old stashes
4. **Use branches for longer work** - Stash is for quick switches
5. **Include untracked if needed** - Use `-u` flag
