# Sample: `cmux :: docs` End-to-End Walkthrough

Real worked example of this skill applied to the topic **cmux** (manaflow-ai) — the native macOS terminal for parallel AI coding agents. Built on 2026-04-21. All IDs and URLs are verifiable.

## Inputs from the user

> "create a entirely `cmux :: docs` notebooklm, go to the web and make a deepresearch about that and add as source for this notebooklm
> - https://www.youtube.com/watch?v=8oLP8oxqtOE
> - https://vibecoding.app/blog/cmux-review
> go to forum like `reddit`, `discord`, `quora`"

## Phase 1 — Intent

- Topic: **cmux** — ambiguous (multiple projects share the name); anchor on user URLs
- Seed URLs: YouTube video + vibecoding blog
- Forums: Reddit, Discord, Quora explicitly named
- Title: `cmux :: docs` (matches existing `{topic} :: docs` convention)
- Studio: deferred to a second user turn ("entirely studio")
- Disambiguation: WebFetch on the two seed URLs confirmed **manaflow-ai/cmux**, not craigsc/cmux or coder/cmux

## Phase 2 — Deep Research

Two parallel subagents dispatched:

**Synthesis agent** produced `research_synthesis.md` (12.8 KB, 9 sections per template). Key findings:
- cmux = native Swift/AppKit macOS terminal, built on libghostty
- Founders: Austin Wang + Lawrence Chen (Manaflow, YC S24)
- Launched Feb 19, 2026 — hit #2 on HN
- ~15k stars by April 2026
- Mitchell Hashimoto (Ghostty creator) publicly endorsed it
- Positioning: "primitive, not a solution"
- Layering: board → orchestrator → review → **terminal (cmux)** → agent

**Community agent** produced `community_content.md` (14.9 KB). Key findings:
- Hacker News Show HN (`id=47079718`) — 198 points, 77 comments, strongly positive
- 3 active Reddit threads (r/ClaudeCode, r/tmux, r/SaasDevelopers)
- GitHub Discussion #681 (session persistence gap) — most cited critical feedback
- **Quora: no cmux threads exist** — confirmed absent
- Discord server exists (`discord.gg/xsgFEVrWCZ`) — content captured indirectly from GitHub Discussions

## Phase 3 — Create notebook

```
mcp__notebooklm-rpc__notebook_create(title="cmux :: docs")
→ notebook_id = e0ed6d5f-abdc-4957-9ccd-fd988f88970f
```

Pre-flight `notebook_list` confirmed no existing `cmux`-named notebooks.

## Phase 4 — Sources (sequential)

11 URL sources added one at a time:

1. `youtube.com/watch?v=8oLP8oxqtOE` ✅
2. `vibecoding.app/blog/cmux-review` ✅
3. `github.com/manaflow-ai/cmux` ✅
4. `www.cmux.dev/` ✅
5. `cmux.com/docs/getting-started` ✅
6. `news.ycombinator.com/item?id=47079718` ✅
7. `reddit.com/r/ClaudeCode/comments/1r9g45u/...` ✅
8. `reddit.com/r/tmux/comments/1s2rnln/...` ✅
9. `reddit.com/r/SaasDevelopers/comments/1sfecai/...` ✅
10. `github.com/ComposioHQ/agent-orchestrator/discussions/526` ✅
11. `github.com/manaflow-ai/cmux/discussions/681` ✅

**Failed adds** (expected, per url-gotchas.md):
- `quora.com/topic/Terminal-Emulators` ❌ — NotebookLM returned `Failed to add URL source`
- `quora.com/What-are-some-of-the-best-free-AI-agents-9` ❌ — same

**Recovery:** Captured Quora absence in the community content text source instead. Added a new feedback memory (`feedback_quora_urls_fail.md`) after observing the failure.

2 text sources added:
- `cmux: Deep Research Synthesis` (source id `4074bf68`)
- `cmux Community (Reddit, HN, GitHub, Discord, Quora)` (source id `57e0fc1e`)

**Final count: 13 usable sources.**

## Phase 5 — Studio (second user turn)

User explicitly requested "entirely studio" — treated as scoped approval.

Dispatched in async-first order, all with `confirm=true`:

| # | Tool | Result |
|---|------|--------|
| 1 | `audio_overview_create(format=deep_dive, focus_prompt=...)` | ✅ "cmux creates mission control for agents" |
| 2 | `video_overview_create(format=explainer)` | 🕐 rendering |
| 3 | `mind_map_create` | ✅ "Cmux: O Terminal Nativo para Orquestração de Agentes IA" |
| 4 | `report_create(Briefing Doc)` | ✅ "cmux: The Terminal Substrate for AI Agent Multitasking" |
| 5 | `report_create(Study Guide)` | ✅ "cmux: A Comprehensive Study Guide for the AI-Native Terminal" |
| 6 | `flashcards_create` | ✅ 9 cards |
| 7 | `quiz_create(question_count=10)` | ✅ "Quiz cmux" — 9 questions (NOTE: classified as `type: flashcards` in studio_status) |
| 8 | `infographic_create(orientation=portrait, detail_level=detailed)` | 🕐 rendering |
| 9 | `slide_deck_create(format=detailed_deck)` | 🕐 rendering |
| 10 | `data_table_create(description="Comparison of AI-Agent Terminals and Orchestrators")` | ✅ |

`studio_status` polled at 45s (6 completed) and again at 2 min (7 completed). Video/infographic/slide deck left rendering — reported to user with expected completion time.

## Phase 6 — Curate prompts

`adapt_prompts.py` with the following facts:

```json
{
  "topic": "cmux",
  "central_theme": "native macOS terminal for AI coding agents built on libghostty",
  "key_concepts": "libghostty rendering, OSC notification protocols, claude-teams, Ghostty config reuse",
  "key_facts": "YC S24 backed, launched Feb 19 2026, ~15k stars, #2 on Hacker News",
  "origin_story": "Austin Wang and Lawrence Chen built it after frustration with generic 'Claude is waiting for your input' notifications",
  "implications": "cmux is a terminal substrate, not an orchestrator",
  "key_concepts_list": "libghostty, OSC 9/99/777, claude-teams, Ghostty config, vertical tabs, notification rings, remote workspaces, AGPL",
  "expected_queries": "cmux, terminal for Claude Code, parallel AI agents macOS"
}
```

Emitted `prompts.md`, saved locally, then added to notebook as text source `4dfd83a6` titled "9 Curated NotebookLM Prompts for cmux".

## Phase 7 — Verify

`notebook_get(notebook_id=e0ed6d5f-...)` returned:
- Title: `cmux :: docs` ✅
- 14 sources total (11 URL + 3 text: research, community, prompts)
- 2 Quora placeholder errors (noted, left in place — harmless)

Final reported to user:
- **Notebook URL:** https://notebooklm.google.com/notebook/e0ed6d5f-abdc-4957-9ccd-fd988f88970f
- 7/10 studio artifacts completed at verification time
- 9 curated prompts available as text source for chat use

## Lessons captured as memory

New memory entries added during this run:
- `feedback_quora_urls_fail.md` — Quora URLs silently fail like Medium
- `feedback_notebooklm_studio_quirks.md` — quiz classification quirk, sync vs async polling
- `project_cmux_notebook.md` — notebook pointer with ID and metadata

These memories now prevent rediscovery in future runs of this skill.
