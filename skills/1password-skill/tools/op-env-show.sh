#!/bin/bash
# op-env-show.sh - Display environment item details from 1Password
#
# Usage:
#   op-env-show.sh <name> <vault> [--reveal]
#
# Examples:
#   op-env-show.sh my-app-dev Development
#   op-env-show.sh my-app-prod Production --reveal

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
op-env-show - Display environment item details from 1Password

USAGE:
    op-env-show.sh <name> <vault> [OPTIONS]

ARGUMENTS:
    <name>      Name/title of the environment item
    <vault>     Vault containing the item

OPTIONS:
    --reveal    Show concealed values (default: masked)
    --json      Output in JSON format
    --keys      Show only variable names (no values)
    --help      Show this help message

EXAMPLES:
    # Show with masked values
    op-env-show.sh my-app-dev Development

    # Show with revealed values
    op-env-show.sh my-app-prod Production --reveal

    # JSON output
    op-env-show.sh my-app-dev Development --json

    # List only variable names
    op-env-show.sh azure-config Shared --keys

NOTES:
    - Values are masked by default for security
    - Use --reveal to see actual values
    - JSON output includes all field metadata
EOF
}

# Parse arguments
ENV_NAME=""
VAULT=""
REVEAL=false
JSON_OUTPUT=false
KEYS_ONLY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            show_help
            exit 0
            ;;
        --reveal|-r)
            REVEAL=true
            shift
            ;;
        --json)
            JSON_OUTPUT=true
            shift
            ;;
        --keys)
            KEYS_ONLY=true
            shift
            ;;
        *)
            if [[ -z "$ENV_NAME" ]]; then
                ENV_NAME="$1"
            elif [[ -z "$VAULT" ]]; then
                VAULT="$1"
            else
                log_error "Unknown argument: $1"
                exit 1
            fi
            shift
            ;;
    esac
done

# Validate required args
if [[ -z "$ENV_NAME" ]] || [[ -z "$VAULT" ]]; then
    log_error "Missing required arguments: name and vault"
    echo ""
    show_help
    exit 1
fi

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

# Check if item exists
if ! op item get "$ENV_NAME" --vault "$VAULT" &> /dev/null; then
    log_error "Item '$ENV_NAME' not found in vault '$VAULT'"
    exit 1
fi

# JSON output mode
if [[ "$JSON_OUTPUT" == true ]]; then
    if [[ "$REVEAL" == true ]]; then
        op item get "$ENV_NAME" --vault "$VAULT" --format json --reveal
    else
        op item get "$ENV_NAME" --vault "$VAULT" --format json
    fi
    exit 0
fi

# Get item data
item_json=$(op item get "$ENV_NAME" --vault "$VAULT" --format json)

# Extract metadata
title=$(echo "$item_json" | jq -r '.title')
vault_name=$(echo "$item_json" | jq -r '.vault.name')
category=$(echo "$item_json" | jq -r '.category')
created=$(echo "$item_json" | jq -r '.created_at // "N/A"')
updated=$(echo "$item_json" | jq -r '.updated_at // "N/A"')
tags=$(echo "$item_json" | jq -r '(.tags // []) | join(", ")')

# Display header
echo ""
echo -e "${CYAN}╔═══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║${NC} Environment: ${GREEN}$title${NC}"
echo -e "${CYAN}╠═══════════════════════════════════════════════════════════════╣${NC}"
echo -e "${CYAN}║${NC} Vault: $vault_name"
echo -e "${CYAN}║${NC} Category: $category"
echo -e "${CYAN}║${NC} Tags: ${tags:-none}"
echo -e "${CYAN}║${NC} Created: $created"
echo -e "${CYAN}║${NC} Updated: $updated"
echo -e "${CYAN}╠═══════════════════════════════════════════════════════════════╣${NC}"
echo -e "${CYAN}║${NC} Variables:"
echo -e "${CYAN}╚═══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Extract variables from 'variables' section
variables=$(echo "$item_json" | jq -r '.fields[]? | select(.section.label == "variables" or .section.id == "variables") | "\(.label)=\(.value // "")"' 2>/dev/null)

if [[ -z "$variables" ]]; then
    # Fallback: try to get all concealed fields
    variables=$(echo "$item_json" | jq -r '.fields[]? | select(.type == "CONCEALED") | "\(.label)=\(.value // "")"' 2>/dev/null)
fi

if [[ -z "$variables" ]]; then
    echo "  (no variables found)"
else
    while IFS='=' read -r key value; do
        if [[ "$KEYS_ONLY" == true ]]; then
            echo "  $key"
        elif [[ "$REVEAL" == true ]]; then
            # Get revealed value
            revealed_value=$(op read "op://$VAULT/$ENV_NAME/variables/$key" 2>/dev/null || echo "$value")
            echo "  $key=$revealed_value"
        else
            # Mask the value
            if [[ -n "$value" ]]; then
                masked="********"
            else
                masked="(empty)"
            fi
            echo "  $key=$masked"
        fi
    done <<< "$variables"
fi

echo ""
if [[ "$REVEAL" != true ]] && [[ "$KEYS_ONLY" != true ]]; then
    echo "Tip: Use --reveal to show actual values"
fi
