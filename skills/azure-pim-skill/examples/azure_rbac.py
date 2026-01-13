#!/usr/bin/env python3
"""Azure RBAC PIM examples."""

import os
from azure_pim import PIMAuth
from azure_pim.operations import PIMOperations
from azure_pim.models.azure_rbac import AzureScope


def main() -> None:
    """Demonstrate Azure RBAC PIM operations."""
    tenant_id = os.environ.get("ARM_TENANT_ID")
    subscription_id = os.environ.get("AZURE_SUBSCRIPTION_ID")

    if not tenant_id or not subscription_id:
        print("Set ARM_TENANT_ID and AZURE_SUBSCRIPTION_ID")
        return

    auth = PIMAuth.azure_cli(tenant_id=tenant_id)

    # Build scope
    scope = AzureScope.subscription(subscription_id)

    with PIMOperations(auth) as pim:
        # List Azure RBAC roles
        print(f"\n📋 Azure Roles at {scope.to_string()}:")
        roles = pim.list_azure_roles(scope)
        for role in roles[:10]:
            if role.role_type == "BuiltInRole":
                print(f"  - {role.role_name}")

        # List eligible roles
        print("\n🔑 My Eligible Azure Roles:")
        eligible = pim.list_my_eligible_azure_roles(scope)
        for assignment in eligible:
            print(f"  - {assignment.role_definition_id}")
            print(f"    Scope: {assignment.scope}")

        if not eligible:
            print("  (No eligible roles)")


def activate_azure_role() -> None:
    """Activate an Azure RBAC role."""
    tenant_id = os.environ.get("ARM_TENANT_ID")
    subscription_id = os.environ.get("AZURE_SUBSCRIPTION_ID")

    if not tenant_id or not subscription_id:
        return

    auth = PIMAuth.azure_cli(tenant_id=tenant_id)
    scope = f"/subscriptions/{subscription_id}"

    with PIMOperations(auth) as pim:
        result = pim.activate_azure_role(
            scope=scope,
            role_name_or_id="Contributor",
            justification="Deployment automation",
            duration="PT1H",
        )

        status = result.get("properties", {}).get("status", "Unknown")
        print(f"Activation status: {status}")


def resource_group_example() -> None:
    """Work with resource group scope."""
    tenant_id = os.environ.get("ARM_TENANT_ID")
    subscription_id = os.environ.get("AZURE_SUBSCRIPTION_ID")
    resource_group = os.environ.get("AZURE_RESOURCE_GROUP", "my-rg")

    if not tenant_id or not subscription_id:
        return

    auth = PIMAuth.azure_cli(tenant_id=tenant_id)

    # Scope to resource group
    scope = AzureScope.resource_group_scope(subscription_id, resource_group)
    print(f"Scope: {scope.to_string()}")

    with PIMOperations(auth) as pim:
        eligible = pim.list_my_eligible_azure_roles(scope)
        print(f"Eligible roles in {resource_group}: {len(eligible)}")


if __name__ == "__main__":
    main()
