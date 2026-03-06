---
name: NotebookLM
description: |
  Programmatic access to Google NotebookLM via the notebooklm-py CLI and Python API. Use this skill whenever the user wants to create notebooks, add sources (URLs, YouTube, PDFs, files), generate audio overviews/podcasts, videos, slide decks, quizzes, flashcards, infographics, reports, mind maps, or data tables from their research materials. Also use when the user mentions NotebookLM, wants to turn documents into podcasts, generate study materials, or automate any NotebookLM workflow — even if they don't explicitly say "NotebookLM". Triggers on: podcast from documents, audio overview, NotebookLM, notebook research, generate quiz from PDF, flashcards from notes, study materials, deep dive audio.
---

# NotebookLM Automation

Unofficial Python CLI and API for Google NotebookLM (`notebooklm-py`). Provides full programmatic access including capabilities the web UI doesn't expose.

## Prerequisites

- Python 3.10+
- Google account with NotebookLM access
- One-time browser login via Playwright

## Installation

```bash
# Install with browser login support
pip install "notebooklm-py[browser]"
playwright install chromium

# Linux only: also run
playwright install-deps chromium
```

## Authentication

First-time setup requires browser login:

```bash
notebooklm login
# Opens Chromium → sign into Google → press Enter when done
# Session saved to ~/.notebooklm/storage_state.json
```

Check auth status: `notebooklm auth check --test`

For headless/CI environments, copy `storage_state.json` from a local machine or set `NOTEBOOKLM_AUTH_JSON` env var.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `NOTEBOOKLM_HOME` | Config directory | `~/.notebooklm` |
| `NOTEBOOKLM_AUTH_JSON` | Inline auth JSON (CI/CD) | — |
| `NOTEBOOKLM_LOG_LEVEL` | `DEBUG`/`INFO`/`WARNING`/`ERROR` | `WARNING` |
| `NOTEBOOKLM_DEBUG_RPC` | Enable RPC debug (`1`) | `false` |

## Core Workflow

The typical workflow is: **create notebook → add sources → generate content → download**.

### 1. Notebook Management

```bash
notebooklm create "My Research"       # Create notebook
notebooklm list                        # List all notebooks
notebooklm use <id>                    # Set active notebook (supports partial ID)
notebooklm summary                     # AI summary of current notebook
notebooklm rename "New Title"          # Rename
notebooklm delete <id>                 # Delete
```

### 2. Adding Sources

Sources are auto-detected by type:

```bash
notebooklm source add "https://example.com/article"          # URL
notebooklm source add "https://youtube.com/watch?v=..."       # YouTube
notebooklm source add ./document.pdf                           # File (PDF, MD, DOCX, TXT, audio, video, images)
notebooklm source add-drive <drive-file-id> "Title"           # Google Drive
notebooklm source add-research "climate policy" --mode deep --import-all  # Research agent
```

Other source commands:

```bash
notebooklm source list                # List sources
notebooklm source fulltext <id>       # Get source full text
notebooklm source guide <id>          # AI-generated source guide
notebooklm source rename <id> "New"   # Rename
notebooklm source refresh <id>        # Re-fetch URL source
notebooklm source delete <id>         # Delete
```

### 3. Chat / Q&A

```bash
notebooklm ask "What are the key findings?" -s <source_id>
notebooklm ask "Compare sources" --json --save-as-note --note-title "Comparison"
notebooklm history                     # View chat history
notebooklm history --save              # Save history as note
```

### 4. Content Generation

All generate commands support: `-s/--source` (repeatable, limit to specific sources), `--json`, `--language`, `--retry N`.

Most are async — use `--wait` to block until complete.

#### Audio Overviews (Podcasts)

```bash
notebooklm generate audio "Focus on practical applications" \
  --format deep-dive \    # deep-dive | brief | critique | debate
  --length long \         # short | default | long
  --wait
```

#### Video Overviews

```bash
notebooklm generate video "Explain the architecture" \
  --format explainer \    # explainer | brief
  --style whiteboard \    # auto | classic | whiteboard | kawaii | anime | watercolor | retro-print | heritage | paper-craft
  --wait
```

#### Slide Decks

```bash
notebooklm generate slide-deck "Executive summary" \
  --format detailed \     # detailed | presenter
  --length default \      # default | short
  --wait

# Revise a specific slide
notebooklm generate revise-slide "Add more data points" \
  -a <artifact_id> --slide 2 --wait    # slide is zero-based
```

