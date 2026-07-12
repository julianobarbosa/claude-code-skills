"""
Shared pytest fixtures for the yt-music skill test suite.

Goals:
- Never touch the user's real ~/.yt-music/ data dir — every test gets a temp dir
  via the YT_MUSIC_DATA_DIR env var.
- Never import the real `ytmusicapi` or `playwright` packages at test time —
  fake modules are installed in sys.modules before the scripts are imported.
- Each test gets a freshly-reloaded `helper` / `player` / `player_daemon` module
  so module-level constants (DATA_DIR, AUTH_FILE, STATE_FILE) reflect the per-test env.
"""

from __future__ import annotations

import importlib
import sys
import types
from pathlib import Path
from unittest.mock import MagicMock

import pytest

SKILL_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = SKILL_ROOT / "scripts"

# Ensure scripts/ is importable as a top-level package path.
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def _purge(*names: str) -> None:
    for name in names:
        sys.modules.pop(name, None)


@pytest.fixture
def data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Per-test data dir; the scripts honor YT_MUSIC_DATA_DIR at import time."""
    target = tmp_path / "yt-music-data"
    target.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("YT_MUSIC_DATA_DIR", str(target))
    return target


@pytest.fixture
def fake_yt_instance() -> MagicMock:
    """A MagicMock standing in for a YTMusic client. Tests assert on its calls."""
    return MagicMock(name="YTMusicInstance")


@pytest.fixture
def fake_ytmusicapi(monkeypatch: pytest.MonkeyPatch, fake_yt_instance: MagicMock):
    """
    Install a fake `ytmusicapi` module in sys.modules.

    `helper.get_yt()` does a lazy `from ytmusicapi import YTMusic` and instantiates
    it with either an auth file path or no args. We capture both call shapes and
    always return `fake_yt_instance` so test assertions can inspect method calls.
    """
    fake_module = types.ModuleType("ytmusicapi")
    yt_factory = MagicMock(name="YTMusicFactory", return_value=fake_yt_instance)
    fake_module.YTMusic = yt_factory  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "ytmusicapi", fake_module)
    yield yt_factory
    sys.modules.pop("ytmusicapi", None)


@pytest.fixture
def helper_mod(data_dir: Path, fake_ytmusicapi: MagicMock):
    """
    Fresh import of `helper.py` with the temp data dir env var set and a fake
    ytmusicapi already in sys.modules. Returns the module.
    """
    _purge("helper")
    module = importlib.import_module("helper")
    assert Path(module.DATA_DIR) == data_dir, (
        f"helper.DATA_DIR ({module.DATA_DIR}) did not pick up YT_MUSIC_DATA_DIR ({data_dir})"
    )
    yield module
    _purge("helper")


@pytest.fixture
def player_mod(data_dir: Path):
    """Fresh import of `player.py` with the temp data dir env var set."""
    _purge("player")
    module = importlib.import_module("player")
    assert Path(module.DATA_DIR) == data_dir
    yield module
    _purge("player")


@pytest.fixture
def fake_playwright(monkeypatch: pytest.MonkeyPatch) -> types.ModuleType:
    """
    Install fake `playwright` + `playwright.sync_api` modules so that importing
    `player_daemon` never reaches the real Playwright. The fake `sync_playwright`
    is a no-op context manager; tests that instantiate YTMusicRuntime should
    additionally patch its internals — most unit tests only touch pure helpers
    that never reach Playwright at all.
    """
    pkg = types.ModuleType("playwright")
    sync_api = types.ModuleType("playwright.sync_api")
    sync_api.sync_playwright = MagicMock(name="sync_playwright")  # type: ignore[attr-defined]
    pkg.sync_api = sync_api  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "playwright", pkg)
    monkeypatch.setitem(sys.modules, "playwright.sync_api", sync_api)
    yield sync_api
    sys.modules.pop("playwright", None)
    sys.modules.pop("playwright.sync_api", None)


@pytest.fixture
def player_daemon_mod(data_dir: Path, fake_playwright: types.ModuleType):
    """Fresh import of `player_daemon.py` for pure-helper tests."""
    _purge("player_daemon")
    module = importlib.import_module("player_daemon")
    assert Path(module.DATA_DIR) == data_dir
    yield module
    _purge("player_daemon")


def run_cli(module, *argv: str, monkeypatch: pytest.MonkeyPatch):
    """Invoke a script's `main()` with patched sys.argv, returning the SystemExit code."""
    monkeypatch.setattr(sys, "argv", [getattr(module, "__name__", "script"), *argv])
    try:
        module.main()
        return 0
    except SystemExit as exc:  # bail() and parser exits
        code = exc.code
        if code is None:
            return 0
        if isinstance(code, int):
            return code
        return 1
