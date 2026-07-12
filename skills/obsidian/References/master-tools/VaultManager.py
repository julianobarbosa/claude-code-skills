#!/usr/bin/env python3
"""VaultManager - Vault health checks, orphan detection, and lifecycle management.

Commands:
  health        - Full vault health report
  orphans       - Find notes with no inlinks or outlinks
  broken-links  - Find wikilinks pointing to non-existent notes
  lifecycle     - Change note lifecycle state
  move          - Move note between PARA folders
  inbox         - List inbox notes for triage

Environment:
  OBSIDIAN_VAULT - Vault path (default: auto-detect from cwd)
"""
from __future__ import annotations

import json
import os
import re
import shutil
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
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

WIKILINK_RE = re.compile(r"\[\[([^\]|#]+?)(?:#[^\]|]*)?(?:\|[^\]]+)?\]\]")
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---", re.DOTALL)
TAG_RE = re.compile(r"(?:^|\s)#([a-zA-Z][a-zA-Z0-9_/\-]*)", re.MULTILINE)


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


def _iter_notes(vault: Path):
    for md in vault.rglob("*.md"):
        rel = str(md.relative_to(vault))
        if rel.startswith(".obsidian") or rel.startswith("."):
            continue
        yield md, rel


def _read_note(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _parse_frontmatter(text: str) -> dict:
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}
    if yaml:
        try:
            return yaml.safe_load(m.group(1)) or {}
        except Exception:
            return {}
    return {"_raw": m.group(1)}


def _extract_wikilinks(text: str) -> list[str]:
    return WIKILINK_RE.findall(text)


def _extract_tags(text: str) -> list[str]:
    return TAG_RE.findall(text)


def _note_name(rel: str) -> str:
    return Path(rel).stem


def _folder_name(rel: str) -> str:
    parts = Path(rel).parts
    return parts[0] if len(parts) > 1 else "/"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


@click.group()
def cli():
    """Obsidian vault management and health checks."""


@cli.command()
@click.option("--vault", help="Vault path")
@click.option("--json", "as_json", is_flag=True, help="JSON output")
def health(vault, as_json):
    """Full vault health report."""
    v = _detect_vault(vault)
    folder_counts: Counter = Counter()
    tag_counts: Counter = Counter()
    total = 0
    empty_notes = []
    no_frontmatter = []
    no_tags = []

    for md, rel in _iter_notes(v):
        total += 1
        folder_counts[_folder_name(rel)] += 1
        text = _read_note(md)
        if len(text.strip()) < 10:
            empty_notes.append(rel)
        fm = _parse_frontmatter(text)
        if not fm:
            no_frontmatter.append(rel)
        tags = fm.get("tags", []) or []
        if isinstance(tags, list):
            for t in tags:
                tag_counts[str(t)] += 1
        inline_tags = _extract_tags(text)
        for t in inline_tags:
            tag_counts[t] += 1
        if not tags and not inline_tags:
            no_tags.append(rel)

    fm_coverage = ((total - len(no_frontmatter)) / total * 100) if total else 0

    report = {
        "total_notes": total,
        "by_folder": dict(folder_counts.most_common(20)),
        "frontmatter_coverage_pct": round(fm_coverage, 1),
        "notes_without_tags": len(no_tags),
        "empty_notes": len(empty_notes),
        "top_tags": dict(tag_counts.most_common(15)),
    }

    if as_json:
        click.echo(json.dumps(report, indent=2))
    else:
        click.echo("Vault Health Report")
        click.echo("=" * 40)
        click.echo(f"Total notes: {total:,}")
        click.echo(f"\nBy folder:")
        for folder, count in folder_counts.most_common(20):
            click.echo(f"  {folder:<30} {count:>5}")
        click.echo(f"\nFrontmatter coverage: {fm_coverage:.1f}%")
        click.echo(f"Notes without tags: {len(no_tags)}")
        click.echo(f"Empty notes: {len(empty_notes)}")
        if empty_notes:
            for n in empty_notes[:5]:
                click.echo(f"  - {n}")
        click.echo(f"\nTop tags:")
        for tag, count in tag_counts.most_common(15):
            click.echo(f"  #{tag:<25} {count:>4}")


@cli.command()
@click.option("--vault", help="Vault path")
@click.option("--json", "as_json", is_flag=True)
def orphans(vault, as_json):
    """Find notes with no inlinks or outlinks."""
    v = _detect_vault(vault)
    outlinks: dict[str, set] = {}
    inlinks: defaultdict[str, set] = defaultdict(set)
    all_names: dict[str, str] = {}

    for md, rel in _iter_notes(v):
        name = _note_name(rel)
        all_names[name.lower()] = rel
        text = _read_note(md)
        links = _extract_wikilinks(text)
        outlinks[rel] = {l.strip() for l in links}
        for link in links:
            inlinks[link.strip().lower()].add(rel)

    orphan_list = []
    for md, rel in _iter_notes(v):
        name = _note_name(rel)
        has_outlinks = bool(outlinks.get(rel))
        has_inlinks = bool(inlinks.get(name.lower()))
        if not has_outlinks and not has_inlinks:
            orphan_list.append(rel)

    if as_json:
        click.echo(json.dumps({"orphans": orphan_list, "count": len(orphan_list)}, indent=2))
    else:
        click.echo(f"Orphan notes (no inlinks or outlinks): {len(orphan_list)}")
        for o in sorted(orphan_list):
            click.echo(f"  - {o}")


