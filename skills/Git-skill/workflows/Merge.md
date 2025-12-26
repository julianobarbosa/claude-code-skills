# Merge Workflow

Merge branches together safely.

## Prerequisites

- Git repository initialized
- Branches to merge exist
- Clean working directory recommended

## Basic Merge

### Standard Merge (with commit)

```bash
# Ensure you're on target branch
git checkout main

# Merge source branch
git merge feature/my-feature
```

This creates a merge commit preserving branch history.

### Fast-Forward Merge

```bash
# When target hasn't diverged
git merge --ff-only feature/my-feature
```

This moves the pointer forward without a merge commit.

### No Fast-Forward (Force Merge Commit)

```bash
# Always create merge commit
git merge --no-ff feature/my-feature
```

Useful for maintaining clear feature boundaries in history.

## Merge Workflow Steps

### Step 1: Prepare for Merge

```bash
# Check current status
git status

# Ensure working directory is clean
# If not, commit or stash changes

# Switch to target branch
git checkout main

# Update target branch
git pull origin main
```

### Step 2: Preview Merge

```bash
# See what will be merged
git log main..feature/branch --oneline

# See file changes
git diff main...feature/branch --stat

# Dry run (check for conflicts without merging)
git merge --no-commit --no-ff feature/branch
git merge --abort  # Cancel preview
```

### Step 3: Execute Merge

```bash
# Merge the branch
git merge feature/my-feature -m "Merge feature/my-feature into main"
```

### Step 4: Verify Merge

```bash
# Check status
git status

# View merge commit
git log -1

# Verify changes
git diff HEAD~1
```

### Step 5: Push Merged Result

```bash
git push origin main
```

## Handling Merge Conflicts

### When Conflicts Occur

```bash
# Git will report conflicting files
git status

# Files with conflicts shown as:
# both modified: <filename>
```

### Resolve Conflicts

1. **Open conflicting files** - Look for conflict markers:
   ```
   <<<<<<< HEAD
   your changes
   =======
   incoming changes
   >>>>>>> feature/branch
   ```

2. **Edit to resolve** - Keep desired code, remove markers

3. **Mark as resolved**:
   ```bash
   git add <resolved-file>
   ```

4. **Complete merge**:
   ```bash
   git commit
   ```

### Abort Merge

```bash
# Cancel merge and return to pre-merge state
git merge --abort
```

### Use Merge Tool

```bash
# Open configured merge tool
git mergetool

# Common tools: vimdiff, meld, kdiff3, vscode
```

## Merge Strategies

### Recursive (Default)

```bash
git merge -s recursive feature/branch
```

Best for most merges, handles renames well.

### Ours (Keep Target)

```bash
git merge -s ours feature/branch
```

Keeps all changes from current branch, discards source changes.
**Use case:** Marking a branch as merged without taking changes.

### Theirs (Keep Source)

```bash
git merge -X theirs feature/branch
```

Prefers changes from source branch in conflicts.

### Octopus (Multi-branch)

```bash
git merge branch1 branch2 branch3
```

Merge multiple branches at once (no conflict resolution).

## Squash Merge

Combine all commits into one:

```bash
# Squash merge (no commit yet)
git merge --squash feature/branch

# Commit the squashed changes
git commit -m "feat: add feature (squashed)"
```

**Pros:** Clean history, single commit
**Cons:** Loses individual commit details

## Common Merge Scenarios

### Merge Main into Feature (Update Feature)

```bash
# On feature branch
git checkout feature/my-feature

# Merge main
git merge main

# Resolve any conflicts
# Push updated feature branch
git push origin feature/my-feature
```

### Merge Feature into Main (Complete Feature)

```bash
# On main branch
git checkout main
git pull origin main

# Merge feature
git merge --no-ff feature/my-feature

# Push
git push origin main

# Delete feature branch (optional)
git branch -d feature/my-feature
git push origin --delete feature/my-feature
```

### Merge Release Branch

```bash
# Merge to main
git checkout main
git merge --no-ff release/v1.0 -m "Release v1.0"
git tag -a v1.0 -m "Version 1.0"
git push origin main --tags

# Merge back to develop
git checkout develop
git merge --no-ff release/v1.0
git push origin develop
```

## Safety Rules

1. **Always update target branch first** - Pull before merge
2. **Check for uncommitted work** - Clean working directory
3. **Preview before merging** - Know what's coming
4. **Don't force push after merge** - Others may have pulled
5. **Test after merge** - Ensure nothing broke
6. **Use `--no-ff` for features** - Maintain clear history

## Error Handling

### Merge Conflict

```
CONFLICT (content): Merge conflict in <file>
Automatic merge failed.

Resolution:
1. Edit conflicting files
2. git add <resolved-files>
3. git commit
```

### Cannot Fast-Forward

```
Error: Not possible to fast-forward.

Options:
1. Allow merge commit: git merge <branch>
2. Rebase instead: git rebase <branch>
3. Force FF (loses commits): Not recommended
```

### Nothing to Merge

```
Already up to date.

The branches are identical - no merge needed.
```
