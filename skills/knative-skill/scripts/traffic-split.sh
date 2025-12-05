#!/bin/bash
# Configure traffic splitting for a Knative Service
# Usage: ./traffic-split.sh <service> <revision1:percent> [revision2:percent] ... [cluster]

set -euo pipefail

SERVICE="${1:-}"
shift || true

if [[ -z "$SERVICE" ]]; then
    echo "Usage: $0 <service> <revision:percent> [revision:percent] ... [--cluster=name]"
    echo ""
    echo "Examples:"
    echo "  # Blue-green deployment (100% to new revision)"
    echo "  $0 my-service my-service-00002:100"
    echo ""
    echo "  # Canary deployment (90/10 split)"
    echo "  $0 my-service my-service-00001:90 my-service-00002:10"
    echo ""
    echo "  # Gradual rollout"
    echo "  $0 my-service my-service-00001:70 my-service-00002:30"
    echo ""
    echo "  # With specific cluster"
    echo "  $0 my-service my-service-00002:100 --cluster=cafehyna-dev"
    echo ""
    echo "Special revision names:"
    echo "  @latest - Route to latest ready revision"
    exit 1
fi

NAMESPACE="${NAMESPACE:-default}"
CLUSTER=""
TRAFFIC_ENTRIES=()

# Parse arguments
for arg in "$@"; do
    if [[ "$arg" == --cluster=* ]]; then
        CLUSTER="${arg#--cluster=}"
    elif [[ "$arg" == --namespace=* ]]; then
        NAMESPACE="${arg#--namespace=}"
    elif [[ "$arg" == *:* ]]; then
        TRAFFIC_ENTRIES+=("$arg")
    fi
done

if [[ ${#TRAFFIC_ENTRIES[@]} -eq 0 ]]; then
    echo "Error: At least one revision:percent pair is required"
    exit 1
fi

# Set kubeconfig if cluster specified
if [[ -n "$CLUSTER" ]]; then
    KUBECONFIG_PATH="$HOME/.kube/aks-rg-hypera-${CLUSTER}-config"
    if [[ -f "$KUBECONFIG_PATH" ]]; then
        export KUBECONFIG="$KUBECONFIG_PATH"
        echo "Using kubeconfig: $KUBECONFIG_PATH"
    else
        echo "Error: Kubeconfig not found: $KUBECONFIG_PATH"
        exit 1
    fi
fi

# Validate percentages sum to 100
TOTAL=0
for entry in "${TRAFFIC_ENTRIES[@]}"; do
    percent="${entry#*:}"
    TOTAL=$((TOTAL + percent))
done

if [[ $TOTAL -ne 100 ]]; then
    echo "Error: Traffic percentages must sum to 100 (got $TOTAL)"
    exit 1
fi

# Build traffic patch
TRAFFIC_JSON="["
FIRST=true
for entry in "${TRAFFIC_ENTRIES[@]}"; do
    revision="${entry%:*}"
    percent="${entry#*:}"

    if [[ "$FIRST" == "true" ]]; then
        FIRST=false
    else
        TRAFFIC_JSON+=","
    fi

    if [[ "$revision" == "@latest" ]]; then
        TRAFFIC_JSON+="{\"latestRevision\":true,\"percent\":${percent}}"
    else
        TRAFFIC_JSON+="{\"revisionName\":\"${revision}\",\"percent\":${percent}}"
    fi
done
TRAFFIC_JSON+="]"

echo "Service: $SERVICE"
echo "Namespace: $NAMESPACE"
echo "Traffic configuration:"
for entry in "${TRAFFIC_ENTRIES[@]}"; do
    revision="${entry%:*}"
    percent="${entry#*:}"
    echo "  - $revision: ${percent}%"
done
echo ""

# Show the patch that would be applied
echo "Patch to apply:"
echo "{\"spec\":{\"traffic\":$TRAFFIC_JSON}}"
echo ""

read -p "Apply this traffic split? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

# Apply the patch
kubectl patch ksvc "$SERVICE" -n "$NAMESPACE" --type=merge -p "{\"spec\":{\"traffic\":$TRAFFIC_JSON}}"

echo ""
echo "Traffic split applied. Current status:"
kubectl get ksvc "$SERVICE" -n "$NAMESPACE" -o jsonpath='{range .status.traffic[*]}  {.revisionName}: {.percent}%{"\n"}{end}'
