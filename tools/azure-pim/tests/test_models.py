"""Tests for PIM data models."""

import pytest
from datetime import datetime

from azure_pim.models.common import (
    ExpirationPattern,
    PIMAction,
    RequestSchedule,
    RequestStatus,
)
from azure_pim.models.entra import EntraRole, EntraRolePolicy
from azure_pim.models.azure_rbac import AzureScope


class TestExpirationPattern:
    """Tests for ExpirationPattern model."""

    def test_default_values(self) -> None:
        pattern = ExpirationPattern()
        assert pattern.type == "noExpiration"
        assert pattern.duration is None
        assert pattern.end_datetime is None

    def test_with_duration(self) -> None:
        pattern = ExpirationPattern(type="afterDuration", duration="PT8H")
        assert pattern.type == "afterDuration"
        assert pattern.duration == "PT8H"


class TestPIMAction:
    """Tests for PIMAction enum."""

    def test_action_values(self) -> None:
        assert PIMAction.SELF_ACTIVATE.value == "selfActivate"
        assert PIMAction.SELF_DEACTIVATE.value == "selfDeactivate"
        assert PIMAction.ADMIN_ASSIGN.value == "adminAssign"


class TestAzureScope:
    """Tests for AzureScope model."""

    def test_subscription_scope(self) -> None:
        scope = AzureScope.subscription("12345678-1234-1234-1234-123456789abc")
        assert scope.to_string() == "/subscriptions/12345678-1234-1234-1234-123456789abc"

    def test_resource_group_scope(self) -> None:
        scope = AzureScope.resource_group_scope(
            "12345678-1234-1234-1234-123456789abc",
            "my-rg",
        )
        expected = "/subscriptions/12345678-1234-1234-1234-123456789abc/resourceGroups/my-rg"
        assert scope.to_string() == expected

    def test_parse_scope_string(self) -> None:
        scope_str = "/subscriptions/12345678-1234-1234-1234-123456789abc/resourceGroups/my-rg"
        scope = AzureScope.from_string(scope_str)
        assert scope.subscription_id == "12345678-1234-1234-1234-123456789abc"
        assert scope.resource_group == "my-rg"

    def test_full_resource_scope(self) -> None:
        scope = AzureScope(
            subscription_id="sub-123",
            resource_group="rg-prod",
            provider="Microsoft.Compute",
            resource_type="virtualMachines",
            resource_name="vm-001",
        )
        expected = "/subscriptions/sub-123/resourceGroups/rg-prod/providers/Microsoft.Compute/virtualMachines/vm-001"
        assert scope.to_string() == expected


class TestEntraRole:
    """Tests for EntraRole model."""

    def test_role_from_api_response(self) -> None:
        data = {
            "id": "role-id-123",
            "displayName": "Global Administrator",
            "description": "Can manage all aspects of Azure AD",
            "templateId": "template-id-456",
            "isBuiltIn": True,
            "isEnabled": True,
        }
        role = EntraRole.model_validate(data)
        assert role.display_name == "Global Administrator"
        assert role.role_id == "template-id-456"

    def test_role_id_fallback(self) -> None:
        data = {
            "id": "role-id-123",
            "displayName": "Custom Role",
            "isBuiltIn": False,
        }
        role = EntraRole.model_validate(data)
        assert role.role_id == "role-id-123"


class TestEntraRolePolicy:
    """Tests for EntraRolePolicy model."""

    def test_policy_rules(self) -> None:
        data = {
            "id": "policy-123",
            "scopeId": "/",
            "scopeType": "DirectoryRole",
            "rules": [
                {
                    "@odata.type": "#microsoft.graph.unifiedRoleManagementPolicyExpirationRule",
                    "id": "Expiration_EndUser_Assignment",
                    "maximumDuration": "PT8H",
                },
                {
                    "@odata.type": "#microsoft.graph.unifiedRoleManagementPolicyEnablementRule",
                    "id": "Justification_EndUser_Assignment",
                    "isEnabled": True,
                },
            ],
        }
        policy = EntraRolePolicy.model_validate(data)
        assert policy.max_activation_duration == "PT8H"
        assert policy.requires_justification is True

    def test_get_rule(self) -> None:
        data = {
            "id": "policy-123",
            "scopeId": "/",
            "scopeType": "DirectoryRole",
            "rules": [
                {
                    "@odata.type": "#microsoft.graph.unifiedRoleManagementPolicyApprovalRule",
                    "id": "Approval_EndUser_Assignment",
                    "setting": {"isApprovalRequired": True},
                },
            ],
        }
        policy = EntraRolePolicy.model_validate(data)
        assert policy.requires_approval is True
