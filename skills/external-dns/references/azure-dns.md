# External-DNS Azure DNS Configuration Reference

Complete guide for configuring External-DNS with Azure DNS (public and private zones) in AKS clusters.

## Authentication Methods

Azure DNS supports three authentication methods with External-DNS:

| Method | Security | Complexity | Recommended For |
|--------|----------|------------|-----------------|
| **Workload Identity** | Highest | Medium | AKS 1.22+ (Production) |
| **Managed Identity (Pod Identity)** | High | Medium | Legacy AKS |
| **Service Principal** | Medium | Low | Dev/Testing |

## Workload Identity Configuration (Recommended)

### Prerequisites

1. AKS cluster with Workload Identity enabled
2. User-Assigned Managed Identity
3. Federated credential configured
4. DNS Zone Contributor role assigned

### Step 1: Create Managed Identity

```bash
# Variables
RESOURCE_GROUP="rg-myapp"
IDENTITY_NAME="id-external-dns"
LOCATION="eastus"

# Create identity
az identity create \
  --name $IDENTITY_NAME \
  --resource-group $RESOURCE_GROUP \
  --location $LOCATION

# Get identity details
IDENTITY_CLIENT_ID=$(az identity show --name $IDENTITY_NAME --resource-group $RESOURCE_GROUP --query clientId -o tsv)
IDENTITY_OBJECT_ID=$(az identity show --name $IDENTITY_NAME --resource-group $RESOURCE_GROUP --query principalId -o tsv)
IDENTITY_RESOURCE_ID=$(az identity show --name $IDENTITY_NAME --resource-group $RESOURCE_GROUP --query id -o tsv)
```

### Step 2: Assign DNS Zone Permissions

```bash
# For Public DNS Zone
DNS_ZONE_RESOURCE_GROUP="rg-dns"
DNS_ZONE_NAME="example.com"
DNS_ZONE_ID="/subscriptions/<SUB_ID>/resourceGroups/$DNS_ZONE_RESOURCE_GROUP/providers/Microsoft.Network/dnszones/$DNS_ZONE_NAME"

az role assignment create \
  --role "DNS Zone Contributor" \
  --assignee $IDENTITY_OBJECT_ID \
  --scope $DNS_ZONE_ID

# For Private DNS Zone
PRIVATE_DNS_ZONE_ID="/subscriptions/<SUB_ID>/resourceGroups/$DNS_ZONE_RESOURCE_GROUP/providers/Microsoft.Network/privateDnsZones/$DNS_ZONE_NAME"

az role assignment create \
  --role "Private DNS Zone Contributor" \
  --assignee $IDENTITY_OBJECT_ID \
  --scope $PRIVATE_DNS_ZONE_ID
```

### Step 3: Create Federated Credential

```bash
# Get AKS OIDC issuer URL
AKS_CLUSTER_NAME="aks-myapp"
AKS_RESOURCE_GROUP="rg-myapp"
AKS_OIDC_ISSUER=$(az aks show --name $AKS_CLUSTER_NAME --resource-group $AKS_RESOURCE_GROUP --query oidcIssuerProfile.issuerUrl -o tsv)

# Create federated credential
az identity federated-credential create \
  --name "external-dns-federated" \
  --identity-name $IDENTITY_NAME \
  --resource-group $RESOURCE_GROUP \
  --issuer $AKS_OIDC_ISSUER \
  --subject "system:serviceaccount:external-dns:external-dns" \
  --audiences "api://AzureADTokenExchange"
```

### Step 4: Helm Values Configuration

```yaml
# values.yaml for Workload Identity
fullnameOverride: external-dns

provider:
  name: azure

# Workload Identity configuration
serviceAccount:
  create: true
  name: external-dns
  labels:
    azure.workload.identity/use: "true"
  annotations:
    azure.workload.identity/client-id: "<IDENTITY_CLIENT_ID>"

podLabels:
  azure.workload.identity/use: "true"

# Azure-specific environment variables
env:
  - name: AZURE_TENANT_ID
    value: "<TENANT_ID>"
  - name: AZURE_SUBSCRIPTION_ID
    value: "<SUBSCRIPTION_ID>"
  - name: AZURE_RESOURCE_GROUP
    value: "<DNS_ZONE_RESOURCE_GROUP>"  # Resource group containing DNS zone

# Source configuration
sources:
  - service
  - ingress

# Domain filter - IMPORTANT: restrict to your domains
domainFilters:
  - example.com
  - subdomain.example.com

# TXT record ownership (must be unique per cluster)
txtOwnerId: "aks-myapp-eastus"
txtPrefix: "_externaldns."

# Policy
policy: upsert-only  # Production: upsert-only, Dev: sync

# Sync interval
interval: "5m"

# Logging
logLevel: info
logFormat: json

# Resources
resources:
  requests:
    memory: "64Mi"
    cpu: "25m"
  limits:
    memory: "128Mi"
    # No CPU limits per AKS best practices

# Security context
securityContext:
  runAsNonRoot: true
  runAsUser: 65534
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities:
    drop: ["ALL"]

# Pod security context
podSecurityContext:
  runAsNonRoot: true
  runAsUser: 65534
  fsGroup: 65534
  seccompProfile:
    type: RuntimeDefault
```

