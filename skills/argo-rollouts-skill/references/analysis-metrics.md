# Analysis & Metrics Integration

## Overview

Argo Rollouts Analysis system allows automated promotion or rollback decisions based on metrics from various providers.

## Analysis CRDs

### AnalysisTemplate

Namespace-scoped template defining metrics and success criteria.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: success-rate
spec:
  args:
  - name: service-name
  metrics:
  - name: success-rate
    interval: 1m
    count: 5
    successCondition: result[0] >= 0.95
    failureLimit: 3
    provider:
      prometheus:
        address: http://prometheus.monitoring:9090
        query: |
          sum(rate(
            http_requests_total{service="{{args.service-name}}",status=~"2.*"}[5m]
          )) / sum(rate(
            http_requests_total{service="{{args.service-name}}"}[5m]
          ))
```

### ClusterAnalysisTemplate

Cluster-scoped version for organization-wide templates.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ClusterAnalysisTemplate
metadata:
  name: global-success-rate
spec:
  args:
  - name: service-name
  - name: namespace
  metrics:
  - name: success-rate
    successCondition: result[0] >= 0.95
    provider:
      prometheus:
        address: http://prometheus.monitoring:9090
        query: |
          sum(rate(
            http_requests_total{service="{{args.service-name}}",namespace="{{args.namespace}}"}[5m]
          ))
```

### AnalysisRun

Instantiated analysis (created automatically by Rollouts).

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisRun
metadata:
  name: my-rollout-abc123-1
spec:
  args:
  - name: service-name
    value: my-service
  metrics:
  - name: success-rate
    # ... copied from template
```

## Metric Configuration

### Common Metric Fields

| Field | Type | Description |
|-------|------|-------------|
| `name` | string | Metric identifier |
| `interval` | duration | Time between measurements |
| `count` | int | Total measurements to take |
| `successCondition` | string | Expr that must be true for success |
| `failureCondition` | string | Expr that must be true for failure |
| `failureLimit` | int | Max failures before analysis fails |
| `inconclusiveLimit` | int | Max inconclusive before fail |
| `consecutiveErrorLimit` | int | Max consecutive errors |
| `initialDelay` | duration | Delay before first measurement |

### Success/Failure Conditions

```yaml
# Numeric comparison
successCondition: result[0] >= 0.95

# Boolean result
successCondition: result[0] == true

# Multiple conditions
successCondition: result[0] >= 0.95 && result[1] < 500

# Array access (for multiple values)
successCondition: result[0] >= 0.90 && result[1] >= 0.95

# Failure condition
failureCondition: result[0] < 0.80
```

## Metric Providers

### Prometheus

```yaml
provider:
  prometheus:
    address: http://prometheus.monitoring:9090
    timeout: 30
    insecure: false
    headers:
    - key: Authorization
      value: Bearer token
    query: |
      sum(rate(http_requests_total{status=~"5.*"}[5m]))
      / sum(rate(http_requests_total[5m])) * 100
```

### Datadog

> **Credentials**: Datadog requires `DD_API_KEY` and `DD_APP_KEY` configured via a Kubernetes Secret
> referenced in the argo-rollouts controller deployment, or set as environment variables.

```yaml
provider:
  datadog:
    interval: 5m
    query: avg:kubernetes.cpu.usage{service:{{args.service-name}}}
    apiVersion: v2
```

### New Relic

> **Profiles**: New Relic profiles are configured in a ConfigMap (`argo-rollouts-config`) with
> `personal-api-key` and `account-id`. The `profile` field references a named configuration.

```yaml
provider:
  newRelic:
    profile: default
    query: |
      SELECT average(duration)
      FROM Transaction
      WHERE appName = '{{args.service-name}}'
```

### CloudWatch

> **IAM Permissions**: The argo-rollouts controller needs IAM permissions for `cloudwatch:GetMetricData`.
> Use IRSA (IAM Roles for Service Accounts) or node instance profiles.

```yaml
provider:
  cloudWatch:
    interval: 5m
    metricDataQueries:
    - id: errors
      expression: "errors / requests * 100"
      label: "Error Rate"
    - id: errors
      metricStat:
        metric:
          namespace: AWS/ApplicationELB
          metricName: HTTPCode_Target_5XX_Count
          dimensions:
          - name: LoadBalancer
            value: "{{args.alb-name}}"
        period: 300
        stat: Sum
```

### Wavefront

```yaml
provider:
  wavefront:
    address: https://company.wavefront.com
    query: |
      mavg(5m, sum(rate(ts("requests.errors", service="{{args.service-name}}"))))
```

### Kayenta (Automated Canary Analysis)

```yaml
provider:
  kayenta:
    address: https://kayenta.example.com
    application: my-app
    canaryConfigName: my-canary-config
    metricsAccountName: prometheus
    configurationAccountName: s3
    storageAccountName: s3
    threshold:
      pass: 95
      marginal: 75
    scopes:
    - name: default
      controlScope:
        scope: baseline
        region: us-west-2
      experimentScope:
        scope: canary
        region: us-west-2
