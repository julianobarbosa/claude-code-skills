# Setup — First-Time Auth + Playback Daemon

Run this the first time a user installs the skill or after `auth check` reports `missing`. Goal: leave the user able to call any auth-gated command (`library`, `playlist`, `rate`, `home`, `history`, `taste`, `upload`, `auth account`) and start playback without further setup.

## Preconditions

- `uv` is on PATH (the skill installs `ytmusicapi` and `playwright` on demand via `uv run --with`).
- The user has a logged-in YouTube Music browser session somewhere they can copy a cookie from.

## Steps

### 1. Probe current auth state

```bash
uv run --with ytmusicapi python scripts/helper.py auth check
```

Branch on the JSON response:

- `status: "ok"` → skip to step 4 (daemon start).
- `status: "missing"` → continue to step 2.

### 2. Ask the user for one credential artifact

Pick a wording that mirrors the user's language. Default English template:

```text
You need to sign in to YouTube Music before I can access your library, playlists,
account, uploads, or full playback.

Please send me one of these:
1. A Cookie string copied from a logged-in music.youtube.com request
2. A cookies JSON file path exported from a browser cookie extension
```

If the user does not yet know how to obtain either, send the matching mini-guide from `SKILL.md` (Cookie string instructions / Cookies JSON instructions).

### 3. Persist the credential

Cookie string:

```bash
uv run --with ytmusicapi python scripts/helper.py auth setup --cookie '<cookie string>'
```

Cookies JSON file path:

```bash
uv run --with ytmusicapi python scripts/helper.py auth setup --cookies-file /path/to/cookies.json
```

Verify it stuck:

```bash
uv run --with ytmusicapi python scripts/helper.py auth check
```

Expected: `status: "ok"`.

### 4. Start the playback daemon

```bash
uv run --with playwright python scripts/player.py daemon-start
```

Verify without re-launching:

```bash
uv run --with playwright python scripts/player.py daemon-status
```

Expected: a JSON object with `daemon: "running"` (or equivalent — current daemon returns a health body, not the literal stopped sentinel).

### 5. Confirm account binding

```bash
uv run --with ytmusicapi python scripts/helper.py auth account
```

If this returns the expected account name, setup is complete.

## Failure modes

| Symptom | Likely cause | Remediation |
|--------|--------------|-------------|
| `SAPISID not found in cookie string` | The pasted Cookie header is partial. | Ask for the full `Cookie:` header value, not just one cookie line. |
| `No YouTube/Google cookies found in the file` | JSON export came from a non-YT domain. | Re-export cookies specifically from `music.youtube.com`. |
| `Timed out waiting for the playback daemon to start` | Playwright never finished launching. | Inspect `./.yt-music/player-daemon.log`; usually a missing Chromium download — `uv run --with playwright python -m playwright install chromium`. |
| `auth check` still `missing` after `auth setup` | Auth file written to an unexpected dir. | Confirm `YT_MUSIC_DATA_DIR` is unset or points where you expect; default is `<skill-root>/.yt-music/auth.json`. |

## Output template

```text
✅ Auth ok ({{account_name}})
✅ Playback daemon running on port {{port}}
```

## Next suggestions

- Try `Workflows/PlayDiscover.md` to play something and explore related tracks.
- Try `Workflows/BuildPlaylist.md` to compose a fresh playlist from search or charts.
