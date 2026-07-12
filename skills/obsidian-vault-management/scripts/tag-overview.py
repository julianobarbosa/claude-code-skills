#!/usr/bin/env python3
"""
Generate an overview of all tags used in the vault.
Usage: python tag-overview.py [vault_path] [--output FILE]
"""

import os
import re
import sys
import argparse
from pathlib import Path
from collections import defaultdict
import yaml

def extract_frontmatter_tags(content: str) -> list:
    """Extract tags from YAML frontmatter."""
    tags = []

    # Match frontmatter
    fm_match = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if fm_match:
        try:
            fm = yaml.safe_load(fm_match.group(1))
            if fm and 'tags' in fm:
                fm_tags = fm['tags']
                if isinstance(fm_tags, list):
                    tags.extend(fm_tags)
                elif isinstance(fm_tags, str):
                    tags.append(fm_tags)
        except:
            pass

    return tags

def extract_inline_tags(content: str) -> list:
    """Extract inline #tags from content."""
    # Match #tag but not in code blocks or links
    pattern = r'(?<![`\[])#([a-zA-Z0-9_-]+(?:/[a-zA-Z0-9_-]+)*)'
    return re.findall(pattern, content)

def generate_tag_overview(vault_path: str = ".", output_file: str = None):
    """Generate tag usage statistics."""

    vault = Path(vault_path)

    # Exclude folders
    exclude_folders = {'.obsidian', '.git', '.claude', 'node_modules'}

    # Track tags
    tag_usage = defaultdict(list)  # tag -> list of notes using it

    # Find all markdown files
    for md_file in vault.rglob("*.md"):
        # Skip excluded folders
        if any(ex in md_file.parts for ex in exclude_folders):
            continue

        try:
            content = md_file.read_text(encoding='utf-8')

            # Get all tags
            all_tags = set()
            all_tags.update(extract_frontmatter_tags(content))
            all_tags.update(extract_inline_tags(content))

            # Normalize tags (remove # prefix if present)
            for tag in all_tags:
                clean_tag = tag.lstrip('#')
                if clean_tag:
                    tag_usage[clean_tag].append(md_file.stem)

        except Exception as e:
            print(f"Error reading {md_file}: {e}", file=sys.stderr)

    # Sort by usage count
    sorted_tags = sorted(tag_usage.items(), key=lambda x: len(x[1]), reverse=True)

    # Generate output
    output_lines = []
    output_lines.append("# Tag Overview")
    output_lines.append("")
    output_lines.append(f"Total unique tags: {len(sorted_tags)}")
    output_lines.append("")
    output_lines.append("## Tags by Usage")
    output_lines.append("")
    output_lines.append("| Tag | Count |")
    output_lines.append("|-----|-------|")

    for tag, notes in sorted_tags:
        output_lines.append(f"| #{tag} | {len(notes)} |")

    output_lines.append("")
    output_lines.append("## Tag Details")
    output_lines.append("")

    for tag, notes in sorted_tags[:20]:  # Top 20 detailed
        output_lines.append(f"### #{tag} ({len(notes)} notes)")
        output_lines.append("")
        for note in sorted(notes)[:10]:  # First 10 notes
            output_lines.append(f"- [[{note}]]")
        if len(notes) > 10:
            output_lines.append(f"- ... and {len(notes) - 10} more")
        output_lines.append("")

    output = "\n".join(output_lines)

    if output_file:
        Path(output_file).write_text(output)
        print(f"Tag overview saved to: {output_file}")
    else:
        print(output)

    return dict(tag_usage)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate tag overview for Obsidian vault')
    parser.add_argument('vault_path', nargs='?', default='.', help='Path to vault')
    parser.add_argument('--output', '-o', help='Output file path')

    args = parser.parse_args()
    generate_tag_overview(args.vault_path, args.output)
