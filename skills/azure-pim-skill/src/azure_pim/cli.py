"""Command-line interface for Azure PIM operations.

Usage:
    pim --help
    pim roles list
    pim activate "Global Administrator" --justification "Emergency"
    pim deactivate "Global Administrator"
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime
from enum import Enum
from typing import Annotated, Any

import typer
from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table

from azure_pim.auth import PIMAuth
from azure_pim.config import PIMConfig
from azure_pim.exceptions import PIMError
from azure_pim.operations.pim import PIMOperations

# Initialize CLI app
app = typer.Typer(
    name="pim",
    help="Azure Privileged Identity Management (PIM) CLI",
    no_args_is_help=True,
)

# Sub-commands
entra_app = typer.Typer(help="Entra ID (Azure AD) role management")
azure_app = typer.Typer(help="Azure RBAC role management")
config_app = typer.Typer(help="Configuration management")

app.add_typer(entra_app, name="entra")
app.add_typer(azure_app, name="azure")
app.add_typer(config_app, name="config")

console = Console()


class OutputFormat(str, Enum):
    """Output format options."""

    TABLE = "table"
    JSON = "json"
    YAML = "yaml"


# ==================== Global Options ====================


def setup_logging(verbose: bool) -> None:
    """Configure logging based on verbosity."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s",
        handlers=[RichHandler(console=console, rich_tracebacks=True)],
    )


def get_auth(tenant_id: str | None = None) -> PIMAuth:
    """Get authentication from config or environment."""
    if tenant_id:
        config = PIMConfig(tenant_id=tenant_id)
    else:
        config = PIMConfig.from_env()
    return PIMAuth(config)


def output_result(data: Any, fmt: OutputFormat) -> None:
    """Output data in specified format."""
    if fmt == OutputFormat.JSON:
        if isinstance(data, list):
            console.print_json(json.dumps([_serialize(d) for d in data], default=str))
        else:
            console.print_json(json.dumps(_serialize(data), default=str))
    elif fmt == OutputFormat.YAML:
        import yaml

        console.print(yaml.safe_dump(_serialize(data), default_flow_style=False))
    else:
        if isinstance(data, list):
            _print_table(data)
        else:
            _print_dict(data)


def _serialize(obj: Any) -> Any:
    """Serialize object for output."""
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: _serialize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_serialize(v) for v in obj]
    return obj


def _print_table(data: list[dict[str, Any]]) -> None:
    """Print list of dicts as a table."""
    if not data:
        console.print("[yellow]No results found[/yellow]")
        return

    table = Table(show_header=True, header_style="bold cyan")

    keys = list(data[0].keys()) if data else []
    for key in keys[:6]:
        table.add_column(key)

    for row in data[:50]:
        values = [str(row.get(k, ""))[:50] for k in keys[:6]]
        table.add_row(*values)

    console.print(table)
    if len(data) > 50:
        console.print(f"[dim]... and {len(data) - 50} more[/dim]")


def _print_dict(data: dict[str, Any]) -> None:
    """Print dict as key-value pairs."""
    table = Table(show_header=False)
    table.add_column("Key", style="cyan")
    table.add_column("Value")

    for key, value in data.items():
        table.add_row(key, str(value)[:100])

    console.print(table)


# ==================== Main Commands ====================


@app.command()
def whoami(
    tenant_id: Annotated[str | None, typer.Option(help="Azure tenant ID")] = None,
    output: Annotated[OutputFormat, typer.Option("-o", "--output")] = OutputFormat.TABLE,
) -> None:
    """Show current authenticated user."""
    try:
        auth = get_auth(tenant_id)
        with PIMOperations(auth) as pim:
            user = pim.whoami()
            output_result(
                {
                    "id": user.get("id"),
                    "displayName": user.get("displayName"),
                    "userPrincipalName": user.get("userPrincipalName"),
                    "mail": user.get("mail"),
                },
                output,
            )
    except PIMError as e:
        console.print(f"[red]Error: {e.message}[/red]")
        raise typer.Exit(1) from e


