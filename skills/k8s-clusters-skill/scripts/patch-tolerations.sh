#!/bin/bash
# patch-tolerations.sh - Add spot tolerations to a deployment
# Usage: ./patch-tolerations.sh <cluster> <deployment> <namespace>

set -e

# Cluster to kubeconfig mapping
declare -A KUBECONFIGS=(
    ["cafehyna-dev"]="aks-rg-hypera-cafehyna-dev-config"
    ["cafehyna-hub"]="aks-rg-hypera-cafehyna-hub-config"
    ["cafehyna-prd"]="aks-rg-hypera-cafehyna-prd-config"
    ["loyalty-dev"]="aks-rg-hypera-loyalty-dev-config"
    ["loyalty-prd"]="aks-rg-hypera-loyalty-prd-config"
    ["sonora-dev"]="aks-rg-hypera-sonora-dev-config"
    ["painelclientes-dev"]="aks-rg-hypera-painelclientes-dev-config"
)

CLUSTER="${1:?Usage: $0 <cluster> <deployment> <namespace>}"
DEPLOYMENT="${2:?Usage: $0 <cluster> <deployment> <namespace>}"
NAMESPACE="${3:?Usage: $0 <cluster> <deployment> <namespace>}"

KUBECONFIG_NAME="${KUBECONFIGS[$CLUSTER]}"
if [[ -z "$KUBECONFIG_NAME" ]]; then
    echo "Error: Unknown cluster '$CLUSTER'"
    echo "Valid clusters: ${!KUBECONFIGS[*]}"
    exit 1
fi

KUBECONFIG_PATH="$HOME/.kube/$KUBECONFIG_NAME"

if [[ ! -f "$KUBECONFIG_PATH" ]]; then
    echo "Error: Kubeconfig not found at $KUBECONFIG_PATH"
    echo "Run: scripts/get-creds.sh $CLUSTER"
    exit 1
fi

echo "Patching deployment '$DEPLOYMENT' in namespace '$NAMESPACE' on cluster '$CLUSTER'..."

kubectl --kubeconfig "$KUBECONFIG_PATH" patch deployment "$DEPLOYMENT" -n "$NAMESPACE" --type='json' \
    -p='[{
        "op": "add",
        "path": "/spec/template/spec/tolerations",
        "value": [{
            "key": "kubernetes.azure.com/scalesetpriority",
            "operator": "Equal",
            "value": "spot",
            "effect": "NoSchedule"
        }]
    }]'

echo "✅ Tolerations added successfully"
echo "Waiting for rollout..."
kubectl --kubeconfig "$KUBECONFIG_PATH" rollout status deployment/"$DEPLOYMENT" -n "$NAMESPACE" --timeout=120s
