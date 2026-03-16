# ValidateCidr Workflow

Check whether a CIDR range is valid, within a known subscription, and free from overlaps.

## Inputs

1. **CIDR to validate** — e.g., `10.248.0.0/20` or `10.144.17.0/24`

## Steps

### Step 1: Parse the CIDR

Extract:
- Network address
- Prefix length (mask)
- Range start (network address)
- Range end (broadcast address)
- Total addresses: `2^(32 - mask)`

### Step 2: Identify Subscription

Read [CidrMasterAllocation.md](../CidrMasterAllocation.md).

For each subscription, check if the input CIDR falls entirely within the subscription's `/13` range:
- Input start >= subscription start AND input end <= subscription end

If no subscription matches: **FAIL** — "CIDR is outside all known subscription ranges."

### Step 3: Check VNet-Level Overlap

For the matched subscription, check against all known VNet allocations:

Two CIDRs overlap if:
```
range_a_start <= range_b_end AND range_b_start <= range_a_end
```

For each known VNet in the subscription:
- If overlap detected: **FAIL** — "Overlaps with {VNet name} ({VNet CIDR})"

### Step 4: Check Subnet-Level Overlap

If the input is a subnet-sized CIDR (/24 or smaller), also check against known subnet allocations within the containing VNet.

### Step 5: Validate Alignment

- If `/20`: verify third octet is a multiple of 16 (relative to subscription base)
- If `/22`: verify third octet is a multiple of 4 (relative to VNet base)
- If `/24`: verify fourth octet is 0
- If `/27`: verify fourth octet is 0, 32, 64, 96, 128, 160, 192, or 224
- If `/26`: verify fourth octet is 0, 64, 128, or 192

If misaligned: **WARN** — "CIDR is not naturally aligned for its mask."

### Step 6: Output

```
## CIDR Validation: {input_cidr}

| Check | Result | Details |
|-------|--------|---------|
| Valid CIDR | PASS/FAIL | {parsed details} |
| Within subscription | PASS/FAIL | {subscription name} ({subscription CIDR}) |
| No VNet overlap | PASS/FAIL | {overlap details if any} |
| No subnet overlap | PASS/FAIL/N/A | {overlap details if any} |
| Alignment | PASS/WARN | {alignment details} |

**Overall: PASS / FAIL**
```

If FAIL, suggest the nearest valid alternative:
- Next available VNet index (for /20)
- Next available /24 block within the VNet (for /24)
