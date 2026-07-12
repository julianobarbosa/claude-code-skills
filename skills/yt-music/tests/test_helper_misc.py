"""Tests for the long-tail subcommands of helper.py."""

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


# ─── artist / album / song ───────────────────────────────────────────────────

def test_artist(helper_mod, fake_yt_instance, capsys, monkeypatch):
    fake_yt_instance.get_artist.return_value = {"name": "Queen"}
    code = run_cli(helper_mod, "artist", "UC123", monkeypatch=monkeypatch)
    assert code == 0
    body = json.loads(capsys.readouterr().out)
    assert body == {"name": "Queen"}
    fake_yt_instance.get_artist.assert_called_once_with("UC123")


def test_artist_albums_with_params(helper_mod, fake_yt_instance, capsys, monkeypatch):
    fake_yt_instance.get_artist.return_value = {
        "albums": {"params": "ABC", "results": ["ignored"]},
    }
    fake_yt_instance.get_artist_albums.return_value = [{"title": "News of the World"}]
    code = run_cli(helper_mod, "artist-albums", "UC123", monkeypatch=monkeypatch)
    assert code == 0
    body = json.loads(capsys.readouterr().out)
    assert body == [{"title": "News of the World"}]
    fake_yt_instance.get_artist_albums.assert_called_once_with("UC123", "ABC")


def test_artist_albums_falls_back_to_inline_results(helper_mod, fake_yt_instance, capsys, monkeypatch):
    fake_yt_instance.get_artist.return_value = {
        "albums": {"results": [{"title": "A Day at the Races"}]},  # no params
    }
    code = run_cli(helper_mod, "artist-albums", "UC123", monkeypatch=monkeypatch)
    assert code == 0
    body = json.loads(capsys.readouterr().out)
    assert body == [{"title": "A Day at the Races"}]
    fake_yt_instance.get_artist_albums.assert_not_called()


def test_album_with_browse_id(helper_mod, fake_yt_instance, monkeypatch):
    fake_yt_instance.get_album.return_value = {"title": "News"}
    code = run_cli(helper_mod, "album", "MPREb_xxx", monkeypatch=monkeypatch)
    assert code == 0
    fake_yt_instance.get_album.assert_called_once_with("MPREb_xxx")
    fake_yt_instance.get_album_browse_id.assert_not_called()


def test_album_converts_olak_id(helper_mod, fake_yt_instance, monkeypatch):
    fake_yt_instance.get_album_browse_id.return_value = "MPREb_converted"
    fake_yt_instance.get_album.return_value = {}
    code = run_cli(helper_mod, "album", "OLAK5uy_abc", monkeypatch=monkeypatch)
    assert code == 0
    fake_yt_instance.get_album_browse_id.assert_called_once_with("OLAK5uy_abc")
    fake_yt_instance.get_album.assert_called_once_with("MPREb_converted")


def test_album_converts_pl_id(helper_mod, fake_yt_instance, monkeypatch):
    fake_yt_instance.get_album_browse_id.return_value = "MPREb_x"
    fake_yt_instance.get_album.return_value = {}
    code = run_cli(helper_mod, "album", "PL_abc", monkeypatch=monkeypatch)
    assert code == 0
    fake_yt_instance.get_album_browse_id.assert_called_once_with("PL_abc")


def test_song(helper_mod, fake_yt_instance, monkeypatch):
    fake_yt_instance.get_song.return_value = {"videoId": "v1"}
    code = run_cli(helper_mod, "song", "v1", monkeypatch=monkeypatch)
    assert code == 0
    fake_yt_instance.get_song.assert_called_once_with("v1")


# ─── lyrics / related / watch ────────────────────────────────────────────────

def test_lyrics_success(helper_mod, fake_yt_instance, capsys, monkeypatch):
    fake_yt_instance.get_watch_playlist.return_value = {"lyrics": "lyrics_id_1"}
    fake_yt_instance.get_lyrics.return_value = {"lyrics": "ohh, can you feel..."}
    code = run_cli(helper_mod, "lyrics", "v1", monkeypatch=monkeypatch)
    assert code == 0
    body = json.loads(capsys.readouterr().out)
    assert body == {"lyrics": "ohh, can you feel..."}
    fake_yt_instance.get_watch_playlist.assert_called_once_with("v1")
    fake_yt_instance.get_lyrics.assert_called_once_with("lyrics_id_1")


def test_lyrics_unavailable(helper_mod, fake_yt_instance, capsys, monkeypatch):
    fake_yt_instance.get_watch_playlist.return_value = {"lyrics": None}
    code = run_cli(helper_mod, "lyrics", "v1", monkeypatch=monkeypatch)
    assert code == 0
    body = json.loads(capsys.readouterr().out)
    assert body == {"error": "No lyrics available for this song"}
    fake_yt_instance.get_lyrics.assert_not_called()


