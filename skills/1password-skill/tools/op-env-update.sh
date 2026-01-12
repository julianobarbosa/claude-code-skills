#!/bin/bash
# op-env-update.sh - Update environment item in 1Password
# Modifies existing environment items (add/update/remove variables)
#
# Usage:
#   op-env-update.sh <name> <vault> [OPTIONS] [key=value...]
#
# Examples:
#   op-env-update.sh my-app-dev Development API_KEY=new-key
#   op-env-update.sh my-app-prod Production --from-file .env.prod
#   op-env-update.sh azure-config Shared --remove OLD_KEY

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

show_help() {
    cat << 'EOF'
op-env-update - Update environment item in 1Password

USAGE:
    op-env-update.sh <name> <vault> [OPTIONS] [key=value...]

ARGUMENTS:
    <name>      Name/title of the environment item
    <vault>     Vault containing the item

OPTIONS:
    --from-file <path>   Import/merge variables from .env file
    --remove <keys>      Comma-separated list of keys to remove
    --replace            Replace all variables (instead of merge)
    --help               Show this help message

EXAMPLES:
    # Update single variable
    op-env-update.sh my-app-dev Development API_KEY=new-key

    # Merge from .env file (keeps existing, updates matching)
    op-env-update.sh my-app-prod Production --from-file .env.prod

    # Replace all variables from file
    op-env-update.sh my-app-prod Production --replace --from-file .env.prod

    # Remove specific variables
    op-env-update.sh azure-config Shared --remove OLD_KEY,DEPRECATED_VAR

    # Update and remove in one command
    op-env-update.sh my-app Development NEW_KEY=value --remove OLD_KEY

NOTES:
    - By default, updates merge with existing variables
    - Use --replace to completely replace all variables
    - Removed keys are permanently deleted from the item
EOF
}

# Parse arguments
ENV_NAME=""
VAULT=""
ENV_FILE=""
REMOVE_KEYS=""
REPLACE_MODE=false
declare -a VARS=()

while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            show_help
            exit 0
            ;;
        --from-file)
            ENV_FILE="$2"
            shift 2
            ;;
        --remove)
            REMOVE_KEYS="$2"
            shift 2
            ;;
        --replace)
            REPLACE_MODE=true
            shift
            ;;
        *=*)
            VARS+=("$1")
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
    log_info "Use op-env-create.sh to create a new environment"
    exit 1
fi

# Declare associative array for new variables
declare -A new_vars

# Parse .env file if provided
if [[ -n "$ENV_FILE" ]]; then
    if [[ ! -f "$ENV_FILE" ]]; then
        log_error "File not found: $ENV_FILE"
        exit 1
    fi

    log_info "Loading variables from: $ENV_FILE"
    while IFS= read -r line || [[ -n "$line" ]]; do
        [[ "$line" =~ ^[[:space:]]*# ]] && continue
        [[ -z "${line// }" ]] && continue

        if [[ "$line" =~ ^([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]]; then
            key="${BASH_REMATCH[1]}"
            value="${BASH_REMATCH[2]}"
            value="${value#\"}"
            value="${value%\"}"
            value="${value#\'}"
            value="${value%\'}"
            new_vars["$key"]="$value"
        fi
    done < "$ENV_FILE"
fi

# Add/override with inline variables
for var in "${VARS[@]}"; do
    if [[ "$var" =~ ^([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]]; then
        key="${BASH_REMATCH[1]}"
        value="${BASH_REMATCH[2]}"
        new_vars["$key"]="$value"
    fi
done

log_info "Updating environment: $ENV_NAME in vault: $VAULT"

# Build edit command arguments
edit_args=()

# Add/update variables
for key in "${!new_vars[@]}"; do
    edit_args+=("variables.${key}[concealed]=${new_vars[$key]}")
done

# Handle removals
if [[ -n "$REMOVE_KEYS" ]]; then
    IFS=',' read -ra keys_to_remove <<< "$REMOVE_KEYS"
    for key in "${keys_to_remove[@]}"; do
        key=$(echo "$key" | tr -d ' ')  # trim whitespace
        log_info "Removing variable: $key"
        # Delete field using op item edit
        op item edit "$ENV_NAME" --vault "$VAULT" "variables.${key}[delete]" 2>/dev/null || true
    done
fi

# Apply updates if we have new/updated vars
if [[ ${#edit_args[@]} -gt 0 ]]; then
    log_info "Updating variables: ${!new_vars[@]}"

    if op item edit "$ENV_NAME" --vault "$VAULT" "${edit_args[@]}" > /dev/null; then
        log_info "Environment '$ENV_NAME' updated successfully"
    else
        log_error "Failed to update environment"
        exit 1
    fi
else
    if [[ -z "$REMOVE_KEYS" ]]; then
        log_warn "No variables to update"
    fi
fi

echo ""
echo "Current state:"
echo "  op-env-show.sh '$ENV_NAME' '$VAULT'"
