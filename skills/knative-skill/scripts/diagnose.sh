#!/bin/bash
# Knative Diagnostics Script
# Usage: ./diagnose.sh [cluster-name] [component]
# Components: serving, eventing, all (default)

set -euo pipefail

CLUSTER="${1:-}"
COMPONENT="${2:-all}"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_header() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_section() {
    echo -e "\n${YELLOW}▶ $1${NC}"
}

print_ok() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Set kubeconfig if cluster specified
if [[ -n "$CLUSTER" ]]; then
    KUBECONFIG_PATH="$HOME/.kube/aks-rg-hypera-${CLUSTER}-config"
    if [[ -f "$KUBECONFIG_PATH" ]]; then
        export KUBECONFIG="$KUBECONFIG_PATH"
        print_ok "Using kubeconfig: $KUBECONFIG_PATH"
    else
        print_error "Kubeconfig not found: $KUBECONFIG_PATH"
        exit 1
    fi
fi

print_header "Knative Diagnostics"
echo "Cluster: ${CLUSTER:-current-context}"
echo "Component: $COMPONENT"
echo "Time: $(date)"

# Check Knative installation
check_installation() {
    print_section "Checking Knative Installation"

    # Check namespaces
    if kubectl get namespace knative-serving &>/dev/null; then
        print_ok "knative-serving namespace exists"
    else
        print_error "knative-serving namespace not found"
    fi

    if kubectl get namespace knative-eventing &>/dev/null; then
        print_ok "knative-eventing namespace exists"
    else
        print_warn "knative-eventing namespace not found (optional)"
    fi

    # Check CRDs
    print_section "Checking CRDs"

    SERVING_CRDS=("services.serving.knative.dev" "routes.serving.knative.dev" "configurations.serving.knative.dev" "revisions.serving.knative.dev")
    EVENTING_CRDS=("brokers.eventing.knative.dev" "triggers.eventing.knative.dev" "channels.messaging.knative.dev")

    for crd in "${SERVING_CRDS[@]}"; do
        if kubectl get crd "$crd" &>/dev/null; then
            print_ok "$crd"
        else
            print_error "$crd not found"
        fi
    done

    for crd in "${EVENTING_CRDS[@]}"; do
        if kubectl get crd "$crd" &>/dev/null; then
            print_ok "$crd"
        else
            print_warn "$crd not found (eventing)"
        fi
    done
}

# Check Serving components
check_serving() {
    print_section "Checking Knative Serving Components"

    # Controller
    echo -e "\n${YELLOW}Controller:${NC}"
    kubectl get pods -n knative-serving -l app=controller --no-headers 2>/dev/null | while read -r line; do
        pod_name=$(echo "$line" | awk '{print $1}')
        status=$(echo "$line" | awk '{print $3}')
        restarts=$(echo "$line" | awk '{print $4}')
        if [[ "$status" == "Running" && "$restarts" -lt 5 ]]; then
            print_ok "$pod_name ($status, restarts: $restarts)"
        else
            print_error "$pod_name ($status, restarts: $restarts)"
        fi
    done

    # Activator
    echo -e "\n${YELLOW}Activator:${NC}"
    kubectl get pods -n knative-serving -l app=activator --no-headers 2>/dev/null | while read -r line; do
        pod_name=$(echo "$line" | awk '{print $1}')
        status=$(echo "$line" | awk '{print $3}')
        print_ok "$pod_name ($status)"
    done

    # Autoscaler
    echo -e "\n${YELLOW}Autoscaler:${NC}"
    kubectl get pods -n knative-serving -l app=autoscaler --no-headers 2>/dev/null | while read -r line; do
        pod_name=$(echo "$line" | awk '{print $1}')
        status=$(echo "$line" | awk '{print $3}')
        print_ok "$pod_name ($status)"
    done

    # Webhook
    echo -e "\n${YELLOW}Webhook:${NC}"
    kubectl get pods -n knative-serving -l app=webhook --no-headers 2>/dev/null | while read -r line; do
        pod_name=$(echo "$line" | awk '{print $1}')
        status=$(echo "$line" | awk '{print $3}')
        print_ok "$pod_name ($status)"
    done
}