## Service Principal Configuration (Alternative)

### Step 1: Create Service Principal

```bash
# Create SP with DNS Zone Contributor role
SP_NAME="sp-external-dns"
DNS_ZONE_ID="/subscriptions/<SUB_ID>/resourceGroups/<RG>/providers/Microsoft.Network/dnszones/<ZONE>"

az ad sp create-for-rbac \
  --name $SP_NAME \
  --role "DNS Zone Contributor" \
  --scopes $DNS_ZONE_ID \
  --output json

# Save output:
# {
#   "appId": "<CLIENT_ID>",
#   "displayName": "sp-external-dns",
#   "password": "<CLIENT_SECRET>",
#   "tenant": "<TENANT_ID>"
# }
```

### Step 2: Create Kubernetes Secret

```bash
kubectl create namespace external-dns

kubectl create secret generic azure-credentials \
  --namespace external-dns \
  --from-literal=client-id=<CLIENT_ID> \
  --from-literal=client-secret=<CLIENT_SECRET>
```

### Step 3: Helm Values Configuration

```yaml
# values.yaml for Service Principal
fullnameOverride: external-dns

provider:
  name: azure

env:
  - name: AZURE_TENANT_ID
    value: "<TENANT_ID>"
  - name: AZURE_SUBSCRIPTION_ID
    value: "<SUBSCRIPTION_ID>"
  - name: AZURE_RESOURCE_GROUP
    value: "<DNS_ZONE_RESOURCE_GROUP>"
  - name: AZURE_CLIENT_ID
    valueFrom:
      secretKeyRef:
        name: azure-credentials
        key: client-id
  - name: AZURE_CLIENT_SECRET
    valueFrom:
      secretKeyRef:
        name: azure-credentials
        key: client-secret

sources:
  - service
  - ingress

domainFilters:
  - example.com

txtOwnerId: "aks-myapp"
policy: upsert-only
interval: "5m"
```

## Azure Private DNS Zone Configuration

For private DNS zones, use the `azure-private-dns` provider:

```yaml
provider:
  name: azure-private-dns

env:
  - name: AZURE_TENANT_ID
    value: "<TENANT_ID>"
  - name: AZURE_SUBSCRIPTION_ID
    value: "<SUBSCRIPTION_ID>"
  - name: AZURE_RESOURCE_GROUP
    value: "<PRIVATE_DNS_ZONE_RESOURCE_GROUP>"

# Workload Identity labels
serviceAccount:
  labels:
    azure.workload.identity/use: "true"
  annotations:
    azure.workload.identity/client-id: "<IDENTITY_CLIENT_ID>"

podLabels:
  azure.workload.identity/use: "true"

domainFilters:
  - internal.example.com

txtOwnerId: "aks-myapp-private"
```

## Multiple DNS Zones Configuration

When managing multiple DNS zones in different resource groups:

```yaml
provider:
  name: azure

env:
  - name: AZURE_TENANT_ID
    value: "<TENANT_ID>"
  - name: AZURE_SUBSCRIPTION_ID
    value: "<SUBSCRIPTION_ID>"

# Use extraArgs for multiple resource groups
extraArgs:
  azure-resource-group: ""  # Empty to use zone-specific resource groups

# Domain filters for all zones
domainFilters:
  - zone1.example.com
  - zone2.example.com
```

> **Note**: For zones in different resource groups, you need to grant the identity permissions on each zone and may need to deploy separate External-DNS instances.

## Azure RBAC Roles Reference

| Role | Permissions | Use Case |
|------|-------------|----------|
| **DNS Zone Contributor** | Full access to DNS zones (no network access) | Public DNS zones |
| **Private DNS Zone Contributor** | Full access to private DNS zones | Private DNS zones |
| **Reader** | Read-only access | Troubleshooting only |

### Custom Role (Minimum Permissions)

```json
{
  "Name": "External DNS Operator",
  "Description": "Allows External-DNS to manage DNS records",
  "Actions": [
    "Microsoft.Network/dnsZones/read",
    "Microsoft.Network/dnsZones/A/read",
    "Microsoft.Network/dnsZones/A/write",
    "Microsoft.Network/dnsZones/A/delete",
    "Microsoft.Network/dnsZones/AAAA/read",
    "Microsoft.Network/dnsZones/AAAA/write",
    "Microsoft.Network/dnsZones/AAAA/delete",
    "Microsoft.Network/dnsZones/CNAME/read",
    "Microsoft.Network/dnsZones/CNAME/write",
    "Microsoft.Network/dnsZones/CNAME/delete",
    "Microsoft.Network/dnsZones/TXT/read",
    "Microsoft.Network/dnsZones/TXT/write",
    "Microsoft.Network/dnsZones/TXT/delete"
  ],
  "NotActions": [],
  "AssignableScopes": [
    "/subscriptions/<SUBSCRIPTION_ID>/resourceGroups/<RESOURCE_GROUP>"
  ]
}
```

