---
name: research-outline
user-invocable: true
allowed-tools: Read, Write, Task, AskUserQuestion
description: Bootstrap a structured research project on any topic — generate an initial items list and research-field schema from model knowledge, supplement with up-to-date web search, then emit `outline.yaml` + `fields.yaml` that drive the rest of the research pipeline. Use when starting academic research, benchmark comparisons, technology selection, competitive analysis, market scans, literature reviews, or any structured investigation that needs a typed schema before deep dives — even when the user just says "let's research X" without explicitly asking for an outline.
---

# Research — Preliminary Research

Bootstraps a research project. Produces the outline (items + execution config) and field schema (the research dimensions) that `/research-deep` and `/research-report` consume.

## Trigger

`/research-outline <topic>`

## Pipeline contract

This skill is the entry point of a four-step pipeline:

```
/research-outline <topic>          # this skill — produces outline.yaml + fields.yaml
   ├─ /research-add-items     # optional — append more research objects
   ├─ /research-add-fields    # optional — append more research dimensions
   ├─ /research-deep          # fan-out per-item deep research → results/*.json
   └─ /research-report        # summarise results into a markdown report
```

Output layout:

```
{current_working_directory}/{topic_slug}/
  ├── outline.yaml    # items list + execution config
  └── fields.yaml     # field definitions
```

## Workflow

### Step 1 — Generate initial framework from model knowledge

Based on the topic, use the model's existing knowledge to draft:
- a main research-objects (items) list in the domain
- a suggested research-field framework

Show the draft as `{step1_output}`, then `AskUserQuestion` to confirm:
- Need to add or remove items?
- Does the field framework match what they want to learn?

### Step 2 — Web-search supplement

`AskUserQuestion` for the time range (e.g. last 6 months, since 2024, unlimited).

**Parameters captured at this point:**

- `{topic}` — the user's research topic
- `{YYYY-MM-DD}` — today's date
- `{step1_output}` — full output from Step 1
- `{time_range}` — user's chosen window

Launch one background research agent via the `Task` tool with `subagent_type: general-purpose` (or your project's research subagent if one is registered).

**Why the prompt below is templated literally:** the subagent runs in isolation without the conversation's context. Its prompt has to carry every parameter explicitly, and small wording changes ("supplement" vs "add") subtly change how aggressively it searches. Treat the template as a stable contract — replace `{xxx}` variables and keep the rest as-is so results stay comparable across runs.

**Prompt template (replace variables, preserve structure):**

```
## Task
Research topic: {topic}
Current date: {YYYY-MM-DD}

Based on the following initial framework, supplement latest items and recommended research fields.

## Existing Framework
{step1_output}

## Goals
1. Verify if existing items are missing important objects
2. Supplement items based on missing objects
3. Continue searching for {topic} related items within {time_range} and supplement
4. Supplement new fields

## Output Requirements
Return structured results directly (do not write files):

### Supplementary Items
- item_name: Brief explanation (why it should be added)
...

### Recommended Supplementary Fields
- field_name: Field description (why this dimension is needed)
...

### Sources
- [Source1](url1)
- [Source2](url2)
```

**Worked example** (topic = "AI Coding History"):

```
## Task
Research topic: AI Coding History
Current date: 2025-12-30

Based on the following initial framework, supplement latest items and recommended research fields.

## Existing Framework
### Items List
1. GitHub Copilot: Developed by Microsoft/GitHub, first mainstream AI coding assistant
2. Cursor: AI-first IDE, based on VSCode
...

### Field Framework
- Basic Info: name, release_date, company
- Technical Features: underlying_model, context_window
...

## Goals
1. Verify if existing items are missing important objects
2. Supplement items based on missing objects
3. Continue searching for AI Coding History related items within since 2024 and supplement
4. Supplement new fields

## Output Requirements
[as above]
```

### Step 3 — Ask user for existing fields

`AskUserQuestion`: do you have an existing field-definitions file we should merge with? If yes, `Read` it and fold it into the field set.

### Step 4 — Generate outline (two files)

Merge `{step1_output}`, the subagent's `{step2_output}`, and any user-supplied fields. Write two files:

**`outline.yaml`** — items + execution config:

```yaml
topic: <research topic>
items:
  - name: <item>
    category: <optional>
    description: <optional>
execution:
  batch_size: <parallel agents — confirm with AskUserQuestion>
  items_per_agent: <items per agent — confirm with AskUserQuestion>
  output_dir: ./results   # default
```

**`fields.yaml`** — field definitions:

```yaml
field_categories:
  - category: <name>
    fields:
      - name: <field_name>
        description: <what to capture>
        detail_level: brief | moderate | detailed
        required: false   # optional; validator checks required fields are present
uncertain: []   # reserved — auto-filled during /research-deep
```

`detail_level` runs `brief → moderate → detailed`. The `uncertain` array is populated by `/research-deep`; leave it empty here.

### Step 5 — Save and confirm

- Create `./{topic_slug}/`
- Save `outline.yaml` and `fields.yaml`
- Show both to the user for confirmation before they move on

## Follow-up commands

- `/research-add-items` — append more research objects
- `/research-add-fields` — append more field definitions
- `/research-deep` — start parallel deep research
- `/research-report` — summarise results

## Gotchas

- **`{topic_slug}` is conventionally a kebab-case slug** of the topic (e.g. `AI Coding History` → `ai-coding-history`). The follow-up skills auto-locate `*/outline.yaml`, so the directory name only needs to be filesystem-safe and unique.
- **The subagent prompt template in Step 2 is a contract, not a suggestion.** `/research-deep` and `/research-report` both assume the schema produced here is stable. If you reword the template ad-hoc, downstream skills may receive fields they don't know how to render.
- **`required: true` on a field is enforced at deep-phase validation** (`validate_json.py`) — missing required fields fail the validator. Use sparingly; over-marking creates noise in the report.
- **The `uncertain` array in `fields.yaml` is reserved for downstream use.** Don't put anything in it during this skill; `/research-deep` populates it per-item.
