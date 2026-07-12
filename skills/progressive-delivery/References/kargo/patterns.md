# Kargo Deployment Patterns Reference

Comprehensive guide to Kargo deployment patterns and architectural approaches.

## 1. Image Updater Pattern

Single Warehouse monitors image repository, produces Freight for each new version.

**Use Case:** Rolling out container image updates across environments.

```yaml
apiVersion: kargo.akuity.io/v1alpha1
kind: Warehouse
metadata:
  name: image-warehouse
  namespace: my-project
spec:
  subscriptions:
  - image:
      repoURL: ghcr.io/example/app
      imageSelectionStrategy: SemVer
      constraint: ^1.0.0
---
apiVersion: kargo.akuity.io/v1alpha1
kind: Stage
metadata:
  name: test
spec:
  requestedFreight:
  - origin:
      kind: Warehouse
      name: image-warehouse
    sources:
      direct: true
  promotionTemplate:
    spec:
      steps:
      - uses: git-clone
        config:
          repoURL: https://github.com/example/repo.git
          checkout:
          - branch: main
            path: ./out
      - uses: kustomize-set-image
        config:
          path: ./out/overlays/test
          images:
          - image: ghcr.io/example/app
            tag: ${{ imageFrom('ghcr.io/example/app').Tag }}
      - uses: git-commit
        config:
          path: ./out
          message: "Update image to ${{ imageFrom('ghcr.io/example/app').Tag }}"
      - uses: git-push
        config:
          path: ./out
          targetBranch: stage/test
      - uses: argocd-update
        config:
          apps:
          - name: app-test
```

## 2. Config Updater Pattern

Warehouse tracks Git commits, stages combine base config with overlays.

**Use Case:** Rolling out configuration changes across environments.

```yaml
apiVersion: kargo.akuity.io/v1alpha1
kind: Warehouse
metadata:
  name: config-warehouse
spec:
  subscriptions:
  - git:
      repoURL: https://github.com/example/config.git
      branch: main
      commitSelectionStrategy: NewestFromBranch
      includePaths:
      - base/
      excludePaths:
      - "*.md"
```

**Critical:** Avoid feedback loops by writing to different branches or excluding output paths.

## 3. Common Case Pattern (Image + Config)

Single Warehouse subscribes to both image AND Git repositories.

**Use Case:** Promoting both application code and configuration together.

```yaml
apiVersion: kargo.akuity.io/v1alpha1
kind: Warehouse
metadata:
  name: combined-warehouse
spec:
  subscriptions:
  - image:
      repoURL: ghcr.io/example/app
      imageSelectionStrategy: SemVer
      constraint: ^1.0.0
  - git:
      repoURL: https://github.com/example/config.git
      branch: main
      includePaths:
      - config/
```

Both artifacts referenced by single Freight, promoted together as a unit.

## 4. Multiple Warehouses Pattern

Separate Warehouses for images and configs with independent promotion cadences.

**Use Case:** When image updates occur frequently but configuration changes are rare.

```yaml
apiVersion: kargo.akuity.io/v1alpha1
kind: Warehouse
metadata:
  name: image-warehouse
spec:
  subscriptions:
  - image:
      repoURL: ghcr.io/example/app
---
apiVersion: kargo.akuity.io/v1alpha1
kind: Warehouse
metadata:
  name: config-warehouse
spec:
  subscriptions:
  - git:
      repoURL: https://github.com/example/config.git
---
apiVersion: kargo.akuity.io/v1alpha1
kind: Stage
metadata:
  name: test
spec:
  requestedFreight:
  - origin:
      kind: Warehouse
      name: image-warehouse
    sources:
      direct: true
  - origin:
      kind: Warehouse
      name: config-warehouse
    sources:
      direct: true
```

## 5. Grouped Services Pattern

Single Warehouse subscribes to multiple repositories for coordinated promotion.

**Use Case:** Microservices that must be deployed together.

```yaml
apiVersion: kargo.akuity.io/v1alpha1
kind: Warehouse
metadata:
  name: microservices-warehouse
spec:
  subscriptions:
  - image:
      repoURL: ghcr.io/example/frontend
      imageSelectionStrategy: SemVer
  - image:
      repoURL: ghcr.io/example/backend
      imageSelectionStrategy: SemVer
  - image:
      repoURL: ghcr.io/example/api-gateway
      imageSelectionStrategy: SemVer
  freightCreationPolicy: Automatic
  freightCreationCriteria:
    expression: |
      imageFrom('ghcr.io/example/frontend').Tag ==
      imageFrom('ghcr.io/example/backend').Tag
```

