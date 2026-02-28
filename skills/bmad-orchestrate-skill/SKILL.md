---
name: BmadOrchestrate
description: Parallel BMAD workflow orchestration using git worktrees and tmux. USE WHEN BMAD parallel, orchestrate sprint, run stories in parallel, worktree orchestration, sprint acceleration, parallel dev stories, bmad worktree, parallelize BMAD, accelerate epic.
---

# BmadOrchestrate

Accelerates BMAD sprints by analyzing story dependencies, identifying parallelization opportunities, and orchestrating concurrent execution across git worktrees with tmux and Claude Code.

## Customization

**Before executing, check for user customizations at:**
`~/.claude/skills/PAI/USER/SKILLCUSTOMIZATIONS/BmadOrchestrate/`

If this directory exists, load and apply any PREFERENCES.md, configurations, or resources found there. These override default behavior. If the directory does not exist, proceed with skill defaults.

## Voice Notification

**When executing a workflow, do BOTH:**

1. **Send voice notification**:
   ```bash
   curl -s -X POST http://localhost:8888/notify \
     -H "Content-Type: application/json" \
     -d '{"message": "Running WORKFLOWNAME in BmadOrchestrate to ACTION"}' \
     > /dev/null 2>&1 &
   ```

2. **Output text notification**:
   ```
   Running the **WorkflowName** workflow in the **BmadOrchestrate** skill to ACTION...
   ```

**Full documentation:** `~/.claude/skills/PAI/THENOTIFICATIONSYSTEM.md`

## Workflow Routing

| Workflow | Trigger | File |
|----------|---------|------|
| **Analyze** | "analyze for parallelization", "find parallel stories", "dependency graph" | `Workflows/Analyze.md` |
| **Execute** | "execute parallel", "launch worktrees", "run stories in parallel" | `Workflows/Execute.md` |
| **Merge** | "merge worktrees", "combine branches", "merge parallel work" | `Workflows/Merge.md` |

## Examples

**Example 1: Full orchestration from bmad-help output**
```
User: "Parallelize the remaining Epic 4 stories"
→ Invokes Analyze workflow
→ Reads sprint-status.yaml + epics.md
→ Builds dependency graph, identifies 4-2 ‖ 4-4 as independent
→ Presents phase plan with parallel tracks
→ User approves → Invokes Execute workflow
→ Creates worktrees, launches tmux + Claude Code instances
```

**Example 2: Analyze only**
```
User: "Which stories can I run in parallel?"
→ Invokes Analyze workflow
→ Reads sprint status and epic definitions
→ Returns dependency graph + parallelization opportunities
→ Does NOT execute (analysis only)
```

**Example 3: Merge completed worktrees**
```
User: "Merge the parallel story branches back"
→ Invokes Merge workflow
→ Lists worktree branches with changes
→ Merges sequentially, resolving sprint-status.yaml conflicts
→ Cleans up worktrees
```

## Quick Reference

- **Dependency detection:** Reads acceptance criteria for cross-story references
- **Conflict hotspot:** `sprint-status.yaml` — always needs manual merge
- **Worktree location:** `.claude/worktrees/` (Claude Code default)
- **tmux session name:** `bmad-epic-{N}` where N is the active epic number

**Full Documentation:**
- Dependency patterns: `DependencyPatterns.md`
