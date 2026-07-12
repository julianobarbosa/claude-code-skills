#!/bin/bash
#
# link-skills.sh — Interactive TUI for selectively symlinking skills
# from claude-code-skills repo to ~/.claude/skills/
#

set -euo pipefail

# ── Paths ──────────────────────────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILLS_SRC="$(cd "$SCRIPT_DIR/../skills" && pwd)" || {
    echo "Error: Cannot resolve skills directory"; exit 1
}
SKILLS_DST="$HOME/.claude/skills"

# ── Color support ──────────────────────────────────────────────────────
if [ -t 1 ] && command -v tput >/dev/null 2>&1 && [ "$(tput colors 2>/dev/null || echo 0)" -ge 8 ]; then
    BOLD=$(tput bold)
    DIM=$(tput dim)
    RESET=$(tput sgr0)
    RED=$(tput setaf 1)
    GREEN=$(tput setaf 2)
    YELLOW=$(tput setaf 3)
    BLUE=$(tput setaf 4)
    CYAN=$(tput setaf 6)
    WHITE=$(tput setaf 7)
else
    BOLD="" DIM="" RESET="" RED="" GREEN="" YELLOW="" BLUE="" CYAN="" WHITE=""
fi

# ── Discover skills ───────────────────────────────────────────────────
declare -a SKILLS=()
declare -a SELECTED=()

