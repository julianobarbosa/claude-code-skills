#!/usr/bin/env python3
"""VaultBuilder — CLI tool for creating and verifying Obsidian vaults."""

import json
import os
import platform
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

try:
    import click
except ImportError:
    print("Error: click is required. Install with: pip install click", file=sys.stderr)
    sys.exit(1)

BASE_FOLDERS = ["inbox", "daily", "projects", "archive"]

KEYWORD_FOLDER_MAP = {
    "pipeline": "runbooks",
    "infrastructure": "runbooks",
    "devops": "runbooks",
    "cloud": "runbooks",
    "deploy": "runbooks",
    "terraform": "runbooks",
    "kubernetes": "runbooks",
    "client": "clients",
    "customer": "clients",
    "account": "clients",
    "engagement": "clients",
    "research": "research",
    "evaluate": "research",
    "architecture": "research",
    "tool": "research",
    "compare": "research",
    "content": "content",
    "blog": "content",
    "video": "content",
    "podcast": "content",
    "newsletter": "content",
    "meeting": "meetings",
    "standup": "meetings",
    "retro": "meetings",
    "1-on-1": "meetings",
    "personal": "personal",
    "life": "personal",
    "health": "personal",
    "family": "personal",
    "finance": "personal",
    "notes": "notes",
    "class": "notes",
    "lecture": "notes",
    "course": "notes",
    "study": "notes",
    "decision": "decisions",
    "adr": "decisions",
    "tradeoff": "decisions",
    "people": "people",
    "team": "people",
    "reports": "people",
    "manager": "people",
    "operations": "operations",
    "sop": "operations",
    "procedure": "operations",
    "runbook": "operations",
    "sales": "sales",
    "deal": "sales",
    "crm": "sales",
}


def detect_folders(keywords_csv: str) -> list[str]:
    """Detect additional folders from comma-separated keywords."""
    keywords = [k.strip().lower() for k in keywords_csv.split(",")]
    detected = set()
    for kw in keywords:
        if kw in KEYWORD_FOLDER_MAP:
            detected.add(KEYWORD_FOLDER_MAP[kw])
    return sorted(detected)


def open_obsidian(vault_path: Path) -> None:
    """Open vault in Obsidian, cross-platform."""
    system = platform.system()
    uri = f"obsidian://open?path={vault_path.resolve()}"
    try:
        if system == "Darwin":
            subprocess.run(["open", "-a", "Obsidian", str(vault_path.resolve())], check=False)
        elif system == "Linux":
            subprocess.run(["xdg-open", uri], check=False)
        elif system == "Windows":
            os.startfile(uri)
        else:
            click.echo(f"  [--] Unknown platform '{system}' — open Obsidian manually")
    except Exception as e:
        click.echo(f"  [--] Could not open Obsidian: {e}")


@click.group()
def cli():
    """VaultBuilder — Create and verify Obsidian vaults."""
    pass


@cli.command()
@click.option("--role-keywords", required=True, help="Comma-separated keywords (e.g., 'devops,cloud,pipeline')")
@click.option("--scope", type=click.Choice(["work", "personal", "both"]), default="work", help="Vault scope")
@click.option("--vault-path", type=click.Path(), default=".", help="Path to create vault in")
@click.option("--role-description", default="", help="Free-text role description for CLAUDE.md")
@click.option("--open-obsidian/--no-open-obsidian", "should_open", default=True, help="Open vault in Obsidian after creation")
def create(role_keywords, scope, vault_path, role_description, should_open):
    """Create vault folders and CLAUDE.md based on keyword detection."""
    vault = Path(vault_path).resolve()

    # Detect additional folders
    extra_folders = detect_folders(role_keywords)
    if scope in ("personal", "both"):
        extra_folders = sorted(set(extra_folders) | {"personal"})

    all_folders = BASE_FOLDERS + [f for f in extra_folders if f not in BASE_FOLDERS]

    # Create folders
    click.echo("Creating vault structure:")
    for folder in all_folders:
        folder_path = vault / folder
        folder_path.mkdir(parents=True, exist_ok=True)
        click.echo(f"  [ok] {folder}/")

    # Write CLAUDE.md
    claude_md = vault / "CLAUDE.md"
    role_line = role_description if role_description else f"Knowledge worker ({', '.join(role_keywords.split(',')[:3])})"

    folder_tree = "\n".join(f"{f + '/':20s} — " for f in all_folders)

    content = f"""# CLAUDE.md — {role_line}'s Second Brain

## Who I Am
{role_description if role_description else f"I work with {role_keywords}. This vault is my second brain."}

## My Vault Structure
```
{chr(10).join(f'{f}/' for f in all_folders)}
```

## How I Work
- When I capture something, sort it fast — inbox should stay empty
- I prefer concise, actionable documentation

## Context Rules
When something lands in inbox/ → ask if I want it sorted now
"""

    claude_md.write_text(content)
    click.echo(f"  [ok] CLAUDE.md written")

    # Open Obsidian
    if should_open:
        open_obsidian(vault)
        click.echo(f"  [ok] Obsidian open requested")

    click.echo(f"\nVault created at {vault} with {len(all_folders)} folders.")


