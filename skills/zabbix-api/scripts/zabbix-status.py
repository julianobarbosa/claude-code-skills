#!/usr/bin/env python3
"""
Zabbix environment diagnostics and status check.

Usage:
    python zabbix-status.py           # Full status report
    python zabbix-status.py problems  # Current problems only
    python zabbix-status.py hosts     # Host status summary
    python zabbix-status.py queue     # Queue status

Environment variables:
    ZABBIX_URL - Zabbix frontend URL
    ZABBIX_TOKEN - API token
"""

import os
import sys
import argparse
from datetime import datetime
from zabbix_utils import ZabbixAPI

def get_api():
    url = os.environ.get("ZABBIX_URL", "http://localhost/zabbix")
    api = ZabbixAPI(url=url)

    if "ZABBIX_TOKEN" in os.environ:
        api.login(token=os.environ["ZABBIX_TOKEN"])
    elif "ZABBIX_USER" in os.environ:
        api.login(user=os.environ["ZABBIX_USER"],
                  password=os.environ.get("ZABBIX_PASSWORD", ""))
    else:
        print("Error: Set ZABBIX_TOKEN or ZABBIX_USER/ZABBIX_PASSWORD")
        sys.exit(1)
    return api

SEVERITY_NAMES = {
    "0": "Not classified",
    "1": "Information",
    "2": "Warning",
    "3": "Average",
    "4": "High",
    "5": "Disaster"
}

SEVERITY_COLORS = {
    "0": "\033[90m",  # Gray
    "1": "\033[94m",  # Blue
    "2": "\033[93m",  # Yellow
    "3": "\033[33m",  # Orange
    "4": "\033[91m",  # Light red
    "5": "\033[31m",  # Red
}
RESET = "\033[0m"

def show_problems(api, limit=50):
    """Show current problems."""
    problems = api.problem.get(
        output=["eventid", "name", "severity", "clock", "acknowledged"],
        selectHosts=["host"],
        recent=True,
        sortfield=["severity", "clock"],
        sortorder=["DESC", "DESC"],
        limit=limit
    )

    if not problems:
        print("✓ No active problems")
        return

    print(f"\n{'='*60}")
    print(f"ACTIVE PROBLEMS ({len(problems)})")
    print(f"{'='*60}")

    # Group by severity
    by_severity = {}
    for p in problems:
        sev = p["severity"]
        if sev not in by_severity:
            by_severity[sev] = []
        by_severity[sev].append(p)

    for sev in sorted(by_severity.keys(), reverse=True):
        color = SEVERITY_COLORS.get(sev, "")
        sev_name = SEVERITY_NAMES.get(sev, "Unknown")
        print(f"\n{color}[{sev_name}]{RESET}")

        for p in by_severity[sev]:
            host = p["hosts"][0]["host"] if p.get("hosts") else "Unknown"
            time_str = datetime.fromtimestamp(int(p["clock"])).strftime("%Y-%m-%d %H:%M")
            ack = "✓" if p["acknowledged"] == "1" else " "
            print(f"  {ack} [{time_str}] {host}: {p['name']}")

def show_hosts_status(api):
    """Show host status summary."""
    hosts = api.host.get(
        output=["hostid", "host", "name", "status", "available"],
        selectInterfaces=["ip", "available"]
    )

    total = len(hosts)
    enabled = sum(1 for h in hosts if h["status"] == "0")
    disabled = total - enabled

    available = sum(1 for h in hosts if h.get("available") == "1")
    unavailable = sum(1 for h in hosts if h.get("available") == "2")
    unknown = total - available - unavailable

    print(f"\n{'='*40}")
    print("HOST STATUS")
    print(f"{'='*40}")
    print(f"Total hosts:      {total}")
    print(f"  Enabled:        {enabled}")
    print(f"  Disabled:       {disabled}")
    print(f"\nAgent availability:")
    print(f"  Available:      {available}")
    print(f"  Unavailable:    {unavailable}")
    print(f"  Unknown:        {unknown}")

    # Show unavailable hosts
    unavailable_hosts = [h for h in hosts if h.get("available") == "2"]
    if unavailable_hosts:
        print(f"\nUnavailable hosts ({len(unavailable_hosts)}):")
        for h in unavailable_hosts[:10]:
            ip = h["interfaces"][0]["ip"] if h.get("interfaces") else "N/A"
            print(f"  - {h['host']} ({ip})")
        if len(unavailable_hosts) > 10:
            print(f"  ... and {len(unavailable_hosts) - 10} more")

def show_queue(api):
    """Show item queue status."""
    # Get items not yet processed
    try:
        # This requires specific permissions
        queue = api.queue.get(output="extend")

        if not queue:
            print("✓ Queue is empty")
            return

        print(f"\n{'='*40}")
        print("QUEUE STATUS")
        print(f"{'='*40}")

        # Group by delay
        delays = {}
        for item in queue:
            delay = int(item.get("delay", 0))
            if delay not in delays:
                delays[delay] = 0
            delays[delay] += 1

        for delay in sorted(delays.keys()):
            print(f"  {delay}s+ delay: {delays[delay]} items")

    except Exception as e:
        print(f"Queue status unavailable: {e}")

def show_full_status(api):
    """Show full environment status."""
    print(f"\n{'='*60}")
    print("ZABBIX ENVIRONMENT STATUS")
    print(f"{'='*60}")

    # API info
    version = api.api_version()
    print(f"API Version: {version}")
    print(f"URL: {os.environ.get('ZABBIX_URL', 'http://localhost/zabbix')}")

    # Counts
    hosts = api.host.get(countOutput=True)
    templates = api.template.get(countOutput=True)
    items = api.item.get(countOutput=True, monitored=True)
    triggers = api.trigger.get(countOutput=True, monitored=True)

    print(f"\nObject counts:")
    print(f"  Hosts:     {hosts}")
    print(f"  Templates: {templates}")
    print(f"  Items:     {items}")
    print(f"  Triggers:  {triggers}")

    # Problems summary
    problems = api.problem.get(countOutput=True, recent=True)
    print(f"\nActive problems: {problems}")

    # Show details
    show_hosts_status(api)
    show_problems(api, limit=20)

def main():
    parser = argparse.ArgumentParser(description="Zabbix status check")
    parser.add_argument("command", nargs="?", default="full",
                       choices=["full", "problems", "hosts", "queue"],
                       help="Status type (default: full)")
    parser.add_argument("--limit", type=int, default=50,
                       help="Limit results (for problems)")

    args = parser.parse_args()
    api = get_api()

    if args.command == "full":
        show_full_status(api)
    elif args.command == "problems":
        show_problems(api, args.limit)
    elif args.command == "hosts":
        show_hosts_status(api)
    elif args.command == "queue":
        show_queue(api)

if __name__ == "__main__":
    main()
