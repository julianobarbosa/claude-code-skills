"""Configuration management for Azure PIM."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class PIMConfig:
    """Configuration for Azure PIM operations.

    Attributes:
        tenant_id: Azure AD tenant ID
        client_id: Application (client) ID for authentication
        client_secret: Client secret (for app-only auth)
        authority: Azure AD authority URL
        scopes_graph: Scopes for Microsoft Graph API
        scopes_arm: Scopes for Azure Resource Manager API
        default_duration: Default activation duration (ISO 8601)
        cache_path: Path to token cache file
    """

    tenant_id: str
    client_id: str | None = None
    client_secret: str | None = None
    authority: str = ""
    scopes_graph: list[str] = field(default_factory=list)
    scopes_arm: list[str] = field(default_factory=list)
    default_duration: str = "PT1H"
    cache_path: Path = field(default_factory=lambda: Path.home() / ".azure-pim" / "token_cache")

    def __post_init__(self) -> None:
        if not self.authority:
            self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        if not self.scopes_graph:
            self.scopes_graph = [
                "https://graph.microsoft.com/RoleManagement.ReadWrite.Directory",
                "https://graph.microsoft.com/RoleEligibilitySchedule.ReadWrite.Directory",
                "https://graph.microsoft.com/RoleAssignmentSchedule.ReadWrite.Directory",
            ]
        if not self.scopes_arm:
            self.scopes_arm = ["https://management.azure.com/.default"]

    @classmethod
    def from_env(cls) -> PIMConfig:
        """Create configuration from environment variables."""
        tenant_id = os.environ.get("ARM_TENANT_ID", "")
        if not tenant_id:
            msg = "ARM_TENANT_ID environment variable is required"
            raise ValueError(msg)

        return cls(
            tenant_id=tenant_id,
            client_id=os.environ.get("AZURE_CLIENT_ID"),
            client_secret=os.environ.get("AZURE_CLIENT_SECRET"),
            default_duration=os.environ.get("PIM_DEFAULT_DURATION", "PT1H"),
        )

    @classmethod
    def from_file(cls, path: str | Path) -> PIMConfig:
        """Load configuration from YAML file."""
        config_path = Path(path)
        if not config_path.exists():
            msg = f"Config file not found: {config_path}"
            raise FileNotFoundError(msg)

        with config_path.open() as f:
            data: dict[str, Any] = yaml.safe_load(f)

        return cls(
            tenant_id=data.get("tenant_id", ""),
            client_id=data.get("client_id"),
            client_secret=data.get("client_secret"),
            default_duration=data.get("default_duration", "PT1H"),
        )

    def save(self, path: str | Path) -> None:
        """Save configuration to YAML file (excluding secrets)."""
        config_path = Path(path)
        config_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "tenant_id": self.tenant_id,
            "client_id": self.client_id,
            "default_duration": self.default_duration,
        }

        with config_path.open("w") as f:
            yaml.safe_dump(data, f, default_flow_style=False)
