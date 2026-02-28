# Analyze Workflow

Analyze BMAD sprint status for parallelization opportunities by building a story dependency graph.

## Voice Notification

```bash
curl -s -X POST http://localhost:8888/notify \
  -H "Content-Type: application/json" \
  -d '{"message": "Running Analyze in BmadOrchestrate to find parallelization opportunities"}' \
  > /dev/null 2>&1 &
```

Running the **Analyze** workflow in the **BmadOrchestrate** skill to find parallelization opportunities...

## Step 1: Load Sprint State

Read the sprint status file to understand current progress:

```
Read {project-root}/_bmad-output/implementation-artifacts/sprint-status.yaml
```

Identify:
- Which epic is `in-progress`
- Which stories are `backlog` or `ready-for-dev` (candidates for work)
- Which stories are already `done` or `in-progress`

## Step 1a: Cross-Validate Status

For each story NOT in `backlog` status:

1. If a story file exists at `{project-root}/_bmad-output/implementation-artifacts/{story-slug}.md`, compare its `Status:` header to the status in `sprint-status.yaml`
2. If **mismatch detected** → WARN the user: _"Story N.M shows '{sprint-status}' in sprint-status.yaml but '{story-file-status}' in the story file."_
3. Use the **story file as source of truth** (it's updated during Dev Story execution)
4. Recommend updating `sprint-status.yaml` before proceeding to avoid incorrect parallelization decisions (e.g., re-running a story that's already done)

## Step 2: Load Epic Definitions

Read the epics document for the active epic:

```
Read {project-root}/_bmad-output/planning-artifacts/epics.md
```

For each candidate story, extract:
- **Story title and description**
- **Acceptance criteria** (look for cross-story references like "Given X from Story N.M")
- **Infrastructure domain** (what system does this story touch: Terraform, Kubernetes, Helm, Azure DevOps, etc.)

## Step 2a: Resolve Story Detail Source

For each candidate story identified in Steps 1–2:

1. Check if a story file exists at `{project-root}/_bmad-output/implementation-artifacts/{story-slug}.md`
2. If **EXISTS** → read it for detailed acceptance criteria, tasks, dev notes, and infrastructure domain
3. If **NOT EXISTS** (typical for `backlog` stories) → extract acceptance criteria from `epics.md` by searching for the `### Story N.M:` heading under the active epic
4. **Flag reduced precision** when analyzing from `epics.md` only — epic-level AC may be less granular than a fully elaborated story file

This distinction matters because backlog stories haven't been through Create Story yet and only exist as narrative descriptions in the epics document.

## Step 3: Build Dependency Graph

For each pair of candidate stories (using detail resolved in Step 2a), determine if they are:

### Independent (can parallelize) when:
- They operate on **different infrastructure planes** (e.g., Azure DevOps pipelines vs. Kubernetes/Helm)
- They create **separate files** that don't overlap (different Terraform modules, different directories)
- Their acceptance criteria have **no cross-references** to each other's outputs
- They don't modify the **same Terraform state file**

### Dependent (must be sequential) when:
- Story B's acceptance criteria explicitly reference Story A's outputs ("Given pipeline from 4-2...")
- They modify the **same files** (e.g., both edit `terraform/main.tf`)
- Story B extends or modifies infrastructure that Story A creates
- They share a **Terraform state file** and would cause state lock contention

### Reference: Common Dependency Patterns

Load `~/.claude/skills/BmadOrchestrate/DependencyPatterns.md` for detailed patterns.

## Step 4: Identify BMAD Workflow Parallelization

Beyond story dependencies, analyze which BMAD workflow steps can overlap:

| BMAD Step | Parallelizable? | Notes |
|-----------|----------------|-------|
| Create Story (CS) | YES — spec files are independent | Each creates its own `.md` file |
| Dev Story (DS) | CONDITIONAL — only if stories are independent | Depends on Step 3 analysis |
| Code Review (CR) | YES — reviews are per-story | Can review any completed story |
| Retrospective (ER) | NO — requires all stories done | End of epic only |

## Step 5: Design Phase Plan

Organize work into phases where each phase's items can run in parallel:

```
Phase 1 (parallel): [items that have no dependencies on each other]
Phase 2 (parallel): [items that depend on Phase 1 but not on each other]
Phase 3 (sequential): [items that depend on Phase 2 outputs]
...
Final: [Retrospective, sprint status update]
```

For each phase, specify:
- **What runs in parallel** (with worktree names)
- **Which BMAD command** each worktree should execute
- **Conflict hotspots** (files that multiple worktrees might touch)

## Step 6: Calculate Speedup

Compare:
- **Serial time:** Total number of sequential context windows needed
- **Parallel time:** Number of phase rounds needed
- **Speedup factor:** Serial / Parallel

## Step 7: Present Analysis

Output the analysis in this format:

```
## Dependency Graph

[ASCII or description of story dependencies]

## Parallelization Plan

### Phase N: [Description] — [N worktrees in parallel]

| Worktree | BMAD Command | Story | Domain |
|----------|-------------|-------|--------|
| wt-{name} | /bmad-bmm-{cmd} | {story} | {domain} |

### Conflict Hotspots
- {file}: touched by {worktrees} — merge strategy: {strategy}

## Speedup
- Serial: {N} context windows
- Parallel: {M} phase rounds
- Speedup: ~{N/M}x
```

## Step 8: Ask for Approval

Present the plan and ask: "Ready to execute this parallel plan? I'll set up worktrees and tmux."

If approved, hand off to the **Execute** workflow.
