#!/bin/bash
# op-env-list.sh - List environment items from 1Password
#
# Usage:
#   op-env-list.sh [--vault <vault>] [--tags <tags>]
#
# Examples:
#   op-env-list.sh
#   op-env-list.sh --vault Development
#   op-env-list.sh --tags environment,production

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

show_help() {
    cat << 'EOF'
op-env-list - List environment items from 1Password

USAGE:
    op-env-list.sh [OPTIONS]

OPTIONS:
    --vault <vault>   Filter by vault name
    --tags <tags>     Filter by tags (comma-separated)
    --json            Output in JSON format
    --help            Show this help message

EXAMPLES:
    # List all environments
    op-env-list.sh

    # Filter by vault
    op-env-list.sh --vault Development

    # Filter by tags
    op-env-list.sh --tags environment,production

    # JSON output
    op-env-list.sh --json

NOTES:
    - Lists items tagged with 'environment' by default
    - Use --tags to filter by different tags
    - Environments are stored as API Credential items
EOF
}

# Parse arguments
VAULT=""
TAGS="environment"
JSON_OUTPUT=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            show_help
            exit 0
            ;;
        --vault)
            VAULT="$2"
            shift 2
            ;;
        --tags)
            TAGS="$2"
            shift 2
            ;;
        --json)
            JSON_OUTPUT=true
            shift
            ;;
        *)
            log_error "Unknown argument: $1"
            exit 1
            ;;
    esac
done

# Check op CLI
if ! command -v op &> /dev/null; then
    log_error "1Password CLI (op) not found"
    exit 1
fi

# Check authentication
if ! op whoami &> /dev/null; then
    log_error "Not signed in to 1Password. Run: op signin"
    exit 1
fi

# Build command
cmd="op item list --tags \"$TAGS\" --format json"
if [[ -n "$VAULT" ]]; then
    cmd="op item list --vault \"$VAULT\" --tags \"$TAGS\" --format json"
fi

# Execute
items=$(eval "$cmd" 2>/dev/null || echo "[]")

# JSON output mode
if [[ "$JSON_OUTPUT" == true ]]; then
    echo "$items" | jq '.'
    exit 0
fi

# Parse and display
count=$(echo "$items" | jq 'length')

if [[ "$count" -eq 0 ]]; then
    echo "No environments found"
    echo ""
    echo "Tip: Create one with: op-env-create.sh <name> <vault> KEY=value"
    exit 0
fi

echo ""
echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║${NC}                           1Password Environments                              ${CYAN}║${NC}"
echo -e "${CYAN}╠═══════════════════════════════════════════════════════════════════════════════╣${NC}"
printf "${CYAN}║${NC} %-35s │ %-20s │ %-15s ${CYAN}║${NC}\n" "NAME" "VAULT" "UPDATED"
echo -e "${CYAN}╠═══════════════════════════════════════════════════════════════════════════════╣${NC}"

echo "$items" | jq -r '.[] | "\(.title)|\(.vault.name)|\(.updated_at // "N/A")"' | while IFS='|' read -r title vault updated; do
    # Truncate if too long
    title=$(echo "$title" | cut -c1-35)
    vault=$(echo "$vault" | cut -c1-20)
    # Format date
    if [[ "$updated" != "N/A" ]]; then
        updated=$(echo "$updated" | cut -c1-10)
    fi
    printf "${CYAN}║${NC} %-35s │ %-20s │ %-15s ${CYAN}║${NC}\n" "$title" "$vault" "$updated"
done

echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Total: $count environments"
echo ""
echo "Commands:"
echo "  Show details: op-env-show.sh <name> <vault>"
echo "  Export .env:  op-env-export.sh <name> <vault> > .env"
