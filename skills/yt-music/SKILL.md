---
name: yt-music
description: Operate YouTube Music via natural language. Search songs, artists, albums, playlists, lyrics, charts, recommendations, and control playback. Browse personal library, manage playlists, rate tracks, and inspect account info. Use this skill whenever the user asks about YouTube Music, wants to play music, manage playlists, search by song or artist name, inspect lyrics, or control playback.
version: 0.3.0
metadata:
  openclaw:
    requires:
      bins:
        - uv
      config:
        - .yt-music/auth.json
    skillKey: yt-music
    homepage: https://github.com/julianobarbosa/claude-code-skills
---

# YouTube Music Skill

Run bundled scripts from the skill root:

- `scripts/helper.py`: search, library, playlists, lyrics, ratings, account
- `scripts/player.py`: playback client and daemon management
- `scripts/player_daemon.py`: persistent Playwright browser daemon
- Runtime state is local to `./.yt-music/`
- Playback uses a dedicated Playwright-managed browser profile in `./.yt-music/playwright-profile`

## Workflow Routing

For multi-step or composed flows, route the user into a workflow file instead of orchestrating ad-hoc:

| User intent | Workflow file |
|-------------|---------------|
| First-time setup, expired auth, daemon not running | `Workflows/Setup.md` |
| "Play X / play something like Y / find me music" | `Workflows/PlayDiscover.md` |
| "Make a playlist of …", "save the charts", artist deep cut | `Workflows/BuildPlaylist.md` |
| Auth errors, daemon timeouts, silent playback, cookie issues | `Workflows/DiagnoseAuth.md` |
| "Run the tests", verify scripts after edits, CI smoke check | `Workflows/RunTests.md` |

Single-shot requests (one search, one rating, one `playlist get`) stay inline — no workflow needed.

## Decision flow

1. If the user gives names instead of IDs, search first.
2. For auth-required actions, run `auth check` first.
3. If auth is missing, switch into auth-guidance mode and do not continue yet.
4. Only after auth succeeds, execute the original command.
5. Format JSON into short tables or lists.

## ID Resolution

Use search to resolve `videoId`, `browseId`, or `playlistId`:

```bash
uv run --with yt-musicapi python scripts/helper.py search "<query>" --type songs --limit 5
uv run --with yt-musicapi python scripts/helper.py search "<query>" --type artists --limit 3
uv run --with yt-musicapi python scripts/helper.py search "<query>" --type albums --limit 3
```

If results are ambiguous, ask the user which one they want.

## Auth

Check auth before `library`, `playlist`, `rate`, `subscribe`, `home`, `history`, `taste`, `upload`, or `auth account`:

```bash
uv run --with yt-musicapi python scripts/helper.py auth check
```

If auth is missing, do not continue with the requested action yet.

You must explicitly guide the user to provide one of these:

- a Cookie string copied from a logged-in `music.youtube.com` request
- a cookies JSON export file path

This is a hard rule:

- Do not just say "auth missing"
- Do not stop after showing a shell error
- Do not ask a vague question like "please log in first"
- Do ask for the exact artifact you need next: Cookie string or cookies JSON file path
- Mirror the user's language when possible; if the user's language is unclear, default to concise English
- Treat the English templates below as defaults and translate or adapt them to match the user's language

Use this flow:

1. Tell the user authentication is required before you can access their library, playlists, account, uploads, or full playback.
2. Ask them to open `music.youtube.com` in a logged-in browser.
3. Offer two options:
   - Cookie string: open DevTools, Network, filter `/browse`, reload, open any matching request, copy the `Cookie` header value, send it back
   - Cookies JSON: export cookies for `music.youtube.com` with a cookie extension and send the file path back
4. When the user replies with either the cookie string or a JSON file path, run `auth setup`.
5. Retry the original command after `auth setup` succeeds.

Preferred default user-facing wording:

```text
You need to sign in to YouTube Music before I can access your library, playlists, account, uploads, or full playback.

Please send me one of these:
1. A Cookie string
2. A cookies JSON file path
```

Cookie string instructions:

```text
Open a logged-in music.youtube.com page
Open DevTools -> Network
Filter /browse and reload the page
Open any matching request
Copy the Cookie request header value
Send the full Cookie string back to me
```

Cookies JSON instructions:

```text
Use a cookie export extension such as Cookie-Editor on music.youtube.com
Export cookies as JSON
Save the exported file locally
Send me the file path
```

Setup commands:

```bash
uv run --with yt-musicapi python scripts/helper.py auth setup --cookie '<cookie string>'
uv run --with yt-musicapi python scripts/helper.py auth setup --cookies-file /path/to/cookies.json
```

## Common Commands

```bash
uv run --with yt-musicapi python scripts/helper.py search "<query>" [--type songs|artists|albums|playlists|videos]
uv run --with yt-musicapi python scripts/helper.py library playlists
uv run --with yt-musicapi python scripts/helper.py playlist get <playlistId>
uv run --with yt-musicapi python scripts/helper.py playlist create --title "<name>"
uv run --with yt-musicapi python scripts/helper.py playlist add <playlistId> <videoId...>
uv run --with yt-musicapi python scripts/helper.py lyrics <videoId>
uv run --with yt-musicapi python scripts/helper.py related <videoId>
uv run --with yt-musicapi python scripts/helper.py rate <videoId> LIKE|DISLIKE|INDIFFERENT
uv run --with yt-musicapi python scripts/helper.py charts [--country CN|US|KR|JP|ZZ]
```

