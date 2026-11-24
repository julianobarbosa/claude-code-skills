# Infra review lens

Runs when `ship-preflight.ts` prints `review_required=true`: the change touches IaC,
Kubernetes/Helm manifests or GitOps objects (`review_files=` lists them). It happens after
the push and before `ship-pr.ts`. A blocking finding stops the PR until it is fixed or the
user explicitly ships over it, in which case the finding goes into the PR body.

## Who reviews

A reviewer from a different model family from the one that wrote the change, in read-only
mode and with a fresh context: it reads the diff and the repo, never this conversation.
Its own build is never its own audit. If no other family is available, use a fresh
same-family agent in read-only audit mode and say so in the PR body.

## The brief (hand this over with the diff range and `review_files`)

> Adversarially review `git diff <remote>/<target>...HEAD` in this repo. Report **blocking
> issues only**: a change that, merged and applied as-is, breaks a running workload,
> widens exposure, or fails to deploy. Each finding gives `file:line`, what breaks, and the
> evidence you read (the file or object that proves it). Style, naming and "consider"
> notes are out of scope. If nothing blocks, say `no blocking issues` and list what you
> checked.
>
> At minimum, establish for this diff:
>
> 1. **Cross-environment exposure.** Nothing grants one environment, spoke, tenant or
>    cluster reach into another, or into prod: network rules, firewall/NSG entries,
>    private endpoints, peering, RBAC scopes, shared identities, DNS. A rule scoped wider
>    than the workload that needs it counts.
> 2. **GitOps admission.** Every resource kind, namespace, destination and source repo
>    the change introduces is permitted by its ArgoCD `AppProject` (or equivalent)
>    whitelists, so the sync will not be refused.
> 3. **Config contract.** Every config key, env var, secret key, mounted file or
>    ConfigMap/Secret entry the running app reads is still provided after the change,
>    under the same name and shape. A rename, removal or move that the app's code or chart
>    still references counts.
> 4. **Destructive plans.** No stateful resource (database, storage, key vault, volume,
>    cluster) is replaced or destroyed by an attribute change that forces a new resource.
> 5. **Secret material.** No credential, key or token is committed in plain text. Auth
>    stays keyless where the repo already is.

## Reading the result

- `no blocking issues`: continue to `ship-pr.ts`.
- Any blocking finding: surface it to the user verbatim with its evidence, and do not open
  the PR. A "fix" from the user licenses fixing every listed finding, then re-running the
  review on the new diff.
- The repo's own `CLAUDE.md` / `AGENTS.md` may add checks for its platform. Append them to
  the brief; never drop the five above.
