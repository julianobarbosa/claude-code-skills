# Verify — Post-Setup Verification

Run after vault setup to confirm everything was created correctly. Called by Setup.md Step 6, or run independently to check an existing vault.

## Checks

### 1. Directory Structure

List all expected directories. For each, check existence and report status.

```bash
for dir in inbox daily projects archive [detected-role-folders]; do
  if [ -d "$dir" ]; then
    echo "  [ok] $dir/"
  else
    echo "  [MISSING] $dir/"
  fi
done
```

### 2. CLAUDE.md

Verify CLAUDE.md exists in the vault root. Show first 5 lines as confirmation.

```bash
if [ -f CLAUDE.md ]; then
  echo "  [ok] CLAUDE.md written"
  head -5 CLAUDE.md
else
  echo "  [MISSING] CLAUDE.md not found"
fi
```

### 3. Companion Skill Symlinks

Check if any companion skills were symlinked and whether the symlinks are valid (not broken).

```bash
for skill in daily-skill tldr-skill; do
  link=".claude/skills/$skill"
  if [ -L "$link" ]; then
    if [ -e "$link" ]; then
      echo "  [ok] $skill linked"
    else
      echo "  [BROKEN] $skill symlink exists but target missing"
    fi
  else
    echo "  [--] $skill not linked (optional)"
  fi
done
```

### 4. Global Context

If the user chose global context injection, verify `~/.claude/CLAUDE.md` contains the vault path.

```bash
vault_path="$(pwd)"
if [ -f ~/.claude/CLAUDE.md ]; then
  if grep -q "$vault_path" ~/.claude/CLAUDE.md; then
    echo "  [ok] Global context configured"
  else
    echo "  [--] Global context not configured (vault path not found in ~/.claude/CLAUDE.md)"
  fi
else
  echo "  [--] ~/.claude/CLAUDE.md does not exist"
fi
```

### 5. Obsidian Running

Check if Obsidian is running (informational only — not a failure if it isn't).

```bash
case "$(uname -s)" in
  Darwin)  pgrep -x Obsidian > /dev/null && echo "  [ok] Obsidian running" || echo "  [--] Obsidian not detected (open manually)" ;;
  Linux)   pgrep -f obsidian > /dev/null && echo "  [ok] Obsidian running" || echo "  [--] Obsidian not detected (open manually)" ;;
  MINGW*|MSYS*) tasklist | grep -qi obsidian && echo "  [ok] Obsidian running" || echo "  [--] Obsidian not detected (open manually)" ;;
esac
```

## Output Format

Combine all checks into a single summary block:

```
Verification:
  [ok] 7 folders created
  [ok] CLAUDE.md written (DevOps / Cloud Engineer)
  [ok] daily-skill linked
  [ok] tldr-skill linked
  [ok] Global context configured
  [--] Obsidian not detected (open manually)
```

Status indicators:
- `[ok]` — check passed
- `[MISSING]` — required item not found (setup may have failed)
- `[BROKEN]` — item exists but is invalid (e.g., broken symlink)
- `[--]` — optional item not present (informational, not an error)
