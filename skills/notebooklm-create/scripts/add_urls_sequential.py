#!/usr/bin/env python3
"""
add_urls_sequential.py — plan-printer for sequential NotebookLM URL adds.

This script does NOT call the MCP tool itself (that happens from Claude's tool
layer). Instead it:
  1. Reads a list of candidate URLs
  2. Filters out known-failing domains (Medium, Quora, LinkedIn)
  3. Cleans URL quirks (strips trailing .md from llms.txt)
  4. Emits the sequential call plan for Claude to execute

Usage:
  python scripts/add_urls_sequential.py --notebook-id NB_UUID --urls urls.txt

  where urls.txt has one URL per line (blank lines and # comments ignored).

Output: prints each filtered URL on its own line, prefixed with
`CALL:` for URLs to add and `SKIP:` for filtered-out ones with a reason.

Claude should execute the CALL lines as separate sequential
mcp__notebooklm-rpc__notebook_add_url calls — one at a time, waiting for each
success response before the next.
"""

import argparse
import re
import sys
from urllib.parse import urlparse

# Domains that silently fail in NotebookLM's URL fetcher.
# Add as a text source instead (scrape with WebFetch).
BLOCKED_DOMAINS = {
    "medium.com",
    "quora.com",
    "linkedin.com",
}

BLOCKED_SUBDOMAIN_SUFFIXES = (
    ".medium.com",
    ".quora.com",
    ".linkedin.com",
)


def clean_url(url: str) -> str:
    """Apply known URL-quirk fixes."""
    # Strip trailing .md from llms.txt
    url = re.sub(r"(/llms\.txt)\.md(\?|$|#)", r"\1\2", url)
    return url.strip()


def is_blocked(url: str) -> tuple[bool, str]:
    """Return (blocked, reason)."""
    try:
        host = urlparse(url).hostname or ""
    except Exception:
        return True, "unparseable URL"
    host = host.lower()
    if host in BLOCKED_DOMAINS:
        return True, f"domain {host} silently fails in NotebookLM"
    for suffix in BLOCKED_SUBDOMAIN_SUFFIXES:
        if host.endswith(suffix):
            return True, f"subdomain of {suffix.lstrip('.')} silently fails"
    return False, ""


def load_urls(path: str) -> list[str]:
    with open(path) as f:
        lines = [ln.strip() for ln in f]
    return [ln for ln in lines if ln and not ln.startswith("#")]


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--notebook-id", required=True)
    p.add_argument("--urls", required=True, help="path to file with one URL per line")
    args = p.parse_args()

    urls = [clean_url(u) for u in load_urls(args.urls)]
    call_count = 0
    skip_count = 0

    print(f"# Sequential add plan for notebook {args.notebook_id}")
    print(f"# {len(urls)} candidate URL(s)")
    print()

    for u in urls:
        blocked, reason = is_blocked(u)
        if blocked:
            print(f"SKIP: {u}  # {reason} — scrape content with WebFetch and add as text")
            skip_count += 1
        else:
            print(f"CALL: mcp__notebooklm-rpc__notebook_add_url(notebook_id=\"{args.notebook_id}\", url=\"{u}\")")
            call_count += 1

    print()
    print(f"# Summary: {call_count} to add sequentially, {skip_count} skipped")
    print("# Execute each CALL line one at a time. Wait for success before the next.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
