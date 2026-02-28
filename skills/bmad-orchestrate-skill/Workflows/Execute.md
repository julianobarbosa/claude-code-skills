# Execute Workflow

Set up git worktrees and tmux sessions to run BMAD workflows in parallel via Claude Code.

## Voice Notification

```bash
curl -s -X POST http://localhost:8888/notify \
  -H "Content-Type: application/json" \
  -d '{"message": "Running Execute in BmadOrchestrate to launch parallel worktrees"}' \
  > /dev/null 2>&1 &
```

Running the **Execute** workflow in the **BmadOrchestrate** skill to launch parallel worktrees...

## Prerequisites

- The **Analyze** workflow has been run and a phase plan exists
- Or the user provides explicit instructions on what to parallelize
- Git working tree is clean (no uncommitted changes that would block worktree creation)

## Configuration

- **Worktree root:** `.claude/worktrees/` (Claude Code default, adjustable per project)
- **Execution state:** `{worktree-root}/execution-state.yaml`
- **Worktree naming:** `{worktree-root}/wt-{story-id}`
- **Branch naming:** `bmad/story-{story-id}`

## Step 1: Verify Clean State

```bash
git status --porcelain
```

If dirty, ask the user to commit or stash before proceeding. Worktrees share the same Git repository, so uncommitted changes in the main tree can cause confusion.

## Step 2: Determine Active Phase

From the Analyze output, identify the current phase to execute. Each phase contains N parallel items.

Example phase structure:
```
Phase 1:
  - Worktree A: /bmad-bmm-create-story → Story 4-2
  - Worktree B: /bmad-bmm-create-story → Story 4-3
  - Worktree C: /bmad-bmm-create-story → Story 4-4
```

## Step 3: Create Git Worktrees

For each parallel item in the phase, create a worktree:

```bash
# Pattern: git worktree add <path> -b <branch-name>
git worktree add .claude/worktrees/wt-{story-id} -b bmad/{story-id}
```

Example:
```bash
git worktree add .claude/worktrees/wt-4-2 -b bmad/story-4-2
git worktree add .claude/worktrees/wt-4-4 -b bmad/story-4-4
```

Record the worktree paths for the merge step.

## Step 4: Create tmux Session

Set up a tmux session with one pane per parallel worktree:

```bash
# Create named session for the epic
EPIC_NUM={active_epic_number}
tmux new-session -d -s "bmad-epic-${EPIC_NUM}" -c ".claude/worktrees/wt-{first-story}"

# Split for additional worktrees
tmux split-window -h -t "bmad-epic-${EPIC_NUM}" -c ".claude/worktrees/wt-{second-story}"
# Add more splits as needed for additional parallel items
```

For 3 parallel items, use:
```bash
tmux new-session -d -s "bmad-epic-${EPIC_NUM}" -c ".claude/worktrees/wt-{first}"
tmux split-window -h -t "bmad-epic-${EPIC_NUM}" -c ".claude/worktrees/wt-{second}"
tmux split-window -v -t "bmad-epic-${EPIC_NUM}" -c ".claude/worktrees/wt-{third}"
tmux select-layout -t "bmad-epic-${EPIC_NUM}" tiled
```

## Step 5: Launch Claude Code in Each Pane

Send the BMAD command to each tmux pane:

```bash
# Pane indexing: 0, 1, 2, ...
# Each pane runs Claude Code with the appropriate BMAD slash command

tmux send-keys -t "bmad-epic-${EPIC_NUM}:0.0" \
  "claude --dangerously-skip-permissions '/{bmad-command} {story-context}'" Enter

tmux send-keys -t "bmad-epic-${EPIC_NUM}:0.1" \
  "claude --dangerously-skip-permissions '/{bmad-command} {story-context}'" Enter
```

**IMPORTANT:** The `--dangerously-skip-permissions` flag is optional. If the user prefers interactive approval, omit it and let each Claude Code instance prompt for permissions.

**Alternative (safer):** Launch Claude Code without auto-permissions:
```bash
tmux send-keys -t "bmad-epic-${EPIC_NUM}:0.0" "claude" Enter
# Then manually send the /bmad command after Claude starts
tmux send-keys -t "bmad-epic-${EPIC_NUM}:0.0" "/{bmad-command}" Enter
```

## Step 6: Monitor Progress

Attach to the tmux session to monitor:

```bash
tmux attach -t "bmad-epic-${EPIC_NUM}"
```

Key tmux navigation:
- `Ctrl-b` then arrow keys to switch panes
- `Ctrl-b` then `z` to zoom a pane (toggle fullscreen)
- `Ctrl-b` then `d` to detach (processes continue in background)

## Step 7: Record Execution State

Create a tracking file in the project:

```bash
cat > {worktree-root}/execution-state.yaml << 'EOF'
phase: {phase_number}
epic: {epic_number}
tmux_session: bmad-epic-{epic_number}
worktrees:
  - path: .claude/worktrees/wt-{id}
    branch: bmad/story-{id}
    command: /bmad-bmm-{command}
    story: "{story_title}"
    status: running
EOF
```

This file is consumed by the **Merge** workflow.

## Step 8: Wait and Verify

Once all panes show completion:

1. Check each worktree for changes:
   ```bash
   cd .claude/worktrees/wt-{id} && git log --oneline main..HEAD
   ```

2. Verify expected artifacts were created (story files, terraform configs, etc.)

3. Update execution-state.yaml status to `completed` for each worktree

4. Hand off to the **Merge** workflow when ready.
