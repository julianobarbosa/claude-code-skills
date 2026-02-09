#!/usr/bin/env python3
"""NoteCreator - Create notes with templates, frontmatter, and wikilinks.

Commands:
  create   - Create a new note with template and PARA placement
  daily    - Create or append to daily note
  capture  - Capture knowledge from conversation into vault

Environment:
  OBSIDIAN_VAULT - Vault path (default: auto-detect from cwd)
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

try:
    import click
except ImportError:
    print("Missing dependency: pip install click", file=sys.stderr)
    sys.exit(1)

# ---------------------------------------------------------------------------
# Constants & vault detection
# ---------------------------------------------------------------------------

PARA_FOLDERS = {
    "inbox": "00 - Inbox",
    "moc": "00 - Maps of Content",
    "projects": "01 - Projects",
    "areas": "02 - Areas",
    "resources": "03 - Resources",
    "archive": "04 - Archive",
    "permanent": "04 - Permanent",
    "daily": "06 - Daily",
    "books": "08 - books",
    "meetings": "10 - 1-1",
}

CAPTURE_DESTINATIONS = {
    "concept": "permanent",
    "adr": "resources",
    "howto": "resources",
    "meeting": "meetings",
    "moc": "moc",
    "project": "projects",
    "daily": "daily",
    "generic": "inbox",
}

WIKILINK_RE = re.compile(r"\[\[([^\]|#]+?)(?:#[^\]|]*)?(?:\|[^\]]+)?\]\]")


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


def _now_str() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M")


def _today() -> datetime:
    return datetime.now()


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------


def _template_generic(title: str, tags: list[str]) -> str:
    tag_yaml = "\n".join(f"  - {t}" for t in tags) if tags else "  - inbox"
    return f"""---
created: {_now_str()}
updated: {_now_str()}
tags:
{tag_yaml}
---

# {title}

"""


def _template_concept(title: str, tags: list[str]) -> str:
    tag_yaml = "\n".join(f"  - {t}" for t in ["permanent", "concept"] + tags)
    return f"""---
created: {_now_str()}
updated: {_now_str()}
type: zettelkasten
tags:
{tag_yaml}
---

# {title}

## Definition
One-paragraph explanation in your own words.

## Key Insight
**Core idea**:

## How It Works


## Examples
-

## Connections
-

## Sources
-
"""


def _template_adr(title: str, tags: list[str]) -> str:
    tag_yaml = "\n".join(f"  - {t}" for t in ["decision"] + tags)
    return f"""---
created: {_now_str()}
updated: {_now_str()}
type: adr
status: accepted
tags:
{tag_yaml}
---

# ADR: {title}

## Status
Accepted

## Context
What is the issue we're deciding on?

## Decision
What is the change that we're proposing?

## Consequences

### Positive
-

### Negative
-

## Related
-
"""


def _template_howto(title: str, tags: list[str]) -> str:
    tag_yaml = "\n".join(f"  - {t}" for t in ["howto"] + tags)
    return f"""---
created: {_now_str()}
updated: {_now_str()}
type: howto
tags:
{tag_yaml}
---

# How To: {title}

## Prerequisites
-

## Steps

### 1. First Step


### 2. Second Step


### 3. Third Step


## Verification
How to confirm it worked.

## Troubleshooting
Common issues and fixes.

## Related
-
"""


def _template_meeting(title: str, tags: list[str]) -> str:
    tag_yaml = "\n".join(f"  - {t}" for t in ["meeting"] + tags)
    date = _today().strftime("%Y-%m-%d")
    return f"""---
created: {_now_str()}
updated: {_now_str()}
type: meeting
attendees: []
tags:
{tag_yaml}
---

# Meeting: {title} - {date}

## Attendees
-

## Agenda
1.

## Notes


## Decisions
-

## Action Items
- [ ]

## Follow-up
"""


def _template_project(title: str, tags: list[str]) -> str:
    tag_yaml = "\n".join(f"  - {t}" for t in [f"project/{title.lower().replace(' ', '-')}"] + tags)
    return f"""---
created: {_now_str()}
updated: {_now_str()}
type: project
status: active
priority: medium
tags:
{tag_yaml}
---

# {title}

## Overview


## Goals
-

## Tasks
- [ ]

## Notes


## Related
-
"""


def _template_moc(title: str, tags: list[str]) -> str:
    tag_yaml = "\n".join(f"  - {t}" for t in ["moc"] + tags)
    return f"""---
