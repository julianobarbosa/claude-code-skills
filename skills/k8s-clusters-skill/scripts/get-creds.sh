#!/bin/bash
# get-creds.sh - Get or refresh kubeconfig for a cluster
# Usage: ./get-creds.sh <cluster> [--admin]

set -e

# Cluster configurations: azure_name|resource_group|kubeconfig_name
declare -A CLUSTERS=(
    ["cafehyna-dev"]="aks-cafehyna-dev-hlg|RS_Hypera_Cafehyna_Dev|aks-rg-hypera-cafehyna-dev-config"
    ["cafehyna-hub"]="aks-cafehyna-default|rs_hypera_cafehyna|aks-rg-hypera-cafehyna-hub-config"
    ["cafehyna-prd"]="aks-cafehyna-prd|rs_hypera_cafehyna_prd|aks-rg-hypera-cafehyna-prd-config"
    ["loyalty-dev"]="Loyalty_AKS-QAS|RS_Hypera_Loyalty_AKS_QAS|aks-rg-hypera-loyalty-dev-config"
    ["loyalty-prd"]="Loyalty_AKS-PRD|RS_Hypera_Loyalty_AKS_PRD|aks-rg-hypera-loyalty-prd-config"
    ["sonora-dev"]="AKS-Hypera-Sonora-Dev-Hlg|rg-hypera-sonora-dev|aks-rg-hypera-sonora-dev-config"
    ["painelclientes-dev"]="akspainelclientedev|rg-hypera-painelclientes-dev|aks-rg-hypera-painelclientes-dev-config"
    ["painelclientes-hub"]="akspainelclienteshub|rg-hypera-painelclientes-hub|aks-rg-hypera-painelclientes-hub-config"
    ["painelclientes-prd"]="akspainelclientesprd|rg-hypera-painelclientes-prd|aks-rg-hypera-painelclientes-prd-config"
)

CLUSTER="${1:?Usage: $0 <cluster> [--admin]}"
ADMIN_FLAG=""
[[ "$2" == "--admin" ]] && ADMIN_FLAG="--admin"

CONFIG="${CLUSTERS[$CLUSTER]}"
if [[ -z "$CONFIG" ]]; then
    echo "Error: Unknown cluster '$CLUSTER'"
    echo "Valid clusters: ${!CLUSTERS[*]}"
    exit 1
fi

IFS='|' read -r AZURE_NAME RESOURCE_GROUP KUBECONFIG_NAME <<< "$CONFIG"
KUBECONFIG_PATH="$HOME/.kube/$KUBECONFIG_NAME"

echo "Cluster: $CLUSTER"
echo "Azure Name: $AZURE_NAME"
echo "Resource Group: $RESOURCE_GROUP"
echo "Kubeconfig: $KUBECONFIG_PATH"
echo ""

# Check Azure login
if ! az account show &>/dev/null; then
    echo "Not logged in to Azure. Running 'az login'..."
    az login
fi

echo "Fetching credentials..."
az aks get-credentials \
    --resource-group "$RESOURCE_GROUP" \
    --name "$AZURE_NAME" \
    --file "$KUBECONFIG_PATH" \
    --overwrite-existing \
    $ADMIN_FLAG

chmod 600 "$KUBECONFIG_PATH"

echo ""
echo "✅ Credentials saved to $KUBECONFIG_PATH"
echo ""
echo "Test with:"
echo "  kubectl --kubeconfig $KUBECONFIG_PATH get nodes"
