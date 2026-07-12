#!/usr/bin/env bash
#
# GitOps Health Check Script
# Validates GitOps setup and checks for common issues
#
# Usage:
#   ./gitops-health-check.sh                    # Full check
#   ./gitops-health-check.sh --argocd           # ArgoCD only
#   ./gitops-health-check.sh --flux             # Flux only
#   ./gitops-health-check.sh --manifests ./path # Validate manifests
#
# Requirements:
#   - kubectl configured with cluster access
#   - argocd CLI (for ArgoCD checks)
#   - flux CLI (for Flux checks)
#   - kustomize (for manifest validation)
#   - helm (for chart validation)

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0
WARNINGS=0

# Functions
print_header() {
    echo -e "\n${BLUE}═══════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════════${NC}\n"
}

print_check() {
    echo -ne "  Checking: $1... "
}

pass() {
    echo -e "${GREEN}✓ PASS${NC}"
    ((PASSED++))
}

fail() {
    echo -e "${RED}✗ FAIL${NC}"
    echo -e "    ${RED}→ $1${NC}"
    ((FAILED++))
}

warn() {
    echo -e "${YELLOW}⚠ WARN${NC}"
    echo -e "    ${YELLOW}→ $1${NC}"
    ((WARNINGS++))
}

skip() {
    echo -e "${YELLOW}○ SKIP${NC}"
    echo -e "    ${YELLOW}→ $1${NC}"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# ============================================
# KUBECTL / CLUSTER CHECKS
# ============================================

check_cluster_connectivity() {
    print_header "CLUSTER CONNECTIVITY"

    print_check "kubectl available"
    if command_exists kubectl; then
        pass
    else
        fail "kubectl not found in PATH"
        return 1
    fi

    print_check "Cluster connection"
    if kubectl cluster-info >/dev/null 2>&1; then
        pass
        CLUSTER_CONTEXT=$(kubectl config current-context)
        echo -e "    ${BLUE}→ Context: ${CLUSTER_CONTEXT}${NC}"
    else
        fail "Cannot connect to cluster"
        return 1
    fi

    print_check "Cluster version"
    if VERSION=$(kubectl version --short 2>/dev/null | grep "Server" | awk '{print $3}'); then
        pass
        echo -e "    ${BLUE}→ Server: ${VERSION}${NC}"
    else
        warn "Could not determine cluster version"
    fi
}

# ============================================
# ARGOCD CHECKS
# ============================================

check_argocd() {
    print_header "ARGOCD HEALTH"

    # Check if ArgoCD is installed
    print_check "ArgoCD namespace exists"
    if kubectl get namespace argocd >/dev/null 2>&1; then
        pass
    else
        skip "ArgoCD not installed"
        return 0
    fi

    # Check ArgoCD pods
    print_check "ArgoCD pods running"
    NOT_RUNNING=$(kubectl get pods -n argocd -o jsonpath='{.items[?(@.status.phase!="Running")].metadata.name}' 2>/dev/null)
    if [ -z "$NOT_RUNNING" ]; then
        pass
    else
        fail "Pods not running: $NOT_RUNNING"
    fi

    # Check ArgoCD CLI
    print_check "ArgoCD CLI available"
    if command_exists argocd; then
        pass
        ARGOCD_VERSION=$(argocd version --client --short 2>/dev/null || echo "unknown")
        echo -e "    ${BLUE}→ CLI Version: ${ARGOCD_VERSION}${NC}"
    else
        warn "argocd CLI not installed"
    fi

    # Check ArgoCD server version
    print_check "ArgoCD server version"
    if SERVER_VERSION=$(kubectl get deployment argocd-server -n argocd -o jsonpath='{.spec.template.spec.containers[0].image}' 2>/dev/null); then
        pass
        echo -e "    ${BLUE}→ Server: ${SERVER_VERSION}${NC}"
    else
        warn "Could not determine server version"
    fi

    # Check Applications status
    print_check "Application health"
    if command_exists argocd && argocd app list >/dev/null 2>&1; then
        DEGRADED=$(argocd app list -o json 2>/dev/null | jq -r '.[] | select(.status.health.status != "Healthy") | .metadata.name' 2>/dev/null || true)
        if [ -z "$DEGRADED" ]; then
            pass
            APP_COUNT=$(argocd app list -o json 2>/dev/null | jq length 2>/dev/null || echo "?")
            echo -e "    ${BLUE}→ All ${APP_COUNT} applications healthy${NC}"
        else
            warn "Degraded apps: $DEGRADED"
        fi
    else
        skip "Cannot check apps (not logged in or CLI unavailable)"
    fi

    # Check for OutOfSync applications
    print_check "Application sync status"
    if command_exists argocd && argocd app list >/dev/null 2>&1; then
        OUTOFSYNC=$(argocd app list -o json 2>/dev/null | jq -r '.[] | select(.status.sync.status != "Synced") | .metadata.name' 2>/dev/null || true)
        if [ -z "$OUTOFSYNC" ]; then
            pass
        else
            warn "OutOfSync apps: $OUTOFSYNC"
        fi
    else
        skip "Cannot check sync status"
    fi

    # Check repo server cache
    print_check "Repository server health"
    if kubectl exec -n argocd deploy/argocd-repo-server -- curl -s localhost:8084/healthz >/dev/null 2>&1; then
        pass
    else
        warn "Cannot verify repo-server health"
    fi
}

# ============================================
# FLUX CHECKS
# ============================================

check_flux() {
    print_header "FLUX HEALTH"

    # Check if Flux is installed
    print_check "Flux namespace exists"
    if kubectl get namespace flux-system >/dev/null 2>&1; then
        pass
    else
        skip "Flux not installed"
        return 0
    fi

    # Check Flux CLI
    print_check "Flux CLI available"
    if command_exists flux; then
        pass
        FLUX_VERSION=$(flux version --client 2>/dev/null | head -1 || echo "unknown")
        echo -e "    ${BLUE}→ CLI: ${FLUX_VERSION}${NC}"
    else
        warn "flux CLI not installed"
    fi

    # Check Flux components
    print_check "Flux controllers running"
    if command_exists flux; then
        FLUX_STATUS=$(flux check 2>&1 || true)
        if echo "$FLUX_STATUS" | grep -q "all checks passed"; then
            pass
        else
            warn "Some Flux checks failed"
            echo "$FLUX_STATUS" | head -5 | sed 's/^/    /'
        fi
    else
        # Fallback to kubectl check
        NOT_RUNNING=$(kubectl get pods -n flux-system -o jsonpath='{.items[?(@.status.phase!="Running")].metadata.name}' 2>/dev/null)
        if [ -z "$NOT_RUNNING" ]; then
            pass
        else
            fail "Pods not running: $NOT_RUNNING"
        fi
    fi

    # Check Kustomizations
    print_check "Kustomization reconciliation"
    if kubectl get kustomizations.kustomize.toolkit.fluxcd.io -A >/dev/null 2>&1; then
        FAILED_KS=$(kubectl get kustomizations.kustomize.toolkit.fluxcd.io -A -o json 2>/dev/null | \
            jq -r '.items[] | select(.status.conditions[-1].status != "True") | .metadata.namespace + "/" + .metadata.name' 2>/dev/null || true)
        if [ -z "$FAILED_KS" ]; then
            pass
        else
            warn "Failed Kustomizations: $FAILED_KS"
        fi
    else
        skip "No Kustomizations found"
    fi

    # Check Git sources
    print_check "Git sources ready"
    if kubectl get gitrepositories.source.toolkit.fluxcd.io -A >/dev/null 2>&1; then
        FAILED_GIT=$(kubectl get gitrepositories.source.toolkit.fluxcd.io -A -o json 2>/dev/null | \
            jq -r '.items[] | select(.status.conditions[-1].status != "True") | .metadata.namespace + "/" + .metadata.name' 2>/dev/null || true)
        if [ -z "$FAILED_GIT" ]; then
            pass
        else
            warn "Failed Git sources: $FAILED_GIT"
        fi
    else
        skip "No GitRepositories found"
    fi
}

# ============================================
# MANIFEST VALIDATION
# ============================================

validate_manifests() {
    local MANIFEST_PATH="${1:-.}"

    print_header "MANIFEST VALIDATION"

    print_check "Manifest path exists"
    if [ -d "$MANIFEST_PATH" ]; then
        pass
        echo -e "    ${BLUE}→ Path: ${MANIFEST_PATH}${NC}"
    else
        fail "Path does not exist: $MANIFEST_PATH"
        return 1
    fi

    # Check for kustomization.yaml
    print_check "Kustomize structure"
    if find "$MANIFEST_PATH" -name "kustomization.yaml" -o -name "kustomization.yml" | grep -q .; then
        pass
        KUSTOMIZE_COUNT=$(find "$MANIFEST_PATH" -name "kustomization.yaml" -o -name "kustomization.yml" | wc -l | tr -d ' ')
        echo -e "    ${BLUE}→ Found ${KUSTOMIZE_COUNT} kustomization files${NC}"
    else
        skip "No kustomization files found"
    fi

    # Validate kustomize build
    if command_exists kustomize; then
        print_check "Kustomize build validation"
        local BUILD_FAILED=false
        while IFS= read -r -d '' KS_FILE; do
            KS_DIR=$(dirname "$KS_FILE")
            if ! kustomize build "$KS_DIR" >/dev/null 2>&1; then
                fail "Kustomize build failed for: $KS_DIR"
                kustomize build "$KS_DIR" 2>&1 | head -5 | sed 's/^/    /'
                BUILD_FAILED=true
            fi
        done < <(find "$MANIFEST_PATH" \( -name "kustomization.yaml" -o -name "kustomization.yml" \) -print0 2>/dev/null)
        if [ "$BUILD_FAILED" = false ]; then
            pass
        fi
    else
        skip "kustomize CLI not installed"
    fi

    # Check for mutable image tags
    print_check "Image tag immutability"
    MUTABLE_TAGS=$(grep -rh "image:" "$MANIFEST_PATH" 2>/dev/null | grep -E ":(latest|dev|staging|master|main)$" || true)
    if [ -z "$MUTABLE_TAGS" ]; then
        pass
    else
        warn "Mutable image tags found"
        echo "$MUTABLE_TAGS" | head -3 | sed 's/^/    /'
    fi

    # Check for secrets in plain text
    print_check "No plaintext secrets"
    SECRETS_IN_GIT=$(grep -rl "kind: Secret" "$MANIFEST_PATH" 2>/dev/null | \
        xargs -I {} grep -l "^  [a-zA-Z]*:" {} 2>/dev/null | \
        grep -v "SealedSecret\|ExternalSecret" || true)
    if [ -z "$SECRETS_IN_GIT" ]; then
        pass
    else
        warn "Plain secrets found (use SealedSecrets or ExternalSecrets)"
        echo "$SECRETS_IN_GIT" | head -3 | sed 's/^/    /'
    fi

    # Validate Helm charts if present
    if command_exists helm; then
        print_check "Helm chart validation"
        CHARTS=$(find "$MANIFEST_PATH" -name "Chart.yaml" 2>/dev/null || true)
        if [ -n "$CHARTS" ]; then
            for CHART in $CHARTS; do
                CHART_DIR=$(dirname "$CHART")
                if helm lint "$CHART_DIR" >/dev/null 2>&1; then
                    : # success
                else
                    fail "Helm lint failed for: $CHART_DIR"
                fi
            done
            pass
        else
            skip "No Helm charts found"
        fi
    fi
}

# ============================================
# GITOPS BEST PRACTICES
# ============================================

check_best_practices() {
    print_header "GITOPS BEST PRACTICES"

    # Check for automated sync with self-heal
    print_check "Self-healing enabled"
    if command_exists argocd && argocd app list >/dev/null 2>&1; then
        NO_SELFHEAL=$(argocd app list -o json 2>/dev/null | \
            jq -r '.[] | select(.spec.syncPolicy.automated.selfHeal != true) | .metadata.name' 2>/dev/null || true)
        if [ -z "$NO_SELFHEAL" ]; then
            pass
        else
            warn "Apps without self-heal: $(echo "$NO_SELFHEAL" | wc -l | tr -d ' ')"
        fi
    else
        skip "Cannot check ArgoCD apps"
    fi

    # Check for prune enabled
    print_check "Prune enabled"
    if command_exists argocd && argocd app list >/dev/null 2>&1; then
        NO_PRUNE=$(argocd app list -o json 2>/dev/null | \
            jq -r '.[] | select(.spec.syncPolicy.automated.prune != true) | .metadata.name' 2>/dev/null || true)
        if [ -z "$NO_PRUNE" ]; then
            pass
        else
            warn "Apps without prune: $(echo "$NO_PRUNE" | wc -l | tr -d ' ')"
        fi
    else
        skip "Cannot check ArgoCD apps"
    fi

    # Check for sync windows in production
    print_check "Sync windows configured"
    if kubectl get appprojects.argoproj.io -n argocd -o json 2>/dev/null | jq -e '.items[] | select(.metadata.name == "production") | .spec.syncWindows' >/dev/null 2>&1; then
        pass
    else
        warn "No sync windows on production project"
    fi
}

# ============================================
# SUMMARY
# ============================================

print_summary() {
    print_header "SUMMARY"

    echo -e "  ${GREEN}Passed:${NC}   $PASSED"
    echo -e "  ${RED}Failed:${NC}   $FAILED"
    echo -e "  ${YELLOW}Warnings:${NC} $WARNINGS"
    echo ""

    if [ $FAILED -gt 0 ]; then
        echo -e "  ${RED}Status: UNHEALTHY - Fix failed checks above${NC}"
        exit 1
    elif [ $WARNINGS -gt 0 ]; then
        echo -e "  ${YELLOW}Status: WARNING - Review warnings above${NC}"
        exit 0
    else
        echo -e "  ${GREEN}Status: HEALTHY - All checks passed!${NC}"
        exit 0
    fi
}

# ============================================
# MAIN
# ============================================

main() {
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║              GitOps Health Check                              ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"

    case "${1:-all}" in
        --argocd)
            check_cluster_connectivity
            check_argocd
            ;;
        --flux)
            check_cluster_connectivity
            check_flux
            ;;
        --manifests)
            validate_manifests "${2:-.}"
            ;;
        --practices)
            check_cluster_connectivity
            check_best_practices
            ;;
        all|*)
            check_cluster_connectivity
            check_argocd
            check_flux
            check_best_practices
            ;;
    esac

    print_summary
}

main "$@"
