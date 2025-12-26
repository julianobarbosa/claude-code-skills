# Log Workflow

View commit history and logs.

## Prerequisites

- Git repository initialized
- Commits to view

## Basic Log Commands

```bash
# Default log
git log

# One line per commit
git log --oneline

# With graph
git log --oneline --graph

# All branches
git log --oneline --graph --all
```

## Log Formatting

### Compact Formats

```bash
# One line
git log --oneline

# Short format
git log --format=short

# Full format
git log --format=full

# Custom format
git log --format="%h %an %s"
```

### Custom Format Placeholders

| Placeholder | Meaning |
|-------------|---------|
| `%H` | Full commit hash |
| `%h` | Short hash |
| `%an` | Author name |
| `%ae` | Author email |
| `%ad` | Author date |
| `%ar` | Author date (relative) |
| `%cn` | Committer name |
| `%s` | Subject (first line) |
| `%b` | Body |
| `%d` | Ref names |

**Example custom format:**
```bash
git log --format="%h - %an, %ar : %s"
# abc1234 - John Doe, 2 days ago : Add feature
```

### Visual Formats

```bash
# Graph view
git log --graph --oneline --all

# Decorated (show branches/tags)
git log --oneline --decorate

# Stat summary
git log --stat

# Full patch
git log -p
```

## Filtering Logs

### By Count

```bash
# Last N commits
git log -5

# Skip first N
git log --skip=5 -10
```

### By Date

```bash
# After date
git log --after="2024-01-01"

# Before date
git log --before="2024-12-31"

# Date range
git log --after="2024-01-01" --before="2024-06-30"

# Relative dates
git log --after="2 weeks ago"
git log --since="yesterday"
```

### By Author

```bash
# By author name
git log --author="John"

# By email
git log --author="john@example.com"

# Multiple authors
git log --author="John\|Jane"
```

### By Message

```bash
# Search in commit message
git log --grep="bug fix"

# Case insensitive
git log --grep="BUG" -i

# Regex
git log --grep="^feat:"
```

### By File

```bash
# Commits affecting file
git log -- path/to/file.js

# Multiple files
git log -- src/*.js tests/*.js

# Renamed files
git log --follow -- new-name.js
```

### By Content

```bash
# Commits changing specific string
git log -S"functionName"

# With regex
git log -G"function.*Name"
```

### By Branch/Range

```bash
# Commits in branch not in main
git log main..feature/branch

# Commits in either, not both
git log main...feature/branch

# Commits reachable from branch
git log feature/branch
```

## Common Use Cases

### View Recent Activity

```bash
git log --oneline -20
```

### Find When Something Changed

```bash
# When was file changed
git log --oneline -- path/to/file

# What changed in file
git log -p -- path/to/file
```

### Find Who Changed Something

```bash
# Line-by-line blame
git blame path/to/file

# With log
git log --format="%h %an %s" -- path/to/file
```

### Review PR Commits

```bash
# Commits in branch vs main
git log main..feature/branch --oneline

# With changes
git log main..feature/branch -p
```

### Find Breaking Commit

```bash
# Bisect for bug introduction
git bisect start
git bisect bad HEAD
git bisect good v1.0.0
# Test each commit Git checks out
git bisect good  # or bad
git bisect reset
```

### Daily Standup Log

```bash
# My commits since yesterday
git log --author="$(git config user.name)" --since="yesterday" --oneline
```

## Output Format

Present log results as:

```
Commit History
──────────────

Recent commits (last 10):

  abc1234  2h ago   John Doe     feat: add user auth
  def5678  1d ago   Jane Smith   fix: resolve login bug
  ghi9012  2d ago   John Doe     docs: update README

Summary:
  Total: 10 commits
  Authors: 2
  Date range: Dec 20 - Dec 25, 2024
```

## Useful Aliases

```bash
# Add to ~/.gitconfig
[alias]
  lg = log --oneline --graph --decorate
  ll = log --format='%h %an %s' -10
  hist = log --pretty=format:'%h %ad | %s%d [%an]' --date=short
  today = log --since=midnight --oneline
  week = log --since='1 week ago' --oneline
```

## Quick Reference

| Purpose | Command |
|---------|---------|
| Last 10 commits | `git log --oneline -10` |
| Graph view | `git log --oneline --graph --all` |
| By author | `git log --author="name"` |
| By date | `git log --after="date"` |
| By file | `git log -- file` |
| Search message | `git log --grep="text"` |
| Search content | `git log -S"code"` |
| Branch diff | `git log main..branch` |
| With changes | `git log -p` |
| Stats only | `git log --stat` |
