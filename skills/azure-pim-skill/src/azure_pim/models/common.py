"""Common models shared across Entra ID and Azure RBAC PIM."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class PIMAction(str, Enum):
    """PIM request actions."""

    ADMIN_ASSIGN = "adminAssign"
    ADMIN_REMOVE = "adminRemove"
    ADMIN_EXTEND = "adminExtend"
    ADMIN_RENEW = "adminRenew"
    SELF_ACTIVATE = "selfActivate"
    SELF_DEACTIVATE = "selfDeactivate"
    SELF_EXTEND = "selfExtend"
    SELF_RENEW = "selfRenew"


class RequestStatus(str, Enum):
    """PIM request status."""

    PENDING = "Pending"
    PENDING_APPROVAL = "PendingApproval"
    PENDING_SCHEDULE = "PendingScheduleCreation"
    PROVISIONED = "Provisioned"
    GRANTED = "Granted"
    DENIED = "Denied"
    FAILED = "Failed"
    CANCELED = "Canceled"
    REVOKED = "Revoked"
    SCHEDULED = "Scheduled"
    EXPIRED = "Expired"


class AssignmentType(str, Enum):
    """Type of role assignment."""

    ELIGIBLE = "Eligible"
    ACTIVE = "Active"


class ExpirationPattern(BaseModel):
    """Expiration settings for role assignments."""

    type: str = Field(
        default="noExpiration",
        description="Expiration type: noExpiration, afterDuration, afterDateTime",
    )
    duration: str | None = Field(
        default=None,
        description="ISO 8601 duration (e.g., PT1H, P365D)",
    )
    end_datetime: datetime | None = Field(
        default=None,
        alias="endDateTime",
        description="Specific end date/time",
    )


class RequestSchedule(BaseModel):
    """Schedule information for role requests."""

    start_datetime: datetime | None = Field(
        default=None,
        alias="startDateTime",
        description="When the assignment starts",
    )
    expiration: ExpirationPattern = Field(
        default_factory=ExpirationPattern,
        description="Expiration settings",
    )


class TicketInfo(BaseModel):
    """Ticket/incident information for audit trail."""

    ticket_number: str | None = Field(
        default=None,
        alias="ticketNumber",
        description="Ticket or incident number",
    )
    ticket_system: str | None = Field(
        default=None,
        alias="ticketSystem",
        description="Ticket system name (e.g., ServiceNow, Jira)",
    )


class Principal(BaseModel):
    """User or service principal reference."""

    id: str = Field(description="Object ID of the principal")
    display_name: str | None = Field(default=None, alias="displayName")
    type: str | None = Field(default=None, alias="@odata.type")
    user_principal_name: str | None = Field(default=None, alias="userPrincipalName")


class AuditEvent(BaseModel):
    """Audit log event."""

    id: str
    activity_display_name: str = Field(alias="activityDisplayName")
    activity_date_time: datetime = Field(alias="activityDateTime")
    category: str
    initiated_by: dict[str, Any] = Field(alias="initiatedBy")
    target_resources: list[dict[str, Any]] = Field(alias="targetResources")
    result: str
    result_reason: str | None = Field(default=None, alias="resultReason")
