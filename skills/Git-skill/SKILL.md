---
name: Git
description: Complete Git version control workflow automation. USE WHEN user mentions commit, push, pull request, PR, branch, merge, rebase, stash, git status, staged files, unstaged changes, OR any version control operations. Handles conventional commits, security checks, and GitHub CLI integration.
---

# Git

Complete Git version control workflow automation for Claude Code. This skill provides safe, structured workflows for all common git operations with built-in security checks, conventional commit support, and GitHub CLI integration.

## Workflow Routing

**When executing a workflow, output this notification:**

```
Running the **WorkflowName** workflow from the **Git** skill...
```

| Workflow | Trigger | File |
|----------|---------|------|
| **Commit** | "commit", "stage changes", "cm" | `workflows/Commit.md` |
| **CommitPush** | "commit and push", "push changes", "cp" | `workflows/CommitPush.md` |
| **PullRequest** | "create pr", "pull request", "open pr" | `workflows/PullRequest.md` |
| **Branch** | "create branch", "switch branch", "list branches" | `workflows/Branch.md` |
| **Merge** | "merge branch", "merge into" | `workflows/Merge.md` |
| **Rebase** | "rebase", "rebase onto" | `workflows/Rebase.md` |
| **Stash** | "stash changes", "save work", "pop stash" | `workflows/Stash.md` |
| **Status** | "git status", "what changed", "show changes" | `workflows/Status.md` |
| **Sync** | "sync branch", "pull latest", "update branch" | `workflows/Sync.md` |
| **Undo** | "undo commit", "reset", "revert" | `workflows/Undo.md` |
| **Log** | "git log", "commit history", "show commits" | `workflows/Log.md` |
| **Diff** | "show diff", "what changed", "compare" | `workflows/Diff.md` |
| **Worktree** | "worktree", "add worktree", "list worktrees", "remove worktree" | `workflows/Worktree.md` |

## Examples

**Example 1: Stage and commit changes locally**
```
User: "Commit these changes"
→ Invokes Commit workflow
→ Reviews all modified files for sensitive data
→ Generates conventional commit message
→ Stages and commits changes (NO push)
→ Returns commit hash and summary
```

**Example 2: Full commit and push workflow**
```
User: "Push my changes"
→ Invokes CommitPush workflow
→ Security scan for credentials/secrets
→ Generates descriptive commit message
→ Commits and pushes to remote
→ Confirms successful push with branch info
```

**Example 3: Create a pull request**
```
User: "Create a PR to main"
→ Invokes PullRequest workflow
→ Summarizes all commits in branch
→ Generates PR title and description
→ Uses GitHub CLI to create PR
→ Returns PR URL and details
```

**Example 4: Check repository status**
```
User: "What's the git status?"
→ Invokes Status workflow
→ Shows staged/unstaged/untracked files
→ Displays current branch info
→ Shows ahead/behind remote status
```

**Example 5: Create worktree for parallel development**
```
User: "Create a worktree for the hotfix"
→ Invokes Worktree workflow
→ Creates new worktree directory
→ Checks out branch in isolated directory
→ Returns worktree path and branch info
→ Preserves current work context
```

## Security Protocols

**CRITICAL: The following are NEVER committed:**

| Pattern | Example | Action |
|---------|---------|--------|
| Environment files | `.env`, `.env.local`, `.env.production` | Block commit |
| Credentials | `credentials.json`, `*.pem`, `*.key` | Block commit |
| API keys | Hardcoded keys in source | Warn and block |
| Database URLs | Connection strings with passwords | Block commit |
| Cloud configs | `*.tfvars`, `kubeconfig` | Warn user |

## Conventional Commits Reference

All commits follow [Conventional Commits](https://www.conventionalcommits.org/):

| Type | When to Use |
|------|-------------|
| `feat` | New feature or capability |
| `fix` | Bug fix |
| `docs` | Documentation only changes |
| `style` | Formatting, no code change |
| `refactor` | Code restructuring, no behavior change |
| `perf` | Performance improvement |
| `test` | Adding or fixing tests |
| `build` | Build system or dependencies |
| `ci` | CI/CD configuration |
| `chore` | Maintenance tasks |
| `revert` | Reverting previous commits |

**Commit Message Format:**
```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

**Rules:**
- Title under 70 characters
- Use imperative mood ("add" not "added")
- No period at end of title
- Body explains what and why, not how

## Git Safety Rules

1. **NEVER force push to main/master** without explicit user confirmation
2. **NEVER run destructive commands** (`git reset --hard`, `git clean -fd`) without confirmation
3. **ALWAYS check for uncommitted changes** before switching branches
4. **ALWAYS verify remote** before pushing sensitive repos
5. **NEVER skip pre-commit hooks** unless explicitly requested
6. **NEVER amend pushed commits** without confirmation

## AI Attribution Policy

**DO NOT include AI attribution in commits:**
- No "Generated with [Claude Code]" signatures
- No "Co-Authored-By: Claude" attributions
- No AI tool references in commit messages
- Create clean, professional commit messages

## Tools

This skill uses standard git commands and optionally:
- **GitHub CLI (`gh`)**: For PR creation and GitHub operations
- **pre-commit**: For validation hooks before commits

## References

- `references/ConventionalCommits.md` - Detailed conventional commits guide
- `references/GitBestPractices.md` - Git workflow best practices
- `references/GitWorktree.md` - Git worktree concepts and command reference
- `references/SecurityChecklist.md` - Pre-commit security checklist
