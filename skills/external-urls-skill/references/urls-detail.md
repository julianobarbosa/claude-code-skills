# External URLs - Detailed Reference

Extended information with source file locations and configuration details.

---

## Application URLs - Complete Reference

### ArgoCD

| Property | Value |
|----------|-------|
| **URL** | `https://argocd.cafehyna.com.br` |
| **Environment** | Hub |
| **Namespace** | `argocd` |
| **Ingress Class** | nginx |
| **TLS Secret** | `argocd-server-tls` |
| **ClusterIssuer** | `letsencrypt-prod` |
| **Config File** | `argo-cd-helm-values/kube-addons/argocd/hub/values.yaml` |

**API Endpoints:**

```
GET  https://argocd.cafehyna.com.br/api/v1/applications
POST https://argocd.cafehyna.com.br/api/v1/applications/{name}/sync
GET  https://argocd.cafehyna.com.br/api/v1/clusters
```

---

### Sentry

**Hub Environment:**

| Property | Value |
|----------|-------|
| **URL** | `https://sentry-hub.cafehyna.hypera.com.br` |
| **Environment** | Hub |
| **Namespace** | `sentry` |
| **Config File** | `argo-cd-helm-values/kube-addons/sentry/cafehyna-hub/values.yaml` |
| **SMTP Host** | `smtp.office365.com` |
| **Email** | `sentry-hub@hypera.com.br` |

**Production Environment:**

| Property | Value |
|----------|-------|
| **URL** | `https://sentry.cafehyna.hypera.com.br` |
| **Environment** | Production |
| **Config File** | `argo-cd-helm-values/kube-addons/sentry/cafehyna-prd/values.yaml` |
| **SMTP Host** | `smtp.sendgrid.net` |

**Development Environment:**

| Property | Value |
|----------|-------|
| **URL** | `https://sentry.adocyl.com.br` |
| **Environment** | Development |
| **Config File** | `argo-cd-helm-values/kube-addons/sentry/cafehyna-dev/values.yaml` |

---

### SonarQube

**Hub Environment:**

| Property | Value |
|----------|-------|
| **URL** | `https://sonarqube-hub.cafehyna.com.br` |
| **Environment** | Hub |
| **Namespace** | `sonarqube` |
| **Config File** | `argo-cd-helm-values/kube-addons/sonarqube/cafehyna-hub/values.yaml` |
| **TLS Secret** | `sonarqube-hub-tls` |

**Development Environment:**

| Property | Value |
|----------|-------|
| **URL** | `https://sonarqube.hypera.com.br` |
| **Environment** | Development |
| **Config File** | `argo-cd-helm-values/kube-addons/sonarqube/cafehyna-dev/values.yaml` |

---

### Database Administration Tools

**phpMyAdmin (Hub):**

| Property | Value |
|----------|-------|
| **URL** | `https://dba.cafehyna.com.br` |
| **Environment** | Hub |
| **Namespace** | `phpmyadmin` |
| **Config File** | `argo-cd-helm-values/kube-addons/phpmyadmin/hub/values.yaml` |
| **Load Balancer IP** | `172.172.73.104` |

**phpMyAdmin (Dev):**

| Property | Value |
|----------|-------|
| **URL** | `https://dev-dba.cafehyna.com.br` |
| **Environment** | Development |
| **Config File** | `argo-cd-helm-values/kube-addons/phpmyadmin/dev/values.yaml` |

**Adminer (Hub):**

| Property | Value |
|----------|-------|
| **URL** | `https://dba2.cafehyna.com.br` |
| **Environment** | Hub |
| **Namespace** | `adminer` |
| **Config File** | `argo-cd-helm-values/kube-addons/adminer/hub/values.yaml` |
| **TLS Secret** | `adminer-hub-tls` |

---

### Grafana OnCall

| Property | Value |
|----------|-------|
| **URL** | `https://oncall-dev.cafehyna.com` |
| **Environment** | Development |
| **Namespace** | `monitoring` |
| **Config File** | `argo-cd-helm-values/kube-addons/grafana-oncall/dev/values.yaml` |

