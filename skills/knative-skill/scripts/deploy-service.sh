#!/bin/bash
# Deploy a Knative Service
# Usage: ./deploy-service.sh <name> <image> [namespace] [cluster]

set -euo pipefail

NAME="${1:-}"
IMAGE="${2:-}"
NAMESPACE="${3:-default}"
CLUSTER="${4:-}"

if [[ -z "$NAME" || -z "$IMAGE" ]]; then
    echo "Usage: $0 <name> <image> [namespace] [cluster]"
    echo ""
    echo "Examples:"
    echo "  $0 hello-world gcr.io/knative-samples/helloworld-go"
    echo "  $0 my-app myregistry/myapp:v1 production cafehyna-dev"
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

# Check if cluster uses spot instances (dev clusters)
SPOT_TOLERATIONS=""
if [[ "$CLUSTER" == *"-dev"* ]]; then
    echo "Dev cluster detected - adding spot tolerations"
    SPOT_TOLERATIONS='
      tolerations:
        - key: kubernetes.azure.com/scalesetpriority
          operator: Equal
          value: "spot"
          effect: NoSchedule
      affinity:
        nodeAffinity:
          requiredDuringSchedulingIgnoredDuringExecution:
            nodeSelectorTerms:
              - matchExpressions:
                  - key: agentpool
                    operator: In
                    values:
                      - cafedevspot'
fi

# Generate Knative Service YAML
cat <<EOF
---
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: ${NAME}
  namespace: ${NAMESPACE}
spec:
  template:
    metadata:
      annotations:
        # Autoscaling configuration
        autoscaling.knative.dev/class: kpa.autoscaling.knative.dev
        autoscaling.knative.dev/min-scale: "0"
        autoscaling.knative.dev/max-scale: "10"
        autoscaling.knative.dev/target: "100"
    spec:${SPOT_TOLERATIONS}
      containers:
        - image: ${IMAGE}
          ports:
            - containerPort: 8080
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              memory: 128Mi
          # readinessProbe:
          #   httpGet:
          #     path: /health
          #     port: 8080
EOF

echo ""
echo "---"
echo ""
echo "To deploy this service, pipe the output to kubectl:"
echo "  $0 $NAME $IMAGE $NAMESPACE $CLUSTER | kubectl apply -f -"
echo ""
echo "Or save to file and apply:"
echo "  $0 $NAME $IMAGE $NAMESPACE $CLUSTER > ksvc-${NAME}.yaml"
echo "  kubectl apply -f ksvc-${NAME}.yaml"
