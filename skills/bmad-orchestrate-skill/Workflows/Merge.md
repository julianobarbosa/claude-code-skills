# Merge Workflow

Merge parallel worktree branches back into main, resolving conflicts and cleaning up.

## Voice Notification

```bash
curl -s -X POST http://localhost:8888/notify \
  -H "Content-Type: application/json" \
  -d '{"message": "Running Merge in BmadOrchestrate to combine parallel branches"}' \
  > /dev/null 2>&1 &
```

Running the **Merge** workflow in the **BmadOrchestrate** skill to combine parallel branches...

## Step 1: Read Execution State

Load the tracking file created by the Execute workflow (default path: `.claude/worktrees/`):

```bash
cat {worktree-root}/execution-state.yaml
```

Identify all worktrees that need merging and their branches.

If no execution-state.yaml exists, list worktrees manually:
```bash
git worktree list
```

## Step 2: Verify All Worktrees Complete

For each worktree, verify it has commits beyond main:

```bash
for wt in .claude/worktrees/wt-*; do
  branch=$(cd "$wt" && git rev-parse --abbrev-ref HEAD)
  commits=$(git log --oneline main.."$branch" | wc -l)
  echo "$branch: $commits commits"
done
```

If any worktree has 0 commits, it either wasn't started or had no changes. Confirm with the user before proceeding.

## Step 3: Preview Changes Per Branch

For each branch, show what changed:

```bash
git diff --stat main..bmad/story-{id}
```

Pay special attention to:
- **sprint-status.yaml** — multiple branches likely modified this (CONFLICT EXPECTED)
- **terraform/main.tf** — if multiple stories add Terraform modules
- **Any shared configuration files**

## Step 4: Determine Merge Order

Merge in dependency order (independent stories first):

1. Stories with no dependencies on other parallel stories → merge first
2. Stories that depend on already-merged stories → merge next

If all stories were truly independent (no file overlap except sprint-status.yaml), order doesn't matter.

## Step 5: Merge Each Branch

For each branch, in order:

```bash
# Ensure we're on main
git checkout main

# Merge the branch
git merge bmad/story-{id} --no-ff -m "feat: merge story {id} - {title}"
```

### Handling sprint-status.yaml Conflicts

This file WILL conflict if multiple branches updated it. Resolution strategy:

1. Open the conflicted file
2. Accept ALL story status changes (each branch updated different story lines)
3. Keep the latest `generated` date
4. Verify the combined result makes sense

```bash
# After resolving conflicts
git add _bmad-output/implementation-artifacts/sprint-status.yaml
git commit --no-edit
```

### Handling Terraform Conflicts

If multiple branches modified `terraform/main.tf` (adding modules):

1. Accept both module blocks (they're additive)
2. Ensure no duplicate resource names
3. Run `terraform validate` after resolution

### Handling Other Conflicts

For unexpected conflicts:
1. Show the diff to the user
2. Ask which version to keep
3. Never auto-resolve without understanding

## Step 6: Verify Merged State

After all branches are merged:

```bash
# Check the combined sprint status
cat _bmad-output/implementation-artifacts/sprint-status.yaml

# Verify all expected artifacts exist
ls _bmad-output/implementation-artifacts/

# If Terraform was involved
cd terraform && terraform validate
```

## Step 7: Clean Up Worktrees

Remove the worktrees and their branches:

```bash
# Remove each worktree
for wt in .claude/worktrees/wt-*; do
  git worktree remove "$wt"
done

# Delete the tracking branches
git branch -d bmad/story-{id}  # repeat for each

# Remove execution state
rm -f {worktree-root}/execution-state.yaml
```

## Step 8: Kill tmux Session

```bash
tmux kill-session -t "bmad-epic-{N}"
```

## Step 9: Summary

Output a merge summary:

```
## Merge Complete

| Branch | Commits | Files Changed | Conflicts |
|--------|---------|---------------|-----------|
| bmad/story-{id} | {N} | {M} | {resolved/none} |

### Combined Changes
- {total files changed} files modified
- {new artifacts created}
- sprint-status.yaml: {stories updated}

### Next Steps
- Run next phase (if more phases remain)
- Or proceed to: /bmad-bmm-{next-command}
```
