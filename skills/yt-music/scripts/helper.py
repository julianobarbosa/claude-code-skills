#!/usr/bin/env python3
"""
YouTube Music CLI Helper
Auth: <skill-root>/.yt-music/auth.json by default
Usage: uv run --with ytmusicapi python scripts/helper.py <command> [args]
"""

import argparse
import hashlib
import json
import os
import tempfile
import sys
import time
from pathlib import Path
from typing import NoReturn


def _resolve_data_dir() -> Path:
    configured = os.environ.get("YT_MUSIC_DATA_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parent.parent / ".yt-music"


SCRIPT_PATH = Path(__file__).resolve()
DATA_DIR = _resolve_data_dir()
AUTH_FILE = DATA_DIR / "auth.json"
AUTH_HEADER_KEYS = {"Authorization", "Cookie", "X-Goog-AuthUser", "x-origin"}


def auth_setup_instructions() -> dict:
    return {
        "required": True,
        "message": "Authentication is required before library, playlist, rating, upload, or account operations.",
        "agent_prompt": (
            "Authentication is required. Ask the user for either a Cookie string "
            "from a logged-in music.youtube.com request or a cookies JSON export file path."
        ),
        "language_policy": (
            "Mirror the user's language when replying. If the user's language is unclear, default to concise English."
        ),
        "reply_templates": {
            "short_en": (
                "You need to sign in to YouTube Music before I can continue with your "
                "library, playlists, account, uploads, or full playback.\n\n"
                "Please send me one of these:\n"
                "1. A Cookie string\n"
                "2. A cookies JSON file path"
            ),
            "cookie_string_en": (
                "Open a logged-in music.youtube.com page\n"
                "Open DevTools -> Network\n"
                "Filter /browse and reload the page\n"
                "Open any matching request\n"
                "Copy the Cookie request header value\n"
                "Send the full Cookie string back to me"
            ),
            "cookies_json_en": (
                "Use a cookie export extension such as Cookie-Editor on music.youtube.com\n"
                "Export cookies as JSON\n"
                "Save the exported file locally\n"
                "Send me the file path"
            ),
        },
        "cookie_string_steps": [
            "Open https://music.youtube.com in a logged-in browser session",
            "Open DevTools and go to the Network tab",
            "Filter requests with /browse and reload the page",
            "Open any matching request and copy the Cookie header value",
            "Send that Cookie string back to the agent",
        ],
        "cookies_json_steps": [
            "Open a cookie export extension such as Cookie-Editor on music.youtube.com",
            "Export cookies as JSON",
            "Save the JSON file locally",
            "Send the JSON file path back to the agent",
        ],
        "setup_commands": {
            "cookie_string": f"uv run --with ytmusicapi python {SCRIPT_PATH} auth setup --cookie '<cookie string>'",
            "cookies_json": f"uv run --with ytmusicapi python {SCRIPT_PATH} auth setup --cookies-file /path/to/cookies.json",
        },
    }


def _write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=path.parent) as tmp:
        json.dump(data, tmp, indent=2, ensure_ascii=False)
        tmp.write("\n")
    Path(tmp.name).replace(path)


def _sanitize_auth_headers(data: dict) -> dict:
    return {key: value for key, value in data.items() if key in AUTH_HEADER_KEYS and isinstance(value, str)}


def _migrate_legacy_auth_file() -> None:
    if not AUTH_FILE.exists():
        return
    try:
        raw = json.loads(AUTH_FILE.read_text())
    except Exception:
        return
    if not isinstance(raw, dict):
        return

    headers = _sanitize_auth_headers(raw)
    changed = set(raw) != set(headers)
    if changed:
        _write_json(AUTH_FILE, headers)


# ─── Auth ────────────────────────────────────────────────────────────────────

