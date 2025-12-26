# Rebase Workflow

Reapply commits on top of another base.

## Prerequisites

- Git repository initialized
- Understanding of rebase implications
- **Never rebase public/shared branches**

## Understanding Rebase

Rebase rewrites commit history by:
1. Taking your commits
2. Temporarily removing them
3. Applying target branch commits
4. Replaying your commits on top

**Result:** Linear history without merge commits.

## Basic Rebase

### Rebase onto Branch

```bash
# On feature branch
git checkout feature/my-feature

# Rebase onto main
git rebase main
```

### Rebase onto Remote

```bash
# Fetch latest
git fetch origin

# Rebase onto remote main
git rebase origin/main
```

## Rebase Workflow Steps

### Step 1: Prepare

```bash
# Ensure clean working directory
git status

# Switch to branch to rebase
git checkout feature/my-feature

# Fetch latest from remote
git fetch origin
```

### Step 2: Execute Rebase

```bash
# Rebase onto main
git rebase main
```

### Step 3: Handle Conflicts (if any)

```bash
# Git pauses at conflicts
# Edit files to resolve

# After resolving:
git add <resolved-files>
git rebase --continue

# Or abort:
git rebase --abort
```

### Step 4: Force Push (if already pushed)

**DANGER: Only do this on YOUR branch:**
```bash
# Force push rebased branch
git push --force-with-lease origin feature/my-feature
```

## Interactive Rebase

Rewrite, reorder, squash, or drop commits.

### Start Interactive Rebase

```bash
# Rebase last N commits
git rebase -i HEAD~5

# Rebase onto branch interactively
git rebase -i main
```

### Interactive Commands

```
pick   - Use commit as-is
reword - Use commit but edit message
edit   - Stop for amending
squash - Meld into previous commit (keep message)
fixup  - Meld into previous commit (discard message)
drop   - Remove commit
```

### Common Interactive Operations

**Squash multiple commits:**
```bash
git rebase -i HEAD~3

# In editor:
pick abc1234 First commit
squash def5678 Second commit
squash ghi9012 Third commit

# Save, then edit combined message
```

**Reword commit message:**
```bash
git rebase -i HEAD~2

# Change 'pick' to 'reword'
reword abc1234 Old message

# Save, then edit message in next editor
```

**Reorder commits:**
```bash
git rebase -i HEAD~3

# Simply reorder the lines
pick ghi9012 Third commit
pick abc1234 First commit
pick def5678 Second commit
```

**Drop a commit:**
```bash
git rebase -i HEAD~3

# Change 'pick' to 'drop' or delete the line
pick abc1234 First commit
drop def5678 Second commit
pick ghi9012 Third commit
```

## Rebase vs Merge

| Aspect | Rebase | Merge |
|--------|--------|-------|
| History | Linear | Preserves branches |
| Conflicts | Per commit | Once |
| Safety | Rewrites history | Safe for shared |
| Use case | Clean up before merge | Integrate branches |

**Golden rule:** Only rebase commits that haven't been pushed/shared.

## Common Scenarios

### Update Feature Branch with Main

```bash
# On feature branch
git checkout feature/my-feature

# Fetch and rebase
git fetch origin
git rebase origin/main

# Force push if needed
git push --force-with-lease origin feature/my-feature
```

### Clean Up Before PR

```bash
# Squash WIP commits
git rebase -i main

# Make commits logical units
# Force push cleaned branch
git push --force-with-lease origin feature/my-feature
```

### Split a Commit

```bash
git rebase -i HEAD~2

# Mark commit as 'edit'
edit abc1234 Large commit

# When stopped:
git reset HEAD~
git add <first-part>
git commit -m "first change"
git add <second-part>
git commit -m "second change"
git rebase --continue
```

## Handling Conflicts

### During Rebase

```bash
# Git pauses at conflict
# Files shown in git status

# Resolve conflicts in files
# Remove conflict markers

# Stage resolved files
git add <file>

# Continue rebase
git rebase --continue
```

### Abort Rebase

```bash
# Return to pre-rebase state
git rebase --abort
```

### Skip Problematic Commit

```bash
# Skip current commit
git rebase --skip
```

## Safety Rules

1. **NEVER rebase public branches** (main, develop)
2. **NEVER rebase commits others have based work on**
3. **Use `--force-with-lease`** not `--force`
4. **Backup before complex rebases**: `git branch backup-branch`
5. **Understand the commits** before rebasing

## Error Handling

### Nothing to Rebase

```
Current branch is up to date.

Already rebased or no new commits to apply.
```

### Conflicts During Rebase

```
CONFLICT (content): Merge conflict in <file>

Resolve:
1. Edit file
2. git add <file>
3. git rebase --continue

Or abort: git rebase --abort
```

### Diverged After Force Push

```
Error: Others have pulled the old version.

Solutions:
1. Coordinate with team to reset
2. Never rebase shared branches again
```

## Autosquash

Automatically squash fixup commits:

```bash
# Create fixup commit
git commit --fixup=<commit-hash>

# Rebase with autosquash
git rebase -i --autosquash main
```

Git automatically arranges fixup commits.
