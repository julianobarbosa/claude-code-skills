"""op-env-export — Export environment to .env file format (Python SDK version).

Usage:
    op-env-export <name> <vault> [--format <fmt>] [--prefix <str>] > .env
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime, timezone

from .utils import (
    extract_variables,
    find_item_by_title,
    get_client,
    log,
    resolve_vault_id,
)

HELP_EPILOG = """\
examples:
  # Export to .env file
  uv run op-env-export my-app-dev Development > .env

  # Docker-compatible format
  uv run op-env-export my-app Development --format docker > .env

  # Create template with op:// references
  uv run op-env-export my-app-prod Production --format op-refs > .env.tpl

  # JSON format
  uv run op-env-export config Shared --format json

  # Add prefix to all variables
  uv run op-env-export azure Shared --prefix AZURE_ > .env
"""

VALID_FORMATS = ("env", "docker", "op-refs", "json")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="op-env-export",
        description="Export environment to .env file format",
        epilog=HELP_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("name", help="Name/title of the environment item")
    parser.add_argument("vault", help="Vault containing the item")
    parser.add_argument(
        "--format",
        dest="fmt",
        default="env",
        choices=VALID_FORMATS,
        help="Output format (default: env)",
    )
    parser.add_argument("--prefix", default="", help="Add prefix to all variable names")
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

    log.info(f"Exporting: {args.name} from {args.vault} (format: {args.fmt})")

    # Extract variable names
    variables = extract_variables(item)
    if not variables:
        log.error("No variables found in environment")
        sys.exit(1)

    # Resolve actual values using batch resolution
    refs = [f"op://{args.vault}/{args.name}/variables/{key}" for key in variables]
    try:
        resolved_values = await client.secrets.resolve_all(refs)
    except Exception:
        # Fallback: resolve individually
        resolved_values = []
        for ref in refs:
            try:
                resolved_values.append(await client.secrets.resolve(ref))
            except Exception:
                resolved_values.append(variables[list(variables.keys())[len(resolved_values)]])

    revealed: dict[str, str] = dict(zip(variables.keys(), resolved_values))

    # Output header
    timestamp = datetime.now(timezone.utc).isoformat()
    prefix = args.prefix

    if args.fmt in ("env", "docker"):
        print(f"# Generated from 1Password: {args.name} ({args.vault})")
        print(f"# Date: {timestamp}")
        print()
    elif args.fmt == "op-refs":
        print(f"# 1Password Template: {args.name} ({args.vault})")
        print("# Use with: op inject -i .env.tpl -o .env")
        print("# Or: op run --env-file .env.tpl -- command")
        print()

    # Output variables
    if args.fmt == "env":
        for key, value in revealed.items():
            escaped = value.replace("\\", "\\\\").replace('"', '\\"')
            print(f"{prefix}{key}={escaped}")
    elif args.fmt == "docker":
        for key, value in revealed.items():
            escaped = value.replace("\\", "\\\\").replace('"', '\\"')
            print(f'{prefix}{key}="{escaped}"')
    elif args.fmt == "op-refs":
        for key in revealed:
            print(f"{prefix}{key}=op://{args.vault}/{args.name}/variables/{key}")
    elif args.fmt == "json":
        obj = {f"{prefix}{key}": value for key, value in revealed.items()}
        print(json.dumps(obj, indent=2))

    log.info("Export complete")


def main_sync() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    main_sync()
