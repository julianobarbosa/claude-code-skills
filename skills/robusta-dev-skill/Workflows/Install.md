# Install Robusta

Step-by-step workflow for installing Robusta on Kubernetes clusters.

## Prerequisites Check

```bash
# Verify Helm is installed
helm version

# Verify kubectl is configured
kubectl cluster-info

# Check cluster resources (for sizing)
kubectl get nodes
```

## Installation Options

### Option 1: All-in-One (Robusta + Prometheus Stack)

Best for new clusters without existing monitoring.

```bash
# Step 1: Generate configuration
pipx run robusta-cli gen-config --enable-prometheus-stack

# Or using Docker if pipx not available
curl -fsSL -o robusta https://docs.robusta.dev/master/_static/robusta
chmod +x robusta
./robusta gen-config --enable-prometheus-stack

# Step 2: Add Helm repository
helm repo add robusta https://robusta-charts.storage.googleapis.com
helm repo update

# Step 3: Install
helm install robusta robusta/robusta \
  -f ./generated_values.yaml \
  --set clusterName=my-cluster \
  --namespace robusta \
  --create-namespace

# Step 4: Verify
kubectl get pods -n robusta
kubectl logs -n robusta deploy/robusta-runner -f
```

### Option 2: Standalone (Existing Prometheus)

For clusters with existing Prometheus/AlertManager.

```bash
# Generate config without Prometheus stack
pipx run robusta-cli gen-config

# Install
helm install robusta robusta/robusta \
  -f ./generated_values.yaml \
  --set clusterName=my-cluster
```

## Platform-Specific Configurations

### GKE Autopilot

```bash
helm install robusta robusta/robusta \
  -f ./generated_values.yaml \
  --set clusterName=my-gke-cluster \
  --set kube-prometheus-stack.coreDns.enabled=false \
  --set kube-prometheus-stack.kubeControllerManager.enabled=false \
  --set kube-prometheus-stack.kubeEtcd.enabled=false \
  --set kube-prometheus-stack.kubeScheduler.enabled=false \
  --set kube-prometheus-stack.kubeProxy.enabled=false
```

### EKS

Ensure EBS CSI driver is installed:
```bash
# Install EBS CSI driver add-on via eksctl or AWS console
helm install robusta robusta/robusta \
  -f ./generated_values.yaml \
  --set clusterName=my-eks-cluster \
  --set enablePlatformPlaybooks=true
```

### AKS

```bash
helm install robusta robusta/robusta \
  -f ./generated_values.yaml \
  --set clusterName=my-aks-cluster
```

### Small/Test Clusters

For clusters with limited resources:
```bash
helm install robusta robusta/robusta \
  -f ./generated_values.yaml \
  --set isSmallCluster=true
```

### OpenShift

```bash
helm install robusta robusta/robusta \
  -f ./generated_values.yaml \
  --set openshift.enabled=true \
  --set openshift.createScc=true
```

## Post-Installation Verification

```bash
# Check all pods are running
kubectl get pods -n robusta

# Expected pods:
# - robusta-runner (main processor)
# - robusta-forwarder (event collector)
# - prometheus-* (if all-in-one install)

# Check logs for errors
kubectl logs -n robusta deploy/robusta-runner --tail=50

# Test connectivity to sinks
kubectl exec -n robusta deploy/robusta-runner -- robusta playbooks list
```

## Upgrading

```bash
helm repo update
helm upgrade robusta robusta/robusta \
  -f ./generated_values.yaml \
  --namespace robusta
```

## Uninstalling

```bash
helm uninstall robusta -n robusta
kubectl delete namespace robusta
```