@app.command("activate")
def activate_role(
    role: Annotated[str, typer.Argument(help="Role name or ID to activate")],
    justification: Annotated[str, typer.Option("-j", "--justification", help="Reason for activation")],
    duration: Annotated[str, typer.Option("-d", "--duration", help="Duration (ISO 8601)")] = "PT1H",
    scope: Annotated[str, typer.Option("-s", "--scope", help="Scope (/ for tenant, subscription ID for Azure)")] = "/",
    ticket: Annotated[str | None, typer.Option("--ticket", help="Ticket/incident number")] = None,
    ticket_system: Annotated[str | None, typer.Option("--ticket-system", help="Ticket system name")] = None,
    tenant_id: Annotated[str | None, typer.Option(help="Azure tenant ID")] = None,
    azure: Annotated[bool, typer.Option("--azure", help="Activate Azure RBAC role (not Entra)")] = False,
    output: Annotated[OutputFormat, typer.Option("-o", "--output")] = OutputFormat.TABLE,
) -> None:
    """Activate an eligible role (JIT activation)."""
    try:
        auth = get_auth(tenant_id)
        with PIMOperations(auth) as pim:
            if azure:
                result = pim.activate_azure_role(
                    scope=scope,
                    role_name_or_id=role,
                    justification=justification,
                    duration=duration,
                    ticket_number=ticket,
                    ticket_system=ticket_system,
                )
            else:
                result = pim.activate_entra_role(
                    role_name_or_id=role,
                    justification=justification,
                    duration=duration,
                    scope=scope,
                    ticket_number=ticket,
                    ticket_system=ticket_system,
                )

            status = result.get("status", result.get("properties", {}).get("status", "Unknown"))
            console.print(f"[green]Role activation requested. Status: {status}[/green]")
            output_result(result, output)

    except PIMError as e:
        console.print(f"[red]Activation failed: {e.message}[/red]")
        if e.details:
            console.print(f"[dim]{e.details}[/dim]")
        raise typer.Exit(1) from e


@app.command("deactivate")
def deactivate_role(
    role: Annotated[str, typer.Argument(help="Role name or ID to deactivate")],
    scope: Annotated[str, typer.Option("-s", "--scope", help="Scope")] = "/",
    tenant_id: Annotated[str | None, typer.Option(help="Azure tenant ID")] = None,
    azure: Annotated[bool, typer.Option("--azure", help="Deactivate Azure RBAC role")] = False,
) -> None:
    """Deactivate an active role early."""
    try:
        auth = get_auth(tenant_id)
        with PIMOperations(auth) as pim:
            if azure:
                result = pim.deactivate_azure_role(scope=scope, role_name_or_id=role)
            else:
                result = pim.deactivate_entra_role(role_name_or_id=role, scope=scope)

            console.print(f"[green]Role deactivated successfully[/green]")

    except PIMError as e:
        console.print(f"[red]Deactivation failed: {e.message}[/red]")
        raise typer.Exit(1) from e


# ==================== Entra ID Commands ====================


@entra_app.command("roles")
def list_entra_roles(
    tenant_id: Annotated[str | None, typer.Option(help="Azure tenant ID")] = None,
    output: Annotated[OutputFormat, typer.Option("-o", "--output")] = OutputFormat.TABLE,
) -> None:
    """List all Entra ID role definitions."""
    try:
        auth = get_auth(tenant_id)
        with PIMOperations(auth) as pim:
            roles = pim.list_entra_roles()
            data = [{"displayName": r.display_name, "id": r.id, "templateId": r.template_id} for r in roles]
            output_result(data, output)

    except PIMError as e:
        console.print(f"[red]Error: {e.message}[/red]")
        raise typer.Exit(1) from e


@entra_app.command("eligible")
def list_my_eligible_entra(
    tenant_id: Annotated[str | None, typer.Option(help="Azure tenant ID")] = None,
    output: Annotated[OutputFormat, typer.Option("-o", "--output")] = OutputFormat.TABLE,
) -> None:
    """List my eligible Entra ID roles."""
    try:
        auth = get_auth(tenant_id)
        with PIMOperations(auth) as pim:
            roles = pim.list_my_eligible_entra_roles()
            data = [
                {
                    "roleDefinitionId": r.get("roleDefinitionId"),
                    "status": r.get("status"),
                    "createdDateTime": r.get("createdDateTime"),
                }
                for r in roles
            ]
            output_result(data, output)

    except PIMError as e:
        console.print(f"[red]Error: {e.message}[/red]")
        raise typer.Exit(1) from e


@entra_app.command("active")
def list_my_active_entra(
    tenant_id: Annotated[str | None, typer.Option(help="Azure tenant ID")] = None,
    output: Annotated[OutputFormat, typer.Option("-o", "--output")] = OutputFormat.TABLE,
) -> None:
    """List my active Entra ID roles."""
    try:
        auth = get_auth(tenant_id)
        with PIMOperations(auth) as pim:
            roles = pim.list_my_active_entra_roles()
            data = [
                {
                    "roleDefinitionId": r.get("roleDefinitionId"),
                    "status": r.get("status"),
                    "action": r.get("action"),
                }
                for r in roles
            ]
            output_result(data, output)

    except PIMError as e:
        console.print(f"[red]Error: {e.message}[/red]")
        raise typer.Exit(1) from e