@cli.command("broken-links")
@click.option("--vault", help="Vault path")
@click.option("--json", "as_json", is_flag=True)
def broken_links(vault, as_json):
    """Find wikilinks pointing to non-existent notes."""
    v = _detect_vault(vault)
    all_names: set[str] = set()
    for md, rel in _iter_notes(v):
        all_names.add(_note_name(rel).lower())

    broken = []
    for md, rel in _iter_notes(v):
        text = _read_note(md)
        links = _extract_wikilinks(text)
        for link in links:
            target = link.strip().lower()
            if target and target not in all_names:
                broken.append({"source": rel, "target": link.strip()})

    if as_json:
        click.echo(json.dumps({"broken_links": broken, "count": len(broken)}, indent=2))
    else:
        click.echo(f"Broken wikilinks: {len(broken)}")
        seen = set()
        for b in broken:
            key = f"{b['source']} -> {b['target']}"
            if key not in seen:
                seen.add(key)
                click.echo(f"  {b['source']}")
                click.echo(f"    -> [[{b['target']}]]")


@cli.command()
@click.option("--vault", help="Vault path")
@click.option("--path", "note_path", required=True, help="Note path relative to vault")
@click.option("--state", type=click.Choice(["active", "processed", "archived"]), required=True)
def lifecycle(vault, note_path, state):
    """Change note lifecycle state."""
    v = _detect_vault(vault)
    full = v / note_path
    if not full.exists():
        raise click.ClickException(f"Note not found: {note_path}")

    text = _read_note(full)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M")

    fm = FRONTMATTER_RE.match(text)
    if fm:
        fm_text = fm.group(1)
        if re.search(r"^status:", fm_text, re.MULTILINE):
            fm_text = re.sub(r"^status:.*$", f"status: {state}", fm_text, flags=re.MULTILINE)
        else:
            fm_text += f"\nstatus: {state}"
        fm_text = re.sub(r"^updated:.*$", f"updated: {now}", fm_text, flags=re.MULTILINE)
        new_text = f"---\n{fm_text}\n---{text[fm.end():]}"
    else:
        new_text = f"---\nstatus: {state}\nupdated: {now}\n---\n{text}"

    full.write_text(new_text, encoding="utf-8")
    click.echo(f"Updated {note_path} -> status: {state}")


@cli.command()
@click.option("--vault", help="Vault path")
@click.option("--path", "note_path", required=True, help="Note path relative to vault")
@click.option("--to", "dest", required=True, help="Destination folder")
def move(vault, note_path, dest):
    """Move note between PARA folders."""
    v = _detect_vault(vault)
    src = v / note_path
    if not src.exists():
        raise click.ClickException(f"Note not found: {note_path}")

    dest_dir = v / dest
    dest_dir.mkdir(parents=True, exist_ok=True)
    dst = dest_dir / src.name

    if dst.exists():
        raise click.ClickException(f"Destination already exists: {dst.relative_to(v)}")

    shutil.move(str(src), str(dst))
    click.echo(f"Moved: {note_path} -> {dst.relative_to(v)}")


@cli.command()
@click.option("--vault", help="Vault path")
@click.option("--json", "as_json", is_flag=True)
def inbox(vault, as_json):
    """List notes in 00 - Inbox/ for triage."""
    v = _detect_vault(vault)
    inbox_dir = v / "00 - Inbox"
    if not inbox_dir.is_dir():
        click.echo("No inbox folder found (00 - Inbox/)")
        return

    notes = []
    for md in sorted(inbox_dir.rglob("*.md")):
        rel = str(md.relative_to(v))
        text = _read_note(md)
        fm = _parse_frontmatter(text)
        preview = ""
        lines = text.split("\n")
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith("---") and not stripped.startswith("#"):
                preview = stripped[:100]
                break
        notes.append({
            "path": rel,
            "name": md.stem,
            "has_frontmatter": bool(fm),
            "tags": fm.get("tags", []),
            "preview": preview,
            "size": md.stat().st_size,
            "modified": datetime.fromtimestamp(md.stat().st_mtime).isoformat(),
        })

    if as_json:
        click.echo(json.dumps(notes, indent=2, default=str))
    else:
        click.echo(f"Inbox notes: {len(notes)}")
        for n in notes:
            fm_icon = "+" if n["has_frontmatter"] else "-"
            click.echo(f"  [{fm_icon}] {n['name']}")
            if n["preview"]:
                click.echo(f"      {n['preview']}")


if __name__ == "__main__":
    cli()
