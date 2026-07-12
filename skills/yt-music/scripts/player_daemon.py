#!/usr/bin/env python3
"""
Persistent Playwright browser daemon for YouTube Music playback control.
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import shutil
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

YTM_URL = "https://music.youtube.com"
YTM_DAEMON_HOST = "127.0.0.1"

KEYS = {
    "toggle": "k",
    "next": "Shift+N",
    "prev": "Shift+P",
}

SELECTORS = {
    "app": "ytmusic-app",
    "player_bar": "ytmusic-player-bar",
    "shuffle": ".shuffle",
    "repeat": ".repeat",
}


def _resolve_data_dir() -> Path:
    configured = os.environ.get("YT_MUSIC_DATA_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parent.parent / ".yt-music"


DATA_DIR = _resolve_data_dir()
PROFILE_DIR = DATA_DIR / "playwright-profile"
STATE_FILE = DATA_DIR / "player-daemon.json"


def _write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    tmp.replace(path)


def _remove_state_file(pid: int) -> None:
    try:
        raw = json.loads(STATE_FILE.read_text())
    except Exception:
        raw = None
    if isinstance(raw, dict) and raw.get("pid") == pid:
        try:
            STATE_FILE.unlink()
        except FileNotFoundError:
            pass


def _candidate_paths() -> list[str]:
    system = os.uname().sysname if hasattr(os, "uname") else ""
    if system == "Darwin":
        return [
            "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            str(Path.home() / "Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
        ]
    if os.name == "nt":
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        program_files = os.environ.get("PROGRAMFILES", "")
        program_files_x86 = os.environ.get("PROGRAMFILES(X86)", "")
        return [
            str(Path(local_app_data) / "Google/Chrome/Application/chrome.exe"),
            str(Path(program_files) / "Google/Chrome/Application/chrome.exe"),
            str(Path(program_files_x86) / "Google/Chrome/Application/chrome.exe"),
        ]
    return [
        "google-chrome",
        "google-chrome-stable",
        "chromium",
        "chromium-browser",
    ]


def _find_browser() -> str | None:
    for candidate in _candidate_paths():
        if Path(candidate).exists():
            return candidate
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    return None


def _browser_version(browser_path: str | None) -> str | None:
    if not browser_path:
        return None
    result = subprocess.run([browser_path, "--version"], capture_output=True, text=True, check=False)
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


class PlayerError(RuntimeError):
    pass


class YTMusicRuntime:
    def __init__(self, user_data_dir: Path):
        from playwright.sync_api import sync_playwright

        self._lock = threading.RLock()
        self.user_data_dir = user_data_dir
        self.browser_path = _find_browser()
        self.browser_version = _browser_version(self.browser_path)
        self._pw_cm = sync_playwright()
        self._pw = self._pw_cm.start()
        launch_kwargs: dict[str, Any] = {
            "user_data_dir": str(self.user_data_dir),
            "headless": False,
            "args": ["--start-maximized"],
            "no_viewport": True,
        }
        if self.browser_path:
            launch_kwargs["executable_path"] = self.browser_path
        self.context = self._pw.chromium.launch_persistent_context(**launch_kwargs)
        self.context.set_default_timeout(15000)
        self.page = self._ensure_page()
        self._ensure_ytm_loaded()

    def close(self) -> None:
        with self._lock:
            self.context.close()
            self._pw_cm.stop()

    def health(self) -> dict[str, Any]:
        with self._lock:
            page = self._ensure_page()
            player_loaded = self._has_player(page)
            return {
                "daemon": "running",
                "mode": "playwright-persistent",
                "browser_path": self.browser_path,
                "browser_version": self.browser_version,
                "profile_dir": str(self.user_data_dir),
                "page_url": page.url,
                "player_loaded": player_loaded,
                "playing": self._is_playing(page) if player_loaded else False,
            }

    def handle(self, payload: dict[str, Any]) -> dict[str, Any]:
        action = str(payload.get("action") or "").strip()
        if not action:
            raise PlayerError("Missing action")

        with self._lock:
            page = self._ensure_page()

            if action == "open":
                video_id = str(payload.get("video_id") or "").strip()
                if not video_id:
                    raise PlayerError("Missing video_id")
                return self._cmd_open(page, video_id)
            if action in {"toggle", "play", "pause", "next", "prev"}:
                return self._cmd_control(page, action)
            if action == "volume":
                return self._cmd_volume(page, int(payload.get("level", 0)))
            if action == "seek":
                return self._cmd_seek(page, float(payload.get("seconds", 0)))
            if action == "shuffle":
                return self._cmd_shuffle(page)
            if action == "repeat":
                return self._cmd_repeat(page)
            if action == "status":
                return self._cmd_status(page)
            raise PlayerError(f"Unsupported action: {action}")

    def _ensure_page(self):
        if getattr(self, "page", None) and not self.page.is_closed():
            return self.page
        for page in self.context.pages:
            if not page.is_closed() and "music.youtube.com" in page.url:
                self.page = page
                return page
        for page in self.context.pages:
            if not page.is_closed():
                self.page = page
                return page
        self.page = self.context.new_page()
        return self.page

    def _ensure_ytm_loaded(self) -> None:
        page = self._ensure_page()
        if "music.youtube.com" not in page.url:
            page.goto(YTM_URL, wait_until="domcontentloaded", timeout=20000)
        try:
            page.wait_for_selector(SELECTORS["app"], timeout=15000)
        except Exception:
            pass
        try:
            page.bring_to_front()
        except Exception:
            pass

    def _wait_for_player(self, page, timeout: int = 15000) -> None:
        try:
            page.wait_for_selector(SELECTORS["player_bar"], timeout=timeout)
        except Exception:
            raise PlayerError(
                "Player bar not found. Open music.youtube.com in the launched browser, sign in if needed, "
                "then retry."
            )

    def _has_player(self, page) -> bool:
        try:
            return bool(page.locator(SELECTORS["player_bar"]).count())
        except Exception:
            return False

    def _send_key(self, page, key: str) -> None:
        page.focus("body")
        page.keyboard.press(key)
        time.sleep(0.3)

    def _is_playing(self, page) -> bool:
        try:
            return bool(page.evaluate("""
                (() => {
                    const v = document.querySelector('video');
                    return v ? !v.paused : false;
                })()
            """))
        except Exception:
            return False

    def _empty_status(self, page) -> dict[str, Any]:
        return {
            "title": None,
            "artist": None,
            "playing": False,
            "position": "0:00",
            "duration": "0:00",
            "position_seconds": 0,
            "duration_seconds": 0,
            "volume": None,
            "page_url": page.url,
            "player_loaded": False,
        }

    def _get_status(self, page) -> dict[str, Any]:
        try:
            data = page.evaluate("""
                (() => {
                    const video = document.querySelector('video');
                    const titleEl = document.querySelector('.title.ytmusic-player-bar');
                    const artistEl = document.querySelector('.byline-wrapper.ytmusic-player-bar a');

                    const title = titleEl ? titleEl.innerText.trim() : null;
                    const artist = artistEl ? artistEl.innerText.trim() : null;
                    const cur = video ? Math.floor(video.currentTime) : 0;
                    const dur = video ? Math.floor(video.duration) || 0 : 0;
                    const fmt = s => {
                        const m = Math.floor(s / 60);
                        return m + ':' + (s % 60 + '').padStart(2, '0');
                    };

                    return {
                        title,
                        artist,
                        playing: video ? !video.paused : false,
                        position: fmt(cur),
                        duration: fmt(dur),
                        position_seconds: cur,
                        duration_seconds: dur,
                        volume: video ? Math.round(video.volume * 100) : null,
                    };
                })()
            """)
        except Exception as exc:
            raise PlayerError(str(exc)) from exc
        data["page_url"] = page.url
        data["player_loaded"] = self._has_player(page)
        return data

    def _attempt_start_playback(self, page) -> str:
        try:
            started = page.evaluate("""
                async () => {
                    const video = document.querySelector('video');
                    if (!video) return false;
                    try {
                        await video.play();
                        return !video.paused;
                    } catch {
                        return false;
                    }
                }
            """)
            if started:
                return "video.play()"
        except Exception:
            pass

        for method, action in [
            ("play_button", lambda: page.locator("tp-yt-paper-icon-button.play-pause-button").first.click(timeout=3000)),
            ("toggle_key", lambda: self._send_key(page, KEYS["toggle"])),
        ]:
            try:
                action()
                time.sleep(0.8)
                if self._is_playing(page):
                    return method
            except Exception:
                continue
        return "failed"

    def _ensure_playing(self, page, timeout_ms: int = 12000) -> tuple[bool, list[str]]:
        deadline = time.time() + (timeout_ms / 1000)
        actions: list[str] = []
        while time.time() < deadline:
            if self._is_playing(page):
                return True, actions
            action = self._attempt_start_playback(page)
            if action != "failed":
                actions.append(action)
            if self._is_playing(page):
                return True, actions
            time.sleep(1.0)
        return self._is_playing(page), actions

    def _cmd_open(self, page, video_id: str) -> dict[str, Any]:
        url = f"{YTM_URL}/watch?v={video_id}"
        page.goto(url, wait_until="domcontentloaded", timeout=20000)
        self._wait_for_player(page, timeout=20000)
        verified, recovery_actions = self._ensure_playing(page)
        return {
            "action": "open",
            "url": url,
            "mode": "playwright-daemon",
            "playback_verified": verified,
            "recovery_actions": recovery_actions,
            **self._get_status(page),
        }

    def _cmd_control(self, page, action: str) -> dict[str, Any]:
        self._ensure_ytm_loaded()
        self._wait_for_player(page)

        if action == "toggle":
            self._send_key(page, KEYS["toggle"])
            time.sleep(0.3)
        elif action == "play":
            if not self._is_playing(page):
                self._send_key(page, KEYS["toggle"])
                time.sleep(0.3)
                self._ensure_playing(page, timeout_ms=5000)
        elif action == "pause":
            if self._is_playing(page):
                self._send_key(page, KEYS["toggle"])
                time.sleep(0.3)
        elif action == "next":
            self._send_key(page, KEYS["next"])
            time.sleep(1.5)
        elif action == "prev":
            self._send_key(page, KEYS["prev"])
            time.sleep(1.5)

        return {"action": action, **self._get_status(page)}

    def _cmd_volume(self, page, level: int) -> dict[str, Any]:
        self._ensure_ytm_loaded()
        self._wait_for_player(page)
        level = max(0, min(100, level))
        result = page.evaluate(
            """
            (targetLevel) => {
                const v = document.querySelector('video');
                if (!v) return 'video_not_found';
                v.volume = targetLevel / 100;
                v.muted = false;
                return Math.round(v.volume * 100);
            }
            """,
            level,
        )
        return {"action": "volume", "level": level, "result": result, **self._get_status(page)}

    def _cmd_seek(self, page, seconds: float) -> dict[str, Any]:
        self._ensure_ytm_loaded()
        self._wait_for_player(page)
        seconds = max(0, seconds)
        result = page.evaluate(
            """
            (targetSeconds) => {
                const v = document.querySelector('video');
                if (!v) return 'video_not_found';
                v.currentTime = targetSeconds;
                return Math.floor(v.currentTime);
            }
            """,
            seconds,
        )
        time.sleep(0.3)
        return {"action": "seek", "target_seconds": seconds, "result": result, **self._get_status(page)}

    def _cmd_shuffle(self, page) -> dict[str, Any]:
        self._ensure_ytm_loaded()
        self._wait_for_player(page)
        try:
            btn = page.locator(SELECTORS["shuffle"])
            btn.click()
            time.sleep(0.3)
            active = btn.get_attribute("aria-checked") == "true"
        except Exception as exc:
            raise PlayerError(f"Could not find shuffle button: {exc}") from exc
        return {"action": "shuffle", "shuffle_on": active, **self._get_status(page)}

    def _cmd_repeat(self, page) -> dict[str, Any]:
        self._ensure_ytm_loaded()
        self._wait_for_player(page)
        try:
            btn = page.locator(SELECTORS["repeat"])
            btn.click()
            time.sleep(0.3)
            mode = btn.get_attribute("aria-label") or "unknown"
        except Exception as exc:
            raise PlayerError(f"Could not find repeat button: {exc}") from exc
        return {"action": "repeat", "mode": mode, **self._get_status(page)}

    def _cmd_status(self, page) -> dict[str, Any]:
        self._ensure_ytm_loaded()
        if not self._has_player(page):
            return {"action": "status", **self._empty_status(page)}
        return {"action": "status", **self._get_status(page)}


class RequestHandler(BaseHTTPRequestHandler):
    server: "PlayerHTTPServer"

    def log_message(self, format: str, *args) -> None:
        return

    def _auth_ok(self) -> bool:
        return self.headers.get("X-YTMUSIC-Token") == self.server.token

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0") or "0")
        raw = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise PlayerError(f"Invalid JSON payload: {exc}") from exc
        if not isinstance(data, dict):
            raise PlayerError("JSON payload must be an object")
        return data

    def _send(self, status: int, data: dict[str, Any]) -> None:
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        if not self._auth_ok():
            self._send(403, {"error": "Forbidden"})
            return
        if self.path != "/health":
            self._send(404, {"error": "Not found"})
            return
        self._send(200, self.server.runtime.health())

    def do_POST(self) -> None:
        if not self._auth_ok():
            self._send(403, {"error": "Forbidden"})
            return
        try:
            payload = self._read_json()
            if self.path == "/command":
                response = self.server.runtime.handle(payload)
                self._send(200, response)
                return
            if self.path == "/shutdown":
                self._send(200, {"action": "daemon-stop", "daemon": "stopping"})
                threading.Thread(target=self.server.shutdown, daemon=True).start()
                return
            self._send(404, {"error": "Not found"})
        except PlayerError as exc:
            self._send(400, {"error": str(exc)})
        except Exception as exc:
            self._send(500, {"error": f"Unhandled daemon error: {exc}"})


class PlayerHTTPServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, server_address, runtime: YTMusicRuntime, token: str):
        super().__init__(server_address, RequestHandler)
        self.runtime = runtime
        self.token = token


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="yt-music-player-daemon",
        description="Run the persistent Playwright daemon for YouTube Music playback control",
    )
    parser.add_argument("--host", default=YTM_DAEMON_HOST)
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--user-data-dir", type=Path, default=PROFILE_DIR)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.user_data_dir = args.user_data_dir.expanduser().resolve()
    args.user_data_dir.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    token = secrets.token_hex(16)
    runtime = YTMusicRuntime(args.user_data_dir)
    server = PlayerHTTPServer((args.host, args.port), runtime=runtime, token=token)

    state = {
        "pid": os.getpid(),
        "host": args.host,
        "port": server.server_address[1],
        "token": token,
        "profile_dir": str(args.user_data_dir),
        "started_at": int(time.time()),
        "mode": "playwright-persistent",
    }
    _write_json(STATE_FILE, state)

    try:
        server.serve_forever(poll_interval=0.5)
    finally:
        try:
            server.server_close()
        finally:
            runtime.close()
            _remove_state_file(os.getpid())


if __name__ == "__main__":
    main()
