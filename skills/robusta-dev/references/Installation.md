# Installation Reference

Detailed installation reference for Robusta on Kubernetes.

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Kubernetes | 1.19+ | Any distribution |
| Helm | 3.x | Required for installation |
| kubectl | Matching cluster | Configured for target cluster |

## Helm Chart

```bash
# Add repository
helm repo add robusta https://robusta-charts.storage.googleapis.com
helm repo update
```

## Configuration Generation

### Using pipx (Recommended)

```bash
pipx run robusta-cli gen-config --enable-prometheus-stack
```

### Using Docker

```bash
curl -fsSL -o robusta https://docs.robusta.dev/master/_static/robusta
chmod +x robusta
./robusta gen-config --enable-prometheus-stack
```

### Configuration Options

| Flag | Description |
|------|-------------|
| `--enable-prometheus-stack` | Include kube-prometheus-stack |
| `--no-enable-prometheus-stack` | Standalone mode (existing Prometheus) |
| `--slack-api-key` | Pre-configure Slack sink |
| `--cluster-name` | Set cluster identifier |

## Helm Values

### Core Values

```yaml
clusterName: my-cluster
globalConfig:
  signing_key: <generated>
  account_id: <generated>

sinksConfig:
  - slack_sink:
      name: main_slack
      slack_channel: alerts
      api_key: xoxb-...

runner:
  resources:
    requests:
      memory: 512Mi
      cpu: 250m
    limits:
      memory: 1Gi
      cpu: 1000m
```

### Platform-Specific Values

#### GKE Autopilot

```yaml
kube-prometheus-stack:
  coreDns:
    enabled: false
  kubeControllerManager:
    enabled: false
  kubeEtcd:
    enabled: false
  kubeScheduler:
    enabled: false
  kubeProxy:
    enabled: false
```

#### EKS

```yaml
enablePlatformPlaybooks: true
# Requires EBS CSI driver installed
```

#### OpenShift

```yaml
openshift:
  enabled: true
  createScc: true
```

#### Small Clusters

```yaml
isSmallCluster: true
runner:
  resources:
    limits:
      memory: 256Mi
      cpu: 250m
```

## Installation Commands

### Standard Install

```bash
helm install robusta robusta/robusta \
  -f ./generated_values.yaml \
  --set clusterName=my-cluster \
  --namespace robusta \
  --create-namespace
```

### Upgrade

```bash
helm repo update
helm upgrade robusta robusta/robusta \
  -f ./generated_values.yaml \
  --namespace robusta
```

### Uninstall

```bash
helm uninstall robusta -n robusta
kubectl delete namespace robusta
```

## Verification

```bash
# Check pods
kubectl get pods -n robusta

# Check runner logs
kubectl logs -n robusta deploy/robusta-runner --tail=50

# List loaded playbooks
kubectl exec -n robusta deploy/robusta-runner -- robusta playbooks list

# Send test notification
kubectl exec -n robusta deploy/robusta-runner -- robusta demo
```

## Expected Pods

| Pod | Purpose |
|-----|---------|
| robusta-runner | Main processing engine |
| robusta-forwarder | Event collector |
| prometheus-* | Metrics (if all-in-one) |
| alertmanager-* | Alert routing (if all-in-one) |
| grafana-* | Dashboards (if all-in-one) |
