"""Tests for argparse wiring in helper.build_parser."""

from __future__ import annotations

import json
import sys

import pytest

from .conftest import run_cli


def test_help_with_no_command_exits_zero(helper_mod, capsys, monkeypatch):
    code = run_cli(helper_mod, monkeypatch=monkeypatch)
    assert code == 0
    out = capsys.readouterr().out
    assert "yt-music" in out
    assert "search" in out


def test_unknown_command_argparse_exits_two(helper_mod, capsys, monkeypatch):
    code = run_cli(helper_mod, "no-such-command", monkeypatch=monkeypatch)
    # argparse exits with status 2 on invalid arguments
    assert code == 2


def test_search_unknown_filter_rejected_by_choices(helper_mod, capsys, monkeypatch):
    code = run_cli(helper_mod, "search", "q", "--type", "garbage", monkeypatch=monkeypatch)
    assert code == 2


def test_data_dir_env_override(helper_mod, data_dir):
    """Confirm the env-var contract: DATA_DIR / AUTH_FILE follow YT_MUSIC_DATA_DIR."""
    assert helper_mod.DATA_DIR == data_dir
    assert helper_mod.AUTH_FILE == data_dir / "auth.json"


def test_resolve_data_dir_default(monkeypatch, tmp_path):
    """When YT_MUSIC_DATA_DIR is unset, _resolve_data_dir falls back to <skill-root>/.yt-music/."""
    monkeypatch.delenv("YT_MUSIC_DATA_DIR", raising=False)
    # Re-import helper without the fixture so module-level constants reflect default.
    import importlib
    sys.modules.pop("helper", None)
    helper = importlib.import_module("helper")
    try:
        # The default is <scripts dir>/../.yt-music/
        assert helper.DATA_DIR.name == ".yt-music"
        assert helper.DATA_DIR.parent.name == "yt-music"
    finally:
        sys.modules.pop("helper", None)
