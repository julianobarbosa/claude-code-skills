# yt-music

A lightweight `SKILL.md` skill for controlling YouTube Music via natural language.

## Install

Any agent that supports `SKILL.md`-style skills can install this folder directly.

Paste the following into your agent

> `Install the yt-music skill from https://github.com/kadaliao/yt-music`

## Runtime Layout

```text
yt-music/
├── SKILL.md
├── scripts/
│   ├── helper.py
│   ├── player.py
│   └── player_daemon.py
├── references/
│   └── commands.md
└── .yt-music/
    ├── auth.json
    ├── player-daemon.json
    ├── player-daemon.log
    └── playwright-profile/
```

By default:

- `scripts/helper.py` stores API auth headers in `./.yt-music/auth.json`
- `scripts/player.py` is a thin client that auto-starts or reuses a persistent playback daemon
- `scripts/player_daemon.py` holds the long-lived Playwright browser and its dedicated profile

If needed, you can override the runtime data directory with `YT_MUSIC_DATA_DIR`.

## Local Usage

From the skill root:

```bash
uv run --with ytmusicapi python scripts/helper.py auth check
uv run --with playwright python scripts/player.py status
```

## Auth Setup

Cookie string:

```bash
uv run --with ytmusicapi python scripts/helper.py auth setup --cookie '<cookie string>'
```

Cookie JSON export:

```bash
uv run --with ytmusicapi python scripts/helper.py auth setup --cookies-file /path/to/cookies.json
```

Verify:

```bash
uv run --with ytmusicapi python scripts/helper.py auth check
```

## Playback Modes

`scripts/player.py` talks to a persistent Playwright daemon.
Regular playback commands auto-start a dedicated browser window on first use and then reuse the same browser session.

Examples:

```bash
uv run --with playwright python scripts/player.py daemon-start
uv run --with playwright python scripts/player.py open <videoId>
uv run --with playwright python scripts/player.py status
uv run --with playwright python scripts/player.py next
uv run --with playwright python scripts/player.py daemon-status
uv run --with playwright python scripts/player.py daemon-stop
```

## Notes

- `uv` is required
- `ytmusicapi` is pulled on demand via `uv run --with ytmusicapi ...`
- `playwright` is pulled on demand via `uv run --with playwright ...`
- The first playback command opens a dedicated browser profile under `./.yt-music/playwright-profile`
- If `open <videoId>` loads a track but does not start audio, autoplay was likely blocked and the user may need to click play once in the daemon-managed browser window
- `daemon-status` reports whether the background browser daemon is alive without launching a new browser

## ClawHub Notes

- Bump `version` in `SKILL.md` for every published release
- Publish from the skill root directory
- ClawHub-published skills are distributed under ClawHub's platform terms
