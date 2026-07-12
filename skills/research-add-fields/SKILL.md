---
name: research-add-fields
user-invocable: true
allowed-tools: Read, Write, Glob, Task, AskUserQuestion
description: Append new field definitions to an in-progress research outline's `fields.yaml` — either from user-supplied input or from a web-search agent that proposes common dimensions in the domain. Use mid-`/research-outline` when you've realised the schema is missing dimensions (e.g. pricing, performance, ecosystem, governance) before running `/research-deep`, so deep agents fill the new fields on first pass instead of needing a re-run.
---

# Research Add Fields — Append to the Field Schema

In-place updates `fields.yaml` with additional research dimensions.

## Trigger

`/research-add-fields`

## Pipeline position

```
/research-outline → ► /research-add-fields ◄ → /research-deep → /research-report
```

Reachable any time after `/research-outline` has produced `fields.yaml`, but most useful *before* `/research-deep` so deep agents fill the new fields in their first pass.

## Workflow

### Step 1 — Auto-locate fields file

`Glob` `*/fields.yaml` from the current working directory. `Read` it to know what's already defined — so suggestions don't duplicate existing fields and you can show the user the current categories when asking.

### Step 2 — Pick a supplement source

`AskUserQuestion` with two options:

- **A. Direct input** — user dictates field names, descriptions, and categories.
- **B. Web search** — launch a research subagent via the `Task` tool (`subagent_type: general-purpose`) to propose common fields in the topic's domain.

### Step 3 — Display and confirm

- Show the candidate field list back to the user (whether from A or B).
- `AskUserQuestion` for each candidate: keep / drop / edit.
- For each kept field, capture: `category` (must match an existing `field_categories[].category` or be a new one), `detail_level` (`brief | moderate | detailed`), `required` (default `false`).

### Step 4 — Save update

Append the confirmed fields to `fields.yaml`, preserving existing structure and ordering. Save in place.

## Field shape (matches `/research-outline`)

```yaml
field_categories:
  - category: <name>
    fields:
      - name: <field_name>
        description: <what to capture>
        detail_level: brief | moderate | detailed
        required: false
```

## Output

Updated `{topic}/fields.yaml` — in-place modification, user confirms before save.

## Gotchas

- **Adding `required: true` retroactively breaks already-completed items.** If `/research-deep` already produced JSONs for some items and you add a new required field, those JSONs will fail validation. Either add the field as `required: false`, or plan to re-run `/research-deep` for the affected items.
- **Category names are matched literally.** A new field whose `category` doesn't match an existing `field_categories[].category` creates a new top-level category in the schema. That's fine, but make sure it's intentional — a typo here is a silent split.
- **The web-search subagent in option B operates outside the conversation context.** Hand it the topic and an explicit list of categories that already exist, so its proposals fit the schema rather than colliding with what's there.
- **`fields.yaml` is also consumed by `~/.claude/skills/research-outline/validate_json.py`**. The schema this skill writes must stay compatible with that validator — same `field_categories[].fields[].name` / `required` shape, no exotic YAML constructs.
