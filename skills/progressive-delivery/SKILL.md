---
name: progressive-delivery
description: Progressive delivery on Kubernetes — canary and blue-green deployments via Argo Rollouts, plus environment-to-environment promotion via Kargo. USE WHEN implementing canary releases, blue-green deployments, traffic shifting between revisions, metric-gated promotions, AnalysisTemplate/AnalysisRun design, Argo Rollouts CRDs, or Kargo freight/warehouse/stage promotion pipelines, multi-stage promotion across dev/staging/prod, ArgoCD+Kargo integration. Rollouts handles WHICH revision serves traffic; Kargo handles WHICH revision is in which environment. Use both together when you need both deployment strategy AND multi-environment promotion.
---

# Progressive Delivery

Two complementary tools for moving versions safely through Kubernetes environments:

- **Argo Rollouts** — replaces `Deployment` with a `Rollout` CRD that supports canary, blue-green, and metric-gated automated analysis. Handles traffic shaping at the cluster/service-mesh layer.
- **Kargo** — extends GitOps with promotion logic. Tracks `Freight` (versioned bundles of artifacts) and promotes it through `Stages` (dev → staging → prod) via `Warehouses` (sources) and verification steps.

ArgoCD continues to do what it does (sync desired state → cluster). Rollouts decides traffic split during a single deploy. Kargo decides when the next stage gets the new version.

## Scope routing

| If you need to… | Read |
|---|---|
| Canary / blue-green / metric-gated deploy of a single workload | `References/argo-rollouts.md` + `References/argo-rollouts/` |
| Promote a version across dev → stg → prod with manual or automated gates | `References/kargo.md` + `References/kargo/` |
| Both (Rollouts as the deploy strategy inside a Kargo-managed promotion) | Read both; Kargo invokes ArgoCD which deploys a Rollout |

## Mental model

```
Kargo:    Freight v1.2.3 -> [dev stage] -> verify -> [stg stage] -> verify -> [prod stage]
                                                                              |
                                                                              v
ArgoCD:                                                                   syncs Rollout manifest
                                                                              |
                                                                              v
Rollouts:                                                          canary @ 10% -> analysis -> 50% -> 100%
```

## When NOT to use

- Simple `Deployment` rollouts that don't need traffic shaping or analysis gates — vanilla Kubernetes Deployments are fine.
- Manual promotion via PRs editing target revision — that's the core `argocd` skill, not this one.
- Feature flags and runtime percentage rollouts inside the app — that's an application concern (LaunchDarkly, Unleash, etc.), not a deployment one.

## Gotchas

- **Rollouts replaces Deployment; it is not an addition.** Migrating an existing app means changing the resource kind. Plan for one revision of downtime if not handled with kubectl-argo-rollouts conversion.
- **AnalysisTemplate metrics queries are scoped to the Rollouts controller's permissions.** If your Prometheus is in another namespace, the controller needs RBAC or a service-account token.
- **Kargo Freight is immutable.** Once produced, you don't edit it — you produce new Freight. Trying to "patch" a Stage's current Freight is an anti-pattern.
- **Kargo + ArgoCD integration requires Kargo's controller to have permission to update ArgoCD `Application` CRs.** Default install doesn't grant this — read the Helm values for `argocd.permissions`.
- **Verification steps run between stages, not within them.** A failing verification doesn't roll back the prior stage — it just blocks promotion forward. If you need rollback, that's a separate Rollouts-level analysis.
