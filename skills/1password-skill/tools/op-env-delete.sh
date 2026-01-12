#!/bin/bash
# op-env-delete.sh - Delete environment item from 1Password
#
# Usage:
#   op-env-delete.sh <name> <vault> [--force]
#
# Examples:
#   op-env-delete.sh my-app-dev Development
#   op-env-delete.sh old-config Shared --force

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
op-env-delete - Delete environment item from 1Password

USAGE:
    op-env-delete.sh <name> <vault> [OPTIONS]

ARGUMENTS:
    <name>      Name/title of the environment item
    <vault>     Vault containing the item

OPTIONS:
    --force     Skip confirmation prompt
    --archive   Archive instead of permanent delete
    --help      Show this help message

EXAMPLES:
    # Interactive deletion (asks for confirmation)
    op-env-delete.sh my-app-dev Development

    # Force delete without confirmation
    op-env-delete.sh old-config Shared --force

    # Archive instead of delete
    op-env-delete.sh deprecated-env Production --archive

NOTES:
    - Deleted items cannot be recovered (unless archived)
    - Use --archive to soft-delete and preserve history
    - Consider exporting before deleting: op-env-export.sh
EOF
}

# Parse arguments
ENV_NAME=""
VAULT=""
FORCE=false
ARCHIVE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --help|-h)
            show_help
            exit 0
            ;;
        --force|-f)
            FORCE=true
            shift
            ;;
        --archive)
            ARCHIVE=true
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

# Show item info
log_info "Environment to delete:"
echo "  Name: $ENV_NAME"
echo "  Vault: $VAULT"
echo ""

# Confirm unless force
if [[ "$FORCE" != true ]]; then
    if [[ "$ARCHIVE" == true ]]; then
        echo -n "Archive this environment? [y/N] "
    else
        echo -n "Permanently DELETE this environment? [y/N] "
    fi
    read -r response
    if [[ ! "$response" =~ ^[Yy]$ ]]; then
        log_info "Cancelled"
        exit 0
    fi
fi

# Delete or archive
if [[ "$ARCHIVE" == true ]]; then
    if op item delete "$ENV_NAME" --vault "$VAULT" --archive; then
        log_info "Environment '$ENV_NAME' archived successfully"
    else
        log_error "Failed to archive environment"
        exit 1
    fi
else
    if op item delete "$ENV_NAME" --vault "$VAULT"; then
        log_info "Environment '$ENV_NAME' deleted permanently"
    else
        log_error "Failed to delete environment"
        exit 1
    fi
fi