---

### Mimir (Metrics Storage)

| Property | Value |
|----------|-------|
| **URL** | `https://mimir-hub.cafehyna.com.br` |
| **Environment** | Hub |
| **Namespace** | `monitoring` |
| **Config File** | `argo-cd-helm-values/kube-addons/mimir/cafehyna-hub/values.yaml` |

**Internal Endpoints (cluster-local):**

```
http://mimir-distributed-nginx.monitoring.svc.cluster.local/prometheus
```

---

### RabbitMQ

**PainelClientes Dev:**

| Property | Value |
|----------|-------|
| **Management URL** | `https://rabbitmq-painelclientes-dev.cafehyna.com.br` |
| **Environment** | PainelClientes Dev |
| **Config File** | `infra-team/apps/painelclientes-dev-rabbitmq.yaml` |

**Internal Endpoints:**

```
AMQP:     http://painelclientes.rabbitmq.amqp.dev.adocyl.com.br:80
Management: http://painelclientes.rabbitmq.mgmt.dev.adocyl.com.br:80
Metrics:  http://painelclientes.rabbitmq.metrics.dev.adocyl.com.br:80
```

---

## Cluster API Endpoints - Complete Reference

### cafehyna-hub

| Property | Value |
|----------|-------|
| **Developer Name** | cafehyna-hub |
| **Azure AKS Name** | aks-cafehyna-default |
| **API Server** | `https://aks-cafehyna-default-b2ie56p8.5bbf1042-d320-432c-bd11-cea99f009c29.privatelink.eastus.azmk8s.io:443` |
| **Region** | East US |
| **Resource Group** | rs_hypera_cafehyna |
| **Key Vault** | kv-cafehyna-default |
| **Node Type** | Standard |
| **Kubeconfig** | `~/.kube/aks-rg-hypera-cafehyna-hub-config` |
| **Config File** | `infra-team/argocd-clusters/cafehyna-hub-external.yaml` |

**Services Hosted:**

- ArgoCD (GitOps)
- Prometheus/Grafana (Monitoring)
- Loki (Logging)
- cert-manager
- External-DNS
- Ingress-NGINX

---

### cafehyna-dev

| Property | Value |
|----------|-------|
| **Developer Name** | cafehyna-dev |
| **Azure AKS Name** | aks-cafehyna-dev-hlg |
| **API Server** | `https://aks-cafehyna-dev-hlg-q3oga63c.30041054-9b14-4852-9bd5-114d2fac4590.privatelink.eastus.azmk8s.io:443` |
| **Region** | East US |
| **Resource Group** | RS_Hypera_Cafehyna_Dev |
| **Key Vault** | kv-cafehyna-dev-hlg |
| **Node Type** | Spot |
| **Kubeconfig** | `~/.kube/aks-rg-hypera-cafehyna-dev-config` |
| **Config File** | `infra-team/argocd-clusters/cafehyna-dev.yaml` |

---

### cafehyna-prd

| Property | Value |
|----------|-------|
| **Developer Name** | cafehyna-prd |
| **Azure AKS Name** | aks-cafehyna-prd |
| **API Server** | `https://aks-cafehyna-prd-hsr83z2k.c7d864af-cbd7-481b-866b-8559e0d1c1ea.privatelink.eastus.azmk8s.io:443` |
| **Region** | East US |
| **Resource Group** | rs_hypera_cafehyna_prd |
| **Key Vault** | kv-cafehyna-prd |
| **Node Type** | Standard |
| **Kubeconfig** | `~/.kube/aks-rg-hypera-cafehyna-prd-config` |
| **Config File** | `infra-team/argocd-clusters/cafehyna-prd.yaml` |

---

### painelclientes-dev

