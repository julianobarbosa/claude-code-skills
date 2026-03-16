# CIDR Master Allocation

Source of truth for Hypera's Azure network address space. Update this file when VNets are deployed.

## Subscription CIDR Allocation

Each subscription receives a `/13` block (524,288 addresses, 128 x `/20` VNets).

| Subscription | CIDR | Range Start | Range End |
|---|---|---|---|
| hub-spoke | 10.128.0.0/13 | 10.128.0.0 | 10.135.255.255 |
| operacoes | 10.136.0.0/13 | 10.136.0.0 | 10.143.255.255 |
| operacoes-dev | 10.144.0.0/13 | 10.144.0.0 | 10.151.255.255 |
| solucoes | 10.152.0.0/13 | 10.152.0.0 | 10.159.255.255 |
| solucoes-dev | 10.160.0.0/13 | 10.160.0.0 | 10.167.255.255 |
| digital | 10.168.0.0/13 | 10.168.0.0 | 10.175.255.255 |
| digital-dev | 10.176.0.0/13 | 10.176.0.0 | 10.183.255.255 |
| projetos | 10.184.0.0/13 | 10.184.0.0 | 10.191.255.255 |
| projetos-dev | 10.192.0.0/13 | 10.192.0.0 | 10.199.255.255 |
| poc | 10.200.0.0/13 | 10.200.0.0 | 10.207.255.255 |
| visualstudio | 10.208.0.0/13 | 10.208.0.0 | 10.215.255.255 |
| alz-connectivity-dev | 10.216.0.0/13 | 10.216.0.0 | 10.223.255.255 |
| alz-identity-dev | 10.224.0.0/13 | 10.224.0.0 | 10.231.255.255 |
| alz-mgmt-dev | 10.232.0.0/13 | 10.232.0.0 | 10.239.255.255 |
| infrastructure | 10.240.0.0/13 | 10.240.0.0 | 10.247.255.255 |
| infrastructure-dev | 10.248.0.0/13 | 10.248.0.0 | 10.255.255.255 |

## VNet Index Formula

A `/13` contains exactly **128** `/20` VNets.

```
Given subscription base B (e.g., 10.248.0.0 for infrastructure-dev):

VNet index i (0-127):
  octet2 = B.octet2 + floor((i * 16) / 256)
  octet3 = (i * 16) mod 256
  VNet[i] = B.octet1 . (B.octet2 + floor(i*16/256)) . ((i*16) mod 256) . 0 / 20

Shortcut: each /20 is 4,096 addresses = 16 x /24 blocks
  VNet[i] address = base_ip + (i * 4096)
```

**Examples for infrastructure-dev (10.248.0.0/13):**

| Index | VNet CIDR | Range |
|-------|-----------|-------|
| 0 | 10.248.0.0/20 | 10.248.0.0 - 10.248.15.255 |
| 1 | 10.248.16.0/20 | 10.248.16.0 - 10.248.31.255 |
| 2 | 10.248.32.0/20 | 10.248.32.0 - 10.248.47.255 |
| 15 | 10.248.240.0/20 | 10.248.240.0 - 10.248.255.255 |
| 16 | 10.249.0.0/20 | 10.249.0.0 - 10.249.15.255 |
| 127 | 10.255.240.0/20 | 10.255.240.0 - 10.255.255.255 |

## Known VNet Allocations

**Keep this table updated when new VNets are deployed.**

| Subscription | VNet Index | CIDR | Resource Group | Purpose |
|---|---|---|---|---|
| infrastructure-dev | 0 | 10.248.0.0/20 | rg-hypera-packer-image | Packer Image Builder |
| operacoes | 0 | 10.136.0.0/20 | (AKS prd cluster) | AKS Production |
| operacoes | 1 | 10.136.16.0/20 | rg-hypera-painelclientes-hub | Painelclientes Hub |
| operacoes | 2 | 10.136.32.0/20 | rg-hypera-painelclientes-prd | Painelclientes Production |
| operacoes-dev | 0 | 10.144.0.0/20 | (AKS dev cluster) | AKS Development |
| operacoes-dev | 1 | 10.144.16.0/20 | rg-hypera-painelclientes-dev | Painelclientes Development |

## AKS Overlay CIDR Pairs

AKS clusters using Azure CNI Overlay use non-VNet address space for pods and services. Each pair uses a `/16` from the `172.20-29.0.0` range.

| Pair | Pod CIDR | Service CIDR | Assignment |
|------|----------|--------------|------------|
| 0 | 172.20.0.0/16 | 172.21.0.0/16 | operacoes-dev AKS dev |
| 1 | 172.22.0.0/16 | 172.23.0.0/16 | operacoes AKS prd |
| 2 | 172.24.0.0/16 | 172.25.0.0/16 | painelclientes-dev AKS |
| 3 | 172.26.0.0/16 | 172.27.0.0/16 | painelclientes-prd AKS |
| 4 | 172.28.0.0/16 | 172.29.0.0/16 | painelclientes-hub AKS |
| 5-9 | 172.30-38.0.0/16 | 172.31-39.0.0/16 | Available |

**Rule:** Even = Pod CIDR, Odd = Service CIDR. Allocate sequentially.

## /24 Blocks Within a /20

Each `/20` VNet contains exactly **16** `/24` blocks:

```
VNet base X.Y.Z.0/20:
  Block 0:  X.Y.(Z+0).0/24
  Block 1:  X.Y.(Z+1).0/24
  ...
  Block 15: X.Y.(Z+15).0/24
```

Each `/24` provides 256 addresses (251 usable after Azure reserves 5).