def build_auth_from_cookie(cookie_string: str) -> dict:
    """Compute SAPISIDHASH and build the auth headers dict from a raw cookie string."""
    sapisid = None
    for part in cookie_string.split(";"):
        part = part.strip()
        if part.startswith("SAPISID="):
            sapisid = part.split("=", 1)[1]
            break
    if not sapisid:
        # Try __Secure-3PAPISID as fallback
        for part in cookie_string.split(";"):
            part = part.strip()
            if part.startswith("__Secure-3PAPISID="):
                sapisid = part.split("=", 1)[1]
                break
    if not sapisid:
        bail("SAPISID not found in cookie string")

    ts = int(time.time())
    sha1 = hashlib.sha1(f"{ts} {sapisid} https://music.youtube.com".encode()).hexdigest()
    return {
        "Authorization": f"SAPISIDHASH {ts}_{sha1}",
        "Cookie": cookie_string.strip(),
        "X-Goog-AuthUser": "0",
        "x-origin": "https://music.youtube.com",
    }


def get_yt(require_auth=False):
    from ytmusicapi import YTMusic
    _migrate_legacy_auth_file()
    if AUTH_FILE.exists():
        return YTMusic(str(AUTH_FILE))
    if require_auth:
        details = {
            "error": "Auth required",
            "path": str(AUTH_FILE),
            **auth_setup_instructions(),
        }
        print(json.dumps(details, ensure_ascii=False, indent=2), file=sys.stderr)
        sys.exit(1)
    return YTMusic()  # unauthenticated — search/browse only


def bail(msg: str) -> NoReturn:
    print(json.dumps({"error": msg}, ensure_ascii=False), file=sys.stderr)
    sys.exit(1)


def out(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))


# ─── Auth commands ────────────────────────────────────────────────────────────

def cmd_auth(args):
    if args.action == "check":
        _migrate_legacy_auth_file()
        if AUTH_FILE.exists():
            out({"status": "ok", "path": str(AUTH_FILE)})
        else:
            out({
                "status": "missing",
                "path": str(AUTH_FILE),
                **auth_setup_instructions(),
            })

    elif args.action == "setup":
        if getattr(args, "cookies_file", None):
            _import_cookies_json(args.cookies_file)
        else:
            cookie = args.cookie or sys.stdin.read().strip()
            if not cookie:
                bail("No cookie provided. Pass --cookie '<string>' or --cookies-file cookies.json")
            headers = build_auth_from_cookie(cookie)
            _write_json(AUTH_FILE, headers)
            out({"status": "saved", "path": str(AUTH_FILE)})

    elif args.action == "account":
        yt = get_yt(require_auth=True)
        out(yt.get_account_info())

    elif args.action == "remove":
        if AUTH_FILE.exists():
            AUTH_FILE.unlink()
            out({"status": "removed"})
        else:
            out({"status": "already_missing"})


def _import_cookies_json(path: str) -> None:
    """
    Import a full cookie JSON export (array of cookie objects from a browser extension
    such as Cookie-Editor or EditThisCookie) and derive API auth headers.

    Stores:
    - auth.json: Cookie / Authorization headers for ytmusicapi
    """
    p = Path(path)
    if not p.exists():
        bail(f"File not found: {path}")
    try:
        raw = json.loads(p.read_text())
        if not isinstance(raw, list):
            bail("Expected a JSON array of cookie objects (e.g. exported from Cookie-Editor)")
    except json.JSONDecodeError as e:
        bail(f"Could not parse JSON: {e}")

    cookie_parts: list = []
    for c in raw:
        if not isinstance(c, dict) or "name" not in c or "value" not in c:
            continue
        domain = str(c.get("domain", "")).strip()
        if not domain or not any(d in domain for d in ["youtube.com", "google.com"]):
            continue
        if "youtube.com" in domain:
            cookie_parts.append(f"{c['name']}={c['value']}")

    if not cookie_parts:
        bail("No YouTube/Google cookies found in the file")

    cookie_str = "; ".join(cookie_parts)
    try:
        auth_data: dict = build_auth_from_cookie(cookie_str)
    except SystemExit:
        auth_data = {"Cookie": cookie_str, "X-Goog-AuthUser": "0",
                     "x-origin": "https://music.youtube.com"}

    _write_json(AUTH_FILE, _sanitize_auth_headers(auth_data))
    out({"status": "saved", "path": str(AUTH_FILE), "cookies_imported": len(cookie_parts)})


