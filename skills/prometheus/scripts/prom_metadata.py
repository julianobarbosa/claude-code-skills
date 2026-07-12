#!/usr/bin/env python3
"""
Prometheus Metadata Tool

Query metadata from Prometheus: series, labels, label values, and metric info.

Usage:
    python prom_metadata.py <prometheus_url> <command> [options]

Commands:
    series      Find series matching label selectors
    labels      List all label names
    values      Get values for a specific label
    metadata    Get metric metadata
    targets     List scrape targets

Examples:
    python prom_metadata.py http://localhost:9090 series 'up' 'process_start_time_seconds{job="prometheus"}'
    python prom_metadata.py http://localhost:9090 labels
    python prom_metadata.py http://localhost:9090 values job
    python prom_metadata.py http://localhost:9090 metadata --metric http_requests_total
    python prom_metadata.py http://localhost:9090 targets --state active
"""

import argparse
import json
import sys
import urllib.parse
import urllib.request
from typing import Any


def fetch_api(base_url: str, endpoint: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Fetch from Prometheus API."""
    url = f"{base_url.rstrip('/')}{endpoint}"
    if params:
        # Handle repeated parameters (like match[])
        param_parts = []
        for key, value in params.items():
            if isinstance(value, list):
                for v in value:
                    param_parts.append(f"{urllib.parse.quote(key)}={urllib.parse.quote(str(v))}")
            elif value is not None:
                param_parts.append(f"{urllib.parse.quote(key)}={urllib.parse.quote(str(value))}")
        if param_parts:
            url += "?" + "&".join(param_parts)

    try:
        with urllib.request.urlopen(url, timeout=30) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return {"status": "error", "error": body, "errorType": str(e.code)}
    except urllib.error.URLError as e:
        return {"status": "error", "error": str(e.reason), "errorType": "connection_error"}


def cmd_series(base_url: str, matchers: list[str], start: str | None, end: str | None, limit: int | None) -> int:
    """Find series by label matchers."""
    params = {"match[]": matchers}
    if start:
        params["start"] = start
    if end:
        params["end"] = end
    if limit:
        params["limit"] = limit

    result = fetch_api(base_url, "/api/v1/series", params)

    if result.get("status") != "success":
        print(f"Error: {result.get('error', 'Unknown error')}", file=sys.stderr)
        return 1

    series = result.get("data", [])
    print(f"Found {len(series)} series:\n")

    for s in series:
        name = s.get("__name__", "")
        labels = {k: v for k, v in s.items() if k != "__name__"}
        label_str = ", ".join(f'{k}="{v}"' for k, v in sorted(labels.items()))
        if name:
            print(f"{name}{{{label_str}}}" if labels else name)
        else:
            print(f"{{{label_str}}}")

    return 0


def cmd_labels(base_url: str, matchers: list[str] | None, start: str | None, end: str | None, limit: int | None) -> int:
    """List all label names."""
    params = {}
    if matchers:
        params["match[]"] = matchers
    if start:
        params["start"] = start
    if end:
        params["end"] = end
    if limit:
        params["limit"] = limit

    result = fetch_api(base_url, "/api/v1/labels", params if params else None)

    if result.get("status") != "success":
        print(f"Error: {result.get('error', 'Unknown error')}", file=sys.stderr)
        return 1

    labels = result.get("data", [])
    print(f"Found {len(labels)} labels:\n")
    for label in sorted(labels):
        print(f"  {label}")

    return 0


def cmd_values(base_url: str, label_name: str, matchers: list[str] | None, start: str | None, end: str | None, limit: int | None) -> int:
    """Get values for a label."""
    params = {}
    if matchers:
        params["match[]"] = matchers
    if start:
        params["start"] = start
    if end:
        params["end"] = end
    if limit:
        params["limit"] = limit

    result = fetch_api(base_url, f"/api/v1/label/{urllib.parse.quote(label_name)}/values", params if params else None)

    if result.get("status") != "success":
        print(f"Error: {result.get('error', 'Unknown error')}", file=sys.stderr)
        return 1

    values = result.get("data", [])
    print(f"Found {len(values)} values for label '{label_name}':\n")
    for value in sorted(values):
        print(f"  {value}")

    return 0


def cmd_metadata(base_url: str, metric: str | None, limit: int | None, limit_per_metric: int | None) -> int:
    """Get metric metadata."""
    params = {}
    if metric:
        params["metric"] = metric
    if limit:
        params["limit"] = limit
    if limit_per_metric:
        params["limit_per_metric"] = limit_per_metric

    result = fetch_api(base_url, "/api/v1/metadata", params if params else None)

    if result.get("status") != "success":
        print(f"Error: {result.get('error', 'Unknown error')}", file=sys.stderr)
        return 1

    metadata = result.get("data", {})
    print(f"Found metadata for {len(metadata)} metrics:\n")

    for metric_name, info_list in sorted(metadata.items()):
        print(f"{metric_name}:")
        for info in info_list:
            print(f"  Type: {info.get('type', 'unknown')}")
            print(f"  Help: {info.get('help', 'N/A')}")
            if info.get("unit"):
                print(f"  Unit: {info.get('unit')}")
        print()

    return 0


def cmd_targets(base_url: str, state: str | None, scrape_pool: str | None) -> int:
    """List scrape targets."""
    params = {}
    if state:
        params["state"] = state
    if scrape_pool:
        params["scrapePool"] = scrape_pool

    result = fetch_api(base_url, "/api/v1/targets", params if params else None)

    if result.get("status") != "success":
        print(f"Error: {result.get('error', 'Unknown error')}", file=sys.stderr)
        return 1

    data = result.get("data", {})
    active = data.get("activeTargets", [])
    dropped = data.get("droppedTargets", [])

    if active:
        print(f"Active targets ({len(active)}):\n")
        for target in active:
            labels = target.get("labels", {})
            job = labels.get("job", "unknown")
            instance = labels.get("instance", "unknown")
            health = target.get("health", "unknown")
            health_icon = "✓" if health == "up" else "✗" if health == "down" else "?"

            print(f"  [{health_icon}] {job}/{instance}")
            print(f"      URL: {target.get('scrapeUrl', 'N/A')}")
            print(f"      Pool: {target.get('scrapePool', 'N/A')}")
            print(f"      Last scrape: {target.get('lastScrape', 'N/A')}")
            if target.get("lastError"):
                print(f"      Error: {target.get('lastError')}")
            print()

    if dropped and (state is None or state in ("dropped", "any")):
        print(f"\nDropped targets ({len(dropped)}):\n")
        for target in dropped[:20]:  # Limit output
            discovered = target.get("discoveredLabels", {})
            job = discovered.get("job", "unknown")
            address = discovered.get("__address__", "unknown")
            print(f"  - {job}: {address}")
        if len(dropped) > 20:
            print(f"  ... and {len(dropped) - 20} more")

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Query Prometheus metadata",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("url", help="Prometheus server URL")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # Series command
    series_parser = subparsers.add_parser("series", help="Find series by label matchers")
    series_parser.add_argument("matchers", nargs="+", help="Series selectors (e.g., 'up', 'http_requests_total{job=\"api\"}')")
    series_parser.add_argument("--start", help="Start timestamp")
    series_parser.add_argument("--end", help="End timestamp")
    series_parser.add_argument("--limit", type=int, help="Max series to return")

    # Labels command
    labels_parser = subparsers.add_parser("labels", help="List all label names")
    labels_parser.add_argument("--match", action="append", dest="matchers", help="Filter by series selector")
    labels_parser.add_argument("--start", help="Start timestamp")
    labels_parser.add_argument("--end", help="End timestamp")
    labels_parser.add_argument("--limit", type=int, help="Max labels to return")

    # Values command
    values_parser = subparsers.add_parser("values", help="Get values for a label")
    values_parser.add_argument("label_name", help="Label name")
    values_parser.add_argument("--match", action="append", dest="matchers", help="Filter by series selector")
    values_parser.add_argument("--start", help="Start timestamp")
    values_parser.add_argument("--end", help="End timestamp")
    values_parser.add_argument("--limit", type=int, help="Max values to return")

    # Metadata command
    metadata_parser = subparsers.add_parser("metadata", help="Get metric metadata")
    metadata_parser.add_argument("--metric", "-m", help="Filter by metric name")
    metadata_parser.add_argument("--limit", type=int, help="Max metrics to return")
    metadata_parser.add_argument("--limit-per-metric", type=int, help="Max metadata per metric")

    # Targets command
    targets_parser = subparsers.add_parser("targets", help="List scrape targets")
    targets_parser.add_argument("--state", choices=["active", "dropped", "any"], help="Filter by state")
    targets_parser.add_argument("--scrape-pool", help="Filter by scrape pool name")

    args = parser.parse_args()

    if args.command == "series":
        return cmd_series(args.url, args.matchers, args.start, args.end, args.limit)
    elif args.command == "labels":
        return cmd_labels(args.url, args.matchers, args.start, args.end, args.limit)
    elif args.command == "values":
        return cmd_values(args.url, args.label_name, args.matchers, args.start, args.end, args.limit)
    elif args.command == "metadata":
        return cmd_metadata(args.url, args.metric, args.limit, getattr(args, "limit_per_metric", None))
    elif args.command == "targets":
        return cmd_targets(args.url, args.state, getattr(args, "scrape_pool", None))


if __name__ == "__main__":
    sys.exit(main())
