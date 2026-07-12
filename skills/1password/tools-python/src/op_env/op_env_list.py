"""op-env-list — List environment items from 1Password (Python SDK version).

Usage:
    op-env-list [--vault <vault>] [--tags <tags>] [--json]
"""

from __future__ import annotations

import argparse
import asyncio
import json

from .utils import colors, get_client, list_environments

HELP_EPILOG = """\
examples:
  # List all environments
  uv run op-env-list

  # Filter by vault
  uv run op-env-list --vault Development

  # Filter by tags
  uv run op-env-list --tags environment,production

  # JSON output
  uv run op-env-list --json
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="op-env-list",
        description="List environment items from 1Password",
        epilog=HELP_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--vault", help="Filter by vault name")
    parser.add_argument(
        "--tags", default="environment", help="Filter by tags (default: environment)"
    )
    parser.add_argument("--json", dest="json_output", action="store_true", help="JSON output")
    return parser


async def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # list_environments uses the op CLI (hybrid approach — SDK lacks tag filtering)
    # We still call get_client() to validate the token is set, but the listing
    # itself goes through the CLI.
    _ = await get_client()

    items = await list_environments(vault=args.vault, tags=args.tags)

    # JSON output mode
    if args.json_output:
        print(json.dumps(items, indent=2))
        return

    if not items:
        print("No environments found")
        print()
        print("Tip: Create one with: uv run op-env-create <name> <vault> KEY=value")
        return

    c = colors

    print()
    print(c.cyan("+" + "=" * 79 + "+"))
    print(f"{c.cyan('|')}{'1Password Environments':^79}{c.cyan('|')}")
    print(c.cyan("+" + "=" * 79 + "+"))

    # Header
    name_h = "NAME".ljust(35)
    vault_h = "VAULT".ljust(20)
    updated_h = "UPDATED".ljust(15)
    print(f"{c.cyan('|')} {name_h} | {vault_h} | {updated_h} {c.cyan('|')}")
    print(c.cyan("+" + "=" * 79 + "+"))

    # Items
    for item in items:
        title = (item.get("title", "") or "")[:35].ljust(35)
        vault_name = (item.get("vault", {}).get("name", "") or "")[:20].ljust(20)
        updated = (item.get("updated_at", "N/A") or "N/A")[:10].ljust(15)
        print(f"{c.cyan('|')} {title} | {vault_name} | {updated} {c.cyan('|')}")

    print(c.cyan("+" + "=" * 79 + "+"))
    print()
    print(f"Total: {len(items)} environments")
    print()
    print("Commands:")
    print("  Show details: uv run op-env-show <name> <vault>")
    print("  Export .env:  uv run op-env-export <name> <vault> > .env")


def main_sync() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    main_sync()
