"""Tests for the pure (Playwright-free) helpers inside player_daemon.py."""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path
from unittest.mock import MagicMock

import pytest


# ─── _write_json ─────────────────────────────────────────────────────────────

def test_write_json_atomic(player_daemon_mod, tmp_path):
    target = tmp_path / "subdir" / "state.json"
    player_daemon_mod._write_json(target, {"a": 1, "b": [2, 3]})
    assert target.exists()
    assert json.loads(target.read_text()) == {"a": 1, "b": [2, 3]}
    # No stray .tmp left behind
    leftovers = list(target.parent.glob("*.tmp"))
    assert leftovers == []


def test_write_json_overwrites_existing(player_daemon_mod, tmp_path):
    target = tmp_path / "state.json"
    target.write_text("stale")
    player_daemon_mod._write_json(target, {"fresh": True})
    assert json.loads(target.read_text()) == {"fresh": True}


# ─── _remove_state_file ──────────────────────────────────────────────────────

def test_remove_state_file_matching_pid(player_daemon_mod):
    state = {"pid": 4242, "port": 1}
    player_daemon_mod.STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    player_daemon_mod.STATE_FILE.write_text(json.dumps(state))
    player_daemon_mod._remove_state_file(4242)
    assert not player_daemon_mod.STATE_FILE.exists()


def test_remove_state_file_pid_mismatch(player_daemon_mod):
    """Another daemon owns the file — don't delete it."""
    state = {"pid": 7777, "port": 1}
    player_daemon_mod.STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    player_daemon_mod.STATE_FILE.write_text(json.dumps(state))
    player_daemon_mod._remove_state_file(4242)
    assert player_daemon_mod.STATE_FILE.exists()


def test_remove_state_file_when_unreadable(player_daemon_mod):
    """Malformed state file → swallow the error, leave file alone."""
    player_daemon_mod.STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    player_daemon_mod.STATE_FILE.write_text("{not json")
    player_daemon_mod._remove_state_file(4242)
    assert player_daemon_mod.STATE_FILE.exists()


def test_remove_state_file_when_missing(player_daemon_mod):
    player_daemon_mod._remove_state_file(4242)  # must not raise


# ─── _candidate_paths ────────────────────────────────────────────────────────

def test_candidate_paths_returns_non_empty(player_daemon_mod):
    paths = player_daemon_mod._candidate_paths()
    assert isinstance(paths, list)
    assert len(paths) >= 1


# ─── _find_browser ───────────────────────────────────────────────────────────

def test_find_browser_returns_existing_path(player_daemon_mod, tmp_path, monkeypatch):
    fake_bin = tmp_path / "chrome"
    fake_bin.write_text("#!/bin/sh\necho chrome\n")
    fake_bin.chmod(0o755)
    monkeypatch.setattr(player_daemon_mod, "_candidate_paths", lambda: [str(fake_bin)])
    monkeypatch.setattr(player_daemon_mod.shutil, "which", lambda _x: None)
    assert player_daemon_mod._find_browser() == str(fake_bin)


def test_find_browser_falls_back_to_which(player_daemon_mod, monkeypatch):
    monkeypatch.setattr(player_daemon_mod, "_candidate_paths", lambda: ["nonexistent-binary"])
    monkeypatch.setattr(player_daemon_mod.shutil, "which",
                        lambda name: "/resolved/bin/chrome" if name == "nonexistent-binary" else None)
    assert player_daemon_mod._find_browser() == "/resolved/bin/chrome"


def test_find_browser_returns_none(player_daemon_mod, monkeypatch):
    monkeypatch.setattr(player_daemon_mod, "_candidate_paths", lambda: ["nonexistent-binary"])
    monkeypatch.setattr(player_daemon_mod.shutil, "which", lambda _x: None)
    assert player_daemon_mod._find_browser() is None


# ─── _browser_version ────────────────────────────────────────────────────────

def test_browser_version_parses_stdout(player_daemon_mod, monkeypatch):
    completed = MagicMock(
        returncode=0,
        stdout="Google Chrome 124.0.6367.78 \n",
    )
    monkeypatch.setattr(player_daemon_mod.subprocess, "run", lambda *a, **k: completed)
    assert player_daemon_mod._browser_version("/path/to/chrome") == "Google Chrome 124.0.6367.78"


def test_browser_version_no_path(player_daemon_mod):
    assert player_daemon_mod._browser_version(None) is None


def test_browser_version_failed_invocation(player_daemon_mod, monkeypatch):
    completed = MagicMock(returncode=1, stdout="")
    monkeypatch.setattr(player_daemon_mod.subprocess, "run", lambda *a, **k: completed)
    assert player_daemon_mod._browser_version("/path/to/chrome") is None


def test_browser_version_empty_stdout(player_daemon_mod, monkeypatch):
    completed = MagicMock(returncode=0, stdout="")
    monkeypatch.setattr(player_daemon_mod.subprocess, "run", lambda *a, **k: completed)
    assert player_daemon_mod._browser_version("/path/to/chrome") is None


# ─── constants ───────────────────────────────────────────────────────────────

def test_keybindings_present(player_daemon_mod):
    keys = player_daemon_mod.KEYS
    assert keys["toggle"] == "k"
    # Next/prev use Shift+N / Shift+P per YouTube Music's keyboard shortcuts.
    assert "Shift" in keys["next"]
    assert "Shift" in keys["prev"]


def test_selectors_present(player_daemon_mod):
    sels = player_daemon_mod.SELECTORS
    assert sels["app"] == "ytmusic-app"
    assert sels["player_bar"] == "ytmusic-player-bar"
    assert "shuffle" in sels
    assert "repeat" in sels


def test_ytm_url(player_daemon_mod):
    assert player_daemon_mod.YTM_URL == "https://music.youtube.com"


# ─── build_parser ────────────────────────────────────────────────────────────

def test_parser_defaults(player_daemon_mod):
    parser = player_daemon_mod.build_parser()
    args = parser.parse_args([])
    assert args.host == "127.0.0.1"
    assert args.port == 0  # 0 → OS-assigned
    assert isinstance(args.user_data_dir, Path)


def test_parser_overrides(player_daemon_mod, tmp_path):
    parser = player_daemon_mod.build_parser()
    args = parser.parse_args([
        "--host", "0.0.0.0",
        "--port", "1234",
        "--user-data-dir", str(tmp_path),
    ])
    assert args.host == "0.0.0.0"
    assert args.port == 1234
    assert args.user_data_dir == tmp_path
