# Merge Feature Branch to Main
1. Verify current branch is NOT main
2. Stash any uncommitted changes
3. git checkout main && git pull
4. git merge <feature-branch> --no-ff
5. git push origin main
6. Ask user if they want to delete the feature branch and worktree
7. If yes, cd to main repo dir FIRST, then remove worktree and delete branch
