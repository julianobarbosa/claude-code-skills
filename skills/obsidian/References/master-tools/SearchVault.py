#!/usr/bin/env python3
"""SearchVault - Search Obsidian vault via REST API or direct file access.

Commands:
  status   - Check REST API connectivity
  auth     - Verify API key
  search   - Search vault (--type dataview|content|jsonlogic)

Environment:
  OBSIDIAN_API_KEY   - REST API bearer token
  OBSIDIAN_BASE_URL  - API base URL (default: https://127.0.0.1:27124)
  OBSIDIAN_VAULT     - Vault path for direct file fallback
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
    import httpx
except ImportError:
    httpx = None

# ---------------------------------------------------------------------------
# REST API Client
# ---------------------------------------------------------------------------

API_BASE = os.getenv("OBSIDIAN_BASE_URL", "https://127.0.0.1:27124")
API_KEY = os.getenv("OBSIDIAN_API_KEY", "")


def _client() -> "httpx.Client":
    if httpx is None:
        raise click.ClickException("httpx not installed. Run: pip install httpx")
    return httpx.Client(
        base_url=API_BASE,
        headers={"Authorization": f"Bearer {API_KEY}"},
        verify=False,
        timeout=30.0,
    )


def _api_available() -> bool:
    try:
        c = _client()
        r = c.get("/vault/")
        c.close()
        return r.status_code == 200
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Direct file search fallback
# ---------------------------------------------------------------------------


def _detect_vault() -> Path:
    """Detect vault path from env or cwd."""
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


def _direct_content_search(
    query: str,
    folder: str | None = None,
    limit: int = 50,
) -> list[dict]:
    vault = _detect_vault()
    base = vault / folder if folder else vault
    pattern = re.compile(re.escape(query), re.IGNORECASE)
    results = []
    for md in sorted(base.rglob("*.md")):
        rel = str(md.relative_to(vault))
        if rel.startswith(".obsidian"):
            continue
        try:
            text = md.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        matches = []
        for i, line in enumerate(text.splitlines(), 1):
            if pattern.search(line):
                matches.append({"line": i, "text": line.strip()})
        if matches:
            results.append({"path": rel, "matches": matches})
            if len(results) >= limit:
                break
    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


@click.group()
def cli():
    """Search Obsidian vault via REST API or direct file access."""


@cli.command()
def status():
    """Check REST API connectivity."""
    if httpx is None:
        click.echo("httpx not installed - REST API unavailable")
        click.echo(f"Direct file fallback: vault at {_detect_vault()}")
        return
    available = _api_available()
    click.echo(f"REST API ({API_BASE}): {'connected' if available else 'unavailable'}")
    if not available:
        click.echo(f"Direct file fallback: vault at {_detect_vault()}")


@cli.command()
def auth():
    """Verify API key authentication."""
    if httpx is None:
        raise click.ClickException("httpx not installed. Run: pip install httpx")
    try:
        c = _client()
        r = c.get("/vault/")
        c.close()
        if r.status_code == 200:
            click.echo("Authenticated successfully")
        elif r.status_code == 401:
            click.echo("Authentication failed - check OBSIDIAN_API_KEY")
        else:
            click.echo(f"Unexpected status: {r.status_code}")
    except Exception as e:
        click.echo(f"Connection error: {e}")


@cli.command()
@click.argument("query", required=False)
@click.option("--type", "search_type", type=click.Choice(["dataview", "content", "jsonlogic"]), default="content")
@click.option("--query", "query_opt", help="Search query (alternative to positional arg)")
@click.option("--folder", help="Limit search to folder")
@click.option("--tags", help="Filter by tags (comma-separated)")
@click.option("--json", "as_json", is_flag=True, help="JSON output")
@click.option("--table", "as_table", is_flag=True, help="Table output")
@click.option("--limit", default=50, help="Max results")
def search(query, search_type, query_opt, folder, tags, as_json, as_table, limit):
    """Search vault. Positional QUERY or --query flag."""
    q = query or query_opt
    if not q:
        raise click.ClickException("Provide a search query as argument or --query")

    use_api = httpx is not None and _api_available()

    if search_type == "dataview":
        if not use_api:
            raise click.ClickException("Dataview search requires Obsidian REST API running")
        c = _client()
        r = c.post(
            "/search/",
            content=q.encode("utf-8"),
            headers={"Content-Type": "application/vnd.olrapi.dataview.dql+txt"},
        )
        c.close()
        if r.status_code != 200:
            raise click.ClickException(f"Dataview query failed ({r.status_code}): {r.text}")
        results = r.json()

    elif search_type == "jsonlogic":
        if not use_api:
            raise click.ClickException("JsonLogic search requires Obsidian REST API running")
        logic = json.loads(q)
        c = _client()
        r = c.post(
            "/search/jsonlogic/",
            json=logic,
            headers={"Content-Type": "application/vnd.olrapi.jsonlogic+json"},
        )
        c.close()
        if r.status_code != 200:
            raise click.ClickException(f"JsonLogic query failed ({r.status_code}): {r.text}")
        results = r.json()

    elif search_type == "content":
        if use_api:
            c = _client()
            r = c.post("/search/simple/", json={"query": q})
            c.close()
            if r.status_code != 200:
                raise click.ClickException(f"Search failed ({r.status_code}): {r.text}")
            results = r.json()
            if folder:
                results = [r for r in results if r.get("filename", "").startswith(folder)]
            results = results[:limit]
        else:
            results = _direct_content_search(q, folder=folder, limit=limit)
    else:
        raise click.ClickException(f"Unknown search type: {search_type}")

    # Tag filtering (post-filter for content/jsonlogic)
    if tags and isinstance(results, list):
        tag_set = {t.strip().lstrip("#") for t in tags.split(",")}
        filtered = []
        for r in results:
            note_tags = set()
            for t in r.get("tags", []):
                note_tags.add(t.lstrip("#"))
            if tag_set & note_tags:
                filtered.append(r)
        results = filtered

    # Output
    if as_json:
        click.echo(json.dumps(results, indent=2, default=str))
    elif as_table and isinstance(results, list):
        for item in results:
            if isinstance(item, dict):
                path = item.get("path") or item.get("filename", "?")
                matches = item.get("matches", [])
                click.echo(f"\n  {path}")
                for m in matches[:3]:
                    if isinstance(m, dict):
                        click.echo(f"    L{m.get('line', '?')}: {m.get('text', '')[:100]}")
    else:
        if isinstance(results, list):
            for item in results:
                if isinstance(item, dict):
                    click.echo(item.get("path") or item.get("filename", json.dumps(item, default=str)))
                else:
                    click.echo(str(item))
        else:
            click.echo(json.dumps(results, indent=2, default=str))


if __name__ == "__main__":
    cli()