**Warning:** Avoid over-coupling unrelated repositories.

## 6. Ordered Services Pattern

Deploy services in a specific order.

### Option A: ArgoCD Sync Waves

```yaml
# In manifests
metadata:
  annotations:
    argocd.argoproj.io/sync-wave: "1"  # Database first
---
metadata:
  annotations:
    argocd.argoproj.io/sync-wave: "2"  # Backend second
---
metadata:
  annotations:
    argocd.argoproj.io/sync-wave: "3"  # Frontend last
```

### Option B: Sequential Steps

```yaml
promotionTemplate:
  spec:
    steps:
    - uses: argocd-update
      as: deploy-db
      config:
        apps:
        - name: database
    - uses: argocd-update
      as: deploy-backend
      config:
        apps:
        - name: backend
    - uses: argocd-update
      config:
        apps:
        - name: frontend
```

## 7. Control Flow Stages Pattern

Stages without promotion processes for organization and interaction points.

**Use Case:** De-cluttering pipelines, providing approval gates.

```yaml
apiVersion: kargo.akuity.io/v1alpha1
kind: Stage
metadata:
  name: approval-gate
spec:
  requestedFreight:
  - origin:
      kind: Warehouse
      name: my-warehouse
    sources:
      stages:
      - uat
  # No promotionTemplate - manual approval only
```

## 8. Fanning Out/In Pattern

Non-linear pipelines with branching and convergence.

**Use Case:** A/B testing, parallel validation environments.

```yaml
# Test stage feeds two parallel stages
apiVersion: kargo.akuity.io/v1alpha1
kind: Stage
metadata:
  name: test
spec:
  requestedFreight:
  - origin:
      kind: Warehouse
      name: my-warehouse
    sources:
      direct: true
---
# Parallel stage A
apiVersion: kargo.akuity.io/v1alpha1
kind: Stage
metadata:
  name: variant-a
spec:
  requestedFreight:
  - origin:
      kind: Warehouse
      name: my-warehouse
    sources:
      stages:
      - test
---
# Parallel stage B
apiVersion: kargo.akuity.io/v1alpha1
kind: Stage
metadata:
  name: variant-b
spec:
  requestedFreight:
  - origin:
      kind: Warehouse
      name: my-warehouse
    sources:
      stages:
      - test
---
# Convergence stage
apiVersion: kargo.akuity.io/v1alpha1
kind: Stage
metadata:
  name: production
spec:
  requestedFreight:
  - origin:
      kind: Warehouse
      name: my-warehouse
    sources:
      stages:
      - variant-a
      - variant-b
    availabilityStrategy: All  # Require both variants verified
```

## 9. PR Workflow Pattern

Use pull requests for production promotions.

```yaml
apiVersion: kargo.akuity.io/v1alpha1
kind: PromotionTask
metadata:
  name: pr-promotion
spec:
  vars:
  - name: repo
    value: https://github.com/example/repo.git
  steps:
  - uses: git-clone
    config:
      repoURL: ${{ vars.repo }}
      checkout:
      - branch: main
        path: ./out

  - uses: kustomize-set-image
    config:
      path: ./out
      images:
      - image: ghcr.io/example/app
        tag: ${{ imageFrom('ghcr.io/example/app').Tag }}

  - uses: git-commit
    config:
      path: ./out
      message: "Promote to production: ${{ ctx.freight.displayID }}"

  - uses: git-push
    as: push
    config:
      path: ./out
      generateTargetBranch: true
      provider: github

  - uses: git-open-pr
    as: open-pr
    config:
      repoURL: ${{ vars.repo }}
      sourceBranch: ${{ outputs.push.branch }}
      targetBranch: main
      title: "Promote to production"
      labels:
      - kargo
      - production

  - uses: git-wait-for-pr
    config:
      repoURL: ${{ vars.repo }}
      prNumber: ${{ outputs['open-pr'].pr.id }}
      timeout: 48h
```

## 10. Gatekeeper Stage Pattern

A stage where failures block invalid combinations.

**Use Case:** Automatic filtering of incompatible artifact combinations.