```

### Web (HTTP)

> ⚠️ **Security Warning**: The Web provider makes HTTP requests to the specified URL.
> Never use user-controlled input for URLs. Ensure proper network policies to prevent SSRF attacks.
> Always validate and sanitize any templated arguments used in URLs.

```yaml
provider:
  web:
    url: "http://my-service.default.svc/health"
    method: GET
    headers:
    - key: Authorization
      value: "Bearer {{args.token}}"
    timeoutSeconds: 30
    jsonPath: "{$.status}"
```

### Job (Kubernetes Job)

```yaml
provider:
  job:
    metadata:
      generateName: load-test-
    spec:
      backoffLimit: 1
      template:
        spec:
          containers:
          - name: load-test
            image: grafana/k6
            args: ["run", "/scripts/test.js"]
          restartPolicy: Never
```

## Using Analysis in Rollouts

### Inline Analysis (Canary Step)

```yaml
spec:
  strategy:
    canary:
      steps:
      - setWeight: 20
      - pause: {duration: 5m}
      - analysis:
          templates:
          - templateName: success-rate
          args:
          - name: service-name
            value: my-service
      - setWeight: 50
```

### Background Analysis (Continuous)

```yaml
spec:
  strategy:
    canary:
      analysis:
        templates:
        - templateName: continuous-success-rate
        startingStep: 2
        args:
        - name: service-name
          value: my-service
      steps:
      - setWeight: 20
      - pause: {duration: 2m}
      - setWeight: 50
      - pause: {duration: 2m}
```

### Pre-Promotion Analysis (Blue-Green)

```yaml
spec:
  strategy:
    blueGreen:
      activeService: my-app-active
      previewService: my-app-preview
      prePromotionAnalysis:
        templates:
        - templateName: smoke-test
        - templateName: load-test
        args:
        - name: preview-url
          value: http://my-app-preview
```

### Post-Promotion Analysis

```yaml
spec:
  strategy:
    blueGreen:
      postPromotionAnalysis:
        templates:
        - templateName: post-deploy-health
```

## Common AnalysisTemplates

### HTTP Success Rate (Prometheus)

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: http-success-rate
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
        address: http://prometheus:9090
        query: |
          sum(rate(
            http_requests_total{service="{{args.service-name}}",code=~"2.*"}[5m]
          )) / sum(rate(
            http_requests_total{service="{{args.service-name}}"}[5m]
          ))
```

### Latency Check (Prometheus)

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: latency-check
spec:
  args:
  - name: service-name
  - name: latency-threshold
    value: "500"
  metrics:
  - name: p99-latency
    interval: 1m
    count: 5
    successCondition: result[0] < {{args.latency-threshold}}
    provider:
      prometheus:
        address: http://prometheus:9090
        query: |
          histogram_quantile(0.99, sum(rate(
            http_request_duration_seconds_bucket{service="{{args.service-name}}"}[5m]
          )) by (le)) * 1000
```

### Error Rate Check

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: error-rate
spec:
  args:
  - name: service-name
  - name: max-error-rate
    value: "0.05"
  metrics:
  - name: error-rate
    interval: 1m
    count: 5
    successCondition: result[0] <= {{args.max-error-rate}}
    failureLimit: 2
    provider:
      prometheus:
        address: http://prometheus:9090
        query: |
          sum(rate(
            http_requests_total{service="{{args.service-name}}",code=~"5.*"}[5m]
          )) / sum(rate(
            http_requests_total{service="{{args.service-name}}"}[5m]
          ))
```

### Health Check (Web)

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: health-check
spec:
  args:
  - name: host
  metrics:
  - name: health
    interval: 30s
    count: 10
    successCondition: result == "healthy"
    failureLimit: 3
    provider:
      web:
        url: "http://{{args.host}}/health"
        jsonPath: "{$.status}"
```

## Dry-Run Analysis

Test analysis without affecting rollout:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: AnalysisRun
metadata:
  name: test-analysis
spec:
  metrics:
  - name: test-success-rate
    provider:
      prometheus:
        address: http://prometheus:9090
        query: |
          sum(rate(http_requests_total{status="200"}[5m]))
    successCondition: result[0] > 100
    count: 1
  dryRun:
  - metricName: test-success-rate
```

## Troubleshooting Analysis

### Check AnalysisRun Status

```bash
# List analysis runs
kubectl argo rollouts list analysisruns

# Get specific run
kubectl argo rollouts get analysisrun <name>

# Check measurements
kubectl get analysisrun <name> -o jsonpath='{.status.metricResults}'
```

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Analysis timeout | Query too slow | Increase timeout, optimize query |
| Empty result | Query returns no data | Verify metric exists, check labels |
| Auth failure | Missing credentials | Add secret reference to provider |
| Inconclusive | Neither pass nor fail | Add failureCondition |
