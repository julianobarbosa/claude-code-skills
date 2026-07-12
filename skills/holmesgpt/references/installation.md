# HolmesGPT Installation Guide

Complete installation instructions for all deployment methods.

## Prerequisites

- Kubernetes cluster (for Helm/in-cluster deployment)
- kubectl configured with cluster access
- API key from supported AI provider (Anthropic, OpenAI, Azure, etc.)
- Python 3.9+ (for pip/poetry installation)

## Installation Methods

### 1. Homebrew (Mac/Linux) - Recommended for CLI

```bash
# Install
brew tap robusta-dev/homebrew-holmesgpt
brew install holmesgpt

# Verify installation
holmes ask --help

# Upgrade
brew upgrade holmesgpt
```

### 2. Pipx (Cross-platform)

```bash
# Install pipx first if needed
# macOS: brew install pipx
# Linux: python3 -m pip install --user pipx
# pipx ensurepath

# Install HolmesGPT
pipx install holmesgpt

# Verify
holmes ask --help

# Upgrade
pipx upgrade holmesgpt
```

### 3. Poetry (Development/Source)

```bash
# Clone repository
git clone https://github.com/robusta-dev/holmesgpt.git
cd holmesgpt

# Install with Poetry
poetry install --no-root

# Run via poetry
poetry run holmes ask --help

# Or activate shell
poetry shell
holmes ask --help
```

### 4. Docker

```bash
# Basic usage with OpenAI
docker run -it --net=host \
  -e OPENAI_API_KEY="your-api-key" \
  -v ~/.kube/config:/root/.kube/config \
  us-central1-docker.pkg.dev/genuine-flight-317411/devel/holmes \
  ask "what pods are unhealthy?"

# With Anthropic
docker run -it --net=host \
  -e ANTHROPIC_API_KEY="your-api-key" \
  -v ~/.kube/config:/root/.kube/config \
  us-central1-docker.pkg.dev/genuine-flight-317411/devel/holmes \
  ask "what pods are unhealthy?"

# Full mount for all credentials
docker run -it --net=host \
  -e ANTHROPIC_API_KEY="your-key" \
  -v ~/.holmes:/root/.holmes \
  -v ~/.aws:/root/.aws \
  -v ~/.config/gcloud:/root/.config/gcloud \
  -v ~/.kube/config:/root/.kube/config \
  us-central1-docker.pkg.dev/genuine-flight-317411/devel/holmes \
  ask "query here"
```

### 5. Kubernetes (Helm) - Production Deployment

```bash
# Add Helm repository
helm repo add robusta https://robusta-charts.storage.googleapis.com
helm repo update

# Create namespace
kubectl create namespace holmesgpt

# Create secret for API keys
kubectl create secret generic holmesgpt-secrets \
  --namespace holmesgpt \
  --from-literal=anthropic-api-key="your-anthropic-key"

# Create values.yaml (see below)

# Install
helm install holmesgpt robusta/holmes \
  --namespace holmesgpt \
  -f values.yaml

# Verify deployment
kubectl get pods -n holmesgpt
kubectl logs -n holmesgpt deployment/holmesgpt-holmes

# Upgrade
helm repo update
helm upgrade holmesgpt robusta/holmes \
  --namespace holmesgpt \
  -f values.yaml

# Uninstall
helm uninstall holmesgpt -n holmesgpt
```

### Version Pinning (Production Recommended)

For production environments, pin to specific chart versions to ensure
reproducible deployments and controlled upgrades.

```bash
# List available chart versions
helm search repo robusta/holmes --versions

# Install specific version
helm install holmesgpt robusta/holmes \
  --version 1.5.0 \
  --namespace holmesgpt \
  -f values.yaml

# Upgrade to specific version
helm upgrade holmesgpt robusta/holmes \
  --version 1.6.0 \
  --namespace holmesgpt \
  -f values.yaml

# Check current installed version
helm list -n holmesgpt
```

**ArgoCD Application with Version Pinning:**

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: holmesgpt
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://robusta-charts.storage.googleapis.com
    chart: holmes
    targetRevision: 1.5.0  # Pin chart version
    helm:
      valueFiles:
        - values.yaml
  destination:
    server: https://kubernetes.default.svc
    namespace: holmesgpt
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

**Upgrade Strategy:**

1. Review changelog for breaking changes
2. Test in non-production environment first
3. Update `targetRevision` in ArgoCD or `--version` in Helm
4. Monitor pod logs after upgrade

## Helm values.yaml Examples

### Minimal Configuration (OpenAI)

```yaml
env:
  - name: OPENAI_API_KEY
    valueFrom:
      secretKeyRef:
        name: holmesgpt-secrets
        key: openai-api-key

modelList:
  gpt4:
    api_key: "{{ env.OPENAI_API_KEY }}"
    model: openai/gpt-4.1
    temperature: 0
```

### Anthropic Configuration (Recommended)

