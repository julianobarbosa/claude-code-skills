#!/usr/bin/env python3
"""Import files into an Obsidian vault's inbox folder.

Usage:
    python process_docs_to_obsidian.py SOURCE_DIR VAULT_DIR

Copies supported files (.md, .txt, .pdf) from SOURCE_DIR to VAULT_DIR/inbox/,
adding basic frontmatter to .md files. Skips files that already exist.
"""

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

SUPPORTED_EXTENSIONS = {".md", ".txt", ".pdf", ".docx"}


def add_frontmatter(content: str, source_path: Path) -> str:
    """Add basic frontmatter to markdown content if not already present."""
    if content.startswith("---"):
        return content  # Already has frontmatter

    now = datetime.now().strftime("%Y-%m-%dT%H:%M")
    frontmatter = f"""---
created: {now}
imported_from: {source_path}
status: inbox
tags:
  - imported
---

"""
    return frontmatter + content


def import_files(source_dir: Path, vault_dir: Path) -> dict:
    """Import files from source to vault inbox."""
    inbox = vault_dir / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)

    stats = {"imported": 0, "skipped": 0, "errors": 0, "files": []}

    for file_path in sorted(source_dir.iterdir()):
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        if file_path.name.startswith("."):
            continue

        target = inbox / file_path.name

        # Skip if already exists
        if target.exists():
            stats["skipped"] += 1
            print(f"  [skip] {file_path.name} (already exists)")
            continue

        try:
            if file_path.suffix.lower() == ".md":
                # Add frontmatter to markdown files
                raw_bytes = file_path.read_bytes()
                try:
                    content = raw_bytes.decode("utf-8")
                except UnicodeDecodeError:
                    content = raw_bytes.decode("utf-8", errors="replace")
                    print(f"  [warn] {file_path.name}: encoding issues detected, some characters replaced")
                content = add_frontmatter(content, file_path)
                target.write_text(content, encoding="utf-8")
            else:
                # Binary copy for PDF, DOCX, etc.
                shutil.copy2(file_path, target)

            stats["imported"] += 1
            stats["files"].append(file_path.name)
            print(f"  [ok] {file_path.name}")
        except Exception as e:
            stats["errors"] += 1
            print(f"  [error] {file_path.name}: {e}")

    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Import files into an Obsidian vault's inbox folder."
    )
    parser.add_argument("source", type=Path, help="Source directory containing files to import")
    parser.add_argument("vault", type=Path, help="Target Obsidian vault directory")

    args = parser.parse_args()

    if not args.source.is_dir():
        print(f"Error: Source directory not found: {args.source}", file=sys.stderr)
        sys.exit(1)

    if not args.vault.is_dir():
        print(f"Error: Vault directory not found: {args.vault}", file=sys.stderr)
        sys.exit(1)

    print(f"Importing from {args.source} → {args.vault}/inbox/\n")

    stats = import_files(args.source, args.vault)

    print(f"\nDone: {stats['imported']} imported, {stats['skipped']} skipped, {stats['errors']} errors")

    if stats["imported"] > 0:
        print(f'\nNext step: tell Claude "Sort everything in inbox/"')


if __name__ == "__main__":
    main()
