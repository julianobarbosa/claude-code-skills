---
name: managing-infra
description: Infrastructure patterns for Kubernetes, Terraform, Helm, Kustomize, and GitHub Actions. Use when making K8s architectural decisions, choosing between Helm vs Kustomize, structuring Terraform modules, writing CI/CD workflows, or applying security best practices.
allowed-tools: Read, Bash, Grep, Glob
---

# Infrastructure Patterns

## When to Use What

| Tool               | Use For                                             |
| ------------------ | --------------------------------------------------- |
| **Raw K8s YAML**   | Simple deployments, one-off resources               |
| **Kustomize**      | Environment variations, overlays without templating |
| **Helm**           | Complex apps, third-party charts, heavy templating  |
| **Terraform**      | Cloud resources, infrastructure lifecycle           |
| **GitHub Actions** | CI/CD, automated testing, releases                  |
| **Makefile**       | Build automation, self-documenting targets          |
| **Dockerfile**     | Container builds, multi-stage, multi-arch           |

## Quick Decisions

**Kustomize** when: Simple env differences, readable manifests, patching YAML
**Helm** when: Complex templating, third-party charts, release management

## K8s Security Defaults

Every workload: non-root user, read-only filesystem, no privilege escalation, dropped capabilities, network policies.

## GitHub Actions Patterns

- **CI workflow**: Lint, test, compile on PRs (run on both x86 + ARM)
- **Release workflow**: Multi-arch Docker build on tags (native ARM runners)
- Pin actions by SHA, least-privilege permissions

## References

- [KUBERNETES.md](KUBERNETES.md) - K8s resource patterns
- [TERRAFORM.md](TERRAFORM.md) - Terraform module patterns
- [GITHUB-ACTIONS.md](GITHUB-ACTIONS.md) - CI/CD workflow patterns
- [MAKEFILE.md](MAKEFILE.md) - Build automation patterns
- [DOCKERFILE.md](DOCKERFILE.md) - Container build patterns
- [templates/](templates/) - Ready-to-use templates

## Commands

```bash
kubectl apply -k ./              # Apply kustomize
helm upgrade --install NAME .    # Install/upgrade chart
terraform plan && terraform apply
```

---

## Gotchas

- **Terraform state lock contention**: default 10-min lock timeout; bumped timeout doesn't help if the lock holder hung — force-unlock only after confirming the process is dead.
- **Helm release name reuse on uninstalled-but-not-purged release** fails install with "already exists" — use `--no-hooks` + explicit purge, or never reuse names.
- **Kustomize patches that match nothing silently produce empty diffs** — verify with `kustomize build` after every patch addition.
- **Terraform `for_each` over a computed value forces apply-time count** — can cause spurious re-creation of resources between plans.
- **`helm upgrade --install` on a changed values schema** can silently drop fields that no longer match — diff the rendered output, not just the values file.
- **`kubectl apply --server-side` vs client-side conflicts** when both have been used: client-side last-applied-config can shadow server-side managed fields without error.
