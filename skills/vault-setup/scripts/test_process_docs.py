#!/usr/bin/env python3
"""Unit tests for process_docs_to_obsidian.py — uses only stdlib unittest."""

import tempfile
import unittest
from pathlib import Path

from process_docs_to_obsidian import add_frontmatter, import_files


class TestAddFrontmatter(unittest.TestCase):
    """Tests for frontmatter injection."""

    def test_adds_frontmatter_to_plain_content(self):
        result = add_frontmatter("# Hello", Path("test.md"))
        self.assertTrue(result.startswith("---"))
        self.assertIn("status: inbox", result)
        self.assertIn("# Hello", result)

    def test_preserves_existing_frontmatter(self):
        content = "---\ntitle: existing\n---\n# Hello"
        result = add_frontmatter(content, Path("test.md"))
        self.assertEqual(result, content)

    def test_includes_source_path(self):
        result = add_frontmatter("content", Path("/some/source.md"))
        self.assertIn("/some/source.md", result)


class TestImportFiles(unittest.TestCase):
    """Tests for the file import logic."""

    def test_imports_markdown_files(self):
        with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as vault:
            # Create a test markdown file
            (Path(src) / "test.md").write_text("# Test note")
            stats = import_files(Path(src), Path(vault))
            self.assertEqual(stats["imported"], 1)
            self.assertTrue((Path(vault) / "inbox" / "test.md").exists())

    def test_skips_existing_files(self):
        with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as vault:
            (Path(src) / "test.md").write_text("# Test")
            inbox = Path(vault) / "inbox"
            inbox.mkdir()
            (inbox / "test.md").write_text("# Already here")
            stats = import_files(Path(src), Path(vault))
            self.assertEqual(stats["skipped"], 1)
            self.assertEqual(stats["imported"], 0)

    def test_skips_unsupported_extensions(self):
        with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as vault:
            (Path(src) / "image.png").write_bytes(b"\x89PNG")
            stats = import_files(Path(src), Path(vault))
            self.assertEqual(stats["imported"], 0)

    def test_creates_inbox_directory(self):
        with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as vault:
            (Path(src) / "note.md").write_text("content")
            import_files(Path(src), Path(vault))
            self.assertTrue((Path(vault) / "inbox").is_dir())


if __name__ == "__main__":
    unittest.main()
