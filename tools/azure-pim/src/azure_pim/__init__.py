"""Azure Privileged Identity Management (PIM) automation toolkit.

This package provides a Python SDK and CLI for managing Azure PIM across:
- Microsoft Entra ID (Azure AD) roles via Microsoft Graph API
- Azure RBAC roles via Azure Resource Manager API

Key Features:
- JIT (Just-In-Time) role activation
- Eligible and active role assignment management
- Access reviews and compliance
- Audit logging and reporting
"""

from azure_pim.auth import PIMAuth
from azure_pim.clients.arm import ARMClient
from azure_pim.clients.graph import GraphClient
from azure_pim.config import PIMConfig
from azure_pim.exceptions import PIMError

__version__ = "0.1.0"

__all__ = [
    "PIMAuth",
    "PIMConfig",
    "PIMError",
    "GraphClient",
    "ARMClient",
]
