# Worktree Workflow

Create, manage, and work with multiple working trees simultaneously.

## Overview

Git worktrees allow you to check out multiple branches at once, each in its own directory. This enables parallel development without stashing changes or creating multiple clones.

## Prerequisites

- Git 2.5+ installed
- Git repository initialized
- Sufficient disk space for additional working directories

## Operations

### List Worktrees

```bash
# List all worktrees
git worktree list

# Verbose output with more details
git worktree list --porcelain
```

**Output example:**
```
/path/to/main-repo      abc1234 [main]
/path/to/feature-tree   def5678 [feature/auth]
/path/to/hotfix-tree    ghi9012 [hotfix/urgent]
```

### Add New Worktree

**From existing branch:**
```bash
# Add worktree for existing branch
git worktree add <path> <branch>

# Example
git worktree add ../feature-auth feature/user-authentication
```

**Create new branch in worktree:**
```bash
# Add worktree with new branch
git worktree add -b <new-branch> <path> [<start-point>]

# Example: new branch from main
git worktree add -b feature/new-feature ../new-feature main

# Example: new branch from current HEAD
git worktree add -b hotfix/urgent ../hotfix-urgent
```

**From detached HEAD:**
```bash
# Checkout specific commit without branch
git worktree add --detach <path> <commit>

# Example
git worktree add --detach ../investigate abc1234
```

**From remote branch:**
```bash
# Fetch first
git fetch origin

# Create worktree tracking remote branch
git worktree add -b local-name <path> origin/remote-branch

# Or track with same name
git worktree add --track -b feature/x ../feature-x origin/feature/x
```

### Remove Worktree

**Standard removal:**
```bash
# Remove worktree (after it's clean)
git worktree remove <path>

# Example
git worktree remove ../feature-auth
```

**Force removal:**
```bash
# Force remove (discards changes)
git worktree remove --force <path>

# Or manually delete and prune
rm -rf <path>
git worktree prune
```

### Move Worktree

```bash
# Move worktree to new location
git worktree move <source> <destination>

# Example
git worktree move ../old-location ../new-location
```

### Lock/Unlock Worktree

Prevent worktree from being pruned (useful for removable drives or network mounts):

```bash
# Lock worktree
git worktree lock <path>
git worktree lock --reason "On external drive" <path>

# Unlock worktree
git worktree unlock <path>

# List shows locked status
git worktree list
```

### Prune Stale Worktrees

```bash
# Remove stale worktree references
git worktree prune

# Dry run - see what would be pruned
git worktree prune --dry-run

# Verbose output
git worktree prune -v
```

### Repair Worktree

```bash
# Repair worktree admin files
git worktree repair [<path>...]

# Repair from within worktree
cd /path/to/worktree
git worktree repair
```

## Common Workflows

### Parallel Feature Development

```bash
# Start from main repo
cd /path/to/main-repo

# Create worktree for new feature
git worktree add -b feature/auth ../auth-feature main

# Work in the new worktree
cd ../auth-feature
# ... make changes, commit ...

# Meanwhile, in another terminal, work on main repo
cd /path/to/main-repo
# ... different work here ...
```

### Hotfix While Working on Feature

```bash
# Currently working on feature branch
pwd
# /path/to/project

# Create hotfix worktree without losing context
git worktree add -b hotfix/critical ../hotfix main

# Fix the issue
cd ../hotfix
# ... apply fix ...
git commit -am "fix: critical security issue"
git push origin hotfix/critical

# Return to feature work
cd /path/to/project
# Context preserved!
```

### Code Review in Separate Directory

```bash
# Create worktree for PR review
git fetch origin
git worktree add ../review-pr-123 origin/feature/pr-123

# Review the code
cd ../review-pr-123
# ... run tests, inspect code ...

# Clean up after review
git worktree remove ../review-pr-123
```

### Testing Different Versions

```bash
# Create worktrees for multiple versions
git worktree add ../v1.0 v1.0.0
git worktree add ../v2.0 v2.0.0
git worktree add ../main-test main

# Run comparative tests across versions
```

### Build Different Branches Simultaneously

```bash
# Create worktrees for parallel builds
git worktree add ../build-staging staging
git worktree add ../build-prod production

# Run builds in parallel (different terminals)
cd ../build-staging && npm run build &
cd ../build-prod && npm run build &
```

## Directory Structure Best Practices

**Recommended layout:**
```
~/projects/
├── my-project/              # Main worktree (bare or with main branch)
├── my-project-feature-x/    # Feature worktree
├── my-project-hotfix/       # Hotfix worktree
└── my-project-review/       # Review worktree
```

**Or nested approach:**
```
~/projects/
└── my-project/
    ├── main/                # Main branch
    ├── features/
    │   ├── auth/            # feature/auth
    │   └── api/             # feature/api
    └── hotfixes/
        └── critical/        # hotfix/critical
```

## Bare Repository Pattern

For heavy worktree usage, consider a bare repository:

```bash
# Clone as bare repo
git clone --bare https://github.com/user/repo.git repo.git

# Create worktrees from bare repo
cd repo.git
git worktree add ../main main
git worktree add ../develop develop
git worktree add ../feature ../feature feature/x

# Main worktree list
git worktree list
```

## Safety Rules

1. **Never delete main worktree** - All others depend on it
2. **Check for uncommitted changes** before removing worktrees
3. **Prune regularly** - Clean up stale references
4. **Lock remote worktrees** - Prevent accidental pruning
5. **Avoid nested worktrees** - Keep directory structure flat
6. **Don't checkout same branch twice** - Git prevents this

## Error Handling

### Branch Already Checked Out

```
Error: '<branch>' is already checked out at '<path>'

This is a safety feature. Options:
1. Use a different branch
2. Remove existing worktree: git worktree remove <path>
3. Force (DANGER): git checkout --ignore-other-worktrees
```

### Worktree Path Already Exists

```
Error: '<path>' already exists

Options:
1. Remove existing directory: rm -rf <path>
2. Choose different path
3. If it's a valid worktree: git worktree repair <path>
```

### Stale Worktree Reference

```
Warning: worktree at '<path>' is missing

Run:
  git worktree prune
```

### Cannot Remove Dirty Worktree

```
Error: '<path>' contains modified or untracked files

Options:
1. Commit or stash changes
2. Force remove: git worktree remove --force <path>
```

### Worktree Locked

```
Error: '<path>' is locked

Check lock reason:
  git worktree list

Unlock if safe:
  git worktree unlock <path>
```

## Performance Considerations

- **Disk space**: Each worktree shares .git objects but has its own working copy
- **Memory**: Multiple worktrees = multiple file watchers if IDE is open
- **Network**: Only one fetch needed - all worktrees share objects
- **IDE integration**: Some IDEs handle worktrees better than others

## Integration with Other Commands

```bash
# Show status across all worktrees
for wt in $(git worktree list --porcelain | grep "^worktree" | cut -d' ' -f2); do
  echo "=== $wt ==="
  git -C "$wt" status -s
done

# Fetch updates for all worktrees (only needed once)
git fetch --all

# Push from any worktree (all share same remote config)
git push origin feature/branch
```
