#!/usr/bin/env bash
#
# upload-sbom.sh - Upload CycloneDX SBOM to Dependency-Track
#
# Usage:
#   ./upload-sbom.sh -f bom.json -n "project-name" -v "1.0.0"
#   ./upload-sbom.sh -f bom.json -u "project-uuid"
#
# Environment variables:
#   DTRACK_URL      - Dependency-Track base URL
#   DTRACK_API_KEY  - API key for authentication
#
# Options:
#   -f, --file      BOM file path (required)
#   -n, --name      Project name (required if no UUID)
#   -v, --version   Project version (required if no UUID)
#   -u, --uuid      Project UUID (alternative to name/version)
#   -a, --auto      Auto-create project if not exists (default: true)
#   -w, --wait      Wait for processing to complete
#   -t, --timeout   Timeout in seconds for waiting (default: 300)
#   -h, --help      Show this help message

set -euo pipefail

# Default values
AUTO_CREATE="true"
WAIT="false"
TIMEOUT=300
POLL_INTERVAL=5

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

usage() {
    grep '^#' "$0" | grep -v '#!/' | cut -c3-
    exit 1
}

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -f|--file)
            BOM_FILE="$2"
            shift 2
            ;;
        -n|--name)
            PROJECT_NAME="$2"
            shift 2
            ;;
        -v|--version)
            PROJECT_VERSION="$2"
            shift 2
            ;;
        -u|--uuid)
            PROJECT_UUID="$2"
            shift 2
            ;;
        -a|--auto)
            AUTO_CREATE="$2"
            shift 2
            ;;
        -w|--wait)
            WAIT="true"
            shift
            ;;
        -t|--timeout)
            TIMEOUT="$2"
            shift 2
            ;;
        -h|--help)
            usage
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            ;;
    esac
done

# Validate environment
if [[ -z "${DTRACK_URL:-}" ]]; then
    log_error "DTRACK_URL environment variable not set"
    exit 1
fi

if [[ -z "${DTRACK_API_KEY:-}" ]]; then
    log_error "DTRACK_API_KEY environment variable not set"
    exit 1
fi

# Validate arguments
if [[ -z "${BOM_FILE:-}" ]]; then
    log_error "BOM file is required (-f/--file)"
    usage
fi

if [[ ! -f "$BOM_FILE" ]]; then
    log_error "BOM file not found: $BOM_FILE"
    exit 1
fi

if [[ -z "${PROJECT_UUID:-}" ]] && [[ -z "${PROJECT_NAME:-}" || -z "${PROJECT_VERSION:-}" ]]; then
    log_error "Either project UUID (-u) or project name (-n) and version (-v) are required"
    usage
fi

# Base64 encode the BOM
log_info "Encoding BOM file: $BOM_FILE"
BOM_CONTENT=$(base64 -w0 "$BOM_FILE")

# Build JSON payload
if [[ -n "${PROJECT_UUID:-}" ]]; then
    PAYLOAD=$(cat <<EOF
{
    "project": "${PROJECT_UUID}",
    "autoCreate": ${AUTO_CREATE},
    "bom": "${BOM_CONTENT}"
}
EOF
)
else
    PAYLOAD=$(cat <<EOF
{
    "projectName": "${PROJECT_NAME}",
    "projectVersion": "${PROJECT_VERSION}",
    "autoCreate": ${AUTO_CREATE},
    "bom": "${BOM_CONTENT}"
}
EOF
)
fi

# Upload SBOM
log_info "Uploading SBOM to Dependency-Track..."
RESPONSE=$(curl -s -w "\n%{http_code}" -X PUT "${DTRACK_URL}/api/v1/bom" \
    -H "X-Api-Key: ${DTRACK_API_KEY}" \
    -H "Content-Type: application/json" \
    -d "${PAYLOAD}")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | head -n-1)

if [[ "$HTTP_CODE" -ne 200 ]]; then
    log_error "Failed to upload SBOM. HTTP $HTTP_CODE"
    echo "$BODY"
    exit 1
fi

TOKEN=$(echo "$BODY" | jq -r '.token')
log_info "SBOM uploaded successfully. Token: $TOKEN"

# Wait for processing if requested
if [[ "$WAIT" == "true" ]]; then
    log_info "Waiting for BOM processing to complete (timeout: ${TIMEOUT}s)..."

    START_TIME=$(date +%s)
    while true; do
        ELAPSED=$(($(date +%s) - START_TIME))
        if [[ $ELAPSED -ge $TIMEOUT ]]; then
            log_error "Timeout waiting for BOM processing"
            exit 1
        fi

        STATUS=$(curl -s -H "X-Api-Key: ${DTRACK_API_KEY}" \
            "${DTRACK_URL}/api/v1/bom/token/${TOKEN}")

        PROCESSING=$(echo "$STATUS" | jq -r '.processing')

        if [[ "$PROCESSING" == "false" ]]; then
            log_info "BOM processing complete!"
            break
        fi

        echo -n "."
        sleep $POLL_INTERVAL
    done
fi

# Output the token for use in other scripts
echo "$TOKEN"
