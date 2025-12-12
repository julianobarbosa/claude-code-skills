# DefectDojo Troubleshooting Guide

## Authentication Issues

### Azure AD SSO Login Fails

#### Error: ADSTS50011 - Redirect URI Mismatch

**Error Message:**

```
ADSTS50011: The redirect URI 'http://xxxxx/azuread-tenant-oauth2/' specified in the request does not match
```

**Cause:** Azure AD requires HTTPS but DefectDojo is sending HTTP redirect URI

**Solutions:**

1. **Verify Azure AD Redirect URI:**
   - Must be exactly: `https://defectdojo.dev.cafehyna.com.br/complete/azuread-tenant-oauth2/`
   - Note the `/complete/` in the path

2. **Set SSL Environment Variables:**

   ```yaml
   extraEnv:
     - name: DD_SESSION_COOKIE_SECURE
       value: "True"
     - name: DD_CSRF_COOKIE_SECURE
       value: "True"
     - name: DD_SECURE_PROXY_SSL_HEADER
       value: "True"
   ```

3. **Restart pods after changes:**

   ```bash
   KUBECONFIG=~/.kube/aks-rg-hypera-cafehyna-dev-config \
     kubectl rollout restart deployment/defectdojo-django -n defectdojo
   ```

#### Error: ERR_TOO_MANY_REDIRECTS

**Cause:** `DD_SECURE_SSL_REDIRECT=True` behind TLS-terminating proxy causes infinite redirect loop

**Solution:**

```yaml
# Set to False when behind NGINX Ingress (it handles SSL redirect)
- name: DD_SECURE_SSL_REDIRECT
  value: "False"
```

#### User Locked Out / SSO Broken

**Emergency Access:**
Navigate to: `https://defectdojo.dev.cafehyna.com.br/login?force_login_form`

This bypasses SSO redirect and shows standard username/password login.

---

## Group Synchronization Issues

### Groups Not Syncing from Azure AD

**Symptoms:**

- User logs in via Azure AD
- User profile shows "No group members found"
- User doesn't have expected permissions

**Diagnostic Steps:**

1. **Check Configuration:**

   ```bash
   KUBECONFIG=~/.kube/aks-rg-hypera-cafehyna-dev-config \
     kubectl get deployment defectdojo-django -n defectdojo -o yaml | \
     grep -A1 "DD_SOCIAL_AUTH_AZUREAD_TENANT_OAUTH2_GET_GROUPS"
   ```

   Should show `value: "True"`

2. **Check Azure AD API Permissions:**
   - Go to Azure Portal > App Registrations > DefectDojo > API Permissions
   - Verify `Group.Read.All` is listed as **Application** permission
   - Verify "Admin consent granted" shows green checkmark

3. **Check Azure AD Token Configuration:**
   - Go to Token configuration
   - Verify "Groups claim" is added
   - Verify "Emit groups as role claims" is **NOT** enabled

4. **Check Pod Logs for Graph API Errors:**

   ```bash
   KUBECONFIG=~/.kube/aks-rg-hypera-cafehyna-dev-config \
     kubectl logs -n defectdojo -l app.kubernetes.io/name=defectdojo -c uwsgi | \
     grep -i "graph\|group\|403"
   ```

**Solutions:**

1. **Grant API Permissions:**
   - Add `Group.Read.All` (Application type)
   - Add `GroupMember.Read.All` (Application type)
   - Click "Grant admin consent"

2. **Fix Token Configuration:**
   - Add Groups claim if missing
   - Disable "Emit groups as role claims"

3. **Create Matching Groups in DefectDojo:**
   - Go to Configuration > Groups
   - Create group with exact Azure AD group name
   - Assign Global Role

4. **User Must Re-login:**
   - Groups sync only at login time
   - User must log out and log back in

### Error: 403 Forbidden from Microsoft Graph API

**Cause:** Missing or incorrect API permissions

**Check Current Permissions:**

```bash
az ad app show --id 79ada8c7-4270-41e8-9ea0-1e1e62afff3d \
  --query "requiredResourceAccess" -o json
```

**Solution:**

1. Go to Azure AD > App Registration > API Permissions
2. Add `Group.Read.All` as **Application** permission (not Delegated)
3. Click "Grant admin consent for [tenant]"
4. Wait 5-10 minutes for propagation
5. Restart DefectDojo pods

---

## CSRF Issues

### Error: "CSRF verification failed"

**Symptoms:** 403 error after form submission

**Common Causes:**

1. **Missing CSRF Trusted Origins:**

   ```yaml
   - name: DD_CSRF_TRUSTED_ORIGINS
     value: https://defectdojo.dev.cafehyna.com.br
   ```

2. **Stale CSRF Cookie:**
   - Clear browser cookies
   - Use incognito/private window

3. **Proxy Not Forwarding Headers:**

   ```yaml
   # Trust X-Forwarded-Proto header
   - name: DD_SECURE_PROXY_SSL_HEADER
     value: "True"
   ```

---

## Pod/Container Issues

### Pods Stuck in ContainerCreating

**Check Events:**

```bash
KUBECONFIG=~/.kube/aks-rg-hypera-cafehyna-dev-config \
  kubectl describe pod -n defectdojo -l app.kubernetes.io/name=defectdojo | tail -20
```

**Common Causes:**

1. **CSI Driver Secret Mount Failure:**
   - Check SecretProviderClass exists
   - Verify Key Vault permissions

