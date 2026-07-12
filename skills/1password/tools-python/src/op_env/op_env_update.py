"""op-env-update — Update environment item in 1Password (Python SDK version).

Usage:
    op-env-update <name> <vault> [--from-file <.env>] [--remove <keys>] [KEY=VALUE ...]
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys

from .utils import (
    find_item_by_title,
    get_client,
    log,
    parse_env_file,
    parse_inline_vars,
    resolve_vault_id,
)

HELP_EPILOG = """\
examples:
  # Update single variable
  uv run op-env-update my-app-dev Development API_KEY=new-key

  # Merge from .env file
  uv run op-env-update my-app-prod Production --from-file .env.prod

  # Remove specific variables
  uv run op-env-update azure-config Shared --remove OLD_KEY,DEPRECATED_VAR

  # Update and remove in one command
  uv run op-env-update my-app Development NEW_KEY=value --remove OLD_KEY
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="op-env-update",
        description="Update environment item in 1Password",
        epilog=HELP_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("positionals", nargs="*", help="<name> <vault> [KEY=VALUE ...]")
    parser.add_argument("--from-file", dest="from_file", help="Import/merge variables from .env")
    parser.add_argument("--remove", help="Comma-separated list of keys to remove")
    return parser


async def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    # Separate name, vault, and KEY=VALUE from positionals
    name = ""
    vault = ""
    env_args: list[str] = []

    for arg in args.positionals:
        if "=" in arg:
            env_args.append(arg)
        elif not name:
            name = arg
        elif not vault:
            vault = arg

    if not name or not vault:
        log.error("Missing required arguments: name and vault")
        parser.print_help()
        sys.exit(1)

    client = await get_client()
    vault_id = await resolve_vault_id(client, vault)

    # Find existing item
    item = await find_item_by_title(client, vault_id, name)
    if item is None:
        log.error(f"Item '{name}' not found in vault '{vault}'")
        log.info("Use op-env-create to create a new environment")
        sys.exit(1)

    log.info(f"Updating environment: {name} in vault: {vault}")

    # Handle removals
    if args.remove:
        keys_to_remove = [k.strip() for k in args.remove.split(",")]
        # Remove fields from the item
        current_fields = list(getattr(item, "fields", []))
        for key in keys_to_remove:
            log.info(f"Removing variable: {key}")
            current_fields = [
                f for f in current_fields
                if not (
                    (getattr(f, "title", "") == key or getattr(f, "label", "") == key)
                    and (
                        getattr(f, "section_id", "") == "variables"
                        or getattr(getattr(f, "section", None), "id", "") == "variables"
                        or str(getattr(f, "field_type", "")) == "Concealed"
                    )
                )
            ]
        item.fields = current_fields

    # Collect variables to add/update
    variables: dict[str, str] = {}

    if args.from_file:
        if not os.path.isfile(args.from_file):
            log.error(f"File not found: {args.from_file}")
            sys.exit(1)
        log.info(f"Loading variables from: {args.from_file}")
        with open(args.from_file) as f:
            variables.update(parse_env_file(f.read()))

    # Add inline variables
    variables.update(parse_inline_vars(env_args))

    # Apply variable updates to item fields
    if variables:
        log.info(f"Updating variables: {' '.join(variables.keys())}")
        current_fields = list(getattr(item, "fields", []))

        for key, value in variables.items():
            # Check if field already exists and update it
            found = False
            for field in current_fields:
                field_title = getattr(field, "title", "") or getattr(field, "label", "")
                sec_id = getattr(field, "section_id", "") or getattr(
                    getattr(field, "section", None), "id", ""
                )
                if field_title == key and sec_id == "variables":
                    field.value = value
                    found = True
                    break

            if not found:
                from onepassword.types import ItemField, ItemFieldType

                current_fields.append(
                    ItemField(
                        id=key,
                        title=key,
                        value=value,
                        field_type=ItemFieldType.CONCEALED,
                        section_id="variables",
                    )
                )

        item.fields = current_fields

    # Save the updated item
    if variables or args.remove:
        try:
            await client.items.put(vault_id, item)
            log.info(f"Environment '{name}' updated successfully")
        except Exception as exc:
            log.error(f"Failed to update environment: {exc}")
            sys.exit(1)
    else:
        log.warn("No variables to update")

    print("\nCurrent state:")
    print(f"  uv run op-env-show '{name}' '{vault}'")


def main_sync() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    main_sync()
