# Git Best Practices Reference

Guidelines for effective Git usage in collaborative environments.

## Commit Practices

### Atomic Commits

Make each commit a single logical change:

```bash
# Good: Separate concerns
git add src/auth.js
git commit -m "feat(auth): add login validation"

git add src/auth.test.js
git commit -m "test(auth): add login validation tests"

# Bad: Mixed changes
git add .
git commit -m "add login and fix header and update styles"
```

### Commit Frequency

- Commit often, push regularly
- Each commit should compile and pass tests
- Don't commit broken code to shared branches

### Meaningful History

```bash
# Review before committing
git diff --cached

# Amend last commit (before push)
git commit --amend

# Interactive rebase to clean history
git rebase -i HEAD~3
```

## Branch Strategy

### Branch Naming

```bash
# Feature branches
feature/user-authentication
feature/JIRA-123-add-cart

# Bug fixes
fix/login-timeout
bugfix/header-alignment

# Hotfixes
hotfix/security-patch

# Releases
release/v2.0.0

# Experiments
experiment/new-algorithm
```

### Branch Lifecycle

```bash
# Create from updated main
git checkout main
git pull origin main
git checkout -b feature/new-feature

# Keep updated with main
git fetch origin
git rebase origin/main

# Delete after merge
git branch -d feature/new-feature
git push origin --delete feature/new-feature
```

### Protected Branches

- `main`/`master` - Production-ready code
- `develop` - Integration branch
- Never force push to protected branches
- Require pull request reviews

## Pull Request Workflow

### Before Opening PR

1. Rebase on latest main
2. Run all tests locally
3. Review your own changes
4. Write clear description

### PR Description Template

```markdown
## Summary
Brief description of changes

## Changes Made
- Added X feature
- Fixed Y bug
- Updated Z documentation

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed

## Screenshots (if UI changes)

## Related Issues
Closes #123
```

### Review Process

1. Request specific reviewers
2. Address all feedback
3. Re-request review after changes
4. Squash commits if needed before merge

## Merge Strategies

### Merge Commit

```bash
git merge feature/branch
```

Preserves full history. Good for feature branches.

### Squash Merge

```bash
git merge --squash feature/branch
```

Combines all commits into one. Good for cleanup.

### Rebase Merge

```bash
git rebase main
git checkout main
git merge feature/branch --ff-only
```

Linear history. Best for small changes.

### When to Use Each

| Strategy | Use Case |
|----------|----------|
| Merge | Feature branches with meaningful commits |
| Squash | Messy history, WIP commits |
| Rebase | Linear history, small changes |

## Conflict Resolution

### Prevention

```bash
# Update frequently
git fetch origin
git rebase origin/main

# Communicate about shared files
# Keep changes focused
```

### Resolution Steps

```bash
# 1. Identify conflicts
git status

# 2. Open conflicted files
# Look for conflict markers:
# <<<<<<< HEAD
# your changes
# =======
# their changes
# >>>>>>> branch-name

# 3. Resolve manually or with tool
git mergetool

# 4. Stage resolved files
git add resolved-file.js

# 5. Continue operation
git rebase --continue
# or
git merge --continue
```

## Git Hooks

### Common Hooks

```bash
# pre-commit: Run before commit
- Lint code
- Run tests
- Check formatting

# commit-msg: Validate message
- Enforce conventional commits
- Check length

# pre-push: Run before push
- Run full test suite
- Check for secrets
```

### Setup with Husky

```json
// package.json
{
  "husky": {
    "hooks": {
      "pre-commit": "npm run lint",
      "commit-msg": "commitlint -E HUSKY_GIT_PARAMS"
    }
  }
}
```

## Stash Best Practices

```bash
# Always name stashes
git stash push -m "WIP: feature X halfway done"

# List with context
git stash list

# Apply specific stash
git stash apply stash@{2}

# Clean up old stashes
git stash drop stash@{0}
```

## Tagging

### Semantic Versioning

```bash
# Annotated tags (recommended)
git tag -a v1.0.0 -m "Release version 1.0.0"

# Push tags
git push origin v1.0.0
git push origin --tags
```

### Tag Naming

```
v1.0.0     # Release
v1.0.0-rc1 # Release candidate
v1.0.0-beta.1 # Beta
```

## Repository Hygiene

### .gitignore

```gitignore
# Dependencies
node_modules/
vendor/

# Build outputs
dist/
build/

# Environment
.env
.env.local

# IDE
.idea/
.vscode/

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/
```

### Large Files

```bash
# Use Git LFS for large files
git lfs install
git lfs track "*.psd"
git lfs track "*.zip"
```

### Repository Size

- Don't commit binaries
- Don't commit dependencies
- Don't commit build artifacts
- Use `.gitignore` aggressively

## Collaboration Tips

### Communication

- Write descriptive commit messages
- Document complex changes
- Comment on PRs constructively

### Code Review

- Review promptly
- Be specific in feedback
- Approve when ready, not just okay

### Synchronization

```bash
# Start of day
git fetch --all --prune
git pull origin main

# Before creating PR
git fetch origin
git rebase origin/main
```

## Troubleshooting

### Common Issues

```bash
# Undo last commit (keep changes)
git reset --soft HEAD~1

# Discard local changes
git checkout -- file.js

# Find lost commits
git reflog

# Recover deleted branch
git checkout -b recovered-branch abc1234
```

### Emergency Recovery

```bash
# Force update to remote state
git fetch origin
git reset --hard origin/main

# Cherry-pick specific commit
git cherry-pick abc1234
```