2. **PVC Not Bound:**

   ```bash
   KUBECONFIG=~/.kube/aks-rg-hypera-cafehyna-dev-config \
     kubectl get pvc -n defectdojo
   ```

3. **Node Scheduling Issues:**
   - Check tolerations match node taints
   - Verify nodeSelector/affinity

### Pods CrashLoopBackOff

**Check Logs:**

```bash
KUBECONFIG=~/.kube/aks-rg-hypera-cafehyna-dev-config \
  kubectl logs -n defectdojo -l app.kubernetes.io/name=defectdojo -c uwsgi --previous
```

**Common Causes:**

1. **Database Connection Failed:**
   - Check PostgreSQL pod is running
   - Verify database credentials

2. **Redis Connection Failed:**
   - Check Redis pod is running
   - Verify Redis password

3. **Missing Environment Variables:**
   - Check all required secrets exist

### Liveness/Readiness Probe Failures

**Symptoms:** Pod restarts frequently

**Solutions:**

1. **Increase Initial Delay:**

   ```yaml
   django:
     uwsgi:
       livenessProbe:
         initialDelaySeconds: 180
       readinessProbe:
         initialDelaySeconds: 120
   ```

2. **Check Resource Limits:**
   - Pod may be OOMKilled
   - Increase memory limits

---

## Database Issues

### Database Migration Failures

**Check Migration Status:**

```bash
KUBECONFIG=~/.kube/aks-rg-hypera-cafehyna-dev-config \
  kubectl logs -n defectdojo -l app.kubernetes.io/component=initializer
```

**Solutions:**

1. **Run Migrations Manually:**

   ```bash
   KUBECONFIG=~/.kube/aks-rg-hypera-cafehyna-dev-config \
     kubectl exec -it -n defectdojo deployment/defectdojo-django -c uwsgi -- \
     python manage.py migrate
   ```

2. **Check Database Connectivity:**

   ```bash
   KUBECONFIG=~/.kube/aks-rg-hypera-cafehyna-dev-config \
     kubectl exec -it -n defectdojo deployment/defectdojo-django -c uwsgi -- \
     python manage.py dbshell
   ```

---

## Secrets Issues

### Kubernetes Secret Not Created

**Symptoms:** Secret referenced but doesn't exist

**Cause:** CSI driver only creates secrets when a pod mounts the volume

**Solution:**

1. Verify `secret-sync-pod` is running
2. Check SecretProviderClass is correctly configured
3. Pod must mount the CSI volume for secrets to sync

**Check Secret Sync Pod:**

```bash
KUBECONFIG=~/.kube/aks-rg-hypera-cafehyna-dev-config \
  kubectl get pods -n defectdojo | grep secret-sync
```

### Key Vault 403 Forbidden

**Check Managed Identity Permissions:**

```bash
az keyvault show --name kv-cafehyna-dev-hlg --query "properties.accessPolicies"
```

**Grant Permissions:**

```bash
az keyvault set-policy \
  --name kv-cafehyna-dev-hlg \
  --object-id <managed-identity-object-id> \
  --secret-permissions get list
```

---

## ArgoCD Sync Issues

### App Out of Sync

**Common Causes:**

1. **Job podReplacementPolicy Field:**
   - Already handled in ApplicationSet with `ignoreDifferences`

2. **Replica Count Drift:**
   - HPA changes replica counts
   - Handled with `ignoreDifferences`

### Sync Failed

**Check ArgoCD Logs:**

```bash
kubectl logs -n argocd -l app.kubernetes.io/name=argocd-application-controller
```

**Manual Sync:**

```bash
argocd app sync cafehyna-dev-defectdojo
```

---

## Useful Diagnostic Commands

### Overall Health Check

```bash
# Pod status
KUBECONFIG=~/.kube/aks-rg-hypera-cafehyna-dev-config \
  kubectl get pods -n defectdojo

# Recent events
KUBECONFIG=~/.kube/aks-rg-hypera-cafehyna-dev-config \
  kubectl get events -n defectdojo --sort-by='.lastTimestamp' | tail -20

# Secret status
KUBECONFIG=~/.kube/aks-rg-hypera-cafehyna-dev-config \
  kubectl get secrets -n defectdojo

# PVC status
KUBECONFIG=~/.kube/aks-rg-hypera-cafehyna-dev-config \
  kubectl get pvc -n defectdojo
```

### Application Logs

```bash
# Django/uWSGI logs
KUBECONFIG=~/.kube/aks-rg-hypera-cafehyna-dev-config \
  kubectl logs -n defectdojo -l app.kubernetes.io/name=defectdojo -c uwsgi -f

# Celery worker logs
KUBECONFIG=~/.kube/aks-rg-hypera-cafehyna-dev-config \
  kubectl logs -n defectdojo -l app.kubernetes.io/component=celery-worker -f

# Celery beat logs
KUBECONFIG=~/.kube/aks-rg-hypera-cafehyna-dev-config \
  kubectl logs -n defectdojo -l app.kubernetes.io/component=celery-beat -f
```

### Restart Services

```bash
# Restart Django
KUBECONFIG=~/.kube/aks-rg-hypera-cafehyna-dev-config \
  kubectl rollout restart deployment/defectdojo-django -n defectdojo

# Restart all components
KUBECONFIG=~/.kube/aks-rg-hypera-cafehyna-dev-config \
  kubectl rollout restart deployment -n defectdojo
```
