# Studio Quirks — NotebookLM artifact generation

Quirks observed when calling the `notebooklm-rpc` Studio tools. Consult before Phase 5.

## The confirm guard

Every Studio creation tool takes `confirm: bool` (default `false`). Calling with `confirm=false` returns an error.

Per the `notebooklm-rpc` MCP server instructions: **Tools with confirm param require user approval before setting confirm=True.**

**Workflow:**
1. Present the studio plan to the user (list of artifacts, options, focus prompts)
2. Get explicit approval (or treat a clear user request like "build the full studio" as scoped approval)
3. Then dispatch each tool with `confirm=true`

Do NOT hide this guard from the user. If in doubt, ask.

## Sync vs async

| Artifact | Mode | Typical time |
|----------|------|--------------|
| `mind_map_create` | **Synchronous** — returns full mind map in the create response | <5s |
| `report_create` (all formats) | Async | 30–90s |
| `flashcards_create` | Async | 30–90s |
| `quiz_create` | Async | 30–90s |
| `data_table_create` | Async | 30–90s |
| `audio_overview_create` | Async | 1–3 min |
| `infographic_create` | Async | 2–5 min |
| `slide_deck_create` | Async | 2–5 min |
| `video_overview_create` | Async | 3–10 min |

**Implication:** Dispatch the longest async ones FIRST so they render in parallel with the shorter ones.

## Quiz classified as flashcards

When you call `quiz_create`, the synchronous response correctly reports `type: "quiz"`. But after generation completes, `studio_status` shows the quiz artifact with `type: "flashcards"` and a `flashcard_count` field.

**Do not rely on the `type` field to distinguish quiz from flashcards post-generation.** Use the artifact title (e.g., `"Quiz cmux"`) or the original `artifact_id` you captured at creation.

## Counts are approximations

Requested `question_count: 10` → NotebookLM commonly returns 9. Flashcards behave similarly. Budget ±1–2 from the requested count.

## Focus prompts

`audio_overview_create`, `video_overview_create`, `infographic_create`, `slide_deck_create`, and the "Create Your Own" report format accept a `focus_prompt` parameter. **Use it.** A targeted focus prompt dramatically improves grounding vs the default "summarize everything" behavior.

Good focus prompts:
- Name the topic explicitly
- List 3–5 specific sub-themes to emphasize
- Mention key actors, quotes, or facts from the sources
- Indicate the audience (e.g., "for developers evaluating X")

Bad focus prompts:
- Generic ("make it good")
- Longer than ~3 sentences (NotebookLM truncates)
- Instructions about structure the tool already knows (e.g., telling an audio overview to "have two hosts")

## Polling

After dispatch, call `mcp__notebooklm-rpc__studio_status(notebook_id=NB)` after ~45s. Most synchronous artifacts will be complete. Async media (audio/video/infographic/slide deck) may still show `in_progress` — poll again after 2–3 minutes, or tell the user they'll finish rendering in the NotebookLM UI.

## Audio overview formats

- `deep_dive` — two-host podcast, default, most engaging
- `brief` — shorter summary format
- `critique` — adversarial / analytical framing
- `debate` — two opposing positions

`deep_dive` is the right default. Pick `brief` only if the user explicitly wants ≤5 min.

## Video overview visual styles

Accepted values: `auto_select | classic | whiteboard | kawaii | anime | watercolor | retro_print | heritage | paper_craft`.

Default to `auto_select`; NotebookLM picks based on content. Override only if the user specifies a style.

## Report formats

- `"Briefing Doc"` — executive summary style
- `"Study Guide"` — student-facing, with study questions
- `"Blog Post"` — narrative, shareable
- `"Create Your Own"` — requires `custom_prompt`

For a typical topic notebook, generating both `Briefing Doc` and `Study Guide` covers the two dominant consumption modes (skim vs learn).

## Recovery

If an artifact fails or produces poor output, delete and regenerate:

```
mcp__notebooklm-rpc__studio_delete(notebook_id=NB, artifact_id=AID)
# then re-call the create tool
```
