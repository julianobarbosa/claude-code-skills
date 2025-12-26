# Status Workflow

Check repository status, changes, and sync state.

## Prerequisites

- Git repository initialized

## Basic Status

```bash
# Full status
git status

# Short format
git status -s

# With branch tracking info
git status -sb
```

## Status Output Explained

### Full Status Format

```
On branch main
Your branch is ahead of 'origin/main' by 2 commits.

Changes to be committed:
  (staged)
        modified:   file1.js
        new file:   file2.js

Changes not staged for commit:
  (unstaged)
        modified:   file3.js
        deleted:    file4.js

Untracked files:
  (new files not yet added)
        file5.js
```

### Short Status Format

```
 M file1.js    # Modified (unstaged)
M  file2.js    # Modified (staged)
MM file3.js    # Modified (staged + unstaged)
A  file4.js    # Added (staged)
 D file5.js    # Deleted (unstaged)
D  file6.js    # Deleted (staged)
?? file7.js    # Untracked
!! ignored.js  # Ignored
```

**Position meanings:**
- First column: Staged changes
- Second column: Unstaged changes

## Workflow Steps

### Step 1: Check Overall Status

```bash
# Get full picture
git status

# Quick view
git status -sb
```

### Step 2: Review Specific Changes

```bash
# Unstaged changes
git diff

# Staged changes
git diff --cached

# All changes (staged + unstaged)
git diff HEAD
```

### Step 3: Check Remote Sync

```bash
# Fetch remote info
git fetch origin

# Check ahead/behind
git status

# Detailed comparison
git log origin/main..HEAD --oneline   # Local not on remote
git log HEAD..origin/main --oneline   # Remote not in local
```

### Step 4: List Changed Files

```bash
# Names only
git diff --name-only

# With status
git diff --name-status

# Stats summary
git diff --stat
```

## Detailed Status Commands

### Branch Information

```bash
# Current branch
git branch --show-current

# All branches with details
git branch -vv

# Remote tracking info
git remote show origin
```

### Commit Status

```bash
# Last commit
git log -1

# Unpushed commits
git log origin/main..HEAD --oneline

# Commits to pull
git log HEAD..origin/main --oneline
```

### File Status

```bash
# Check specific file
git status -- path/to/file

# List ignored files
git status --ignored

# Show ignored too (short)
git status -s --ignored
```

### Worktree Status

```bash
# Check if in repo
git rev-parse --is-inside-work-tree

# Get repo root
git rev-parse --show-toplevel

# Current directory relative to root
git rev-parse --show-prefix
```

## Common Status Scenarios

### Clean Working Directory

```
On branch main
Your branch is up to date with 'origin/main'.

nothing to commit, working tree clean
```

### Ready to Commit

```
On branch feature/xyz
Changes to be committed:
        modified:   src/app.js
        new file:   src/utils.js

All staged - ready for: git commit
```

### Need to Stage

```
On branch feature/xyz
Changes not staged for commit:
        modified:   src/app.js

Stage with: git add src/app.js
```

### Ahead of Remote

```
Your branch is ahead of 'origin/main' by 3 commits.

Push with: git push origin main
```

### Behind Remote

```
Your branch is behind 'origin/main' by 2 commits.

Pull with: git pull origin main
```

### Diverged

```
Your branch and 'origin/main' have diverged,
and have 2 and 3 different commits each.

Options:
1. Merge: git pull origin main
2. Rebase: git rebase origin/main
```

## Output Format

Provide status in this structured format:

```
Repository Status
─────────────────

Branch: <current-branch>
Remote: <tracking-branch>
Status: [Clean | Changes pending | Conflicts]

Sync Status:
  Ahead: <count> commits
  Behind: <count> commits

Changes:
  Staged:
    - <file1> (modified)
    - <file2> (new file)

  Unstaged:
    - <file3> (modified)
    - <file4> (deleted)

  Untracked:
    - <file5>
    - <file6>

Recommendations:
  - <action to take>
```

## Quick Commands Reference

| Command | Purpose |
|---------|---------|
| `git status` | Full status |
| `git status -s` | Short format |
| `git status -sb` | Short with branch |
| `git diff` | Unstaged changes |
| `git diff --cached` | Staged changes |
| `git diff --stat` | Summary stats |
| `git log -1` | Last commit |
| `git branch -vv` | Branch tracking |

## Safety Checks

Before major operations, always check:

1. **Current branch** - Am I on the right branch?
2. **Uncommitted changes** - Will they be lost?
3. **Sync status** - Am I up to date with remote?
4. **Staged vs unstaged** - What exactly will be committed?
