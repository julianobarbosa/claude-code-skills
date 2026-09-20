#!/usr/bin/env bash
# Run AFTER merging PR #5. Removes skills/ship-workspace from all history.
# IRREVERSIBLE: rewrites every SHA from 78c6256 (2026-09-12) onward.
set -euo pipefail
FR=/tmp/claude-1000/-home-barbosa-Repos-github-claude-code-skills--claude-worktrees-check-sensitive-data/efa0d524-6106-43da-8f7f-141a03128557/scratchpad/bin/git-filter-repo
WORK=$(mktemp -d)

git clone https://github.com/julianobarbosa/claude-code-skills.git "$WORK/repo"
cd "$WORK/repo"

# prove the target is present before rewriting
git log --oneline --all -- skills/ship-workspace | tee /dev/stderr | grep -q . \
  || { echo "nothing to purge — already clean"; exit 0; }

# OPTIONAL: also rewrite the author/committer email on all 32 commits that carry
# julianomb@gmail.com, plus the Signed-off-by trailers that repeat it in message
# bodies. Do this in the SAME pass — a second rewrite means a second force-push.
# Enable with:  REWRITE_EMAIL=1 bash history-purge-runbook.sh
MAILMAP_ARG=()
if [[ "${REWRITE_EMAIL:-0}" == "1" ]]; then
  cat > "$WORK/mailmap" <<'MM'
Juliano Barbosa <julianobarbosa@users.noreply.github.com> <julianomb@gmail.com>
MM
  MAILMAP_ARG=(--mailmap "$WORK/mailmap"
               --replace-message <(echo 'julianomb@gmail.com==>julianobarbosa@users.noreply.github.com'))
fi

python3 "$FR" --force --path skills/ship-workspace --invert-paths "${MAILMAP_ARG[@]}"

# falsifier: zero hits anywhere in the rewritten history
if git log --all --oneline -- skills/ship-workspace | grep -q .; then
  echo "REFUSING: path still present after rewrite"; exit 1
fi
echo "OK: skills/ship-workspace absent from all $(git rev-list --count --all) commits"

if [[ "${REWRITE_EMAIL:-0}" == "1" ]]; then
  if git log --all --format='%ae%n%b' | grep -q 'julianomb@gmail.com'; then
    echo "REFUSING: gmail address still present after mailmap rewrite"; exit 1
  fi
  echo "OK: julianomb@gmail.com absent from all author fields and message bodies"
fi

git remote add origin https://github.com/julianobarbosa/claude-code-skills.git
git push --force origin main

echo "Now: re-clone your local copy, and file the GitHub Support request."
echo "Rewritten clone: $WORK/repo"
