#!/bin/bash
#
# Diagnose Secrets Store CSI Driver issues
#
# Usage: ./diagnose-csi.sh [namespace] [secretproviderclass-name]
#
# Examples:
#   ./diagnose-csi.sh                    # Check kube-system only
#   ./diagnose-csi.sh external-dns       # Check specific namespace
#   ./diagnose-csi.sh external-dns cloudflare-api-token-kv  # Check specific SPC

set -e

NS="${1:-}"
SPC="${2:-}"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${GREEN}=== Secrets Store CSI Driver Diagnostics ===${NC}"
echo ""

# Check CSI Driver pods
echo -e "${CYAN}[1/5] CSI Driver Pods${NC}"
kubectl get pods -n kube-system -l 'app in (secrets-store-csi-driver, secrets-store-provider-azure)' -o wide
echo ""

# Check CSI Driver status
DRIVER_PODS=$(kubectl get pods -n kube-system -l app=secrets-store-csi-driver -o jsonpath='{.items[*].status.phase}' 2>/dev/null || echo "")
PROVIDER_PODS=$(kubectl get pods -n kube-system -l app=secrets-store-provider-azure -o jsonpath='{.items[*].status.phase}' 2>/dev/null || echo "")

if [[ "$DRIVER_PODS" == *"Running"* ]] && [[ "$PROVIDER_PODS" == *"Running"* ]]; then
    echo -e "${GREEN}CSI Driver and Provider are running${NC}"
else
    echo -e "${RED}CSI Driver or Provider not healthy!${NC}"
    echo "Driver status: $DRIVER_PODS"
    echo "Provider status: $PROVIDER_PODS"
fi
echo ""

# Check CRD
echo -e "${CYAN}[2/5] SecretProviderClass CRD${NC}"
if kubectl get crd secretproviderclasses.secrets-store.csi.x-k8s.io &>/dev/null; then
    echo -e "${GREEN}SecretProviderClass CRD is installed${NC}"
else
    echo -e "${RED}SecretProviderClass CRD is NOT installed!${NC}"
fi
echo ""

# Check CSI Driver registration
echo -e "${CYAN}[3/5] CSI Driver Registration${NC}"
kubectl get csidriver secrets-store.csi.k8s.io -o jsonpath='{.metadata.name}' 2>/dev/null && echo -e " ${GREEN}(registered)${NC}" || echo -e "${RED}CSI Driver not registered!${NC}"
echo ""

# List SecretProviderClasses
echo -e "${CYAN}[4/5] SecretProviderClasses${NC}"
if [ -n "$NS" ]; then
    echo "Namespace: $NS"
    kubectl get secretproviderclass -n "$NS" 2>/dev/null || echo "No SecretProviderClasses found in $NS"
else
    echo "All namespaces:"
    kubectl get secretproviderclass -A 2>/dev/null || echo "No SecretProviderClasses found"
fi
echo ""

# Detailed SPC info if specified
if [ -n "$SPC" ] && [ -n "$NS" ]; then
    echo -e "${CYAN}[4b] SecretProviderClass Details: $SPC${NC}"
    echo ""

    if kubectl get secretproviderclass "$SPC" -n "$NS" &>/dev/null; then
        echo -e "${YELLOW}Configuration:${NC}"
        kubectl get secretproviderclass "$SPC" -n "$NS" -o yaml | grep -A50 "spec:"

        echo ""
        echo -e "${YELLOW}Events:${NC}"
        kubectl describe secretproviderclass "$SPC" -n "$NS" | grep -A20 "Events:" || echo "No events"
    else
        echo -e "${RED}SecretProviderClass $SPC not found in $NS${NC}"
    fi
    echo ""
fi

# Recent logs
echo -e "${CYAN}[5/5] Recent Logs${NC}"
echo ""

echo -e "${YELLOW}CSI Driver logs (last 10 lines):${NC}"
kubectl logs -n kube-system -l app=secrets-store-csi-driver --tail=10 2>/dev/null || echo "No logs available"
echo ""

echo -e "${YELLOW}Azure Provider logs (last 10 lines):${NC}"
kubectl logs -n kube-system -l app=secrets-store-provider-azure --tail=10 2>/dev/null || echo "No logs available"
echo ""

# Check for common errors in logs
echo -e "${CYAN}[Bonus] Checking for common errors...${NC}"
ERRORS=$(kubectl logs -n kube-system -l app=secrets-store-provider-azure --tail=100 2>/dev/null | grep -i "error\|failed\|forbidden" || echo "")

if [ -n "$ERRORS" ]; then
    echo -e "${RED}Errors found in provider logs:${NC}"
    echo "$ERRORS" | head -20
else
    echo -e "${GREEN}No obvious errors in recent provider logs${NC}"
fi
echo ""

echo -e "${GREEN}=== Diagnostics Complete ===${NC}"