## Validation Commands

### Check Identity Assignment

```bash
# Verify role assignment
az role assignment list --assignee $IDENTITY_OBJECT_ID --scope $DNS_ZONE_ID -o table

# Verify federated credential
az identity federated-credential list --identity-name $IDENTITY_NAME --resource-group $RESOURCE_GROUP -o table
```

### Check External-DNS Status

```bash
# Check pods
kubectl get pods -n external-dns -l app.kubernetes.io/name=external-dns

# Check logs for Azure authentication
kubectl logs -n external-dns deployment/external-dns | grep -i azure

# Check for authentication errors
kubectl logs -n external-dns deployment/external-dns | grep -i "error\|unauthorized\|forbidden"
```

### Verify DNS Records

```bash
# List A records in zone
az network dns record-set a list -g <RESOURCE_GROUP> -z example.com -o table

# List TXT records (ownership)
az network dns record-set txt list -g <RESOURCE_GROUP> -z example.com -o table

# Query specific record
az network dns record-set a show -g <RESOURCE_GROUP> -z example.com -n myapp

# Test resolution
nslookup myapp.example.com
dig myapp.example.com @168.63.129.16  # Azure DNS resolver
```

## Common Issues and Solutions

### Issue: Authentication Failed

**Symptoms**: `authorization failed` or `client credentials` errors in logs

**Solutions**:

1. Verify AZURE_TENANT_ID, AZURE_SUBSCRIPTION_ID are correct
2. Check Workload Identity labels are set on both ServiceAccount and Pod
3. Verify federated credential subject matches: `system:serviceaccount:<namespace>:<sa-name>`
4. Check role assignment scope includes the DNS zone

### Issue: No DNS Records Created

**Symptoms**: External-DNS runs but no records appear in Azure

**Solutions**:

1. Verify `domainFilters` includes your domain
2. Check `AZURE_RESOURCE_GROUP` points to the zone's resource group
3. Verify source type is correct (service/ingress)
4. Check for `dry-run: true` in extraArgs

### Issue: Rate Limiting

**Symptoms**: `429 Too Many Requests` errors

**Solutions**:

1. Increase `interval` (e.g., from `1m` to `5m`)
2. Reduce number of watched namespaces
3. Use `--azure-batch-change-size` to batch updates

### Issue: TXT Record Conflicts

**Symptoms**: `TXT record is already in use` errors

**Solutions**:

1. Verify `txtOwnerId` is unique per cluster
2. Manually delete orphaned TXT records
3. Use different `txtPrefix` if needed

## High Availability Configuration

```yaml
# Production HA configuration
replicaCount: 2

affinity:
  podAntiAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchExpressions:
            - key: app.kubernetes.io/name
              operator: In
              values:
                - external-dns
        topologyKey: kubernetes.io/hostname

podDisruptionBudget:
  enabled: true
  minAvailable: 1

priorityClassName: system-cluster-critical

topologySpreadConstraints:
  - maxSkew: 1
    topologyKey: topology.kubernetes.io/zone
    whenUnsatisfiable: ScheduleAnyway
    labelSelector:
      matchLabels:
        app.kubernetes.io/name: external-dns
```

## Azure-Specific Annotations

```yaml
# Custom TTL (seconds)
external-dns.alpha.kubernetes.io/ttl: "300"

# Target for the record
external-dns.alpha.kubernetes.io/target: "20.10.5.100"

# Multiple hostnames
external-dns.alpha.kubernetes.io/hostname: "app.example.com,api.example.com"
```

## Integration with Azure Application Gateway Ingress Controller (AGIC)

When using AGIC, External-DNS can read the Application Gateway's public IP:

```yaml
sources:
  - ingress

# AGIC Ingress Class
extraArgs:
  ingress-class: azure-application-gateway
```

## Monitoring and Alerting

### Prometheus Alert Rules

```yaml
groups:
  - name: external-dns
    rules:
      - alert: ExternalDNSSyncErrors
        expr: increase(external_dns_controller_sync_errors_total[5m]) > 0
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: External-DNS sync errors detected

      - alert: ExternalDNSNotSyncing
        expr: time() - external_dns_controller_last_sync_timestamp_seconds > 900
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: External-DNS has not synced in 15 minutes
```

## References

- [Azure DNS Tutorial](https://kubernetes-sigs.github.io/external-dns/latest/tutorials/azure/)
- [Azure Private DNS Tutorial](https://kubernetes-sigs.github.io/external-dns/latest/tutorials/azure-private-dns/)
- [AKS Workload Identity](https://learn.microsoft.com/en-us/azure/aks/workload-identity-overview)
- [Azure RBAC Built-in Roles](https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles)
