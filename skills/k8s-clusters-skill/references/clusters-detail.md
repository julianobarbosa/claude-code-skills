# Clusters Detail Reference

Extended information not in SKILL.md. Use grep patterns: `## <cluster-name>` to find specific cluster.

## cafehyna-dev

- **API Server**: `aks-cafehyna-dev-hlg-q3oga63c.30041054-9b14-4852-9bd5-114d2fac4590.privatelink.eastus.azmk8s.io`
- **API Alias**: `cafehyna-dev-aks.eastus.cloudapp.azure.com`
- **Key Vault**: `kv-cafehyna-dev-hlg`
- **Managed Identity**: `f1a14a8f-6d38-40a0-a935-3cdd91a25f47`
- **Nodepools**:
  - `cafedev` (System nodepool - has `CriticalAddonsOnly` taint, NOT for workloads)
  - `cafedevspot` (User nodepool - spot instances, use this for workloads)
- **Region**: East US
- **Important**: Only use `cafedevspot` in node affinity selectors. The `cafedev` nodepool has `CriticalAddonsOnly` taint.

## cafehyna-hub

- **API Server**: `aks-cafehyna-default-b2ie56p8.5bbf1042-d320-432c-bd11-cea99f009c29.privatelink.eastus.azmk8s.io`
- **API Alias**: `cafehyna-hub-aks.eastus.cloudapp.azure.com`
- **Key Vault**: `kv-cafehyna-default`
- **Managed Identity**: `f1a14a8f-6d38-40a0-a935-3cdd91a25f47`
- **Nodepools**: `hub`
- **Region**: East US
- **Services**: ArgoCD, Prometheus, Grafana, Loki, cert-manager, External-DNS, Ingress-NGINX

## cafehyna-prd

- **API Server**: `aks-cafehyna-prd-hsr83z2k.c7d864af-cbd7-481b-866b-8559e0d1c1ea.privatelink.eastus.azmk8s.io`
- **API Alias**: `cafehyna-aks-.eastus.cloudapp.azure.com`
- **Key Vault**: `kv-cafehyna-prd`
- **Managed Identity**: `f1a14a8f-6d38-40a0-a935-3cdd91a25f47`
- **Nodepools**: `cafehynaprd`
- **Region**: East US

## loyalty-dev

- **API Server**: `loyaltyaks-qas-dns-d330cafe.hcp.eastus.azmk8s.io`
- **Nodepools**: `agentpoolqas`
- **Region**: East US

## loyalty-prd

- **API Server**: `loyaltyaks-prd-dns-4d88035e.hcp.eastus.azmk8s.io`
- **Nodepools**: `agentprdpool`
- **Region**: East US

## sonora-dev

- **API Server**: `aks-hypera-sonora-dev-hlg-yz9t4ou8.d9f58524-b5b3-4fa9-af7d-cd5007447dea.privatelink.eastus.azmk8s.io`
- **API Alias**: `sonora-dev-aks.eastus.cloudapp.azure.com`
- **Nodepools**: `agentpoolqas`
- **Region**: East US

## painelclientes-dev

- **API Server**: `akspainelclientedev-dns-vjs3nd48.hcp.eastus2.azmk8s.io`
- **Subscription**: `operation-dev` (56bb103c-1075-4536-b6fc-abf6df80b15c)
- **Key Vault**: `painel-clientes-dev`
- **Managed Identity**: `ec7174fd-dc97-46fe-a255-75943580c685`
- **Nodepools**: `pcdev` (System), `pcdevspot` (Spot)
- **Region**: East US2
- **Policy**: AMD-only compute (Dasv5, Easv5 series)

## painelclientes-hub

- **Key Vault**: `kv-painelclientes-hub`
- **Nodepools**: `hub`
- **Region**: East US2

## painelclientes-prd

- **Key Vault**: `painel-clientes-prd`
- **Managed Identity (KV)**: `18a14a67-899c-45a1-aa84-c9b4813aa8d7`
- **Managed Identity (Pool)**: `542b4bcd-811b-4f69-9d96-f2e52055f186`
- **Nodepools**: `prd`
- **Region**: East US2

---

## Resource Templates

### Spot Toleration + Affinity (Full)

```yaml
spec:
  tolerations:
    - key: kubernetes.azure.com/scalesetpriority
      operator: Equal
      value: "spot"
      effect: NoSchedule
  affinity:
    nodeAffinity:
      preferredDuringSchedulingIgnoredDuringExecution:
        - weight: 100
          preference:
            matchExpressions:
              - key: kubernetes.azure.com/scalesetpriority
                operator: In
                values: ["spot"]
      requiredDuringSchedulingIgnoredDuringExecution:
        nodeSelectorTerms:
          - matchExpressions:
              - key: agentpool
                operator: In
                values: ["cafedevspot"]  # Do NOT include "cafedev" - it has CriticalAddonsOnly taint
```

### Ingress with TLS

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: app-ingress
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod-cloudflare  # or staging
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
spec:
  ingressClassName: nginx
  tls:
    - secretName: app-tls
      hosts: ["app.cafehyna.com.br"]
  rules:
    - host: app.cafehyna.com.br
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: app-service
                port: {number: 80}
