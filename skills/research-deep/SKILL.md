---
name: research-deep
user-invocable: true
allowed-tools: Bash, Read, Glob, Task
description: Read an existing research outline and fan out independent background agents to deeply research each item, producing one structured JSON per item against the shared field schema. Resumable, batched, with output disabled per agent (each agent has its explicit output file). Use when `outline.yaml` + `fields.yaml` from `/research-outline` are in place and you want to parallelise the per-item investigation — academic paper deep-dives, product comparisons, benchmark fills, multi-target competitive analysis. Trigger this after `/research-outline`, before `/research-report`.
---

# Research Deep — Per-Item Deep Research

Reads the outline produced by `/research-outline`, launches one background agent per batch, each populating an item's full JSON against the field schema.

## Trigger

`/research-deep`

## Pipeline position

```
/research-outline → /research-add-* → ► /research-deep ◄ → /research-report
```

## Workflow

### Step 1 — Auto-locate the outline

`Glob` `*/outline.yaml` from the current working directory. `Read` it to get `items`, `execution.batch_size`, `execution.items_per_agent`, and `execution.output_dir`.

### Step 2 — Resume check

`Glob` `{output_dir}/*.json` to find already-completed items. Skip them — only schedule items that don't yet have a JSON.

### Step 3 — Batch execution

- Group remaining items into batches of `batch_size`.
- For each batch: launch agents via the `Task` tool with `subagent_type: general-purpose` (or your project's research subagent if one is registered), `run_in_background: true`. Disable per-agent output — agents write directly to their assigned JSON path, so streaming their dialogue back into the parent context just burns tokens.
- Each agent handles up to `items_per_agent` items.
- **Wait for the user to approve the next batch** before launching it (lets the user spot-check the first batch's output and stop early if quality is off).

**Parameters captured per item:**

- `{topic}` — `topic` field from `outline.yaml`
- `{item_name}` — the item's `name` field
- `{item_related_info}` — the item's full YAML stanza (name + category + description + …)
- `{output_dir}` — `execution.output_dir` from `outline.yaml` (default `./results`)
- `{fields_path}` — absolute path to `{topic_dir}/fields.yaml`
- `{output_path}` — absolute path to `{output_dir}/{item_name_slug}.json`

**Slug rule for `{item_name_slug}`:** lowercase, replace runs of any non-alphanumeric character with `_`, strip leading/trailing `_`. Concretely: `re.sub(r"[^a-z0-9]+", "_", item_name.lower()).strip("_")`. Examples: `GitHub Copilot` → `github_copilot`, `Cursor (Anysphere)` → `cursor_anysphere`.

**Why the prompt below is templated literally:** the subagent runs in isolation. Its prompt carries every parameter explicitly, and small wording drifts cause the JSON shape to drift across runs. Treat the template as a stable contract — replace `{xxx}` variables, keep the rest as-is.

**Prompt template:**

```
## Task
Research {item_related_info}, output structured JSON to {output_path}

## Field Definitions
Read {fields_path} to get all field definitions

## Output Requirements
1. Output JSON according to fields defined in fields.yaml
2. Mark uncertain field values with [uncertain]
3. Add uncertain array at the end of JSON, listing all uncertain field names
4. All field values must be in English

## Output Path
{output_path}

## Validation
After completing JSON output, run validation script to ensure complete field coverage:
python ~/.claude/skills/research-outline/validate_json.py -f {fields_path} -j {output_path}
Task is complete only after validation passes.
```

**Worked example** (item = "GitHub Copilot"):

```
## Task
Research name: GitHub Copilot
category: International Product
description: Developed by Microsoft/GitHub, first mainstream AI coding assistant, ~40% market share, output structured JSON to {project_dir}/results/github_copilot.json

## Field Definitions
Read {project_dir}/fields.yaml to get all field definitions

## Output Requirements
1. Output JSON according to fields defined in fields.yaml
2. Mark uncertain field values with [uncertain]
3. Add uncertain array at the end of JSON, listing all uncertain field names
4. All field values must be in English

## Output Path
{project_dir}/results/github_copilot.json

## Validation
After completing JSON output, run validation script to ensure complete field coverage:
python ~/.claude/skills/research-outline/validate_json.py -f {project_dir}/fields.yaml -j {project_dir}/results/github_copilot.json
Task is complete only after validation passes.
```

### Step 4 — Wait and monitor

- Wait for the current batch to finish (each agent signals completion by emitting its JSON).
- Launch the next batch after the user's go-ahead.
- Display progress (`N/total` items complete).

### Step 5 — Summary report

After all batches finish, output:

- count complete
- list of items marked failed or with `uncertain` entries
- path to `{output_dir}/`

## Agent config

- Background execution: yes (`run_in_background: true`)
- Task output: disabled — each agent's deliverable is the JSON file it writes
- Resume support: yes (Step 2 skips completed items)

## Gotchas

- **The validator path `~/.claude/skills/research-outline/validate_json.py` is install-coupled.** It assumes the `research-outline` skill is installed at `~/.claude/skills/research-outline/`, which is what `claude-code-skills/scripts/link-skills.sh` and `install-skills.sh` set up. If you copied the skill anywhere else (e.g. a project-local `.claude/skills/`), the validator path in the templated prompt will break and the subagent will hang at the validation step. Fix by either keeping the canonical install path, or replacing the validator path in the template above with the correct absolute path for your install before kicking off `/research-deep`.
- **Background agents with task output disabled give you no early-warning if they go off the rails.** That's the deliberate tradeoff — token economy over verbosity. Spot-check the first batch's JSON before approving more.
- **Resume relies purely on filename match.** A half-written JSON from a crashed run looks "done" to Step 2. If a previous run was interrupted, delete the corrupt JSONs before re-running.
- **`{item_name_slug}` collisions silently overwrite.** Two items whose names slugify to the same string (e.g. `GPT-4` and `GPT 4`) will clobber each other. If you suspect collision, add a discriminator in the item's `category` field and slug them as `{category_slug}_{name_slug}` instead.
- **The validator's required-field check is the only post-condition.** If `fields.yaml` doesn't mark anything `required: true`, the validator passes anything, including agents that returned almost-empty JSON. Mark at least one field per category as `required` to get meaningful gating.
