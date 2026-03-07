# Git Worktrees Workflow

Detailed step-by-step for creating worktrees with tmux integration and task dispatch.

## Phase 1: Pre-flight Checks

### 1.1 Verify Git Repository

```bash
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)
if [ -z "$REPO_ROOT" ]; then
  echo "Error: Not in a git repository"
  exit 1
fi
```

### 1.2 Verify tmux Session

```bash
if [ -z "$TMUX" ]; then
  echo "Warning: Not in a tmux session — tmux window creation will be skipped"
  TMUX_AVAILABLE=false
else
  SESSION=$(tmux display-message -p '#S')
  TMUX_AVAILABLE=true
fi
```

### 1.3 Ensure Worktree Directory is Ignored

```bash
mkdir -p "$REPO_ROOT/.claude/worktrees"

# Test if the directory is ignored
if ! git check-ignore -q "$REPO_ROOT/.claude/worktrees/test" 2>/dev/null; then
  # Add to .gitignore
  echo ".claude/worktrees/" >> "$REPO_ROOT/.gitignore"
  echo "Added .claude/worktrees/ to .gitignore"
  # Note: Don't auto-commit — let the user decide
fi
```

### 1.4 Verify Clean State (Optional)

If creating worktrees for parallel work, a clean working tree avoids confusion:

```bash
if [ -n "$(git status --porcelain)" ]; then
  echo "Warning: Working tree has uncommitted changes"
  echo "Worktree creation will proceed, but consider committing first"
fi
```

## Phase 2: Create Worktree

### 2.1 Determine Parameters

Required:
- `WORKTREE_NAME` — short identifier (e.g., `story-1-3`)
- `BRANCH_NAME` — git branch name (e.g., `bmad/story-1-3-deploy-nat-gateway`)
- `BASE_BRANCH` — branch to fork from (e.g., `main`, current branch)

### 2.2 Create

```bash
WORKTREE_PATH="$REPO_ROOT/.claude/worktrees/$WORKTREE_NAME"

# Check if path already exists
if [ -d "$WORKTREE_PATH" ]; then
  echo "Error: Worktree already exists at $WORKTREE_PATH"
  echo "Remove it first: git worktree remove $WORKTREE_PATH"
  exit 1
fi

# Create with new branch
git worktree add "$WORKTREE_PATH" -b "$BRANCH_NAME" "$BASE_BRANCH"

# Or attach to existing branch
# git worktree add "$WORKTREE_PATH" "$BRANCH_NAME"
```

### 2.3 Project Setup (Auto-detect)

```bash
cd "$WORKTREE_PATH"

# Node.js
[ -f package.json ] && npm install

# Python
[ -f pyproject.toml ] && uv sync 2>/dev/null || pip install -e ".[dev]" 2>/dev/null
[ -f requirements.txt ] && pip install -r requirements.txt

# Go
[ -f go.mod ] && go mod download

# Rust
[ -f Cargo.toml ] && cargo build
```

### 2.4 Verify

```bash
git worktree list
echo "Worktree ready at: $WORKTREE_PATH"
echo "Branch: $BRANCH_NAME (based on $BASE_BRANCH)"
```

## Phase 3: tmux Window

Skip this phase if `TMUX_AVAILABLE=false`.

### 3.1 Create Window

```bash
WINDOW_NAME="${SESSION}-${WORKTREE_NAME}"

# Create window in current session, starting in worktree directory
tmux new-window -t "$SESSION" -n "$WINDOW_NAME" -c "$WORKTREE_PATH"

echo "Created tmux window: $WINDOW_NAME in session $SESSION"
```

### 3.2 Verify Directory

```bash
# The -c flag should handle this, but verify
tmux send-keys -t "${SESSION}:${WINDOW_NAME}" "pwd" Enter
```

## Phase 4: Dispatch Task (Optional)

Only execute if the user provided a task/command to run.

### 4.1 Send Command

```bash
TASK_COMMAND="claude '/bmad-create-story story 1-3'"  # example

tmux send-keys -t "${SESSION}:${WINDOW_NAME}" "$TASK_COMMAND" Enter

echo "Dispatched task to window $WINDOW_NAME"
```

### 4.2 Monitor

The user can switch to the window to monitor progress:
- `Ctrl-b` then window number to switch
- `tmux select-window -t "${SESSION}:${WINDOW_NAME}"` from another pane

## Phase 5: Cleanup

After work is done and merged back.

### 5.1 Kill tmux Window

```bash
tmux kill-window -t "${SESSION}:${WINDOW_NAME}" 2>/dev/null
```

### 5.2 Remove Worktree

```bash
git worktree remove "$WORKTREE_PATH"
```

### 5.3 Delete Branch (if merged)

```bash
git branch -d "$BRANCH_NAME" 2>/dev/null
```

### 5.4 Prune

```bash
git worktree prune
```

## Edge Cases

### Multiple Worktrees in Parallel

Create each one sequentially — each gets its own tmux window:

```bash
for story in "1-3" "1-4" "2-1"; do
  # Each iteration creates worktree + tmux window
  # Use unique WORKTREE_NAME and BRANCH_NAME per story
done
```

### Worktree from Remote Branch

```bash
git fetch origin
git worktree add "$WORKTREE_PATH" "origin/feature-branch"
```

### Resume After Disconnect

Worktrees persist across tmux detach/reattach. If the tmux window was lost:

```bash
# Recreate window for existing worktree
tmux new-window -t "$SESSION" -n "$WINDOW_NAME" -c "$WORKTREE_PATH"
```
