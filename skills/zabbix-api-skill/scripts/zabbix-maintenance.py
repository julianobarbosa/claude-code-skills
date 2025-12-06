#!/usr/bin/env python3
"""
Maintenance window management for Zabbix.

Usage:
    python zabbix-maintenance.py create --name "Weekly Maintenance" --hosts host1,host2 --duration 3600
    python zabbix-maintenance.py create --name "Patching" --groups "Linux servers" --start "2024-01-15 02:00" --duration 7200
    python zabbix-maintenance.py list [--active]
    python zabbix-maintenance.py delete --name "Weekly Maintenance"
    python zabbix-maintenance.py delete --id 123

Environment variables:
    ZABBIX_URL - Zabbix frontend URL
    ZABBIX_TOKEN - API token
"""

import os
import sys
import argparse
import time
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

def parse_datetime(dt_str):
    """Parse datetime string to Unix timestamp."""
    if dt_str is None:
        return int(time.time())

    for fmt in ["%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M"]:
        try:
            return int(datetime.strptime(dt_str, fmt).timestamp())
        except ValueError:
            continue

    raise ValueError(f"Cannot parse datetime: {dt_str}")

def resolve_host_ids(api, host_names):
    """Convert host names to host IDs."""
    host_ids = []
    for name in host_names.split(","):
        name = name.strip()
        result = api.host.get(filter={"host": name}, output=["hostid"])
        if result:
            host_ids.append(result[0]["hostid"])
        else:
            print(f"Warning: Host '{name}' not found")
    return host_ids

def resolve_group_ids(api, group_names):
    """Convert group names to group IDs."""
    group_ids = []
    for name in group_names.split(","):
        name = name.strip()
        result = api.hostgroup.get(filter={"name": name}, output=["groupid"])
        if result:
            group_ids.append(result[0]["groupid"])
        else:
            print(f"Warning: Group '{name}' not found")
    return group_ids

def create_maintenance(api, args):
    """Create a maintenance window."""
    start_time = parse_datetime(args.start)
    duration = int(args.duration)
    end_time = start_time + duration

    params = {
        "name": args.name,
        "active_since": start_time,
        "active_till": end_time,
        "timeperiods": [{
            "timeperiod_type": 0,  # One-time
            "start_date": start_time,
            "period": duration
        }]
    }

    # Add hosts or groups
    if args.hosts:
        host_ids = resolve_host_ids(api, args.hosts)
        if host_ids:
            params["hostids"] = host_ids

    if args.groups:
        group_ids = resolve_group_ids(api, args.groups)
        if group_ids:
            params["groupids"] = group_ids

    if not params.get("hostids") and not params.get("groupids"):
        print("Error: Must specify --hosts or --groups")
        sys.exit(1)

    # Maintenance type
    if args.no_data:
        params["maintenance_type"] = 1  # No data collection
    else:
        params["maintenance_type"] = 0  # With data collection

    # Description
    if args.description:
        params["description"] = args.description

    try:
        result = api.maintenance.create(**params)
        print(f"Created maintenance: {args.name} (id={result['maintenanceids'][0]})")
        print(f"  Start: {datetime.fromtimestamp(start_time)}")
        print(f"  End: {datetime.fromtimestamp(end_time)}")
        print(f"  Duration: {duration}s ({duration//3600}h {(duration%3600)//60}m)")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def list_maintenance(api, args):
    """List maintenance windows."""
    params = {
        "output": ["maintenanceid", "name", "active_since", "active_till",
                   "maintenance_type", "description"],
        "selectHosts": ["host"],
        "selectGroups": ["name"]
    }

    maintenances = api.maintenance.get(**params)

    now = int(time.time())

    for m in maintenances:
        start = int(m["active_since"])
        end = int(m["active_till"])

        # Filter active only if requested
        if args.active and (now < start or now > end):
            continue

        status = "ACTIVE" if start <= now <= end else ("PENDING" if now < start else "EXPIRED")
        mtype = "No data" if m["maintenance_type"] == "1" else "With data"

        print(f"\n[{m['maintenanceid']}] {m['name']} ({status})")
        print(f"  Type: {mtype}")
        print(f"  Start: {datetime.fromtimestamp(start)}")
        print(f"  End: {datetime.fromtimestamp(end)}")

        if m.get("hosts"):
            hosts = [h["host"] for h in m["hosts"]]
            print(f"  Hosts: {', '.join(hosts)}")

        if m.get("groups"):
            groups = [g["name"] for g in m["groups"]]
            print(f"  Groups: {', '.join(groups)}")

def delete_maintenance(api, args):
    """Delete maintenance window."""
    if args.id:
        maintenance_id = args.id
    elif args.name:
        result = api.maintenance.get(filter={"name": args.name},
                                     output=["maintenanceid"])
        if not result:
            print(f"Error: Maintenance '{args.name}' not found")
            sys.exit(1)
        maintenance_id = result[0]["maintenanceid"]
    else:
        print("Error: Must specify --id or --name")
        sys.exit(1)

    try:
        api.maintenance.delete(maintenance_id)
        print(f"Deleted maintenance: {maintenance_id}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Zabbix maintenance management")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Create command
    create_parser = subparsers.add_parser("create", help="Create maintenance window")
    create_parser.add_argument("--name", required=True, help="Maintenance name")
    create_parser.add_argument("--hosts", help="Comma-separated host names")
    create_parser.add_argument("--groups", help="Comma-separated group names")
    create_parser.add_argument("--start", help="Start time (YYYY-MM-DD HH:MM), default: now")
    create_parser.add_argument("--duration", required=True, help="Duration in seconds")
    create_parser.add_argument("--description", help="Description")
    create_parser.add_argument("--no-data", action="store_true",
                               help="Disable data collection during maintenance")

    # List command
    list_parser = subparsers.add_parser("list", help="List maintenance windows")
    list_parser.add_argument("--active", action="store_true", help="Show only active")

    # Delete command
    delete_parser = subparsers.add_parser("delete", help="Delete maintenance window")
    delete_parser.add_argument("--id", help="Maintenance ID")
    delete_parser.add_argument("--name", help="Maintenance name")

    args = parser.parse_args()
    api = get_api()

    if args.command == "create":
        create_maintenance(api, args)
    elif args.command == "list":
        list_maintenance(api, args)
    elif args.command == "delete":
        delete_maintenance(api, args)

if __name__ == "__main__":
    main()