@entra_app.command("policy")
def get_entra_policy(
    role: Annotated[str, typer.Argument(help="Role name or ID")],
    tenant_id: Annotated[str | None, typer.Option(help="Azure tenant ID")] = None,
    output: Annotated[OutputFormat, typer.Option("-o", "--output")] = OutputFormat.TABLE,
) -> None:
    """Get policy settings for an Entra ID role."""
    try:
        auth = get_auth(tenant_id)
        with PIMOperations(auth) as pim:
            policy = pim.get_entra_role_policy(role)
            if policy:
                data = {
                    "id": policy.id,
                    "maxActivationDuration": policy.max_activation_duration,
                    "requiresMFA": policy.requires_mfa,
                    "requiresJustification": policy.requires_justification,
                    "requiresApproval": policy.requires_approval,
                }
                output_result(data, output)
            else:
                console.print("[yellow]No policy found for this role[/yellow]")

    except PIMError as e:
        console.print(f"[red]Error: {e.message}[/red]")
        raise typer.Exit(1) from e


@entra_app.command("assign")
def assign_entra_role(
    principal_id: Annotated[str, typer.Argument(help="User or service principal ID")],
    role: Annotated[str, typer.Argument(help="Role name or ID")],
    justification: Annotated[str, typer.Option("-j", "--justification")] = "",
    scope: Annotated[str, typer.Option("-s", "--scope")] = "/",
    duration: Annotated[str | None, typer.Option("-d", "--duration", help="Eligibility duration (e.g., P365D)")] = None,
    tenant_id: Annotated[str | None, typer.Option(help="Azure tenant ID")] = None,
) -> None:
    """Create an eligible role assignment."""
    try:
        auth = get_auth(tenant_id)
        with PIMOperations(auth) as pim:
            result = pim.assign_eligible_entra_role(
                principal_id=principal_id,
                role_name_or_id=role,
                justification=justification,
                scope=scope,
                expiration_type="afterDuration" if duration else "noExpiration",
                expiration_duration=duration,
            )
            console.print(f"[green]Eligible assignment created. ID: {result.get('id')}[/green]")

    except PIMError as e:
        console.print(f"[red]Assignment failed: {e.message}[/red]")
        raise typer.Exit(1) from e


@entra_app.command("remove")
def remove_entra_role(
    principal_id: Annotated[str, typer.Argument(help="User or service principal ID")],
    role: Annotated[str, typer.Argument(help="Role name or ID")],
    justification: Annotated[str, typer.Option("-j", "--justification")] = "",
    scope: Annotated[str, typer.Option("-s", "--scope")] = "/",
    tenant_id: Annotated[str | None, typer.Option(help="Azure tenant ID")] = None,
) -> None:
    """Remove an eligible role assignment."""
    try:
        auth = get_auth(tenant_id)
        with PIMOperations(auth) as pim:
            pim.remove_eligible_entra_role(
                principal_id=principal_id,
                role_name_or_id=role,
                justification=justification,
                scope=scope,
            )
            console.print(f"[green]Eligible assignment removed[/green]")

    except PIMError as e:
        console.print(f"[red]Removal failed: {e.message}[/red]")
        raise typer.Exit(1) from e


# ==================== Azure RBAC Commands ====================


@azure_app.command("roles")
def list_azure_roles(
    subscription: Annotated[str, typer.Argument(help="Azure subscription ID")],
    tenant_id: Annotated[str | None, typer.Option(help="Azure tenant ID")] = None,
    output: Annotated[OutputFormat, typer.Option("-o", "--output")] = OutputFormat.TABLE,
) -> None:
    """List Azure RBAC role definitions."""
    try:
        auth = get_auth(tenant_id)
        scope = f"/subscriptions/{subscription}"
        with PIMOperations(auth) as pim:
            roles = pim.list_azure_roles(scope)
            data = [
                {"roleName": r.role_name, "type": r.role_type, "id": r.name}
                for r in roles[:50]
            ]
            output_result(data, output)

    except PIMError as e:
        console.print(f"[red]Error: {e.message}[/red]")
        raise typer.Exit(1) from e


