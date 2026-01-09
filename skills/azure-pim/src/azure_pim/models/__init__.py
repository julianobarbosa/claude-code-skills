"""Pydantic models for Azure PIM data structures."""

from azure_pim.models.common import (
    AssignmentType,
    ExpirationPattern,
    PIMAction,
    RequestSchedule,
    RequestStatus,
    TicketInfo,
)
from azure_pim.models.entra import (
    EntraRole,
    EntraRoleAssignment,
    EntraRolePolicy,
    RoleActivationRequest,
    RoleAssignmentRequest,
)
from azure_pim.models.azure_rbac import (
    AzureRole,
    AzureRoleAssignment,
    AzureScope,
)

__all__ = [
    # Common
    "AssignmentType",
    "PIMAction",
    "RequestStatus",
    "RequestSchedule",
    "ExpirationPattern",
    "TicketInfo",
    # Entra ID
    "EntraRole",
    "EntraRoleAssignment",
    "EntraRolePolicy",
    "RoleActivationRequest",
    "RoleAssignmentRequest",
    # Azure RBAC
    "AzureRole",
    "AzureRoleAssignment",
    "AzureScope",
]
