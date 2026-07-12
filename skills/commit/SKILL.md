---
name: commit
description: Stage, commit, and push changes to the current branch. Use when asked to commit, push, or create a commit for the current task.
---

# Commit and Push Skill

1. Stage only files related to the current task
2. Run `git commit --no-verify` if pre-commit hooks fail on unrelated issues
3. Push to the current branch
4. Report the commit hash and branch name

NOTE: This repo uses Azure DevOps. For PRs use `az repos pr create`.
NOTE: The `commit-msg` hook strips `Co-Authored-By` trailers so commits appear as sole-author.

---

## Gotchas

- **`git commit --no-verify` bypasses pre-commit hook** — logged in reflog but easy to forget. A CI check that fails on no-verify trailers prevents drift.
- **`commit-msg` hook transforms the message AFTER the editor closes** — verify the final state with `git show -s --format=%B`, not the editor draft.
- **Azure DevOps strips `Co-Authored-By` server-side** — local commits show co-author; PR display doesn't. Test what shows in the PR UI before assuming attribution worked.
- **`git commit` on a detached HEAD creates an orphan** — `git checkout main` loses it unless you branch first. Reflog recovers but only for 30 days.
- **Trailing whitespace in commit messages**: some hooks normalize, some preserve. Format-checks comparing raw vs normalized fail confusingly.