```yaml
apiVersion: kargo.akuity.io/v1alpha1
kind: Stage
metadata:
  name: gatekeeper
spec:
  requestedFreight:
  - origin:
      kind: Warehouse
      name: my-warehouse
    sources:
      direct: true
  promotionTemplate:
    spec:
      steps:
      - uses: http
        config:
          url: https://api.example.com/validate
          method: POST
          body: '{"version": "${{ imageFrom(vars.repo).Tag }}"}'
          successExpression: response.body.valid == true
  verification:
    analysisTemplates:
    - name: compatibility-check
```

Auto-promotion enabled; failures block incompatible Freight from progressing.

## 11. Rendered Configs Pattern

Use `helm template` or `kustomize build` to generate plain YAML.

**Benefits:**

- Improved GitOps agent performance
- Complete visibility of changes in PR reviews
- Simplified debugging

```yaml
promotionTemplate:
  spec:
    steps:
    - uses: git-clone
      config:
        repoURL: ${{ vars.repo }}
        checkout:
        - branch: main
          path: ./src

    - uses: helm-template
      config:
        path: ./src/charts/app
        outPath: ./src/rendered/manifests.yaml
        releaseName: my-app
        namespace: production
        valuesFiles:
        - ./src/values-prod.yaml
        setValues:
        - key: image.tag
          value: ${{ imageFrom(vars.imageRepo).Tag }}

    - uses: git-commit
      config:
        path: ./src
        message: "Render manifests for ${{ ctx.stage }}"

    - uses: git-push
      config:
        path: ./src
        targetBranch: rendered/${{ ctx.stage }}
```

## Repository Layout Patterns

### Helm Chart Layout

```
.
├── Chart.yaml
├── values.yaml
├── templates/
│   ├── deployment.yaml
│   └── service.yaml
└── stages/
    ├── test/values.yaml
    ├── uat/values.yaml
    └── prod/values.yaml
```

### Kustomize Layout

```
.
├── base/
│   ├── kustomization.yaml
│   ├── deployment.yaml
│   └── service.yaml
└── stages/
    ├── test/kustomization.yaml
    ├── uat/kustomization.yaml
    └── prod/kustomization.yaml
```

### Monorepo Layout

```
.
├── guestbook/
│   ├── base/
│   └── stages/
└── portal/
    ├── base/
    └── stages/
```

**Important:** Configure Warehouse path filters for monorepos.

## Storage Options

### Option 1: Stage-Specific Branches (Recommended)

Treat branches as storage, not merge targets.

```yaml
- uses: git-push
  config:
    targetBranch: stage/${{ ctx.stage }}
```

### Option 2: Writing to Main Branch

Separate input and output paths to avoid feedback loops.

```yaml
# Warehouse excludes output
spec:
  subscriptions:
  - git:
      includePaths:
      - src/
      excludePaths:
      - builds/
```

### Option 3: Separate Repository

Write output to different repository entirely.

```yaml
- uses: git-clone
  config:
    repoURL: https://github.com/example/output-repo.git
    checkout:
    - branch: main
      path: ./output
```

## Auto-Promotion Configuration

### Project-Level Policy

```yaml
apiVersion: kargo.akuity.io/v1alpha1
kind: ProjectConfig
metadata:
  name: my-project
spec:
  promotionPolicies:
  - stages:
    - test
    - uat
    autoPromotionEnabled: true
  - stages:
    - prod
    autoPromotionEnabled: false
```

### Pattern-Based Matching

```yaml
promotionPolicies:
- stages:
  - regex:^dev-.*
  autoPromotionEnabled: true
- stages:
  - glob:prod-*
  autoPromotionEnabled: false
```

### Label Selectors

```yaml
promotionPolicies:
- stageSelector:
    matchLabels:
      tier: development
  autoPromotionEnabled: true
```

## Best Practices

1. **Start Simple:** Begin with Image Updater pattern, add complexity as needed
2. **Avoid Feedback Loops:** Use separate branches/paths for input and output
3. **Use Path Filters:** Essential for monorepos to prevent unnecessary Freight
4. **Enable Auto-Promotion Carefully:** Auto-promote to dev/test, manual for prod
5. **Implement Verification:** Add AnalysisTemplates for critical stages
6. **Use Soak Times:** Require minimum duration in pre-prod stages
7. **Document Patterns:** Maintain clear documentation of your pipeline topology
