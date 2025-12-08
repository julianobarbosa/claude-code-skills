#!/usr/bin/env bash
#
# sync-check.sh
# Verify External Secrets Operator synchronization with 1Password
#
# Usage:
#   ./sync-check.sh [namespace]
#
# Arguments:
#   namespace - Kubernetes namespace to check (default: all namespaces)
#
# Requirements:
#   - kubectl configured with cluster access
#   - External Secrets Operator installed
#   - 1Password Connect Server running
#

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Print functions
info() { echo -e "${BLUE}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[OK]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }
header() { echo -e "\n${CYAN}=== $1 ===${NC}\n"; }

# Check if kubectl is available
check_kubectl() {
    if ! command -v kubectl &> /dev/null; then
        error "kubectl is not installed or not in PATH"
        exit 1
    fi

    if ! kubectl cluster-info &> /dev/null; then
        error "Cannot connect to Kubernetes cluster"
        exit 1
    fi

    local context
    context=$(kubectl config current-context)
    info "Connected to cluster: $context"
}

# Check SecretStore status
check_secret_stores() {
    header "SecretStore Status"

    local stores
    stores=$(kubectl get secretstore,clustersecretstore -A -o json 2>/dev/null || echo '{"items":[]}')

    local count
    count=$(echo "$stores" | jq '.items | length')

    if [[ "$count" -eq 0 ]]; then
        warn "No SecretStores found"
        return
    fi

    echo "$stores" | jq -r '.items[] | [
        .kind,
        .metadata.namespace // "cluster-scoped",
        .metadata.name,
        (.status.conditions[]? | select(.type=="Ready") | .status) // "Unknown"
    ] | @tsv' | while IFS=$'\t' read -r kind namespace name ready; do
        if [[ "$ready" == "True" ]]; then
            success "$kind/$name (ns: $namespace) - Ready"
        else
            error "$kind/$name (ns: $namespace) - Not Ready"
        fi
    done
}

# Check ExternalSecret status
check_external_secrets() {
    local namespace="$1"
    header "ExternalSecret Status"

    local ns_flag=""
    if [[ -n "$namespace" ]]; then
        ns_flag="-n $namespace"
    else
        ns_flag="-A"
    fi

    local secrets
    secrets=$(kubectl get externalsecret $ns_flag -o json 2>/dev/null || echo '{"items":[]}')

    local count
    count=$(echo "$secrets" | jq '.items | length')

    if [[ "$count" -eq 0 ]]; then
        warn "No ExternalSecrets found"
        return
    fi

    info "Found $count ExternalSecret(s)"
    echo ""

    local synced=0
    local failed=0
    local pending=0

    echo "$secrets" | jq -r '.items[] | [
        .metadata.namespace,
        .metadata.name,
        (.status.conditions[]? | select(.type=="Ready") | .status) // "Unknown",
        (.status.conditions[]? | select(.type=="Ready") | .message) // "N/A",
        .status.refreshTime // "Never"
    ] | @tsv' | while IFS=$'\t' read -r ns name ready message refresh; do
        local status_icon
        case "$ready" in
            "True")
                status_icon="${GREEN}✓${NC}"
                ((synced++)) || true
                ;;
            "False")
                status_icon="${RED}✗${NC}"
                ((failed++)) || true
                ;;
            *)
                status_icon="${YELLOW}?${NC}"
                ((pending++)) || true
                ;;
        esac

        echo -e "$status_icon $ns/$name"
        echo "    Status: $ready"
        echo "    Message: $message"
        echo "    Last Refresh: $refresh"
        echo ""
    done

    echo "---"
    echo "Summary:"
    kubectl get externalsecret $ns_flag -o json | jq -r '
        .items |
        group_by(.status.conditions[]? | select(.type=="Ready") | .status) |
        map({
            status: (.[0].status.conditions[]? | select(.type=="Ready") | .status) // "Unknown",
            count: length
        }) |
        .[] |
        "  \(.status): \(.count)"
    '
}

# Check 1Password Connect Server
check_connect_server() {
    header "1Password Connect Server"

    # Try to find Connect Server deployment
    local connect_deploy
    connect_deploy=$(kubectl get deploy -A -l app=onepassword-connect -o json 2>/dev/null || echo '{"items":[]}')

    local count
    count=$(echo "$connect_deploy" | jq '.items | length')

    if [[ "$count" -eq 0 ]]; then
        # Try alternative label
        connect_deploy=$(kubectl get deploy -A -o json 2>/dev/null | jq '[.items[] | select(.metadata.name | contains("onepassword") or contains("1password"))]' || echo '[]')
        count=$(echo "$connect_deploy" | jq 'length')
    fi

    if [[ "$count" -eq 0 ]]; then
        warn "1Password Connect Server not found"
        info "Looking for any 1Password related pods..."
        kubectl get pods -A | grep -i "password\|1password\|onepassword" || warn "No 1Password pods found"
        return
    fi

    echo "$connect_deploy" | jq -r '.[] // .items[] | [
        .metadata.namespace,
        .metadata.name,
        "\(.status.readyReplicas // 0)/\(.spec.replicas)"
    ] | @tsv' | while IFS=$'\t' read -r ns name replicas; do
        local ready
        ready=$(echo "$replicas" | cut -d'/' -f1)
        local desired
        desired=$(echo "$replicas" | cut -d'/' -f2)

        if [[ "$ready" -eq "$desired" && "$ready" -gt 0 ]]; then
            success "Deployment $ns/$name ($replicas replicas)"
        else
            error "Deployment $ns/$name ($replicas replicas) - Not healthy"
        fi
    done

    # Check pods
    info "Connect Server Pods:"
    kubectl get pods -A -l app=onepassword-connect 2>/dev/null || \
    kubectl get pods -A | grep -i "onepassword-connect\|1password-connect" || \
    warn "No Connect Server pods found"
}

