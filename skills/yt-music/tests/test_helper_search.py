"""Tests for search + suggest commands."""

from __future__ import annotations

import json

from .conftest import run_cli


def test_search_minimal_query(helper_mod, fake_yt_instance, capsys, monkeypatch):
    fake_yt_instance.search.return_value = [{"title": "Bohemian Rhapsody"}]
    code = run_cli(helper_mod, "search", "Bohemian Rhapsody", monkeypatch=monkeypatch)
    assert code == 0
    body = json.loads(capsys.readouterr().out)
    assert body == [{"title": "Bohemian Rhapsody"}]
    fake_yt_instance.search.assert_called_once_with("Bohemian Rhapsody", limit=10)


def test_search_with_filter_and_limit(helper_mod, fake_yt_instance, capsys, monkeypatch):
    fake_yt_instance.search.return_value = []
    code = run_cli(
        helper_mod, "search", "queen", "--type", "songs", "--limit", "25",
        monkeypatch=monkeypatch,
    )
    assert code == 0
    fake_yt_instance.search.assert_called_once_with("queen", limit=25, filter="songs")


def test_search_in_library_passes_scope(helper_mod, fake_yt_instance, capsys, monkeypatch):
    fake_yt_instance.search.return_value = []
    code = run_cli(
        helper_mod, "search", "queen", "--type", "songs", "--library",
        monkeypatch=monkeypatch,
    )
    assert code == 0
    fake_yt_instance.search.assert_called_once_with(
        "queen", limit=10, filter="songs", scope="library",
    )


def test_search_accepts_all_documented_filters(helper_mod, fake_yt_instance, monkeypatch):
    fake_yt_instance.search.return_value = []
    for t in ("songs", "artists", "albums", "playlists", "videos",
              "podcasts", "episodes", "profiles"):
        code = run_cli(helper_mod, "search", "x", "--type", t, monkeypatch=monkeypatch)
        assert code == 0


def test_suggest(helper_mod, fake_yt_instance, capsys, monkeypatch):
    fake_yt_instance.get_search_suggestions.return_value = ["queen", "queens"]
    code = run_cli(helper_mod, "suggest", "que", monkeypatch=monkeypatch)
    assert code == 0
    body = json.loads(capsys.readouterr().out)
    assert body == ["queen", "queens"]
    fake_yt_instance.get_search_suggestions.assert_called_once_with("que")