def test_related_success(helper_mod, fake_yt_instance, monkeypatch):
    fake_yt_instance.get_watch_playlist.return_value = {"related": "rel_id"}
    fake_yt_instance.get_song_related.return_value = [{"title": "Other"}]
    code = run_cli(helper_mod, "related", "v1", monkeypatch=monkeypatch)
    assert code == 0
    fake_yt_instance.get_song_related.assert_called_once_with("rel_id")


def test_related_empty(helper_mod, fake_yt_instance, capsys, monkeypatch):
    fake_yt_instance.get_watch_playlist.return_value = {"related": None}
    code = run_cli(helper_mod, "related", "v1", monkeypatch=monkeypatch)
    assert code == 0
    body = json.loads(capsys.readouterr().out)
    assert body == {"error": "No related songs found"}


def test_watch_with_playlist_id_and_limit(helper_mod, fake_yt_instance, monkeypatch):
    fake_yt_instance.get_watch_playlist.return_value = {"tracks": []}
    code = run_cli(
        helper_mod, "watch", "v1", "--playlist-id", "PL123", "--limit", "5",
        monkeypatch=monkeypatch,
    )
    assert code == 0
    fake_yt_instance.get_watch_playlist.assert_called_once_with(
        "v1", limit=5, playlistId="PL123",
    )


# ─── rate ────────────────────────────────────────────────────────────────────

def test_rate_requires_auth(helper_mod, capsys, monkeypatch):
    code = run_cli(helper_mod, "rate", "v1", "LIKE", monkeypatch=monkeypatch)
    assert code == 1
    err = json.loads(capsys.readouterr().err)
    assert err["error"] == "Auth required"


def test_rate(authed, fake_yt_instance, capsys, monkeypatch):
    fake_yt_instance.rate_song.return_value = "STATUS_SUCCEEDED"
    code = run_cli(authed, "rate", "v1", "DISLIKE", monkeypatch=monkeypatch)
    assert code == 0
    body = json.loads(capsys.readouterr().out)
    assert body == {"status": "STATUS_SUCCEEDED", "videoId": "v1", "rating": "DISLIKE"}
    fake_yt_instance.rate_song.assert_called_once_with("v1", "DISLIKE")


# ─── subscribe ───────────────────────────────────────────────────────────────

def test_subscribe(authed, fake_yt_instance, monkeypatch):
    fake_yt_instance.subscribe_artists.return_value = "OK"
    code = run_cli(authed, "subscribe", "subscribe", "ch1", "ch2", monkeypatch=monkeypatch)
    assert code == 0
    fake_yt_instance.subscribe_artists.assert_called_once_with(["ch1", "ch2"])
    fake_yt_instance.unsubscribe_artists.assert_not_called()


def test_unsubscribe(authed, fake_yt_instance, monkeypatch):
    fake_yt_instance.unsubscribe_artists.return_value = "OK"
    code = run_cli(authed, "subscribe", "unsubscribe", "ch1", monkeypatch=monkeypatch)
    assert code == 0
    fake_yt_instance.unsubscribe_artists.assert_called_once_with(["ch1"])


# ─── charts / moods / mood-playlist / home ───────────────────────────────────

def test_charts_default_country(helper_mod, fake_yt_instance, monkeypatch):
    fake_yt_instance.get_charts.return_value = {"videos": []}
    code = run_cli(helper_mod, "charts", monkeypatch=monkeypatch)
    assert code == 0
    fake_yt_instance.get_charts.assert_called_once_with(country="ZZ")


def test_charts_explicit_country(helper_mod, fake_yt_instance, monkeypatch):
    fake_yt_instance.get_charts.return_value = {}
    code = run_cli(helper_mod, "charts", "--country", "BR", monkeypatch=monkeypatch)
    assert code == 0
    fake_yt_instance.get_charts.assert_called_once_with(country="BR")


def test_moods(helper_mod, fake_yt_instance, monkeypatch):
    fake_yt_instance.get_mood_categories.return_value = {}
    code = run_cli(helper_mod, "moods", monkeypatch=monkeypatch)
    assert code == 0
    fake_yt_instance.get_mood_categories.assert_called_once_with()


def test_mood_playlist(helper_mod, fake_yt_instance, monkeypatch):
    fake_yt_instance.get_mood_playlists.return_value = []
    code = run_cli(helper_mod, "mood-playlist", "ABCDEF", monkeypatch=monkeypatch)
    assert code == 0
    fake_yt_instance.get_mood_playlists.assert_called_once_with("ABCDEF")


