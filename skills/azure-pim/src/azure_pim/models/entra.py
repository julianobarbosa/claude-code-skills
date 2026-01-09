"""Models for Microsoft Entra ID (Azure AD) PIM operations."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from azure_pim.models.common import (
    AssignmentType,
    ExpirationPattern,
    PIMAction,
    Principal,
    RequestSchedule,
    RequestStatus,
    TicketInfo,
)


class EntraRole(BaseModel):
    """Microsoft Entra directory role definition."""

    id: str = Field(description="Role definition ID")
    display_name: str = Field(alias="displayName")
    description: str | None = None
    template_id: str | None = Field(default=None, alias="templateId")
    is_built_in: bool = Field(default=True, alias="isBuiltIn")
    is_enabled: bool = Field(default=True, alias="isEnabled")

    @property
    def role_id(self) -> str:
        """Get the role template ID for API operations."""
        return self.template_id or self.id


class EntraRoleAssignment(BaseModel):
    """Entra ID role assignment (eligible or active)."""

    id: str
    principal_id: str = Field(alias="principalId")
    role_definition_id: str = Field(alias="roleDefinitionId")
    directory_scope_id: str = Field(default="/", alias="directoryScopeId")
    assignment_type: AssignmentType = Field(alias="memberType")
    status: str | None = None
    created_datetime: datetime | None = Field(default=None, alias="createdDateTime")
    start_datetime: datetime | None = Field(default=None, alias="startDateTime")
    end_datetime: datetime | None = Field(default=None, alias="endDateTime")

    # Expanded relations
    principal: Principal | None = None
    role_definition: EntraRole | None = Field(default=None, alias="roleDefinition")


class RoleActivationRequest(BaseModel):
    """Request to activate an eligible Entra ID role."""

    role_definition_id: str = Field(
        description="Role definition ID or template ID to activate",
    )
    directory_scope_id: str = Field(
        default="/",
        description="Scope: / for tenant-wide or /administrativeUnits/{id}",
    )
    justification: str = Field(
        default="",
        description="Reason for activation (required by most policies)",
    )
    duration: str = Field(
        default="PT1H",
        description="Activation duration in ISO 8601 (e.g., PT1H, PT8H)",
    )
    ticket_info: TicketInfo | None = Field(
        default=None,
        description="Optional ticket/incident reference",
    )


class RoleAssignmentRequest(BaseModel):
    """Request to create/modify a role assignment."""

    action: PIMAction = Field(description="Action to perform")
    principal_id: str = Field(description="Target user or service principal ID")
    role_definition_id: str = Field(description="Role to assign")
    directory_scope_id: str = Field(default="/", description="Scope")
    justification: str = Field(default="", description="Reason for request")
    schedule_info: RequestSchedule = Field(
        default_factory=RequestSchedule,
        alias="scheduleInfo",
    )
    ticket_info: TicketInfo | None = Field(default=None, alias="ticketInfo")


class RoleAssignmentRequestResult(BaseModel):
    """Result of a role assignment request."""

    id: str
    status: RequestStatus
    action: str = Field(alias="action")
    principal_id: str = Field(alias="principalId")
    role_definition_id: str = Field(alias="roleDefinitionId")
    directory_scope_id: str = Field(alias="directoryScopeId")
    created_datetime: datetime = Field(alias="createdDateTime")
    completed_datetime: datetime | None = Field(default=None, alias="completedDateTime")
    approval_id: str | None = Field(default=None, alias="approvalId")


class EntraRolePolicy(BaseModel):
    """Role management policy for an Entra ID role."""

    id: str
    display_name: str | None = Field(default=None, alias="displayName")
    description: str | None = None
    is_organization_default: bool = Field(default=False, alias="isOrganizationDefault")
    scope_id: str = Field(alias="scopeId")
    scope_type: str = Field(alias="scopeType")
    rules: list[dict[str, Any]] = Field(default_factory=list)

    def get_rule(self, rule_type: str) -> dict[str, Any] | None:
        """Get a specific rule by its @odata.type."""
        for rule in self.rules:
            if rule.get("@odata.type", "").endswith(rule_type):
                return rule
        return None

    @property
    def max_activation_duration(self) -> str | None:
        """Get maximum activation duration from policy."""
        rule = self.get_rule("ExpirationRule")
        if rule and rule.get("id") == "Expiration_EndUser_Assignment":
            return rule.get("maximumDuration")
        return None

    @property
    def requires_mfa(self) -> bool:
        """Check if MFA is required for activation."""
        rule = self.get_rule("AuthenticationContextRule")
        if rule:
            return rule.get("isEnabled", False)
        return False

    @property
    def requires_justification(self) -> bool:
        """Check if justification is required for activation."""
        rule = self.get_rule("EnabledRule")
        if rule and rule.get("id") == "Justification_EndUser_Assignment":
            return rule.get("isEnabled", False)
        return False

    @property
    def requires_approval(self) -> bool:
        """Check if approval is required for activation."""
        rule = self.get_rule("ApprovalRule")
        if rule:
            setting = rule.get("setting", {})
            return setting.get("isApprovalRequired", False)
        return False
