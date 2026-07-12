#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///
"""
Azure Network Calculator — CIDR planning, gap analysis, overlap detection.

Uses only Python stdlib (ipaddress, json, argparse). Zero external deps.
Azure reserves 5 IPs per subnet: .0 (network), .1 (gateway), .2-.3 (DNS), broadcast.

Usage:
    python3 network-calc.py calculate 10.248.0.0/20
    python3 network-calc.py calculate --from-hosts 500
    python3 network-calc.py analyze --vnet 10.248.0.0/20 --subnets 10.248.0.0/22,10.248.4.0/22
    python3 network-calc.py validate --vnet 10.248.0.0/20 --subnets 10.248.0.0/22,10.248.4.0/22
    python3 network-calc.py plan-multi --base 10.248.0.0/16 --envs 3 --prefix 20
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import math
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

AZURE_RESERVED_IPS = 5

# Azure minimum subnet sizes by purpose
AZURE_MIN_PREFIX = {
    "AzureBastionSubnet": 26,
    "GatewaySubnet": 27,
    "AzureFirewallSubnet": 26,
    "AzureFirewallManagementSubnet": 26,
    "RouteServerSubnet": 27,
}


def azure_usable_hosts(prefix_len: int) -> int:
    """Calculate usable hosts in an Azure subnet (total - 5 reserved)."""
    total = 2 ** (32 - prefix_len)
    return max(total - AZURE_RESERVED_IPS, 0)


def min_prefix_for_hosts(hosts_needed: int) -> int:
    """Calculate minimum CIDR prefix length for N usable hosts (Azure-adjusted)."""
    total_needed = hosts_needed + AZURE_RESERVED_IPS
    bits = math.ceil(math.log2(total_needed))
    return 32 - bits


def cidr_info(cidr_str: str) -> dict:
    """Return comprehensive info about a CIDR block."""
    net = ipaddress.IPv4Network(cidr_str, strict=False)
    prefix = net.prefixlen
    total = net.num_addresses
    usable = azure_usable_hosts(prefix)
    hosts = list(net.hosts())

    return {
        "cidr": str(net),
        "network": str(net.network_address),
        "broadcast": str(net.broadcast_address),
        "netmask": str(net.netmask),
        "prefix_length": prefix,
        "total_ips": total,
        "azure_reserved": min(AZURE_RESERVED_IPS, total),
        "usable_hosts": usable,
        "first_usable": str(hosts[0]) if hosts else None,
        "last_usable": str(hosts[-1]) if hosts else None,
        "wildcard": str(net.hostmask),
    }


def find_gaps(vnet_cidr: str, subnet_cidrs: list[str]) -> list[dict]:
    """Find unallocated address ranges within a VNet."""
    vnet = ipaddress.IPv4Network(vnet_cidr, strict=False)
    subnets = sorted(
        [ipaddress.IPv4Network(s, strict=False) for s in subnet_cidrs],
        key=lambda n: n.network_address,
    )

    gaps = []
    current = int(vnet.network_address)
    vnet_end = int(vnet.broadcast_address)

    for subnet in subnets:
        subnet_start = int(subnet.network_address)
        subnet_end = int(subnet.broadcast_address)

        if subnet_start > current:
            gap_start = ipaddress.IPv4Address(current)
            gap_end = ipaddress.IPv4Address(subnet_start - 1)
            gap_size = subnet_start - current
            # Break into valid CIDR blocks
            gap_cidrs = list(
                ipaddress.summarize_address_range(gap_start, gap_end)
            )
            gaps.append({
                "start": str(gap_start),
                "end": str(gap_end),
                "size": gap_size,
                "cidrs": [str(c) for c in gap_cidrs],
                "usable_hosts": sum(azure_usable_hosts(c.prefixlen) for c in gap_cidrs),
            })

        current = max(current, subnet_end + 1)

    # Check for gap after last subnet
    if current <= vnet_end:
        gap_start = ipaddress.IPv4Address(current)
        gap_end = ipaddress.IPv4Address(vnet_end)
        gap_size = vnet_end - current + 1
        gap_cidrs = list(
            ipaddress.summarize_address_range(gap_start, gap_end)
        )
        gaps.append({
            "start": str(gap_start),
            "end": str(gap_end),
            "size": gap_size,
            "cidrs": [str(c) for c in gap_cidrs],
            "usable_hosts": sum(azure_usable_hosts(c.prefixlen) for c in gap_cidrs),
        })

    return gaps


def find_overlaps(subnet_cidrs: list[str]) -> list[dict]:
    """Detect overlapping CIDR ranges."""
    nets = [(s, ipaddress.IPv4Network(s, strict=False)) for s in subnet_cidrs]
    overlaps = []

    for i, (name_a, net_a) in enumerate(nets):
        for j, (name_b, net_b) in enumerate(nets):
            if i >= j:
                continue
            if net_a.overlaps(net_b):
                overlap_start = max(int(net_a.network_address), int(net_b.network_address))
                overlap_end = min(int(net_a.broadcast_address), int(net_b.broadcast_address))
                overlaps.append({
                    "subnet_a": name_a,
                    "subnet_b": name_b,
                    "overlap_ips": overlap_end - overlap_start + 1,
                    "overlap_range": f"{ipaddress.IPv4Address(overlap_start)} - {ipaddress.IPv4Address(overlap_end)}",
                })

    return overlaps


def check_azure_constraints(named_subnets: dict[str, str]) -> list[dict]:
    """Validate Azure-specific subnet constraints."""
    violations = []

    for name, cidr in named_subnets.items():
        net = ipaddress.IPv4Network(cidr, strict=False)
        if name in AZURE_MIN_PREFIX:
            min_pf = AZURE_MIN_PREFIX[name]
            if net.prefixlen > min_pf:
                violations.append({
                    "subnet": name,
                    "cidr": cidr,
                    "violation": f"Prefix /{net.prefixlen} too small. {name} requires minimum /{min_pf} ({2**(32-min_pf)} IPs)",
                    "severity": "ERROR",
                })

        # General minimum: /29
        if net.prefixlen > 29:
            violations.append({
                "subnet": name,
                "cidr": cidr,
                "violation": f"Prefix /{net.prefixlen} below Azure minimum /29 (8 IPs, 3 usable)",
                "severity": "ERROR",
            })

    return violations


def detect_anti_patterns(named_subnets: dict[str, str], security_rules: list[dict] | None = None) -> list[dict]:
    """Detect network anti-patterns."""
    warnings = []

    # Check for subnets without standard naming
    for name, cidr in named_subnets.items():
        net = ipaddress.IPv4Network(cidr, strict=False)
        # Warn on very large subnets that waste space
        if net.prefixlen < 20 and name not in ("GatewaySubnet",):
            warnings.append({
                "type": "oversized_subnet",
                "subnet": name,
                "cidr": cidr,
                "message": f"Subnet /{net.prefixlen} allocates {net.num_addresses} IPs. Consider if this is necessary.",
                "severity": "WARNING",
            })

    if security_rules:
        for rule in security_rules:
            src = rule.get("source_address_prefix", "")
            dst_port = rule.get("destination_port_range", "")
            direction = rule.get("direction", "")

            if src == "0.0.0.0/0" and direction == "Inbound":
                warnings.append({
                    "type": "open_ingress",
                    "rule": rule.get("name", "unknown"),
                    "message": "Inbound rule allows traffic from 0.0.0.0/0 (entire internet). Restrict to specific CIDRs.",
                    "severity": "CRITICAL",
                })

            if dst_port == "*" and direction == "Inbound":
                warnings.append({
                    "type": "wildcard_ports",
                    "rule": rule.get("name", "unknown"),
                    "message": "Inbound rule allows all destination ports. Restrict to specific ports.",
                    "severity": "HIGH",
                })

    return warnings


def parse_tfvars_network(tfvars_path: str) -> dict:
    """Parse network-related variables from a terraform.tfvars file."""
    content = Path(tfvars_path).read_text()
    result = {"subnets": {}, "vnet": None}

    # Parse list variables: var_name = ["value1", "value2"]
    list_pattern = re.compile(r'(\w+)\s*=\s*\[([^\]]*)\]', re.DOTALL)
    for match in list_pattern.finditer(content):
        var_name = match.group(1)
        values = re.findall(r'"([^"]*)"', match.group(2))

        if var_name == "vnet_address_space" and values:
            result["vnet"] = values[0]
        elif var_name.startswith("vnet_subnet_") or var_name.startswith("vnet_azure_"):
            # Map variable name to subnet name
            subnet_name = var_name.replace("vnet_subnet_", "").replace("vnet_azure_subnet_", "")
            if values:
                result["subnets"][subnet_name] = values[0]

    return result


def split_cidr(cidr_str: str, new_prefix: int) -> list[dict]:
    """Split a CIDR into smaller subnets of a given prefix length."""
    net = ipaddress.IPv4Network(cidr_str, strict=False)
    if new_prefix <= net.prefixlen:
        return [{"error": f"New prefix /{new_prefix} must be longer than /{net.prefixlen}"}]

    subnets = list(net.subnets(new_prefix=new_prefix))
    return [cidr_info(str(s)) for s in subnets]


def first_fit(vnet_cidr: str, existing_cidrs: list[str], hosts_needed: int) -> dict | None:
    """Find the first available gap that fits the required number of hosts."""
    prefix = min_prefix_for_hosts(hosts_needed)
    subnet_size = 2 ** (32 - prefix)
    gaps = find_gaps(vnet_cidr, existing_cidrs)

    for gap in gaps:
        if gap["size"] >= subnet_size:
            # Align to subnet boundary within gap
            gap_start = int(ipaddress.IPv4Address(gap["start"]))
            aligned_start = ((gap_start + subnet_size - 1) // subnet_size) * subnet_size

            if aligned_start + subnet_size - 1 <= int(ipaddress.IPv4Address(gap["end"])):
                new_cidr = f"{ipaddress.IPv4Address(aligned_start)}/{prefix}"
                info = cidr_info(new_cidr)
                info["placement"] = f"first-fit in gap {gap['start']} - {gap['end']}"
                return info

    return None


# ── Subcommand handlers ──────────────────────────────────────────────────

def cmd_calculate(args):
    """Handle 'calculate' subcommand."""
    if args.from_hosts:
        prefix = min_prefix_for_hosts(args.from_hosts)
        print(json.dumps({
            "hosts_requested": args.from_hosts,
            "minimum_prefix": prefix,
            "subnet_mask": str(ipaddress.IPv4Network(f"0.0.0.0/{prefix}").netmask),
            "total_ips": 2 ** (32 - prefix),
            "usable_hosts": azure_usable_hosts(prefix),
            "recommendation": f"Use /{prefix} for {args.from_hosts} hosts ({azure_usable_hosts(prefix)} usable with Azure 5-IP reservation)",
        }, indent=2))
        return

    if args.split:
        results = split_cidr(args.cidr, args.split)
        print(json.dumps({"source": args.cidr, "split_prefix": args.split, "subnets": results}, indent=2))
        return

    if args.cidr:
        print(json.dumps(cidr_info(args.cidr), indent=2))
    else:
        print("Error: provide a CIDR (e.g., 10.0.0.0/20) or --from-hosts N", file=sys.stderr)
        sys.exit(1)


def cmd_analyze(args):
    """Handle 'analyze' subcommand."""
    vnet = args.vnet
    subnets = {}

    if args.from_tfvars:
        parsed = parse_tfvars_network(args.from_tfvars)
        if parsed["vnet"]:
            vnet = parsed["vnet"]
        subnets = parsed["subnets"]
    elif args.subnets:
        for i, s in enumerate(args.subnets.split(",")):
            subnets[f"subnet_{i}"] = s.strip()

    if not vnet:
        print("Error: provide --vnet CIDR or --from-tfvars PATH", file=sys.stderr)
        sys.exit(1)

    vnet_info = cidr_info(vnet)
    subnet_list = list(subnets.values())

    # Allocation table
    allocations = []
    total_allocated = 0
    for name, cidr in subnets.items():
        info = cidr_info(cidr)
        total_allocated += info["total_ips"]
        allocations.append({
            "name": name,
            "cidr": cidr,
            "total_ips": info["total_ips"],
            "usable_hosts": info["usable_hosts"],
        })

    # Gaps
    gaps = find_gaps(vnet, subnet_list) if subnet_list else []
    total_unallocated = sum(g["size"] for g in gaps)

    utilization = (total_allocated / vnet_info["total_ips"] * 100) if vnet_info["total_ips"] > 0 else 0

    result = {
        "vnet": vnet_info,
        "allocations": allocations,
        "total_allocated_ips": total_allocated,
        "total_unallocated_ips": total_unallocated,
        "utilization_percent": round(utilization, 1),
        "gaps": gaps,
        "subnet_count": len(allocations),
    }

    print(json.dumps(result, indent=2))


def cmd_validate(args):
    """Handle 'validate' subcommand."""
    vnet = args.vnet
    subnets = {}

    if args.from_tfvars:
        parsed = parse_tfvars_network(args.from_tfvars)
        if parsed["vnet"]:
            vnet = parsed["vnet"]
        subnets = parsed["subnets"]
    elif args.subnets:
        for i, s in enumerate(args.subnets.split(",")):
            subnets[f"subnet_{i}"] = s.strip()

    subnet_list = list(subnets.values())
    issues = []

    # Overlap detection
    overlaps = find_overlaps(subnet_list)
    for o in overlaps:
        issues.append({"type": "overlap", "severity": "CRITICAL", **o})

    # VNet containment check
    if vnet:
        vnet_net = ipaddress.IPv4Network(vnet, strict=False)
        for name, cidr in subnets.items():
            subnet_net = ipaddress.IPv4Network(cidr, strict=False)
            if not subnet_net.subnet_of(vnet_net):
                issues.append({
                    "type": "out_of_vnet",
                    "severity": "CRITICAL",
                    "subnet": name,
                    "cidr": cidr,
                    "message": f"Subnet {cidr} is not within VNet {vnet}",
                })

    # Azure constraints
    constraints = check_azure_constraints(subnets)
    issues.extend([{"type": "azure_constraint", **c} for c in constraints])

    # Anti-patterns
    anti = detect_anti_patterns(subnets)
    issues.extend(anti)

    result = {
        "valid": len([i for i in issues if i["severity"] in ("CRITICAL", "ERROR")]) == 0,
        "issues_count": len(issues),
        "critical": len([i for i in issues if i["severity"] == "CRITICAL"]),
        "errors": len([i for i in issues if i["severity"] == "ERROR"]),
        "warnings": len([i for i in issues if i["severity"] in ("WARNING", "HIGH")]),
        "issues": issues,
    }

    print(json.dumps(result, indent=2))

    if not result["valid"]:
        sys.exit(1)


def cmd_plan_multi(args):
    """Handle 'plan-multi' subcommand."""
    base = ipaddress.IPv4Network(args.base, strict=False)
    env_count = args.envs
    env_prefix = args.prefix

    env_subnet_size = 2 ** (32 - env_prefix)
    total_needed = env_subnet_size * env_count

    if total_needed > base.num_addresses:
        print(json.dumps({
            "error": f"Cannot fit {env_count} /{env_prefix} VNets ({total_needed} IPs) in {args.base} ({base.num_addresses} IPs)",
        }, indent=2))
        sys.exit(1)

    env_names = args.names.split(",") if args.names else [f"env_{i}" for i in range(env_count)]
    environments = []
    current = int(base.network_address)

    for i, name in enumerate(env_names[:env_count]):
        env_cidr = f"{ipaddress.IPv4Address(current)}/{env_prefix}"
        info = cidr_info(env_cidr)
        info["environment"] = name.strip()
        environments.append(info)
        current += env_subnet_size

    # Validate no overlaps
    env_cidrs = [e["cidr"] for e in environments]
    overlaps = find_overlaps(env_cidrs)

    result = {
        "base_cidr": args.base,
        "environments": environments,
        "env_count": env_count,
        "env_prefix": env_prefix,
        "total_allocated": env_subnet_size * env_count,
        "remaining_in_base": base.num_addresses - total_needed,
        "overlaps": overlaps,
        "peering_safe": len(overlaps) == 0,
    }

    print(json.dumps(result, indent=2))


def cmd_first_fit(args):
    """Handle 'first-fit' subcommand — find optimal placement for a new subnet."""
    subnets = []
    if args.subnets:
        subnets = [s.strip() for s in args.subnets.split(",")]
    elif args.from_tfvars:
        parsed = parse_tfvars_network(args.from_tfvars)
        if parsed["vnet"]:
            args.vnet = parsed["vnet"]
        subnets = list(parsed["subnets"].values())

    result = first_fit(args.vnet, subnets, args.hosts)
    if result:
        result["requested_hosts"] = args.hosts
        print(json.dumps(result, indent=2))
    else:
        print(json.dumps({
            "error": f"No gap large enough for {args.hosts} hosts in {args.vnet}",
            "requested_hosts": args.hosts,
            "gaps": find_gaps(args.vnet, subnets),
        }, indent=2))
        sys.exit(1)


# ── CLI ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Azure Network Calculator — CIDR planning, gap analysis, overlap detection",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # calculate
    calc = sub.add_parser("calculate", help="CIDR info, host sizing, subnet splitting")
    calc.add_argument("cidr", nargs="?", help="CIDR to analyze (e.g., 10.0.0.0/20)")
    calc.add_argument("--from-hosts", type=int, help="Calculate minimum prefix for N hosts")
    calc.add_argument("--split", type=int, help="Split CIDR into subnets of this prefix")

    # analyze
    analyze = sub.add_parser("analyze", help="Analyze VNet layout: utilization, gaps")
    analyze.add_argument("--vnet", help="VNet CIDR (e.g., 10.248.0.0/20)")
    analyze.add_argument("--subnets", help="Comma-separated subnet CIDRs")
    analyze.add_argument("--from-tfvars", help="Read from terraform.tfvars file")

    # validate
    validate = sub.add_parser("validate", help="Validate for overlaps, Azure constraints")
    validate.add_argument("--vnet", help="VNet CIDR")
    validate.add_argument("--subnets", help="Comma-separated subnet CIDRs")
    validate.add_argument("--from-tfvars", help="Read from terraform.tfvars file")

    # plan-multi
    plan = sub.add_parser("plan-multi", help="Plan multi-environment VNet allocation")
    plan.add_argument("--base", required=True, help="Base CIDR to divide")
    plan.add_argument("--envs", type=int, default=3, help="Number of environments (default: 3)")
    plan.add_argument("--prefix", type=int, default=20, help="Prefix per environment (default: /20)")
    plan.add_argument("--names", help="Comma-separated env names (default: env_0,env_1,...)")

    # first-fit
    ff = sub.add_parser("first-fit", help="Find optimal placement for a new subnet")
    ff.add_argument("--vnet", help="VNet CIDR")
    ff.add_argument("--subnets", help="Comma-separated existing subnet CIDRs")
    ff.add_argument("--from-tfvars", help="Read from terraform.tfvars file")
    ff.add_argument("--hosts", type=int, required=True, help="Number of usable hosts needed")

    args = parser.parse_args()

    commands = {
        "calculate": cmd_calculate,
        "analyze": cmd_analyze,
        "validate": cmd_validate,
        "plan-multi": cmd_plan_multi,
        "first-fit": cmd_first_fit,
    }

    commands[args.command](args)


if __name__ == "__main__":
    main()
