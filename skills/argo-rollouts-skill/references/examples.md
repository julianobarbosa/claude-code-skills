# Complete YAML Examples

## Basic Canary Rollout

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: basic-canary
  namespace: default
spec:
  replicas: 5
  revisionHistoryLimit: 3
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
        image: nginx:1.21
        ports:
        - containerPort: 80
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
          limits:
            cpu: 200m
            memory: 256Mi
        readinessProbe:
          httpGet:
            path: /healthz
            port: 80
          initialDelaySeconds: 5
          periodSeconds: 10
  strategy:
    canary:
      steps:
      - setWeight: 20
      - pause: {duration: 30s}
      - setWeight: 40
      - pause: {duration: 30s}
      - setWeight: 60
      - pause: {duration: 30s}
      - setWeight: 80
      - pause: {duration: 30s}
```

## Basic Blue-Green Rollout

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: basic-blue-green
  namespace: default
spec:
  replicas: 3
  revisionHistoryLimit: 2
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
        image: nginx:1.21
        ports:
        - containerPort: 80
  strategy:
    blueGreen:
      activeService: my-app-active
      previewService: my-app-preview
      autoPromotionEnabled: false
---
apiVersion: v1
kind: Service
metadata:
  name: my-app-active
spec:
  selector:
    app: my-app
  ports:
  - port: 80
    targetPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: my-app-preview
spec:
  selector:
    app: my-app
  ports:
  - port: 80
    targetPort: 80
```

> **Note on Service Selectors**: Both `activeService` and `previewService` use the same base selector (`app: my-app`).
> Argo Rollouts automatically manages `rollouts-pod-template-hash` labels on pods to distinguish between stable and preview ReplicaSets.
> You do NOT need to add hash-based selectors to your services—the Rollouts controller handles traffic routing automatically.

## Canary with Istio Traffic Management

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: canary-istio
  namespace: default
spec:
  replicas: 5
  selector:
    matchLabels:
      app: my-app
  template:
    metadata:
      labels:
        app: my-app
        istio-injection: enabled
      annotations:
        sidecar.istio.io/inject: "true"
    spec:
      containers:
      - name: app
        image: myregistry/myapp:v1
        ports:
        - containerPort: 8080
        env:
        - name: VERSION
          value: "v1"
  strategy:
    canary:
      stableService: my-app-stable
      canaryService: my-app-canary
      trafficRouting:
        istio:
          virtualService:
            name: my-app-vsvc
            routes:
            - primary
      steps:
      - setWeight: 5
      - pause: {duration: 1m}
      - setWeight: 20
      - pause: {duration: 2m}
      - setWeight: 50
      - pause: {duration: 2m}
      - setWeight: 80
      - pause: {duration: 2m}
---
apiVersion: v1
kind: Service
metadata:
  name: my-app-stable
spec:
  selector:
    app: my-app
  ports:
  - port: 80
    targetPort: 8080
---
apiVersion: v1
kind: Service
metadata:
  name: my-app-canary
spec:
  selector:
    app: my-app
  ports:
  - port: 80
    targetPort: 8080
---
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: my-app-vsvc
spec:
  hosts:
  - my-app.example.com
  gateways:
  - my-gateway
  http:
  - name: primary
    route:
    - destination:
        host: my-app-stable
      weight: 100
    - destination:
        host: my-app-canary
      weight: 0
