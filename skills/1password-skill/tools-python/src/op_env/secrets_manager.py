"""SecretsManager — high-level abstraction for 1Password secret resolution.

Provides a reusable class for Python applications (FastAPI, Django, scripts)
that need to resolve secrets from 1Password at runtime.

Usage::

    from op_env.secrets_manager import SecretsManager

    async def main():
        sm = await SecretsManager.create()

        # Single secret
        api_key = await sm.get("op://Production/API/key")

        # Batch resolve
        secrets = await sm.get_many([
            "op://Production/DB/password",
            "op://Production/DB/host",
        ])

        # Load all vars from a 1Password environment item
        env = await sm.resolve_environment("my-app-prod", "Production")
"""

from __future__ import annotations

from onepassword import Client

from .utils import extract_variables, find_item_by_title, resolve_vault_id


class SecretsManager:
    """High-level 1Password secrets manager with caching.

    Use the async :meth:`create` factory to instantiate.
    """

    def __init__(self, client: Client) -> None:
        self._client = client
        self._cache: dict[str, str] = {}

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    async def create(
        cls,
        token: str | None = None,
        integration_name: str = "op-env-tools",
        integration_version: str = "0.1.0",
    ) -> SecretsManager:
        """Create an authenticated SecretsManager.

        Parameters
        ----------
        token:
            ``OP_SERVICE_ACCOUNT_TOKEN``.  Falls back to environment variable
            if not provided.
        integration_name:
            Name reported to 1Password for audit logs.
        integration_version:
            Version reported to 1Password for audit logs.
        """
        import os

        auth = token or os.environ.get("OP_SERVICE_ACCOUNT_TOKEN", "")
        if not auth:
            raise ValueError(
                "OP_SERVICE_ACCOUNT_TOKEN must be set or passed as 'token'"
            )

        client = await Client.authenticate(
            auth=auth,
            integration_name=integration_name,
            integration_version=integration_version,
        )
        return cls(client)

    # ------------------------------------------------------------------
    # Secret resolution
    # ------------------------------------------------------------------

    async def get(self, reference: str, *, use_cache: bool = True) -> str:
        """Resolve a single ``op://`` secret reference.

        Parameters
        ----------
        reference:
            A 1Password secret reference, e.g. ``op://Vault/Item/Field``.
        use_cache:
            Return cached value if previously resolved.
        """
        if use_cache and reference in self._cache:
            return self._cache[reference]

        value = await self._client.secrets.resolve(reference)
        self._cache[reference] = value
        return value

    async def get_many(self, references: list[str]) -> dict[str, str]:
        """Batch-resolve multiple ``op://`` secret references.

        Returns a dict mapping each reference to its resolved value.
        """
        # Use the SDK's batch resolve for efficiency
        resolved = await self._client.secrets.resolve_all(references)
        # resolved is a list of strings in the same order as references
        result: dict[str, str] = {}
        for ref, val in zip(references, resolved):
            self._cache[ref] = val
            result[ref] = val
        return result

    # ------------------------------------------------------------------
    # Environment resolution
    # ------------------------------------------------------------------

    async def resolve_environment(
        self, name: str, vault: str
    ) -> dict[str, str]:
        """Load all variables from a 1Password environment item.

        Parameters
        ----------
        name:
            Title of the environment item.
        vault:
            Vault name containing the item.

        Returns
        -------
        dict:
            A mapping of variable names to their resolved (plaintext) values.
        """
        vault_id = await resolve_vault_id(self._client, vault)
        item = await find_item_by_title(self._client, vault_id, name)
        if item is None:
            raise ValueError(f"Environment '{name}' not found in vault '{vault}'")

        variables = extract_variables(item)

        # Resolve each variable through op:// references for plaintext values
        refs = [
            f"op://{vault}/{name}/variables/{key}" for key in variables
        ]
        if not refs:
            return {}

        resolved = await self._client.secrets.resolve_all(refs)
        result: dict[str, str] = {}
        for key, val in zip(variables.keys(), resolved):
            result[key] = val
        return result

    # ------------------------------------------------------------------
    # Vault listing
    # ------------------------------------------------------------------

    async def list_vaults(self) -> list[dict[str, str]]:
        """List all accessible vaults."""
        result: list[dict[str, str]] = []
        vaults = await self._client.vaults.list_all()
        async for vault in vaults:
            result.append({"id": vault.id, "title": vault.title})
        return result

    # ------------------------------------------------------------------
    # Cache management
    # ------------------------------------------------------------------

    def clear_cache(self) -> None:
        """Invalidate all cached secret values."""
        self._cache.clear()
