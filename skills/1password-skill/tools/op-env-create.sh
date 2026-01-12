#!/bin/bash
# op-env-create.sh - Create environment item in 1Password
# Uses API Credential category to store environment variables
#
# Usage:
#   op-env-create.sh <name> <vault> [--from-file <.env>] [key=value...]
#
# Examples:
#   op-env-create.sh my-app-dev Development API_KEY=xxx DB_HOST=localhost
#   op-env-create.sh my-app-prod Production --from-file .env.prod
#   op-env-create.sh azure-config Shared --from-file .env EXTRA_KEY=value

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
op-env-create - Create environment item in 1Password

USAGE:
    op-env-create.sh <name> <vault> [OPTIONS] [key=value...]

ARGUMENTS:
    <name>      Name/title for the environment item
    <vault>     Vault to store the item in

OPTIONS:
    --from-file <path>   Import variables from .env file
    --tags <tags>        Comma-separated tags (default: environment)
    --help               Show this help message

EXAMPLES:
    # Create with inline variables
    op-env-create.sh my-app-dev Development API_KEY=xxx DB_HOST=localhost

    # Create from .env file
    op-env-create.sh my-app-prod Production --from-file .env.prod

    # Combine file and inline (inline overrides file)
    op-env-create.sh azure-config Shared --from-file .env EXTRA_KEY=value

    # With custom tags
    op-env-create.sh secrets DevOps --tags "env,production,api" KEY=value

NOTES:
    - Uses API Credential category for environment storage
    - Variables are stored as concealed fields for security
    - Tags help organize and filter environments
    - Use 'op-env-list.sh' to view created environments
    - Use 'op-env-export.sh' to export to .env format
EOF
}

# Parse arguments
ENV_NAME=""
VAULT=""
ENV_FILE=""
TAGS="environment"
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
        --tags)
            TAGS="$2"
            shift 2
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
    log_error "1Password CLI (op) not found. Install from: https://developer.1password.com/docs/cli"
    exit 1
fi

# Check authentication
if ! op whoami &> /dev/null; then
    log_error "Not signed in to 1Password. Run: op signin"
    exit 1
fi

# Check if item already exists
if op item get "$ENV_NAME" --vault "$VAULT" &> /dev/null; then
    log_error "Item '$ENV_NAME' already exists in vault '$VAULT'"
    log_info "Use op-env-update.sh to modify existing environment"
    exit 1
fi

# Declare associative array for variables
declare -A env_vars

# Parse .env file if provided
if [[ -n "$ENV_FILE" ]]; then
    if [[ ! -f "$ENV_FILE" ]]; then
        log_error "File not found: $ENV_FILE"
        exit 1
    fi

    log_info "Loading variables from: $ENV_FILE"
    while IFS= read -r line || [[ -n "$line" ]]; do
        # Skip comments and empty lines
        [[ "$line" =~ ^[[:space:]]*# ]] && continue
        [[ -z "${line// }" ]] && continue

        # Parse KEY=VALUE (handle quotes)
        if [[ "$line" =~ ^([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]]; then
            key="${BASH_REMATCH[1]}"
            value="${BASH_REMATCH[2]}"
            # Remove surrounding quotes
            value="${value#\"}"
            value="${value%\"}"
            value="${value#\'}"
            value="${value%\'}"
            env_vars["$key"]="$value"
        fi
    done < "$ENV_FILE"
fi

# Add/override with inline variables
for var in "${VARS[@]}"; do
    if [[ "$var" =~ ^([A-Za-z_][A-Za-z0-9_]*)=(.*)$ ]]; then
        key="${BASH_REMATCH[1]}"
        value="${BASH_REMATCH[2]}"
        env_vars["$key"]="$value"
    fi
done

# Validate we have variables
if [[ ${#env_vars[@]} -eq 0 ]]; then
    log_error "No environment variables provided"
    log_info "Use --from-file <.env> or provide KEY=value pairs"
    exit 1
fi

log_info "Creating environment: $ENV_NAME in vault: $VAULT"
log_info "Variables: ${!env_vars[@]}"

# Build field arguments
field_args=()
for key in "${!env_vars[@]}"; do
    # Store as concealed fields in 'variables' section
    field_args+=("variables.${key}[concealed]=${env_vars[$key]}")
done

# Create the item
if op item create \
    --category "API Credential" \
    --title "$ENV_NAME" \
    --vault "$VAULT" \
    --tags "$TAGS" \
    "${field_args[@]}" \
    > /dev/null; then

    log_info "Environment '$ENV_NAME' created successfully"
    echo ""
    echo "Variables stored:"
    for key in "${!env_vars[@]}"; do
        echo "  - $key"
    done
    echo ""
    echo "Usage:"
    echo "  # Export to .env file"
    echo "  op-env-export.sh '$ENV_NAME' '$VAULT' > .env"
    echo ""
    echo "  # Read single variable"
    echo "  op read 'op://$VAULT/$ENV_NAME/variables/$key'"
else
    log_error "Failed to create environment"
    exit 1
fi