```

## Canary with Analysis

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: canary-with-analysis
  namespace: default
spec:
  replicas: 5
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
        image: myregistry/myapp:v1
        ports:
        - containerPort: 8080
  strategy:
    canary:
      steps:
      - setWeight: 10
      - pause: {duration: 2m}
      - analysis:
          templates:
          - templateName: success-rate-analysis
          args:
          - name: service-name
            value: my-app
      - setWeight: 30
      - pause: {duration: 2m}
      - analysis:
          templates:
          - templateName: latency-analysis
      - setWeight: 50
      - pause: {duration: 5m}
      - analysis:
          templates:
          - templateName: success-rate-analysis
          - templateName: latency-analysis
          args:
          - name: service-name
            value: my-app
---
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: success-rate-analysis
spec:
  args:
  - name: service-name
  metrics:
  - name: success-rate
    interval: 1m
    count: 5
    successCondition: result[0] >= 0.95
    failureLimit: 2
    provider:
      prometheus:
        address: http://prometheus.monitoring:9090
        query: |
          sum(rate(
            http_requests_total{service="{{args.service-name}}",status=~"2.*"}[5m]
          )) / sum(rate(
            http_requests_total{service="{{args.service-name}}"}[5m]
          ))
---
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: latency-analysis
spec:
  metrics:
  - name: p99-latency
    interval: 1m
    count: 5
    successCondition: result[0] < 500
    failureLimit: 2
    provider:
      prometheus:
        address: http://prometheus.monitoring:9090
        query: |
          histogram_quantile(0.99, sum(rate(
            http_request_duration_seconds_bucket[5m]
          )) by (le)) * 1000
```

## Blue-Green with Pre/Post Promotion Analysis

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: blue-green-with-analysis
  namespace: default
spec:
  replicas: 3
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
        image: myregistry/myapp:v1
        ports:
        - containerPort: 8080
  strategy:
    blueGreen:
      activeService: my-app-active
      previewService: my-app-preview
      autoPromotionEnabled: false
      scaleDownDelaySeconds: 30
      prePromotionAnalysis:
        templates:
        - templateName: smoke-test
        args:
        - name: preview-host
          value: my-app-preview.default.svc.cluster.local
      postPromotionAnalysis:
        templates:
        - templateName: post-deploy-check
        args:
        - name: active-host
          value: my-app-active.default.svc.cluster.local
---
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: smoke-test
spec:
  args:
  - name: preview-host
  metrics:
  - name: smoke-test
    count: 1
    successCondition: result == "ok"
    provider:
      web:
        url: "http://{{args.preview-host}}/health"
        jsonPath: "{$.status}"
---
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: post-deploy-check
spec:
  args:
  - name: active-host
  metrics:
  - name: post-deploy
    interval: 30s
    count: 5
    successCondition: result == "ok"
    failureLimit: 1
    provider:
      web:
        url: "http://{{args.active-host}}/health"
        jsonPath: "{$.status}"
```

## Canary with Background Analysis

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: canary-background-analysis
spec:
  replicas: 5
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
        image: myregistry/myapp:v1
        ports:
        - containerPort: 8080
  strategy:
    canary:
      # Background analysis runs continuously during rollout
      analysis:
        templates:
        - templateName: continuous-analysis
        startingStep: 1  # Start after first step
        args:
        - name: service-name
          value: my-app
      steps:
      - setWeight: 10
      - pause: {duration: 5m}
      - setWeight: 30
      - pause: {duration: 5m}
      - setWeight: 50
      - pause: {duration: 5m}
      - setWeight: 80
      - pause: {duration: 5m}
---
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: continuous-analysis
spec:
  args:
  - name: service-name
  metrics:
  - name: error-rate
    interval: 1m
    failureLimit: 5
    successCondition: result[0] < 0.05
    provider:
      prometheus:
        address: http://prometheus:9090
        query: |
          sum(rate(http_requests_total{service="{{args.service-name}}",status=~"5.*"}[1m]))
          / sum(rate(http_requests_total{service="{{args.service-name}}"}[1m]))
```

## Canary with Experiment (A/B Testing)

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: canary-experiment
spec:
  replicas: 5
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
        image: myregistry/myapp:v1
        ports:
        - containerPort: 8080
  strategy:
    canary:
      steps:
      - experiment:
          duration: 10m
          templates:
          - name: baseline
            specRef: stable
            replicas: 1
          - name: canary
            specRef: canary
            replicas: 1
          analyses:
          - name: compare
            templateName: ab-test
            args:
            - name: baseline-hash
              valueFrom:
                podTemplateHashValue: Stable
            - name: canary-hash
              valueFrom:
                podTemplateHashValue: Latest
      - setWeight: 50
      - pause: {duration: 5m}
