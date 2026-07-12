---
name: merge
description: Merge the current feature branch into main and (optionally) clean up the branch and worktree. Prefers fast-forward (--ff-only) for linear history; falls back to a merge commit (--no-ff) when the branch has diverged or the user wants the merge commit preserved. Interactive cleanup at the end. USE WHEN asked to "merge to main", "merge and cleanup", "integrate the feature branch", or "finish this branch" — i.e. a direct local merge with no review gate. For PR-based delivery (push → open a PR → link a work item → clean up after merge), use the `ship` skill instead.
---

# Merge

Combine `merge-and-cleanup` and `merge-to-main` into one flow. Default to fast-forward; preserve a merge commit when fast-forward isn't possible or the user asks for one. Always interactive about deleting branches and worktrees.

## Flow

1. **Refuse if already on main.** If `git rev-parse --abbrev-ref HEAD` returns `main` (or `master`), stop and report — there's nothing to merge.
2. **Working tree must be clean.** If there are uncommitted changes, ask the user whether to commit, stash, or abort. Do not silently stash.
3. **Capture the feature branch name** — `FEATURE=$(git rev-parse --abbrev-ref HEAD)`.
4. **Sync main.**
   - `git checkout main`
   - `git pull --ff-only origin main`
5. **Try fast-forward merge first.**
   - `git merge --ff-only "$FEATURE"`
   - If it succeeds, history is linear — done with the merge step.
   - If it fails (branch diverged), proceed to step 6.
6. **Fall back to merge commit** — `git merge --no-ff "$FEATURE"`.
   - If there are conflicts, stop and report. Do not auto-resolve.
   - Write a meaningful merge-commit message; do not accept the default if it's just "Merge branch …".
7. **Push** — `git push origin main`.
8. **Interactive cleanup.** Ask the user: "Delete `$FEATURE` (local + remote) and any associated worktree?"
   - On **yes**:
     - If a worktree exists for `$FEATURE` (`git worktree list | grep -F "$FEATURE"`), **`cd` to the main repo dir first**, then `git worktree remove <path>`.
     - `git branch -d "$FEATURE"` (use `-D` only if user explicitly confirms — `-d` refuses if branch isn't merged, which is the safety we want).
     - `git push origin --delete "$FEATURE"` (ignore failure if branch was never pushed).
   - On **no**: leave everything in place.
9. **Report final status** — commit hash on main, whether branch was deleted, whether a worktree was removed.

## Notes

- **Prefer ff-only.** Linear history is easier to reason about. Only fall back to a merge commit when the branch genuinely diverged.
- **Never `--no-verify`.** If a pre-push hook fails, fix the underlying issue; don't bypass.
- **Worktree-first cleanup.** If the feature branch was developed in a worktree, you cannot delete the branch from inside the worktree. Always `cd` to the main repo working directory first.
- **Conflict policy.** This skill does not auto-resolve conflicts. If `git merge` reports a conflict, stop and surface it to the user — they decide.

## Gotchas

- `git pull --ff-only` on main fails if main has diverged locally (e.g., you committed directly to main). That's a different problem — surface it; don't paper over with `--rebase`.
- `git branch -d` refuses on unmerged branches. That refusal is your safety net — never automatically promote to `-D`.
- `git push origin --delete` exits non-zero if the remote branch doesn't exist. That's fine in this flow (branch was local-only) — log and continue.
- macOS case-insensitive filesystems can mask case-only conflicts; if the feature branch differs only in case from another branch, `git checkout` will surprise you.
