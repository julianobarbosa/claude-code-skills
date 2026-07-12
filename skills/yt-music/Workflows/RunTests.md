# RunTests — Verify the Skill's Python Bindings

The yt-music skill ships a pytest suite that exercises every CLI subcommand in `scripts/helper.py` and `scripts/player.py`, plus the pure helpers inside `scripts/player_daemon.py`. The suite uses fake `ytmusicapi` / `playwright` modules and a per-test `YT_MUSIC_DATA_DIR`, so it never touches the network, the user's auth file, or a real Chromium binary.

Run this workflow whenever you:

- Modify any script under `scripts/`
- Change `pytest.ini` or test fixtures
- Want a quick smoke check after pulling upstream

## Preconditions

- `uv` is on `PATH`
- You are inside the skill root (`skills/yt-music/`)

## Steps

### 1. Run the suite

```bash
uv run --with pytest python -m pytest
```

Expected: every test under `tests/` passes. The suite has no live-network calls, so it should be deterministic on a cold machine.

### 2. Run a single file (when iterating on one area)

```bash
uv run --with pytest python -m pytest tests/test_helper_auth.py -v
```

### 3. Run a single test by name

```bash
uv run --with pytest python -m pytest -k "build_auth_from_cookie_with_sapisid" -v
```

### 4. Re-run only the last failures

```bash
uv run --with pytest python -m pytest --lf -v
```

### 5. Integration tier (opt-in)

Tests tagged `@pytest.mark.integration` are skipped by default. They hit the real `ytmusicapi` or launch a real Playwright browser, so only run them when those tools and a logged-in profile are available:

```bash
uv run --with pytest --with ytmusicapi --with playwright python -m pytest -m integration -v
```

(None ship by default — the marker is reserved for future end-to-end coverage.)

## What the suite covers

| Area | File | Notes |
|------|------|-------|
| Auth (cookie / cookies-file / check / remove / account) | `tests/test_helper_auth.py` | SAPISID derivation, `__Secure-3PAPISID` fallback, JSON export ingestion, legacy-key migration |
| Search & suggest | `tests/test_helper_search.py` | All filter choices, `--library` scope, `--limit` plumbing |
| Library | `tests/test_helper_library.py` | Every dispatch-table entry plus auth requirement |
| Playlist | `tests/test_helper_playlist.py` | All eight actions including `add-playlist` and `remove` with track lookup |
| Long-tail commands | `tests/test_helper_misc.py` | artist / album (with OLAK/PL conversion) / song / lyrics / related / watch / rate / subscribe / charts / moods / home / history / taste / user / upload |
| CLI parser | `tests/test_helper_parser.py` | Help screen, invalid choices, env-var data-dir resolution |
| Player client | `tests/test_player_client.py` | `_load_state` / `_request` / `_probe` / `_ensure_daemon`, every CLI verb, error handling on HTTPError and OSError |
| Daemon pure helpers | `tests/test_player_daemon_pure.py` | `_write_json`, `_remove_state_file`, browser detection, version parsing, constants |

## How the fixtures keep the suite safe

`tests/conftest.py` provides:

- `data_dir` — points `YT_MUSIC_DATA_DIR` at a `tmp_path` so the scripts never read or write the user's real `.yt-music/` folder.
- `fake_ytmusicapi` — installs a stub `ytmusicapi` module whose `YTMusic` is a `MagicMock`. Tests assert on its call shape rather than going over the wire.
- `fake_playwright` — same trick for `playwright.sync_api`.
- `helper_mod` / `player_mod` / `player_daemon_mod` — fresh imports of each script under the per-test env, so module-level constants reflect the temp data dir.
- `run_cli(module, *argv, monkeypatch=...)` — invokes `module.main()` with patched `sys.argv` and returns the exit code so tests can assert `SystemExit` codes cleanly.

## Failure modes

| Symptom | Likely cause | Remediation |
|---------|--------------|-------------|
| `ModuleNotFoundError: helper` | Tests run from outside the skill root | `cd skills/yt-music && uv run --with pytest python -m pytest` |
| Tests touch the real `~/.yt-music/` | Fixture not applied | Confirm the test asks for `helper_mod`/`player_mod`, not raw `helper`/`player` imports |
| `ModuleNotFoundError: ytmusicapi` or `playwright` | A new test imports the module without the fake fixture | Add `helper_mod` / `player_daemon_mod` to the test's fixture list |
| Test passes locally, fails in CI | CI shell didn't pre-cache the `pytest` install | Use `uv run --with pytest python -m pytest`; `uv` resolves the env on each invocation |
| `Failed to inspect Python interpreter from active virtual environment` | `$VIRTUAL_ENV` points at a broken or removed venv | Run with `env -u VIRTUAL_ENV uv run --no-project --with pytest python -m pytest` or `deactivate` first |

## Next suggestions

- Add coverage reporting: `uv run --with pytest --with coverage python -m pytest --cov=scripts --cov-report=term-missing`
- Wire the pytest invocation into CI on every push under `skills/yt-music/`
- Add `@pytest.mark.integration` smoke tests for auth + playback once a CI-safe credential strategy exists
