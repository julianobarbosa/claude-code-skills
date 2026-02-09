#!/usr/bin/env python3
"""BaseBuilder - Generate Obsidian .base files programmatically.

Commands:
  create    - Build a .base file from parameters
  validate  - Validate existing .base YAML
  preview   - Dry-run showing generated YAML

Environment:
  OBSIDIAN_VAULT - Vault path (default: auto-detect from cwd)
"""
from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

try:
    import click
except ImportError:
    print("Missing dependency: pip install click", file=sys.stderr)
    sys.exit(1)

try:
    import yaml
except ImportError:
    yaml = None

# ---------------------------------------------------------------------------
# Vault detection
# ---------------------------------------------------------------------------


def _detect_vault(vault_arg: str | None = None) -> Path:
    if vault_arg:
        return Path(vault_arg)
    env = os.getenv("OBSIDIAN_VAULT")
    if env:
        return Path(env)
    cwd = Path.cwd()
    if (cwd / ".obsidian").is_dir():
        return cwd
    for parent in cwd.parents:
        if (parent / ".obsidian").is_dir():
            return parent
    return cwd


# ---------------------------------------------------------------------------
# YAML generation (manual to avoid pyyaml formatting issues with quoted strings)
# ---------------------------------------------------------------------------


def _build_base_yaml(
    name: str,
    filter_expr: str | None,
    view_type: str,
    columns: list[str],
    formulas: dict[str, str] | None = None,
    group_by: str | None = None,
    sort_dir: str = "ASC",
    limit: int | None = None,
    summaries: dict[str, str] | None = None,
) -> str:
    lines = []

    # Global filters
    if filter_expr:
        filters = _parse_filter_expr(filter_expr)
        lines.append("filters:")
        lines.append("  and:")
        for f in filters:
            lines.append(f"    - '{f}'")
        lines.append("")

    # Formulas
    if formulas:
        lines.append("formulas:")
        for fname, fexpr in formulas.items():
            lines.append(f"  {fname}: '{fexpr}'")
        lines.append("")

    # Properties display names for formulas
    if formulas:
        lines.append("properties:")
        for fname in formulas:
            display = fname.replace("_", " ").title()
            lines.append(f"  formula.{fname}:")
            lines.append(f'    displayName: "{display}"')
        lines.append("")

    # Views
    lines.append("views:")
    lines.append(f"  - type: {view_type}")
    lines.append(f'    name: "{name}"')

    if limit:
        lines.append(f"    limit: {limit}")

    if group_by:
        lines.append("    groupBy:")
        lines.append(f"      property: {group_by}")
        lines.append(f"      direction: {sort_dir}")

    lines.append("    order:")
    for col in columns:
        lines.append(f"      - {col}")

    if summaries:
        lines.append("    summaries:")
        for prop, summary_type in summaries.items():
            lines.append(f"      {prop}: {summary_type}")

    return "\n".join(lines) + "\n"


def _parse_filter_expr(expr: str) -> list[str]:
    """Split a filter expression by && into individual filter strings."""
    parts = re.split(r"\s*&&\s*", expr)
    return [p.strip() for p in parts if p.strip()]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


@click.group()
def cli():
    """Generate Obsidian .base files."""


