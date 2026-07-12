"""Tests for the library command's dispatch table."""

from __future__ import annotations

import json

import pytest

from .conftest import run_cli


@pytest.fixture
def authed(helper_mod):
    """All library calls require auth — write a stub auth.json once."""
    helper_mod.AUTH_FILE.parent.mkdir(parents=True, exist_ok=True)
    helper_mod.AUTH_FILE.write_text(json.dumps({
        "Authorization": "x", "Cookie": "y", "X-Goog-AuthUser": "0", "x-origin": "z",
    }))
    return helper_mod


def test_library_requires_auth(helper_mod, capsys, monkeypatch):
    code = run_cli(helper_mod, "library", "playlists", monkeypatch=monkeypatch)
    assert code == 1
    err = json.loads(capsys.readouterr().err)
    assert err["error"] == "Auth required"


def test_library_songs_passes_limit_and_order(authed, fake_yt_instance, capsys, monkeypatch):
    fake_yt_instance.get_library_songs.return_value = [{"title": "Track"}]
    code = run_cli(
        authed, "library", "songs", "--limit", "5", "--order", "a_to_z",
        monkeypatch=monkeypatch,
    )
    assert code == 0
    body = json.loads(capsys.readouterr().out)
    assert body == [{"title": "Track"}]
    fake_yt_instance.get_library_songs.assert_called_once_with(limit=5, order="a_to_z")


def test_library_liked(authed, fake_yt_instance, monkeypatch):
    fake_yt_instance.get_liked_songs.return_value = {"tracks": []}
    code = run_cli(authed, "library", "liked", monkeypatch=monkeypatch)
    assert code == 0
    fake_yt_instance.get_liked_songs.assert_called_once_with(limit=25)


def test_library_playlists_default(authed, fake_yt_instance, monkeypatch):
    fake_yt_instance.get_library_playlists.return_value = []
    code = run_cli(authed, "library", "playlists", monkeypatch=monkeypatch)
    assert code == 0
    fake_yt_instance.get_library_playlists.assert_called_once_with(limit=25)


def test_library_default_subcommand_returns_playlists_overview(authed, fake_yt_instance, capsys, monkeypatch):
    """`library` with no sub uses the default `playlists` choice and wraps in overview."""
    fake_yt_instance.get_library_playlists.return_value = [{"title": "Pl1"}]
    code = run_cli(authed, "library", monkeypatch=monkeypatch)
    assert code == 0
    body = json.loads(capsys.readouterr().out)
    # Default `sub` is "playlists", which hits dispatch (not overview branch).
    assert body == [{"title": "Pl1"}]


def test_library_albums(authed, fake_yt_instance, monkeypatch):
    fake_yt_instance.get_library_albums.return_value = []
    code = run_cli(authed, "library", "albums", "--order", "recently_added", monkeypatch=monkeypatch)
    assert code == 0
    fake_yt_instance.get_library_albums.assert_called_once_with(limit=25, order="recently_added")


def test_library_artists(authed, fake_yt_instance, monkeypatch):
    fake_yt_instance.get_library_artists.return_value = []
    code = run_cli(authed, "library", "artists", monkeypatch=monkeypatch)
    assert code == 0
    fake_yt_instance.get_library_artists.assert_called_once_with(limit=25, order=None)


def test_library_subscriptions(authed, fake_yt_instance, monkeypatch):
    fake_yt_instance.get_library_subscriptions.return_value = []
    code = run_cli(authed, "library", "subscriptions", monkeypatch=monkeypatch)
    assert code == 0
    fake_yt_instance.get_library_subscriptions.assert_called_once_with(limit=25)


def test_library_history(authed, fake_yt_instance, monkeypatch):
    fake_yt_instance.get_history.return_value = []
    code = run_cli(authed, "library", "history", monkeypatch=monkeypatch)
    assert code == 0
    fake_yt_instance.get_history.assert_called_once_with()


def test_library_uploads(authed, fake_yt_instance, monkeypatch):
    fake_yt_instance.get_library_upload_songs.return_value = []
    code = run_cli(authed, "library", "uploads", "--limit", "7", monkeypatch=monkeypatch)
    assert code == 0
    fake_yt_instance.get_library_upload_songs.assert_called_once_with(limit=7)
