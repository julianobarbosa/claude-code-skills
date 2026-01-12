#!/bin/bash
# op-env-export.sh - Export environment to .env file format
#
# Usage:
#   op-env-export.sh <name> <vault> [--format <format>]
#
# Examples:
#   op-env-export.sh my-app-dev Development > .env
#   op-env-export.sh my-app-prod Production --format docker
#   op-env-export.sh azure-config Shared --format op-refs

set -euo pipefail

# Colors (only for stderr to not pollute output)
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1" >&2; }
log_error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }

show_help() {
    cat << 'EOF'
op-env-export - Export environment to .env file format

USAGE:
    op-env-export.sh <name> <vault> [OPTIONS]

ARGUMENTS:
    <name>      Name/title of the environment item
    <vault>     Vault containing the item

OPTIONS:
    --format <fmt>   Output format (default: env)
                     - env: Standard KEY=value format
                     - docker: Docker-compatible with quotes
                     - op-refs: Use op:// references (for templates)
                     - json: JSON key-value object
    --prefix <str>   Add prefix to all variable names
    --help           Show this help message

EXAMPLES:
    # Export to .env file
    op-env-export.sh my-app-dev Development > .env

    # Docker-compatible format
    op-env-export.sh my-app Development --format docker > .env

    # Create template with op:// references
    op-env-export.sh my-app-prod Production --format op-refs > .env.tpl

    # JSON format
    op-env-export.sh config Shared --format json

    # Add prefix to all variables
    op-env-export.sh azure Shared --prefix AZURE_ > .env

NOTES:
    - Output goes to stdout, redirect to file as needed
    - Use --format op-refs to create templates for op inject/run
    - Values are retrieved with revealed secrets
EOF
}

# Parse arguments
ENV_NAME=""
VAULT=""
FORMAT="env"
PREFIX=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            show_help
            exit 0
            ;;
        --format)
            FORMAT="$2"
            shift 2
            ;;
        --prefix)
            PREFIX="$2"
            shift 2
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

log_info "Exporting: $ENV_NAME from $VAULT (format: $FORMAT)"

# Get item with revealed values
item_json=$(op item get "$ENV_NAME" --vault "$VAULT" --format json --reveal)

# Extract variables
# Try 'variables' section first, then fall back to concealed fields
variables=$(echo "$item_json" | jq -r '
    .fields[]? |
    select(.section.label == "variables" or .section.id == "variables" or .type == "CONCEALED") |
    select(.label != null and .label != "") |
    "\(.label)=\(.value // "")"
' 2>/dev/null)

if [[ -z "$variables" ]]; then
    log_error "No variables found in environment"
    exit 1
fi

# Output header comment
case "$FORMAT" in
    env|docker)
        echo "# Generated from 1Password: $ENV_NAME ($VAULT)"
        echo "# Date: $(date -Iseconds)"
        echo ""
        ;;
    op-refs)
        echo "# 1Password Template: $ENV_NAME ($VAULT)"
        echo "# Use with: op inject -i .env.tpl -o .env"
        echo "# Or: op run --env-file .env.tpl -- command"
        echo ""
        ;;
esac

# Process and output variables
case "$FORMAT" in
    env)
        while IFS='=' read -r key value; do
            [[ -z "$key" ]] && continue
            # Escape special characters
            escaped_value=$(echo "$value" | sed 's/\\/\\\\/g; s/"/\\"/g')
            echo "${PREFIX}${key}=${escaped_value}"
        done <<< "$variables"
        ;;

    docker)
        while IFS='=' read -r key value; do
            [[ -z "$key" ]] && continue
            # Quote values for Docker
            escaped_value=$(echo "$value" | sed 's/\\/\\\\/g; s/"/\\"/g')
            echo "${PREFIX}${key}=\"${escaped_value}\""
        done <<< "$variables"
        ;;

    op-refs)
        while IFS='=' read -r key value; do
            [[ -z "$key" ]] && continue
            echo "${PREFIX}${key}=op://${VAULT}/${ENV_NAME}/variables/${key}"
        done <<< "$variables"
        ;;

    json)
        echo "{"
        first=true
        while IFS='=' read -r key value; do
            [[ -z "$key" ]] && continue
            if [[ "$first" != true ]]; then
                echo ","
            fi
            first=false
            # Escape for JSON
            escaped_value=$(echo "$value" | jq -R .)
            printf '  "%s%s": %s' "$PREFIX" "$key" "$escaped_value"
        done <<< "$variables"
        echo ""
        echo "}"
        ;;

    *)
        log_error "Unknown format: $FORMAT"
        log_error "Supported formats: env, docker, op-refs, json"
        exit 1
        ;;
esac

log_info "Export complete"
