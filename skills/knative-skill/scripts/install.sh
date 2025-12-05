#!/bin/bash
# Knative Installation Script
# Usage: ./install.sh [cluster-name] [version] [networking-layer]
# Networking layers: kourier (default), istio, contour

set -euo pipefail

CLUSTER="${1:-}"
VERSION="${2:-v1.20.0}"
NETWORKING="${3:-kourier}"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "\n${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_step() {
    echo -e "\n${YELLOW}▶ $1${NC}"
}

print_ok() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
    exit 1
}

# Set kubeconfig if cluster specified
if [[ -n "$CLUSTER" ]]; then
    KUBECONFIG_PATH="$HOME/.kube/aks-rg-hypera-${CLUSTER}-config"
    if [[ -f "$KUBECONFIG_PATH" ]]; then
        export KUBECONFIG="$KUBECONFIG_PATH"
        print_ok "Using kubeconfig: $KUBECONFIG_PATH"
    else
        print_error "Kubeconfig not found: $KUBECONFIG_PATH"
    fi
fi

print_header "Knative Installation"
echo "Cluster: ${CLUSTER:-current-context}"
echo "Version: $VERSION"
echo "Networking: $NETWORKING"
echo ""

# Confirm installation
read -p "Proceed with installation? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Installation cancelled."
    exit 0
fi

# Install Knative Serving
print_step "Installing Knative Serving CRDs"
kubectl apply -f "https://github.com/knative/serving/releases/download/knative-${VERSION}/serving-crds.yaml"
print_ok "Serving CRDs installed"

print_step "Installing Knative Serving Core"
kubectl apply -f "https://github.com/knative/serving/releases/download/knative-${VERSION}/serving-core.yaml"
print_ok "Serving core installed"

# Wait for serving pods
print_step "Waiting for Serving pods to be ready"
kubectl wait --for=condition=ready pod -l app=controller -n knative-serving --timeout=120s
kubectl wait --for=condition=ready pod -l app=activator -n knative-serving --timeout=120s
kubectl wait --for=condition=ready pod -l app=autoscaler -n knative-serving --timeout=120s
kubectl wait --for=condition=ready pod -l app=webhook -n knative-serving --timeout=120s
print_ok "Serving pods ready"

# Install Networking Layer
print_step "Installing Networking Layer: $NETWORKING"

case "$NETWORKING" in
    kourier)
        kubectl apply -f "https://github.com/knative/net-kourier/releases/download/knative-${VERSION}/kourier.yaml"
        kubectl patch configmap/config-network \
            --namespace knative-serving \
            --type merge \
            --patch '{"data":{"ingress-class":"kourier.ingress.networking.knative.dev"}}'
        print_ok "Kourier installed"

        # Wait for Kourier
        kubectl wait --for=condition=ready pod -l app=3scale-kourier-gateway -n kourier-system --timeout=120s
        print_ok "Kourier gateway ready"
        ;;
    istio)
        kubectl apply -f "https://github.com/knative/net-istio/releases/download/knative-${VERSION}/net-istio.yaml"
        kubectl patch configmap/config-network \
            --namespace knative-serving \
            --type merge \
            --patch '{"data":{"ingress-class":"istio.ingress.networking.knative.dev"}}'
        print_ok "Istio networking installed"
        ;;
    contour)
        kubectl apply -f "https://github.com/knative/net-contour/releases/download/knative-${VERSION}/contour.yaml"
        kubectl apply -f "https://github.com/knative/net-contour/releases/download/knative-${VERSION}/net-contour.yaml"
        kubectl patch configmap/config-network \
            --namespace knative-serving \
            --type merge \
            --patch '{"data":{"ingress-class":"contour.ingress.networking.knative.dev"}}'
        print_ok "Contour networking installed"
        ;;
    *)
        print_error "Unknown networking layer: $NETWORKING. Use: kourier, istio, or contour"
        ;;
esac

# Install Knative Eventing
print_step "Installing Knative Eventing CRDs"
kubectl apply -f "https://github.com/knative/eventing/releases/download/knative-${VERSION}/eventing-crds.yaml"
print_ok "Eventing CRDs installed"

print_step "Installing Knative Eventing Core"
kubectl apply -f "https://github.com/knative/eventing/releases/download/knative-${VERSION}/eventing-core.yaml"
print_ok "Eventing core installed"

# Install In-Memory Channel (dev) or wait for Kafka setup
print_step "Installing In-Memory Channel (for development)"
kubectl apply -f "https://github.com/knative/eventing/releases/download/knative-${VERSION}/in-memory-channel.yaml"
print_ok "In-Memory Channel installed"

print_step "Installing MT-Channel-Based Broker"
kubectl apply -f "https://github.com/knative/eventing/releases/download/knative-${VERSION}/mt-channel-broker.yaml"
print_ok "MT-Channel-Based Broker installed"

# Wait for eventing pods
print_step "Waiting for Eventing pods to be ready"
kubectl wait --for=condition=ready pod -l app=eventing-controller -n knative-eventing --timeout=120s
kubectl wait --for=condition=ready pod -l app=eventing-webhook -n knative-eventing --timeout=120s
print_ok "Eventing pods ready"

# Get External IP for DNS configuration
print_header "Installation Complete"

echo -e "\n${YELLOW}External IP for DNS configuration:${NC}"
case "$NETWORKING" in
    kourier)
        kubectl get svc kourier -n kourier-system
        ;;
    istio)
        kubectl get svc istio-ingressgateway -n istio-system
        ;;
    contour)
        kubectl get svc envoy -n contour-external
        ;;
esac

echo -e "\n${YELLOW}Next steps:${NC}"
echo "1. Configure DNS:"
echo "   - Production: Create A record *.knative.yourdomain.com -> EXTERNAL-IP"
echo "   - Development: Use sslip.io magic DNS"
echo ""
echo "2. Configure domain:"
echo "   kubectl patch configmap/config-domain \\"
echo "     --namespace knative-serving \\"
echo "     --type merge \\"
echo "     --patch '{\"data\":{\"<EXTERNAL-IP>.sslip.io\":\"\"}}'"
echo ""
echo "3. (Optional) Enable auto-TLS with cert-manager"
echo ""
echo "Run './diagnose.sh ${CLUSTER:-}' to verify installation"
