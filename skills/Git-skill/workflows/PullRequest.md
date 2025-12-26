# PullRequest Workflow

Create a pull request using GitHub CLI.

## Prerequisites

- Git repository with GitHub remote
- GitHub CLI (`gh`) installed and authenticated
- Feature branch with commits to merge
- Push access to repository

## Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `TO_BRANCH` | Target branch for PR | `main` |
| `FROM_BRANCH` | Source branch | Current branch |

## Workflow Steps

### Step 1: Verify Prerequisites

```bash
# Check gh CLI is available
gh --version

# Check authentication
gh auth status

# Verify current branch
git branch --show-current
```

**If `gh` not available:**
```
GitHub CLI is required for this workflow.

Install:
  macOS: brew install gh
  Linux: sudo apt install gh
  Windows: winget install GitHub.cli

Then authenticate:
  gh auth login
```

### Step 2: Ensure Branch is Pushed

```bash
# Get current branch
BRANCH=$(git branch --show-current)

# Check if branch exists on remote
git fetch origin

# Push if needed
git push -u origin $BRANCH
```

### Step 3: Gather PR Information

```bash
# Get commits in this branch vs target
git log origin/main..HEAD --oneline

# Get changed files
git diff origin/main --stat

# Get full diff for summary
git diff origin/main
```

### Step 4: Generate PR Content

**Title format:**
```
<type>(<scope>): <concise description>
```

**Description template:**
```markdown
## Summary

<2-3 bullet points describing what this PR does>

## Changes

<List of key changes>

## Testing

<How this was tested>

## Checklist

- [ ] Tests pass
- [ ] Documentation updated (if needed)
- [ ] No breaking changes (or documented)
```

### Step 5: Create Pull Request

```bash
# Create PR with title and body
gh pr create \
  --title "<type>(<scope>): <description>" \
  --body "$(cat <<'EOF'
## Summary

- <change 1>
- <change 2>
- <change 3>

## Changes

<detailed changes>

## Testing

<testing approach>
EOF
)" \
  --base main \
  --head $(git branch --show-current)
```

**With reviewers:**
```bash
gh pr create \
  --title "<title>" \
  --body "<body>" \
  --base main \
  --reviewer @username1,@username2
```

**As draft:**
```bash
gh pr create \
  --title "<title>" \
  --body "<body>" \
  --base main \
  --draft
```

### Step 6: Verify PR Created

```bash
# Show PR details
gh pr view

# Get PR URL
gh pr view --json url -q .url
```

## Output Format

```
Pull Request created!

PR #<number>: <title>
URL: <pr-url>

From: <source-branch>
To: <target-branch>

Commits: <count>
Files changed: <count>
Additions: <count>
Deletions: <count>

Status: [Draft | Ready for review]
```

## Advanced Options

### Create PR with Labels

```bash
gh pr create \
  --title "<title>" \
  --body "<body>" \
  --label "enhancement" \
  --label "needs-review"
```

### Create PR with Milestone

```bash
gh pr create \
  --title "<title>" \
  --body "<body>" \
  --milestone "v1.0"
```

### Create PR with Project

```bash
gh pr create \
  --title "<title>" \
  --body "<body>" \
  --project "Sprint 1"
```

### Create PR Linking Issues

```bash
gh pr create \
  --title "fix: resolve login issue" \
  --body "Fixes #123

## Summary
- Fixed authentication bug
- Added error handling"
```

## Error Handling

### Branch Not Pushed

```
Error: Branch not found on remote.

Run: git push -u origin $(git branch --show-current)
```

### No Commits to Merge

```
Error: No commits between main and current branch.

The branches are identical. Make commits before creating a PR.
```

### PR Already Exists

```
Error: PR already exists for this branch.

View existing PR: gh pr view
Or close it first: gh pr close
```

### Not Authenticated

```
Error: Not authenticated with GitHub.

Run: gh auth login
And follow the prompts.
```

## PR Best Practices

1. **Keep PRs focused** - One feature/fix per PR
2. **Write clear descriptions** - Help reviewers understand changes
3. **Link related issues** - Use "Fixes #123" syntax
4. **Request specific reviewers** - Don't rely on auto-assignment
5. **Use draft PRs** - For work-in-progress
6. **Respond to feedback** - Address comments promptly