@cli.command()
@click.option("--vault-path", type=click.Path(exists=True), default=".", help="Path to vault")
def verify(vault_path):
    """Verify vault setup — check directories, CLAUDE.md, symlinks, global config."""
    vault = Path(vault_path).resolve()
    ok_count = 0
    issues = []

    click.echo("Verification:")

    # Check directories
    dirs_found = 0
    for item in vault.iterdir():
        if item.is_dir() and not item.name.startswith("."):
            dirs_found += 1
    if dirs_found > 0:
        click.echo(f"  [ok] {dirs_found} folders found")
        ok_count += 1
    else:
        click.echo(f"  [MISSING] No vault folders found")
        issues.append("No folders")

    # Check CLAUDE.md
    claude_md = vault / "CLAUDE.md"
    if claude_md.exists():
        lines = claude_md.read_text().splitlines()[:5]
        role = "vault"
        for line in lines:
            if line.startswith("# CLAUDE.md"):
                role = line.split("—")[-1].strip() if "—" in line else "vault"
                break
        click.echo(f"  [ok] CLAUDE.md written ({role})")
        ok_count += 1
    else:
        click.echo(f"  [MISSING] CLAUDE.md not found")
        issues.append("No CLAUDE.md")

    # Check companion skill symlinks
    for skill in ["daily-skill", "tldr-skill"]:
        link = vault / ".claude" / "skills" / skill
        if link.is_symlink():
            if link.resolve().exists():
                click.echo(f"  [ok] {skill} linked")
                ok_count += 1
            else:
                click.echo(f"  [BROKEN] {skill} symlink exists but target missing")
                issues.append(f"Broken {skill} symlink")
        else:
            click.echo(f"  [--] {skill} not linked (optional)")

    # Check global context
    global_claude = Path.home() / ".claude" / "CLAUDE.md"
    if global_claude.exists():
        content = global_claude.read_text()
        if str(vault) in content:
            click.echo(f"  [ok] Global context configured")
            ok_count += 1
        else:
            click.echo(f"  [--] Global context not configured")
    else:
        click.echo(f"  [--] ~/.claude/CLAUDE.md does not exist")

    # Check Obsidian running
    system = platform.system()
    try:
        if system == "Darwin":
            result = subprocess.run(["pgrep", "-x", "Obsidian"], capture_output=True)
        elif system == "Linux":
            result = subprocess.run(["pgrep", "-f", "obsidian"], capture_output=True)
        else:
            result = type("R", (), {"returncode": 1})()

        if result.returncode == 0:
            click.echo(f"  [ok] Obsidian running")
        else:
            click.echo(f"  [--] Obsidian not detected (open manually)")
    except Exception:
        click.echo(f"  [--] Could not check Obsidian status")


@cli.command("inject-global")
@click.option("--vault-path", required=True, type=click.Path(exists=True), help="Absolute path to vault")
def inject_global(vault_path):
    """Safe global context injection — idempotent, won't duplicate."""
    vault = Path(vault_path).resolve()
    global_claude = Path.home() / ".claude" / "CLAUDE.md"

    vault_line = f"At the start of every session, read {vault}/CLAUDE.md for context about who I am, my work, and my conventions."
    section_header = "## My Personal Context"

    if global_claude.exists():
        content = global_claude.read_text()

        # Already configured?
        if str(vault) in content:
            click.echo("Already configured — vault path found in ~/.claude/CLAUDE.md")
            return

        # Has section? Append under it
        if section_header in content:
            content = content.replace(section_header, f"{section_header}\n{vault_line}")
            global_claude.write_text(content)
            click.echo(f"Appended vault path under existing '{section_header}' section.")
        else:
            # Append section
            content = content.rstrip() + f"\n\n{section_header}\n{vault_line}\n"
            global_claude.write_text(content)
            click.echo(f"Added '{section_header}' section with vault path.")
    else:
        # Create file
        global_claude.parent.mkdir(parents=True, exist_ok=True)
        global_claude.write_text(f"{section_header}\n{vault_line}\n")
        click.echo(f"Created ~/.claude/CLAUDE.md with vault path.")


if __name__ == "__main__":
    cli()
