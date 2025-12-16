#!/usr/bin/env bash
#
# setup-service-account.sh
# Create and configure a 1Password service account for automation
#
# Usage:
#   ./setup-service-account.sh <name> <vault> [permissions]
#
# Arguments:
#   name        - Name for the service account (e.g., "CI-CD-Pipeline")
#   vault       - Vault name or ID to grant access to
#   permissions - Comma-separated permissions (default: read_items)
#                 Options: read_items, write_items, share_items
#
# Examples:
#   ./setup-service-account.sh "GitHub-Actions" "Production" "read_items"
#   ./setup-service-account.sh "Deploy-Bot" "Staging" "read_items,write_items"
#
# Requirements:
#   - 1Password CLI (op) version 2.18.0 or later
#   - Signed in to 1Password account with admin permissions
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print functions
info() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1" >&2; }

# Check prerequisites
check_prerequisites() {
    info "Checking prerequisites..."

    # Check if op CLI is installed
    if ! command -v op &> /dev/null; then
        error "1Password CLI (op) is not installed."
        echo "Install it from: https://1password.com/downloads/command-line"
        exit 1
    fi

    # Check op version
    OP_VERSION=$(op --version | head -1)
    info "Found 1Password CLI version: $OP_VERSION"

    # Check if signed in
    if ! op whoami &> /dev/null; then
        error "Not signed in to 1Password."
        echo "Run 'op signin' first."
        exit 1
    fi

    ACCOUNT=$(op whoami --format json | jq -r '.email // .url')
    success "Signed in as: $ACCOUNT"
}

# Validate vault exists
validate_vault() {
    local vault="$1"
    info "Validating vault: $vault"

    if ! op vault get "$vault" &> /dev/null; then
        error "Vault '$vault' not found or not accessible."
        echo ""
        echo "Available vaults:"
        op vault list --format json | jq -r '.[] | "  - \(.name) (\(.id))"'
        exit 1
    fi

    VAULT_ID=$(op vault get "$vault" --format json | jq -r '.id')
    success "Found vault: $vault (ID: $VAULT_ID)"
}

# Parse and validate permissions
parse_permissions() {
    local perms="$1"
    local valid_perms=("read_items" "write_items" "share_items")

    IFS=',' read -ra PERM_ARRAY <<< "$perms"

    for perm in "${PERM_ARRAY[@]}"; do
        perm=$(echo "$perm" | tr -d ' ')
        local found=false
        for valid in "${valid_perms[@]}"; do
            if [[ "$perm" == "$valid" ]]; then
                found=true
                break
            fi
        done
        if [[ "$found" == "false" ]]; then
            error "Invalid permission: $perm"
            echo "Valid permissions: ${valid_perms[*]}"
            exit 1
        fi
    done

    success "Permissions validated: $perms"
}

# Create service account
create_service_account() {
    local name="$1"
    local vault="$2"
    local permissions="$3"

    info "Creating service account: $name"
    info "Vault: $vault"
    info "Permissions: $permissions"
    echo ""

    # Build the command
    local cmd="op service-account create \"$name\" --vault \"$vault:$permissions\""

    info "Running: $cmd"
    echo ""

    # Execute and capture the token
    local output
    if output=$(op service-account create "$name" --vault "$vault:$permissions" 2>&1); then
        echo ""
        success "Service account created successfully!"
        echo ""
        echo -e "${YELLOW}========================================${NC}"
        echo -e "${YELLOW}  IMPORTANT: Save this token securely!  ${NC}"
        echo -e "${YELLOW}  It will NOT be shown again.           ${NC}"
        echo -e "${YELLOW}========================================${NC}"
        echo ""
        echo "$output"
        echo ""
        echo -e "${BLUE}Usage:${NC}"
        echo "  export OP_SERVICE_ACCOUNT_TOKEN=\"<token>\""
        echo "  op vault list  # Test connection"
        echo ""
        echo -e "${BLUE}In CI/CD:${NC}"
        echo "  Store the token as a secret named OP_SERVICE_ACCOUNT_TOKEN"
        echo ""
    else
        error "Failed to create service account:"
        echo "$output"
        exit 1
    fi
}

# Show usage
usage() {
    echo "Usage: $0 <name> <vault> [permissions]"
    echo ""
    echo "Arguments:"
    echo "  name        - Name for the service account"
    echo "  vault       - Vault name or ID to grant access to"
    echo "  permissions - Comma-separated permissions (default: read_items)"
    echo "                Options: read_items, write_items, share_items"
    echo ""
    echo "Examples:"
    echo "  $0 \"GitHub-Actions\" \"Production\" \"read_items\""
    echo "  $0 \"Deploy-Bot\" \"Staging\" \"read_items,write_items\""
    exit 1
}

# Main
main() {
    # Check arguments
    if [[ $# -lt 2 ]]; then
        usage
    fi

    local name="$1"
    local vault="$2"
    local permissions="${3:-read_items}"

    echo ""
    echo "1Password Service Account Setup"
    echo "================================"
    echo ""

    check_prerequisites
    echo ""
    validate_vault "$vault"
    echo ""
    parse_permissions "$permissions"
    echo ""

    # Confirm before creating
    echo -e "${YELLOW}About to create service account:${NC}"
    echo "  Name:        $name"
    echo "  Vault:       $vault"
    echo "  Permissions: $permissions"
    echo ""
    read -p "Continue? (y/N) " -n 1 -r
    echo ""

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        info "Aborted."
        exit 0
    fi

    echo ""
    create_service_account "$name" "$vault" "$permissions"
}

main "$@"
