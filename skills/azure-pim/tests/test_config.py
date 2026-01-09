"""Tests for PIM configuration."""

import os
import tempfile
from pathlib import Path

import pytest

from azure_pim.config import PIMConfig


class TestPIMConfig:
    """Tests for PIMConfig."""

    def test_default_values(self) -> None:
        config = PIMConfig(tenant_id="test-tenant")
        assert config.tenant_id == "test-tenant"
        assert config.default_duration == "PT1H"
        assert "graph.microsoft.com" in config.scopes_graph[0]

    def test_authority_auto_set(self) -> None:
        config = PIMConfig(tenant_id="my-tenant-id")
        assert config.authority == "https://login.microsoftonline.com/my-tenant-id"

    def test_from_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.setenv("ARM_TENANT_ID", "env-tenant")
        monkeypatch.setenv("AZURE_CLIENT_ID", "env-client")
        monkeypatch.setenv("PIM_DEFAULT_DURATION", "PT2H")

        config = PIMConfig.from_env()
        assert config.tenant_id == "env-tenant"
        assert config.client_id == "env-client"
        assert config.default_duration == "PT2H"

    def test_from_env_missing_tenant(self, monkeypatch: pytest.MonkeyPatch) -> None:
        monkeypatch.delenv("ARM_TENANT_ID", raising=False)

        with pytest.raises(ValueError, match="ARM_TENANT_ID"):
            PIMConfig.from_env()

    def test_save_and_load(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "config.yaml"

            original = PIMConfig(
                tenant_id="save-tenant",
                client_id="save-client",
                default_duration="PT4H",
            )
            original.save(config_path)

            loaded = PIMConfig.from_file(config_path)
            assert loaded.tenant_id == "save-tenant"
            assert loaded.client_id == "save-client"
            assert loaded.default_duration == "PT4H"

    def test_from_file_not_found(self) -> None:
        with pytest.raises(FileNotFoundError):
            PIMConfig.from_file("/nonexistent/config.yaml")