created: {_now_str()}
updated: {_now_str()}
type: moc
tags:
{tag_yaml}
---

# {title} MOC

## Overview


## Core Concepts
-

## How-Tos
-

## Decisions
-

## Projects
-

## Resources
-
"""


def _template_daily(dt: datetime) -> str:
    date_str = dt.strftime("%Y-%m-%d")
    title = dt.strftime("%Y%m%d")
    year = dt.strftime("%Y")
    month = dt.strftime("%Y-%m")
    prev_dt = dt - timedelta(days=1)
    next_dt = dt + timedelta(days=1)
    prev = prev_dt.strftime("%Y%m%d")
    nxt = next_dt.strftime("%Y%m%d")
    return f"""---
created: {dt.strftime("%Y-%m-%dT%H:%M")}
updated: {dt.strftime("%Y-%m-%dT%H:%M")}
title: "{title}"
type: daily-note
status: true
tags:
  - daily
  - {year}
  - {month}
date_formatted: {date_str}
---

# Daily Note - {date_str}

### Tasks
- [ ]

### Journal


### Navigation
<< [[{prev}]] | **Today** | [[{nxt}]] >>
"""


TEMPLATES = {
    "generic": _template_generic,
    "concept": _template_concept,
    "adr": _template_adr,
    "howto": _template_howto,
    "meeting": _template_meeting,
    "project": _template_project,
    "moc": _template_moc,
}


# ---------------------------------------------------------------------------
# Wikilink scanning
# ---------------------------------------------------------------------------


def _scan_related(vault: Path, title: str, content: str) -> list[str]:
    """Find existing notes that could be linked."""
    words = set(title.lower().split())
    related = []
    for md in vault.rglob("*.md"):
        rel = str(md.relative_to(vault))
        if rel.startswith(".obsidian"):
            continue
        name = md.stem.lower()
        if any(w in name for w in words if len(w) > 3):
            related.append(md.stem)
    return related[:10]


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


@click.group()
def cli():
    """Create Obsidian notes with templates and proper organization."""


@cli.command()
@click.option("--title", required=True, help="Note title")
@click.option("--template", "tmpl", type=click.Choice(list(TEMPLATES.keys())), default="generic")
@click.option("--folder", type=click.Choice(list(PARA_FOLDERS.keys())), default="inbox")
@click.option("--tags", help="Comma-separated tags")
@click.option("--content", help="Additional body content")
@click.option("--vault", help="Vault path")
@click.option("--dry-run", is_flag=True, help="Preview without creating")
def create(title, tmpl, folder, tags, content, vault, dry_run):
    """Create a new note with template and PARA placement."""
    v = _detect_vault(vault)
    tag_list = [t.strip() for t in tags.split(",")] if tags else []
    template_fn = TEMPLATES[tmpl]
    note_content = template_fn(title, tag_list)

    if content:
        note_content += f"\n{content}\n"

    dest_dir = v / PARA_FOLDERS[folder]
    if tmpl == "adr":
        dest_dir = dest_dir / "decisions"
    elif tmpl == "howto":
        dest_dir = dest_dir / "howtos"

    filename = f"{title}.md"
    dest = dest_dir / filename

    if dry_run:
        click.echo(f"Would create: {dest.relative_to(v)}")
        click.echo("---")
        click.echo(note_content)
        return

    dest_dir.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        raise click.ClickException(f"Note already exists: {dest.relative_to(v)}")

    dest.write_text(note_content, encoding="utf-8")
    click.echo(f"Created: {dest.relative_to(v)}")

    related = _scan_related(v, title, note_content)
    if related:
        click.echo(f"Related notes: {', '.join(f'[[{r}]]' for r in related)}")


@cli.command()
@click.option("--date", "date_str", help="Date (YYYY-MM-DD), default today")
@click.option("--content", help="Initial content")
@click.option("--append", "append_text", help="Append to existing daily note")
@click.option("--vault", help="Vault path")
@click.option("--dry-run", is_flag=True)
def daily(date_str, content, append_text, vault, dry_run):
    """Create or append to daily note."""
    v = _detect_vault(vault)
    dt = datetime.strptime(date_str, "%Y-%m-%d") if date_str else _today()
    year = dt.strftime("%Y")
    month = dt.strftime("%m")
    filename = dt.strftime("%Y%m%d.md")
    dest_dir = v / "06 - Daily" / year / month
    dest = dest_dir / filename

    if append_text and dest.exists():
        existing = dest.read_text(encoding="utf-8")
        now = _now_str()
        existing = re.sub(r"^updated:.*$", f"updated: {now}", existing, count=1, flags=re.MULTILINE)
        new_content = f"{existing.rstrip()}\n\n{append_text}\n"
        if dry_run:
            click.echo(f"Would append to: {dest.relative_to(v)}")
            click.echo(f"Content: {append_text}")
            return
        dest.write_text(new_content, encoding="utf-8")
        click.echo(f"Appended to: {dest.relative_to(v)}")
        return

    if dest.exists() and not append_text:
        click.echo(f"Daily note exists: {dest.relative_to(v)}")
        return

    note_content = _template_daily(dt)
    if content:
        note_content = note_content.replace("### Journal\n", f"### Journal\n{content}\n")

    if dry_run:
        click.echo(f"Would create: {dest.relative_to(v)}")
        click.echo("---")
        click.echo(note_content)
        return

    dest_dir.mkdir(parents=True, exist_ok=True)
    dest.write_text(note_content, encoding="utf-8")
    click.echo(f"Created: {dest.relative_to(v)}")


@cli.command()
@click.option("--type", "capture_type", type=click.Choice(list(CAPTURE_DESTINATIONS.keys())), required=True)
@click.option("--title", help="Note title (required for non-daily)")
@click.option("--content", required=True, help="Content to capture")
@click.option("--tags", help="Comma-separated tags")
@click.option("--vault", help="Vault path")
@click.option("--dry-run", is_flag=True)
def capture(capture_type, title, content, tags, vault, dry_run):
    """Capture knowledge from conversation into vault."""
    v = _detect_vault(vault)

    if capture_type == "daily":
        # Append to today's daily note
        dt = _today()
        year = dt.strftime("%Y")
        month = dt.strftime("%m")
        filename = dt.strftime("%Y%m%d.md")
        dest = v / "06 - Daily" / year / month / filename
        if dest.exists():
            existing = dest.read_text(encoding="utf-8")
            now = _now_str()
            existing = re.sub(r"^updated:.*$", f"updated: {now}", existing, count=1, flags=re.MULTILINE)
            new_content = f"{existing.rstrip()}\n\n{content}\n"
            if dry_run:
                click.echo(f"Would append to daily: {dest.relative_to(v)}")
                return
            dest.write_text(new_content, encoding="utf-8")
            click.echo(f"Appended to daily: {dest.relative_to(v)}")
        else:
            note = _template_daily(dt)
            note = note.replace("### Journal\n", f"### Journal\n{content}\n")
            if dry_run:
                click.echo(f"Would create daily with content: {dest.relative_to(v)}")
                return
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(note, encoding="utf-8")
            click.echo(f"Created daily with content: {dest.relative_to(v)}")
        return

    if not title:
        raise click.ClickException("--title required for non-daily captures")

    folder = CAPTURE_DESTINATIONS[capture_type]
    tag_list = [t.strip() for t in tags.split(",")] if tags else []

    if capture_type in TEMPLATES:
        template_fn = TEMPLATES[capture_type]
        note_content = template_fn(title, tag_list)
        # Inject content into appropriate section
        if capture_type == "concept":
            note_content = note_content.replace(
                "One-paragraph explanation in your own words.",
                content,
            )
        elif capture_type == "adr":
            note_content = note_content.replace(
                "What is the issue we're deciding on?",
                content,
            )
        elif capture_type == "howto":
            note_content = note_content.replace(
                "### 1. First Step\n",
                f"### 1. First Step\n{content}\n",
            )
        else:
            note_content += f"\n{content}\n"
    else:
        note_content = _template_generic(title, tag_list)
        note_content += f"\n{content}\n"

    dest_dir = v / PARA_FOLDERS[folder]
    if capture_type == "adr":
        dest_dir = dest_dir / "decisions"
    elif capture_type == "howto":
        dest_dir = dest_dir / "howtos"

    dest = dest_dir / f"{title}.md"

    if dry_run:
        click.echo(f"Would create: {dest.relative_to(v)}")
        click.echo("---")
        click.echo(note_content)
        return

    dest_dir.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        raise click.ClickException(f"Note already exists: {dest.relative_to(v)}")
    dest.write_text(note_content, encoding="utf-8")
    click.echo(f"Captured: {dest.relative_to(v)}")

    related = _scan_related(v, title, note_content)
    if related:
        click.echo(f"Related notes: {', '.join(f'[[{r}]]' for r in related)}")


if __name__ == "__main__":
    cli()
