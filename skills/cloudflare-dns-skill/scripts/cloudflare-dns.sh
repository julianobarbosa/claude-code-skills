#!/usr/bin/env bash
#
# Cloudflare DNS Management Script
# Helper script for common DNS operations
#
# Usage:
#   ./cloudflare-dns.sh <command> [args]
#
# Commands:
#   list-zones                     List all zones
#   list-records [zone_id]         List DNS records for a zone
#   get-record <zone_id> <name>    Get specific record by name
#   create-a <zone_id> <name> <ip> [proxied]    Create A record
#   create-cname <zone_id> <name> <target> [proxied]  Create CNAME
#   delete-record <zone_id> <record_id>  Delete record
#   export <zone_id>               Export zone to BIND format
#   verify-token                   Verify API token validity
#
# Environment Variables:
#   CF_API_TOKEN - Cloudflare API Token (required)
#   CF_ZONE_ID   - Default zone ID (optional)
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Cloudflare API base URL
CF_API="https://api.cloudflare.com/client/v4"

# Check required environment
check_token() {
    if [[ -z "${CF_API_TOKEN:-}" ]]; then
        echo -e "${RED}Error: CF_API_TOKEN environment variable not set${NC}"
        echo "Export your Cloudflare API token:"
        echo "  export CF_API_TOKEN='your-api-token'"
        exit 1
    fi
}

# API request helper
cf_api() {
    local method="$1"
    local endpoint="$2"
    local data="${3:-}"

    local args=(-s -X "$method")
    args+=(-H "Authorization: Bearer $CF_API_TOKEN")
    args+=(-H "Content-Type: application/json")

    if [[ -n "$data" ]]; then
        args+=(-d "$data")
    fi

    curl "${args[@]}" "${CF_API}${endpoint}"
}

# Print formatted output
print_success() { echo -e "${GREEN}✓${NC} $1"; }
print_error() { echo -e "${RED}✗${NC} $1"; }
print_info() { echo -e "${BLUE}ℹ${NC} $1"; }
print_warn() { echo -e "${YELLOW}⚠${NC} $1"; }

# Verify API token
cmd_verify_token() {
    check_token
    echo "Verifying API token..."

    result=$(cf_api GET "/user/tokens/verify")

    if echo "$result" | jq -e '.success == true' > /dev/null 2>&1; then
        print_success "Token is valid"
        echo "$result" | jq -r '.result | "  Status: \(.status)\n  Expires: \(.expires_on // "Never")"'
    else
        print_error "Token verification failed"
        echo "$result" | jq -r '.errors[] | "  Error: \(.message)"'
        exit 1
    fi
}

# List all zones
cmd_list_zones() {
    check_token
    echo "Listing zones..."

    cf_api GET "/zones?per_page=50" | jq -r '.result[] | "\(.name)\t\(.id)\t\(.status)"' | \
        column -t -s $'\t' -N "ZONE,ID,STATUS"
}

# List DNS records
cmd_list_records() {
    check_token
    local zone_id="${1:-${CF_ZONE_ID:-}}"

    if [[ -z "$zone_id" ]]; then
        echo -e "${RED}Error: Zone ID required${NC}"
        echo "Usage: $0 list-records <zone_id>"
        echo "  Or set CF_ZONE_ID environment variable"
        exit 1
    fi

    echo "Listing DNS records for zone: $zone_id"

    cf_api GET "/zones/$zone_id/dns_records?per_page=5000" | \
        jq -r '.result[] | "\(.type)\t\(.name)\t\(.content)\t\(.proxied)\t\(.ttl)"' | \
        column -t -s $'\t' -N "TYPE,NAME,CONTENT,PROXIED,TTL"
}

# Get specific record
cmd_get_record() {
    check_token
    local zone_id="${1:-}"
    local name="${2:-}"

    if [[ -z "$zone_id" || -z "$name" ]]; then
        echo -e "${RED}Error: Zone ID and record name required${NC}"
        echo "Usage: $0 get-record <zone_id> <name>"
        exit 1
    fi

    cf_api GET "/zones/$zone_id/dns_records?name=$name" | jq '.result[]'
}

