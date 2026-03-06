# Cluster Inventory

Complete inventory of AKS clusters managed by the Cafehyna ArgoCD platform.

## Cluster Reference Table

| Cluster | URL | Project | Environment | Spot? | Business Unit |
|---------|-----|---------|-------------|-------|---------------|
| `cafehyna-dev` | `https://aks-cafehyna-dev-hlg-q3oga63c.30041054-9b14-4852-9bd5-114d2fac4590.privatelink.eastus.azmk8s.io:443` | `kube-addons` | development | Yes | cafehyna |
| `cafehyna-hub` | `https://kubernetes.default.svc` | `kube-addons` | hub | No | cafehyna |
| `cafehyna-prd` | `https://aks-cafehyna-prd-hsr83z2k.c7d864af-cbd7-481b-866b-8559e0d1c1ea.privatelink.eastus.azmk8s.io:443` | `kube-addons` | production | No | cafehyna |
| `loyalty-dev` | `https://loyaltyaks-qas-dns-d330cafe.hcp.eastus.azmk8s.io:443` | `loyalty-kube-addons` | development | Yes | loyalty |
| `loyalty-prd` | `https://loyaltyaks-prd-dns-4d88035e.hcp.eastus.azmk8s.io:443` | `loyalty-kube-addons` | production | No | loyalty |
| `painelclientes-dev` | `https://akspainelclientedev-dns-vjs3nd48.hcp.eastus2.azmk8s.io:443` | `painelclientes-kube-addons` | development | Yes | painelclientes |
| `painelclientes-prd` | `https://akspainelclientesprd-dns-kezy4skd.hcp.eastus2.azmk8s.io:443` | `painelclientes-kube-addons` | production | No | painelclientes |
| `sonora-dev` | `https://aks-hypera-sonora-dev-hlg-yz9t4ou8.d9f58524-b5b3-4fa9-af7d-cd5007447dea.privatelink.eastus.azmk8s.io:443` | `sonora-kube-addons` | development | Yes | sonora |
| `sonora-prd` | `https://aks-hypera-sonora-prod-2xiqgc37.84a80cec-6ef2-41fd-b6f7-2b6b934f8fb3.privatelink.eastus.azmk8s.io:443` | `sonora-kube-addons` | production | No | sonora |

## Notes

- **Hub cluster** (`cafehyna-hub`) uses `https://kubernetes.default.svc` because ArgoCD runs in-cluster there
- **Development clusters** use Azure Spot VMs -- all workloads MUST include spot tolerations
- **Project naming**: `kube-addons` for cafehyna, `<unit>-kube-addons` for other business units
- **Private link**: cafehyna and sonora clusters use Azure Private Link endpoints
- **Region**: cafehyna/loyalty/sonora in `eastus`, painelclientes in `eastus2`

## Spot Tolerations (Required for Dev)

```yaml
tolerations:
  - key: kubernetes.azure.com/scalesetpriority
    operator: Equal
    value: "spot"
    effect: NoSchedule
```

## Git Repository

All values files are committed to the same Azure DevOps repo:
```
https://hyperadevops@dev.azure.com/hyperadevops/devops-team/_git/argocd
```

## Currently Deployed Services (in kustomization.yaml)

adminer, adp-agent, akv2k8s, argocd-image-updater, argocd-projects, argocd-repos, bytebase, cert-manager, defectdojo, dependency-track, external-dns, ingress-nginx, kargo, loki, mimir, otel, painelclientes-cronjobs, pyroscope, robusta, sonarqube, storage-class, tempo
