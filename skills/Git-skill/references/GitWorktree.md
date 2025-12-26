# Git Worktree Reference

Comprehensive guide for managing multiple working trees in a single repository.

## What is a Worktree?

A Git worktree allows you to check out multiple branches simultaneously, each in its own directory. All worktrees share the same Git history and objects, but have independent working directories and index files.

```
Main Repository (.git)
    │
    ├── main-worktree/     ← Branch: main
    ├── feature-worktree/  ← Branch: feature/auth
    └── hotfix-worktree/   ← Branch: hotfix/urgent
```

## When to Use Worktrees

| Scenario | Benefit |
|----------|---------|
| Urgent hotfix while on feature branch | No stashing required, context preserved |
| Code review without losing work | Isolated review environment |
| Comparing behavior across branches | Side-by-side testing |
| Long-running builds | Continue development while building |
| Testing migrations | Run old and new code simultaneously |
| Parallel feature development | Multiple features without branch switching |

## Core Commands Reference

### List Worktrees

```bash
# Basic list
git worktree list

# Machine-readable format
git worktree list --porcelain

# Output example:
# /path/to/main      abc1234 [main]
# /path/to/feature   def5678 [feature/x]
```

### Add Worktree

```bash
# From existing branch
git worktree add <path> <branch>

# Create new branch in worktree
git worktree add -b <new-branch> <path> [start-point]

# Detached HEAD (specific commit)
git worktree add --detach <path> <commit>

# Track remote branch
git worktree add --track -b <local> <path> origin/<remote>
```

### Remove Worktree

```bash
# Standard removal (must be clean)
git worktree remove <path>

# Force removal (discards changes)
git worktree remove --force <path>

# Manual cleanup
rm -rf <path>
git worktree prune
```

### Move Worktree

```bash
git worktree move <source> <destination>
```

### Lock/Unlock

```bash
# Lock (prevent pruning)
git worktree lock <path>
git worktree lock --reason "On external drive" <path>

# Unlock
git worktree unlock <path>
```

### Prune Stale References

```bash
# Remove stale entries
git worktree prune

# Dry run (preview)
git worktree prune --dry-run

# Verbose
git worktree prune -v
```

### Repair Worktree

```bash
# Repair admin files
git worktree repair [<path>...]
```

## Directory Organization Patterns

### Sibling Pattern (Recommended)

```
~/projects/
├── my-project/              # Main worktree
├── my-project-feature-x/    # Feature worktree
├── my-project-hotfix/       # Hotfix worktree
└── my-project-review/       # Review worktree
```

### Nested Pattern

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

### Bare Repository Pattern

For heavy worktree usage:

```bash
# Clone as bare
git clone --bare https://github.com/user/repo.git repo.git

# Create worktrees from bare
cd repo.git
git worktree add ../main main
git worktree add ../develop develop
```

## Best Practices

### Do

1. **Name worktrees descriptively** - Include branch purpose in path
2. **Prune regularly** - Clean up stale references
3. **Lock remote worktrees** - Prevent accidental pruning
4. **Keep structure flat** - Avoid deeply nested worktrees
5. **Share fetch results** - One fetch updates all worktrees
6. **Use for isolation** - Keep unrelated work separated

### Don't

1. **Never delete main worktree** - All others depend on it
2. **Don't checkout same branch twice** - Git prevents this
3. **Don't nest worktrees** - Creates confusion
4. **Don't leave dirty worktrees** - Clean up before removing
5. **Don't ignore lock warnings** - Check before forcing

## Common Workflows

### Emergency Hotfix

```bash
# Currently on feature branch
git worktree add -b hotfix/urgent ../hotfix main

# Fix issue
cd ../hotfix
# ... make changes ...
git commit -am "fix: critical issue"
git push origin hotfix/urgent

# Return to feature (context preserved)
cd ../my-project
```

### Code Review

```bash
# Create review worktree
git fetch origin
git worktree add ../review-pr-123 origin/feature/pr-123

# Review
cd ../review-pr-123
# ... run tests, inspect code ...

# Cleanup
git worktree remove ../review-pr-123
```

### Parallel Builds

```bash
# Build multiple versions simultaneously
git worktree add ../build-staging staging
git worktree add ../build-prod production

# Parallel builds
cd ../build-staging && npm run build &
cd ../build-prod && npm run build &
wait
```

## Error Troubleshooting

### Branch Already Checked Out

```
Error: '<branch>' is already checked out at '<path>'
```

**Solutions:**
1. Use a different branch name
2. Remove existing worktree: `git worktree remove <path>`
3. Force (dangerous): `git checkout --ignore-other-worktrees`

### Path Already Exists

```
Error: '<path>' already exists
```

**Solutions:**
1. Remove directory: `rm -rf <path>`
2. Choose different path
3. If valid worktree: `git worktree repair <path>`

### Cannot Remove Dirty Worktree

```
Error: '<path>' contains modified or untracked files
```

**Solutions:**
1. Commit or stash changes first
2. Force remove: `git worktree remove --force <path>`

### Stale Worktree Reference

```
Warning: worktree at '<path>' is missing
```

**Solution:**
```bash
git worktree prune
```

### Worktree Locked

```
Error: '<path>' is locked
```

**Solutions:**
1. Check reason: `git worktree list`
2. Unlock: `git worktree unlock <path>`

## Performance Notes

| Aspect | Impact |
|--------|--------|
| Disk space | Shared .git objects, separate working copies |
| Memory | Each open IDE adds file watchers |
| Network | Single fetch updates all worktrees |
| CPU | Multiple builds can run in parallel |

## Integration Tips

### IDE Support

- **VS Code**: Open each worktree as separate workspace
- **JetBrains**: Use separate project windows
- **vim/neovim**: Works seamlessly with any worktree

### CI/CD

```bash
# Status across all worktrees
for wt in $(git worktree list --porcelain | grep "^worktree" | cut -d' ' -f2); do
  echo "=== $wt ==="
  git -C "$wt" status -s
done
```

### Shell Aliases

```bash
# Add to ~/.bashrc or ~/.zshrc
alias gwl='git worktree list'
alias gwa='git worktree add'
alias gwr='git worktree remove'
alias gwp='git worktree prune'
```

## Quick Reference Card

| Command | Purpose |
|---------|---------|
| `git worktree list` | List all worktrees |
| `git worktree add <path> <branch>` | Add worktree for branch |
| `git worktree add -b <new> <path>` | Add with new branch |
| `git worktree remove <path>` | Remove worktree |
| `git worktree prune` | Clean stale entries |
| `git worktree lock <path>` | Prevent pruning |
| `git worktree repair` | Fix admin files |
