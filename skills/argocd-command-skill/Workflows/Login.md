# Login Workflow

Authenticate to ArgoCD server for the cafehyna-hub cluster.

## Cluster Configuration

| Setting | Value |
|---------|-------|
| **Kubeconfig** | `~/.kube/aks-rg-hypera-cafehyna-hub-config` |
| **ArgoCD Server** | `argocd.cafehyna.com.br` |
| **ArgoCD Namespace** | `argocd` |

## Connection Options

| Mode | Server | Command |
|------|--------|---------|
| **Production** | `argocd.cafehyna.com.br` | `argocd login argocd.cafehyna.com.br --sso` |
| **Port-Forward** | `localhost:8080` | `argocd login localhost:8080 --insecure` |

## Steps

### 1. Production Login (SSO)

```bash
# Set kubeconfig for cafehyna-hub
export KUBECONFIG=~/.kube/aks-rg-hypera-cafehyna-hub-config

# Login with Azure AD SSO
argocd login argocd.cafehyna.com.br --sso

# Verify login
argocd account get-user-info
```

### 2. Port-Forward Login (Development)

```bash
# Start port-forward in background (cafehyna-hub cluster)
kubectl --kubeconfig ~/.kube/aks-rg-hypera-cafehyna-hub-config port-forward svc/argocd-server -n argocd 8080:443 &

# Login with insecure flag (self-signed cert)
argocd login localhost:8080 --insecure

# Get initial admin password (if needed)
kubectl --kubeconfig ~/.kube/aks-rg-hypera-cafehyna-hub-config -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
```

### 3. Token-Based Login

```bash
# Login with auth token
argocd login argocd.cafehyna.com.br --auth-token $ARGOCD_AUTH_TOKEN

# Generate new token
argocd account generate-token
```

## Context Management

```bash
# List available contexts
argocd context

# Switch context
argocd context <context-name>

# Delete context
argocd context --delete <context-name>
```

## Account Management

```bash
# Get current user info
argocd account get-user-info

# List accounts
argocd account list

# Update password
argocd account update-password

# Get account details
argocd account get --account <username>
```

## Logout

```bash
# Logout from current server
argocd logout argocd.cafehyna.com.br

# Relogin (refresh token)
argocd relogin
```

## Troubleshooting

### Certificate Issues
```bash
# Skip TLS verification
argocd login argocd.cafehyna.com.br --insecure

# Use specific CA certificate
argocd login argocd.cafehyna.com.br --certificate-authority /path/to/ca.crt
```

### Connection Issues
```bash
# Check server connectivity
curl -k https://argocd.cafehyna.com.br/api/version

# Check ArgoCD server pod (cafehyna-hub cluster)
kubectl --kubeconfig ~/.kube/aks-rg-hypera-cafehyna-hub-config get pods -n argocd -l app.kubernetes.io/name=argocd-server
```
