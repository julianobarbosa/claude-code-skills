#!/usr/bin/env python3
"""
Bulk host management for Zabbix via API.
Supports create, update, delete, and export operations from CSV.

Usage:
    python zabbix-bulk-hosts.py create hosts.csv
    python zabbix-bulk-hosts.py update hosts.csv
    python zabbix-bulk-hosts.py delete hosts.csv
    python zabbix-bulk-hosts.py export output.csv [--group GROUP_NAME]

Environment variables:
    ZABBIX_URL - Zabbix frontend URL (default: http://localhost/zabbix)
    ZABBIX_TOKEN - API token (preferred)
    ZABBIX_USER - Username (fallback)
    ZABBIX_PASSWORD - Password (fallback)

CSV format for create/update:
    hostname,ip,groups,templates,description
    server01,192.168.1.100,Linux servers,Linux by Zabbix agent,Web server
"""

import os
import sys
import csv
import argparse
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

def resolve_groups(api, group_names):
    """Convert group names to group IDs."""
    groups = []
    for name in group_names.split(","):
        name = name.strip()
        result = api.hostgroup.get(filter={"name": name}, output=["groupid"])
        if result:
            groups.append({"groupid": result[0]["groupid"]})
        else:
            # Create group if not exists
            result = api.hostgroup.create(name=name)
            groups.append({"groupid": result["groupids"][0]})
    return groups

def resolve_templates(api, template_names):
    """Convert template names to template IDs."""
    templates = []
    for name in template_names.split(","):
        name = name.strip()
        if not name:
            continue
        result = api.template.get(filter={"host": name}, output=["templateid"])
        if result:
            templates.append({"templateid": result[0]["templateid"]})
        else:
            print(f"Warning: Template '{name}' not found")
    return templates

def create_hosts(api, csv_file):
    """Create hosts from CSV file."""
    with open(csv_file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            hostname = row.get("hostname", "").strip()
            ip = row.get("ip", "").strip()

            if not hostname or not ip:
                print(f"Skipping row: missing hostname or ip")
                continue

            # Check if host exists
            existing = api.host.get(filter={"host": hostname}, output=["hostid"])
            if existing:
                print(f"Skip: {hostname} already exists")
                continue

            try:
                groups = resolve_groups(api, row.get("groups", "Discovered hosts"))
                templates = resolve_templates(api, row.get("templates", ""))

                params = {
                    "host": hostname,
                    "groups": groups,
                    "interfaces": [{
                        "type": 1,
                        "main": 1,
                        "useip": 1,
                        "ip": ip,
                        "dns": "",
                        "port": "10050"
                    }]
                }

                if templates:
                    params["templates"] = templates
                if row.get("description"):
                    params["description"] = row["description"]

                result = api.host.create(**params)
                print(f"Created: {hostname} (hostid={result['hostids'][0]})")

            except Exception as e:
                print(f"Error creating {hostname}: {e}")

def update_hosts(api, csv_file):
    """Update existing hosts from CSV file."""
    with open(csv_file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            hostname = row.get("hostname", "").strip()
            if not hostname:
                continue

            existing = api.host.get(filter={"host": hostname}, output=["hostid"])
            if not existing:
                print(f"Skip: {hostname} not found")
                continue

            hostid = existing[0]["hostid"]

            try:
                params = {"hostid": hostid}

                if row.get("groups"):
                    params["groups"] = resolve_groups(api, row["groups"])
                if row.get("templates"):
                    params["templates"] = resolve_templates(api, row["templates"])
                if row.get("description"):
                    params["description"] = row["description"]

                api.host.update(**params)
                print(f"Updated: {hostname}")

            except Exception as e:
                print(f"Error updating {hostname}: {e}")

def delete_hosts(api, csv_file):
    """Delete hosts from CSV file."""
    with open(csv_file) as f:
        reader = csv.DictReader(f)
        for row in reader:
            hostname = row.get("hostname", "").strip()
            if not hostname:
                continue

            existing = api.host.get(filter={"host": hostname}, output=["hostid"])
            if not existing:
                print(f"Skip: {hostname} not found")
                continue

            try:
                api.host.delete(existing[0]["hostid"])
                print(f"Deleted: {hostname}")
            except Exception as e:
                print(f"Error deleting {hostname}: {e}")

def export_hosts(api, csv_file, group_name=None):
    """Export hosts to CSV file."""
    params = {
        "output": ["host", "name", "description"],
        "selectInterfaces": ["ip"],
        "selectGroups": ["name"],
        "selectParentTemplates": ["host"]
    }

    if group_name:
        groups = api.hostgroup.get(filter={"name": group_name}, output=["groupid"])
        if groups:
            params["groupids"] = [groups[0]["groupid"]]

    hosts = api.host.get(**params)

    with open(csv_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["hostname", "ip", "groups", "templates", "description"])

        for host in hosts:
            ip = host["interfaces"][0]["ip"] if host.get("interfaces") else ""
            groups = ",".join(g["name"] for g in host.get("groups", []))
            templates = ",".join(t["host"] for t in host.get("parentTemplates", []))
            writer.writerow([
                host["host"],
                ip,
                groups,
                templates,
                host.get("description", "")
            ])

    print(f"Exported {len(hosts)} hosts to {csv_file}")

def main():
    parser = argparse.ArgumentParser(description="Bulk host management for Zabbix")
    parser.add_argument("action", choices=["create", "update", "delete", "export"])
    parser.add_argument("csv_file", help="CSV file path")
    parser.add_argument("--group", help="Filter by group name (for export)")
    args = parser.parse_args()

    api = get_api()

    if args.action == "create":
        create_hosts(api, args.csv_file)
    elif args.action == "update":
        update_hosts(api, args.csv_file)
    elif args.action == "delete":
        delete_hosts(api, args.csv_file)
    elif args.action == "export":
        export_hosts(api, args.csv_file, args.group)

if __name__ == "__main__":
    main()
