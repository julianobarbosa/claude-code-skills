# Diff Workflow

Compare changes between commits, branches, or working directory.

## Prerequisites

- Git repository initialized
- Something to compare

## Basic Diff Commands

```bash
# Unstaged changes
git diff

# Staged changes
git diff --cached
git diff --staged

# All changes (staged + unstaged)
git diff HEAD
```

## Diff Types

### Working Directory Diffs

```bash
# Unstaged vs last commit
git diff

# Specific file
git diff path/to/file.js

# Specific directory
git diff src/
```

### Staged Diffs

```bash
# Staged vs last commit
git diff --cached

# Staged specific file
git diff --cached path/to/file.js
```

### Commit Diffs

```bash
# Between two commits
git diff abc1234 def5678

# Parent to commit
git diff abc1234^..abc1234

# Last commit changes
git diff HEAD~1
```

### Branch Diffs

```bash
# Current vs another branch
git diff main

# Between two branches
git diff main..feature/branch

# What's in branch but not main
git diff main...feature/branch
```

## Diff Output Formats

### Standard Patch

```bash
git diff
```

```diff
diff --git a/file.js b/file.js
index abc1234..def5678 100644
--- a/file.js
+++ b/file.js
@@ -10,7 +10,8 @@ function example() {
   console.log("before");
-  oldCode();
+  newCode();
+  additionalCode();
   console.log("after");
 }
```

### Stat Summary

```bash
git diff --stat
```

```
 src/app.js    | 10 +++++-----
 src/utils.js  |  5 +++++
 tests/app.js  |  3 +--
 3 files changed, 11 insertions(+), 7 deletions(-)
```

### Short Stat

```bash
git diff --shortstat
```

```
 3 files changed, 11 insertions(+), 7 deletions(-)
```

### Name Only

```bash
git diff --name-only
```

```
src/app.js
src/utils.js
tests/app.js
```

### Name Status

```bash
git diff --name-status
```

```
M  src/app.js
A  src/utils.js
D  tests/old.js
R  old-name.js -> new-name.js
```

Status codes: M=Modified, A=Added, D=Deleted, R=Renamed, C=Copied

## Advanced Diff Options

### Word Diff

```bash
# Color words instead of lines
git diff --word-diff

# Plain format
git diff --word-diff=plain
```

### Ignore Whitespace

```bash
# Ignore all whitespace
git diff -w

# Ignore at end of line
git diff --ignore-space-at-eol

# Ignore amount of whitespace
git diff -b
```

### Context Control

```bash
# Show more/less context lines
git diff -U10    # 10 lines of context
git diff -U0     # No context
```

### Binary Diffs

```bash
# Show binary file changes
git diff --binary

# Just note that binary changed
git diff --stat
```

## Common Scenarios

### What Did I Change?

```bash
# All uncommitted changes
git diff

# Just file names
git diff --name-only
```

### What's Staged?

```bash
# Staged changes
git diff --cached

# Stats
git diff --cached --stat
```

### Compare Branches

```bash
# Current vs main
git diff main

# What's different in feature
git diff main..feature/branch --stat
```

### Review PR Changes

```bash
# All changes in PR
git diff main...feature/branch

# Specific file in PR
git diff main...feature/branch -- path/to/file
```

### Find Changed Functions

```bash
# Show function context
git diff -p --function-context
```

### Check Specific Commit

```bash
# What changed in commit
git diff abc1234^..abc1234

# Or simpler
git show abc1234
```

### Compare Across Time

```bash
# File at two points
git diff HEAD~10:path/to/file HEAD:path/to/file

# Or between dates
git diff $(git rev-list -1 --before="1 week ago" HEAD) HEAD
```

## Diff Tools

### External Diff Tool

```bash
# Use configured difftool
git difftool

# Use specific tool
git difftool --tool=vscode
```

### Configure Difftool

```bash
# Set default
git config --global diff.tool vscode
git config --global difftool.vscode.cmd 'code --wait --diff $LOCAL $REMOTE'
```

## Output Format

Present diffs as:

```
Changes Summary
───────────────

Files Changed: 3
Insertions: +15
Deletions: -8

Modified Files:
  M  src/app.js       (+10, -5)
  A  src/utils.js     (+5)
  D  tests/old.js     (-3)

Details:
  [Show relevant diff snippets]
```

## Quick Reference

| Purpose | Command |
|---------|---------|
| Unstaged changes | `git diff` |
| Staged changes | `git diff --cached` |
| All changes | `git diff HEAD` |
| Between commits | `git diff A B` |
| Between branches | `git diff main..branch` |
| Stats only | `git diff --stat` |
| File names only | `git diff --name-only` |
| Word-level diff | `git diff --word-diff` |
| Ignore whitespace | `git diff -w` |
| Specific file | `git diff -- file` |

## Three-Dot vs Two-Dot

```bash
# Two dots: Direct comparison
git diff A..B
# Shows what B has that A doesn't

# Three dots: Common ancestor comparison
git diff A...B
# Shows what B has since diverging from A
```

Use three dots for PR reviews (what changed in feature branch since branching).
