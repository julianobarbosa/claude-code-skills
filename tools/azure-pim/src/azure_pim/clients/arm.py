"""Azure Resource Manager (ARM) client for Azure RBAC PIM operations.

Handles PIM for Azure resources:
- roleAssignmentScheduleRequests - Active role assignments
- roleEligibilityScheduleRequests - Eligible role assignments
- Scope: Subscriptions, Resource Groups, Resources
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any
from urllib.parse import quote

import httpx

from azure_pim.exceptions import APIError, RateLimitError, RoleNotFoundError

if TYPE_CHECKING:
    from azure_pim.auth import PIMAuth

logger = logging.getLogger(__name__)


class ARMClient:
    """Azure Resource Manager client for Azure RBAC PIM.

    Manages PIM for Azure resources (Owner, Contributor, etc. on
    subscriptions, resource groups, and resources).

    Example:
        >>> auth = PIMAuth.azure_cli(tenant_id="...")
        >>> client = ARMClient(auth)
        >>> roles = client.list_eligible_roles(subscription_id="...")
    """

    BASE_URL = "https://management.azure.com"
    API_VERSION = "2022-04-01-preview"

    def __init__(self, auth: PIMAuth, timeout: float = 30.0) -> None:
        self.auth = auth
        self.timeout = timeout
        self._client: httpx.Client | None = None

    def _get_client(self) -> httpx.Client:
        """Get or create HTTP client with auth headers."""
        token = self.auth.get_arm_token()
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
    ) -> dict[str, Any]:
        """Make HTTP request to ARM API."""
        client = self._get_client()

        all_params = {"api-version": self.API_VERSION}
        if params:
            all_params.update(params)

        try:
            response = client.request(
                method,
                endpoint,
                json=json_data,
                params=all_params,
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
                    f"ARM API error: {error_msg}",
                    status_code=response.status_code,
                    response_body=body,
                )

            if response.status_code == 204 or not response.content:
                return {}

            return response.json()

        except httpx.HTTPError as e:
            raise APIError(f"HTTP request failed: {e}", status_code=0) from e

    def close(self) -> None:
        """Close HTTP client."""
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self) -> ARMClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    @staticmethod
    def _build_scope(
        subscription_id: str,
        resource_group: str | None = None,
        provider: str | None = None,
        resource_type: str | None = None,
        resource_name: str | None = None,
    ) -> str:
        """Build Azure resource scope string."""
        scope = f"/subscriptions/{subscription_id}"
        if resource_group:
            scope += f"/resourceGroups/{resource_group}"
        if provider and resource_type and resource_name:
            scope += f"/providers/{provider}/{resource_type}/{resource_name}"
        return scope

    # ==================== Role Definitions ====================

    def list_role_definitions(self, scope: str) -> list[dict[str, Any]]:
        """List role definitions at the specified scope."""
        encoded_scope = quote(scope, safe="")
        result = self._request(
            "GET",
            f"/{scope}/providers/Microsoft.Authorization/roleDefinitions",
        )
        return result.get("value", [])

    def get_role_definition(self, scope: str, role_id: str) -> dict[str, Any]:
        """Get a specific role definition."""
        return self._request(
            "GET",
            f"/{scope}/providers/Microsoft.Authorization/roleDefinitions/{role_id}",
        )

    def find_role_by_name(self, scope: str, role_name: str) -> dict[str, Any] | None:
        """Find role definition by display name (e.g., 'Owner', 'Contributor')."""
        result = self._request(
            "GET",
            f"/{scope}/providers/Microsoft.Authorization/roleDefinitions",
            params={"$filter": f"roleName eq '{role_name}'"},
        )
        roles = result.get("value", [])
        return roles[0] if roles else None

    # ==================== Eligible Role Assignments ====================

    def list_eligible_schedules(
        self,
        scope: str,
        principal_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """List eligible role assignment schedules."""
        params: dict[str, str] = {}
        if principal_id:
            params["$filter"] = f"principalId eq '{principal_id}'"

        result = self._request(
            "GET",
            f"/{scope}/providers/Microsoft.Authorization/roleEligibilitySchedules",
            params=params,
        )
        return result.get("value", [])

    def list_eligible_schedule_instances(
        self,
        scope: str,
        principal_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """List eligible schedule instances (active eligibilities)."""
        params: dict[str, str] = {}
        if principal_id:
            params["$filter"] = f"principalId eq '{principal_id}'"

        result = self._request(
            "GET",
            f"/{scope}/providers/Microsoft.Authorization/roleEligibilityScheduleInstances",
            params=params,
        )
        return result.get("value", [])

    def create_eligible_assignment(
        self,
        scope: str,
        principal_id: str,
        role_definition_id: str,
        request_id: str,
        justification: str = "",
        start_datetime: str | None = None,
        expiration_type: str = "NoExpiration",
        expiration_duration: str | None = None,
        expiration_datetime: str | None = None,
    ) -> dict[str, Any]:
        """Create an eligible role assignment.

        Args:
            scope: Azure scope (subscription, resource group, etc.)
            principal_id: User or service principal ID
            role_definition_id: Full role definition ID (include scope prefix)
            request_id: Unique GUID for the request
            justification: Reason for the assignment
            start_datetime: When eligibility starts (ISO 8601)
            expiration_type: "NoExpiration", "AfterDuration", "AfterDateTime"
            expiration_duration: Duration (e.g., "P365D" for 1 year)
            expiration_datetime: End date (ISO 8601)
        """
        schedule_info: dict[str, Any] = {}
        if start_datetime:
            schedule_info["startDateTime"] = start_datetime

        expiration: dict[str, str] = {"type": expiration_type}
        if expiration_duration:
            expiration["duration"] = expiration_duration
        if expiration_datetime:
            expiration["endDateTime"] = expiration_datetime
        schedule_info["expiration"] = expiration

        payload = {
            "properties": {
                "requestType": "AdminAssign",
                "principalId": principal_id,
                "roleDefinitionId": role_definition_id,
                "justification": justification,
                "scheduleInfo": schedule_info,
            },
        }

        return self._request(
            "PUT",
            f"/{scope}/providers/Microsoft.Authorization/roleEligibilityScheduleRequests/{request_id}",
            json_data=payload,
        )

    def remove_eligible_assignment(
        self,
        scope: str,
        principal_id: str,
        role_definition_id: str,
        request_id: str,
        justification: str = "",
    ) -> dict[str, Any]:
        """Remove an eligible role assignment."""
        payload = {
            "properties": {
                "requestType": "AdminRemove",
                "principalId": principal_id,
                "roleDefinitionId": role_definition_id,
                "justification": justification,
            },
        }

        return self._request(
            "PUT",
            f"/{scope}/providers/Microsoft.Authorization/roleEligibilityScheduleRequests/{request_id}",
            json_data=payload,
        )

    # ==================== Active Role Assignments ====================

    def list_active_schedules(
        self,
        scope: str,
        principal_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """List active role assignment schedules."""
        params: dict[str, str] = {}
        if principal_id:
            params["$filter"] = f"principalId eq '{principal_id}'"

        result = self._request(
            "GET",
            f"/{scope}/providers/Microsoft.Authorization/roleAssignmentSchedules",
            params=params,
        )
        return result.get("value", [])

    def list_active_schedule_instances(
        self,
        scope: str,
        principal_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """List active schedule instances (currently active assignments)."""
        params: dict[str, str] = {}
        if principal_id:
            params["$filter"] = f"principalId eq '{principal_id}'"

        result = self._request(
            "GET",
            f"/{scope}/providers/Microsoft.Authorization/roleAssignmentScheduleInstances",
            params=params,
        )
        return result.get("value", [])

    # ==================== Role Activation (JIT) ====================

    def activate_role(
        self,
        scope: str,
        role_definition_id: str,
        request_id: str,
        justification: str = "",
        duration: str = "PT1H",
        ticket_number: str | None = None,
        ticket_system: str | None = None,
    ) -> dict[str, Any]:
        """Activate an eligible Azure role (JIT activation).

        Args:
            scope: Azure scope (subscription, resource group, etc.)
            role_definition_id: Full role definition ID
            request_id: Unique GUID for the request
            justification: Reason for activation
            duration: How long to activate (ISO 8601)
            ticket_number: Optional ticket/incident number
            ticket_system: Optional ticket system name
        """
        schedule_info = {
            "expiration": {
                "type": "AfterDuration",
                "duration": duration,
            },
        }

        properties: dict[str, Any] = {
            "requestType": "SelfActivate",
            "roleDefinitionId": role_definition_id,
            "justification": justification,
            "scheduleInfo": schedule_info,
        }

        if ticket_number or ticket_system:
            properties["ticketInfo"] = {}
            if ticket_number:
                properties["ticketInfo"]["ticketNumber"] = ticket_number
            if ticket_system:
                properties["ticketInfo"]["ticketSystem"] = ticket_system

        payload = {"properties": properties}

        return self._request(
            "PUT",
            f"/{scope}/providers/Microsoft.Authorization/roleAssignmentScheduleRequests/{request_id}",
            json_data=payload,
        )

    def deactivate_role(
        self,
        scope: str,
        role_definition_id: str,
        request_id: str,
    ) -> dict[str, Any]:
        """Deactivate an active Azure role early."""
        payload = {
            "properties": {
                "requestType": "SelfDeactivate",
                "roleDefinitionId": role_definition_id,
            },
        }

        return self._request(
            "PUT",
            f"/{scope}/providers/Microsoft.Authorization/roleAssignmentScheduleRequests/{request_id}",
            json_data=payload,
        )

    # ==================== Request Status ====================

    def get_eligibility_request(self, scope: str, request_id: str) -> dict[str, Any]:
        """Get status of an eligibility schedule request."""
        return self._request(
            "GET",
            f"/{scope}/providers/Microsoft.Authorization/roleEligibilityScheduleRequests/{request_id}",
        )

    def get_assignment_request(self, scope: str, request_id: str) -> dict[str, Any]:
        """Get status of an assignment schedule request."""
        return self._request(
            "GET",
            f"/{scope}/providers/Microsoft.Authorization/roleAssignmentScheduleRequests/{request_id}",
        )

    def list_eligibility_requests(
        self,
        scope: str,
        filter_query: str | None = None,
    ) -> list[dict[str, Any]]:
        """List eligibility schedule requests."""
        params: dict[str, str] = {}
        if filter_query:
            params["$filter"] = filter_query

        result = self._request(
            "GET",
            f"/{scope}/providers/Microsoft.Authorization/roleEligibilityScheduleRequests",
            params=params,
        )
        return result.get("value", [])

    def list_assignment_requests(
        self,
        scope: str,
        filter_query: str | None = None,
    ) -> list[dict[str, Any]]:
        """List assignment schedule requests."""
        params: dict[str, str] = {}
        if filter_query:
            params["$filter"] = filter_query

        result = self._request(
            "GET",
            f"/{scope}/providers/Microsoft.Authorization/roleAssignmentScheduleRequests",
            params=params,
        )
        return result.get("value", [])

    # ==================== Role Management Policies ====================

    def get_role_management_policy(self, scope: str, policy_id: str) -> dict[str, Any]:
        """Get role management policy settings."""
        return self._request(
            "GET",
            f"/{scope}/providers/Microsoft.Authorization/roleManagementPolicies/{policy_id}",
        )

    def list_role_management_policies(self, scope: str) -> list[dict[str, Any]]:
        """List role management policies at scope."""
        result = self._request(
            "GET",
            f"/{scope}/providers/Microsoft.Authorization/roleManagementPolicies",
        )
        return result.get("value", [])

    def list_policy_assignments(self, scope: str) -> list[dict[str, Any]]:
        """List role management policy assignments."""
        result = self._request(
            "GET",
            f"/{scope}/providers/Microsoft.Authorization/roleManagementPolicyAssignments",
        )
        return result.get("value", [])
