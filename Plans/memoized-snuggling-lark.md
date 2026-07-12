# Plan: Remove Co-Author Trailer from Commit Skill

## Context

Claude Code automatically appends a `Co-Authored-By: Claude <noreply@anthropic.com>` trailer to every git commit message. The user wants the commit-skill to strip this trailer so commits appear as sole-author.

The repo already has a `commit-msg` hook at `.git/hooks/commit-msg` that adds `Signed-off-by` trailers — we can use the same hook to also strip the co-author line.

## Approach

**Option A (recommended): Extend the existing `commit-msg` hook** to remove `Co-Authored-By` lines before the commit finalizes.

Add one line to `.git/hooks/commit-msg`:
```bash
sed -i '' '/^Co-[Aa]uthored-[Bb]y:/d' "$1"
```

This runs *inside* the git commit process, so the trailer never lands in the final commit message.

**Option B: Update SKILL.md instructions** to tell Claude to amend the commit after creating it. This is less clean since it creates two commits in reflog.

## File Changes

1. **`.git/hooks/commit-msg`** — Add the `sed` line to strip `Co-Authored-By` trailers
2. **`skills/commit-skill/SKILL.md`** — Add a note documenting that the hook strips co-author trailers

## Verification

- Make a test commit → run `git log -1 --format='%B'` → confirm no `Co-Authored-By` line
- Confirm `Signed-off-by` trailer is still present (existing hook behavior preserved)
