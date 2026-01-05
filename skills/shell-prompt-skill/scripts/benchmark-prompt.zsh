#!/usr/bin/env zsh
# benchmark-prompt.zsh - Shell prompt performance benchmark
# Usage: ./benchmark-prompt.zsh [iterations]

set -e

ITERATIONS=${1:-10}
BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

echo "${BOLD}Shell Prompt Performance Benchmark${NC}"
echo "===================================="
echo ""

# Detect current prompt
detect_prompt() {
  if [[ -n "$POWERLEVEL9K_MODE" ]] || [[ -f ~/.p10k.zsh ]]; then
    echo "powerlevel10k"
  elif command -v starship &>/dev/null && grep -q "starship" ~/.zshrc 2>/dev/null; then
    echo "starship"
  elif [[ -n "$ZSH_THEME" ]]; then
    echo "omz:$ZSH_THEME"
  else
    echo "default"
  fi
}

PROMPT_TYPE=$(detect_prompt)
echo "Detected prompt: ${BOLD}${PROMPT_TYPE}${NC}"
echo "Iterations: ${ITERATIONS}"
echo ""

# Shell startup time
echo "${BOLD}1. Shell Startup Time${NC}"
echo "---------------------"

startup_times=()
for i in $(seq 1 $ITERATIONS); do
  start=$(date +%s%N)
  zsh -i -c exit 2>/dev/null
  end=$(date +%s%N)
  duration=$(( (end - start) / 1000000 ))
  startup_times+=($duration)
  printf "  Run %2d: %d ms\n" $i $duration
done

# Calculate average
total=0
for t in "${startup_times[@]}"; do
  total=$((total + t))
done
avg=$((total / ITERATIONS))

if [[ $avg -lt 100 ]]; then
  color=$GREEN
elif [[ $avg -lt 300 ]]; then
  color=$YELLOW
else
  color=$RED
fi

echo ""
echo "  ${BOLD}Average: ${color}${avg} ms${NC}"
echo ""

# Per-command latency (if zsh-bench available)
if [[ -x ~/zsh-bench/zsh-bench ]]; then
  echo "${BOLD}2. zsh-bench Results${NC}"
  echo "--------------------"
  ~/zsh-bench/zsh-bench 2>/dev/null | grep -E "(first_prompt|command_lag|input_lag)"
  echo ""
fi

# Starship-specific timing
if [[ "$PROMPT_TYPE" == "starship" ]] && command -v starship &>/dev/null; then
  echo "${BOLD}2. Starship Module Timing${NC}"
  echo "-------------------------"
  starship timings 2>/dev/null | head -20
  echo ""
fi

# Git performance (if in a repo)
if git rev-parse --git-dir &>/dev/null; then
  echo "${BOLD}3. Git Status Performance${NC}"
  echo "-------------------------"

  # Native git status
  start=$(date +%s%N)
  git status --porcelain &>/dev/null
  end=$(date +%s%N)
  git_time=$(( (end - start) / 1000000 ))
  echo "  Native git status: ${git_time} ms"

  # File count
  file_count=$(git ls-files | wc -l | tr -d ' ')
  echo "  Tracked files: ${file_count}"

  # Untracked count
  untracked=$(git status --porcelain 2>/dev/null | grep '^??' | wc -l | tr -d ' ')
  echo "  Untracked files: ${untracked}"

  if [[ $git_time -gt 100 ]]; then
    echo ""
    echo "  ${YELLOW}Warning: Git operations are slow in this repo.${NC}"
    echo "  Consider disabling git_status in prompt config."
  fi
  echo ""
fi

# Recommendations
echo "${BOLD}4. Recommendations${NC}"
echo "------------------"

if [[ $avg -gt 300 ]]; then
  echo "  ${RED}! Startup is slow (>300ms)${NC}"
  echo "    - Enable instant prompt (P10k)"
  echo "    - Lazy load plugins"
  echo "    - Cache completions"
fi

if [[ "$PROMPT_TYPE" == "starship" ]]; then
  echo "  - Run 'starship timings' to identify slow modules"
  echo "  - Consider disabling git_status for large repos"
fi

if [[ "$PROMPT_TYPE" == "powerlevel10k" ]]; then
  echo "  - Verify instant prompt is enabled"
  echo "  - Check POWERLEVEL9K_VCS_MAX_INDEX_SIZE_DIRTY setting"
fi

echo ""
echo "${BOLD}Benchmark complete.${NC}"
