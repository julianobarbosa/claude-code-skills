---
name: using-git-worktrees
description: Git worktree management with tmux integration and task dispatch. Use when creating isolated dev environments, launching parallel feature work, running multiple Claude instances, managing worktrees, dispatching tasks to worktree terminals, or cleaning up after merge. Covers worktree creation in .claude/worktrees/, tmux window management in the current session, and command dispatch. Also use when someone says "create a worktree", "launch in a worktree", "worktree for story X", or "parallel development".
---

# Git Worktrees with tmux Integration

Create isolated workspaces, open them in tmux windows within your current session, and dispatch tasks — all in one flow.

## Core Flow

```
1. Create worktree     → git worktree add .claude/worktrees/{name} -b {branch}
2. Create tmux window  → new window in CURRENT session named {session}-{name}
3. cd into worktree    → send-keys to the new window
4. Dispatch task       → send-keys with the command to execute
```

## Workflow Routing

| Intent | Action |
|--------|--------|
| "create worktree for X" | Create → steps 1-3 only |
| "create worktree and run Y" | Create + Dispatch → steps 1-4 |
| "clean up worktree X" | Cleanup → remove worktree + tmux window + optionally delete branch |
| "list worktrees" | Show `git worktree list` |
| "analyze for parallelization" | Read `references/bmad-orchestration.md` for BMAD-specific dependency analysis |
| "merge worktree branches" | Read `references/bmad-orchestration.md` for merge workflow |

## Step 1: Create Worktree

### Safety Check

Before creating, verify `.claude/worktrees/` is git-ignored:

```bash
# Check if ignored (test with a hypothetical file)
git check-ignore .claude/worktrees/test 2>/dev/null
```

If NOT ignored, add to `.gitignore` immediately:

```bash
echo ".claude/worktrees/" >> .gitignore
# Stage and commit the gitignore change
```

### Create

```bash
REPO_ROOT=$(git rev-parse --show-toplevel)
WORKTREE_NAME="the-feature-name"
BRANCH_NAME="feature/the-feature-name"  # or bmad/story-1-3 etc.
BASE_BRANCH="main"  # or current branch

mkdir -p "$REPO_ROOT/.claude/worktrees"
git worktree add "$REPO_ROOT/.claude/worktrees/$WORKTREE_NAME" -b "$BRANCH_NAME" "$BASE_BRANCH"
```

### Verify

```bash
git worktree list
```

## Step 2: Create tmux Window

Create a new window in the **current tmux session** (not a new session). The window name follows the pattern `{current-session-name}-{worktree-name}` so it's easy to identify.

```bash
# Get current tmux session name
SESSION=$(tmux display-message -p '#S')
WINDOW_NAME="${SESSION}-${WORKTREE_NAME}"
WORKTREE_PATH="$REPO_ROOT/.claude/worktrees/$WORKTREE_NAME"

# Create window in current session, starting in worktree directory
tmux new-window -t "$SESSION" -n "$WINDOW_NAME" -c "$WORKTREE_PATH"
```

## Step 3: Ensure Working Directory

The `-c` flag in step 2 already sets the initial directory, but if you need to explicitly cd (e.g., shell profile overrides it):

```bash
tmux send-keys -t "${SESSION}:${WINDOW_NAME}" "cd '$WORKTREE_PATH'" Enter
```

## Step 4: Dispatch Task (Optional)

Send a command to the new tmux window:

```bash
# Example: launch Claude Code with a task
tmux send-keys -t "${SESSION}:${WINDOW_NAME}" "claude 'your task here'" Enter

# Example: run a BMAD skill
tmux send-keys -t "${SESSION}:${WINDOW_NAME}" "claude '/bmad-create-story story 1-3'" Enter

# Example: run any shell command
tmux send-keys -t "${SESSION}:${WINDOW_NAME}" "make test" Enter
```

For unattended execution (no permission prompts):
```bash
tmux send-keys -t "${SESSION}:${WINDOW_NAME}" "claude --dangerously-skip-permissions 'your task'" Enter
```

**Important:** Only use `--dangerously-skip-permissions` if the user explicitly requests it.

## Cleanup Workflow

After work is complete and merged:

```bash
WORKTREE_NAME="the-feature-name"
REPO_ROOT=$(git rev-parse --show-toplevel)
SESSION=$(tmux display-message -p '#S')

# 1. Kill the tmux window
tmux kill-window -t "${SESSION}:${SESSION}-${WORKTREE_NAME}" 2>/dev/null

# 2. Remove the git worktree
git worktree remove "$REPO_ROOT/.claude/worktrees/$WORKTREE_NAME"

# 3. Optionally delete the branch (only if merged)
git branch -d "$BRANCH_NAME" 2>/dev/null

# 4. Prune stale worktree references
git worktree prune
```

## Quick Reference

| Situation | Action |
|-----------|--------|
| `.claude/worktrees/` exists | Use it (verify ignored) |
| Not in `.gitignore` | Add `.claude/worktrees/` and commit |
| Not in tmux | Skip tmux steps, just create worktree and report path |
| Branch already exists | Use `git worktree add <path> <existing-branch>` (no `-b`) |
| Worktree path exists | Report error, ask user to remove or pick different name |

## Naming Conventions

| Element | Pattern | Example |
|---------|---------|---------|
| Worktree directory | `.claude/worktrees/{name}` | `.claude/worktrees/story-1-3` |
| Branch | `{convention}/{name}` | `bmad/story-1-3-deploy-nat-gateway` |
| tmux window | `{session}-{name}` | `hypera-golden-image-story-1-3` |

The branch naming convention depends on the project. Check CLAUDE.md for project-specific patterns (e.g., `bmad/story-{id}` for BMAD projects).

## Troubleshooting

**Branch already checked out:**
```bash
# Another worktree has this branch — remove it first or use a different name
git worktree list  # find which worktree has the branch
```

**tmux window name conflict:**
```bash
# Rename or kill the conflicting window
tmux kill-window -t "session:conflicting-name" 2>/dev/null
```

**Worktree not in .gitignore after adding:**
```bash
# .gitignore uses directory patterns — ensure trailing slash
# Check with: git check-ignore .claude/worktrees/testfile
```

## References

- [WORKFLOW.md](WORKFLOW.md) — Detailed step-by-step workflow with edge cases
- [references/bmad-orchestration.md](references/bmad-orchestration.md) — BMAD sprint parallelization, dependency analysis, and merge workflows
- [references/tmux-integration.md](references/tmux-integration.md) — Advanced tmux configuration for worktrees
- [scripts/setup-worktree.sh](scripts/setup-worktree.sh) — Shell script for automated worktree setup
