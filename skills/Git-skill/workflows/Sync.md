# Sync Workflow

Synchronize local branch with remote repository.

## Prerequisites

- Git repository initialized
- Remote configured (origin)
- Network access to remote

## Basic Sync Operations

### Fetch (Download Only)

```bash
# Fetch all branches
git fetch origin

# Fetch specific branch
git fetch origin main

# Fetch and prune deleted branches
git fetch --prune origin
```

### Pull (Fetch + Merge)

```bash
# Pull current branch
git pull origin $(git branch --show-current)

# Pull with rebase
git pull --rebase origin main

# Pull and autostash
git pull --autostash origin main
```

### Push (Upload)

```bash
# Push current branch
git push origin $(git branch --show-current)

# Push and set upstream
git push -u origin $(git branch --show-current)

# Push all branches
git push origin --all
```

## Sync Workflow Steps

### Step 1: Check Current State

```bash
# Current branch
git branch --show-current

# Current sync status
git status

# Uncommitted changes?
git status --porcelain
```

### Step 2: Fetch Latest

```bash
# Get latest from remote
git fetch origin

# Check what's new
git log HEAD..origin/$(git branch --show-current) --oneline
```

### Step 3: Review Changes

```bash
# See what will be pulled
git log HEAD..origin/main --oneline

# See file changes
git diff HEAD..origin/main --stat
```

### Step 4: Pull Changes

```bash
# Standard pull (merge)
git pull origin main

# Or with rebase (cleaner history)
git pull --rebase origin main
```

### Step 5: Push Local Changes

```bash
# Push to remote
git push origin $(git branch --show-current)
```

### Step 6: Verify Sync

```bash
# Confirm up to date
git status
```

## Sync Strategies

### Merge Strategy (Default)

```bash
git pull origin main
```

Creates merge commit if diverged. Preserves all history.

### Rebase Strategy

```bash
git pull --rebase origin main
```

Replays your commits on top of remote. Linear history.

**Set as default:**
```bash
git config pull.rebase true
```

### Fast-Forward Only

```bash
git pull --ff-only origin main
```

Fails if not fast-forwardable. Safest option.

## Common Scenarios

### Update Feature Branch from Main

```bash
# On feature branch
git checkout feature/my-feature

# Fetch latest main
git fetch origin main

# Rebase onto main
git rebase origin/main

# Force push if already pushed
git push --force-with-lease origin feature/my-feature
```

### Sync Fork with Upstream

```bash
# Add upstream remote (once)
git remote add upstream https://github.com/original/repo.git

# Fetch upstream
git fetch upstream

# Merge upstream into local main
git checkout main
git merge upstream/main

# Push to your fork
git push origin main
```

### Recover from Diverged State

```bash
# Option 1: Merge (keeps both histories)
git pull origin main

# Option 2: Rebase (linear history)
git fetch origin
git rebase origin/main

# Option 3: Reset to remote (LOSES local commits)
# DANGER - only if local commits are disposable
git fetch origin
git reset --hard origin/main
```

### Pull with Local Changes

```bash
# Option 1: Stash, pull, pop
git stash push -m "before pull"
git pull origin main
git stash pop

# Option 2: Autostash
git pull --autostash origin main

# Option 3: Commit first
git add -A
git commit -m "wip: save before pull"
git pull origin main
```

## Handling Conflicts

### During Pull

```bash
# Conflicts shown after pull
git status

# Resolve conflicts in files
# Remove conflict markers

# Stage resolved files
git add <file>

# Complete merge
git commit
```

### During Rebase

```bash
# Conflicts during rebase
git status

# Resolve conflicts
git add <file>

# Continue rebase
git rebase --continue

# Or abort
git rebase --abort
```

## Safety Features

### Force Push Protection

```bash
# Use --force-with-lease (safer than --force)
git push --force-with-lease origin feature/branch
```

This fails if remote has new commits you haven't fetched.

### Before Pull Checklist

1. Check for uncommitted changes: `git status`
2. Stash or commit them
3. Verify you're on correct branch
4. Fetch first to preview: `git fetch origin`

## Error Handling

### Push Rejected

```
Error: Updates were rejected because the remote contains work
that you do not have locally.

Resolution:
  git pull origin <branch>
  # Resolve any conflicts
  git push origin <branch>
```

### Cannot Pull with Local Changes

```
Error: Your local changes would be overwritten by merge.

Options:
1. Commit: git add -A && git commit -m "wip"
2. Stash: git stash push -m "before pull"
3. Discard: git checkout -- . (CAUTION)
```

### Divergent Branches

```
Error: Branches have diverged.

Options:
1. Merge: git pull origin main
2. Rebase: git pull --rebase origin main
3. Reset: git reset --hard origin/main (DANGER)
```

## Quick Reference

| Task | Command |
|------|---------|
| Fetch all | `git fetch origin` |
| Pull current | `git pull` |
| Pull with rebase | `git pull --rebase` |
| Push current | `git push` |
| Push new branch | `git push -u origin <branch>` |
| Sync fork | `git fetch upstream && git merge upstream/main` |
| Force push safely | `git push --force-with-lease` |
