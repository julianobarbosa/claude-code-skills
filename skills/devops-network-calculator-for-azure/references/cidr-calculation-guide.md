# CIDR Calculation Guide

Comprehensive reference for IP address planning in Azure environments.

## CIDR Notation Fundamentals

A CIDR block `10.248.0.0/20` means:
- **Network address:** 10.248.0.0
- **Prefix length:** /20 (20 bits for network, 12 bits for hosts)
- **Total addresses:** 2^12 = 4,096
- **Subnet mask:** 255.255.240.0
- **Broadcast:** 10.248.15.255
- **Usable range:** 10.248.0.1 - 10.248.15.254

## Subnet Sizing Formula

Given N hosts needed:
```
min_prefix = 32 - ceil(log2(N + 5))
```

The +5 accounts for Azure's 5 reserved addresses per subnet.

**Growth planning:** Always plan for 2x current need. If you need 100 hosts today, plan for 200 (use /24 = 251 usable, not /25 = 123 usable).

### Examples

| Hosts Needed | Add Azure Reserved | Total | Min Prefix | Usable Hosts |
|-------------|-------------------|-------|------------|-------------|
| 10 | +5 = 15 | 16 | /28 | 11 |
| 30 | +5 = 35 | 64 | /26 | 59 |
| 100 | +5 = 105 | 128 | /25 | 123 |
| 250 | +5 = 255 | 256 | /24 | 251 |
| 500 | +5 = 505 | 512 | /23 | 507 |
| 1000 | +5 = 1005 | 1024 | /22 | 1,019 |

## Gap Analysis

To find unallocated space within a VNet:
1. List all subnet CIDRs
2. Sort by network address (ascending)
3. Check for gaps between each subnet's broadcast+1 and the next subnet's network address
4. Report gaps as valid CIDR blocks using `summarize_address_range()`

### Real Example: This Project (10.248.0.0/20)

```
VNet: 10.248.0.0/20 (4,096 IPs)

Allocated:
  GatewaySubnet:        10.248.0.0/22   (1,024 IPs)
  PublicSubnet:          10.248.4.0/22   (1,024 IPs)
  AzureBastionSubnet:   10.248.8.0/26   (64 IPs)
  PrivateSubnet:         10.248.9.0/24   (256 IPs)
  ─────────────────────────────────────────────
  Total allocated:       2,368 IPs (57.8%)

Gaps (unallocated):
  Gap 1: 10.248.8.64  - 10.248.8.255   (192 IPs)
    = 10.248.8.64/26 + 10.248.8.128/25
  Gap 2: 10.248.10.0  - 10.248.15.255  (1,536 IPs)
    = 10.248.10.0/23 + 10.248.12.0/22
  ─────────────────────────────────────────────
  Total unallocated:     1,728 IPs (42.2%)
```

## Overlap Detection

Two CIDRs overlap when either contains the other's network address.

```
OVERLAP: 10.248.8.0/24 and 10.248.8.0/26
  10.248.8.0/24 range: 10.248.8.0 - 10.248.8.255
  10.248.8.0/26 range: 10.248.8.0 - 10.248.8.63
  Overlap: 64 IPs in conflict
```

Python: `ipaddress.IPv4Network('10.248.8.0/24').overlaps(IPv4Network('10.248.8.0/26'))` returns True.

## Address Space Planning Best Practices

### RFC 1918 Private Address Ranges

| Range | CIDR | Total IPs | Typical Use |
|-------|------|-----------|-------------|
| 10.0.0.0 - 10.255.255.255 | 10.0.0.0/8 | 16.7M | Enterprise networks |
| 172.16.0.0 - 172.31.255.255 | 172.16.0.0/12 | 1M | Medium networks |
| 192.168.0.0 - 192.168.255.255 | 192.168.0.0/16 | 65K | Small networks |

### Azure-Specific Ranges to Avoid

| Range | Reason |
|-------|--------|
| 168.63.129.16/32 | Azure platform health monitoring |
| 169.254.0.0/16 | APIPA / link-local |
| 100.64.0.0/10 | CGN (Carrier-Grade NAT) |

