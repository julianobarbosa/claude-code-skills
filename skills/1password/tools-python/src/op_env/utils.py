"""Shared utilities for 1Password environment tools (Python SDK version).

Mirrors the functionality of tools/src/utils.ts but uses the onepassword-sdk
Python package instead of shelling out to the op CLI.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
from typing import Any

from onepassword import Client

# ---------------------------------------------------------------------------
# Colors & logging (mirrors TS colors / log objects)
# ---------------------------------------------------------------------------

class Colors:
    """ANSI terminal color helpers."""

    @staticmethod
    def red(s: str) -> str:
        return f"\033[31m{s}\033[0m"

    @staticmethod
    def green(s: str) -> str:
        return f"\033[32m{s}\033[0m"

    @staticmethod
    def yellow(s: str) -> str:
        return f"\033[33m{s}\033[0m"

    @staticmethod
    def cyan(s: str) -> str:
        return f"\033[36m{s}\033[0m"

    @staticmethod
    def bold(s: str) -> str:
        return f"\033[1m{s}\033[0m"


class Log:
    """Structured log output matching the TypeScript log helpers."""

    @staticmethod
    def info(msg: str) -> None:
        print(f"{Colors.green('[INFO]')} {msg}")

    @staticmethod
    def warn(msg: str) -> None:
        print(f"{Colors.yellow('[WARN]')} {msg}")

    @staticmethod
    def error(msg: str) -> None:
        import sys
        print(f"{Colors.red('[ERROR]')} {msg}", file=sys.stderr)


colors = Colors()
log = Log()


# ---------------------------------------------------------------------------
# SDK client
# ---------------------------------------------------------------------------

async def get_client() -> Client:
    """Create an authenticated 1Password SDK client.

    Requires ``OP_SERVICE_ACCOUNT_TOKEN`` environment variable.
    """
    token = os.environ.get("OP_SERVICE_ACCOUNT_TOKEN")
    if not token:
        log.error(
            "OP_SERVICE_ACCOUNT_TOKEN not set. "
            "Export a service account token: export OP_SERVICE_ACCOUNT_TOKEN='ops_...'"
        )
        raise SystemExit(1)

    client = await Client.authenticate(
        auth=token,
        integration_name="op-env-tools",
        integration_version="0.1.0",
    )
    return client


# ---------------------------------------------------------------------------
# Vault helpers
# ---------------------------------------------------------------------------

async def resolve_vault_id(client: Client, vault_name: str) -> str:
    """Resolve a vault name to its ID.

    The SDK requires vault IDs for most operations.  This iterates the
    accessible vaults and returns the first match by name (case-insensitive).
    """
    vaults = await client.vaults.list_all()
    async for vault in vaults:
        if vault.title.lower() == vault_name.lower():
            return vault.id
    log.error(f"Vault not found: {vault_name}")
    raise SystemExit(1)


async def list_vaults(client: Client) -> list[dict[str, str]]:
    """Return a list of accessible vaults as dicts with id and title."""
    result: list[dict[str, str]] = []
    vaults = await client.vaults.list_all()
    async for vault in vaults:
        result.append({"id": vault.id, "title": vault.title})
    return result


# ---------------------------------------------------------------------------
# Item helpers
# ---------------------------------------------------------------------------

async def find_item_by_title(
    client: Client, vault_id: str, title: str
) -> Any | None:
    """Find an item by title within a vault.

    The SDK has no get-by-title; we iterate the vault's items.
    Returns the full item object or ``None``.
    """
    items = await client.items.list_all(vault_id)
    async for item_overview in items:
        if item_overview.title == title:
            return await client.items.get(vault_id, item_overview.id)
    return None


async def item_exists(client: Client, vault_id: str, title: str) -> bool:
    """Check whether an item with the given title exists in the vault."""
    items = await client.items.list_all(vault_id)
    async for item_overview in items:
        if item_overview.title == title:
            return True
    return False


# ---------------------------------------------------------------------------
# Environment listing (hybrid: uses op CLI for tag filtering)
# ---------------------------------------------------------------------------

async def list_environments(
    vault: str | None = None,
    tags: str = "environment",
) -> list[dict[str, Any]]:
    """List environment items filtered by tag.

    The SDK does not support tag-based filtering, so we fall back to the ``op``
    CLI for this operation (same approach as the TypeScript tools).
    """
    args = ["op", "item", "list", "--tags", tags, "--format", "json"]
    if vault:
        args.extend(["--vault", vault])

    try:
        proc = await asyncio.create_subprocess_exec(
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        if proc.returncode == 0 and stdout:
            return json.loads(stdout.decode())  # type: ignore[no-any-return]
    except FileNotFoundError:
        log.error("op CLI not found — required for listing environments")
    return []


# ---------------------------------------------------------------------------
# Parsing helpers (mirrors TS parseEnvFile / parseInlineVars)
# ---------------------------------------------------------------------------

_ENV_VAR_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$")


def parse_env_file(content: str) -> dict[str, str]:
    """Parse ``.env`` file content into a dict of key-value pairs."""
    result: dict[str, str] = {}
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        m = _ENV_VAR_RE.match(stripped)
        if m:
            key, value = m.group(1), m.group(2)
            # Strip surrounding quotes
            if len(value) >= 2 and (
                (value[0] == '"' and value[-1] == '"')
                or (value[0] == "'" and value[-1] == "'")
            ):
                value = value[1:-1]
            result[key] = value
    return result


def parse_inline_vars(args: list[str]) -> dict[str, str]:
    """Parse ``KEY=VALUE`` arguments into a dict."""
    result: dict[str, str] = {}
    for arg in args:
        m = _ENV_VAR_RE.match(arg)
        if m:
            result[m.group(1)] = m.group(2)
    return result


# ---------------------------------------------------------------------------
# Item field extraction
# ---------------------------------------------------------------------------

def extract_variables(item: Any) -> dict[str, str]:
    """Extract environment variables from an item's fields.

    Matches the TypeScript ``extractVariables`` logic: looks for fields in the
    ``variables`` section or fields of type ``CONCEALED``.
    """
    result: dict[str, str] = {}
    fields = getattr(item, "fields", None) or []
    for field in fields:
        # Check section — SDK uses section_id (str) or nested section object
        section_id = getattr(field, "section_id", "") or ""
        if not section_id and hasattr(field, "section") and field.section:
            section_id = getattr(field.section, "label", "") or getattr(
                field.section, "id", ""
            )
        field_type = getattr(field, "field_type", "") or ""
        if section_id == "variables" or str(field_type) == "Concealed":
            label = getattr(field, "title", "") or getattr(field, "label", "")
            if label:
                result[label] = getattr(field, "value", "") or ""
    return result
