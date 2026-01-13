"""Models for Azure RBAC PIM operations."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from azure_pim.models.common import AssignmentType, RequestStatus


class AzureScope(BaseModel):
    """Azure resource scope."""

    subscription_id: str = Field(description="Azure subscription ID")
    resource_group: str | None = Field(
        default=None,
        description="Resource group name (optional)",
    )
    provider: str | None = Field(
        default=None,
        description="Resource provider (e.g., Microsoft.Compute)",
    )
    resource_type: str | None = Field(
        default=None,
        description="Resource type (e.g., virtualMachines)",
    )
    resource_name: str | None = Field(
        default=None,
        description="Resource name",
    )

    def to_string(self) -> str:
        """Convert to Azure scope string."""
        scope = f"/subscriptions/{self.subscription_id}"
        if self.resource_group:
            scope += f"/resourceGroups/{self.resource_group}"
        if self.provider and self.resource_type and self.resource_name:
            scope += f"/providers/{self.provider}/{self.resource_type}/{self.resource_name}"
        return scope

    @classmethod
    def from_string(cls, scope: str) -> AzureScope:
        """Parse Azure scope string."""
        parts = scope.strip("/").split("/")

        subscription_id = ""
        resource_group = None
        provider = None
        resource_type = None
        resource_name = None

        i = 0
        while i < len(parts):
            if parts[i].lower() == "subscriptions" and i + 1 < len(parts):
                subscription_id = parts[i + 1]
                i += 2
            elif parts[i].lower() == "resourcegroups" and i + 1 < len(parts):
                resource_group = parts[i + 1]
                i += 2
            elif parts[i].lower() == "providers" and i + 3 < len(parts):
                provider = parts[i + 1]
                resource_type = parts[i + 2]
                resource_name = parts[i + 3]
                i += 4
            else:
                i += 1

        return cls(
            subscription_id=subscription_id,
            resource_group=resource_group,
            provider=provider,
            resource_type=resource_type,
            resource_name=resource_name,
        )

    @classmethod
    def subscription(cls, subscription_id: str) -> AzureScope:
        """Create scope for entire subscription."""
        return cls(subscription_id=subscription_id)

    @classmethod
    def resource_group_scope(cls, subscription_id: str, resource_group: str) -> AzureScope:
        """Create scope for a resource group."""
        return cls(subscription_id=subscription_id, resource_group=resource_group)


class AzureRole(BaseModel):
    """Azure RBAC role definition."""

    id: str = Field(description="Full role definition ID")
    name: str = Field(description="Role definition GUID")
    type: str = Field(description="Resource type")
    properties: dict[str, Any] = Field(default_factory=dict)

    @property
    def role_name(self) -> str:
        """Get display name of the role."""
        return self.properties.get("roleName", "")

    @property
    def description(self) -> str:
        """Get role description."""
        return self.properties.get("description", "")

    @property
    def role_type(self) -> str:
        """Get role type (BuiltInRole or CustomRole)."""
        return self.properties.get("type", "")

    @property
    def permissions(self) -> list[dict[str, Any]]:
        """Get role permissions."""
        return self.properties.get("permissions", [])


class AzureRoleAssignment(BaseModel):
    """Azure RBAC role assignment (eligible or active)."""

    id: str
    name: str
    type: str
    properties: dict[str, Any] = Field(default_factory=dict)

    @property
    def principal_id(self) -> str:
        """Get assigned principal ID."""
        return self.properties.get("principalId", "")

    @property
    def principal_type(self) -> str:
        """Get principal type (User, Group, ServicePrincipal)."""
        return self.properties.get("principalType", "")

    @property
    def role_definition_id(self) -> str:
        """Get role definition ID."""
        return self.properties.get("roleDefinitionId", "") or self.properties.get(
            "expandedProperties", {}
        ).get("roleDefinition", {}).get("id", "")

    @property
    def scope(self) -> str:
        """Get assignment scope."""
        return self.properties.get("scope", "")

    @property
    def status(self) -> str:
        """Get assignment status."""
        return self.properties.get("status", "")

    @property
    def start_datetime(self) -> datetime | None:
        """Get start time."""
        start = self.properties.get("startDateTime")
        return datetime.fromisoformat(start.replace("Z", "+00:00")) if start else None

    @property
    def end_datetime(self) -> datetime | None:
        """Get end time."""
        end = self.properties.get("endDateTime")
        return datetime.fromisoformat(end.replace("Z", "+00:00")) if end else None

    @property
    def assignment_type(self) -> AssignmentType:
        """Get assignment type based on resource type."""
        if "roleEligibility" in self.type.lower():
            return AssignmentType.ELIGIBLE
        return AssignmentType.ACTIVE


class AzureRoleAssignmentRequest(BaseModel):
    """Azure RBAC role assignment request."""

    id: str
    name: str
    type: str
    properties: dict[str, Any] = Field(default_factory=dict)

    @property
    def status(self) -> RequestStatus:
        """Get request status."""
        status_str = self.properties.get("status", "")
        try:
            return RequestStatus(status_str)
        except ValueError:
            return RequestStatus.PENDING

    @property
    def request_type(self) -> str:
        """Get request type (AdminAssign, SelfActivate, etc.)."""
        return self.properties.get("requestType", "")

    @property
    def principal_id(self) -> str:
        """Get target principal ID."""
        return self.properties.get("principalId", "")

    @property
    def role_definition_id(self) -> str:
        """Get role definition ID."""
        return self.properties.get("roleDefinitionId", "")

    @property
    def justification(self) -> str:
        """Get request justification."""
        return self.properties.get("justification", "")

    @property
    def created_datetime(self) -> datetime | None:
        """Get creation time."""
        created = self.properties.get("createdDateTime")
        return datetime.fromisoformat(created.replace("Z", "+00:00")) if created else None