---
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: ab-test
spec:
  args:
  - name: baseline-hash
  - name: canary-hash
  metrics:
  - name: conversion-rate-comparison
    interval: 1m
    count: 10
    successCondition: result[0] >= result[1]
    provider:
      prometheus:
        address: http://prometheus:9090
        query: |
          sum(rate(conversions_total{pod_hash="{{args.canary-hash}}"}[5m]))
          / sum(rate(page_views_total{pod_hash="{{args.canary-hash}}"}[5m]))
```

## Canary with NGINX Ingress

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: canary-nginx
spec:
  replicas: 5
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
        image: myregistry/myapp:v1
        ports:
        - containerPort: 8080
  strategy:
    canary:
      stableService: my-app-stable
      canaryService: my-app-canary
      trafficRouting:
        nginx:
          stableIngress: my-app-ingress
          annotationPrefix: nginx.ingress.kubernetes.io
          additionalIngressAnnotations:
            canary-by-header: X-Canary
            canary-by-header-value: "true"
      steps:
      - setWeight: 10
      - pause: {duration: 2m}
      - setWeight: 30
      - pause: {duration: 2m}
      - setWeight: 50
      - pause: {}
---
apiVersion: v1
kind: Service
metadata:
  name: my-app-stable
spec:
  selector:
    app: my-app
  ports:
  - port: 80
    targetPort: 8080
---
apiVersion: v1
kind: Service
metadata:
  name: my-app-canary
spec:
  selector:
    app: my-app
  ports:
  - port: 80
    targetPort: 8080
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: my-app-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  ingressClassName: nginx
  rules:
  - host: my-app.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: my-app-stable
            port:
              number: 80
```

## ClusterAnalysisTemplate Example

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ClusterAnalysisTemplate
metadata:
  name: org-wide-success-rate
spec:
  args:
  - name: service-name
  - name: namespace
  - name: threshold
    value: "0.95"
  metrics:
  - name: success-rate
    interval: 1m
    count: 5
    successCondition: result[0] >= {{args.threshold}}
    failureLimit: 3
    provider:
      prometheus:
        address: http://prometheus.monitoring:9090
        query: |
          sum(rate(
            http_requests_total{
              service="{{args.service-name}}",
              namespace="{{args.namespace}}",
              status=~"2.*"
            }[5m]
          )) / sum(rate(
            http_requests_total{
              service="{{args.service-name}}",
              namespace="{{args.namespace}}"
            }[5m]
          ))
```

## Using ClusterAnalysisTemplate in Rollout

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: my-rollout
  namespace: production
spec:
  replicas: 5
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
        image: myregistry/myapp:v1
  strategy:
    canary:
      steps:
      - setWeight: 20
      - analysis:
          templates:
          - templateName: org-wide-success-rate
            clusterScope: true  # Reference ClusterAnalysisTemplate
          args:
          - name: service-name
            value: my-app
          - name: namespace
            value: production
          - name: threshold
            value: "0.98"
      - setWeight: 50
      - pause: {duration: 5m}
```

## HPA Integration

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: rollout-with-hpa
spec:
  replicas: 5
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
        image: myregistry/myapp:v1
        resources:
          requests:
            cpu: 100m
            memory: 128Mi
  strategy:
    canary:
      steps:
      - setWeight: 20
      - pause: {duration: 5m}
      - setWeight: 50
      - pause: {duration: 5m}
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: my-app-hpa
spec:
  scaleTargetRef:
    apiVersion: argoproj.io/v1alpha1
    kind: Rollout
    name: rollout-with-hpa
  minReplicas: 3
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```