### Recommended Allocation Strategy

1. **Assign a /16 per major site or region** (65K IPs)
2. **Subdivide into /20 per environment** (4K IPs per env)
3. **Leave /24 gaps between VNets** for future peering
4. **Document every allocation** in your network address inventory

## Subnet Alignment Rules

CIDR blocks must be naturally aligned. A /24 must start on a 256-address boundary, a /22 on a 1024-address boundary, etc.

**Alignment formula:** `network_address % (2^(32 - prefix)) == 0`

### Common Alignment Mistakes

| Attempted CIDR | Problem | Correct Alternative |
|---------------|---------|-------------------|
| 10.248.1.0/22 | /22 must start at .0.0, .4.0, .8.0, etc. | 10.248.0.0/22 or 10.248.4.0/22 |
| 10.248.3.0/23 | /23 must start at even third octet | 10.248.2.0/23 or 10.248.4.0/23 |
| 10.248.8.64/25 | /25 must start at .0 or .128 | 10.248.8.0/25 or 10.248.8.128/25 |

## Supernetting and Summarization

When multiple contiguous subnets can be expressed as a single larger block:

```
10.248.0.0/24 + 10.248.1.0/24 = 10.248.0.0/23
10.248.0.0/23 + 10.248.2.0/23 = 10.248.0.0/22
```

**Rule:** Two adjacent CIDRs of the same size can be summarized only if the first starts on a boundary that is a multiple of the combined size.

## Conversion Quick Reference

| Prefix | Mask | Wildcard | Block Size |
|--------|------|----------|------------|
| /16 | 255.255.0.0 | 0.0.255.255 | 65,536 |
| /17 | 255.255.128.0 | 0.0.127.255 | 32,768 |
| /18 | 255.255.192.0 | 0.0.63.255 | 16,384 |
| /19 | 255.255.224.0 | 0.0.31.255 | 8,192 |
| /20 | 255.255.240.0 | 0.0.15.255 | 4,096 |
| /21 | 255.255.248.0 | 0.0.7.255 | 2,048 |
| /22 | 255.255.252.0 | 0.0.3.255 | 1,024 |
| /23 | 255.255.254.0 | 0.0.1.255 | 512 |
| /24 | 255.255.255.0 | 0.0.0.255 | 256 |
| /25 | 255.255.255.128 | 0.0.0.127 | 128 |
| /26 | 255.255.255.192 | 0.0.0.63 | 64 |
| /27 | 255.255.255.224 | 0.0.0.31 | 32 |
| /28 | 255.255.255.240 | 0.0.0.15 | 16 |
| /29 | 255.255.255.248 | 0.0.0.7 | 8 |
| /30 | 255.255.255.252 | 0.0.0.3 | 4 |
| /31 | 255.255.255.254 | 0.0.0.1 | 2 |
| /32 | 255.255.255.255 | 0.0.0.0 | 1 |

## Using the Calculator Script

```bash
# Basic CIDR info
python3 scripts/network-calc.py calculate 10.248.0.0/20

# How many hosts fit in a /23?
python3 scripts/network-calc.py calculate 10.0.0.0/23

# What prefix do I need for 500 hosts?
python3 scripts/network-calc.py calculate --from-hosts 500

# Split a /20 into /22 subnets
python3 scripts/network-calc.py calculate 10.248.0.0/20 --split 22

# Analyze current VNet utilization
python3 scripts/network-calc.py analyze --vnet 10.248.0.0/20 \
  --subnets "10.248.0.0/22,10.248.4.0/22,10.248.8.0/26,10.248.9.0/24"

# Find first available gap for 500 hosts
python3 scripts/network-calc.py first-fit --vnet 10.248.0.0/20 \
  --subnets "10.248.0.0/22,10.248.4.0/22,10.248.8.0/26,10.248.9.0/24" \
  --hosts 500

# Validate for overlaps (pre-commit hook)
python3 scripts/network-calc.py validate --vnet 10.248.0.0/20 \
  --subnets "10.248.0.0/22,10.248.4.0/22,10.248.8.0/26,10.248.9.0/24"
```
