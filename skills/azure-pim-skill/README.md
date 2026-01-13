# Azure PIM

Enterprise-grade Azure Privileged Identity Management (PIM) automation toolkit.

Provides a Python SDK, CLI, and automation framework for managing privileged access lifecycle across:
- **Microsoft Entra ID (Azure AD) roles** - via Microsoft Graph API
- **Azure RBAC roles** - via Azure Resource Manager API

## Features

- **JIT (Just-In-Time) Activation** - Activate eligible roles on-demand with justification
- **Role Assignment Management** - Create/modify eligible and active role assignments
- **Policy Inspection** - View role settings (MFA, approval, max duration)
- **Audit Logging** - Query PIM-related audit events
- **Multiple Auth Methods** - Interactive, device code, client credentials, Azure CLI, managed identity

## Installation

```bash
# Using pip
pip install azure-pim

# Using uv (recommended)
uv add azure-pim

# Development install
git clone https://github.com/hypera/azure-pim
cd azure-pim
uv sync --dev
```

## Quick Start

### Authentication

```bash
# Set tenant ID (required)
export ARM_TENANT_ID="your-tenant-id"

# Option 1: Use Azure CLI auth (recommended for interactive use)
az login

# Option 2: Service principal auth
export AZURE_CLIENT_ID="your-client-id"
export AZURE_CLIENT_SECRET="your-client-secret"
```

### CLI Usage

```bash
# Show current user
pim whoami

# List your eligible Entra ID roles
pim entra eligible

# Activate a role
pim activate "Global Administrator" -j "Emergency access for incident INC-123" -d PT1H

# Deactivate a role
pim deactivate "Global Administrator"

# List Azure RBAC roles
pim azure roles <subscription-id>

# Activate Azure role
pim activate "Owner" --azure -s "/subscriptions/<sub-id>" -j "Deployment"
```

### Python SDK

```python
from azure_pim import PIMAuth
from azure_pim.operations import PIMOperations

# Authenticate
auth = PIMAuth.azure_cli(tenant_id="your-tenant-id")

# Use high-level operations
with PIMOperations(auth) as pim:
    # Get current user
    user = pim.whoami()
    print(f"Logged in as: {user['displayName']}")

    # List eligible Entra ID roles
    eligible = pim.list_my_eligible_entra_roles()
    for role in eligible:
        print(f"  - {role['roleDefinitionId']}")

    # Activate a role
    result = pim.activate_entra_role(
        role_name_or_id="Global Administrator",
        justification="Emergency access",
        duration="PT1H",
    )
    print(f"Activation status: {result['status']}")

    # Deactivate when done
    pim.deactivate_entra_role("Global Administrator")
```

### Low-Level Client Access

```python
from azure_pim import PIMAuth, GraphClient, ARMClient

auth = PIMAuth.azure_cli(tenant_id="...")

# Microsoft Graph for Entra ID roles
with GraphClient(auth) as graph:
    roles = graph.list_role_definitions()
    eligible = graph.list_my_eligible_roles()

    # Activate role
    graph.activate_role(
        role_definition_id="62e90394-69f5-4237-9190-012177145e10",
        justification="Emergency",
        duration="PT1H",
    )

# ARM for Azure RBAC roles
with ARMClient(auth) as arm:
    scope = "/subscriptions/your-subscription-id"
    roles = arm.list_role_definitions(scope)
    eligible = arm.list_eligible_schedule_instances(scope)
```

## CLI Reference

### Global Commands

| Command | Description |
|---------|-------------|
| `pim whoami` | Show current authenticated user |
| `pim activate <role>` | Activate an eligible role (JIT) |
| `pim deactivate <role>` | Deactivate an active role early |
| `pim audit` | List recent PIM audit events |
| `pim version` | Show version information |

### Entra ID Commands (`pim entra`)

