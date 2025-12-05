#!/bin/bash
# Create managed-premium-zrs StorageClass on a cluster
# Usage: ./create-storageclass.sh <cluster-name>
# Example: ./create-storageclass.sh cafehyna-dev

set -e

CLUSTER=${1:-}

if [[ -z "$CLUSTER" ]]; then
    echo "Usage: $0 <cluster-name>"
    echo "Available clusters: cafehyna-dev, cafehyna-hub, cafehyna-prd, loyalty-dev, loyalty-prd, sonora-dev, painelclientes-dev"
    exit 1
fi

# Map cluster names to kubeconfig files
declare -A KUBECONFIGS=(
    ["cafehyna-dev"]="aks-rg-hypera-cafehyna-dev-config"
    ["cafehyna-hub"]="aks-rg-hypera-cafehyna-hub-config"
    ["cafehyna-prd"]="aks-rg-hypera-cafehyna-prd-config"
    ["loyalty-dev"]="aks-rg-hypera-loyalty-dev-config"
    ["loyalty-prd"]="aks-rg-hypera-loyalty-prd-config"
    ["sonora-dev"]="aks-rg-hypera-sonora-dev-config"
    ["painelclientes-dev"]="aks-rg-hypera-painelclientes-dev-config"
)

KUBECONFIG_FILE="${KUBECONFIGS[$CLUSTER]}"

if [[ -z "$KUBECONFIG_FILE" ]]; then
    echo "Error: Unknown cluster '$CLUSTER'"
    echo "Available clusters: ${!KUBECONFIGS[*]}"
    exit 1
fi

KUBECONFIG_PATH="$HOME/.kube/$KUBECONFIG_FILE"

if [[ ! -f "$KUBECONFIG_PATH" ]]; then
    echo "Error: Kubeconfig file not found: $KUBECONFIG_PATH"
    echo "Run: az aks get-credentials to download the config"
    exit 1
fi

export KUBECONFIG="$KUBECONFIG_PATH"

echo "=== Checking cluster: $CLUSTER ==="
echo "Using kubeconfig: $KUBECONFIG_PATH"

# Check if StorageClass already exists
if kubectl get storageclass managed-premium-zrs &>/dev/null; then
    echo "StorageClass 'managed-premium-zrs' already exists on $CLUSTER"
    kubectl get storageclass managed-premium-zrs
    exit 0
fi

echo "Creating StorageClass 'managed-premium-zrs' on $CLUSTER..."

kubectl apply -f - <<EOF
apiVersion: storage.k8s.io/v1
kind: StorageClass
metadata:
  name: managed-premium-zrs
  labels:
    kubernetes.io/cluster-service: "true"
provisioner: disk.csi.azure.com
parameters:
  skuName: Premium_ZRS
  kind: Managed
reclaimPolicy: Delete
volumeBindingMode: WaitForFirstConsumer
allowVolumeExpansion: true
EOF

echo ""
echo "StorageClass created successfully!"
kubectl get storageclass managed-premium-zrs