```

### PVC with ZRS

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: data-pvc
spec:
  accessModes: ["ReadWriteOnce"]
  storageClassName: managed-premium-zrs
  resources:
    requests: {storage: 100Gi}
```

### Helm Values StorageClass Configuration (LGTM Stack)

**CRITICAL**: Always set `storageClass: managed-premium-zrs` explicitly. Never use `null`.

**Loki** (`argo-cd-helm-values/kube-addons/loki/<cluster>/values.yaml`):

```yaml
# Set in each persistence section: ingester, write, read, backend, singleBinary
ingester:
  persistence:
    storageClass: managed-premium-zrs  # NOT null
write:
  persistence:
    storageClass: managed-premium-zrs
read:
  persistence:
    storageClass: managed-premium-zrs
backend:
  persistence:
    storageClass: managed-premium-zrs
singleBinary:
  persistence:
    storageClass: managed-premium-zrs
```

**Tempo** (`argo-cd-helm-values/kube-addons/tempo/<cluster>/values.yaml`):

```yaml
global:
  storageClass: managed-premium-zrs  # Global default

ingester:
  persistentVolume:
    storageClass: managed-premium-zrs  # Override for ingester

metricsGenerator:
  persistentVolume:
    storageClass: managed-premium-zrs  # Override for metrics-generator

# Zone-aware replication (if enabled)
ingester:
  zoneAwareReplication:
    zones:
      - name: zone-a
        storageClass: managed-premium-zrs
      - name: zone-b
        storageClass: managed-premium-zrs
      - name: zone-c
        storageClass: managed-premium-zrs
```

**Mimir** (`argo-cd-helm-values/kube-addons/mimir/<cluster>/values.yaml`):

```yaml
# Set in each component's persistence section
ingester:
  persistentVolume:
    storageClass: managed-premium-zrs

store_gateway:
  persistentVolume:
    storageClass: managed-premium-zrs

compactor:
  persistentVolume:
    storageClass: managed-premium-zrs

alertmanager:
  persistentVolume:
    storageClass: managed-premium-zrs
```

---

## Troubleshooting Commands

### Certificate Issues

```bash
# Find stuck certificates
kubectl --kubeconfig ~/.kube/<config> get certificates -A -o jsonpath='{range .items[?(@.status.conditions[*].status=="False")]}{.metadata.namespace}/{.metadata.name} {.status.conditions[0].message}{"\n"}{end}'

# Check certificate request
kubectl --kubeconfig ~/.kube/<config> get certificaterequests -A
kubectl --kubeconfig ~/.kube/<config> describe certificaterequest <name> -n <ns>

# Check ClusterIssuer status
kubectl --kubeconfig ~/.kube/<config> describe clusterissuer letsencrypt-prod-cloudflare
```

### Spot Node Issues

```bash
# List spot nodes
kubectl --kubeconfig ~/.kube/<config> get nodes -l kubernetes.azure.com/scalesetpriority=spot -o wide

# Check eviction events
kubectl --kubeconfig ~/.kube/<config> get events -A --field-selector reason=Evicted

# Verify pod tolerations
kubectl --kubeconfig ~/.kube/<config> get pod <pod> -n <ns> -o jsonpath='{.spec.tolerations}' | jq
```

### RBAC Issues

```bash
# Check what you can do
kubectl --kubeconfig ~/.kube/<config> auth can-i --list

# Check specific action
kubectl --kubeconfig ~/.kube/<config> auth can-i create deployments -n <ns>

# Who am I
kubectl --kubeconfig ~/.kube/<config> auth whoami
```

### Storage / PVC Issues

```bash
# Check PVC status
kubectl --kubeconfig ~/.kube/<config> get pvc -n monitoring

# Check PV details and zone binding
kubectl --kubeconfig ~/.kube/<config> get pv -o wide

# Describe stuck PVC
kubectl --kubeconfig ~/.kube/<config> describe pvc <pvc-name> -n <ns>

# Check for volume affinity conflict events
kubectl --kubeconfig ~/.kube/<config> get events -n <ns> --field-selector reason=FailedScheduling | grep -i "volume node affinity"

# Fix: Delete stuck PVC to allow recreation in correct zone
# WARNING: Data loss! Only for non-critical/stateless workloads
kubectl --kubeconfig ~/.kube/<config> delete pvc <pvc-name> -n <ns>

# Check storageClass configuration in Helm values
grep -r "storageClass:" argo-cd-helm-values/kube-addons/<app>/<cluster>/values.yaml

# Find null storageClass (problematic)
grep -rn "storageClass: null" argo-cd-helm-values/kube-addons/
```

---

## Operational Info

### ArgoCD Access

- **URL**: <https://argocd.cafehyna.com.br>
- **Port-forward**: `kubectl --kubeconfig ~/.kube/aks-rg-hypera-cafehyna-hub-config port-forward svc/argocd-server -n argocd 8080:443`
- **Local**: <https://localhost:8080>

### Maintenance Windows

| Env | Window | Approval |
|-----|--------|----------|
| dev | Anytime | Notify |
| hub | Weekends 2-6 AM EST | Team |
| prd | Sundays 2-4 AM EST | Required |

### Backup Retention

| Env | Frequency | Retention |
|-----|-----------|-----------|
| dev | Daily | 7 days |
| hub | Hourly | 30 days |
| prd | Continuous | 90 days |