@cli.command()
@click.option("--name", required=True, help="View name")
@click.option("--filter", "filter_expr", help="Filter expression (use && for AND)")
@click.option("--view", "view_type", type=click.Choice(["table", "cards", "list", "map"]), default="table")
@click.option("--columns", required=True, help="Comma-separated column list")
@click.option("--formula", "formula_list", multiple=True, help="name=expression (repeatable)")
@click.option("--group-by", help="Property to group by")
@click.option("--sort", "sort_dir", type=click.Choice(["ASC", "DESC"]), default="ASC")
@click.option("--limit", type=int, help="Max results")
@click.option("--summary", "summary_list", multiple=True, help="property=SummaryType (repeatable)")
@click.option("--output", help="Output .base file path")
@click.option("--vault", help="Vault path")
def create(name, filter_expr, view_type, columns, formula_list, group_by, sort_dir, limit, summary_list, output, vault):
    """Create a .base file from parameters."""
    col_list = [c.strip() for c in columns.split(",")]

    formulas = {}
    for f in formula_list:
        if "=" not in f:
            raise click.ClickException(f"Formula must be name=expression: {f}")
        fname, fexpr = f.split("=", 1)
        formulas[fname.strip()] = fexpr.strip()

    summaries = {}
    for s in summary_list:
        if "=" not in s:
            raise click.ClickException(f"Summary must be property=Type: {s}")
        prop, stype = s.split("=", 1)
        summaries[prop.strip()] = stype.strip()

    base_yaml = _build_base_yaml(
        name=name,
        filter_expr=filter_expr,
        view_type=view_type,
        columns=col_list,
        formulas=formulas or None,
        group_by=group_by,
        sort_dir=sort_dir,
        limit=limit,
        summaries=summaries or None,
    )

    if output:
        v = _detect_vault(vault)
        dest = v / output if not Path(output).is_absolute() else Path(output)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(base_yaml, encoding="utf-8")
        click.echo(f"Created: {dest}")
    else:
        click.echo(base_yaml)


@cli.command()
@click.option("--path", required=True, help="Path to .base file")
@click.option("--vault", help="Vault path")
def validate(path, vault):
    """Validate existing .base YAML."""
    if yaml is None:
        raise click.ClickException("pyyaml required for validation. Run: pip install pyyaml")

    v = _detect_vault(vault)
    base_path = v / path if not Path(path).is_absolute() else Path(path)
    if not base_path.exists():
        raise click.ClickException(f"File not found: {base_path}")

    text = base_path.read_text(encoding="utf-8")
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as e:
        raise click.ClickException(f"Invalid YAML: {e}")

    if not isinstance(data, dict):
        raise click.ClickException("Root must be a YAML mapping")

    errors = []
    warnings = []

    # Check views
    views = data.get("views", [])
    if not views:
        errors.append("No views defined")
    for i, view in enumerate(views):
        if not isinstance(view, dict):
            errors.append(f"View {i} is not a mapping")
            continue
        vtype = view.get("type")
        if vtype not in ("table", "cards", "list", "map"):
            errors.append(f"View {i}: invalid type '{vtype}'")
        if not view.get("name"):
            warnings.append(f"View {i}: no name specified")
        if not view.get("order"):
            warnings.append(f"View {i}: no order (columns) specified")

    # Check formulas reference valid syntax
    formulas = data.get("formulas", {})
    if formulas and not isinstance(formulas, dict):
        errors.append("formulas must be a mapping")

    # Check filters
    filters = data.get("filters")
    if filters and not isinstance(filters, (str, dict)):
        errors.append("filters must be a string or mapping with and/or/not")

    if errors:
        click.echo("INVALID")
        for e in errors:
            click.echo(f"  ERROR: {e}")
        for w in warnings:
            click.echo(f"  WARN: {w}")
        sys.exit(1)
    else:
        click.echo("VALID")
        for w in warnings:
            click.echo(f"  WARN: {w}")
        click.echo(f"  Views: {len(views)}")
        click.echo(f"  Formulas: {len(formulas)}")


@cli.command()
@click.option("--filter", "filter_expr", help="Filter expression")
@click.option("--view", "view_type", type=click.Choice(["table", "cards", "list", "map"]), default="table")
@click.option("--columns", required=True, help="Comma-separated column list")
@click.option("--formula", "formula_list", multiple=True, help="name=expression (repeatable)")
def preview(filter_expr, view_type, columns, formula_list):
    """Preview generated YAML (dry run)."""
    col_list = [c.strip() for c in columns.split(",")]
    formulas = {}
    for f in formula_list:
        if "=" in f:
            fname, fexpr = f.split("=", 1)
            formulas[fname.strip()] = fexpr.strip()

    base_yaml = _build_base_yaml(
        name="Preview",
        filter_expr=filter_expr,
        view_type=view_type,
        columns=col_list,
        formulas=formulas or None,
    )
    click.echo(base_yaml)


if __name__ == "__main__":
    cli()
