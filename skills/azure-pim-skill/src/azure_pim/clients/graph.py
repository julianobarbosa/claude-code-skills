"""Microsoft Graph API client for Entra ID PIM operations.

Handles:
- unifiedRoleAssignmentScheduleRequest - Active role assignments
- unifiedRoleEligibilityScheduleRequest - Eligible role assignments
- unifiedRoleManagementPolicy - Policy and rules management
- directoryAudits - Audit logging
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import httpx

from azure_pim.exceptions import APIError, AssignmentNotFoundError, RateLimitError, RoleNotFoundError

if TYPE_CHECKING:
    from azure_pim.auth import PIMAuth

logger = logging.getLogger(__name__)


class GraphClient:
    """Microsoft Graph API client for Entra ID PIM.

    Example:
        >>> auth = PIMAuth.azure_cli(tenant_id="...")
        >>> client = GraphClient(auth)
        >>> roles = client.list_eligible_roles()
    """

    BASE_URL = "https://graph.microsoft.com/v1.0"
    BETA_URL = "https://graph.microsoft.com/beta"

    def __init__(self, auth: PIMAuth, timeout: float = 30.0) -> None:
        self.auth = auth
        self.timeout = timeout
        self._client: httpx.Client | None = None

    def _get_client(self) -> httpx.Client:
        """Get or create HTTP client with auth headers."""
        token = self.auth.get_graph_token()
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.BASE_URL,
                timeout=self.timeout,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
            )
        else:
            self._client.headers["Authorization"] = f"Bearer {token}"
        return self._client

    def _request(
        self,
        method: str,
        endpoint: str,
        *,
        json_data: dict[str, Any] | None = None,
        params: dict[str, str] | None = None,
        use_beta: bool = False,
    ) -> dict[str, Any]:
        """Make HTTP request to Graph API."""
        client = self._get_client()

        if use_beta:
            url = f"{self.BETA_URL}{endpoint}"
        else:
            url = endpoint

        try:
            response = client.request(
                method,
                url,
                json=json_data,
                params=params,
            )

            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After", "60")
                raise RateLimitError(
                    f"Rate limited. Retry after {retry_after} seconds",
                    status_code=429,
                )

            if response.status_code == 404:
                raise RoleNotFoundError(f"Resource not found: {endpoint}")

            if response.status_code >= 400:
                body = response.json() if response.content else {}
                error_msg = body.get("error", {}).get("message", response.text)
                raise APIError(
                    f"Graph API error: {error_msg}",
                    status_code=response.status_code,
                    response_body=body,
                )

            if response.status_code == 204:
                return {}

            return response.json()

        except httpx.HTTPError as e:
            raise APIError(f"HTTP request failed: {e}", status_code=0) from e

    def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self) -> GraphClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    # ==================== Role Definitions ====================

    def list_role_definitions(self) -> list[dict[str, Any]]:
        """List all directory role definitions."""
        result = self._request("GET", "/roleManagement/directory/roleDefinitions")
        return result.get("value", [])

    def get_role_definition(self, role_id: str) -> dict[str, Any]:
        """Get a specific role definition by ID or template ID."""
        return self._request("GET", f"/roleManagement/directory/roleDefinitions/{role_id}")

    def find_role_by_name(self, display_name: str) -> dict[str, Any] | None:
        """Find role definition by display name."""
        result = self._request(
            "GET",
            "/roleManagement/directory/roleDefinitions",
            params={"$filter": f"displayName eq '{display_name}'"},
        )
        roles = result.get("value", [])
        return roles[0] if roles else None

    # ==================== Eligible Role Assignments ====================

    def list_eligible_assignments(
        self,
        principal_id: str | None = None,
        role_definition_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """List eligible role assignments.

        Args:
            principal_id: Filter by user/service principal ID
            role_definition_id: Filter by role definition ID
        """
        filters = []
        if principal_id:
            filters.append(f"principalId eq '{principal_id}'")
        if role_definition_id:
            filters.append(f"roleDefinitionId eq '{role_definition_id}'")

        params: dict[str, str] = {}
        if filters:
            params["$filter"] = " and ".join(filters)

        result = self._request(
            "GET",
            "/roleManagement/directory/roleEligibilitySchedules",
            params=params,
        )
        return result.get("value", [])

    def list_my_eligible_roles(self) -> list[dict[str, Any]]:
        """List eligible roles for the current user."""
        result = self._request(
            "GET",
            "/roleManagement/directory/roleEligibilityScheduleRequests/filterByCurrentUser(on='principal')",
        )
        return result.get("value", [])

    def create_eligible_assignment(
        self,
        principal_id: str,
        role_definition_id: str,
        directory_scope_id: str = "/",
        justification: str = "",
        start_datetime: str | None = None,
        expiration_type: str = "noExpiration",
        expiration_duration: str | None = None,
        expiration_datetime: str | None = None,
    ) -> dict[str, Any]:
        """Create an eligible role assignment.

        Args:
            principal_id: User or service principal ID
            role_definition_id: Role definition ID or template ID
            directory_scope_id: Scope (/ for tenant-wide)
            justification: Reason for the assignment
            start_datetime: When the eligibility starts (ISO 8601)
            expiration_type: "noExpiration", "afterDuration", "afterDateTime"
            expiration_duration: Duration in ISO 8601 (e.g., "P365D")
            expiration_datetime: End date in ISO 8601
        """
        schedule_info: dict[str, Any] = {}
        if start_datetime:
            schedule_info["startDateTime"] = start_datetime

        expiration: dict[str, Any] = {"type": expiration_type}
        if expiration_duration:
            expiration["duration"] = expiration_duration
        if expiration_datetime:
            expiration["endDateTime"] = expiration_datetime
        schedule_info["expiration"] = expiration

        payload = {
            "action": "adminAssign",
            "principalId": principal_id,
            "roleDefinitionId": role_definition_id,
            "directoryScopeId": directory_scope_id,
            "justification": justification,
            "scheduleInfo": schedule_info,
        }

        return self._request(
            "POST",
            "/roleManagement/directory/roleEligibilityScheduleRequests",
            json_data=payload,
        )

    def remove_eligible_assignment(
        self,
        principal_id: str,
        role_definition_id: str,
        directory_scope_id: str = "/",
        justification: str = "",
    ) -> dict[str, Any]:
        """Remove an eligible role assignment."""
        payload = {
            "action": "adminRemove",
            "principalId": principal_id,
            "roleDefinitionId": role_definition_id,
            "directoryScopeId": directory_scope_id,
            "justification": justification,
        }

        return self._request(
            "POST",
            "/roleManagement/directory/roleEligibilityScheduleRequests",
            json_data=payload,
        )

    # ==================== Active Role Assignments ====================

    def list_active_assignments(
        self,
        principal_id: str | None = None,
        role_definition_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """List active (assigned) role assignments."""
        filters = []
        if principal_id:
            filters.append(f"principalId eq '{principal_id}'")
        if role_definition_id:
            filters.append(f"roleDefinitionId eq '{role_definition_id}'")

        params: dict[str, str] = {}
        if filters:
            params["$filter"] = " and ".join(filters)

        result = self._request(
            "GET",
            "/roleManagement/directory/roleAssignmentSchedules",
            params=params,
        )
        return result.get("value", [])

    def list_my_active_roles(self) -> list[dict[str, Any]]:
        """List active roles for the current user."""
        result = self._request(
            "GET",
            "/roleManagement/directory/roleAssignmentScheduleRequests/filterByCurrentUser(on='principal')",
        )
        return result.get("value", [])

    def create_active_assignment(
        self,
        principal_id: str,
        role_definition_id: str,
        directory_scope_id: str = "/",
        justification: str = "",
        start_datetime: str | None = None,
        expiration_type: str = "afterDuration",
        expiration_duration: str = "PT8H",
        expiration_datetime: str | None = None,
    ) -> dict[str, Any]:
        """Create a permanent active role assignment (admin assign)."""
        schedule_info: dict[str, Any] = {}
        if start_datetime:
            schedule_info["startDateTime"] = start_datetime

        expiration: dict[str, Any] = {"type": expiration_type}
        if expiration_duration:
            expiration["duration"] = expiration_duration
        if expiration_datetime:
            expiration["endDateTime"] = expiration_datetime
        schedule_info["expiration"] = expiration

        payload = {
            "action": "adminAssign",
            "principalId": principal_id,
            "roleDefinitionId": role_definition_id,
            "directoryScopeId": directory_scope_id,
            "justification": justification,
            "scheduleInfo": schedule_info,
        }

        return self._request(
            "POST",
            "/roleManagement/directory/roleAssignmentScheduleRequests",
            json_data=payload,
        )

    # ==================== Role Activation (JIT) ====================

    def activate_role(
        self,
        role_definition_id: str,
        directory_scope_id: str = "/",
        justification: str = "",
        duration: str = "PT1H",
        ticket_number: str | None = None,
        ticket_system: str | None = None,
    ) -> dict[str, Any]:
        """Activate an eligible role (JIT activation).

        This creates a temporary active assignment for the current user.

        Args:
            role_definition_id: Role to activate
            directory_scope_id: Scope (/ for tenant-wide)
            justification: Reason for activation (often required by policy)
            duration: How long to activate (ISO 8601, max 8 hours typically)
            ticket_number: Optional ticket/incident number
            ticket_system: Optional ticket system name (e.g., "ServiceNow")
        """
        payload: dict[str, Any] = {
            "action": "selfActivate",
            "roleDefinitionId": role_definition_id,
            "directoryScopeId": directory_scope_id,
            "justification": justification,
            "scheduleInfo": {
                "expiration": {
                    "type": "afterDuration",
                    "duration": duration,
                },
            },
        }

        if ticket_number or ticket_system:
            payload["ticketInfo"] = {}
            if ticket_number:
                payload["ticketInfo"]["ticketNumber"] = ticket_number
            if ticket_system:
                payload["ticketInfo"]["ticketSystem"] = ticket_system

        return self._request(
            "POST",
            "/roleManagement/directory/roleAssignmentScheduleRequests",
            json_data=payload,
        )

    def deactivate_role(
        self,
        role_definition_id: str,
        directory_scope_id: str = "/",
    ) -> dict[str, Any]:
        """Deactivate an active role early."""
        payload = {
            "action": "selfDeactivate",
            "roleDefinitionId": role_definition_id,
            "directoryScopeId": directory_scope_id,
        }

        return self._request(
            "POST",
            "/roleManagement/directory/roleAssignmentScheduleRequests",
            json_data=payload,
        )

    # ==================== Role Management Policies ====================

    def list_policies(self) -> list[dict[str, Any]]:
        """List all role management policies."""
        result = self._request(
            "GET",
            "/policies/roleManagementPolicies",
            params={"$expand": "rules"},
        )
        return result.get("value", [])

    def get_policy(self, policy_id: str) -> dict[str, Any]:
        """Get a specific policy with its rules."""
        return self._request(
            "GET",
            f"/policies/roleManagementPolicies/{policy_id}",
            params={"$expand": "rules"},
        )

    def get_policy_for_role(self, role_definition_id: str) -> dict[str, Any] | None:
        """Get the policy assigned to a specific role."""
        result = self._request(
            "GET",
            "/policies/roleManagementPolicyAssignments",
            params={
                "$filter": f"roleDefinitionId eq '{role_definition_id}' and scopeId eq '/' and scopeType eq 'DirectoryRole'"
            },
        )
        assignments = result.get("value", [])
        if not assignments:
            return None

        policy_id = assignments[0].get("policyId")
        return self.get_policy(policy_id) if policy_id else None

    # ==================== Audit Logs ====================

    def list_audit_logs(
        self,
        filter_query: str | None = None,
        top: int = 100,
    ) -> list[dict[str, Any]]:
        """List directory audit logs.

        Example filter: "activityDisplayName eq 'Add member to role'"
        """
        params: dict[str, str] = {"$top": str(top)}
        if filter_query:
            params["$filter"] = filter_query

        result = self._request("GET", "/auditLogs/directoryAudits", params=params)
        return result.get("value", [])

    def list_pim_audit_logs(self, top: int = 100) -> list[dict[str, Any]]:
        """List PIM-specific audit events."""
        return self.list_audit_logs(
            filter_query="category eq 'RoleManagement'",
            top=top,
        )

    # ==================== User/Principal Info ====================

    def get_current_user(self) -> dict[str, Any]:
        """Get the current signed-in user's profile."""
        return self._request("GET", "/me")

    def get_user(self, user_id: str) -> dict[str, Any]:
        """Get user by ID or UPN."""
        return self._request("GET", f"/users/{user_id}")

    def get_service_principal(self, sp_id: str) -> dict[str, Any]:
        """Get service principal by ID."""
        return self._request("GET", f"/servicePrincipals/{sp_id}")