def test_home_requires_auth(helper_mod, capsys, monkeypatch):
    code = run_cli(helper_mod, "home", monkeypatch=monkeypatch)
    assert code == 1


def test_home(authed, fake_yt_instance, monkeypatch):
    fake_yt_instance.get_home.return_value = []
    code = run_cli(authed, "home", "--limit", "10", monkeypatch=monkeypatch)
    assert code == 0
    fake_yt_instance.get_home.assert_called_once_with(limit=10)


# ─── history / taste ─────────────────────────────────────────────────────────

def test_history_list(authed, fake_yt_instance, monkeypatch):
    fake_yt_instance.get_history.return_value = []
    code = run_cli(authed, "history", monkeypatch=monkeypatch)
    assert code == 0
    fake_yt_instance.get_history.assert_called_once_with()


def test_history_remove(authed, fake_yt_instance, capsys, monkeypatch):
    fake_yt_instance.remove_history_items.return_value = "OK"
    code = run_cli(authed, "history", "remove", "tok1", "tok2", monkeypatch=monkeypatch)
    assert code == 0
    body = json.loads(capsys.readouterr().out)
    assert body == {"status": "OK"}
    fake_yt_instance.remove_history_items.assert_called_once_with(["tok1", "tok2"])


def test_history_remove_requires_tokens(authed, capsys, monkeypatch):
    code = run_cli(authed, "history", "remove", monkeypatch=monkeypatch)
    assert code == 1
    assert "feedback_tokens required" in capsys.readouterr().err


def test_taste_get(authed, fake_yt_instance, monkeypatch):
    fake_yt_instance.get_tasteprofile.return_value = {}
    code = run_cli(authed, "taste", "get", monkeypatch=monkeypatch)
    assert code == 0
    fake_yt_instance.get_tasteprofile.assert_called_once_with()


def test_taste_set(authed, fake_yt_instance, capsys, monkeypatch):
    fake_yt_instance.get_tasteprofile.return_value = {"some": "profile"}
    fake_yt_instance.set_tasteprofile.return_value = "OK"
    code = run_cli(
        authed, "taste", "set", "--artists", "Queen", "Pink Floyd",
        monkeypatch=monkeypatch,
    )
    assert code == 0
    body = json.loads(capsys.readouterr().out)
    assert body == {"status": "OK"}
    fake_yt_instance.set_tasteprofile.assert_called_once_with(
        ["Queen", "Pink Floyd"], {"some": "profile"},
    )


def test_taste_set_requires_artists(authed, capsys, monkeypatch):
    code = run_cli(authed, "taste", "set", monkeypatch=monkeypatch)
    assert code == 1
    assert "artists required" in capsys.readouterr().err


# ─── user / upload ───────────────────────────────────────────────────────────

def test_user(helper_mod, fake_yt_instance, monkeypatch):
    fake_yt_instance.get_user.return_value = {"name": "x"}
    code = run_cli(helper_mod, "user", "UC123", monkeypatch=monkeypatch)
    assert code == 0
    fake_yt_instance.get_user.assert_called_once_with("UC123")


def test_upload_list(authed, fake_yt_instance, monkeypatch):
    fake_yt_instance.get_library_upload_songs.return_value = []
    code = run_cli(authed, "upload", "list", "--limit", "9", monkeypatch=monkeypatch)
    assert code == 0
    fake_yt_instance.get_library_upload_songs.assert_called_once_with(limit=9)


def test_upload_upload(authed, fake_yt_instance, capsys, monkeypatch):
    fake_yt_instance.upload_song.return_value = "DONE"
    code = run_cli(
        authed, "upload", "upload", "--filepath", "/tmp/song.mp3",
        monkeypatch=monkeypatch,
    )
    assert code == 0
    body = json.loads(capsys.readouterr().out)
    assert body == {"status": "DONE"}
    fake_yt_instance.upload_song.assert_called_once_with("/tmp/song.mp3")


def test_upload_upload_requires_filepath(authed, capsys, monkeypatch):
    code = run_cli(authed, "upload", "upload", monkeypatch=monkeypatch)
    assert code == 1
    assert "filepath required" in capsys.readouterr().err


def test_upload_delete(authed, fake_yt_instance, monkeypatch):
    fake_yt_instance.delete_upload_entity.return_value = "OK"
    code = run_cli(
        authed, "upload", "delete", "--entity-id", "abc",
        monkeypatch=monkeypatch,
    )
    assert code == 0
    fake_yt_instance.delete_upload_entity.assert_called_once_with("abc")


def test_upload_delete_requires_entity(authed, capsys, monkeypatch):
    code = run_cli(authed, "upload", "delete", monkeypatch=monkeypatch)
    assert code == 1
    assert "entity-id required" in capsys.readouterr().err
