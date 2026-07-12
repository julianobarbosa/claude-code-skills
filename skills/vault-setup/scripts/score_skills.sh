#!/usr/bin/env bash
# Skill Quality Scorer — outputs a single integer score (0-100)
# Evaluates vault-setup-skill, daily-skill, tldr-skill across 5 dimensions.
# DO NOT MODIFY after initial creation — only skill files may change.

set -uo pipefail

SCRIPTS_DIR="$(cd "$(dirname "$0")" && pwd)"
VAULT_SETUP="$(cd "$SCRIPTS_DIR/.." && pwd)"
SKILLS_ROOT="$(cd "$VAULT_SETUP/.." && pwd)"

DAILY="$SKILLS_ROOT/daily-skill"
TLDR="$SKILLS_ROOT/tldr-skill"

SCORE=0
DETAILS=""

add() {
  local pts=$1 max=$2 desc=$3
  SCORE=$((SCORE + pts))
  DETAILS="${DETAILS}\n  [${pts}/${max}] ${desc}"
}

# ═══════════════════════════════════════════
# COMPLETENESS (30 pts)
# ═══════════════════════════════════════════

# Each skill SKILL.md has YAML frontmatter with name + description (3 x 2pts = 6)
for skill_dir in "$VAULT_SETUP" "$DAILY" "$TLDR"; do
  skill_file="$skill_dir/SKILL.md"
  if [ -f "$skill_file" ]; then
    if head -5 "$skill_file" | grep -q "^name:"; then
      if head -10 "$skill_file" | grep -q "^description:"; then
        add 2 2 "$(basename "$skill_dir")/SKILL.md has name+description frontmatter"
      else
        add 1 2 "$(basename "$skill_dir")/SKILL.md has name but missing description"
      fi
    else
      add 0 2 "$(basename "$skill_dir")/SKILL.md missing frontmatter"
    fi
  else
    add 0 2 "$(basename "$skill_dir")/SKILL.md not found"
  fi
done

# Each skill has a Troubleshooting/Error section (3 x 3pts = 9)
for skill_dir in "$VAULT_SETUP" "$DAILY" "$TLDR"; do
  skill_file="$skill_dir/SKILL.md"
  if [ -f "$skill_file" ] && grep -qi "troubleshoot\|error handling\|edge.case\|what.if" "$skill_file"; then
    add 3 3 "$(basename "$skill_dir") has troubleshooting/error section"
  else
    add 0 3 "$(basename "$skill_dir") MISSING troubleshooting/error section"
  fi
done

# vault-setup SKILL.md has examples section (2pts)
if grep -q "## Examples" "$VAULT_SETUP/SKILL.md" 2>/dev/null; then
  add 2 2 "vault-setup-skill has Examples section"
else
  add 0 2 "vault-setup-skill MISSING Examples section"
fi

# Each workflow file has at least one code example (3 x 2pts = 6)
for wf in "$VAULT_SETUP/Workflows/Setup.md" "$VAULT_SETUP/Workflows/Verify.md" "$VAULT_SETUP/Workflows/ImportFiles.md"; do
  if [ -f "$wf" ] && grep -q '```' "$wf"; then
    add 2 2 "$(basename "$wf") has code examples"
  else
    add 0 2 "$(basename "$wf") MISSING code examples"
  fi
done

# daily-skill references/templates.md path is explicit (2pts)
if [ -f "$DAILY/SKILL.md" ] && grep -qi "references/templates\.md" "$DAILY/SKILL.md"; then
  # Check if the path is explicit (relative to skill root or absolute)
  if grep -qi "skill.root\|skill.dir\|relative to\|located at\|skill folder" "$DAILY/SKILL.md"; then
    add 2 2 "daily-skill has explicit template path reference"
  else
    add 1 2 "daily-skill mentions templates.md but path not explicit"
  fi
else
  add 0 2 "daily-skill MISSING template path reference"
fi

# VaultBuilder.help.md covers all 3 commands (3pts)
help_file="$VAULT_SETUP/Tools/VaultBuilder.help.md"
if [ -f "$help_file" ]; then
  cmds_found=0
  grep -qi "create" "$help_file" && cmds_found=$((cmds_found + 1))
  grep -qi "verify" "$help_file" && cmds_found=$((cmds_found + 1))
  grep -qi "inject.global" "$help_file" && cmds_found=$((cmds_found + 1))
  add $cmds_found 3 "VaultBuilder.help.md covers $cmds_found/3 commands"
else
  add 0 3 "VaultBuilder.help.md not found"
fi

# ═══════════════════════════════════════════
# CORRECTNESS (25 pts)
# ═══════════════════════════════════════════

