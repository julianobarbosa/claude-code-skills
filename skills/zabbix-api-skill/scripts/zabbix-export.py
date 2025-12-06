#!/usr/bin/env python3
"""
Export and import Zabbix configuration.

Usage:
    python zabbix-export.py templates --output templates.json [--name "Template Name"]
    python zabbix-export.py hosts --output hosts.json [--group "Group Name"]
    python zabbix-export.py all --output config.json
    python zabbix-export.py import config.json

Environment variables:
    ZABBIX_URL - Zabbix frontend URL
    ZABBIX_TOKEN - API token
"""

import os
import sys
import json
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

def export_templates(api, output_file, template_name=None):
    """Export templates to JSON."""
    params = {
        "output": "extend",
        "selectItems": "extend",
        "selectTriggers": "extend",
        "selectGraphs": "extend",
        "selectDiscoveryRules": "extend",
        "selectMacros": "extend",
        "selectTags": "extend"
    }

    if template_name:
        params["filter"] = {"host": template_name}

    templates = api.template.get(**params)

    with open(output_file, "w") as f:
        json.dump({"templates": templates}, f, indent=2)

    print(f"Exported {len(templates)} templates to {output_file}")

def export_hosts(api, output_file, group_name=None):
    """Export hosts to JSON."""
    params = {
        "output": "extend",
        "selectInterfaces": "extend",
        "selectGroups": ["groupid", "name"],
        "selectParentTemplates": ["templateid", "host"],
        "selectMacros": "extend",
        "selectTags": "extend",
        "selectInventory": "extend"
    }

    if group_name:
        groups = api.hostgroup.get(filter={"name": group_name}, output=["groupid"])
        if groups:
            params["groupids"] = [groups[0]["groupid"]]
        else:
            print(f"Warning: Group '{group_name}' not found")

    hosts = api.host.get(**params)

    with open(output_file, "w") as f:
        json.dump({"hosts": hosts}, f, indent=2)

    print(f"Exported {len(hosts)} hosts to {output_file}")

def export_all(api, output_file):
    """Export all configuration."""
    config = {
        "version": api.api_version(),
        "host_groups": api.hostgroup.get(output="extend"),
        "templates": api.template.get(
            output="extend",
            selectItems=["itemid", "name", "key_"],
            selectTriggers=["triggerid", "description"],
            selectMacros="extend"
        ),
        "hosts": api.host.get(
            output="extend",
            selectInterfaces="extend",
            selectGroups=["groupid", "name"],
            selectParentTemplates=["templateid", "host"],
            selectMacros="extend"
        ),
        "actions": api.action.get(
            output="extend",
            selectOperations="extend",
            selectFilter="extend"
        ),
        "media_types": api.mediatype.get(output="extend"),
        "users": api.user.get(output=["userid", "username", "name", "surname"])
    }

    with open(output_file, "w") as f:
        json.dump(config, f, indent=2)

    print(f"Exported configuration to {output_file}")
    print(f"  Host groups: {len(config['host_groups'])}")
    print(f"  Templates: {len(config['templates'])}")
    print(f"  Hosts: {len(config['hosts'])}")
    print(f"  Actions: {len(config['actions'])}")

def import_config(api, input_file):
    """Import configuration from JSON (hosts only for safety)."""
    with open(input_file) as f:
        config = json.load(f)

    if "hosts" in config:
        for host_data in config["hosts"]:
            hostname = host_data.get("host")

            # Check if exists
            existing = api.host.get(filter={"host": hostname}, output=["hostid"])
            if existing:
                print(f"Skip: {hostname} already exists")
                continue

            try:
                # Prepare minimal host creation
                groups = [{"groupid": g["groupid"]} for g in host_data.get("groups", [])]
                if not groups:
                    # Use default group
                    groups = [{"groupid": "2"}]

                interfaces = host_data.get("interfaces", [])
                if interfaces:
                    # Clean interface data
                    interfaces = [{
                        "type": int(i.get("type", 1)),
                        "main": int(i.get("main", 1)),
                        "useip": int(i.get("useip", 1)),
                        "ip": i.get("ip", ""),
                        "dns": i.get("dns", ""),
                        "port": i.get("port", "10050")
                    } for i in interfaces]

                params = {
                    "host": hostname,
                    "groups": groups,
                    "interfaces": interfaces
                }

                templates = host_data.get("parentTemplates", [])
                if templates:
                    params["templates"] = [{"templateid": t["templateid"]} for t in templates]

                api.host.create(**params)
                print(f"Imported: {hostname}")

            except Exception as e:
                print(f"Error importing {hostname}: {e}")

    print("Import complete")

def main():
    parser = argparse.ArgumentParser(description="Export/import Zabbix configuration")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Templates export
    tpl_parser = subparsers.add_parser("templates", help="Export templates")
    tpl_parser.add_argument("--output", "-o", required=True, help="Output file")
    tpl_parser.add_argument("--name", help="Template name filter")

    # Hosts export
    host_parser = subparsers.add_parser("hosts", help="Export hosts")
    host_parser.add_argument("--output", "-o", required=True, help="Output file")
    host_parser.add_argument("--group", help="Group name filter")

    # All export
    all_parser = subparsers.add_parser("all", help="Export all configuration")
    all_parser.add_argument("--output", "-o", required=True, help="Output file")

    # Import
    import_parser = subparsers.add_parser("import", help="Import configuration")
    import_parser.add_argument("file", help="Input file")

    args = parser.parse_args()
    api = get_api()

    if args.command == "templates":
        export_templates(api, args.output, args.name)
    elif args.command == "hosts":
        export_hosts(api, args.output, args.group)
    elif args.command == "all":
        export_all(api, args.output)
    elif args.command == "import":
        import_config(api, args.file)

if __name__ == "__main__":
    main()
