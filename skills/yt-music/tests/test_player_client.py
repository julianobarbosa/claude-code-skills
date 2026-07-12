"""Tests for the player.py client (the thin HTTP wrapper around the daemon)."""

from __future__ import annotations

import io
import json
import sys
import urllib.error
from unittest.mock import MagicMock

import pytest

from .conftest import run_cli


# ─── _load_state / _clear_state ──────────────────────────────────────────────

def test_load_state_missing(player_mod):
    assert player_mod._load_state() is None


def test_load_state_valid(player_mod):
    player_mod.STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    payload = {"port": 1234, "token": "tok"}
    player_mod.STATE_FILE.write_text(json.dumps(payload))
    assert player_mod._load_state() == payload


def test_load_state_invalid_json(player_mod):
    player_mod.STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    player_mod.STATE_FILE.write_text("{not json")
    assert player_mod._load_state() is None


def test_load_state_non_dict_payload(player_mod):
    player_mod.STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    player_mod.STATE_FILE.write_text("[1, 2, 3]")
    assert player_mod._load_state() is None


def test_clear_state_missing_is_noop(player_mod):
    player_mod._clear_state()  # should not raise


def test_clear_state_removes_file(player_mod):
    player_mod.STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    player_mod.STATE_FILE.write_text("{}")
    player_mod._clear_state()
    assert not player_mod.STATE_FILE.exists()


# ─── _request ────────────────────────────────────────────────────────────────

class _FakeResponse:
    def __init__(self, payload: dict | list, status: int = 200) -> None:
        self._body = json.dumps(payload).encode("utf-8")
        self.status = status

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self) -> bytes:
        return self._body


def test_request_builds_url_and_headers(player_mod, monkeypatch):
    captured: dict = {}

    def fake_urlopen(req, timeout=5.0):
        captured["url"] = req.full_url
        captured["headers"] = dict(req.header_items())
        captured["data"] = req.data
        return _FakeResponse({"ok": True})

    monkeypatch.setattr(player_mod.urllib.request, "urlopen", fake_urlopen)
    result = player_mod._request(
        state={"port": 9999, "token": "TOK"},
        path="/command",
        payload={"action": "play"},
    )
    assert result == {"ok": True}
    assert captured["url"] == "http://127.0.0.1:9999/command"
    # urllib normalizes header names with capitalized first letter
    headers_lc = {k.lower(): v for k, v in captured["headers"].items()}
    assert headers_lc["x-ytmusic-token"] == "TOK"
    assert headers_lc["content-type"] == "application/json"
    assert headers_lc["accept"] == "application/json"
    assert json.loads(captured["data"].decode("utf-8")) == {"action": "play"}


def test_request_get_omits_content_type(player_mod, monkeypatch):
    captured: dict = {}

    def fake_urlopen(req, timeout=5.0):
        captured["headers"] = dict(req.header_items())
        captured["data"] = req.data
        return _FakeResponse({"ok": True})

    monkeypatch.setattr(player_mod.urllib.request, "urlopen", fake_urlopen)
    player_mod._request(state={"port": 1, "token": "T"}, path="/health")
    assert captured["data"] is None
    headers_lc = {k.lower(): v for k, v in captured["headers"].items()}
    assert "content-type" not in headers_lc


