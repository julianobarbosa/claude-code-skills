#!/bin/bash
# check-urls.sh - Health check script for Hypera infrastructure URLs
# Usage: ./check-urls.sh [environment] [--verbose]
#
# Examples:
#   ./check-urls.sh              # Check all URLs
#   ./check-urls.sh hub          # Check hub environment only
#   ./check-urls.sh dev          # Check development environment
#   ./check-urls.sh prd          # Check production environment
#   ./check-urls.sh --verbose    # Verbose output with response times

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
TIMEOUT=10
VERBOSE=false
ENVIRONMENT="all"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        hub|dev|prd|all)
            ENVIRONMENT="$1"
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [environment] [--verbose]"
            echo ""
            echo "Environments: hub, dev, prd, all (default)"
            echo "Options:"
            echo "  --verbose, -v    Show response times and headers"
            echo "  --help, -h       Show this help"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# URL definitions by environment
declare -A HUB_URLS=(
    ["ArgoCD"]="https://argocd.cafehyna.com.br"
    ["Sentry Hub"]="https://sentry-hub.cafehyna.hypera.com.br"
    ["SonarQube Hub"]="https://sonarqube-hub.cafehyna.com.br"
    ["phpMyAdmin Hub"]="https://dba.cafehyna.com.br"
    ["Adminer Hub"]="https://dba2.cafehyna.com.br"
    ["Mimir Hub"]="https://mimir-hub.cafehyna.com.br"
)

declare -A DEV_URLS=(
    ["Sentry Dev"]="https://sentry.adocyl.com.br"
    ["SonarQube Dev"]="https://sonarqube.hypera.com.br"
    ["Grafana OnCall Dev"]="https://oncall-dev.cafehyna.com"
    ["phpMyAdmin Dev"]="https://dev-dba.cafehyna.com.br"
    ["RabbitMQ PainelClientes Dev"]="https://rabbitmq-painelclientes-dev.cafehyna.com.br"
)

declare -A PRD_URLS=(
    ["Sentry Prd"]="https://sentry.cafehyna.hypera.com.br"
)

# Function to check a single URL
check_url() {
    local name="$1"
    local url="$2"
    local start_time
    local end_time
    local duration
    local http_code
    local result

    start_time=$(date +%s%N)

    # Make the request
    http_code=$(curl -sI "$url" -o /dev/null -w "%{http_code}" --connect-timeout "$TIMEOUT" 2>/dev/null || echo "000")

    end_time=$(date +%s%N)
    duration=$(( (end_time - start_time) / 1000000 ))

    # Determine status
    if [[ "$http_code" == "000" ]]; then
        result="${RED}TIMEOUT${NC}"
    elif [[ "$http_code" =~ ^2 ]] || [[ "$http_code" == "301" ]] || [[ "$http_code" == "302" ]]; then
        result="${GREEN}OK${NC} ($http_code)"
    elif [[ "$http_code" =~ ^4 ]]; then
        result="${YELLOW}WARN${NC} ($http_code)"
    else
        result="${RED}FAIL${NC} ($http_code)"
    fi

    # Output
    if [[ "$VERBOSE" == "true" ]]; then
        printf "  %-30s %s - %dms\n" "$name" "$result" "$duration"
        printf "    ${BLUE}%s${NC}\n" "$url"
    else
        printf "  %-30s %s\n" "$name" "$result"
    fi
}

# Function to check URLs for an environment
check_environment() {
    local env_name="$1"
    local -n urls="$2"

    echo -e "\n${BLUE}=== $env_name Environment ===${NC}"

    for name in "${!urls[@]}"; do
        check_url "$name" "${urls[$name]}"
    done
}

# Main execution
echo -e "${BLUE}Hypera Infrastructure URL Health Check${NC}"
echo "========================================"
echo "Timeout: ${TIMEOUT}s"
echo "Environment: $ENVIRONMENT"
echo ""

# Check based on environment selection
case $ENVIRONMENT in
    hub)
        check_environment "Hub" HUB_URLS
        ;;
    dev)
        check_environment "Development" DEV_URLS
        ;;
    prd)
        check_environment "Production" PRD_URLS
        ;;
    all)
        check_environment "Hub" HUB_URLS
        check_environment "Development" DEV_URLS
        check_environment "Production" PRD_URLS
        ;;
esac

echo ""
echo -e "${BLUE}Check completed at $(date '+%Y-%m-%d %H:%M:%S')${NC}"
