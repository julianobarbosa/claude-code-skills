---
name: research-add-items
user-invocable: true
allowed-tools: Read, Write, Glob, Task, AskUserQuestion
description: Append new items (research objects) to an in-progress research outline's `outline.yaml` — sourced from your direct input, a web-search agent, or both. Use mid-`/research-outline` when you've realised the items list is incomplete (a new competitor surfaced, an important historical entry was missed, a category needs broader coverage) before running `/research-deep`, so the new items are part of the parallel deep pass instead of needing a separate run.
---

# Research Add Items — Append to the Items List

In-place updates `outline.yaml` with additional research objects.

## Trigger

`/research-add-items`

## Pipeline position

```
/research-outline → ► /research-add-items ◄ → /research-deep → /research-report
```

Reachable any time after `/research-outline` has produced `outline.yaml`, but most useful *before* `/research-deep` so the new items get researched in the same parallel pass.

## Workflow

### Step 1 — Auto-locate outline

`Glob` `*/outline.yaml` from the current working directory. `Read` it to know the existing items (avoid duplicates) and the current `execution` config.

### Step 2 — Gather candidates from two sources

These two sources are gathered sequentially (`AskUserQuestion` blocks waiting on the user; web search can run in the background after). Do them in this order:

1. `AskUserQuestion`: "Which items do you want to add? Any specific names?" — capture whatever the user already has in mind.
2. `AskUserQuestion`: "Should I also run a web-search agent for more candidates?" — if yes, launch a research subagent via the `Task` tool (`subagent_type: general-purpose`, `run_in_background: true`) seeded with the topic, the existing items list, and any items the user named in step 1 (so suggestions don't duplicate).

### Step 3 — Merge, deduplicate, confirm

- Combine the user-supplied items and the subagent's suggestions.
- Deduplicate by case-insensitive name match against the existing `outline.yaml`.
- Show the merged candidate list to the user. `AskUserQuestion` for which to accept.
- For each accepted item, capture: `name` (required), `category` (optional), `description` (optional, short).

### Step 4 — Save update

Append accepted items to `outline.yaml`, preserving existing structure. Save in place.

## Item shape (matches `/research-outline`)

```yaml
items:
  - name: <item>
    category: <optional>
    description: <optional, short>
```

## Output

Updated `{topic}/outline.yaml` — in-place modification, user confirms before save.

## Gotchas

- **Duplicate detection is case-insensitive name match only.** `GPT-4` and `GPT 4` (different by one character) are not detected as duplicates. Eyeball the merged list before saving if you suspect near-duplicates.
- **Items added after `/research-deep` has already run are not auto-researched.** You either need to re-run `/research-deep` (its Step 2 resume check will skip already-completed items and only fan out the new ones), or research the new items manually.
- **The web-search subagent operates outside the conversation context.** Hand it the topic AND the current items list explicitly, so its proposals don't repeat what's already there.
- **`outline.yaml.execution.batch_size`** controls how many deep agents `/research-deep` runs in parallel. If you add many items at once, you may want to bump `batch_size` here too — but that's outside this skill's scope; edit `outline.yaml` directly or re-run `/research-outline`'s Step 4 prompts.