def test_request_rejects_non_dict_payload(player_mod, monkeypatch):
    def fake_urlopen(req, timeout=5.0):
        return _FakeResponse([1, 2, 3])

    monkeypatch.setattr(player_mod.urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(RuntimeError, match="non-object JSON"):
        player_mod._request(state={"port": 1, "token": "T"}, path="/health")


# ─── _probe ──────────────────────────────────────────────────────────────────

def test_probe_success(player_mod, monkeypatch):
    monkeypatch.setattr(
        player_mod,
        "_request",
        lambda state, path, timeout=2.0: {"daemon": "running"},
    )
    assert player_mod._probe({"port": 1, "token": "T"}) == {"daemon": "running"}


def test_probe_swallows_oserror(player_mod, monkeypatch):
    def boom(*a, **kw):
        raise OSError("conn refused")
    monkeypatch.setattr(player_mod, "_request", boom)
    assert player_mod._probe({"port": 1, "token": "T"}) is None


def test_probe_swallows_url_error(player_mod, monkeypatch):
    def boom(*a, **kw):
        raise urllib.error.URLError("nope")
    monkeypatch.setattr(player_mod, "_request", boom)
    assert player_mod._probe({"port": 1, "token": "T"}) is None


def test_probe_swallows_runtime_error(player_mod, monkeypatch):
    def boom(*a, **kw):
        raise RuntimeError("bad payload")
    monkeypatch.setattr(player_mod, "_request", boom)
    assert player_mod._probe({"port": 1, "token": "T"}) is None


# ─── _ensure_daemon ──────────────────────────────────────────────────────────

def test_ensure_daemon_reuses_healthy(player_mod, monkeypatch):
    player_mod.STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    player_mod.STATE_FILE.write_text(json.dumps({"port": 1, "token": "T"}))
    monkeypatch.setattr(player_mod, "_probe", lambda state: {"daemon": "running"})
    started = MagicMock()
    monkeypatch.setattr(player_mod, "_start_daemon", started)
    out = player_mod._ensure_daemon()
    assert out["health"] == {"daemon": "running"}
    started.assert_not_called()


def test_ensure_daemon_starts_new_when_probe_fails(player_mod, monkeypatch):
    player_mod.STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    player_mod.STATE_FILE.write_text(json.dumps({"port": 1, "token": "T"}))
    monkeypatch.setattr(player_mod, "_probe", lambda state: None)
    monkeypatch.setattr(player_mod, "_start_daemon", lambda: {"state": {"port": 2}, "health": {"daemon": "running"}})
    out = player_mod._ensure_daemon()
    assert out["state"]["port"] == 2
    # Stale state file should have been cleared.
    assert not player_mod.STATE_FILE.exists()


def test_ensure_daemon_starts_when_no_state(player_mod, monkeypatch):
    monkeypatch.setattr(player_mod, "_start_daemon", lambda: {"state": {"port": 5}, "health": {"daemon": "running"}})
    out = player_mod._ensure_daemon()
    assert out["state"]["port"] == 5


# ─── _wait_for_daemon ────────────────────────────────────────────────────────

def test_wait_for_daemon_times_out(player_mod, monkeypatch):
    monkeypatch.setattr(player_mod.time, "sleep", lambda _x: None)
    with pytest.raises(RuntimeError, match="Timed out"):
        player_mod._wait_for_daemon(deadline=player_mod.time.time() - 1)


def test_wait_for_daemon_returns_when_ready(player_mod, monkeypatch):
    player_mod.STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    player_mod.STATE_FILE.write_text(json.dumps({"port": 9, "token": "T"}))
    monkeypatch.setattr(player_mod, "_probe", lambda state: {"daemon": "running"})
    result = player_mod._wait_for_daemon(deadline=player_mod.time.time() + 5)
    assert result["state"]["port"] == 9
    assert result["health"]["daemon"] == "running"


# ─── _start_daemon ───────────────────────────────────────────────────────────

def test_start_daemon_spawns_subprocess_and_waits(player_mod, monkeypatch):
    popen_calls = []

    def fake_popen(cmd, **kwargs):
        popen_calls.append((cmd, kwargs))
        # Simulate daemon writing state + becoming healthy on next probe.
        player_mod.STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        player_mod.STATE_FILE.write_text(json.dumps({"port": 8888, "token": "T"}))
        return MagicMock()

    monkeypatch.setattr(player_mod.subprocess, "Popen", fake_popen)
    monkeypatch.setattr(player_mod, "_probe", lambda state: {"daemon": "running"})

    result = player_mod._start_daemon()
    assert result["state"]["port"] == 8888
    assert len(popen_calls) == 1
    cmd, kwargs = popen_calls[0]
    assert cmd[0] == sys.executable
    assert cmd[1].endswith("player_daemon.py")
    assert kwargs["start_new_session"] is True


# ─── _cmd_remote ─────────────────────────────────────────────────────────────

def test_cmd_remote_passes_action_payload(player_mod, capsys, monkeypatch):
    monkeypatch.setattr(player_mod, "_ensure_daemon",
                        lambda: {"state": {"port": 1, "token": "T"}, "health": {}})
    captured = {}

    def fake_request(state, path, payload=None, timeout=20.0):
        captured["path"] = path
        captured["payload"] = payload
        return {"action": "play", "ok": True}

    monkeypatch.setattr(player_mod, "_request", fake_request)
    code = run_cli(player_mod, "play", monkeypatch=monkeypatch)
    assert code == 0
    body = json.loads(capsys.readouterr().out)
    assert body == {"action": "play", "ok": True}
    assert captured["path"] == "/command"
    # play has no extra args
    assert captured["payload"] == {"action": "play"}


def test_cmd_remote_open_carries_video_id(player_mod, monkeypatch):
    monkeypatch.setattr(player_mod, "_ensure_daemon",
                        lambda: {"state": {"port": 1, "token": "T"}, "health": {}})
    captured = {}

    def fake_request(state, path, payload=None, timeout=20.0):
        captured["payload"] = payload
        return {}

    monkeypatch.setattr(player_mod, "_request", fake_request)
    code = run_cli(player_mod, "open", "abc123", monkeypatch=monkeypatch)
    assert code == 0
    assert captured["payload"]["action"] == "open"
    assert captured["payload"]["video_id"] == "abc123"


def test_cmd_remote_volume_passes_level(player_mod, monkeypatch):
    monkeypatch.setattr(player_mod, "_ensure_daemon",
                        lambda: {"state": {"port": 1, "token": "T"}, "health": {}})
    captured = {}
    monkeypatch.setattr(player_mod, "_request",
                        lambda *a, payload=None, **kw: (captured.update({"payload": payload}) or {}))
    code = run_cli(player_mod, "volume", "42", monkeypatch=monkeypatch)
    assert code == 0
    assert captured["payload"] == {"action": "volume", "level": 42}


def test_cmd_remote_seek_passes_seconds(player_mod, monkeypatch):
    monkeypatch.setattr(player_mod, "_ensure_daemon",
                        lambda: {"state": {"port": 1, "token": "T"}, "health": {}})
    captured = {}
    monkeypatch.setattr(player_mod, "_request",
                        lambda *a, payload=None, **kw: (captured.update({"payload": payload}) or {}))
    code = run_cli(player_mod, "seek", "12.5", monkeypatch=monkeypatch)
    assert code == 0
    assert captured["payload"] == {"action": "seek", "seconds": 12.5}


def test_cmd_remote_bails_on_http_error(player_mod, capsys, monkeypatch):
    monkeypatch.setattr(player_mod, "_ensure_daemon",
                        lambda: {"state": {"port": 1, "token": "T"}, "health": {}})

    def fake_request(*a, **kw):
        # Simulate a 400 from the daemon with an error body.
        body = io.BytesIO(b'{"error": "Player bar not found"}')
        err = urllib.error.HTTPError(
            url="http://127.0.0.1:1/command",
            code=400,
            msg="Bad Request",
            hdrs=None,
            fp=body,
        )
        raise err

    monkeypatch.setattr(player_mod, "_request", fake_request)
    code = run_cli(player_mod, "play", monkeypatch=monkeypatch)
    assert code == 1
    out = capsys.readouterr().out
    body = json.loads(out)
    assert "Player bar not found" in body["error"]


def test_cmd_remote_bails_on_oserror(player_mod, capsys, monkeypatch):
    monkeypatch.setattr(player_mod, "_ensure_daemon",
                        lambda: {"state": {"port": 1, "token": "T"}, "health": {}})

    def fake_request(*a, **kw):
        raise OSError("conn refused")

    monkeypatch.setattr(player_mod, "_request", fake_request)
    code = run_cli(player_mod, "play", monkeypatch=monkeypatch)
    assert code == 1
    body = json.loads(capsys.readouterr().out)
    assert "Could not reach the playback daemon" in body["error"]


# ─── daemon-start / daemon-status / daemon-stop ──────────────────────────────

def test_daemon_start_command(player_mod, capsys, monkeypatch):
    monkeypatch.setattr(player_mod, "_ensure_daemon",
                        lambda: {"state": {"port": 1}, "health": {"daemon": "running", "page_url": "x"}})
    code = run_cli(player_mod, "daemon-start", monkeypatch=monkeypatch)
    assert code == 0
    body = json.loads(capsys.readouterr().out)
    assert body["action"] == "daemon-start"
    assert body["daemon"] == "running"


def test_daemon_status_when_no_state(player_mod, capsys, monkeypatch):
    code = run_cli(player_mod, "daemon-status", monkeypatch=monkeypatch)
    assert code == 0
    body = json.loads(capsys.readouterr().out)
    assert body == {"action": "daemon-status", "daemon": "stopped"}


def test_daemon_status_when_probe_fails(player_mod, capsys, monkeypatch):
    player_mod.STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    player_mod.STATE_FILE.write_text(json.dumps({"port": 1, "token": "T"}))
    monkeypatch.setattr(player_mod, "_probe", lambda state: None)
    code = run_cli(player_mod, "daemon-status", monkeypatch=monkeypatch)
    assert code == 0
    body = json.loads(capsys.readouterr().out)
    assert body == {"action": "daemon-status", "daemon": "stopped"}
    # Stale state cleared
    assert not player_mod.STATE_FILE.exists()


def test_daemon_status_when_alive(player_mod, capsys, monkeypatch):
    player_mod.STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    player_mod.STATE_FILE.write_text(json.dumps({"port": 1, "token": "T"}))
    monkeypatch.setattr(player_mod, "_probe",
                        lambda state: {"daemon": "running", "player_loaded": False})
    code = run_cli(player_mod, "daemon-status", monkeypatch=monkeypatch)
    assert code == 0
    body = json.loads(capsys.readouterr().out)
    assert body["action"] == "daemon-status"
    assert body["daemon"] == "running"


def test_daemon_stop_when_no_state(player_mod, capsys, monkeypatch):
    code = run_cli(player_mod, "daemon-stop", monkeypatch=monkeypatch)
    assert code == 0
    body = json.loads(capsys.readouterr().out)
    assert body == {"action": "daemon-stop", "daemon": "stopped"}


def test_daemon_stop_with_state_succeeds(player_mod, capsys, monkeypatch):
    player_mod.STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    player_mod.STATE_FILE.write_text(json.dumps({"port": 1, "token": "T"}))

    def fake_request(state, path, payload=None, timeout=5.0):
        # Simulate daemon clearing its own state file on shutdown.
        if path == "/shutdown":
            try:
                player_mod.STATE_FILE.unlink()
            except FileNotFoundError:
                pass
            return {"action": "daemon-stop", "daemon": "stopping"}
        raise AssertionError(f"unexpected path: {path}")

    monkeypatch.setattr(player_mod, "_request", fake_request)
    monkeypatch.setattr(player_mod.time, "sleep", lambda _x: None)
    code = run_cli(player_mod, "daemon-stop", monkeypatch=monkeypatch)
    assert code == 0
    body = json.loads(capsys.readouterr().out)
    assert body["daemon"] == "stopping"
    assert not player_mod.STATE_FILE.exists()


def test_daemon_stop_handles_request_failure(player_mod, capsys, monkeypatch):
    player_mod.STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    player_mod.STATE_FILE.write_text(json.dumps({"port": 1, "token": "T"}))

    def fake_request(*a, **kw):
        raise OSError("conn refused")

    monkeypatch.setattr(player_mod, "_request", fake_request)
    code = run_cli(player_mod, "daemon-stop", monkeypatch=monkeypatch)
    assert code == 0
    body = json.loads(capsys.readouterr().out)
    assert body == {"action": "daemon-stop", "daemon": "stopped"}
    # Stale state file removed even though we couldn't reach daemon.
    assert not player_mod.STATE_FILE.exists()


# ─── parser ──────────────────────────────────────────────────────────────────

def test_player_no_action_prints_help(player_mod, capsys, monkeypatch):
    code = run_cli(player_mod, monkeypatch=monkeypatch)
    assert code == 0
    out = capsys.readouterr().out
    assert "open" in out
    assert "daemon-start" in out


def test_player_unknown_action_exits_two(player_mod, monkeypatch):
    code = run_cli(player_mod, "nonsense", monkeypatch=monkeypatch)
    assert code == 2


@pytest.mark.parametrize(
    "action",
    ["toggle", "play", "pause", "next", "prev", "status", "shuffle", "repeat"],
)
def test_player_zero_arg_actions_dispatch(player_mod, action, monkeypatch):
    """All control verbs with no args should route through _cmd_remote."""
    monkeypatch.setattr(player_mod, "_ensure_daemon",
                        lambda: {"state": {"port": 1, "token": "T"}, "health": {}})
    captured = {}
    monkeypatch.setattr(player_mod, "_request",
                        lambda *a, payload=None, **kw: (captured.update({"payload": payload}) or {}))
    code = run_cli(player_mod, action, monkeypatch=monkeypatch)
    assert code == 0
    assert captured["payload"] == {"action": action}
