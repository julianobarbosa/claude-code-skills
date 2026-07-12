"""Tests for the playlist subcommand."""

from __future__ import annotations

import json

import pytest

from .conftest import run_cli


@pytest.fixture
def authed(helper_mod):
    helper_mod.AUTH_FILE.parent.mkdir(parents=True, exist_ok=True)
    helper_mod.AUTH_FILE.write_text(json.dumps({
        "Authorization": "x", "Cookie": "y", "X-Goog-AuthUser": "0", "x-origin": "z",
    }))
    return helper_mod


def test_playlist_get(authed, fake_yt_instance, capsys, monkeypatch):
    fake_yt_instance.get_playlist.return_value = {"title": "Mix", "tracks": []}
    code = run_cli(authed, "playlist", "get", "PL123", monkeypatch=monkeypatch)
    assert code == 0
    body = json.loads(capsys.readouterr().out)
    assert body == {"title": "Mix", "tracks": []}
    fake_yt_instance.get_playlist.assert_called_once_with("PL123", limit=100)


def test_playlist_get_requires_id(authed, capsys, monkeypatch):
    code = run_cli(authed, "playlist", "get", monkeypatch=monkeypatch)
    assert code == 1
    assert "playlist_id required" in capsys.readouterr().err


def test_playlist_create_minimal(authed, fake_yt_instance, capsys, monkeypatch):
    fake_yt_instance.create_playlist.return_value = "PLNEW"
    code = run_cli(authed, "playlist", "create", "--title", "Vibes", monkeypatch=monkeypatch)
    assert code == 0
    body = json.loads(capsys.readouterr().out)
    assert body == {"playlistId": "PLNEW", "title": "Vibes", "privacy": "PRIVATE"}
    fake_yt_instance.create_playlist.assert_called_once_with(
        "Vibes", "", privacy_status="PRIVATE", video_ids=None,
    )


def test_playlist_create_full(authed, fake_yt_instance, monkeypatch):
    fake_yt_instance.create_playlist.return_value = "PLNEW"
    code = run_cli(
        authed, "playlist", "create",
        "--title", "Run Mix", "--description", "fast", "--privacy", "PUBLIC",
        monkeypatch=monkeypatch,
    )
    assert code == 0
    fake_yt_instance.create_playlist.assert_called_once_with(
        "Run Mix", "fast", privacy_status="PUBLIC", video_ids=None,
    )


def test_playlist_create_requires_title(authed, capsys, monkeypatch):
    code = run_cli(authed, "playlist", "create", monkeypatch=monkeypatch)
    assert code == 1
    assert "title required" in capsys.readouterr().err


def test_playlist_edit(authed, fake_yt_instance, capsys, monkeypatch):
    fake_yt_instance.edit_playlist.return_value = "STATUS_SUCCEEDED"
    code = run_cli(
        authed, "playlist", "edit", "PL123",
        "--title", "New", "--description", "desc", "--privacy", "UNLISTED",
        monkeypatch=monkeypatch,
    )
    assert code == 0
    body = json.loads(capsys.readouterr().out)
    assert body == {"status": "STATUS_SUCCEEDED"}
    fake_yt_instance.edit_playlist.assert_called_once_with(
        "PL123", title="New", description="desc", privacyStatus="UNLISTED",
    )


def test_playlist_edit_requires_id(authed, capsys, monkeypatch):
    code = run_cli(authed, "playlist", "edit", monkeypatch=monkeypatch)
    assert code == 1
    assert "playlist_id required" in capsys.readouterr().err


def test_playlist_delete(authed, fake_yt_instance, capsys, monkeypatch):
    fake_yt_instance.delete_playlist.return_value = "OK"
    code = run_cli(authed, "playlist", "delete", "PL123", monkeypatch=monkeypatch)
    assert code == 0
    body = json.loads(capsys.readouterr().out)
    assert body == {"status": "OK"}
    fake_yt_instance.delete_playlist.assert_called_once_with("PL123")


