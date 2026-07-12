# YouTube Music Command Reference

All commands below assume execution from the skill root.

## Helper Commands

Run helper commands as:

```bash
uv run --with ytmusicapi python scripts/helper.py <subcommand> [args]
```

### auth

```bash
auth check
auth setup --cookie '<cookie>'
auth setup --cookies-file /path/to/cookies.json
auth account
auth remove
```

If `auth check` returns `status: "missing"`, pause the original request and collect one of:
- a Cookie string from a logged-in `music.youtube.com` request
- a cookies JSON export file path

Mirror the user's language when replying. If the user's language is unclear, default to English.

Then run `auth setup` and retry the original command.

### search

```bash
search "<query>"
search "<query>" --type songs
search "<query>" --type artists
search "<query>" --type albums
search "<query>" --type playlists
search "<query>" --type videos
search "<query>" --limit 20
search "<query>" --type songs --library

suggest "<prefix>"
```

### library

```bash
library liked
library playlists
library songs
library albums
library artists
library subscriptions
library history
library uploads

library songs --limit 50
library albums --order a_to_z
```

### playlist

```bash
playlist get <playlistId>
playlist create --title "<name>"
playlist create --title "<name>" --description "<desc>" --privacy PUBLIC
playlist edit <playlistId> --title "<new name>"
playlist delete <playlistId>
playlist add <playlistId> <videoId> ...
playlist add-playlist <playlistId> --source-playlist <sourcePlaylistId>
playlist remove <playlistId> <videoId> ...
playlist rate <playlistId> --rating LIKE
```

### artist / album / song

```bash
artist <browseId>
artist-albums <browseId>
album <browseId>
song <videoId>
lyrics <videoId>
related <videoId>
watch <videoId>
watch <videoId> --limit 10
```

### account / discovery / uploads

```bash
rate <videoId> LIKE
rate <videoId> DISLIKE
rate <videoId> INDIFFERENT

subscribe subscribe <channelId> ...
subscribe unsubscribe <channelId> ...

charts
charts --country CN
moods
mood-playlist <params>
home --limit 3

history list
history remove <feedbackToken> ...

taste get
taste set --artists "<name1>" "<name2>"

upload list
upload upload --filepath /path/to/song.mp3
upload delete --entity-id <entityId>

user <channelId>
```

## Player Commands

Run player commands as:

```bash
uv run --with playwright python scripts/player.py <action> [args]
```

The player uses a persistent Playwright daemon with a dedicated browser profile.

The first playback command auto-starts the daemon if needed:

```bash
uv run --with playwright python scripts/player.py daemon-start
```

Then control the persistent browser session:

```bash
uv run --with playwright python scripts/player.py status
uv run --with playwright python scripts/player.py open <videoId>
uv run --with playwright python scripts/player.py next
uv run --with playwright python scripts/player.py prev
uv run --with playwright python scripts/player.py play
uv run --with playwright python scripts/player.py pause
uv run --with playwright python scripts/player.py volume <0-100>
uv run --with playwright python scripts/player.py seek <seconds>
uv run --with playwright python scripts/player.py shuffle
uv run --with playwright python scripts/player.py repeat
uv run --with playwright python scripts/player.py daemon-status
uv run --with playwright python scripts/player.py daemon-stop
```

Notes:
- The daemon uses `./.yt-music/playwright-profile` to keep its own persistent browser session
- On first launch, sign in to `music.youtube.com` in that browser window if needed
- If `open <videoId>` navigates correctly but audio does not start, autoplay was likely blocked and manual play may be required once
- `daemon-status` checks the daemon without opening a new browser
