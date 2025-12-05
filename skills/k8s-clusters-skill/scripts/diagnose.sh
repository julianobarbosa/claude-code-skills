#!/bin/bash
# diagnose.sh - Diagnose cluster connection issues
# Usage: ./diagnose.sh <cluster>

set -e

# Cluster configurations: kubeconfig|api_server
declare -A CLUSTERS=(
    ["cafehyna-dev"]="aks-rg-hypera-cafehyna-dev-config|aks-cafehyna-dev-hlg-q3oga63c.30041054-9b14-4852-9bd5-114d2fac4590.privatelink.eastus.azmk8s.io"
    ["cafehyna-hub"]="aks-rg-hypera-cafehyna-hub-config|aks-cafehyna-default-b2ie56p8.5bbf1042-d320-432c-bd11-cea99f009c29.privatelink.eastus.azmk8s.io"
    ["cafehyna-prd"]="aks-rg-hypera-cafehyna-prd-config|aks-cafehyna-prd-hsr83z2k.c7d864af-cbd7-481b-866b-8559e0d1c1ea.privatelink.eastus.azmk8s.io"
    ["loyalty-dev"]="aks-rg-hypera-loyalty-dev-config|loyaltyaks-qas-dns-d330cafe.hcp.eastus.azmk8s.io"
    ["loyalty-prd"]="aks-rg-hypera-loyalty-prd-config|loyaltyaks-prd-dns-4d88035e.hcp.eastus.azmk8s.io"
    ["sonora-dev"]="aks-rg-hypera-sonora-dev-config|aks-hypera-sonora-dev-hlg-yz9t4ou8.d9f58524-b5b3-4fa9-af7d-cd5007447dea.privatelink.eastus.azmk8s.io"
    ["painelclientes-dev"]="aks-rg-hypera-painelclientes-dev-config|akspainelclientedev-dns-vjs3nd48.hcp.eastus2.azmk8s.io"
)

CLUSTER="${1:?Usage: $0 <cluster>}"

CONFIG="${CLUSTERS[$CLUSTER]}"
if [[ -z "$CONFIG" ]]; then
    echo "Error: Unknown cluster '$CLUSTER'"
    echo "Valid clusters: ${!CLUSTERS[*]}"
    exit 1
fi

IFS='|' read -r KUBECONFIG_NAME API_SERVER <<< "$CONFIG"
KUBECONFIG_PATH="$HOME/.kube/$KUBECONFIG_NAME"

echo "=========================================="
echo "Diagnostics for: $CLUSTER"
echo "=========================================="
echo ""

# 1. Check kubeconfig exists
echo "1. Kubeconfig file"
if [[ -f "$KUBECONFIG_PATH" ]]; then
    echo "   ✅ Found: $KUBECONFIG_PATH"
    PERMS=$(stat -c "%a" "$KUBECONFIG_PATH" 2>/dev/null || stat -f "%OLp" "$KUBECONFIG_PATH")
    if [[ "$PERMS" == "600" ]]; then
        echo "   ✅ Permissions: $PERMS"
    else
        echo "   ⚠️  Permissions: $PERMS (should be 600)"
    fi
else
    echo "   ❌ Not found: $KUBECONFIG_PATH"
    echo "   Run: scripts/get-creds.sh $CLUSTER"
fi
echo ""

# 2. Check Azure login
echo "2. Azure CLI"
if az account show &>/dev/null; then
    ACCOUNT=$(az account show --query "{name:name,user:user.name}" -o tsv 2>/dev/null)
    echo "   ✅ Logged in: $ACCOUNT"
else
    echo "   ❌ Not logged in. Run: az login"
fi
echo ""

# 3. DNS resolution
echo "3. DNS Resolution"
if command -v nslookup &>/dev/null; then
    if nslookup "$API_SERVER" &>/dev/null; then
        IP=$(nslookup "$API_SERVER" 2>/dev/null | grep -A1 "Name:" | grep "Address" | head -1 | awk '{print $2}')
        echo "   ✅ Resolves to: $IP"
    else
        echo "   ❌ DNS failed for: $API_SERVER"
        echo "   Check VPN connection or DNS configuration"
    fi
else
    echo "   ⚠️  nslookup not available"
fi
echo ""

# 4. TCP connectivity
echo "4. TCP Connectivity (port 443)"
if command -v nc &>/dev/null; then
    if nc -zw3 "$API_SERVER" 443 &>/dev/null; then
        echo "   ✅ Port 443 reachable"
    else
        echo "   ❌ Cannot reach $API_SERVER:443"
        echo "   Check VPN/firewall"
    fi
elif command -v timeout &>/dev/null; then
    if timeout 3 bash -c "echo >/dev/tcp/$API_SERVER/443" 2>/dev/null; then
        echo "   ✅ Port 443 reachable"
    else
        echo "   ❌ Cannot reach $API_SERVER:443"
    fi
else
    echo "   ⚠️  nc/timeout not available"
fi
echo ""

# 5. kubectl test
echo "5. kubectl Connection"
if [[ -f "$KUBECONFIG_PATH" ]]; then
    if kubectl --kubeconfig "$KUBECONFIG_PATH" cluster-info &>/dev/null; then
        echo "   ✅ Connected successfully"
        kubectl --kubeconfig "$KUBECONFIG_PATH" get nodes --no-headers 2>/dev/null | while read line; do
            echo "   Node: $line"
        done
    else
        echo "   ❌ Connection failed"
        kubectl --kubeconfig "$KUBECONFIG_PATH" cluster-info 2>&1 | head -5 | sed 's/^/   /'
    fi
fi
echo ""

echo "=========================================="
echo "Diagnostics complete"
echo "=========================================="
