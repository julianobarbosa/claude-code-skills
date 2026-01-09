"""High-level PIM operations combining Entra ID and Azure RBAC functionality."""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from azure_pim.clients.arm import ARMClient
from azure_pim.clients.graph import GraphClient
from azure_pim.exceptions import ActivationError, RoleNotFoundError
from azure_pim.models.azure_rbac import AzureRole, AzureRoleAssignment, AzureScope
from azure_pim.models.entra import EntraRole, EntraRoleAssignment, EntraRolePolicy

if TYPE_CHECKING:
    from azure_pim.auth import PIMAuth

logger = logging.getLogger(__name__)


class PIMOperations:
    """High-level PIM operations for both Entra ID and Azure RBAC.

    Provides a unified interface for common PIM tasks across both
    Microsoft Entra ID roles and Azure RBAC roles.

    Example:
        >>> auth = PIMAuth.azure_cli(tenant_id="...")
        >>> pim = PIMOperations(auth)
        >>>
        >>> # List all eligible roles
        >>> roles = pim.list_my_eligible_roles()
        >>>
        >>> # Activate a role
        >>> pim.activate_entra_role("Global Administrator", "Emergency access")
    """

    def __init__(self, auth: PIMAuth) -> None:
        self.auth = auth
        self._graph: GraphClient | None = None
        self._arm: ARMClient | None = None

    @property
    def graph(self) -> GraphClient:
        """Get or create Graph client."""
        if self._graph is None:
            self._graph = GraphClient(self.auth)
        return self._graph

    @property
    def arm(self) -> ARMClient:
        """Get or create ARM client."""
        if self._arm is None:
            self._arm = ARMClient(self.auth)
        return self._arm

    def close(self) -> None:
        """Close all API clients."""
        if self._graph:
            self._graph.close()
            self._graph = None
        if self._arm:
            self._arm.close()
            self._arm = None

    def __enter__(self) -> PIMOperations:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    # ==================== Entra ID Role Operations ====================

    def list_entra_roles(self) -> list[EntraRole]:
        """List all Entra ID role definitions."""
        data = self.graph.list_role_definitions()
        return [EntraRole.model_validate(r) for r in data]

    def get_entra_role(self, role_name_or_id: str) -> EntraRole:
        """Get Entra ID role by name or ID.

        Args:
            role_name_or_id: Role display name (e.g., "Global Administrator")
                           or role definition ID/template ID
        """
        role_data = self.graph.find_role_by_name(role_name_or_id)
        if role_data:
            return EntraRole.model_validate(role_data)

        try:
            role_data = self.graph.get_role_definition(role_name_or_id)
            return EntraRole.model_validate(role_data)
        except RoleNotFoundError:
            pass

        msg = f"Role not found: {role_name_or_id}"
        raise RoleNotFoundError(msg)

    def list_my_eligible_entra_roles(self) -> list[dict[str, Any]]:
        """List current user's eligible Entra ID roles."""
        return self.graph.list_my_eligible_roles()

    def list_my_active_entra_roles(self) -> list[dict[str, Any]]:
        """List current user's active Entra ID roles."""
        return self.graph.list_my_active_roles()

    def get_entra_role_policy(self, role_name_or_id: str) -> EntraRolePolicy | None:
        """Get the policy for an Entra ID role."""
        role = self.get_entra_role(role_name_or_id)
        policy_data = self.graph.get_policy_for_role(role.role_id)
        return EntraRolePolicy.model_validate(policy_data) if policy_data else None

    def activate_entra_role(
        self,
        role_name_or_id: str,
        justification: str,
        duration: str = "PT1H",
        scope: str = "/",
        ticket_number: str | None = None,
        ticket_system: str | None = None,
    ) -> dict[str, Any]:
        """Activate an eligible Entra ID role.

        Args:
            role_name_or_id: Role to activate (name or ID)
            justification: Reason for activation
            duration: How long to activate (ISO 8601, default 1 hour)
            scope: Directory scope (/ for tenant-wide)
            ticket_number: Optional ticket reference
            ticket_system: Optional ticket system name

        Returns:
            Activation request result
        """
        role = self.get_entra_role(role_name_or_id)
        logger.info("Activating role: %s for %s", role.display_name, duration)

        return self.graph.activate_role(
            role_definition_id=role.role_id,
            directory_scope_id=scope,
            justification=justification,
            duration=duration,
            ticket_number=ticket_number,
            ticket_system=ticket_system,
        )

    def deactivate_entra_role(
        self,
        role_name_or_id: str,
        scope: str = "/",
    ) -> dict[str, Any]:
        """Deactivate an active Entra ID role early."""
        role = self.get_entra_role(role_name_or_id)
        logger.info("Deactivating role: %s", role.display_name)

        return self.graph.deactivate_role(
            role_definition_id=role.role_id,
            directory_scope_id=scope,
        )

    def assign_eligible_entra_role(
        self,
        principal_id: str,
        role_name_or_id: str,
        justification: str = "",
        scope: str = "/",
        expiration_type: str = "noExpiration",
        expiration_duration: str | None = None,
    ) -> dict[str, Any]:
        """Create an eligible Entra ID role assignment."""
        role = self.get_entra_role(role_name_or_id)
        logger.info("Assigning eligible role %s to %s", role.display_name, principal_id)

        return self.graph.create_eligible_assignment(
            principal_id=principal_id,
            role_definition_id=role.role_id,
            directory_scope_id=scope,
            justification=justification,
            expiration_type=expiration_type,
            expiration_duration=expiration_duration,
        )

    def remove_eligible_entra_role(
        self,
        principal_id: str,
        role_name_or_id: str,
        justification: str = "",
        scope: str = "/",
    ) -> dict[str, Any]:
        """Remove an eligible Entra ID role assignment."""
        role = self.get_entra_role(role_name_or_id)
        logger.info("Removing eligible role %s from %s", role.display_name, principal_id)

        return self.graph.remove_eligible_assignment(
            principal_id=principal_id,
            role_definition_id=role.role_id,
            directory_scope_id=scope,
            justification=justification,
        )

    # ==================== Azure RBAC Role Operations ====================

    def list_azure_roles(self, scope: str | AzureScope) -> list[AzureRole]:
        """List Azure RBAC role definitions at scope."""
        scope_str = scope.to_string() if isinstance(scope, AzureScope) else scope
        data = self.arm.list_role_definitions(scope_str)
        return [AzureRole.model_validate(r) for r in data]

    def get_azure_role(self, scope: str | AzureScope, role_name_or_id: str) -> AzureRole:
        """Get Azure RBAC role by name or ID."""
        scope_str = scope.to_string() if isinstance(scope, AzureScope) else scope

        role_data = self.arm.find_role_by_name(scope_str, role_name_or_id)
        if role_data:
            return AzureRole.model_validate(role_data)

        try:
            role_data = self.arm.get_role_definition(scope_str, role_name_or_id)
            return AzureRole.model_validate(role_data)
        except RoleNotFoundError:
            pass

        msg = f"Role not found: {role_name_or_id}"
        raise RoleNotFoundError(msg)

    def list_my_eligible_azure_roles(
        self,
        scope: str | AzureScope,
        principal_id: str | None = None,
    ) -> list[AzureRoleAssignment]:
        """List eligible Azure RBAC roles at scope."""
        scope_str = scope.to_string() if isinstance(scope, AzureScope) else scope
        data = self.arm.list_eligible_schedule_instances(scope_str, principal_id)
        return [AzureRoleAssignment.model_validate(r) for r in data]

    def list_my_active_azure_roles(
        self,
        scope: str | AzureScope,
        principal_id: str | None = None,
    ) -> list[AzureRoleAssignment]:
        """List active Azure RBAC roles at scope."""
        scope_str = scope.to_string() if isinstance(scope, AzureScope) else scope
        data = self.arm.list_active_schedule_instances(scope_str, principal_id)
        return [AzureRoleAssignment.model_validate(r) for r in data]

    def activate_azure_role(
        self,
        scope: str | AzureScope,
        role_name_or_id: str,
        justification: str,
        duration: str = "PT1H",
        ticket_number: str | None = None,
        ticket_system: str | None = None,
    ) -> dict[str, Any]:
        """Activate an eligible Azure RBAC role.

        Args:
            scope: Azure scope (subscription, resource group, etc.)
            role_name_or_id: Role to activate (e.g., "Owner", "Contributor")
            justification: Reason for activation
            duration: How long to activate (ISO 8601)
            ticket_number: Optional ticket reference
            ticket_system: Optional ticket system name

        Returns:
            Activation request result
        """
        scope_str = scope.to_string() if isinstance(scope, AzureScope) else scope
        role = self.get_azure_role(scope_str, role_name_or_id)

        request_id = str(uuid.uuid4())
        logger.info("Activating Azure role %s at %s", role.role_name, scope_str)

        return self.arm.activate_role(
            scope=scope_str,
            role_definition_id=role.id,
            request_id=request_id,
            justification=justification,
            duration=duration,
            ticket_number=ticket_number,
            ticket_system=ticket_system,
        )

    def deactivate_azure_role(
        self,
        scope: str | AzureScope,
        role_name_or_id: str,
    ) -> dict[str, Any]:
        """Deactivate an active Azure RBAC role early."""
        scope_str = scope.to_string() if isinstance(scope, AzureScope) else scope
        role = self.get_azure_role(scope_str, role_name_or_id)

        request_id = str(uuid.uuid4())
        logger.info("Deactivating Azure role %s at %s", role.role_name, scope_str)

        return self.arm.deactivate_role(
            scope=scope_str,
            role_definition_id=role.id,
            request_id=request_id,
        )

    def assign_eligible_azure_role(
        self,
        scope: str | AzureScope,
        principal_id: str,
        role_name_or_id: str,
        justification: str = "",
        expiration_type: str = "NoExpiration",
        expiration_duration: str | None = None,
    ) -> dict[str, Any]:
        """Create an eligible Azure RBAC role assignment."""
        scope_str = scope.to_string() if isinstance(scope, AzureScope) else scope
        role = self.get_azure_role(scope_str, role_name_or_id)

        request_id = str(uuid.uuid4())
        logger.info("Assigning eligible Azure role %s to %s", role.role_name, principal_id)

        return self.arm.create_eligible_assignment(
            scope=scope_str,
            principal_id=principal_id,
            role_definition_id=role.id,
            request_id=request_id,
            justification=justification,
            expiration_type=expiration_type,
            expiration_duration=expiration_duration,
        )

    def remove_eligible_azure_role(
        self,
        scope: str | AzureScope,
        principal_id: str,
        role_name_or_id: str,
        justification: str = "",
    ) -> dict[str, Any]:
        """Remove an eligible Azure RBAC role assignment."""
        scope_str = scope.to_string() if isinstance(scope, AzureScope) else scope
        role = self.get_azure_role(scope_str, role_name_or_id)

        request_id = str(uuid.uuid4())
        logger.info("Removing eligible Azure role %s from %s", role.role_name, principal_id)

        return self.arm.remove_eligible_assignment(
            scope=scope_str,
            principal_id=principal_id,
            role_definition_id=role.id,
            request_id=request_id,
            justification=justification,
        )

    # ==================== Unified Operations ====================

    def whoami(self) -> dict[str, Any]:
        """Get current authenticated user information."""
        return self.graph.get_current_user()

    def list_pim_audit_events(self, top: int = 50) -> list[dict[str, Any]]:
        """List recent PIM audit events."""
        return self.graph.list_pim_audit_logs(top=top)