# ─── Search ───────────────────────────────────────────────────────────────────

def cmd_search(args):
    yt = get_yt()
    kwargs = dict(limit=args.limit)
    if args.type:
        kwargs["filter"] = args.type
    if args.library:
        kwargs["scope"] = "library"
    results = yt.search(args.query, **kwargs)
    out(results)


def cmd_suggest(args):
    yt = get_yt()
    out(yt.get_search_suggestions(args.query))


# ─── Library ──────────────────────────────────────────────────────────────────

def cmd_library(args):
    yt = get_yt(require_auth=True)
    sub = args.sub
    limit = args.limit

    dispatch = {
        "songs":         lambda: yt.get_library_songs(limit=limit, order=args.order),
        "liked":         lambda: yt.get_liked_songs(limit=limit),
        "playlists":     lambda: yt.get_library_playlists(limit=limit),
        "albums":        lambda: yt.get_library_albums(limit=limit, order=args.order),
        "artists":       lambda: yt.get_library_artists(limit=limit, order=args.order),
        "subscriptions": lambda: yt.get_library_subscriptions(limit=limit),
        "history":       lambda: yt.get_history(),
        "uploads":       lambda: yt.get_library_upload_songs(limit=limit),
    }

    if sub in dispatch:
        out(dispatch[sub]())
    else:
        # Overview: return counts/names of playlists
        playlists = yt.get_library_playlists(limit=limit)
        out({"playlists": playlists})


# ─── Playlist ─────────────────────────────────────────────────────────────────

def cmd_playlist(args):
    yt = get_yt(require_auth=True)
    action = args.action

    if action == "get":
        if not args.playlist_id:
            bail("playlist_id required for 'get'")
        out(yt.get_playlist(args.playlist_id, limit=args.limit))

    elif action == "create":
        if not args.title:
            bail("--title required for 'create'")
        video_ids = args.video_ids or None
        pl_id = yt.create_playlist(
            args.title,
            args.description or "",
            privacy_status=args.privacy or "PRIVATE",
            video_ids=video_ids,
        )
        out({"playlistId": pl_id, "title": args.title, "privacy": args.privacy or "PRIVATE"})

    elif action == "edit":
        if not args.playlist_id:
            bail("playlist_id required for 'edit'")
        kwargs = {}
        if args.title:
            kwargs["title"] = args.title
        if args.description is not None:
            kwargs["description"] = args.description
        if args.privacy:
            kwargs["privacyStatus"] = args.privacy
        result = yt.edit_playlist(args.playlist_id, **kwargs)
        out({"status": result})

    elif action == "delete":
        if not args.playlist_id:
            bail("playlist_id required for 'delete'")
        result = yt.delete_playlist(args.playlist_id)
        out({"status": result})

    elif action == "add":
        if not args.playlist_id or not args.video_ids:
            bail("playlist_id and video_ids required for 'add'")
        result = yt.add_playlist_items(
            args.playlist_id, args.video_ids,
            duplicates=args.duplicates,
        )
        out(result if isinstance(result, dict) else {"status": result})

    elif action == "add-playlist":
        # Add all songs from another playlist
        if not args.playlist_id or not args.source_playlist:
            bail("playlist_id and --source-playlist required for 'add-playlist'")
        result = yt.add_playlist_items(
            args.playlist_id,
            source_playlist=args.source_playlist,
        )
        out(result if isinstance(result, dict) else {"status": result})

    elif action == "remove":
        if not args.playlist_id or not args.video_ids:
            bail("playlist_id and video_ids required for 'remove'")
        pl = yt.get_playlist(args.playlist_id, limit=None)
        to_remove = [t for t in pl.get("tracks", []) if t.get("videoId") in args.video_ids]
        if not to_remove:
            out({"status": "not_found", "removed": 0})
            return
        result = yt.remove_playlist_items(args.playlist_id, to_remove)
        out({"status": result, "removed": len(to_remove)})

    elif action == "rate":
        if not args.playlist_id:
            bail("playlist_id required for 'rate'")
        result = yt.rate_playlist(args.playlist_id, args.rating or "LIKE")
        out({"status": result})


