# Argo Rollouts Summary

## Overview

Argo Rollouts is a Kubernetes controller and set of CRDs that provides advanced deployment capabilities including:

- **Blue-Green Deployments**: Instant traffic switching between versions
- **Canary Deployments**: Gradual traffic shifting with configurable steps
- **Progressive Delivery**: Automated analysis and promotion/rollback
- **Traffic Management**: Native integration with service meshes and ingress controllers
- **Experimentation**: A/B testing with multiple ReplicaSets

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  Argo Rollouts Controller                │
├─────────────────────────────────────────────────────────┤
│  Rollout CRD    │  AnalysisTemplate  │  Experiment CRD  │
│  (replaces      │  (defines metrics  │  (A/B testing    │
│   Deployment)   │   for analysis)    │   workloads)     │
├─────────────────────────────────────────────────────────┤
│              Traffic Management Layer                    │
│  ┌─────────┬─────────┬─────────┬─────────┬──────────┐  │
│  │  Istio  │  NGINX  │   ALB   │ Traefik │ Linkerd  │  │
│  └─────────┴─────────┴─────────┴─────────┴──────────┘  │
├─────────────────────────────────────────────────────────┤
│              Analysis & Metrics Providers               │
│  ┌──────────┬─────────┬──────────┬──────────────────┐  │
│  │Prometheus│ Datadog │ Wavefront│ CloudWatch/NewRelic│  │
│  └──────────┴─────────┴──────────┴──────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Core CRDs

| CRD | Purpose | Scope |
|-----|---------|-------|
| **Rollout** | Replaces Deployment, adds progressive delivery | Namespaced |
| **AnalysisTemplate** | Defines metric queries for automated analysis | Namespaced |
| **ClusterAnalysisTemplate** | Cluster-wide AnalysisTemplate | Cluster |
| **AnalysisRun** | Instantiated analysis execution | Namespaced |
| **Experiment** | Runs multiple ReplicaSets for A/B testing | Namespaced |

## Key Features

### 1. Progressive Delivery

- Gradual rollout with configurable weight steps
- Automatic promotion based on metrics
- Automated rollback on failure detection

### 2. Traffic Management Integration

- Native integration with Istio VirtualService
- NGINX Ingress Controller support
- AWS ALB Ingress Controller
- Ambassador, Traefik, Linkerd, SMI support

### 3. Metrics-Based Analysis

- Query metrics from multiple providers
- Define success criteria and thresholds
- Automated pass/fail decisions

### 4. Rollout Strategies

- **Canary**: Gradual traffic shifting (1% → 5% → 20% → 100%)
- **Blue-Green**: Instant switch with preview environment
- **Hybrid**: Combine strategies with analysis gates

## Installation

```bash
# Install Argo Rollouts controller
kubectl create namespace argo-rollouts
kubectl apply -n argo-rollouts -f https://github.com/argoproj/argo-rollouts/releases/latest/download/install.yaml

# Install kubectl plugin
brew install argoproj/tap/kubectl-argo-rollouts
# or
curl -LO https://github.com/argoproj/argo-rollouts/releases/latest/download/kubectl-argo-rollouts-darwin-amd64
chmod +x kubectl-argo-rollouts-darwin-amd64
sudo mv kubectl-argo-rollouts-darwin-amd64 /usr/local/bin/kubectl-argo-rollouts
```

## How It Works

1. **Rollout Created**: Controller creates initial ReplicaSet
2. **Update Triggered**: New ReplicaSet created with updated spec
3. **Traffic Shifted**: Based on strategy (canary weights or blue-green switch)
4. **Analysis Runs**: Metrics queried against defined thresholds
5. **Promotion/Rollback**: Automatic decision based on analysis results

## Comparison with Kubernetes Deployment

| Feature | Deployment | Rollout |
|---------|------------|---------|
| Rolling Updates | ✅ | ✅ |
| Blue-Green | ❌ | ✅ |
| Canary | ❌ | ✅ |
| Traffic Management | ❌ | ✅ |
| Automated Analysis | ❌ | ✅ |
| Pause/Resume | ❌ | ✅ |
| Automated Rollback | ❌ | ✅ |

## When to Use Argo Rollouts

**Good fit when:**

- Need gradual rollouts with traffic control
- Want automated canary analysis
- Require instant rollback capability
- Using service mesh for traffic management
- Need A/B testing capabilities

**May not need if:**

- Simple rolling updates are sufficient
- No service mesh or advanced ingress
- Don't require metrics-based promotion
