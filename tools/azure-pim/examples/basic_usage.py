#!/usr/bin/env python3
"""Basic Azure PIM usage examples."""

import os
from azure_pim import PIMAuth
from azure_pim.operations import PIMOperations


def main() -> None:
    """Demonstrate basic PIM operations."""
    # Get tenant ID from environment
    tenant_id = os.environ.get("ARM_TENANT_ID")
    if not tenant_id:
        print("Set ARM_TENANT_ID environment variable")
        return

    # Authenticate using Azure CLI (run 'az login' first)
    auth = PIMAuth.azure_cli(tenant_id=tenant_id)

    with PIMOperations(auth) as pim:
        # Show current user
        user = pim.whoami()
        print(f"\n✓ Logged in as: {user.get('displayName')} ({user.get('userPrincipalName')})")

        # List eligible Entra ID roles
        print("\n📋 My Eligible Entra ID Roles:")
        eligible_roles = pim.list_my_eligible_entra_roles()
        for role in eligible_roles[:5]:
            print(f"  - {role.get('roleDefinitionId')} (Status: {role.get('status')})")

        if not eligible_roles:
            print("  (No eligible roles found)")

        # List active Entra ID roles
        print("\n🔥 My Active Entra ID Roles:")
        active_roles = pim.list_my_active_entra_roles()
        for role in active_roles[:5]:
            print(f"  - {role.get('roleDefinitionId')} (Action: {role.get('action')})")

        if not active_roles:
            print("  (No active roles)")

        # Show role definitions
        print("\n📖 Available Entra ID Roles (first 10):")
        all_roles = pim.list_entra_roles()
        for role in sorted(all_roles, key=lambda r: r.display_name)[:10]:
            print(f"  - {role.display_name}")


def activate_example() -> None:
    """Example: Activate a role."""
    tenant_id = os.environ.get("ARM_TENANT_ID")
    if not tenant_id:
        return

    auth = PIMAuth.azure_cli(tenant_id=tenant_id)

    with PIMOperations(auth) as pim:
        # Activate Global Administrator for 1 hour
        result = pim.activate_entra_role(
            role_name_or_id="Global Administrator",
            justification="Emergency access for incident INC-001",
            duration="PT1H",
            ticket_number="INC-001",
            ticket_system="ServiceNow",
        )

        status = result.get("status", "Unknown")
        print(f"Activation status: {status}")

        if status == "Provisioned":
            print("✓ Role activated successfully!")
        elif status == "PendingApproval":
            print("⏳ Waiting for approval...")


def deactivate_example() -> None:
    """Example: Deactivate a role."""
    tenant_id = os.environ.get("ARM_TENANT_ID")
    if not tenant_id:
        return

    auth = PIMAuth.azure_cli(tenant_id=tenant_id)

    with PIMOperations(auth) as pim:
        result = pim.deactivate_entra_role("Global Administrator")
        print("✓ Role deactivated")


if __name__ == "__main__":
    main()