load_skills() {
    SKILLS=()
    SELECTED=()
    for d in "$SKILLS_SRC"/*/; do
        [ -d "$d" ] || continue
        SKILLS+=("$(basename "$d")")
        SELECTED+=(0)
    done
}

# ── Status helpers ────────────────────────────────────────────────────
# Returns: linked | conflict | none
skill_status() {
    local name="$1"
    local target="$SKILLS_DST/$name"
    if [ -L "$target" ]; then
        local real
        real="$(readlink "$target" 2>/dev/null || true)"
        if [ "$real" = "$SKILLS_SRC/$name" ]; then
            echo "linked"
        else
            echo "linked"  # symlink but different source — still a symlink
        fi
    elif [ -d "$target" ]; then
        echo "conflict"
    else
        echo "none"
    fi
}

status_indicator() {
    local st="$1"
    case "$st" in
        linked)   printf "%s[✓]%s" "$GREEN" "$RESET" ;;
        conflict) printf "%s[!]%s" "$RED" "$RESET" ;;
        none)     printf "[ ]" ;;
    esac
}

# ── Display ───────────────────────────────────────────────────────────
COLS=2
PAGE_SIZE=40  # skills per page (rows * cols)

print_header() {
    clear
    printf "\n  %s╔══════════════════════════════════════════════════════════════╗%s\n" "$BLUE" "$RESET"
    printf "  %s║%s  %s⚡ Skill Linker%s — interactive skill symlink manager        %s║%s\n" "$BLUE" "$RESET" "$BOLD$CYAN" "$RESET" "$BLUE" "$RESET"
    printf "  %s╚══════════════════════════════════════════════════════════════╝%s\n\n" "$BLUE" "$RESET"
    printf "  %sSource:%s %s\n" "$DIM" "$RESET" "$SKILLS_SRC"
    printf "  %sTarget:%s %s\n\n" "$DIM" "$RESET" "$SKILLS_DST"
    printf "  %sLegend:%s %s[✓]%s linked  [ ] available  %s[!]%s conflict (real dir)\n" "$DIM" "$RESET" "$GREEN" "$RESET" "$RED" "$RESET"
    printf "  %s*%s = selected for action\n\n" "$YELLOW" "$RESET"
}

print_skills() {
    local total=${#SKILLS[@]}
    local page_start="${1:-0}"
    local page_end=$((page_start + PAGE_SIZE))
    [ "$page_end" -gt "$total" ] && page_end=$total

    local rows=$(( (page_end - page_start + COLS - 1) / COLS ))
    local col_width=40

    for (( r=0; r<rows; r++ )); do
        printf "  "
        for (( c=0; c<COLS; c++ )); do
            local idx=$(( page_start + r + c * rows ))
            [ "$idx" -ge "$page_end" ] && continue

            local name="${SKILLS[$idx]}"
            local st
            st=$(skill_status "$name")
            local indicator
            indicator=$(status_indicator "$st")
            local sel_marker=" "
            if [ "${SELECTED[$idx]}" -eq 1 ]; then
                sel_marker="${YELLOW}*${RESET}"
            fi

            # Truncate long names
            local display_name="$name"
            if [ ${#display_name} -gt 28 ]; then
                display_name="${display_name:0:25}..."
            fi

            printf "%s%3d%s %s %s%-28s%s" "$DIM" "$((idx + 1))" "$RESET" "$indicator" "$sel_marker" "$display_name" "$RESET"

            # Pad if not last column
            if [ "$c" -lt $((COLS - 1)) ]; then
                printf "  "
            fi
        done
        printf "\n"
    done

    if [ "$total" -gt "$PAGE_SIZE" ]; then
        local pages=$(( (total + PAGE_SIZE - 1) / PAGE_SIZE ))
        local cur_page=$(( page_start / PAGE_SIZE + 1 ))
        printf "\n  %sPage %d/%d%s  (n=next  p=prev)\n" "$DIM" "$cur_page" "$pages" "$RESET"
    fi
}

print_menu() {
    local sel_count=0
    for s in "${SELECTED[@]}"; do
        [ "$s" -eq 1 ] && ((sel_count++))
    done

    printf "\n  %s─────────────────────────────────────────%s\n" "$DIM" "$RESET"
    printf "  %sCommands:%s  [nums] toggle (1,3,5 or 1-10)  [a] select all/none\n" "$BOLD" "$RESET"
    printf "           [l] link selected (%d)  [u] unlink selected  [q] quit\n" "$sel_count"
    printf "  %s─────────────────────────────────────────%s\n" "$DIM" "$RESET"
}

# ── Selection parsing ─────────────────────────────────────────────────
parse_selection() {
    local input="$1"
    local total=${#SKILLS[@]}

    # Replace commas and spaces with newlines, process each token
    local tokens
    tokens=$(echo "$input" | tr ',' '\n' | tr ' ' '\n')

    while IFS= read -r token; do
        token=$(echo "$token" | tr -d '[:space:]')
        [ -z "$token" ] && continue

        if [[ "$token" =~ ^([0-9]+)-([0-9]+)$ ]]; then
            # Range: 1-10
            local from="${BASH_REMATCH[1]}"
            local to="${BASH_REMATCH[2]}"
            [ "$from" -lt 1 ] && from=1
            [ "$to" -gt "$total" ] && to=$total
            for (( i=from; i<=to; i++ )); do
                local idx=$((i - 1))
                if [ "$idx" -ge 0 ] && [ "$idx" -lt "$total" ]; then
                    SELECTED[$idx]=$(( 1 - SELECTED[$idx] ))
                fi
            done
        elif [[ "$token" =~ ^[0-9]+$ ]]; then
            # Single number
            local idx=$((token - 1))
            if [ "$idx" -ge 0 ] && [ "$idx" -lt "$total" ]; then
                SELECTED[$idx]=$(( 1 - SELECTED[$idx] ))
            else
                printf "  %s⚠ Invalid number: %s%s\n" "$YELLOW" "$token" "$RESET"
            fi
        else
            printf "  %s⚠ Unknown input: %s%s\n" "$YELLOW" "$token" "$RESET"
        fi
    done <<< "$tokens"
}

# ── Toggle all ────────────────────────────────────────────────────────
toggle_all() {
    local any_selected=0
    for s in "${SELECTED[@]}"; do
        [ "$s" -eq 1 ] && { any_selected=1; break; }
    done

    local new_val=1
    [ "$any_selected" -eq 1 ] && new_val=0

    for (( i=0; i<${#SELECTED[@]}; i++ )); do
        SELECTED[$i]=$new_val
    done
}

# ── Confirmation ──────────────────────────────────────────────────────
confirm() {
    local msg="$1"
    printf "\n  %s%s%s [y/N] " "$BOLD" "$msg" "$RESET"
    local reply
    read -r reply
    case "$reply" in
        [yY]|[yY][eE][sS]) return 0 ;;
        *) return 1 ;;
    esac
}

# ── Link selected ─────────────────────────────────────────────────────
link_selected() {
    local linked=0
    local skipped=0
    local conflicts=0

    # Collect names
    local names=()
    for (( i=0; i<${#SKILLS[@]}; i++ )); do
        [ "${SELECTED[$i]}" -eq 1 ] || continue
        names+=("${SKILLS[$i]}")
    done

    if [ ${#names[@]} -eq 0 ]; then
        printf "\n  %sNo skills selected.%s\n" "$YELLOW" "$RESET"
        sleep 1
        return
    fi

    printf "\n  Skills to link:\n"
    for name in "${names[@]}"; do
        printf "    %s→%s %s\n" "$CYAN" "$RESET" "$name"
    done

    if ! confirm "Link ${#names[@]} skill(s)?"; then
        printf "  %sCancelled.%s\n" "$DIM" "$RESET"
        sleep 1
        return
    fi

    mkdir -p "$SKILLS_DST"

    for name in "${names[@]}"; do
        local target="$SKILLS_DST/$name"
        local source="$SKILLS_SRC/$name"

        if [ -L "$target" ]; then
            # Already a symlink — replace it
            rm "$target"
            ln -s "$source" "$target"
            printf "  %s✓%s Re-linked: %s\n" "$GREEN" "$RESET" "$name"
            ((linked++))
        elif [ -d "$target" ]; then
            printf "  %s!%s Conflict (real dir): %s — skipped\n" "$RED" "$RESET" "$name"
            ((conflicts++))
        else
            ln -s "$source" "$target"
            printf "  %s✓%s Linked: %s\n" "$GREEN" "$RESET" "$name"
            ((linked++))
        fi
    done

    printf "\n  %sSummary:%s %d linked" "$BOLD" "$RESET" "$linked"
    [ "$skipped" -gt 0 ] && printf ", %d skipped" "$skipped"
    [ "$conflicts" -gt 0 ] && printf ", %s%d conflicts%s" "$RED" "$conflicts" "$RESET"
    printf "\n"

    # Clear selection after action
    for (( i=0; i<${#SELECTED[@]}; i++ )); do SELECTED[$i]=0; done

    printf "\n  Press Enter to continue..."
    read -r
}

# ── Unlink selected ───────────────────────────────────────────────────
unlink_selected() {
    local unlinked=0
    local skipped=0

    # Collect names that are actually symlinks
    local names=()
    for (( i=0; i<${#SKILLS[@]}; i++ )); do
        [ "${SELECTED[$i]}" -eq 1 ] || continue
        local target="$SKILLS_DST/${SKILLS[$i]}"
        if [ -L "$target" ]; then
            names+=("${SKILLS[$i]}")
        elif [ -d "$target" ]; then
            printf "  %s!%s %s is a real directory — will NOT remove\n" "$RED" "$RESET" "${SKILLS[$i]}"
            ((skipped++))
        fi
    done

    if [ ${#names[@]} -eq 0 ]; then
        printf "\n  %sNo linked skills in selection to unlink.%s\n" "$YELLOW" "$RESET"
        sleep 1
        return
    fi

    printf "\n  Skills to unlink:\n"
    for name in "${names[@]}"; do
        printf "    %s→%s %s\n" "$CYAN" "$RESET" "$name"
    done

    if ! confirm "Unlink ${#names[@]} skill(s)?"; then
        printf "  %sCancelled.%s\n" "$DIM" "$RESET"
        sleep 1
        return
    fi

    for name in "${names[@]}"; do
        local target="$SKILLS_DST/$name"
        # SAFETY: Only remove if it's a symlink
        if [ -L "$target" ]; then
            rm "$target"
            printf "  %s✓%s Unlinked: %s\n" "$GREEN" "$RESET" "$name"
            ((unlinked++))
        fi
    done

    printf "\n  %sSummary:%s %d unlinked" "$BOLD" "$RESET" "$unlinked"
    [ "$skipped" -gt 0 ] && printf ", %s%d skipped (real dirs)%s" "$RED" "$skipped" "$RESET"
    printf "\n"

    # Clear selection after action
    for (( i=0; i<${#SELECTED[@]}; i++ )); do SELECTED[$i]=0; done

    printf "\n  Press Enter to continue..."
    read -r
}

# ── Main loop ─────────────────────────────────────────────────────────
main() {
    if [ ! -d "$SKILLS_SRC" ]; then
        echo "Error: Skills source not found: $SKILLS_SRC"
        exit 1
    fi

    mkdir -p "$SKILLS_DST"
    load_skills

    if [ ${#SKILLS[@]} -eq 0 ]; then
        echo "No skills found in $SKILLS_SRC"
        exit 1
    fi

    local page=0
    local total=${#SKILLS[@]}
    local pages=$(( (total + PAGE_SIZE - 1) / PAGE_SIZE ))

    while true; do
        print_header
        print_skills $((page * PAGE_SIZE))
        print_menu

        printf "\n  > "
        read -r input

        case "$input" in
            q|Q|quit|exit)
                printf "\n  %sBye!%s\n\n" "$CYAN" "$RESET"
                exit 0
                ;;
            a|A)
                toggle_all
                ;;
            l|L)
                link_selected
                ;;
            u|U)
                unlink_selected
                ;;
            n|N)
                if [ $((page + 1)) -lt "$pages" ]; then
                    ((page++))
                fi
                ;;
            p|P)
                if [ "$page" -gt 0 ]; then
                    ((page--))
                fi
                ;;
            "")
                # Empty input — just refresh
                ;;
            *)
                # Try to parse as number selection
                if [[ "$input" =~ ^[0-9,\ \-]+$ ]]; then
                    parse_selection "$input"
                else
                    printf "  %s⚠ Unknown command: %s%s\n" "$YELLOW" "$input" "$RESET"
                    sleep 1
                fi
                ;;
        esac
    done
}

main "$@"