| Property | Value |
|----------|-------|
| **Developer Name** | painelclientes-dev |
| **Azure AKS Name** | akspainelclientedev |
| **API Server** | `https://akspainelclientedev-dns-vjs3nd48.hcp.eastus2.azmk8s.io:443` |
| **Region** | East US 2 |
| **Resource Group** | rg-hypera-painelclientes-dev |
| **Node Type** | Standard |
| **Kubeconfig** | `~/.kube/aks-rg-hypera-painelclientes-dev-config` |
| **Config File** | `infra-team/argocd-clusters/painelclientes-dev.yaml` |

---

### painelclientes-prd

| Property | Value |
|----------|-------|
| **Developer Name** | painelclientes-prd |
| **Azure AKS Name** | akspainelclientesprd |
| **API Server** | `https://akspainelclientesprd-dns-kezy4skd.hcp.eastus2.azmk8s.io:443` |
| **Region** | East US 2 |
| **Node Type** | Standard |
| **Config File** | `infra-team/argocd-clusters/painelclientes-prd.yaml` |

---

### loyalty-dev

| Property | Value |
|----------|-------|
| **Developer Name** | loyalty-dev |
| **Azure AKS Name** | Loyalty_AKS-QAS |
| **API Server** | `https://loyaltyaks-qas-dns-d330cafe.hcp.eastus.azmk8s.io:443` |
| **Region** | East US |
| **Resource Group** | RS_Hypera_Loyalty_AKS_QAS |
| **Node Type** | Spot |
| **Kubeconfig** | `~/.kube/aks-rg-hypera-loyalty-dev-config` |
| **Config File** | `infra-team/argocd-clusters/loyalty-dev.yaml` |

---

## Git Repository URLs - Complete Reference

### infra-team

| Property | Value |
|----------|-------|
| **URL** | `https://hypera@dev.azure.com/hypera/Cafehyna%20-%20Desenvolvimento%20Web/_git/infra-team` |
| **Type** | Git |
| **Authentication** | Azure Workload Identity |
| **Config File** | `infra-team/argocd-repos/base/git-repositories/01-infra-team-repo.yaml` |
| **Purpose** | Infrastructure configurations, ApplicationSets, cluster definitions |

### argo-cd-helm-values

| Property | Value |
|----------|-------|
| **URL** | `https://hypera@dev.azure.com/hypera/Cafehyna%20-%20Desenvolvimento%20Web/_git/argo-cd-helm-values` |
| **Type** | Git |
| **Authentication** | Azure Workload Identity |
| **Config File** | `infra-team/argocd-repos/base/git-repositories/02-helm-values-repo.yaml` |
| **Purpose** | Environment-specific Helm values (security boundary) |

### kubernetes-configuration

| Property | Value |
|----------|-------|
| **URL** | `https://hypera@dev.azure.com/hypera/Cafehyna%20-%20Desenvolvimento%20Web/_git/kubernetes-configuration` |
| **Type** | Git |
| **Config File** | `infra-team/argocd-repos/base/git-repositories/03-kubernetes-config-repo.yaml` |
| **Purpose** | Kubernetes manifests and configurations |

---

## Helm Repository URLs - Complete Reference

### ingress-nginx

| Property | Value |
|----------|-------|
| **URL** | `https://kubernetes.github.io/ingress-nginx` |
| **Type** | Helm |
| **Config File** | `infra-team/argocd-repos/base/helm-repositories/01-ingress-nginx-repo.yaml` |
| **Charts** | ingress-nginx |

### jetstack

| Property | Value |
|----------|-------|
| **URL** | `https://charts.jetstack.io` |
| **Type** | Helm |
| **Config File** | `infra-team/argocd-repos/base/helm-repositories/02-jetstack-repo.yaml` |
| **Charts** | cert-manager |

### bitnami

| Property | Value |
|----------|-------|
| **URL** | `https://charts.bitnami.com/bitnami` |
| **Type** | Helm |
| **Config File** | `infra-team/argocd-repos/base/helm-repositories/03-bitnami-repo.yaml` |
| **Charts** | external-dns, phpmyadmin, rabbitmq, postgresql |

