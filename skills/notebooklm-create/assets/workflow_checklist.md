# notebooklm-create — Workflow Checklist

Copy this checklist into a `PRD.md` under `MEMORY/WORK/<slug>/` at the start of a run. Tick items as you complete them.

## Phase 1 — Capture intent

- [ ] Topic name confirmed: `_______________`
- [ ] Seed URLs collected (user-provided):
  - [ ] URL 1: `_______________`
  - [ ] URL 2: `_______________`
- [ ] Forum coverage scope: Reddit ☐ HN ☐ GitHub Discussions ☐ Discord ☐ Quora ☐
- [ ] Notebook title decided: `____ :: docs`
- [ ] Studio scope: full (all 10) ☐ selective ☐ (list: ____)
- [ ] Ambiguity check: multiple projects share this name? ☐ yes ☐ no
  - If yes, disambiguation strategy: ____

## Phase 2 — Deep research

- [ ] Seed URLs fetched (WebFetch) to anchor disambiguation
- [ ] Canonical repo URL identified
- [ ] Official docs / website URL identified
- [ ] llms.txt URL located (or confirmed absent)
- [ ] Research synthesis agent dispatched → artifact saved
- [ ] Community content agent dispatched → artifact saved

## Phase 3 — Create notebook

- [ ] `notebook_list` run — no duplicate title exists
- [ ] `notebook_create(title="____ :: docs")` called
- [ ] **Notebook ID captured:** `_______________`

## Phase 4 — Load sources (sequential)

- [ ] `references/url-gotchas.md` consulted
- [ ] URLs filtered: no Medium, no Quora, no LinkedIn
- [ ] Any `llms.txt` URLs have `.md` stripped
- [ ] Sequential URL adds executed — one at a time
- [ ] Research synthesis added as text source
- [ ] Community content added as text source

## Phase 5 — Studio (requires user approval)

- [ ] User approval obtained for full studio dispatch
- [ ] `references/studio-quirks.md` consulted
- [ ] Async media dispatched first:
  - [ ] audio_overview_create
  - [ ] video_overview_create
  - [ ] infographic_create
  - [ ] slide_deck_create
- [ ] Synchronous dispatched second:
  - [ ] mind_map_create
  - [ ] report_create (Briefing Doc)
  - [ ] report_create (Study Guide)
  - [ ] flashcards_create
  - [ ] quiz_create
  - [ ] data_table_create
- [ ] studio_status polled after 45s
- [ ] studio_status polled again after 2–3 min

## Phase 6 — Curate prompts

- [ ] 9 base prompts adapted to topic (via scripts/adapt_prompts.py)
- [ ] Prompts saved to `MEMORY/WORK/<slug>/prompts.md`
- [ ] Prompts added to notebook via `notebook_add_text`

## Phase 7 — Verify

- [ ] `notebook_get(notebook_id=NB)` called
- [ ] Source count matches expected
- [ ] No duplicate placeholder sources from failed URL adds
- [ ] Studio artifacts: N completed, M in_progress
- [ ] Reported notebook URL to user
- [ ] Reported studio artifact status to user
- [ ] Memory entries updated if new gotchas discovered