#### Study Materials

```bash
# Quizzes
notebooklm generate quiz --difficulty hard --quantity more --wait

# Flashcards
notebooklm generate flashcards --difficulty medium --wait
```

#### Visual & Data

```bash
# Infographic
notebooklm generate infographic \
  --orientation landscape \   # landscape | portrait | square
  --detail detailed \         # concise | standard | detailed
  --wait

# Mind map (synchronous, no --wait needed)
notebooklm generate mind-map

# Data table
notebooklm generate data-table "Compare metrics across studies" --wait
```

#### Reports

```bash
notebooklm generate report "Security analysis" \
  --format briefing-doc \     # briefing-doc | study-guide | blog-post | custom
  --append "Include threat modeling" \
  --wait
```

### 5. Downloading Content

All download commands support: `-a/--artifact`, `--all`, `--latest`, `--earliest`, `--name`, `--force`, `--no-clobber`, `--dry-run`, `--json`.

```bash
notebooklm download audio ./podcast.mp3
notebooklm download video ./overview.mp4
notebooklm download slide-deck ./slides.pptx --format pptx   # or pdf (default)
notebooklm download infographic ./info.png
notebooklm download report ./report.md
notebooklm download mind-map ./map.json
notebooklm download data-table ./data.csv
notebooklm download quiz --format json ./quiz.json       # json | markdown | html
notebooklm download flashcards --format markdown ./cards.md
```

### 6. Sharing

```bash
notebooklm share status
notebooklm share public --enable           # Create public link
notebooklm share view-level full           # full | chat
notebooklm share add user@email.com --permission editor -m "Check this out"
notebooklm share remove user@email.com
```

### 7. Language

```bash
notebooklm language list                   # 80+ languages
notebooklm language get
notebooklm language set ja                 # Set to Japanese
```

## Python API

Fully async API for programmatic workflows:

```python
import asyncio
from notebooklm import NotebookLMClient

async def main():
    async with await NotebookLMClient.from_storage() as client:
        # Create notebook and add sources
        nb = await client.notebooks.create("Research")
        await client.sources.add_url(nb.id, "https://example.com")

        # Generate audio overview
        artifact = await client.artifacts.generate_audio(
            nb.id, description="Deep dive on findings",
            format=AudioFormat.DEEP_DIVE, length=AudioLength.LONG
        )

        # Wait and download
        await client.artifacts.wait(nb.id, artifact.id)
        await client.artifacts.download_audio(nb.id, artifact.id, "output.mp3")

        # Chat with sources
        result = await client.chat.ask(nb.id, "Summarize key points")
        print(result.answer)

asyncio.run(main())
```

**API modules:** `client.notebooks`, `client.sources`, `client.artifacts`, `client.chat`, `client.research`, `client.notes`, `client.settings`, `client.sharing`

## Common Recipes

### Research-to-Podcast Pipeline

```bash
notebooklm create "Climate Research"
notebooklm use <id>
notebooklm source add "https://en.wikipedia.org/wiki/Climate_change"
notebooklm source add-research "climate change solutions 2025" --mode deep --import-all
notebooklm generate audio "Focus on actionable solutions" --format debate --length long --wait
notebooklm download audio ./climate-debate.mp3
```

### Document Analysis to Study Materials

```bash
notebooklm create "Exam Prep"
notebooklm use <id>
notebooklm source add ./textbook.pdf
notebooklm generate quiz --difficulty hard --quantity more --wait
notebooklm generate flashcards --wait
notebooklm download quiz --format markdown ./quiz.md
notebooklm download flashcards --format json ./cards.json
```

### Batch Import + Full Report

```bash
notebooklm create "Literature Review"
notebooklm use <id>
for f in ./papers/*.pdf; do notebooklm source add "$f"; done
notebooklm generate report "Systematic review" --format briefing-doc --wait
notebooklm download report ./review.md
```

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Auth expired | Run `notebooklm login` again |
| `playwright` not found | `pip install "notebooklm-py[browser]"` then `playwright install chromium` |
| Generation stuck | Use `notebooklm source wait <id>` for pending sources, check `--retry` flag |
| Partial ID not matching | Use more characters of the notebook ID |
| Debug API calls | Set `NOTEBOOKLM_LOG_LEVEL=DEBUG` or `NOTEBOOKLM_DEBUG_RPC=1` |