# No hardcoded user-specific vault paths in shared skills (5pts, deduct per occurrence)
hardcoded_count=0
for skill_dir in "$VAULT_SETUP" "$DAILY" "$TLDR"; do
  if [ -d "$skill_dir" ]; then
    count=$(grep -r "\.obsidian/vaults/\.obsidian-barbosa" "$skill_dir" --include="*.md" --include="*.py" 2>/dev/null | wc -l | tr -d ' ')
    hardcoded_count=$((hardcoded_count + count))
  fi
done
if [ "$hardcoded_count" -eq 0 ]; then
  add 5 5 "No hardcoded user-specific vault paths"
elif [ "$hardcoded_count" -le 2 ]; then
  add 2 5 "$hardcoded_count hardcoded vault path(s) found"
else
  add 0 5 "$hardcoded_count hardcoded vault paths found"
fi

# VaultBuilder.py: open_obsidian parameter does not shadow function (5pts)
vb="$VAULT_SETUP/Tools/VaultBuilder.py"
if [ -f "$vb" ]; then
  # Check if the create function's parameter name matches the function name
  if grep -q "def create.*open_obsidian)" "$vb" && grep -q "def open_obsidian" "$vb"; then
    add 0 5 "VaultBuilder.py: open_obsidian parameter SHADOWS the function"
  else
    add 5 5 "VaultBuilder.py: no parameter/function name shadowing"
  fi
else
  add 0 5 "VaultBuilder.py not found"
fi

# Python files pass syntax check (5pts)
py_syntax_ok=0
py_total=0
for pyfile in "$VAULT_SETUP/Tools/VaultBuilder.py" "$VAULT_SETUP/scripts/process_docs_to_obsidian.py"; do
  if [ -f "$pyfile" ]; then
    py_total=$((py_total + 1))
    if python3 -c "compile(open('$pyfile').read(), '$pyfile', 'exec')" 2>/dev/null; then
      py_syntax_ok=$((py_syntax_ok + 1))
    fi
  fi
done
if [ "$py_total" -gt 0 ]; then
  pts=$(( (py_syntax_ok * 5) / py_total ))
  add $pts 5 "Python syntax: $py_syntax_ok/$py_total files pass"
else
  add 0 5 "No Python files found"
fi

# SKILL.md name field matches directory name (3 x ~2pts ≈ 5pts, round to 5)
name_match=0
for skill_dir in "$VAULT_SETUP" "$DAILY" "$TLDR"; do
  skill_file="$skill_dir/SKILL.md"
  if [ -f "$skill_file" ]; then
    dir_name=$(basename "$skill_dir" | sed 's/-skill$//')
    skill_name=$(grep "^name:" "$skill_file" 2>/dev/null | head -1 | sed 's/^name:[[:space:]]*//')
    if [ -n "$skill_name" ]; then
      # Check if name field roughly matches directory
      if echo "$dir_name" | grep -qi "$skill_name" || echo "$skill_name" | grep -qi "$dir_name"; then
        name_match=$((name_match + 1))
      fi
    fi
  fi
done
case $name_match in
  3) add 5 5 "All skill names match directory names" ;;
  2) add 3 5 "$name_match/3 skill names match directory names" ;;
  1) add 2 5 "$name_match/3 skill names match directory names" ;;
  *) add 0 5 "No skill names match directory names" ;;
esac

# ═══════════════════════════════════════════
# ERROR RECOVERY (20 pts)
# ═══════════════════════════════════════════

# Each skill has error/edge-case handling section (3 x 4pts = 12)
for skill_dir in "$VAULT_SETUP" "$DAILY" "$TLDR"; do
  found=0
  # Check all markdown files in the skill
  while IFS= read -r -d '' mdfile; do
    if grep -qi "error\|edge.case\|what.if.*fail\|troubleshoot\|fallback\|graceful" "$mdfile" 2>/dev/null; then
      found=1
      break
    fi
  done < <(find "$skill_dir" -name "*.md" -print0 2>/dev/null)
  if [ "$found" -eq 1 ]; then
    add 4 4 "$(basename "$skill_dir") has error/edge-case content"
  else
    add 0 4 "$(basename "$skill_dir") MISSING error/edge-case content"
  fi
done

# VaultBuilder.py has meaningful error messages (4pts)
if [ -f "$vb" ]; then
  err_count=$(grep -c "print.*Error\|click.echo.*error\|sys.exit\|raise\|except" "$vb" 2>/dev/null || echo 0)
  if [ "$err_count" -ge 4 ]; then
    add 4 4 "VaultBuilder.py has $err_count error handling points"
  elif [ "$err_count" -ge 2 ]; then
    add 2 4 "VaultBuilder.py has $err_count error handling points (needs more)"
  else
    add 0 4 "VaultBuilder.py has insufficient error handling"
  fi
else
  add 0 4 "VaultBuilder.py not found"
fi