### prometheus-community

| Property | Value |
|----------|-------|
| **URL** | `https://prometheus-community.github.io/helm-charts` |
| **Type** | Helm |
| **Config File** | `infra-team/argocd-repos/base/helm-repositories/04-prometheus-repo.yaml` |
| **Charts** | kube-prometheus-stack, prometheus |

### robusta

| Property | Value |
|----------|-------|
| **URL** | `https://robusta-charts.storage.googleapis.com` |
| **Type** | Helm |
| **Config File** | `infra-team/argocd-repos/base/helm-repositories/05-robusta-repo.yaml` |
| **Charts** | robusta |

### cetic

| Property | Value |
|----------|-------|
| **URL** | `https://cetic.github.io/helm-charts` |
| **Type** | Helm |
| **Config File** | `infra-team/argocd-repos/base/helm-repositories/06-cetic-repo.yaml` |
| **Charts** | adminer |

### defectdojo

| Property | Value |
|----------|-------|
| **URL** | `https://raw.githubusercontent.com/DefectDojo/django-DefectDojo/helm-charts` |
| **Type** | Helm |
| **Config File** | `infra-team/argocd-repos/base/helm-repositories/07-defectdojo-repo.yaml` |
| **Charts** | defectdojo |

---

## Certificate Services

### Let's Encrypt

| Environment | ACME URL |
|-------------|----------|
| Staging | `https://acme-staging-v02.api.letsencrypt.org/directory` |
| Production | `https://acme-v02.api.letsencrypt.org/directory` |

### ClusterIssuers

| Issuer | Environment | DNS Provider |
|--------|-------------|--------------|
| `letsencrypt-prod` | Production | Cloudflare |
| `letsencrypt-staging` | Testing | Cloudflare |
| `letsencrypt-prod-cloudflare` | Production (legacy) | Cloudflare |
| `letsencrypt-staging-cloudflare` | Testing (legacy) | Cloudflare |

---

## Troubleshooting Commands

### Check Application URL

```bash
# Full health check
curl -sI https://argocd.cafehyna.com.br | head -5

# Certificate info
echo | openssl s_client -servername argocd.cafehyna.com.br -connect argocd.cafehyna.com.br:443 2>/dev/null | openssl x509 -noout -dates

# DNS resolution
dig +short argocd.cafehyna.com.br
```

### Check Cluster Connectivity

```bash
# Test API endpoint (requires VPN)
curl -sk https://aks-cafehyna-default-b2ie56p8.5bbf1042-d320-432c-bd11-cea99f009c29.privatelink.eastus.azmk8s.io:443/healthz

# Full kubectl test
kubectl --kubeconfig ~/.kube/aks-rg-hypera-cafehyna-hub-config get nodes
```

### Check Certificate Status

```bash
# In cluster
kubectl --kubeconfig ~/.kube/<config> get certificates -A
kubectl --kubeconfig ~/.kube/<config> describe certificate <name> -n <namespace>

# Check issuer
kubectl --kubeconfig ~/.kube/<config> describe clusterissuer letsencrypt-prod
```

### Check DNS Records

```bash
# Verify Cloudflare DNS
dig @1.1.1.1 argocd.cafehyna.com.br

# Check external-dns logs
kubectl --kubeconfig ~/.kube/<config> logs -n external-dns -l app.kubernetes.io/name=external-dns --tail=50
```

---

## URL Patterns

### Ingress Annotation Patterns

```yaml
# Standard ingress annotations
annotations:
  cert-manager.io/cluster-issuer: "letsencrypt-prod"
  external-dns.alpha.kubernetes.io/hostname: "app.cafehyna.com.br"
  nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
  nginx.ingress.kubernetes.io/ssl-redirect: "true"
```

### TLS Configuration Pattern

```yaml
tls:
  - secretName: app-tls
    hosts:
      - app.cafehyna.com.br
```