Full command reference: `references/commands.md`

## Playback

Playback runs through a persistent Playwright browser daemon. The first playback command auto-starts a dedicated browser window and reuses it for later `open`, `play`, `pause`, `next`, `prev`, `seek`, `volume`, and `status` commands.

```bash
uv run --with playwright python scripts/player.py daemon-start
uv run --with playwright python scripts/player.py open <videoId>
uv run --with playwright python scripts/player.py play
uv run --with playwright python scripts/player.py pause
uv run --with playwright python scripts/player.py next
uv run --with playwright python scripts/player.py prev
uv run --with playwright python scripts/player.py status
uv run --with playwright python scripts/player.py volume <0-100>
uv run --with playwright python scripts/player.py seek <seconds>
uv run --with playwright python scripts/player.py daemon-status
uv run --with playwright python scripts/player.py daemon-stop
```

Important behavior:

- The daemon launches a dedicated persistent browser profile in `./.yt-music/playwright-profile`
- On first launch, the user may need to sign in to `music.youtube.com` in that browser window
- The user does not need to start Chrome or open a debugging port manually
- If `open <videoId>` loads the page but playback is still paused, autoplay was likely blocked and the user may need to click play once in the daemon-managed window
- `daemon-status` checks whether the background browser is alive without starting a new one

If playback commands fail, first verify:

- The daemon-managed browser window is still open
- The user is signed in at `music.youtube.com` in that browser window if the requested track requires it
- The requested song page can actually play in that browser session
- `./.yt-music/player-daemon.log` does not show a launch or Playwright error

## Output

- Search results: numbered table with title, artist, album, duration
- Playlist tracks: numbered list with title, artist, album
- Lyrics: print plain text
- Playback: `▶ {title} — {artist} ({position} / {duration})`
- Errors: state cause and next action

After success, suggest one natural next step such as play, add to playlist, show lyrics, or fetch related tracks.

## Gotchas

Accumulated lessons — the highest-density section of this skill. Add to it whenever a flow breaks in a non-obvious way.

- **`SAPISID` cookie quirk.** `auth setup --cookie` derives the API auth header by SHA1-hashing `SAPISID` against `time` and `music.youtube.com`. If the user pastes only one cookie line (not the full `Cookie:` header) the script bails with `SAPISID not found`. Always ask for the **full Cookie request header value**, not a single cookie pair. `__Secure-3PAPISID` is accepted as a fallback.
- **Cookies expire silently.** Google rotates session cookies. `auth check` still returns `ok` because the file exists, but the next authenticated call 401s. When that happens, run `auth remove` + re-do `Workflows/Setup.md` step 2 — do not retry blindly.
- **Autoplay block on first daemon launch.** Chrome's media policy blocks autoplay until the user interacts with the page once. The first `player.py open <id>` may load the page in `paused` state. Tell the user to click play once inside the daemon-managed window; subsequent opens autoplay because the gesture sticks to the profile.
- **Profile lock after a crash.** If a previous daemon crashed, `./.yt-music/playwright-profile/SingletonLock` may block re-launch. `daemon-stop` then deleting that lock file recovers without losing the signed-in session.
- **`playlist add-playlist` requires source ownership/access.** Cloning across users' playlists fails silently with no diff in `actions`. Confirm the user owns or has access to `--source-playlist` before reporting success.
- **`get_album` needs a browse ID, not a playlist ID.** The helper auto-converts `OLAK*` / `PL*` IDs via `get_album_browse_id`, but only if the user passes the correct flag — don't pass a `videoId` to `album`.
- **`charts --country ZZ` is "global"**, not a typo. The default. Use ISO alpha-2 (`BR`, `US`, `KR`, `JP`) for regional charts.
- **`related` can return empty.** Less-played tracks have no related-playlist entry. Fall back to `watch <videoId> --limit 10` for a radio mix instead of telling the user "nothing found".
- **`playlist remove` needs full track objects, not just `videoId`s.** The helper looks them up via `get_playlist` first; if `to_remove` is empty the script returns `not_found, removed: 0` rather than an error. Surface that to the user faithfully — they likely passed an ID for a track that isn't in the playlist.
- **`YT_MUSIC_DATA_DIR` overrides the default.** If a user reports auth files in an unexpected location, check whether they set this env var. Default is `<skill-root>/.yt-music/`.

## Examples

**Example 1 — Quick search and play (no auth needed for either).**
```
User: "Play Bohemian Rhapsody."
→ search "Bohemian Rhapsody" --type songs --limit 5
→ confirm pick with user if ambiguous
→ player.py open <videoId>
→ player.py status
→ offer: lyrics, related, save to playlist
```

**Example 2 — Build a charts playlist for Brazil.**
```
User: "Save this week's BR top 50 as a playlist."
→ route to Workflows/BuildPlaylist.md (Mode C)
→ auth check (required for playlist create/add)
→ charts --country BR
→ extract top 50 videoIds
→ playlist create --title "BR Top 50 — <date>" --privacy PRIVATE
→ playlist add <playlistId> <videoIds...>
```

**Example 3 — Auth failure mid-flow.**
```
User: "Add this track to my Liked playlist."
→ playlist add returns 401
→ route to Workflows/DiagnoseAuth.md (Symptom 2)
→ auth remove → Workflows/Setup.md step 2
→ retry original playlist add
```
