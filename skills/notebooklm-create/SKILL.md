---
name: notebooklm-create
description: |
  Complete "topic notebook build" workflow for Google NotebookLM — deep web research, sequential source loading (with known-failing domain skips), full Studio artifact generation, and curated chat-prompt library. Use this skill whenever the user wants to create a new NotebookLM notebook on a topic, build a full research notebook from scratch, generate a "{topic} :: docs" notebook, compile sources from forums (Reddit/HN/GitHub/Discord/Quora) into a notebook, produce a full Studio (audio + video + mind map + reports + flashcards + quiz + infographic + slide deck + data table) for an existing notebook, or prepare curated NotebookLM prompts for a topic. Triggers on phrases like "build a notebook on X", "create cmux :: docs", "research and build NotebookLM", "full studio for my notebook", "entire studio", "NotebookLM prompts for topic Y", "turn this into a NotebookLM notebook". Apply even when the user does not explicitly say "NotebookLM" — if they ask you to assemble a research notebook on a topic with sources and derivative artifacts, this is the right skill.
---

# notebooklm-create

End-to-end workflow for building a complete NotebookLM topic notebook: deep research, source loading, full Studio, curated prompts. Orchestrates the `notebooklm-rpc` MCP tools with domain-specific gotcha handling encoded.

## Relationship to notebooklm-skill

- `notebooklm-skill` = low-level API reference (notebooklm-py CLI)
- **This skill (`notebooklm-create`) = high-level workflow orchestration** using the `notebooklm-rpc` MCP tools available in this session

If the user just wants to call a single API (e.g., "list my notebooks"), use `notebooklm-skill` or the MCP tool directly. If they want to BUILD a research notebook from a topic, use this skill.

## Why this workflow exists

Building a rich NotebookLM notebook for a topic has repeatable shape but is strewn with gotchas that cost real time if rediscovered:

- Some domains silently refuse NotebookLM's URL fetcher (Medium, Quora)
- URL adds cascade-fail when issued in parallel — must be sequential
- `llms.txt` URLs need the trailing `.md` stripped before adding
- Studio artifacts split into synchronous (mind map, reports, flashcards, quiz, data table) and async (audio, video, infographic, slide deck) with different polling behavior
- The Studio API classifies quiz artifacts as `type: flashcards` once generated (title disambiguates)
- `confirm=True` is mandatory on every Studio creation tool AND requires explicit user approval

This skill encodes all of that so future runs don't relearn it.

## Workflow — the 7 phases

Run these in order. Each phase has a clear hand-off to the next.

### Phase 1 — Capture intent

Ask or infer:

