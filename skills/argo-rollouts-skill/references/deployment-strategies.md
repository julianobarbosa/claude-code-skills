# Deployment Strategies

## Overview

Argo Rollouts supports two primary deployment strategies:

1. **Canary**: Gradual traffic shifting with analysis gates
2. **Blue-Green**: Instant traffic switching between versions

## Canary Strategy

### Basic Canary

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: canary-rollout
spec:
  replicas: 5
  strategy:
    canary:
      steps:
      - setWeight: 20
      - pause: {duration: 1m}
      - setWeight: 40
      - pause: {duration: 1m}
      - setWeight: 60
      - pause: {duration: 1m}
      - setWeight: 80
      - pause: {duration: 1m}
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
      - name: app
        image: my-app:v2
```

### Canary Step Types

| Step Type | Description | Example |
|-----------|-------------|---------|
| `setWeight` | Set traffic percentage to canary | `setWeight: 20` |
| `pause` | Pause rollout for duration or indefinitely | `pause: {duration: 5m}` or `pause: {}` |
| `analysis` | Run analysis before proceeding | `analysis: {templates: [...]}` |
| `experiment` | Run experiment with baseline and canary | `experiment: {...}` |
| `setCanaryScale` | Scale canary ReplicaSet | `setCanaryScale: {replicas: 3}` |
| `setHeaderRoute` | Route by header (traffic management) | `setHeaderRoute: {...}` |

### Canary with Analysis

```yaml
spec:
  strategy:
    canary:
      steps:
      - setWeight: 10
      - pause: {duration: 2m}
      - analysis:
          templates:
          - templateName: success-rate
          args:
          - name: service-name
            value: my-service
      - setWeight: 30
      - pause: {duration: 2m}
      - analysis:
          templates:
          - templateName: latency-check
      - setWeight: 50
      - pause: {duration: 5m}
```

### Canary with Traffic Management (Istio)

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: canary-istio
spec:
  replicas: 5
  strategy:
    canary:
      canaryService: my-app-canary
      stableService: my-app-stable
      trafficRouting:
        istio:
          virtualService:
            name: my-app-vsvc
            routes:
            - primary
      steps:
      - setWeight: 10
      - pause: {duration: 1m}
      - setWeight: 30
      - pause: {duration: 1m}
      - setWeight: 50
      - pause: {}  # Manual promotion required
  selector:
    matchLabels:
      app: my-app
  template:
    # ...
```

### Canary with NGINX Ingress

```yaml
spec:
  strategy:
    canary:
      canaryService: my-app-canary
      stableService: my-app-stable
      trafficRouting:
        nginx:
          stableIngress: my-app-ingress
          annotationPrefix: nginx.ingress.kubernetes.io
          additionalIngressAnnotations:
            canary-by-header: X-Canary
      steps:
      - setWeight: 20
      - pause: {duration: 5m}
      - setWeight: 50
      - pause: {}
```

## Blue-Green Strategy

### Basic Blue-Green

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: blue-green-rollout
spec:
  replicas: 3
  strategy:
    blueGreen:
      activeService: my-app-active
      previewService: my-app-preview
      autoPromotionEnabled: false
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
    spec:
      containers:
      - name: app
        image: my-app:v2
```

### Blue-Green Configuration Options

| Option | Type | Description |
|--------|------|-------------|
| `activeService` | string | Service for production traffic |
| `previewService` | string | Service for preview/testing |
| `autoPromotionEnabled` | bool | Auto-promote after delay (default: true) |
| `autoPromotionSeconds` | int | Seconds before auto-promotion |
| `prePromotionAnalysis` | object | Analysis before promotion |
| `postPromotionAnalysis` | object | Analysis after promotion |
| `scaleDownDelaySeconds` | int | Delay before scaling down old version |
| `scaleDownDelayRevisionLimit` | int | Number of old ReplicaSets to retain (default: 1) |
| `antiAffinity` | object | Pod anti-affinity for blue/green |

### Blue-Green with Pre-Promotion Analysis

```yaml
spec:
  strategy:
    blueGreen:
      activeService: my-app-active
      previewService: my-app-preview
      autoPromotionEnabled: false
      prePromotionAnalysis:
        templates:
        - templateName: smoke-tests
        args:
        - name: preview-url
          value: http://my-app-preview.default.svc.cluster.local
```

### Blue-Green with Post-Promotion Analysis

```yaml
spec:
  strategy:
    blueGreen:
      activeService: my-app-active
      previewService: my-app-preview
      autoPromotionEnabled: true
      autoPromotionSeconds: 30
      postPromotionAnalysis:
        templates:
        - templateName: post-deploy-checks
        args:
        - name: service-name
          value: my-app-active
```

### Blue-Green with Anti-Affinity

```yaml
spec:
  strategy:
    blueGreen:
      activeService: my-app-active
      previewService: my-app-preview
      antiAffinity:
        preferredDuringSchedulingIgnoredDuringExecution:
          weight: 100
      scaleDownDelaySeconds: 30
```

## Comparison: Canary vs Blue-Green

| Aspect | Canary | Blue-Green |
|--------|--------|------------|
| Traffic Control | Gradual (1%, 5%, 20%...) | Instant (0% → 100%) |
| Resource Usage | Lower (shared pods) | Higher (2x during deploy) |
| Rollback Speed | Instant | Instant |
| Testing | Production traffic sample | Dedicated preview env |
| Complexity | Higher (more steps) | Simpler |
| Best For | Risk-averse production | Quick validation |

## Advanced Patterns

### Canary with Header-Based Routing

```yaml
spec:
  strategy:
    canary:
      canaryService: my-app-canary
      stableService: my-app-stable
      trafficRouting:
        istio:
          virtualService:
            name: my-app-vsvc
            routes:
            - primary
      steps:
      - setHeaderRoute:
          name: canary-header
          match:
          - headerName: X-Canary
            headerValue:
              exact: "true"
      - pause: {}  # Test with header
      - setWeight: 20
      - pause: {duration: 5m}
```

### Canary with Experiment

```yaml
spec:
  strategy:
    canary:
      steps:
      - experiment:
          duration: 5m
          templates:
          - name: baseline
            specRef: stable
            replicas: 1
          - name: canary
            specRef: canary
            replicas: 1
          analyses:
          - name: compare
            templateName: ab-test-analysis
      - setWeight: 50
      - pause: {duration: 5m}
```

### Gradual Scale with Canary

```yaml
spec:
  strategy:
    canary:
      steps:
      - setCanaryScale:
          replicas: 1
      - pause: {duration: 2m}
      - setCanaryScale:
          weight: 25  # 25% of stable replicas
      - setWeight: 25
      - pause: {duration: 5m}
      - setCanaryScale:
          matchTrafficWeight: true  # Match traffic weight
      - setWeight: 50
```

## Rollback Behavior

### Automatic Rollback (Analysis Failure)

When an AnalysisRun fails, the Rollout automatically:

1. Aborts the current update
2. Scales down canary/preview ReplicaSet
3. Routes all traffic to stable version
4. Sets status to "Degraded"

### Manual Rollback

```bash
# Abort current rollout and rollback
kubectl argo rollouts abort my-rollout

# Undo to previous version
kubectl argo rollouts undo my-rollout

# Undo to specific revision
kubectl argo rollouts undo my-rollout --to-revision=2
```