# ─── Artist ───────────────────────────────────────────────────────────────────

def cmd_artist(args):
    yt = get_yt()
    data = yt.get_artist(args.browse_id)
    out(data)


def cmd_artist_albums(args):
    yt = get_yt()
    # get_artist_albums needs channelId + params from get_artist response
    artist = yt.get_artist(args.browse_id)
    albums_data = artist.get("albums", {})
    browse_params = albums_data.get("params") if albums_data else None
    if browse_params:
        out(yt.get_artist_albums(args.browse_id, browse_params))
    else:
        out(albums_data.get("results", []))


# ─── Album ────────────────────────────────────────────────────────────────────

def cmd_album(args):
    yt = get_yt()
    # handle both browseId and playlistId
    browse_id = args.browse_id
    if browse_id.startswith("OLAK") or browse_id.startswith("PL"):
        browse_id = yt.get_album_browse_id(browse_id)
    out(yt.get_album(browse_id))


# ─── Song ─────────────────────────────────────────────────────────────────────

def cmd_song(args):
    yt = get_yt()
    out(yt.get_song(args.video_id))


def cmd_lyrics(args):
    yt = get_yt()
    watch = yt.get_watch_playlist(args.video_id)
    lyrics_id = watch.get("lyrics")
    if not lyrics_id:
        out({"error": "No lyrics available for this song"})
        return
    out(yt.get_lyrics(lyrics_id))


def cmd_related(args):
    yt = get_yt()
    watch = yt.get_watch_playlist(args.video_id)
    related_id = watch.get("related")
    if not related_id:
        out({"error": "No related songs found"})
        return
    out(yt.get_song_related(related_id))


def cmd_watch(args):
    yt = get_yt()
    kwargs = dict(limit=args.limit)
    if args.playlist_id:
        kwargs["playlistId"] = args.playlist_id
    out(yt.get_watch_playlist(args.video_id, **kwargs))


# ─── Rating & Library Status ──────────────────────────────────────────────────

def cmd_rate(args):
    yt = get_yt(require_auth=True)
    result = yt.rate_song(args.video_id, args.rating)
    out({"status": result, "videoId": args.video_id, "rating": args.rating})


# ─── Artist subscription ──────────────────────────────────────────────────────

def cmd_subscribe(args):
    yt = get_yt(require_auth=True)
    if args.action == "subscribe":
        result = yt.subscribe_artists(args.channel_ids)
    else:
        result = yt.unsubscribe_artists(args.channel_ids)
    out({"status": result})


# ─── Discover ─────────────────────────────────────────────────────────────────

def cmd_charts(args):
    yt = get_yt()
    out(yt.get_charts(country=args.country))


def cmd_moods(args):
    yt = get_yt()
    out(yt.get_mood_categories())


def cmd_mood_playlist(args):
    yt = get_yt()
    out(yt.get_mood_playlists(args.params))


def cmd_home(args):
    yt = get_yt(require_auth=True)
    out(yt.get_home(limit=args.limit))


# ─── History ──────────────────────────────────────────────────────────────────