@azure_app.command("eligible")
def list_my_eligible_azure(
    subscription: Annotated[str, typer.Argument(help="Azure subscription ID")],
    resource_group: Annotated[str | None, typer.Option("--rg", help="Resource group name")] = None,
    tenant_id: Annotated[str | None, typer.Option(help="Azure tenant ID")] = None,
    output: Annotated[OutputFormat, typer.Option("-o", "--output")] = OutputFormat.TABLE,
) -> None:
    """List my eligible Azure RBAC roles."""
    try:
        auth = get_auth(tenant_id)
        scope = f"/subscriptions/{subscription}"
        if resource_group:
            scope += f"/resourceGroups/{resource_group}"

        with PIMOperations(auth) as pim:
            roles = pim.list_my_eligible_azure_roles(scope)
            data = [
                {
                    "roleDefinitionId": r.role_definition_id,
                    "scope": r.scope,
                    "principalType": r.principal_type,
                }
                for r in roles
            ]
            output_result(data, output)

    except PIMError as e:
        console.print(f"[red]Error: {e.message}[/red]")
        raise typer.Exit(1) from e


@azure_app.command("active")
def list_my_active_azure(
    subscription: Annotated[str, typer.Argument(help="Azure subscription ID")],
    resource_group: Annotated[str | None, typer.Option("--rg", help="Resource group name")] = None,
    tenant_id: Annotated[str | None, typer.Option(help="Azure tenant ID")] = None,
    output: Annotated[OutputFormat, typer.Option("-o", "--output")] = OutputFormat.TABLE,
) -> None:
    """List my active Azure RBAC roles."""
    try:
        auth = get_auth(tenant_id)
        scope = f"/subscriptions/{subscription}"
        if resource_group:
            scope += f"/resourceGroups/{resource_group}"

        with PIMOperations(auth) as pim:
            roles = pim.list_my_active_azure_roles(scope)
            data = [
                {
                    "roleDefinitionId": r.role_definition_id,
                    "scope": r.scope,
                    "status": r.status,
                }
                for r in roles
            ]
            output_result(data, output)

    except PIMError as e:
        console.print(f"[red]Error: {e.message}[/red]")
        raise typer.Exit(1) from e


# ==================== Audit Commands ====================


@app.command("audit")
def list_audit_events(
    top: Annotated[int, typer.Option("--top", "-n", help="Number of events")] = 50,
    tenant_id: Annotated[str | None, typer.Option(help="Azure tenant ID")] = None,
    output: Annotated[OutputFormat, typer.Option("-o", "--output")] = OutputFormat.TABLE,
) -> None:
    """List recent PIM audit events."""
    try:
        auth = get_auth(tenant_id)
        with PIMOperations(auth) as pim:
            events = pim.list_pim_audit_events(top=top)
            data = [
                {
                    "activityDisplayName": e.get("activityDisplayName"),
                    "activityDateTime": e.get("activityDateTime"),
                    "result": e.get("result"),
                }
                for e in events
            ]
            output_result(data, output)

    except PIMError as e:
        console.print(f"[red]Error: {e.message}[/red]")
        raise typer.Exit(1) from e


# ==================== Config Commands ====================


@config_app.command("show")
def show_config() -> None:
    """Show current configuration."""
    try:
        config = PIMConfig.from_env()
        console.print(f"Tenant ID: {config.tenant_id}")
        console.print(f"Client ID: {config.client_id or '(not set)'}")
        console.print(f"Default Duration: {config.default_duration}")
        console.print(f"Cache Path: {config.cache_path}")
    except ValueError as e:
        console.print(f"[yellow]Configuration incomplete: {e}[/yellow]")


@config_app.command("clear-cache")
def clear_cache() -> None:
    """Clear token cache."""
    try:
        config = PIMConfig.from_env()
        if config.cache_path.exists():
            config.cache_path.unlink()
            console.print("[green]Token cache cleared[/green]")
        else:
            console.print("[yellow]No cache file found[/yellow]")
    except Exception as e:
        console.print(f"[red]Error clearing cache: {e}[/red]")


# ==================== Version ====================


@app.callback()
def main(
    verbose: Annotated[bool, typer.Option("-v", "--verbose", help="Enable verbose output")] = False,
) -> None:
    """Azure PIM CLI - Manage privileged identity assignments."""
    setup_logging(verbose)


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        from azure_pim import __version__

        console.print(f"azure-pim version {__version__}")
        raise typer.Exit()


@app.command("version")
def version() -> None:
    """Show version information."""
    from azure_pim import __version__

    console.print(f"azure-pim version {__version__}")


if __name__ == "__main__":
    app()
