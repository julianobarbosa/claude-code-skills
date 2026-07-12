# DiagnoseAuth — Triage Auth and Daemon Failures

Run when any command surfaces an auth error, a daemon timeout, or unexpected playback silence. Goal: get the user from a broken state back to a usable state without guessing.

## Decision tree

### Symptom 1: `auth check` returns `status: "missing"`

→ Run `Workflows/Setup.md` from step 2. Do not proceed with the original request until `auth check` returns `ok`.

### Symptom 2: `auth check` returns `ok` but `library`, `playlist`, or `home` fails with HTTP 401/403 / "Unauthorized"

The stored cookie has expired (Google sessions rotate). Fix:

```bash
uv run --with ytmusicapi python scripts/helper.py auth remove
```

Then re-run `Workflows/Setup.md` step 2 with a fresh cookie copy from a currently-logged-in `music.youtube.com` browser tab.

### Symptom 3: `auth setup --cookie '…'` errors with `SAPISID not found in cookie string`

The pasted value is missing the `SAPISID=...` segment (or its `__Secure-3PAPISID` fallback). Causes:

- The user copied only one cookie line (e.g., from "Application" pane) instead of the full `Cookie:` request header.
- The user's session has third-party cookies disabled and Google never set SAPISID.

Remediation:

1. Reload `music.youtube.com` in the logged-in tab.
2. Open DevTools → Network → filter `/browse` → click a matching request → copy the entire **Cookie** request header (right-click → "Copy value").
3. Re-run `auth setup --cookie '<full Cookie header>'`.

### Symptom 4: `auth setup --cookies-file …` errors with `No YouTube/Google cookies found in the file`

The export was scoped to the wrong domain. Re-export with the cookie extension targeting `music.youtube.com` (or `youtube.com` — both domains are accepted).

### Symptom 5: `player.py daemon-start` times out (25s)

Inspect the launch log:

```bash
tail -n 50 ./.yt-music/player-daemon.log
```

Common causes:

| Log signature | Fix |
|--------------|------|
| `Executable doesn't exist at …chromium…` | `uv run --with playwright python -m playwright install chromium` |
| `Address already in use` | A previous daemon is bound to the port. Run `uv run --with playwright python scripts/player.py daemon-stop` then retry. |
| `Profile is in use by another process` | A prior crash left a lock in `./.yt-music/playwright-profile`. Stop any stray Chromium owned by the daemon and remove the `SingletonLock` file in that profile dir. |

### Symptom 6: `player.py open <videoId>` succeeds but `status` shows `paused` or no track

Autoplay was blocked by Chrome's media policy on first launch. Fix once:

1. Switch focus to the daemon-managed Chromium window (it's labeled "music.youtube.com").
2. Click the page once.
3. Re-run `player.py status`.

Subsequent `open` calls should autoplay because the user gesture is now recorded for that profile.

### Symptom 7: `player.py status` returns reachable but track info is empty

The daemon is alive but the page hasn't navigated yet. Re-run `player.py open <videoId>`.

### Symptom 8: Playback works but only short previews play (~30 seconds)

The daemon-managed Chromium isn't signed in. Sign in once inside that window — the persistent profile in `./.yt-music/playwright-profile` keeps the session afterwards.

## Hard reset (last resort)

Only if every step above failed and the user agrees to lose persistent playback state:

```bash
uv run --with playwright python scripts/player.py daemon-stop
rm -rf ./.yt-music/playwright-profile ./.yt-music/player-daemon.json ./.yt-music/player-daemon.log
uv run --with playwright python scripts/player.py daemon-start
```

The user will need to sign in once inside the new daemon window.

## Output template

```text
🩺 Diagnosis: {{symptom_id}}
🔧 Action taken: {{remediation_summary}}
✅ State now: {{verified_state}}
```

## Next suggestions

- Re-run the original command that failed.
- Drop into `Workflows/Setup.md` if state was reset.