# process_docs_to_obsidian.py warns on encoding issues (4pts)
pdoc="$VAULT_SETUP/scripts/process_docs_to_obsidian.py"
if [ -f "$pdoc" ]; then
  if grep -q 'errors="replace"' "$pdoc" && ! grep -qi "warn\|log.*encod\|print.*encod" "$pdoc"; then
    add 0 4 "process_docs silently replaces encoding errors (no warning)"
  elif grep -qi "warn\|log.*encod\|print.*encod" "$pdoc"; then
    add 4 4 "process_docs warns on encoding issues"
  else
    add 2 4 "process_docs has basic encoding handling"
  fi
else
  add 0 4 "process_docs_to_obsidian.py not found"
fi

# ═══════════════════════════════════════════
# PORTABILITY (15 pts)
# ═══════════════════════════════════════════

# No absolute paths containing /Users/ in markdown docs (5pts)
users_count=0
for skill_dir in "$VAULT_SETUP" "$DAILY" "$TLDR"; do
  count=$(grep -r "/Users/" "$skill_dir" --include="*.md" 2>/dev/null | wc -l | tr -d ' ')
  users_count=$((users_count + count))
done
if [ "$users_count" -eq 0 ]; then
  add 5 5 "No /Users/ absolute paths in markdown"
elif [ "$users_count" -le 2 ]; then
  add 2 5 "$users_count /Users/ paths found in markdown"
else
  add 0 5 "$users_count /Users/ paths in markdown"
fi

# Vault path is configurable (5pts)
# Check if tldr-skill uses a convention rather than hardcoded path
if [ -f "$TLDR/SKILL.md" ]; then
  if grep -qi "CLAUDE.md\|env.var\|configurable\|vault.root.*determined\|current.working" "$TLDR/SKILL.md" && \
     ! grep -q "\.obsidian/vaults/\.obsidian-barbosa" "$TLDR/SKILL.md"; then
    add 5 5 "tldr-skill vault path is configurable"
  elif grep -q "\.obsidian/vaults/\.obsidian-barbosa" "$TLDR/SKILL.md"; then
    add 0 5 "tldr-skill has hardcoded vault path"
  else
    add 3 5 "tldr-skill vault path partially configurable"
  fi
else
  add 0 5 "tldr-skill SKILL.md not found"
fi

# Cross-platform notes present (5pts)
platform_notes=0
for skill_dir in "$VAULT_SETUP" "$DAILY" "$TLDR"; do
  if grep -rqi "cross.platform\|darwin\|linux\|windows\|macos\|platform" "$skill_dir" --include="*.md" --include="*.py" 2>/dev/null; then
    platform_notes=$((platform_notes + 1))
  fi
done
case $platform_notes in
  3) add 5 5 "All skills have cross-platform awareness" ;;
  2) add 3 5 "$platform_notes/3 skills have cross-platform content" ;;
  1) add 2 5 "$platform_notes/3 skills have cross-platform content" ;;
  *) add 0 5 "No cross-platform content found" ;;
esac

# ═══════════════════════════════════════════
# TESTING (10 pts)
# ═══════════════════════════════════════════

# test_vaultbuilder.py exists with at least 3 test functions (5pts)
test_vb="$VAULT_SETUP/scripts/test_vaultbuilder.py"
if [ -f "$test_vb" ]; then
  test_count=$(grep -c "def test_" "$test_vb" 2>/dev/null || echo 0)
  if [ "$test_count" -ge 3 ]; then
    add 5 5 "test_vaultbuilder.py has $test_count tests"
  elif [ "$test_count" -ge 1 ]; then
    add 3 5 "test_vaultbuilder.py has $test_count tests (need 3+)"
  else
    add 1 5 "test_vaultbuilder.py exists but no test functions"
  fi
else
  add 0 5 "test_vaultbuilder.py NOT FOUND"
fi

# test_process_docs.py exists with at least 2 test functions (5pts)
test_pd="$VAULT_SETUP/scripts/test_process_docs.py"
if [ -f "$test_pd" ]; then
  test_count=$(grep -c "def test_" "$test_pd" 2>/dev/null || echo 0)
  if [ "$test_count" -ge 2 ]; then
    add 5 5 "test_process_docs.py has $test_count tests"
  elif [ "$test_count" -ge 1 ]; then
    add 3 5 "test_process_docs.py has $test_count tests (need 2+)"
  else
    add 1 5 "test_process_docs.py exists but no test functions"
  fi
else
  add 0 5 "test_process_docs.py NOT FOUND"
fi

# ═══════════════════════════════════════════
# REPORT
# ═══════════════════════════════════════════

echo "═══ Obsidian Skill Quality Score ═══"
echo -e "$DETAILS"
echo ""
echo "TOTAL: $SCORE / 100"
echo "$SCORE"