| Command | Description |
|---------|-------------|
| `pim entra roles` | List all Entra ID role definitions |
| `pim entra eligible` | List my eligible roles |
| `pim entra active` | List my active roles |
| `pim entra policy <role>` | Get policy settings for a role |
| `pim entra assign <user> <role>` | Create eligible assignment |
| `pim entra remove <user> <role>` | Remove eligible assignment |

### Azure RBAC Commands (`pim azure`)

| Command | Description |
|---------|-------------|
| `pim azure roles <subscription>` | List Azure role definitions |
| `pim azure eligible <subscription>` | List my eligible roles |
| `pim azure active <subscription>` | List my active roles |

### Common Options

| Option | Description |
|--------|-------------|
| `-j, --justification` | Reason for the request |
| `-d, --duration` | Duration (ISO 8601, e.g., PT1H, PT8H) |
| `-s, --scope` | Scope (/ for tenant, subscription ID for Azure) |
| `--ticket` | Ticket/incident number |
| `--ticket-system` | Ticket system name (e.g., ServiceNow) |
| `-o, --output` | Output format: table, json, yaml |
| `-v, --verbose` | Enable verbose logging |

## Authentication Methods

### Interactive Browser (Default)

```python
auth = PIMAuth.interactive(tenant_id="...")
```

### Device Code (Headless)

```python
auth = PIMAuth.device_code(tenant_id="...", callback=print)
```

### Client Credentials (App-Only)

```python
auth = PIMAuth.client_credentials(
    tenant_id="...",
    client_id="...",
    client_secret="...",
)
```

### Azure CLI

```python
auth = PIMAuth.azure_cli(tenant_id="...")
```

### Managed Identity

```python
auth = PIMAuth.managed_identity(tenant_id="...", client_id="...")
```

## Required Permissions

### For Entra ID Roles (Microsoft Graph)

| Permission | Type | Description |
|------------|------|-------------|
| `RoleManagement.ReadWrite.Directory` | Delegated | Manage role assignments |
| `RoleEligibilitySchedule.ReadWrite.Directory` | Delegated | Manage eligible assignments |
| `RoleAssignmentSchedule.ReadWrite.Directory` | Delegated | Manage active assignments |
| `AuditLog.Read.All` | Delegated | Read audit logs |

### For Azure RBAC Roles (ARM)

- **Owner** or **User Access Administrator** role on the target scope
- No special Microsoft Graph permissions needed

## Error Handling

```python
from azure_pim.exceptions import (
    PIMError,
    AuthenticationError,
    RoleNotFoundError,
    ActivationError,
    ApprovalRequiredError,
    MFARequiredError,
    RateLimitError,
)

try:
    pim.activate_entra_role("Global Administrator", "Reason")
except MFARequiredError:
    print("MFA challenge required - re-authenticate")
except ApprovalRequiredError:
    print("Activation requires approval")
except RateLimitError as e:
    print(f"Rate limited, retry in {e.details['status_code']} seconds")
except PIMError as e:
    print(f"PIM error: {e.message}")
```

## Development

```bash
# Install dev dependencies
uv sync --dev

# Run tests
pytest

# Run linting
ruff check src tests
mypy src

# Format code
ruff format src tests
```

## API Reference

### Microsoft Graph PIM API (Entra ID)

- [PIM API Overview](https://learn.microsoft.com/en-us/graph/api/resources/privilegedidentitymanagementv3-overview)
- [Role Assignment Requests](https://learn.microsoft.com/en-us/graph/api/resources/unifiedroleassignmentschedulerequest)
- [Role Eligibility Requests](https://learn.microsoft.com/en-us/graph/api/resources/unifiedroleeligibilityschedulerequest)
- [Access Reviews](https://learn.microsoft.com/en-us/graph/tutorial-accessreviews-roleassignments)

### ARM PIM API (Azure RBAC)

- [Role Assignment Schedule Requests](https://learn.microsoft.com/en-us/azure/templates/microsoft.authorization/roleassignmentschedulerequests)
- [Role Eligibility Schedule Requests](https://learn.microsoft.com/en-us/azure/templates/microsoft.authorization/roleeligibilityschedulerequests)

## License

MIT