def cmd_history(args):
    yt = get_yt(require_auth=True)
    if args.action == "list":
        out(yt.get_history())
    elif args.action == "remove":
        if not args.feedback_tokens:
            bail("feedback_tokens required for 'remove'")
        out({"status": yt.remove_history_items(args.feedback_tokens)})


# ─── Taste Profile ────────────────────────────────────────────────────────────

def cmd_taste(args):
    yt = get_yt(require_auth=True)
    if args.action == "get":
        out(yt.get_tasteprofile())
    elif args.action == "set":
        if not args.artists:
            bail("--artists required for 'set'")
        taste = yt.get_tasteprofile()
        result = yt.set_tasteprofile(args.artists, taste)
        out({"status": result})


# ─── User ─────────────────────────────────────────────────────────────────────

def cmd_user(args):
    yt = get_yt()
    out(yt.get_user(args.channel_id))


# ─── Uploads ──────────────────────────────────────────────────────────────────

def cmd_upload(args):
    yt = get_yt(require_auth=True)
    if args.action == "list":
        out(yt.get_library_upload_songs(limit=args.limit))
    elif args.action == "upload":
        if not args.filepath:
            bail("--filepath required for 'upload'")
        out({"status": yt.upload_song(args.filepath)})
    elif args.action == "delete":
        if not args.entity_id:
            bail("--entity-id required for 'delete'")
        out({"status": yt.delete_upload_entity(args.entity_id)})


# ─── Parser ───────────────────────────────────────────────────────────────────

