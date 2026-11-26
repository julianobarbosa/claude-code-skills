---
name: notebooklm-studio
description: >-
  Configure an existing Google NotebookLM notebook (persona and response-length from
  persona_config.json or pt-BR default) and generate the full Studio artifact suite
  (Audio Overview, Video Overview, Infographic, Slide Deck, Mind Map, Briefing Doc,
  Study Guide, Blog Post, Comparison Table Report, Flashcards, and Quiz) with idempotency
  and rate-limit pacing via the notebooklm CLI. Use when the user gives an existing
  NotebookLM URL or ID and asks to "configure and make all studio", "generate full studio",
  "run studio", or "make all artifacts". Do NOT use for creating a brand-new research
  notebook from scratch (use notebooklm-create).
---

# NotebookLM Studio & Persona Runner (`notebooklm-studio`)

Deterministic workflow for configuring an existing NotebookLM notebook and generating its complete Studio suite without cookie-contention, duplicate artifacts, or rate-limit collisions.

## Workflow

### 1. Ground on the Notebook Topic
Extract `<notebook_id>` from the URL (`https://notebook.google.com/notebook/<id>` or `https://notebooklm.google.com/notebook/<id>`) and inspect its sources to formulate a 1–2 sentence topic focus (`<TOPIC_FOCUS>`):

```bash
NB="<notebook_id>"
notebooklm use "$NB"
notebooklm source list -n "$NB" --json
# Inspect the primary source guide so prompts are grounded in actual content:
notebooklm source guide <first_source_id> -n "$NB"
```

If any source is not `ready`, run `notebooklm source wait <source_id> -n "$NB" --timeout 600` first.

### 2. Run the Studio Orchestrator Script
Execute [scripts/run_studio.py](./scripts/run_studio.py) with `python3` and a path relative to this skill directory. By default it enforces `pt-BR` (per project `CLAUDE.md` / `persona_config.json`), serializes concurrent runs per notebook via a file lock, fingerprints source metadata, focus, language, persona, response length, and each artifact's generation recipe, waits for `audio` before dispatching `video`, retries failed artifacts, and paces every CLI call by `--delay` (default `1.5s`):

Fingerprints detect changes visible in `source list` metadata, `--focus`, `--lang`, persona, response length, and the per-artifact generation options. Artifacts already present before this runner records per-artifact inputs have unknown provenance; run once with `--force` to establish it. The CLI does not expose a source-content version, so after editing, appending to, or refreshing content under an existing source ID, run with `--force` again (combine with `--only` to limit regeneration). A partial `--only` run preserves the fingerprints of artifacts it did not regenerate.

```bash
# Run from this repository's root; set SKILL_DIR to the installed skill directory elsewhere.
SKILL_DIR="${SKILL_DIR:-skills/notebooklm-studio}"
python3 "$SKILL_DIR/scripts/run_studio.py" \
  --notebook "$NB" \
  --focus "<TOPIC_FOCUS_IN_PT_BR>"
```

#### Optional Flags
- `--persona-config <path>`: Path to `persona_config.json` (defaults to `./persona_config.json` if present, else canonical `pt-BR` senior technical analyst persona).
- `--lang <code>`: CLI language code (default: `pt_BR`).
- `--only <comma-list>`: Generate only specific keys (`audio,video,infographic,slide-deck,briefing-doc,study-guide,blog-post,table-report,flashcards,quiz,mind-map`). Unknown keys fail fast with exit code `2`.
- `--try-native-table`: Attempt `notebooklm generate data-table` before falling back to the custom tabular report (`table-report`) on unsupported-operation (`UNCONFIRMED_WRITE` / `invalid argument`).
- `--no-wait-audio`: Dispatch `video` after `--delay` without waiting for `audio` completion (not recommended when both `audio` and `video` are generated in the same run).
- `--ignore-fingerprint`: Reuse existing artifacts even if source, focus, language, persona, response-length, or generation-recipe inputs changed.
- `--force`: Regenerate requested artifacts even if they already exist; use after source-content changes the metadata fingerprint cannot detect.
- `--dry-run`: Print the planned `configure` and `generate` commands without executing.

### 3. Verify and Report
The script exits non-zero if any required step fails and outputs a final JSON summary of all Studio artifacts. Present to the user:
1. **Notebook URL:** `https://notebooklm.google.com/notebook/<id>`
2. **Persona Configuration Status:** Mode/response-length + `pt-BR` persona (`applied` when the configuration command actually executed, or `planned` when `--dry-run` is active)
3. **Studio Artifacts Table:** `#`, `Type`, `Title`, `Artifact ID`, and `Status` (`completed` vs `in_progress` server-side rendering).