# Check networking layer
check_networking() {
    print_section "Checking Networking Layer"

    # Detect networking layer
    if kubectl get namespace kourier-system &>/dev/null; then
        print_ok "Kourier detected"
        echo -e "\n${YELLOW}Kourier Pods:${NC}"
        kubectl get pods -n kourier-system --no-headers 2>/dev/null

        echo -e "\n${YELLOW}Kourier Service:${NC}"
        kubectl get svc -n kourier-system kourier --no-headers 2>/dev/null || print_warn "Kourier service not found"
    elif kubectl get namespace istio-system &>/dev/null; then
        print_ok "Istio detected"
        echo -e "\n${YELLOW}Istio Ingress:${NC}"
        kubectl get pods -n istio-system -l app=istio-ingressgateway --no-headers 2>/dev/null
    else
        print_warn "No networking layer detected (Kourier/Istio)"
    fi

    # Check config-network
    echo -e "\n${YELLOW}Network Configuration:${NC}"
    kubectl get configmap config-network -n knative-serving -o jsonpath='{.data.ingress-class}' 2>/dev/null && echo ""
}

# Check Eventing components
check_eventing() {
    print_section "Checking Knative Eventing Components"

    if ! kubectl get namespace knative-eventing &>/dev/null; then
        print_warn "Knative Eventing not installed"
        return
    fi

    # Controller
    echo -e "\n${YELLOW}Eventing Controller:${NC}"
    kubectl get pods -n knative-eventing -l app=eventing-controller --no-headers 2>/dev/null | while read -r line; do
        pod_name=$(echo "$line" | awk '{print $1}')
        status=$(echo "$line" | awk '{print $3}')
        print_ok "$pod_name ($status)"
    done

    # Webhook
    echo -e "\n${YELLOW}Eventing Webhook:${NC}"
    kubectl get pods -n knative-eventing -l app=eventing-webhook --no-headers 2>/dev/null | while read -r line; do
        pod_name=$(echo "$line" | awk '{print $1}')
        status=$(echo "$line" | awk '{print $3}')
        print_ok "$pod_name ($status)"
    done

    # Brokers
    echo -e "\n${YELLOW}Brokers:${NC}"
    kubectl get brokers -A --no-headers 2>/dev/null || print_warn "No brokers found"

    # Triggers
    echo -e "\n${YELLOW}Triggers:${NC}"
    kubectl get triggers -A --no-headers 2>/dev/null || print_warn "No triggers found"
}

# Check Services
check_services() {
    print_section "Knative Services Status"

    echo -e "\n${YELLOW}All Knative Services:${NC}"
    kubectl get ksvc -A 2>/dev/null || print_warn "No Knative services found"

    echo -e "\n${YELLOW}Service Details:${NC}"
    kubectl get ksvc -A -o custom-columns="NAMESPACE:.metadata.namespace,NAME:.metadata.name,URL:.status.url,READY:.status.conditions[?(@.type=='Ready')].status,REASON:.status.conditions[?(@.type=='Ready')].reason" 2>/dev/null
}

# Check Revisions
check_revisions() {
    print_section "Revisions Status"

    echo -e "\n${YELLOW}All Revisions:${NC}"
    kubectl get revisions -A -o custom-columns="NAMESPACE:.metadata.namespace,NAME:.metadata.name,SERVICE:.metadata.labels['serving\.knative\.dev/service'],READY:.status.conditions[?(@.type=='Ready')].status,REASON:.status.conditions[?(@.type=='Ready')].reason" 2>/dev/null
}

# Check domain configuration
check_domain() {
    print_section "Domain Configuration"

    echo -e "\n${YELLOW}config-domain:${NC}"
    kubectl get configmap config-domain -n knative-serving -o yaml 2>/dev/null | grep -A 20 "^data:" || print_warn "config-domain not found"
}

# Check recent events
check_events() {
    print_section "Recent Events (last 10)"

    echo -e "\n${YELLOW}Knative Serving Events:${NC}"
    kubectl get events -n knative-serving --sort-by='.lastTimestamp' 2>/dev/null | tail -10

    if kubectl get namespace knative-eventing &>/dev/null; then
        echo -e "\n${YELLOW}Knative Eventing Events:${NC}"
        kubectl get events -n knative-eventing --sort-by='.lastTimestamp' 2>/dev/null | tail -10
    fi
}

# Main execution
case "$COMPONENT" in
    serving)
        check_installation
        check_serving
        check_networking
        check_services
        check_revisions
        check_domain
        check_events
        ;;
    eventing)
        check_installation
        check_eventing
        check_events
        ;;
    all)
        check_installation
        check_serving
        check_networking
        check_eventing
        check_services
        check_revisions
        check_domain
        check_events
        ;;
    *)
        echo "Usage: $0 [cluster-name] [serving|eventing|all]"
        exit 1
        ;;
esac

print_header "Diagnostics Complete"
