"""op-env-show — Display environment item details from 1Password (Python SDK version).

Usage:
    op-env-show <name> <vault> [--reveal] [--json] [--keys]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys

from .utils import (
    colors,
    extract_variables,
    find_item_by_title,
    get_client,
    log,
    resolve_vault_id,
)

HELP_EPILOG = """\
examples:
  # Show with masked values
  uv run op-env-show my-app-dev Development

  # Show with revealed values
  uv run op-env-show my-app-prod Production --reveal

  # JSON output
  uv run op-env-show my-app-dev Development --json

  # List only variable names
  uv run op-env-show azure-config Shared --keys
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="op-env-show",
        description="Display environment item details from 1Password",
        epilog=HELP_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("name", help="Name/title of the environment item")
    parser.add_argument("vault", help="Vault containing the item")
    parser.add_argument(
        "--reveal", "-r", action="store_true", help="Show concealed values (default: masked)"
    )
    parser.add_argument("--json", dest="json_output", action="store_true", help="JSON output")
    parser.add_argument("--keys", action="store_true", help="Show only variable names")
    return parser


async def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    client = await get_client()
    vault_id = await resolve_vault_id(client, args.vault)

    # Find the item
    item = await find_item_by_title(client, vault_id, args.name)
    if item is None:
        log.error(f"Item '{args.name}' not found in vault '{args.vault}'")
        sys.exit(1)

    # JSON output mode — serialize the raw item
    if args.json_output:
        # Build a serializable representation
        variables = extract_variables(item)
        if args.reveal:
            # Resolve actual values via secret references
            revealed = {}
            for key in variables:
                ref = f"op://{args.vault}/{args.name}/variables/{key}"
                try:
                    revealed[key] = await client.secrets.resolve(ref)
                except Exception:
                    revealed[key] = variables[key]
            variables = revealed

        output = {
            "title": getattr(item, "title", args.name),
            "vault": args.vault,
            "category": str(getattr(item, "category", "Unknown")),
            "tags": getattr(item, "tags", []),
            "variables": variables,
        }
        print(json.dumps(output, indent=2))
        return

    # Extract metadata
    title = getattr(item, "title", args.name)
    category = str(getattr(item, "category", "Unknown"))
    tags = ", ".join(getattr(item, "tags", [])) or "none"
    created = str(getattr(item, "created_at", "N/A"))
    updated = str(getattr(item, "updated_at", "N/A"))

    c = colors

    # Display header
    print()
    print(c.cyan("+" + "=" * 63 + "+"))
    print(f"{c.cyan('|')} Environment: {c.green(title)}")
    print(c.cyan("+" + "=" * 63 + "+"))
    print(f"{c.cyan('|')} Vault: {args.vault}")
    print(f"{c.cyan('|')} Category: {category}")
    print(f"{c.cyan('|')} Tags: {tags}")
    print(f"{c.cyan('|')} Created: {created}")
    print(f"{c.cyan('|')} Updated: {updated}")
    print(c.cyan("+" + "=" * 63 + "+"))
    print(f"{c.cyan('|')} Variables:")
    print(c.cyan("+" + "=" * 63 + "+"))
    print()

    # Extract and display variables
    variables = extract_variables(item)

    if not variables:
        print("  (no variables found)")
    else:
        for key, value in variables.items():
            if args.keys:
                print(f"  {key}")
            elif args.reveal:
                # Resolve actual secret value
                ref = f"op://{args.vault}/{args.name}/variables/{key}"
                try:
                    revealed = await client.secrets.resolve(ref)
                except Exception:
                    revealed = value
                print(f"  {key}={revealed}")
            else:
                masked = "********" if value else "(empty)"
                print(f"  {key}={masked}")

    print()
    if not args.reveal and not args.keys:
        print("Tip: Use --reveal to show actual values")


def main_sync() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    main_sync()
