#!/usr/bin/env python3
"""Unit tests for VaultBuilder.py — uses only stdlib unittest."""

import sys
import tempfile
import unittest
from pathlib import Path

# Add parent Tools/ directory to path so we can import VaultBuilder
TOOLS_DIR = Path(__file__).resolve().parent.parent / "Tools"
sys.path.insert(0, str(TOOLS_DIR))

from VaultBuilder import detect_folders, KEYWORD_FOLDER_MAP, BASE_FOLDERS


class TestDetectFolders(unittest.TestCase):
    """Tests for the keyword-to-folder detection logic."""

    def test_single_keyword_match(self):
        result = detect_folders("pipeline")
        self.assertEqual(result, ["runbooks"])

    def test_multiple_keywords(self):
        result = detect_folders("pipeline, client, research")
        self.assertIn("runbooks", result)
        self.assertIn("clients", result)
        self.assertIn("research", result)

    def test_unknown_keyword_returns_empty(self):
        result = detect_folders("nonexistent_keyword_xyz")
        self.assertEqual(result, [])

    def test_empty_string_returns_empty(self):
        result = detect_folders("")
        self.assertEqual(result, [])

    def test_case_insensitive(self):
        result = detect_folders("Pipeline, CLOUD")
        self.assertEqual(result, ["runbooks"])

    def test_results_are_sorted(self):
        result = detect_folders("client, pipeline, research")
        self.assertEqual(result, sorted(result))

    def test_deduplication(self):
        # pipeline and infrastructure both map to runbooks
        result = detect_folders("pipeline, infrastructure")
        self.assertEqual(result.count("runbooks"), 1)


class TestConstants(unittest.TestCase):
    """Tests for module-level constants."""

    def test_base_folders_exist(self):
        self.assertIn("inbox", BASE_FOLDERS)
        self.assertIn("daily", BASE_FOLDERS)
        self.assertIn("projects", BASE_FOLDERS)
        self.assertIn("archive", BASE_FOLDERS)

    def test_keyword_map_not_empty(self):
        self.assertGreater(len(KEYWORD_FOLDER_MAP), 10)

    def test_all_map_values_are_strings(self):
        for key, value in KEYWORD_FOLDER_MAP.items():
            self.assertIsInstance(value, str, f"Key '{key}' maps to non-string: {value}")


if __name__ == "__main__":
    unittest.main()