# Create A record
cmd_create_a() {
    check_token
    local zone_id="${1:-}"
    local name="${2:-}"
    local ip="${3:-}"
    local proxied="${4:-true}"

    if [[ -z "$zone_id" || -z "$name" || -z "$ip" ]]; then
        echo -e "${RED}Error: Zone ID, name, and IP required${NC}"
        echo "Usage: $0 create-a <zone_id> <name> <ip> [proxied]"
        exit 1
    fi

    echo "Creating A record: $name -> $ip (proxied: $proxied)"

    result=$(cf_api POST "/zones/$zone_id/dns_records" "{
        \"type\": \"A\",
        \"name\": \"$name\",
        \"content\": \"$ip\",
        \"ttl\": 1,
        \"proxied\": $proxied
    }")

    if echo "$result" | jq -e '.success == true' > /dev/null 2>&1; then
        print_success "A record created"
        echo "$result" | jq -r '.result | "  ID: \(.id)\n  Name: \(.name)\n  Content: \(.content)"'
    else
        print_error "Failed to create record"
        echo "$result" | jq -r '.errors[] | "  Error: \(.message)"'
        exit 1
    fi
}

# Create CNAME record
cmd_create_cname() {
    check_token
    local zone_id="${1:-}"
    local name="${2:-}"
    local target="${3:-}"
    local proxied="${4:-true}"

    if [[ -z "$zone_id" || -z "$name" || -z "$target" ]]; then
        echo -e "${RED}Error: Zone ID, name, and target required${NC}"
        echo "Usage: $0 create-cname <zone_id> <name> <target> [proxied]"
        exit 1
    fi

    echo "Creating CNAME record: $name -> $target (proxied: $proxied)"

    result=$(cf_api POST "/zones/$zone_id/dns_records" "{
        \"type\": \"CNAME\",
        \"name\": \"$name\",
        \"content\": \"$target\",
        \"ttl\": 1,
        \"proxied\": $proxied
    }")

    if echo "$result" | jq -e '.success == true' > /dev/null 2>&1; then
        print_success "CNAME record created"
        echo "$result" | jq -r '.result | "  ID: \(.id)\n  Name: \(.name)\n  Content: \(.content)"'
    else
        print_error "Failed to create record"
        echo "$result" | jq -r '.errors[] | "  Error: \(.message)"'
        exit 1
    fi
}

# Delete record
cmd_delete_record() {
    check_token
    local zone_id="${1:-}"
    local record_id="${2:-}"

    if [[ -z "$zone_id" || -z "$record_id" ]]; then
        echo -e "${RED}Error: Zone ID and record ID required${NC}"
        echo "Usage: $0 delete-record <zone_id> <record_id>"
        exit 1
    fi

    echo "Deleting record: $record_id"

    result=$(cf_api DELETE "/zones/$zone_id/dns_records/$record_id")

    if echo "$result" | jq -e '.success == true' > /dev/null 2>&1; then
        print_success "Record deleted"
    else
        print_error "Failed to delete record"
        echo "$result" | jq -r '.errors[] | "  Error: \(.message)"'
        exit 1
    fi
}

# Export zone
cmd_export() {
    check_token
    local zone_id="${1:-${CF_ZONE_ID:-}}"

    if [[ -z "$zone_id" ]]; then
        echo -e "${RED}Error: Zone ID required${NC}"
        echo "Usage: $0 export <zone_id>"
        exit 1
    fi

    local filename="zone-export-$(date +%Y%m%d-%H%M%S).txt"
    echo "Exporting zone $zone_id to $filename..."

    cf_api GET "/zones/$zone_id/dns_records/export" > "$filename"

    if [[ -s "$filename" ]]; then
        print_success "Zone exported to $filename"
        echo "  Records: $(grep -c '^[^;]' "$filename" || echo 0)"
    else
        print_error "Export failed or zone is empty"
        exit 1
    fi
}

