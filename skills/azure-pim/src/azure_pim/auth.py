"""MSAL-based authentication for Azure PIM.

Supports:
- Interactive browser authentication (delegated user)
- Device code flow
- Client credentials (app-only)
- Managed identity
- Azure CLI authentication
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any

import msal

from azure_pim.config import PIMConfig
from azure_pim.exceptions import AuthenticationError, MFARequiredError

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)


class TokenProvider(ABC):
    """Abstract base class for token providers."""

    @abstractmethod
    def get_token(self, scopes: list[str]) -> str:
        """Acquire access token for the given scopes."""


class MSALTokenProvider(TokenProvider):
    """MSAL-based token provider with caching."""

    def __init__(self, config: PIMConfig) -> None:
        self.config = config
        self._cache = msal.SerializableTokenCache()
        self._load_cache()
        self._app: msal.PublicClientApplication | msal.ConfidentialClientApplication | None = None

    def _load_cache(self) -> None:
        """Load token cache from disk."""
        cache_path = self.config.cache_path
        if cache_path.exists():
            try:
                self._cache.deserialize(cache_path.read_text())
            except (json.JSONDecodeError, OSError) as e:
                logger.warning("Failed to load token cache: %s", e)

    def _save_cache(self) -> None:
        """Persist token cache to disk."""
        cache_path = self.config.cache_path
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            cache_path.write_text(self._cache.serialize())
            cache_path.chmod(0o600)
        except OSError as e:
            logger.warning("Failed to save token cache: %s", e)

    def _get_app(self) -> msal.PublicClientApplication | msal.ConfidentialClientApplication:
        """Get or create MSAL application."""
        if self._app is not None:
            return self._app

        if self.config.client_secret:
            self._app = msal.ConfidentialClientApplication(
                client_id=self.config.client_id or "",
                client_credential=self.config.client_secret,
                authority=self.config.authority,
                token_cache=self._cache,
            )
        else:
            client_id = self.config.client_id or "04b07795-8ddb-461a-bbee-02f9e1bf7b46"
            self._app = msal.PublicClientApplication(
                client_id=client_id,
                authority=self.config.authority,
                token_cache=self._cache,
            )

        return self._app

    def get_token(self, scopes: list[str]) -> str:
        """Acquire token silently or interactively."""
        app = self._get_app()

        accounts = app.get_accounts()
        if accounts:
            result = app.acquire_token_silent(scopes, account=accounts[0])
            if result and "access_token" in result:
                return result["access_token"]

        if isinstance(app, msal.ConfidentialClientApplication):
            result = app.acquire_token_for_client(scopes=scopes)
        else:
            result = app.acquire_token_interactive(scopes=scopes)

        if not result or "access_token" not in result:
            error = result.get("error", "unknown") if result else "unknown"
            error_desc = result.get("error_description", "") if result else ""

            if "mfa" in error_desc.lower() or "multi" in error_desc.lower():
                raise MFARequiredError(f"MFA required: {error_desc}")
            raise AuthenticationError(f"Authentication failed: {error} - {error_desc}")

        self._save_cache()
        return result["access_token"]


class DeviceCodeTokenProvider(TokenProvider):
    """Device code flow for headless environments."""

    def __init__(self, config: PIMConfig, callback: Callable[[str], None] | None = None) -> None:
        self.config = config
        self.callback = callback or print
        self._cache = msal.SerializableTokenCache()

    def get_token(self, scopes: list[str]) -> str:
        """Acquire token using device code flow."""
        client_id = self.config.client_id or "04b07795-8ddb-461a-bbee-02f9e1bf7b46"
        app = msal.PublicClientApplication(
            client_id=client_id,
            authority=self.config.authority,
            token_cache=self._cache,
        )

        flow = app.initiate_device_flow(scopes=scopes)
        if "user_code" not in flow:
            msg = f"Failed to create device flow: {flow.get('error')}"
            raise AuthenticationError(msg)

        self.callback(flow["message"])

        result = app.acquire_token_by_device_flow(flow)
        if "access_token" not in result:
            raise AuthenticationError(f"Device flow failed: {result.get('error')}")

        return result["access_token"]


class AzureCliTokenProvider(TokenProvider):
    """Use Azure CLI for authentication (az login)."""

    def get_token(self, scopes: list[str]) -> str:
        """Get token from Azure CLI."""
        resource = scopes[0].rsplit("/", 1)[0] if scopes else "https://graph.microsoft.com"

        try:
            result = subprocess.run(
                ["az", "account", "get-access-token", "--resource", resource, "--query", "accessToken", "-o", "tsv"],
                capture_output=True,
                text=True,
                check=True,
                timeout=30,
            )
            token = result.stdout.strip()
            if not token:
                msg = "Azure CLI returned empty token"
                raise AuthenticationError(msg)
            return token
        except subprocess.CalledProcessError as e:
            raise AuthenticationError(f"Azure CLI authentication failed: {e.stderr}") from e
        except FileNotFoundError as e:
            raise AuthenticationError("Azure CLI not found. Install with: brew install azure-cli") from e


class ManagedIdentityTokenProvider(TokenProvider):
    """Azure Managed Identity authentication."""

    def __init__(self, client_id: str | None = None) -> None:
        self.client_id = client_id

    def get_token(self, scopes: list[str]) -> str:
        """Get token from managed identity endpoint."""
        import httpx

        resource = scopes[0].rsplit("/", 1)[0] if scopes else "https://graph.microsoft.com"
        endpoint = os.environ.get("IDENTITY_ENDPOINT", "http://169.254.169.254/metadata/identity/oauth2/token")
        api_version = "2019-08-01" if "169.254.169.254" in endpoint else "2019-08-01"

        params: dict[str, str] = {
            "api-version": api_version,
            "resource": resource,
        }
        if self.client_id:
            params["client_id"] = self.client_id

        headers = {"Metadata": "true"}
        if "IDENTITY_HEADER" in os.environ:
            headers["X-IDENTITY-HEADER"] = os.environ["IDENTITY_HEADER"]

        try:
            response = httpx.get(endpoint, params=params, headers=headers, timeout=10)
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            return data["access_token"]
        except httpx.HTTPError as e:
            raise AuthenticationError(f"Managed identity authentication failed: {e}") from e


class PIMAuth:
    """High-level authentication manager for Azure PIM.

    Provides automatic token acquisition and management for both
    Microsoft Graph and Azure Resource Manager APIs.
    """

    def __init__(
        self,
        config: PIMConfig | None = None,
        provider: TokenProvider | None = None,
    ) -> None:
        self.config = config or PIMConfig.from_env()
        self._provider = provider or self._auto_select_provider()
        self._tokens: dict[str, tuple[str, datetime]] = {}

    def _auto_select_provider(self) -> TokenProvider:
        """Automatically select best available token provider."""
        if os.environ.get("IDENTITY_ENDPOINT") or os.environ.get("MSI_ENDPOINT"):
            logger.info("Using managed identity authentication")
            return ManagedIdentityTokenProvider(self.config.client_id)

        if self.config.client_secret:
            logger.info("Using client credentials authentication")
            return MSALTokenProvider(self.config)

        try:
            subprocess.run(["az", "account", "show"], capture_output=True, check=True, timeout=5)
            logger.info("Using Azure CLI authentication")
            return AzureCliTokenProvider()
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            pass

        logger.info("Using interactive browser authentication")
        return MSALTokenProvider(self.config)

    def get_graph_token(self) -> str:
        """Get access token for Microsoft Graph API."""
        return self._provider.get_token(self.config.scopes_graph)

    def get_arm_token(self) -> str:
        """Get access token for Azure Resource Manager API."""
        return self._provider.get_token(self.config.scopes_arm)

    @classmethod
    def interactive(cls, tenant_id: str, client_id: str | None = None) -> PIMAuth:
        """Create auth with interactive browser login."""
        config = PIMConfig(tenant_id=tenant_id, client_id=client_id)
        return cls(config=config, provider=MSALTokenProvider(config))

    @classmethod
    def device_code(
        cls,
        tenant_id: str,
        callback: Callable[[str], None] | None = None,
    ) -> PIMAuth:
        """Create auth with device code flow."""
        config = PIMConfig(tenant_id=tenant_id)
        return cls(config=config, provider=DeviceCodeTokenProvider(config, callback))

    @classmethod
    def client_credentials(
        cls,
        tenant_id: str,
        client_id: str,
        client_secret: str,
    ) -> PIMAuth:
        """Create auth with client credentials (app-only)."""
        config = PIMConfig(
            tenant_id=tenant_id,
            client_id=client_id,
            client_secret=client_secret,
        )
        return cls(config=config, provider=MSALTokenProvider(config))

    @classmethod
    def azure_cli(cls, tenant_id: str) -> PIMAuth:
        """Create auth using Azure CLI."""
        config = PIMConfig(tenant_id=tenant_id)
        return cls(config=config, provider=AzureCliTokenProvider())

    @classmethod
    def managed_identity(cls, tenant_id: str, client_id: str | None = None) -> PIMAuth:
        """Create auth using managed identity."""
        config = PIMConfig(tenant_id=tenant_id, client_id=client_id)
        return cls(config=config, provider=ManagedIdentityTokenProvider(client_id))
