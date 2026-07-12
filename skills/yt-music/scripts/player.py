#!/usr/bin/env python3
"""
YouTube Music playback client backed by a persistent Playwright daemon.

Regular playback commands auto-start the daemon when needed.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, NoReturn

YTM_DAEMON_HOST = "127.0.0.1"
YTM_DAEMON_START_TIMEOUT = 25.0


def _resolve_data_dir() -> Path:
    configured = os.environ.get("YT_MUSIC_DATA_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parent.parent / ".yt-music"


SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = _resolve_data_dir()
STATE_FILE = DATA_DIR / "player-daemon.json"
LOG_FILE = DATA_DIR / "player-daemon.log"
DAEMON_SCRIPT = SCRIPT_DIR / "player_daemon.py"


def bail(msg: str) -> NoReturn:
    print(json.dumps({"error": msg}, ensure_ascii=False))
    sys.exit(1)


def out(data: dict[str, Any]) -> None:
    print(json.dumps(data, ensure_ascii=False, indent=2))


def _load_state() -> dict[str, Any] | None:
    if not STATE_FILE.exists():
        return None
    try:
        raw = json.loads(STATE_FILE.read_text())
    except Exception:
        return None
    return raw if isinstance(raw, dict) else None


def _clear_state() -> None:
    try:
        STATE_FILE.unlink()
    except FileNotFoundError:
        pass


def _request(
    state: dict[str, Any],
    path: str,
    payload: dict[str, Any] | None = None,
    timeout: float = 5.0,
) -> dict[str, Any]:
    url = f"http://{YTM_DAEMON_HOST}:{state['port']}{path}"
    body = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {
        "Accept": "application/json",
        "X-YTMUSIC-Token": str(state.get("token", "")),
    }
    if body is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if not isinstance(data, dict):
        raise RuntimeError("Daemon returned a non-object JSON payload")
    return data


def _probe(state: dict[str, Any]) -> dict[str, Any] | None:
    try:
        return _request(state, "/health", timeout=2.0)
    except (OSError, urllib.error.URLError, urllib.error.HTTPError, RuntimeError, json.JSONDecodeError):
        return None


def _wait_for_daemon(deadline: float) -> dict[str, Any]:
    while time.time() < deadline:
        state = _load_state()
        if state:
            health = _probe(state)
            if health:
                return {"state": state, "health": health}
        time.sleep(0.4)
    raise RuntimeError(
        "Timed out waiting for the playback daemon to start. Check .yt-music/player-daemon.log for details."
    )


def _start_daemon() -> dict[str, Any]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DAEMON_SCRIPT.exists():
        raise RuntimeError(f"Daemon script not found: {DAEMON_SCRIPT}")

    with LOG_FILE.open("ab") as log_file:
        subprocess.Popen(
            [sys.executable, str(DAEMON_SCRIPT)],
            cwd=str(SCRIPT_DIR),
            stdin=subprocess.DEVNULL,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True,
            env=os.environ.copy(),
        )

    return _wait_for_daemon(time.time() + YTM_DAEMON_START_TIMEOUT)


def _ensure_daemon() -> dict[str, Any]:
    state = _load_state()
    if state:
        health = _probe(state)
        if health:
            return {"state": state, "health": health}
        _clear_state()
    return _start_daemon()


def _cmd_remote(args: argparse.Namespace) -> None:
    daemon = _ensure_daemon()
    payload: dict[str, Any] = {"action": args.action}
    if hasattr(args, "video_id"):
        payload["video_id"] = args.video_id
    if hasattr(args, "level"):
        payload["level"] = args.level
    if hasattr(args, "seconds"):
        payload["seconds"] = args.seconds

    try:
        response = _request(daemon["state"], "/command", payload=payload, timeout=20.0)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        bail(detail or f"Daemon request failed: HTTP {exc.code}")
    except (OSError, urllib.error.URLError, RuntimeError, json.JSONDecodeError) as exc:
        bail(f"Could not reach the playback daemon: {exc}")
    out(response)


def _cmd_daemon_start(args: argparse.Namespace) -> None:
    daemon = _ensure_daemon()
    out({"action": "daemon-start", **daemon["health"]})


def _cmd_daemon_status(args: argparse.Namespace) -> None:
    state = _load_state()
    if not state:
        out({"action": "daemon-status", "daemon": "stopped"})
        return
    health = _probe(state)
    if not health:
        _clear_state()
        out({"action": "daemon-status", "daemon": "stopped"})
        return
    out({"action": "daemon-status", **health})


def _cmd_daemon_stop(args: argparse.Namespace) -> None:
    state = _load_state()
    if not state:
        out({"action": "daemon-stop", "daemon": "stopped"})
        return

    try:
        response = _request(state, "/shutdown", payload={"action": "daemon-stop"}, timeout=5.0)
    except (OSError, urllib.error.URLError, urllib.error.HTTPError, RuntimeError, json.JSONDecodeError):
        _clear_state()
        out({"action": "daemon-stop", "daemon": "stopped"})
        return

    deadline = time.time() + 5.0
    while time.time() < deadline:
        if not STATE_FILE.exists():
            break
        time.sleep(0.2)
    _clear_state()
    out(response)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="yt-music-player",
        description="Control YouTube Music playback via a persistent Playwright browser daemon",
    )
    parser.add_argument("--chrome-port", help=argparse.SUPPRESS)
    sub = parser.add_subparsers(dest="action", metavar="ACTION")

    open_cmd = sub.add_parser("open", help="Open and play a song by videoId")
    open_cmd.add_argument("video_id")
    open_cmd.set_defaults(func=_cmd_remote)

    for name, help_text in [
        ("toggle", "Toggle play/pause"),
        ("play", "Resume playback"),
        ("pause", "Pause playback"),
        ("next", "Skip to next track"),
        ("prev", "Go to previous track"),
        ("status", "Show current playback status"),
        ("shuffle", "Toggle shuffle mode"),
        ("repeat", "Cycle repeat mode"),
    ]:
        cmd = sub.add_parser(name, help=help_text)
        cmd.set_defaults(func=_cmd_remote)

    volume_cmd = sub.add_parser("volume", help="Set volume (0-100)")
    volume_cmd.add_argument("level", type=int)
    volume_cmd.set_defaults(func=_cmd_remote)

    seek_cmd = sub.add_parser("seek", help="Seek to position in seconds")
    seek_cmd.add_argument("seconds", type=float)
    seek_cmd.set_defaults(func=_cmd_remote)

    daemon_start = sub.add_parser("daemon-start", help="Start the persistent playback daemon")
    daemon_start.set_defaults(func=_cmd_daemon_start)

    daemon_status = sub.add_parser("daemon-status", help="Show daemon status without auto-starting it")
    daemon_status.set_defaults(func=_cmd_daemon_status)

    daemon_stop = sub.add_parser("daemon-stop", help="Stop the persistent playback daemon")
    daemon_stop.set_defaults(func=_cmd_daemon_stop)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if not args.action:
        parser.print_help()
        sys.exit(0)
    args.func(args)


if __name__ == "__main__":
    main()
