# MCP Tool Map — notebooklm-rpc

Which MCP tool to call at each workflow phase. All tools live under the `mcp__notebooklm-rpc__` prefix.

## Phase 1 — Capture intent
_No MCP calls. Conversation only._

## Phase 2 — Deep research
_No notebooklm-rpc calls. Use `WebFetch`, `WebSearch`, and `Agent` (subagents) for research._

## Phase 3 — Create notebook

| Tool | Purpose | Required params |
|------|---------|-----------------|
| `notebook_list` | Pre-flight: check for duplicate title | (none) |
| `notebook_create` | Create the notebook | `title` |

Capture `notebook.id` from the `notebook_create` response.

## Phase 4 — Load sources (sequential)

| Tool | Purpose | Required params |
|------|---------|-----------------|
| `notebook_add_url` | Add a web URL (article, YouTube, GitHub, HN, Reddit) | `notebook_id`, `url` |
| `notebook_add_text` | Add pasted text (research synthesis, community content, Discord captures) | `notebook_id`, `text`, optional `title` |
| `notebook_add_drive` | Add a Google Drive document | `notebook_id`, `file_id` |
| `source_delete` | Remove a failed/broken source | `notebook_id`, `source_id` |

**Order sensitivity:** one-at-a-time. Wait for success response before next call.

## Phase 5 — Studio generation

All require `confirm: true` AND user approval.

### Async media (dispatch FIRST — longer render time)

| Tool | Key options | Recommended focus prompt shape |
|------|-------------|-------------------------------|
| `audio_overview_create` | `format: deep_dive\|brief\|critique\|debate`, `length: short\|default\|long` | "Focus on {topic} — why it exists, the problem it solves, key features {list}, comparison to {alternatives}." |
| `video_overview_create` | `format: explainer\|brief`, `visual_style: auto_select\|classic\|whiteboard\|...` | "Explain {topic} visually: problem, architecture, key features, comparison, traction." |
| `infographic_create` | `orientation: landscape\|portrait\|square`, `detail_level: concise\|standard\|detailed` | "Visual overview of {topic}: key features {list}, traction {metrics}, architecture layering, community sentiment." |
| `slide_deck_create` | `format: detailed_deck\|presenter_slides`, `length: short\|default` | "A presentation on {topic}: the problem, the solution, architecture, comparison, installation, traction, limitations." |

### Synchronous / fast-async (dispatch SECOND)

| Tool | Key options | Notes |
|------|-------------|-------|
| `mind_map_create` | `title` | Returns fully rendered mind map in response |
| `report_create` | `report_format: "Briefing Doc"\|"Study Guide"\|"Blog Post"\|"Create Your Own"`, `custom_prompt` (for Create Your Own) | Call twice for Briefing + Study Guide |
| `flashcards_create` | `difficulty: easy\|medium\|hard` | Returns `flashcard_count` (usually 9±2) |
| `quiz_create` | `question_count` (default 2 — override to 10), `difficulty` | Will be classified as `type: flashcards` post-generation — use title to identify |
| `data_table_create` | `description` (REQUIRED — describe columns & rows) | Good for comparison tables; specify columns explicitly |

### Polling & management

| Tool | Purpose |
|------|---------|
| `studio_status` | Poll artifact generation status |
| `studio_delete` | Remove a failed/poor artifact |

## Phase 6 — Curate prompts

| Tool | Purpose |
|------|---------|
| `notebook_add_text` | Add the 9 curated prompts as a text source titled `"9 Curated NotebookLM Prompts for {topic}"` |

## Phase 7 — Verify

| Tool | Purpose |
|------|---------|
| `notebook_get` | Retrieve full notebook metadata + source list |
| `notebook_describe` | AI-generated notebook summary + suggested topics |
| `studio_status` | Final check on artifact completion |

## Auth refresh

If any tool returns an auth error: **do not save_auth_tokens manually.** Run `notebooklm-mcp-auth` in the terminal (Bash tool) — it handles auth end-to-end.

## Quick reference — full pipeline call order

```
1. notebook_list  # dedup check
2. notebook_create → capture notebook_id
3. notebook_add_url × N  (SEQUENTIAL, skip Medium/Quora)
4. notebook_add_text × 2  (research synthesis + community content)
5. audio_overview_create(confirm=true, focus_prompt=...)
6. video_overview_create(confirm=true, focus_prompt=...)
7. infographic_create(confirm=true, focus_prompt=...)
8. slide_deck_create(confirm=true, focus_prompt=...)
9. mind_map_create(confirm=true)
10. report_create(report_format="Briefing Doc", confirm=true)
11. report_create(report_format="Study Guide", confirm=true)
12. flashcards_create(confirm=true)
13. quiz_create(question_count=10, confirm=true)
14. data_table_create(description=..., confirm=true)
15. notebook_add_text (curated prompts)
16. studio_status  # poll 45s later
17. notebook_get   # final verify
```
