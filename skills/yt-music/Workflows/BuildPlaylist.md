# BuildPlaylist — Compose a Playlist from Search, Artist, or Charts

Author a fresh playlist by composing `playlist create` with `search`, `artist-albums`, or `charts` instead of bouncing the user through raw `videoId` lists.

## When to use

- User asks to "make a playlist of <theme>".
- User wants a per-artist deep cut playlist.
- User wants a country/global charts snapshot saved as a playlist.

## Preconditions

- Auth required for every step except `search`, `artist-albums`, and `charts`. Run `Workflows/Setup.md` first if `auth check` is `missing`.

## Variants

This workflow has three composition modes — pick one with the user.

### Mode A: From a free-text theme

1. Search for candidate tracks:
   ```bash
   uv run --with ytmusicapi python scripts/helper.py search "<theme>" --type songs --limit 25
   ```
2. Curate down to the tracks the user wants (or auto-pick the top N if the user says "just pick").
3. Create the playlist:
   ```bash
   uv run --with ytmusicapi python scripts/helper.py playlist create \
     --title "<theme>" \
     --description "Auto-built from search '<theme>' on $(date +%Y-%m-%d)" \
     --privacy PRIVATE
   ```
4. Add the curated tracks:
   ```bash
   uv run --with ytmusicapi python scripts/helper.py playlist add <playlistId> <videoId...>
   ```

### Mode B: From an artist's discography

1. Resolve the artist's `browseId`:
   ```bash
   uv run --with ytmusicapi python scripts/helper.py search "<artist name>" --type artists --limit 3
   ```
2. Pull their albums:
   ```bash
   uv run --with ytmusicapi python scripts/helper.py artist-albums <browseId>
   ```
3. For each album the user wants, fetch its tracks:
   ```bash
   uv run --with ytmusicapi python scripts/helper.py album <albumBrowseId>
   ```
4. Create + add as in Mode A, step 3–4.

### Mode C: From the current charts

1. Pull charts (default global; pass `--country US|BR|KR|JP|…` for regional):
   ```bash
   uv run --with ytmusicapi python scripts/helper.py charts --country BR
   ```
2. Extract the top-N `videoId`s from the `videos` or `songs` section of the JSON.
3. Create + add as in Mode A, step 3–4.

## Mass-add from an existing playlist

If the user has a similar playlist already and wants to clone or merge:

```bash
uv run --with ytmusicapi python scripts/helper.py playlist add-playlist \
  <destinationPlaylistId> --source-playlist <sourcePlaylistId>
```

This pulls every track from the source playlist into the destination without manually enumerating `videoId`s.

## Privacy choice

Default to `PRIVATE` unless the user asks for `PUBLIC` or `UNLISTED`. Confirm before publishing anything `PUBLIC`.

## Output template

```text
📃 Created playlist: {{title}}
🔒 Privacy: {{privacy}}
🎵 Tracks added: {{n}}
🔗 playlistId: {{playlistId}}
```

## Failure modes

| Symptom | Likely cause | Remediation |
|--------|--------------|-------------|
| `playlist add` returns status with `actions` length 0 | The video is already in the playlist. | Re-run with `--duplicates` only if the user explicitly wants duplicates. |
| `add-playlist` fails on `source_playlist` | Source is private/restricted. | Confirm the user owns or has access to the source playlist. |
| Artist `browseId` not resolving | Search returned a profile, not an artist. | Use `--type artists` explicitly. |

## Next suggestions

- `Workflows/PlayDiscover.md` — play one track from the new playlist and explore related.
- Pass the new `playlistId` to `playlist rate <id> --rating LIKE` if the user wants it in their library faves.