# Check for sync errors
check_sync_errors() {
    local namespace="$1"
    header "Sync Errors"

    local ns_flag=""
    if [[ -n "$namespace" ]]; then
        ns_flag="-n $namespace"
    else
        ns_flag="-A"
    fi

    local errors
    errors=$(kubectl get externalsecret $ns_flag -o json 2>/dev/null | jq -r '
        .items[] |
        select(.status.conditions[]? | select(.type=="Ready" and .status=="False")) |
        {
            namespace: .metadata.namespace,
            name: .metadata.name,
            message: (.status.conditions[] | select(.type=="Ready") | .message)
        }
    ')

    if [[ -z "$errors" || "$errors" == "null" ]]; then
        success "No sync errors found"
        return
    fi

    error "Found sync errors:"
    echo "$errors" | jq -r '"  \(.namespace)/\(.name): \(.message)"'
}

# Check recent events
check_events() {
    local namespace="$1"
    header "Recent Events"

    local ns_flag=""
    if [[ -n "$namespace" ]]; then
        ns_flag="-n $namespace"
    else
        ns_flag="-A"
    fi

    info "External Secrets related events (last 10):"
    kubectl get events $ns_flag --sort-by='.lastTimestamp' -o json 2>/dev/null | jq -r '
        [.items[] | select(.involvedObject.kind == "ExternalSecret" or .involvedObject.kind == "SecretStore" or .involvedObject.kind == "ClusterSecretStore")] |
        reverse |
        .[:10] |
        .[] |
        "\(.lastTimestamp) [\(.type)] \(.involvedObject.kind)/\(.involvedObject.name): \(.message)"
    ' || warn "Could not fetch events"
}

# Health check summary
print_summary() {
    header "Health Check Summary"

    local checks_passed=0
    local checks_failed=0

    # Check SecretStores
    local store_status
    store_status=$(kubectl get secretstore,clustersecretstore -A -o json 2>/dev/null | jq -r '
        [.items[].status.conditions[]? | select(.type=="Ready" and .status=="True")] | length
    ')
    local store_total
    store_total=$(kubectl get secretstore,clustersecretstore -A -o json 2>/dev/null | jq '.items | length')

    if [[ "$store_status" -eq "$store_total" && "$store_total" -gt 0 ]]; then
        success "SecretStores: $store_status/$store_total ready"
        ((checks_passed++))
    else
        error "SecretStores: $store_status/$store_total ready"
        ((checks_failed++))
    fi

    # Check ExternalSecrets
    local es_ready
    es_ready=$(kubectl get externalsecret -A -o json 2>/dev/null | jq -r '
        [.items[].status.conditions[]? | select(.type=="Ready" and .status=="True")] | length
    ')
    local es_total
    es_total=$(kubectl get externalsecret -A -o json 2>/dev/null | jq '.items | length')

    if [[ "$es_ready" -eq "$es_total" && "$es_total" -gt 0 ]]; then
        success "ExternalSecrets: $es_ready/$es_total synced"
        ((checks_passed++))
    elif [[ "$es_total" -eq 0 ]]; then
        warn "ExternalSecrets: None found"
    else
        error "ExternalSecrets: $es_ready/$es_total synced"
        ((checks_failed++))
    fi

    echo ""
    if [[ "$checks_failed" -eq 0 ]]; then
        success "All checks passed!"
    else
        error "$checks_failed check(s) failed"
        exit 1
    fi
}

# Show usage
usage() {
    echo "Usage: $0 [namespace]"
    echo ""
    echo "Verify External Secrets Operator synchronization with 1Password"
    echo ""
    echo "Arguments:"
    echo "  namespace - Kubernetes namespace to check (default: all namespaces)"
    echo ""
    echo "Examples:"
    echo "  $0                    # Check all namespaces"
    echo "  $0 production         # Check only production namespace"
    exit 0
}

# Main
main() {
    local namespace=""

    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                usage
                ;;
            *)
                namespace="$1"
                shift
                ;;
        esac
    done

    echo ""
    echo "1Password External Secrets Sync Check"
    echo "======================================"

    check_kubectl

    if [[ -n "$namespace" ]]; then
        info "Checking namespace: $namespace"
    else
        info "Checking all namespaces"
    fi

    check_secret_stores
    check_connect_server
    check_external_secrets "$namespace"
    check_sync_errors "$namespace"
    check_events "$namespace"
    print_summary
}

main "$@"
