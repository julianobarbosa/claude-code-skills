# CalculateCapacity Workflow

Show remaining network capacity at subscription or VNet level.

## Inputs

One of:
1. **Subscription name** — show /20 VNet capacity (e.g., `infrastructure-dev`)
2. **VNet CIDR** — show /24 subnet capacity within that VNet (e.g., `10.248.0.0/20`)
3. **No input** — show summary across all subscriptions

## Mode 1: Subscription Capacity

### Steps

1. Read [CidrMasterAllocation.md](../CidrMasterAllocation.md)
2. Find the subscription's `/13` base
3. Count known VNet allocations for that subscription
4. Calculate:
   - Total /20 slots: 128
   - Used: count of known allocations
   - Free: 128 - used
   - Next available index and CIDR

### Output

```
## Subscription Capacity: {subscription}

| Metric | Value |
|--------|-------|
| Subscription CIDR | {base}/13 |
| Total /20 VNet slots | 128 |
| Used | {count} |
| Free | {128 - count} |
| Utilization | {percent}% |
| Next available index | {index} |
| Next available CIDR | {cidr}/20 |

### Known Allocations
| Index | CIDR | Resource Group | Purpose |
|-------|------|----------------|---------|
| ... | ... | ... | ... |
```

## Mode 2: VNet Capacity

### Steps

1. Parse the VNet CIDR to get base address
2. Identify which subscription it belongs to
3. Look up known subnet allocations within this VNet from [CidrMasterAllocation.md](../CidrMasterAllocation.md) and any additional sources
4. Map all 16 `/24` blocks

### Output

```
## VNet Capacity: {vnet_cidr}

| Metric | Value |
|--------|-------|
| VNet CIDR | {cidr}/20 |
| Subscription | {subscription} |
| Total /24 blocks | 16 |
| Used/Reserved | {count} |
| Free | {16 - count} |
| Next available | {next_cidr}/24 |

### /24 Block Map
| Block | CIDR | Status | Usage |
|-------|------|--------|-------|
| 0 | X.Y.Z.0/24 | Free/Active/Reserved | {description} |
| 1 | X.Y.(Z+1).0/24 | ... | ... |
| ... | ... | ... | ... |
| 15 | X.Y.(Z+15).0/24 | ... | ... |
```

**Note:** Blocks partially consumed by /22 or /27 subnets should be marked accordingly (e.g., "Part of snet-aks-nodes /22").

## Mode 3: All Subscriptions Summary

### Steps

1. Read all known allocations from [CidrMasterAllocation.md](../CidrMasterAllocation.md)
2. Summarize per subscription

### Output

```
## Network Capacity Summary (All Subscriptions)

| Subscription | CIDR | VNets Used | VNets Free | Utilization | Next Available |
|---|---|---|---|---|---|
| hub-spoke | 10.128.0.0/13 | 0 | 128 | 0% | 10.128.0.0/20 |
| operacoes | 10.136.0.0/13 | 3 | 125 | 2.3% | 10.136.48.0/20 |
| ... | ... | ... | ... | ... | ... |

**Total:** {total_used} / {16 * 128} VNets used across all subscriptions
```

## Calculating Arbitrary Subnets

If the user asks "calculate subnets for X.Y.Z.0/20", enumerate all 16 `/24` blocks:

```
Block 0:  X.Y.(Z+0).0/24   — 256 addresses (251 usable)
Block 1:  X.Y.(Z+1).0/24   — 256 addresses (251 usable)
...
Block 15: X.Y.(Z+15).0/24  — 256 addresses (251 usable)
```

For non-/24 subdivisions, show the requested mask size and how many fit:
- `/22` in `/20` = 4 blocks
- `/25` in `/24` = 2 blocks
- `/27` in `/24` = 8 blocks
- `/26` in `/24` = 4 blocks
