#!/bin/bash
# Create a git worktree with tmux window in the current session
# Usage: setup-worktree.sh <worktree-name> [branch-name] [base-branch] [task-command]
#
# Examples:
#   setup-worktree.sh story-1-3 bmad/story-1-3 main
#   setup-worktree.sh story-1-3 bmad/story-1-3 main "claude '/bmad-create-story 1-3'"

set -euo pipefail

WORKTREE_NAME="${1:?Usage: setup-worktree.sh <name> [branch] [base-branch] [task-command]}"
BRANCH_NAME="${2:-$WORKTREE_NAME}"
BASE_BRANCH="${3:-main}"
TASK_COMMAND="${4:-}"

# Ensure we're in a git repo
REPO_ROOT=$(git rev-parse --show-toplevel 2>/dev/null) || {
	echo "Error: Not in a git repository"
	exit 1
}

WORKTREE_DIR="$REPO_ROOT/.claude/worktrees"
WORKTREE_PATH="$WORKTREE_DIR/$WORKTREE_NAME"

# Create worktree directory
mkdir -p "$WORKTREE_DIR"

# Ensure .gitignore includes worktree dir
if ! git check-ignore -q "$WORKTREE_DIR/test" 2>/dev/null; then
	echo ".claude/worktrees/" >>"$REPO_ROOT/.gitignore"
	echo "Added .claude/worktrees/ to .gitignore"
fi

# Check if worktree already exists
if [ -d "$WORKTREE_PATH" ]; then
	echo "Error: Worktree already exists at $WORKTREE_PATH"
	exit 1
fi

# Create worktree
echo "Creating worktree: $WORKTREE_NAME (branch: $BRANCH_NAME from $BASE_BRANCH)"
git worktree add "$WORKTREE_PATH" -b "$BRANCH_NAME" "$BASE_BRANCH"

# Auto-detect and run project setup
cd "$WORKTREE_PATH"
if [ -f "package.json" ]; then
	echo "Installing npm dependencies..."
	npm install --silent 2>/dev/null || true
elif [ -f "go.mod" ]; then
	echo "Downloading Go modules..."
	go mod download 2>/dev/null || true
elif [ -f "pyproject.toml" ]; then
	echo "Installing Python dependencies..."
	uv sync 2>/dev/null || pip install -e ".[dev]" 2>/dev/null || true
elif [ -f "Cargo.toml" ]; then
	echo "Building Rust project..."
	cargo build 2>/dev/null || true
fi

# tmux integration
if [ -n "${TMUX:-}" ]; then
	SESSION=$(tmux display-message -p '#S')
	WINDOW_NAME="${SESSION}-${WORKTREE_NAME}"

	# Create window in current session
	tmux new-window -t "$SESSION" -n "$WINDOW_NAME" -c "$WORKTREE_PATH"
	echo "Created tmux window: $WINDOW_NAME"

	# Dispatch task if provided
	if [ -n "$TASK_COMMAND" ]; then
		sleep 0.5 # Brief pause for shell init
		tmux send-keys -t "${SESSION}:${WINDOW_NAME}" "$TASK_COMMAND" Enter
		echo "Dispatched: $TASK_COMMAND"
	fi
else
	echo "Not in tmux — skipping window creation"
fi

echo ""
echo "Worktree ready at: $WORKTREE_PATH"
echo "Branch: $BRANCH_NAME"