# Check External-DNS in Kubernetes
cmd_check_external_dns() {
    echo "Checking External-DNS status..."

    # Check pods
    echo -e "\n${BLUE}Pods:${NC}"
    kubectl get pods -n external-dns -o wide 2>/dev/null || print_warn "Cannot access external-dns namespace"

    # Check recent logs
    echo -e "\n${BLUE}Recent logs:${NC}"
    kubectl logs -n external-dns deployment/external-dns --tail=20 2>/dev/null || print_warn "Cannot access logs"

    # Check for errors
    echo -e "\n${BLUE}Errors (last 100 lines):${NC}"
    kubectl logs -n external-dns deployment/external-dns --tail=100 2>/dev/null | grep -i error || print_success "No errors found"
}

# DNS verification
cmd_verify_dns() {
    local hostname="${1:-}"

    if [[ -z "$hostname" ]]; then
        echo -e "${RED}Error: Hostname required${NC}"
        echo "Usage: $0 verify-dns <hostname>"
        exit 1
    fi

    echo "Verifying DNS for: $hostname"

    echo -e "\n${BLUE}A Record (via Cloudflare 1.1.1.1):${NC}"
    dig @1.1.1.1 "$hostname" A +short

    echo -e "\n${BLUE}AAAA Record:${NC}"
    dig @1.1.1.1 "$hostname" AAAA +short

    echo -e "\n${BLUE}TXT Ownership Record:${NC}"
    dig @1.1.1.1 "_externaldns.$hostname" TXT +short

    echo -e "\n${BLUE}Proxy Status:${NC}"
    ip=$(dig +short "$hostname" | head -1)
    if [[ "$ip" =~ ^104\.|^172\.64\.|^141\.101\. ]]; then
        print_success "Proxied through Cloudflare (IP: $ip)"
    else
        print_info "DNS-only / Direct (IP: $ip)"
    fi
}

# Show help
cmd_help() {
    cat << 'EOF'
Cloudflare DNS Management Script

Usage:
  ./cloudflare-dns.sh <command> [arguments]

Commands:
  verify-token                         Verify API token validity
  list-zones                           List all zones
  list-records [zone_id]               List DNS records
  get-record <zone_id> <name>          Get specific record
  create-a <zone_id> <name> <ip> [proxied]        Create A record
  create-cname <zone_id> <name> <target> [proxied] Create CNAME
  delete-record <zone_id> <record_id>  Delete record
  export <zone_id>                     Export zone to BIND format
  check-external-dns                   Check External-DNS in Kubernetes
  verify-dns <hostname>                Verify DNS resolution

Environment Variables:
  CF_API_TOKEN  Cloudflare API Token (required)
  CF_ZONE_ID    Default zone ID (optional)

Examples:
  # Set up environment
  export CF_API_TOKEN='your-token-here'
  export CF_ZONE_ID='your-zone-id'

  # Verify token
  ./cloudflare-dns.sh verify-token

  # List zones
  ./cloudflare-dns.sh list-zones

  # List records
  ./cloudflare-dns.sh list-records

  # Create proxied A record
  ./cloudflare-dns.sh create-a $CF_ZONE_ID app 20.185.100.50 true

  # Create DNS-only A record (for mail)
  ./cloudflare-dns.sh create-a $CF_ZONE_ID mail 20.185.100.51 false

  # Verify DNS
  ./cloudflare-dns.sh verify-dns app.example.com
EOF
}

# Main
main() {
    local command="${1:-help}"
    shift || true

    case "$command" in
        verify-token)      cmd_verify_token "$@" ;;
        list-zones)        cmd_list_zones "$@" ;;
        list-records)      cmd_list_records "$@" ;;
        get-record)        cmd_get_record "$@" ;;
        create-a)          cmd_create_a "$@" ;;
        create-cname)      cmd_create_cname "$@" ;;
        delete-record)     cmd_delete_record "$@" ;;
        export)            cmd_export "$@" ;;
        check-external-dns) cmd_check_external_dns "$@" ;;
        verify-dns)        cmd_verify_dns "$@" ;;
        help|--help|-h)    cmd_help ;;
        *)
            echo -e "${RED}Unknown command: $command${NC}"
            echo "Run '$0 help' for usage"
            exit 1
            ;;
    esac
}

main "$@"