def test_playlist_add(authed, fake_yt_instance, capsys, monkeypatch):
    fake_yt_instance.add_playlist_items.return_value = {"status": "STATUS_SUCCEEDED"}
    code = run_cli(
        authed, "playlist", "add", "PL123", "vid1", "vid2",
        monkeypatch=monkeypatch,
    )
    assert code == 0
    body = json.loads(capsys.readouterr().out)
    assert body == {"status": "STATUS_SUCCEEDED"}
    fake_yt_instance.add_playlist_items.assert_called_once_with(
        "PL123", ["vid1", "vid2"], duplicates=False,
    )


def test_playlist_add_duplicates_flag(authed, fake_yt_instance, monkeypatch):
    fake_yt_instance.add_playlist_items.return_value = {}
    code = run_cli(
        authed, "playlist", "add", "PL123", "vid1", "--duplicates",
        monkeypatch=monkeypatch,
    )
    assert code == 0
    fake_yt_instance.add_playlist_items.assert_called_once_with(
        "PL123", ["vid1"], duplicates=True,
    )


def test_playlist_add_requires_ids(authed, capsys, monkeypatch):
    code = run_cli(authed, "playlist", "add", "PL123", monkeypatch=monkeypatch)
    assert code == 1
    assert "video_ids required" in capsys.readouterr().err


def test_playlist_add_playlist(authed, fake_yt_instance, monkeypatch):
    fake_yt_instance.add_playlist_items.return_value = {"ok": True}
    code = run_cli(
        authed, "playlist", "add-playlist", "PLDEST",
        "--source-playlist", "PLSRC",
        monkeypatch=monkeypatch,
    )
    assert code == 0
    fake_yt_instance.add_playlist_items.assert_called_once_with(
        "PLDEST", source_playlist="PLSRC",
    )


def test_playlist_add_playlist_requires_source(authed, capsys, monkeypatch):
    code = run_cli(authed, "playlist", "add-playlist", "PLDEST", monkeypatch=monkeypatch)
    assert code == 1
    assert "source-playlist required" in capsys.readouterr().err


def test_playlist_remove_matches_filter(authed, fake_yt_instance, capsys, monkeypatch):
    fake_yt_instance.get_playlist.return_value = {
        "tracks": [
            {"videoId": "vid1", "title": "a"},
            {"videoId": "vidZ", "title": "z"},
        ],
    }
    fake_yt_instance.remove_playlist_items.return_value = "STATUS_SUCCEEDED"
    code = run_cli(authed, "playlist", "remove", "PL123", "vid1", monkeypatch=monkeypatch)
    assert code == 0
    body = json.loads(capsys.readouterr().out)
    assert body == {"status": "STATUS_SUCCEEDED", "removed": 1}
    fake_yt_instance.remove_playlist_items.assert_called_once_with(
        "PL123", [{"videoId": "vid1", "title": "a"}],
    )


def test_playlist_remove_no_match(authed, fake_yt_instance, capsys, monkeypatch):
    fake_yt_instance.get_playlist.return_value = {"tracks": [{"videoId": "vidA"}]}
    code = run_cli(authed, "playlist", "remove", "PL123", "vidZ", monkeypatch=monkeypatch)
    assert code == 0
    body = json.loads(capsys.readouterr().out)
    assert body == {"status": "not_found", "removed": 0}
    fake_yt_instance.remove_playlist_items.assert_not_called()


def test_playlist_rate(authed, fake_yt_instance, capsys, monkeypatch):
    fake_yt_instance.rate_playlist.return_value = "OK"
    code = run_cli(
        authed, "playlist", "rate", "PL123", "--rating", "LIKE",
        monkeypatch=monkeypatch,
    )
    assert code == 0
    body = json.loads(capsys.readouterr().out)
    assert body == {"status": "OK"}
    fake_yt_instance.rate_playlist.assert_called_once_with("PL123", "LIKE")


def test_playlist_rate_defaults_to_like(authed, fake_yt_instance, monkeypatch):
    fake_yt_instance.rate_playlist.return_value = "OK"
    code = run_cli(authed, "playlist", "rate", "PL123", monkeypatch=monkeypatch)
    assert code == 0
    fake_yt_instance.rate_playlist.assert_called_once_with("PL123", "LIKE")
