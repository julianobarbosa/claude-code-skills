# .claude/skills/merge-and-cleanup/SKILL.md

## Merge Feature Branch to Main

1. Ensure all changes are committed on current branch
2. Switch to main: `git checkout main && git pull`
3. Merge feature branch: `git merge --ff-only <branch>` (if fails, use regular merge and resolve conflicts)
4. Push main: `git push origin main`
5. Delete feature branch: `git branch -d <branch> && git push origin --delete <branch>`
6. Report final status
