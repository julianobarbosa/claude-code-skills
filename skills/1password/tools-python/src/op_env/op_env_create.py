"""op-env-create — Create environment item in 1Password (Python SDK version).

Usage:
    op-env-create <name> <vault> [--from-file <.env>] [--tags <tags>] [KEY=VALUE ...]
"""

from __future__ import annotations

import argparse
import asyncio
import os
import sys

from onepassword.types import (
    ItemCategory,
    ItemCreateParams,
    ItemField,
    ItemFieldType,
    ItemSection,
)

from .utils import (
    get_client,
    item_exists,
    log,
    parse_env_file,
    parse_inline_vars,
    resolve_vault_id,
)

HELP_EPILOG = """\
examples:
  # Create with inline variables
  uv run op-env-create my-app-dev Development API_KEY=xxx DB_HOST=localhost

  # Create from .env file
  uv run op-env-create my-app-prod Production --from-file .env.prod

  # Combine file and inline (inline overrides file)
  uv run op-env-create azure-config Shared --from-file .env EXTRA_KEY=value

  # With custom tags
  uv run op-env-create secrets DevOps --tags "env,production,api" KEY=value
"""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="op-env-create",
        description="Create environment item in 1Password",
        epilog=HELP_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("positionals", nargs="*", help="<name> <vault> [KEY=VALUE ...]")
    parser.add_argument("--from-file", dest="from_file", help="Import variables from .env file")
    parser.add_argument(
        "--tags", default="environment", help="Comma-separated tags (default: environment)"
    )
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

    # Check if item already exists
    if await item_exists(client, vault_id, name):
        log.error(f"Item '{name}' already exists in vault '{vault}'")
        log.info("Use op-env-update to modify existing environment")
        sys.exit(1)

    # Collect variables
    variables: dict[str, str] = {}

    # Load from file if specified
    if args.from_file:
        if not os.path.isfile(args.from_file):
            log.error(f"File not found: {args.from_file}")
            sys.exit(1)
        log.info(f"Loading variables from: {args.from_file}")
        with open(args.from_file) as f:
            variables.update(parse_env_file(f.read()))

    # Add/override with inline variables
    variables.update(parse_inline_vars(env_args))

    if not variables:
        log.error("No environment variables provided")
        log.info("Use --from-file <.env> or provide KEY=value pairs")
        sys.exit(1)

    log.info(f"Creating environment: {name} in vault: {vault}")
    log.info(f"Variables ({len(variables)}): {' '.join(variables.keys())}")

    # Build the item using the SDK
    # Create fields in a "variables" section with CONCEALED type
    section = ItemSection(id="variables", title="variables")
    fields = []
    for key, value in variables.items():
        fields.append(
            ItemField(
                id=key,
                title=key,
                value=value,
                field_type=ItemFieldType.CONCEALED,
                section_id="variables",
            )
        )

    params = ItemCreateParams(
        title=name,
        category=ItemCategory.APICREDENTIALS,
        vault_id=vault_id,
        tags=args.tags.split(","),
        sections=[section],
        fields=fields,
    )

    try:
        await client.items.create(params)
        log.info(f"Environment '{name}' created successfully")
        print("\nVariables stored:")
        for key in variables:
            print(f"  - {key}")
        print("\nUsage:")
        print("  # Export to .env file")
        print(f"  uv run op-env-export '{name}' '{vault}' > .env")
        print()
        first_key = next(iter(variables))
        print("  # Read single variable")
        print(f"  op read 'op://{vault}/{name}/variables/{first_key}'")
    except Exception as exc:
        log.error(f"Failed to create environment: {exc}")
        sys.exit(1)


def main_sync() -> None:
    asyncio.run(main())


if __name__ == "__main__":
    main_sync()
