# PlayDiscover — Search → Play → Discover → Save

End-to-end "play me something and help me explore" flow. Composes `search`, `open`, `related`, and optionally `playlist add` into one orchestrated experience instead of asking the user to remember command names.

## When to use

- User says "play X", "put on some Y", "find me music like Z".
- User has heard a song and wants more like it.
- User wants a quick listening session without managing IDs themselves.

## Preconditions

- Auth: not required for `search` / `open` / `related`. **Required** for `playlist add` in step 5.
- Daemon: auto-starts on first `open` call. Run `Workflows/Setup.md` if `daemon-start` fails.

## Steps

### 1. Resolve the user's intent to a `videoId`

If the user gave a name, not an ID, search first:

```bash
uv run --with ytmusicapi python scripts/helper.py search "<query>" --type songs --limit 5
```

Present a numbered list (title — artist — album — duration). If results are ambiguous, ask which one. Capture the chosen `videoId`.

### 2. Open and play

```bash
uv run --with playwright python scripts/player.py open <videoId>
```

This auto-starts the daemon if needed. The first time, the user may have to click play once in the dedicated browser window if autoplay is blocked.

Confirm:

```bash
uv run --with playwright python scripts/player.py status
```

Expected response includes `playing: true` and a title/artist matching the resolved track.

### 3. Pull related tracks

```bash
uv run --with ytmusicapi python scripts/helper.py related <videoId>
```

Format the top 5 as a numbered table: index, title, artist, videoId. Offer the user three affordances:

1. Play one of them now (`player.py open <videoId>`)
2. Queue all of them into a "Now exploring" playlist (step 4–5)
3. Show lyrics for the current track (`helper.py lyrics <videoId>`)

### 4. (Optional) Create or reuse a discovery playlist

If the user wants to save what they're hearing:

```bash
# If they don't already have one
uv run --with ytmusicapi python scripts/helper.py playlist create --title "Now exploring — <seed track>"
```

Capture the returned `playlistId`. If they already have a "Now exploring" playlist, reuse it by listing:

```bash
uv run --with ytmusicapi python scripts/helper.py library playlists
```

### 5. (Optional) Add the seed + related tracks to the playlist

```bash
uv run --with ytmusicapi python scripts/helper.py playlist add <playlistId> <seedVideoId> <relatedVideoId...>
```

Pass `--duplicates` only if the user explicitly wants the same track added more than once.

### 6. Rate the seed track (optional)

```bash
uv run --with ytmusicapi python scripts/helper.py rate <seedVideoId> LIKE
```

This feeds YouTube Music's recommender for the user's future home feed.

## Output template

```text
▶ {{seed_title}} — {{seed_artist}}  (playing)

Related:
1. {{r1_title}} — {{r1_artist}}
2. {{r2_title}} — {{r2_artist}}
3. {{r3_title}} — {{r3_artist}}
4. {{r4_title}} — {{r4_artist}}
5. {{r5_title}} — {{r5_artist}}

Reply with a number to play, "save" to add all to a discovery playlist, or "lyrics" for the current track.
```

## Failure modes

| Symptom | Likely cause | Remediation |
|--------|--------------|-------------|
| `open` returns but `status` still shows `paused` | Autoplay blocked. | Tell user to click play once in the daemon-managed window; subsequent `open` calls usually autoplay. |
| `related` returns `No related songs found` | Some less-played tracks have no `related` watch_playlist entry. | Fall back to `watch <videoId> --limit 10` for a radio mix. |
| `playlist add` requires auth | Auth missing or expired. | Drop into `Workflows/Setup.md` step 2 and resume here at step 5. |

## Next suggestions

- `Workflows/BuildPlaylist.md` — promote this discovery session into a curated playlist.
- `Workflows/DiagnoseAuth.md` — if anything in step 4–5 fails with auth errors.
