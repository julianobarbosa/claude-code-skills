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
Execute [scripts/run_studio.py](./scripts/run_studio.py) with the notebook ID and grounded topic focus. By default it enforces `pt-BR` (per project `CLAUDE.md` / `persona_config.json`), skips already-created artifacts, retries failed ones, and paces RPC calls by 1.5s to prevent `storage_state.json` CAS lock collisions:

```bash
/home/barbosa/.venv/tools3/bin/python ~/.agents/skills/notebooklm-studio/scripts/run_studio.py \
  --notebook "$NB" \
  --focus "<TOPIC_FOCUS_IN_PT_BR>"
```

#### Optional Flags
- `--persona-config <path>`: Path to `persona_config.json` (defaults to `./persona_config.json` if present, else canonical `pt-BR` senior technical analyst persona).
- `--lang <code>`: CLI language code (default: `pt_BR`).
- `--only <comma-list>`: Generate only specific keys (`audio,video,infographic,slide-deck,briefing-doc,study-guide,blog-post,table-report,flashcards,quiz,mind-map`).
- `--try-native-table`: Attempt `notebooklm generate data-table` before falling back to the custom tabular report (`table-report`).
- `--force`: Regenerate even if an artifact of that subtype already exists.
- `--dry-run`: Print the planned `configure` and `generate` commands without executing.

### 3. Verify and Report
The script outputs a final JSON summary of all Studio artifacts. Present to the user:
1. **Notebook URL:** `https://notebooklm.google.com/notebook/<id>`
2. **Persona Configuration Status:** Mode/response-length + `pt-BR` persona applied
3. **Studio Artifacts Table:** `#`, `Type`, `Title`, `Artifact ID`, and `Status` (`completed` vs `in_progress` server-side rendering).
