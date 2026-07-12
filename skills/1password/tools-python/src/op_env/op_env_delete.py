"""op-env-delete — Delete environment item from 1Password (Python SDK version).

Usage:
    op-env-delete <name> <vault> [--force] [--archive]
"""

from __future__ import annotations

import argparse
import asyncio
import sys

from .utils import (
    find_item_by_title,
    get_client,
    log,
    resolve_vault_id,
)

HELP_EPILOG = """\
examples:
  # Interactive deletion
  uv run op-env-delete my-app-dev Development

  # Force delete without confirmation
  uv run op-env-delete old-config Shared --force

  # Archive instead of delete
  uv run op-env-delete deprecated-env Production --archive
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="op-env-delete",
        description="Delete environment item from 1Password",
        epilog=HELP_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("name", help="Name/title of the environment item")
    parser.add_argument("vault", help="Vault containing the item")
    parser.add_argument(
        "--force", "-f", action="store_true", help="Skip confirmation prompt"
    )
    parser.add_argument(
        "--archive", action="store_true", help="Archive instead of permanent delete"
    )
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

    item_id = item.id

    log.info("Environment to delete:")
    print(f"  Name: {args.name}")
    print(f"  Vault: {args.vault}")
    print()

    # Confirm unless force
    if not args.force:
        action = "Archive" if args.archive else "Permanently DELETE"
        try:
            response = input(f"{action} this environment? [y/N] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            log.info("Cancelled")
            sys.exit(0)

        if response not in ("y", "yes"):
            log.info("Cancelled")
            sys.exit(0)

    # Delete or archive
    try:
        if args.archive:
            await client.items.archive(vault_id, item_id)
            log.info(f"Environment '{args.name}' archived successfully")
        else:
            await client.items.delete(vault_id, item_id)
            log.info(f"Environment '{args.name}' deleted permanently")
    except Exception as exc:
        log.error(f"Failed to delete environment: {exc}")
        sys.exit(1)


def main_sync() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    main_sync()
