#!/usr/bin/env python3
"""
Find orphan notes (notes with no incoming or outgoing links).
Usage: python find-orphan-notes.py [vault_path]
"""

import os
import re
import sys
from pathlib import Path
from collections import defaultdict

def extract_links(content: str) -> set:
    """Extract wikilinks from note content."""
    # Match [[link]] or [[link|alias]]
    pattern = r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]'
    matches = re.findall(pattern, content)
    return set(matches)

def find_orphan_notes(vault_path: str = "."):
    """Find notes with no links to or from other notes."""

    vault = Path(vault_path)

    # Exclude folders
    exclude_folders = {'.obsidian', '.git', '.claude', 'node_modules', '99 - Meta'}

    # Track links
    outgoing_links = defaultdict(set)  # note -> set of linked notes
    incoming_links = defaultdict(set)  # note -> set of notes linking to it
    all_notes = set()

    # Find all markdown files
    for md_file in vault.rglob("*.md"):
        # Skip excluded folders
        if any(ex in md_file.parts for ex in exclude_folders):
            continue

        note_name = md_file.stem
        all_notes.add(note_name)

        try:
            content = md_file.read_text(encoding='utf-8')
            links = extract_links(content)

            outgoing_links[note_name] = links
            for link in links:
                # Handle links with path (folder/note)
                link_name = Path(link).stem if '/' in link else link
                incoming_links[link_name].add(note_name)
        except Exception as e:
            print(f"Error reading {md_file}: {e}", file=sys.stderr)

    # Find orphans
    orphans = []
    for note in all_notes:
        has_outgoing = bool(outgoing_links.get(note, set()) & all_notes)
        has_incoming = bool(incoming_links.get(note, set()))

        if not has_outgoing and not has_incoming:
            orphans.append(note)

    # Output results
    print(f"Total notes: {len(all_notes)}")
    print(f"Orphan notes: {len(orphans)}")
    print()

    if orphans:
        print("Orphan notes (no incoming or outgoing links):")
        for orphan in sorted(orphans):
            print(f"  - {orphan}")
    else:
        print("No orphan notes found!")

    return orphans


if __name__ == "__main__":
    vault_path = sys.argv[1] if len(sys.argv) > 1 else "."
    find_orphan_notes(vault_path)