```yaml
env:
  - name: ANTHROPIC_API_KEY
    valueFrom:
      secretKeyRef:
        name: holmesgpt-secrets
        key: anthropic-api-key

modelList:
  sonnet:
    api_key: "{{ env.ANTHROPIC_API_KEY }}"
    model: anthropic/claude-sonnet-4-20250514
    temperature: 0
  opus:
    api_key: "{{ env.ANTHROPIC_API_KEY }}"
    model: anthropic/claude-opus-4-20250514
    temperature: 0
```

### Azure OpenAI Configuration

```yaml
env:
  - name: AZURE_API_KEY
    valueFrom:
      secretKeyRef:
        name: holmesgpt-secrets
        key: azure-api-key
  - name: AZURE_API_BASE
    value: "https://your-resource.openai.azure.com"
  - name: AZURE_API_VERSION
    value: "2024-02-15-preview"

modelList:
  azure-gpt4:
    api_key: "{{ env.AZURE_API_KEY }}"
    model: azure/your-deployment-name
    api_base: "{{ env.AZURE_API_BASE }}"
    api_version: "{{ env.AZURE_API_VERSION }}"
    temperature: 0
```

### AWS Bedrock Configuration

```yaml
env:
  - name: AWS_ACCESS_KEY_ID
    valueFrom:
      secretKeyRef:
        name: holmesgpt-secrets
        key: aws-access-key-id
  - name: AWS_SECRET_ACCESS_KEY
    valueFrom:
      secretKeyRef:
        name: holmesgpt-secrets
        key: aws-secret-access-key
  - name: AWS_DEFAULT_REGION
    value: "us-east-1"

modelList:
  bedrock-claude:
    model: bedrock/anthropic.claude-3-sonnet-20240229-v1:0
    temperature: 0
```

### Production Configuration

```yaml
image:
  repository: robustadev/holmes
  tag: latest
  pullPolicy: IfNotPresent

replicaCount: 1

env:
  - name: ANTHROPIC_API_KEY
    valueFrom:
      secretKeyRef:
        name: holmesgpt-secrets
        key: anthropic-api-key
  - name: PROMETHEUS_URL
    value: "http://prometheus-server.monitoring.svc.cluster.local"

modelList:
  sonnet:
    api_key: "{{ env.ANTHROPIC_API_KEY }}"
    model: anthropic/claude-sonnet-4-20250514
    temperature: 0

toolsets:
  kubernetes/core:
    enabled: true
  kubernetes/logs:
    enabled: true
  prometheus/metrics:
    enabled: true
  robusta:
    enabled: false

resources:
  requests:
    memory: "1024Mi"
    cpu: "100m"
  limits:
    memory: "2048Mi"

createServiceAccount: true

logLevel: INFO
enableTelemetry: false

# Node scheduling
nodeSelector: {}
tolerations: []
affinity: {}

# Pod disruption budget
podDisruptionBudget:
  enabled: true
  minAvailable: 1
```

## Post-Installation Verification

### CLI Verification

```bash
# Set API key
export ANTHROPIC_API_KEY="your-key"
# or
export OPENAI_API_KEY="your-key"

# Test basic query
holmes ask "list all namespaces"

# Test with specific cluster context
holmes ask "what pods are running in kube-system?"
```

### Helm Verification

```bash
# Check pod status
kubectl get pods -n holmesgpt

# Check logs
kubectl logs -n holmesgpt deployment/holmesgpt-holmes

# Port forward for API access
kubectl port-forward -n holmesgpt svc/holmesgpt-holmes 8080:80

# Test API
curl -X POST http://localhost:8080/api/chat \
  -H "Content-Type: application/json" \
  -d '{"ask": "list pods in default namespace", "model": "sonnet"}'
```

## Configuration File

Store common settings in `~/.holmes/config.yaml`:

```yaml
# Default model
model: sonnet

# Default toolsets
toolsets:
  - kubernetes/core
  - kubernetes/logs
  - prometheus/metrics

# Custom runbooks location
runbooks: ~/runbooks/

# Log level
log_level: INFO
```

## Troubleshooting Installation

### Common Issues

1. **API Key Not Found**

   ```bash
   # Verify environment variable
   echo $ANTHROPIC_API_KEY

   # Or set inline
   ANTHROPIC_API_KEY="key" holmes ask "test"
   ```

2. **kubectl Access Issues**

   ```bash
   # Verify kubeconfig
   kubectl get pods

   # Check current context
   kubectl config current-context
   ```

3. **Helm Installation Fails**

   ```bash
   # Check Helm repos
   helm repo list

   # Update repos
   helm repo update

   # Debug installation
   helm install holmesgpt robusta/holmes -f values.yaml --debug --dry-run
   ```

4. **Permission Denied**

   ```bash
   # Check RBAC
   kubectl auth can-i get pods --as=system:serviceaccount:holmesgpt:holmesgpt-holmes
   ```
