"""Tests for the auth subsystem inside helper.py."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from .conftest import run_cli


# ─── build_auth_from_cookie ──────────────────────────────────────────────────

def test_build_auth_from_cookie_with_sapisid(helper_mod):
    """Happy path: full Cookie header with SAPISID yields all four required keys."""
    cookie = "Foo=1; SAPISID=mysapisidvalue; Bar=2"
    auth = helper_mod.build_auth_from_cookie(cookie)
    assert set(auth.keys()) == {"Authorization", "Cookie", "X-Goog-AuthUser", "x-origin"}
    assert auth["Cookie"] == cookie
    assert auth["x-origin"] == "https://music.youtube.com"
    assert auth["X-Goog-AuthUser"] == "0"
    # SAPISIDHASH format: "SAPISIDHASH <ts>_<sha1hex>"
    assert auth["Authorization"].startswith("SAPISIDHASH ")
    ts_hash = auth["Authorization"].split(" ", 1)[1]
    ts_str, sha = ts_hash.split("_", 1)
    expected = hashlib.sha1(
        f"{ts_str} mysapisidvalue https://music.youtube.com".encode()
    ).hexdigest()
    assert sha == expected


def test_build_auth_from_cookie_falls_back_to_3papisid(helper_mod):
    """When SAPISID is missing, __Secure-3PAPISID must be accepted as fallback."""
    cookie = "__Secure-3PAPISID=alt_value; SID=abc"
    auth = helper_mod.build_auth_from_cookie(cookie)
    assert auth["Cookie"] == cookie
    assert auth["Authorization"].startswith("SAPISIDHASH ")


def test_build_auth_from_cookie_missing_sapisid_exits(helper_mod, capsys):
    """No SAPISID and no __Secure-3PAPISID → bail with structured error JSON."""
    with pytest.raises(SystemExit) as ei:
        helper_mod.build_auth_from_cookie("Foo=1; Bar=2")
    assert ei.value.code == 1
    err = capsys.readouterr().err
    body = json.loads(err)
    assert "SAPISID" in body["error"]


# ─── auth_setup_instructions ─────────────────────────────────────────────────

def test_auth_setup_instructions_shape(helper_mod):
    """The bundled guidance must include all the artifacts the agent flow depends on."""
    info = helper_mod.auth_setup_instructions()
    assert info["required"] is True
    assert "agent_prompt" in info
    assert "language_policy" in info
    # English fallbacks
    for key in ("short_en", "cookie_string_en", "cookies_json_en"):
        assert key in info["reply_templates"]
    # Step lists
    assert isinstance(info["cookie_string_steps"], list) and info["cookie_string_steps"]
    assert isinstance(info["cookies_json_steps"], list) and info["cookies_json_steps"]
    # Concrete setup commands
    for key in ("cookie_string", "cookies_json"):
        assert key in info["setup_commands"]


# ─── _sanitize_auth_headers ──────────────────────────────────────────────────

def test_sanitize_auth_headers_keeps_only_allowed(helper_mod):
    raw = {
        "Authorization": "SAPISIDHASH 1_a",
        "Cookie": "x=1",
        "X-Goog-AuthUser": "0",
        "x-origin": "https://music.youtube.com",
        "garbage": "drop me",
        "another": 123,  # non-str also dropped
    }
    sanitized = helper_mod._sanitize_auth_headers(raw)
    assert sanitized == {
        "Authorization": "SAPISIDHASH 1_a",
        "Cookie": "x=1",
        "X-Goog-AuthUser": "0",
        "x-origin": "https://music.youtube.com",
    }


# ─── _migrate_legacy_auth_file ───────────────────────────────────────────────

def test_migrate_legacy_auth_file_strips_extra_keys(helper_mod, data_dir):
    legacy = {
        "Authorization": "SAPISIDHASH 1_a",
        "Cookie": "x=1",
        "X-Goog-AuthUser": "0",
        "x-origin": "https://music.youtube.com",
        "old_field": "remove me",
    }
    helper_mod.AUTH_FILE.write_text(json.dumps(legacy))
    helper_mod._migrate_legacy_auth_file()
    after = json.loads(helper_mod.AUTH_FILE.read_text())
    assert "old_field" not in after
    assert after["Authorization"] == "SAPISIDHASH 1_a"


def test_migrate_legacy_auth_file_noop_when_missing(helper_mod):
    """No file → nothing to do, no exception."""
    helper_mod._migrate_legacy_auth_file()
    assert not helper_mod.AUTH_FILE.exists()


def test_migrate_legacy_auth_file_ignores_invalid_json(helper_mod):
    helper_mod.AUTH_FILE.parent.mkdir(parents=True, exist_ok=True)
    helper_mod.AUTH_FILE.write_text("not-valid-json{")
    helper_mod._migrate_legacy_auth_file()
    # File unchanged because we can't parse it.
    assert helper_mod.AUTH_FILE.read_text() == "not-valid-json{"


# ─── cmd_auth check ──────────────────────────────────────────────────────────

def test_cmd_auth_check_missing(helper_mod, capsys, monkeypatch):
    code = run_cli(helper_mod, "auth", "check", monkeypatch=monkeypatch)
    assert code == 0
    body = json.loads(capsys.readouterr().out)
    assert body["status"] == "missing"
    # Hands the agent the full guidance payload.
    assert body["required"] is True
    assert "agent_prompt" in body


def test_cmd_auth_check_ok(helper_mod, capsys, monkeypatch):
    helper_mod.AUTH_FILE.parent.mkdir(parents=True, exist_ok=True)
    helper_mod.AUTH_FILE.write_text(json.dumps({
        "Authorization": "x", "Cookie": "y", "X-Goog-AuthUser": "0", "x-origin": "z",
    }))
    code = run_cli(helper_mod, "auth", "check", monkeypatch=monkeypatch)
    assert code == 0
    body = json.loads(capsys.readouterr().out)
    assert body == {"status": "ok", "path": str(helper_mod.AUTH_FILE)}


# ─── cmd_auth setup --cookie ─────────────────────────────────────────────────

def test_cmd_auth_setup_cookie_string_persists(helper_mod, capsys, monkeypatch):
    code = run_cli(
        helper_mod, "auth", "setup", "--cookie", "SAPISID=mysapisidvalue; Foo=1",
        monkeypatch=monkeypatch,
    )
    assert code == 0
    body = json.loads(capsys.readouterr().out)
    assert body == {"status": "saved", "path": str(helper_mod.AUTH_FILE)}
    persisted = json.loads(helper_mod.AUTH_FILE.read_text())
    assert persisted["Cookie"] == "SAPISID=mysapisidvalue; Foo=1"
    assert persisted["Authorization"].startswith("SAPISIDHASH ")


def test_cmd_auth_setup_empty_cookie_fails(helper_mod, capsys, monkeypatch):
    monkeypatch.setattr(sys, "stdin", _make_stdin(""))
    code = run_cli(helper_mod, "auth", "setup", monkeypatch=monkeypatch)
    assert code == 1
    err = capsys.readouterr().err
    assert "No cookie provided" in err


# ─── cmd_auth setup --cookies-file ───────────────────────────────────────────

def test_cmd_auth_setup_cookies_file_happy_path(helper_mod, tmp_path: Path, capsys, monkeypatch):
    cookies_json = tmp_path / "cookies.json"
    cookies_json.write_text(json.dumps([
        {"name": "SAPISID", "value": "mysapisidvalue", "domain": ".youtube.com"},
        {"name": "SID",      "value": "abc",           "domain": ".youtube.com"},
        {"name": "junk",     "value": "no",            "domain": "bing.com"},  # filtered
    ]))
    code = run_cli(
        helper_mod, "auth", "setup", "--cookies-file", str(cookies_json),
        monkeypatch=monkeypatch,
    )
    assert code == 0
    body = json.loads(capsys.readouterr().out)
    assert body["status"] == "saved"
    assert body["cookies_imported"] == 2
    persisted = json.loads(helper_mod.AUTH_FILE.read_text())
    assert "SAPISID=mysapisidvalue" in persisted["Cookie"]
    assert "SID=abc" in persisted["Cookie"]
    assert "junk=no" not in persisted["Cookie"]


def test_cmd_auth_setup_cookies_file_missing(helper_mod, capsys, monkeypatch):
    code = run_cli(
        helper_mod, "auth", "setup", "--cookies-file", "/no/such/file.json",
        monkeypatch=monkeypatch,
    )
    assert code == 1
    assert "File not found" in capsys.readouterr().err


def test_cmd_auth_setup_cookies_file_not_a_list(helper_mod, tmp_path, capsys, monkeypatch):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"not": "an array"}))
    code = run_cli(
        helper_mod, "auth", "setup", "--cookies-file", str(bad),
        monkeypatch=monkeypatch,
    )
    assert code == 1
    assert "JSON array" in capsys.readouterr().err


def test_cmd_auth_setup_cookies_file_invalid_json(helper_mod, tmp_path, capsys, monkeypatch):
    bad = tmp_path / "bad.json"
    bad.write_text("{not json")
    code = run_cli(
        helper_mod, "auth", "setup", "--cookies-file", str(bad),
        monkeypatch=monkeypatch,
    )
    assert code == 1
    assert "Could not parse JSON" in capsys.readouterr().err


def test_cmd_auth_setup_cookies_file_no_matching_cookies(helper_mod, tmp_path, capsys, monkeypatch):
    empty = tmp_path / "empty.json"
    empty.write_text(json.dumps([
        {"name": "x", "value": "1", "domain": "bing.com"},
    ]))
    code = run_cli(
        helper_mod, "auth", "setup", "--cookies-file", str(empty),
        monkeypatch=monkeypatch,
    )
    assert code == 1
    assert "No YouTube/Google cookies" in capsys.readouterr().err


def test_cmd_auth_setup_cookies_file_falls_back_when_no_sapisid(helper_mod, tmp_path, capsys, monkeypatch):
    """If neither SAPISID nor __Secure-3PAPISID is in the export, persist the headers
    we _do_ have (Cookie / X-Goog-AuthUser / x-origin) but skip Authorization."""
    cookies_json = tmp_path / "cookies.json"
    cookies_json.write_text(json.dumps([
        {"name": "SID", "value": "abc", "domain": ".youtube.com"},
    ]))
    code = run_cli(
        helper_mod, "auth", "setup", "--cookies-file", str(cookies_json),
        monkeypatch=monkeypatch,
    )
    assert code == 0
    body = json.loads(capsys.readouterr().out)
    assert body["status"] == "saved"
    persisted = json.loads(helper_mod.AUTH_FILE.read_text())
    assert "Authorization" not in persisted  # no SAPISID → no SAPISIDHASH
    assert persisted["Cookie"] == "SID=abc"
    assert persisted["x-origin"] == "https://music.youtube.com"


# ─── cmd_auth remove ─────────────────────────────────────────────────────────

def test_cmd_auth_remove_existing(helper_mod, capsys, monkeypatch):
    helper_mod.AUTH_FILE.parent.mkdir(parents=True, exist_ok=True)
    helper_mod.AUTH_FILE.write_text("{}")
    code = run_cli(helper_mod, "auth", "remove", monkeypatch=monkeypatch)
    assert code == 0
    body = json.loads(capsys.readouterr().out)
    assert body == {"status": "removed"}
    assert not helper_mod.AUTH_FILE.exists()


def test_cmd_auth_remove_when_absent(helper_mod, capsys, monkeypatch):
    code = run_cli(helper_mod, "auth", "remove", monkeypatch=monkeypatch)
    assert code == 0
    body = json.loads(capsys.readouterr().out)
    assert body == {"status": "already_missing"}


# ─── cmd_auth account ────────────────────────────────────────────────────────

def test_cmd_auth_account_requires_auth_file(helper_mod, capsys, monkeypatch):
    """Without auth.json, the require_auth path exits 1 with structured guidance."""
    code = run_cli(helper_mod, "auth", "account", monkeypatch=monkeypatch)
    assert code == 1
    err = json.loads(capsys.readouterr().err)
    assert err["error"] == "Auth required"
    assert "agent_prompt" in err


def test_cmd_auth_account_returns_account_info(
    helper_mod, fake_yt_instance, capsys, monkeypatch,
):
    helper_mod.AUTH_FILE.parent.mkdir(parents=True, exist_ok=True)
    helper_mod.AUTH_FILE.write_text(json.dumps({
        "Authorization": "x", "Cookie": "y", "X-Goog-AuthUser": "0", "x-origin": "z",
    }))
    fake_yt_instance.get_account_info.return_value = {"accountName": "Demo User"}
    code = run_cli(helper_mod, "auth", "account", monkeypatch=monkeypatch)
    assert code == 0
    body = json.loads(capsys.readouterr().out)
    assert body == {"accountName": "Demo User"}
    fake_yt_instance.get_account_info.assert_called_once_with()


# ─── helpers ─────────────────────────────────────────────────────────────────

class _StdinShim:
    def __init__(self, text: str) -> None:
        self._text = text

    def read(self) -> str:
        return self._text


def _make_stdin(text: str) -> _StdinShim:
    return _StdinShim(text)
