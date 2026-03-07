# BMAD Sprint Orchestration

Extends the core worktree skill with BMAD-specific parallelization analysis, execution, and merge workflows.

## Analyze: Find Parallelization Opportunities

### Step 1: Load Sprint State

```
Read {project-root}/_bmad-output/implementation-artifacts/sprint-status.yaml
```

Identify:
- Which epic is `in-progress`
- Which stories are `backlog` or `ready-for-dev` (candidates)
- Which stories are `done` or `in-progress`

Cross-validate: if a story file exists, compare its `Status:` header to sprint-status.yaml. Story file is source of truth.

### Step 2: Load Epic Definitions

```
Read {project-root}/_bmad-output/planning-artifacts/epics.md
```

For each candidate story, extract:
- Acceptance criteria (look for cross-story references like "Given X from Story N.M")
- Infrastructure domain (Terraform, Kubernetes, Helm, etc.)

### Step 3: Build Dependency Graph

**Independent (parallelizable):**
- Different infrastructure domains
- Create separate files with no overlap
- No cross-references in acceptance criteria
- Don't modify the same Terraform state

**Dependent (sequential):**
- Story B references Story A's outputs
- Both modify the same files
- One extends what the other creates
- Shared Terraform state with `terraform apply`

### Step 4: Design Phase Plan

```
Phase 1 (parallel): [items with no dependencies on each other]
Phase 2 (parallel): [items depending on Phase 1 but not each other]
Final: [Retrospective, sprint status update]
```

### BMAD Workflow Parallelization

| BMAD Step | Parallelizable? | Notes |
|-----------|----------------|-------|
| Create Story (CS) | YES | Spec files are independent |
| Dev Story (DS) | CONDITIONAL | Only if stories are independent |
| Code Review (CR) | YES | Reviews are per-story |
| Retrospective (ER) | NO | Requires all stories done |

## Execute: Launch Parallel Worktrees

Uses the core worktree skill's Create flow for each parallel item:

- **Worktree naming:** `.claude/worktrees/wt-{story-id}`
- **Branch naming:** `bmad/story-{story-id}`
- **tmux window naming:** `{session}-wt-{story-id}`

### Execution State Tracking

Create a tracking file:

```yaml
# .claude/worktrees/execution-state.yaml
phase: 1
epic: 4
worktrees:
  - path: .claude/worktrees/wt-4-2
    branch: bmad/story-4-2
    command: /bmad-create-story
    story: "CI Pipeline Setup"
    status: running
  - path: .claude/worktrees/wt-4-4
    branch: bmad/story-4-4
    command: /bmad-create-story
    story: "Monitoring Stack"
    status: running
```

## Merge: Combine Parallel Branches

### Step 1: Verify All Worktrees Complete

```bash
for wt in .claude/worktrees/wt-*; do
  branch=$(cd "$wt" && git rev-parse --abbrev-ref HEAD)
  commits=$(git log --oneline main.."$branch" | wc -l)
  echo "$branch: $commits commits"
done
```

### Step 2: Merge in Dependency Order

Independent stories first, then dependent ones:

```bash
git checkout main
git merge bmad/story-{id} --no-ff -m "feat: merge story {id} - {title}"
```

### Step 3: Handle Conflicts

**sprint-status.yaml** (always conflicts):
- Accept ALL story status changes (different lines, always safe)
- Keep the latest `generated` date

**Terraform files** (additive modules):
- Accept both module blocks
- Verify no duplicate resource names
- Run `terraform validate`

### Step 4: Cleanup

```bash
# Remove worktrees
for wt in .claude/worktrees/wt-*; do
  git worktree remove "$wt"
done

# Delete branches
git branch -d bmad/story-{id}  # repeat for each

# Remove tracking
rm -f .claude/worktrees/execution-state.yaml

# Kill tmux windows
# (handled by core cleanup workflow)
```

## Dependency Patterns Reference

### Infrastructure Domain Classification

| Domain | Indicators |
|--------|-----------|
| Terraform Networking | VNet, subnets, NSG, NAT Gateway |
| Terraform Compute | VMs, AKS, node pools |
| Terraform Security | Key Vault, managed identities |
| Kubernetes/Helm | Helm charts, K8s manifests |
| Azure DevOps | Pipeline YAML, build definitions |
| Container Images | Dockerfiles, ACR |
| Observability | Grafana, Prometheus |

### Conflict Hotspots

| File | Resolution |
|------|-----------|
| `sprint-status.yaml` | Accept all status changes (different lines) |
| `terraform/main.tf` | Accept both module blocks (additive) |
| `terraform/variables.tf` | Accept both variable blocks (additive) |
| `terraform/providers.tf` | Deduplicate, keep one copy |
| `terraform/backend.tf` | Should NOT differ — flag if it does |

### Terraform State Considerations

Most projects use a single shared state file. This means:
- Steps that DON'T run `terraform apply` (Create Story, Code Review) are always safe to parallelize
- Steps that DO run `terraform apply` must be serialized (state lock contention)
- Stories touching non-Terraform domains (Helm, K8s, pipelines) remain fully parallelizable
