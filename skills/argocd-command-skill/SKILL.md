---
name: ArgoCdCommand
description: ArgoCD CLI interaction for cafehyna-hub cluster. USE WHEN managing ArgoCD applications OR applicationsets OR syncing OR deploying OR checking app status OR managing clusters/repos/projects via argocd CLI at argocd.cafehyna.com.br or localhost:8080.
---

# ArgoCdCommand

Complete ArgoCD CLI interaction skill for the `cafehyna-hub` cluster at `argocd.cafehyna.com.br` or via port-forward at `localhost:8080`.

## Cluster Configuration

| Setting | Value |
|---------|-------|
| **Kubeconfig** | `~/.kube/aks-rg-hypera-cafehyna-hub-config` |
| **ArgoCD Server** | `argocd.cafehyna.com.br` |
| **ArgoCD Namespace** | `argocd` |
| **Port-Forward** | `localhost:8080` |

### Environment Setup

```bash
# Set kubeconfig for cafehyna-hub
export KUBECONFIG=~/.kube/aks-rg-hypera-cafehyna-hub-config

# Or use --kubeconfig flag
kubectl --kubeconfig ~/.kube/aks-rg-hypera-cafehyna-hub-config get pods -n argocd
```

### Aliases (Recommended)

```bash
# Add to ~/.bashrc or ~/.zshrc
alias k-hub='kubectl --kubeconfig ~/.kube/aks-rg-hypera-cafehyna-hub-config'
alias argocd-hub='KUBECONFIG=~/.kube/aks-rg-hypera-cafehyna-hub-config argocd'
```

## Connection Modes

| Mode | Server | Use Case |
|------|--------|----------|
| **Production** | `argocd.cafehyna.com.br` | Direct access to ArgoCD |
| **Port-Forward** | `localhost:8080` | Local development/debugging |

## Workflow Routing

| Workflow | Trigger | File |
|----------|---------|------|
| **Login** | "login to argocd", "authenticate" | `Workflows/Login.md` |
| **AppManage** | "create app", "delete app", "sync app", "app status" | `Workflows/AppManage.md` |
| **AppSetManage** | "create applicationset", "appset", "generate apps" | `Workflows/AppSetManage.md` |
| **ClusterManage** | "add cluster", "list clusters", "remove cluster" | `Workflows/ClusterManage.md` |
| **RepoManage** | "add repo", "list repos", "remove repository" | `Workflows/RepoManage.md` |
| **ProjectManage** | "create project", "list projects", "project settings" | `Workflows/ProjectManage.md` |
| **Troubleshoot** | "app logs", "diff", "rollback", "history" | `Workflows/Troubleshoot.md` |

## Quick Reference

### Authentication
```bash
# Login to production (with kubeconfig set)
export KUBECONFIG=~/.kube/aks-rg-hypera-cafehyna-hub-config
argocd login argocd.cafehyna.com.br --sso

# Login via port-forward
kubectl --kubeconfig ~/.kube/aks-rg-hypera-cafehyna-hub-config port-forward svc/argocd-server -n argocd 8080:443 &
argocd login localhost:8080 --insecure
```

### Common Operations
```bash
# List applications
argocd app list

# Sync application
argocd app sync <app-name>

# Get app details
argocd app get <app-name>

# List applicationsets
argocd appset list
```

### kubectl Commands (cafehyna-hub)
```bash
# Get ArgoCD pods
kubectl --kubeconfig ~/.kube/aks-rg-hypera-cafehyna-hub-config get pods -n argocd

# Get applications (CRD)
kubectl --kubeconfig ~/.kube/aks-rg-hypera-cafehyna-hub-config get applications -n argocd

# Get applicationsets (CRD)
kubectl --kubeconfig ~/.kube/aks-rg-hypera-cafehyna-hub-config get applicationsets -n argocd

# Get ArgoCD server logs
kubectl --kubeconfig ~/.kube/aks-rg-hypera-cafehyna-hub-config logs -n argocd -l app.kubernetes.io/name=argocd-server -f
```

## Tools

| Tool | Purpose | File |
|------|---------|------|
| **ArgoCdCli** | Execute argocd commands with connection handling | `Tools/ArgoCdCli.ts` |

## Examples

**Example 1: Sync an application**
```
User: "Sync the grafana application in ArgoCD"
→ Invokes AppManage workflow
→ Runs: argocd app sync grafana
→ Reports sync status and health
```

**Example 2: Create ApplicationSet**
```
User: "Create an applicationset for the monitoring stack"
→ Invokes AppSetManage workflow
→ Guides through appset creation with multi-source pattern
→ Applies via: argocd appset create -f appset.yaml
```

**Example 3: Check application logs**
```
User: "Show me logs for the failing defectdojo app"
→ Invokes Troubleshoot workflow
→ Runs: argocd app logs defectdojo --follow
→ Displays pod logs for debugging
```

**Example 4: Add new cluster**
```
User: "Register the new dev cluster with ArgoCD"
→ Invokes ClusterManage workflow
→ Runs: argocd cluster add <context-name>
→ Confirms cluster registration
```