def build_parser():
    p = argparse.ArgumentParser(
        prog="yt-music",
        description="YouTube Music CLI — wraps ytmusicapi",
    )
    sub = p.add_subparsers(dest="command", metavar="COMMAND")

    # auth
    pa = sub.add_parser("auth", help="Authentication management")
    pa.add_argument("action", choices=["check", "setup", "account", "remove"])
    pa.add_argument("--cookie", help="Raw Cookie header string (for setup)")
    pa.add_argument("--cookies-file", dest="cookies_file",
                    help="JSON cookie export from a browser extension (for setup, e.g. Cookie-Editor)")
    pa.set_defaults(func=cmd_auth)

    # search
    ps = sub.add_parser("search", help="Search YouTube Music")
    ps.add_argument("query")
    ps.add_argument("--type", "-t", choices=[
        "songs", "artists", "albums", "playlists",
        "videos", "podcasts", "episodes", "profiles",
    ])
    ps.add_argument("--limit", "-l", type=int, default=10)
    ps.add_argument("--library", action="store_true", help="Search within your library")
    ps.set_defaults(func=cmd_search)

    # suggest
    psg = sub.add_parser("suggest", help="Search autocomplete suggestions")
    psg.add_argument("query")
    psg.set_defaults(func=cmd_suggest)

    # library
    plib = sub.add_parser("library", help="Browse your library")
    plib.add_argument("sub", nargs="?", default="playlists",
                      choices=["songs", "liked", "playlists", "albums",
                               "artists", "subscriptions", "history", "uploads"])
    plib.add_argument("--limit", "-l", type=int, default=25)
    plib.add_argument("--order", choices=["a_to_z", "z_to_a", "recently_added"])
    plib.set_defaults(func=cmd_library)

    # playlist
    ppl = sub.add_parser("playlist", help="Playlist management")
    ppl.add_argument("action", choices=["get", "create", "edit", "delete",
                                         "add", "add-playlist", "remove", "rate"])
    ppl.add_argument("playlist_id", nargs="?")
    ppl.add_argument("video_ids", nargs="*")
    ppl.add_argument("--title")
    ppl.add_argument("--description")
    ppl.add_argument("--privacy", choices=["PUBLIC", "PRIVATE", "UNLISTED"])
    ppl.add_argument("--source-playlist", dest="source_playlist")
    ppl.add_argument("--rating", choices=["LIKE", "DISLIKE", "INDIFFERENT"])
    ppl.add_argument("--duplicates", action="store_true")
    ppl.add_argument("--limit", "-l", type=int, default=100)
    ppl.set_defaults(func=cmd_playlist)

    # artist
    par = sub.add_parser("artist", help="Artist profile")
    par.add_argument("browse_id")
    par.set_defaults(func=cmd_artist)

    paa = sub.add_parser("artist-albums", help="All albums by an artist")
    paa.add_argument("browse_id")
    paa.set_defaults(func=cmd_artist_albums)

    # album
    pal = sub.add_parser("album", help="Album details and tracklist")
    pal.add_argument("browse_id")
    pal.set_defaults(func=cmd_album)

    # song
    pso = sub.add_parser("song", help="Song metadata")
    pso.add_argument("video_id")
    pso.set_defaults(func=cmd_song)

    # lyrics
    ply = sub.add_parser("lyrics", help="Song lyrics")
    ply.add_argument("video_id")
    ply.set_defaults(func=cmd_lyrics)

    # related
    pre = sub.add_parser("related", help="Related songs")
    pre.add_argument("video_id")
    pre.set_defaults(func=cmd_related)

    # watch
    pwt = sub.add_parser("watch", help="'Up next' radio/recommendations")
    pwt.add_argument("video_id")
    pwt.add_argument("--playlist-id", dest="playlist_id")
    pwt.add_argument("--limit", "-l", type=int, default=10)
    pwt.set_defaults(func=cmd_watch)

    # rate
    prt = sub.add_parser("rate", help="Like / dislike / unlike a song")
    prt.add_argument("video_id")
    prt.add_argument("rating", choices=["LIKE", "DISLIKE", "INDIFFERENT"])
    prt.set_defaults(func=cmd_rate)

    # subscribe
    psb = sub.add_parser("subscribe", help="Follow / unfollow artists")
    psb.add_argument("action", choices=["subscribe", "unsubscribe"])
    psb.add_argument("channel_ids", nargs="+")
    psb.set_defaults(func=cmd_subscribe)

    # charts
    pch = sub.add_parser("charts", help="Trending charts")
    pch.add_argument("--country", "-c", default="ZZ",
                     help="ISO country code (ZZ = global)")
    pch.set_defaults(func=cmd_charts)

    # moods
    pmd = sub.add_parser("moods", help="Mood & genre categories")
    pmd.set_defaults(func=cmd_moods)

    pmdp = sub.add_parser("mood-playlist", help="Playlists for a mood/genre")
    pmdp.add_argument("params", help="params value from 'moods' output")
    pmdp.set_defaults(func=cmd_mood_playlist)

    # home
    phm = sub.add_parser("home", help="Personalised home feed")
    phm.add_argument("--limit", "-l", type=int, default=3)
    phm.set_defaults(func=cmd_home)

    # history
    phi = sub.add_parser("history", help="Listening history")
    phi.add_argument("action", nargs="?", default="list", choices=["list", "remove"])
    phi.add_argument("feedback_tokens", nargs="*")
    phi.set_defaults(func=cmd_history)

    # taste
    ptaste = sub.add_parser("taste", help="Taste profile preferences")
    ptaste.add_argument("action", choices=["get", "set"])
    ptaste.add_argument("--artists", nargs="+")
    ptaste.set_defaults(func=cmd_taste)

    # user
    pusr = sub.add_parser("user", help="Public user profile")
    pusr.add_argument("channel_id")
    pusr.set_defaults(func=cmd_user)

    # upload
    pup = sub.add_parser("upload", help="Personal music uploads")
    pup.add_argument("action", choices=["list", "upload", "delete"])
    pup.add_argument("--filepath")
    pup.add_argument("--entity-id", dest="entity_id")
    pup.add_argument("--limit", "-l", type=int, default=25)
    pup.set_defaults(func=cmd_upload)

    return p


def main():
    parser = build_parser()
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)
    args.func(args)


if __name__ == "__main__":
    main()