1. What's the **topic**? (e.g., "cmux", "ArgoCD image updater", "Azure landing zones")
2. Any **seed URLs** the user already wants included (videos, blog posts, GitHub repos)?
3. Which **forums** to cover? Defaults: Reddit, Hacker News, GitHub Discussions. Optional: Discord (captured as text — not URL-indexable), Quora (usually empty for technical topics; confirm via research)
4. Target **notebook title** — default convention: `{topic} :: docs` (matches user's existing naming pattern visible via `notebook_list`)
5. Does the user want the **full Studio** (all 10 artifacts) or selective?

If the topic name is ambiguous (multiple projects share the name — common: `cmux` = manaflow-ai vs craigsc vs coder), anchor disambiguation on the user's seed URLs before researching.

### Phase 2 — Deep research

Goal: produce two artifacts — a **research synthesis** and a **community content** dossier. Both become text sources in the notebook.

Read `references/prompt-library.md` for prompt starters. Use WebFetch on user-provided seed URLs first to lock in disambiguation, then WebSearch for canonical repo / docs / llms.txt.

Dispatch **two parallel agents** (via the `Agent` tool with `general-purpose` subagent):

1. **Research synthesis agent** — produces 2000–3000 word markdown covering overview, architecture, features, comparisons, installation, traction, limitations, official URLs. Output template: `assets/research_synthesis_template.md`.

2. **Community content agent** — searches Reddit, Hacker News, GitHub Discussions for threads, extracts verbatim quotes with attribution. Captures Discord community texture by pulling equivalent content from GitHub Discussions (Discord isn't publicly scrapeable). Confirms Quora status (usually no threads for technical topics). Output template: `assets/community_content_template.md`.

Both agents should return ready-to-paste markdown. Save locally under `MEMORY/WORK/<slug>/`.

### Phase 3 — Create the notebook

Use `mcp__notebooklm-rpc__notebook_create` with the agreed title.

```
mcp__notebooklm-rpc__notebook_create(title="{topic} :: docs")
```

Capture the returned `notebook.id` — you'll need it for every subsequent call.

Verify no duplicate exists first via `mcp__notebooklm-rpc__notebook_list` (filter titles case-insensitively for the topic term).

### Phase 4 — Load sources (SEQUENTIAL — critical)

Read `references/url-gotchas.md` for the domain blocklist and URL-cleaning rules before calling any add tool.

Order of source types to add (each as a separate, sequential call — never in parallel):

1. User's seed URLs (YouTube, blog posts, etc.)
2. Official repo / website / docs
3. Hacker News discussion(s)
4. Reddit thread URL(s) — keep the trailing `/` that Reddit prefers
5. GitHub Discussions / Issues URLs with relevant community content
6. Third-party reviews / comparative discussions
7. After all URL sources: add the research synthesis and community content as **text** sources via `mcp__notebooklm-rpc__notebook_add_text`

**DO NOT** attempt to add:
- `medium.com/*` — always fails
- `quora.com/*` — always fails (as of 2026-04-21; see url-gotchas.md)
- `linkedin.com/*` — typically fails (auth gates)

If a domain is uncertain, probe with WebFetch first — if that returns bot-detection content, assume NotebookLM will fail too and capture as text instead.

If adding an `llms.txt` URL, strip any trailing `.md` before the call (e.g., `foo.com/llms.txt`, not `foo.com/llms.txt.md`).

Sequential sample pattern:

```
# For each url in ordered_list:
mcp__notebooklm-rpc__notebook_add_url(notebook_id=NB, url=url)
# wait for success, then next
```

### Phase 5 — Generate full Studio (requires user approval)

Every Studio tool takes `confirm=True`. The MCP server explicitly states user approval is required before setting it. Present the plan to the user, get approval, then dispatch.

Read `references/studio-quirks.md` for sync vs async classification and known API quirks.

Recommended order (async-first minimizes total wall-clock):

1. `audio_overview_create` — async, ~60s+
2. `video_overview_create` — async, several minutes
3. `infographic_create` — async, several minutes
4. `slide_deck_create` — async, several minutes
5. `mind_map_create` — synchronous
6. `report_create(format="Briefing Doc")` — synchronous
7. `report_create(format="Study Guide")` — synchronous
8. `flashcards_create` — synchronous
9. `quiz_create(question_count=10)` — synchronous (note: classified as `type: flashcards` in studio_status)
10. `data_table_create(description=...)` — synchronous

For each async artifact, pass a `focus_prompt` tailored to the topic — see `references/mcp-tool-map.md` for recommended focus prompts per tool.

After dispatching, poll once via `mcp__notebooklm-rpc__studio_status` after ~45s, then again after 2–3 minutes. Async media can take 5–10 minutes to render.

### Phase 6 — Curate chat prompts

Add a text source containing 9 NotebookLM chat prompts adapted to the topic. Base templates live in `references/prompt-library.md` — they come from two public articles (XDA Developers, AI Fire) and are pre-mapped to structural goals:

1. Five Essential Questions (study)
2. Find the Interesting Bits (insight mining)
3. Quiz Show (gamified review)
4. Content Analyst Report (repurposing)
5. Community → Action Plan (roadmap synthesis)
6. SEO Outline (competitive content)
7. 360° Feedback on Marketing (voice-of-multi-persona critique)
8. Study Guide Kit (onboarding curriculum)
9. Conference Talk Script (narrative pitch)

Replace the topic-specific placeholders in each template with concrete references from the research (actors, quotes, key architectural facts). Save to both:
- A local markdown file under `MEMORY/WORK/<slug>/prompts.md` for reuse
- A text source inside the notebook via `mcp__notebooklm-rpc__notebook_add_text` titled `"9 Curated NotebookLM Prompts for {topic}"`

### Phase 7 — Verify

```
mcp__notebooklm-rpc__notebook_get(notebook_id=NB)
mcp__notebooklm-rpc__studio_status(notebook_id=NB)
```

Confirm:
- Notebook title matches `{topic} :: docs`
- Source count matches expected (seed URLs + forum URLs + 2 text research sources + 1 prompts text source)
- Studio artifacts completed or still rendering (video/infographic/slide deck commonly still rendering at verification time — that's fine)
- No duplicate notebook was created

Report back to the user with:
- Notebook URL (`notebooklm.google.com/notebook/{id}`)
- Table of studio artifacts with status
- Pointer to the 9 curated prompts

## Tools & resources included

- `scripts/add_urls_sequential.py` — wraps the sequential-add pattern with the domain blocklist built in
- `scripts/build_full_studio.py` — dispatches all 10 Studio artifacts in the correct async-first order (prints the MCP call plan; actual MCP invocation happens from Claude's tool layer)
- `scripts/adapt_prompts.py` — takes a topic facts dict and emits the 9 prompts with placeholders filled
- `references/url-gotchas.md` — domain blocklist + URL-cleaning rules
- `references/studio-quirks.md` — sync vs async, quiz classification, confirm guard
- `references/prompt-library.md` — 9 base prompts with source attribution (XDA + AI Fire)
- `references/mcp-tool-map.md` — which MCP tool per phase + recommended focus prompts
- `assets/research_synthesis_template.md` — 9-section research doc scaffold
- `assets/community_content_template.md` — forum/community dossier scaffold
- `assets/workflow_checklist.md` — phase-by-phase checklist to copy into a work PRD
- `samples/cmux_docs_walkthrough.md` — worked example from the original session

## When NOT to use this skill

- User wants to **modify** or **dedupe** an existing notebook — use `notebooklm-skill` or direct MCP calls
- User just wants to LIST notebooks or describe one — use the MCP tools directly
- User wants to add a single source to an existing notebook — direct MCP call is fine, no orchestration needed
- The task has no "build a research notebook" shape (e.g., "convert this PDF to audio") — use `notebooklm-skill`

## References to read during execution

| When | Read |
|------|------|
| Before Phase 4 (URL adds) | `references/url-gotchas.md` |
| Before Phase 5 (Studio) | `references/studio-quirks.md`, `references/mcp-tool-map.md` |
| Before Phase 6 (Prompts) | `references/prompt-library.md` |
| If stuck on a tool choice | `references/mcp-tool-map.md` |

## Anti-patterns (learned from real runs)

- **Parallel URL adds** → cascade fail. Always sequential.
- **Adding Medium or Quora URLs** → silently fail. Scrape content, add as text.
- **Treating Studio like a single batch** → confirm guard will block. Each tool needs its own `confirm=True`.
- **Polling `studio_status` immediately** → async artifacts show `in_progress`; wait 45s minimum.
- **Checking `type` field to distinguish quiz from flashcards** → both classify as flashcards post-generation. Use the artifact title.
- **Forgetting to save the `notebook_id`** → costs a redundant `notebook_list` call to recover it.

---

## Gotchas

- **Web research phase truncates at ~50 URLs** — large topics need batching and manual aggregation; the truncation is silent.
- **Sequential source upload preserves order; parallel upload doesn't** — workflows that use `&` and `wait` in bash get random ordering and unstable citations.
- **Source quotas reset at midnight Pacific** — a script that hits the daily limit at 23:55 PT silently waits 5 minutes; one running at noon waits 12 hours.
- **Full-studio generation: audio/video/slides/quiz/flashcards/etc. run in parallel after upload** — if upload fails midway, the partial set still generates without error; verify all sources before generating.
- **Notebook ID vs notebook title**: the title is mutable; the ID isn't. Scripts that look up by title break on rename.
