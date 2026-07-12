---
name: research-report
user-invocable: true
allowed-tools: Read, Write, Glob, Bash, AskUserQuestion
description: Summarise a completed deep-research run into a single markdown report — full coverage of every defined field, automatic skipping of uncertain values, and a navigable table of contents with user-chosen summary columns. Generates a fresh `generate_report.py` per run (against a stable spec) and executes it. Use after `/research-deep` finishes when you want a readable artifact for sharing, archiving, or comparing items across the chosen schema.
---

# Research Report — Summary Report

Reads the JSON files produced by `/research-deep` and emits a single markdown report at `{topic}/report.md`.

## Trigger

`/research-report`

## Pipeline position

```
/research-outline → /research-add-* → /research-deep → ► /research-report ◄
```

## Workflow

### Step 1 — Locate results directory

`Glob` `*/outline.yaml` in the current working directory. `Read` it to get `topic` and `execution.output_dir`.

### Step 2 — Scan optional summary fields

`Read` every JSON under `output_dir`. Collect candidate fields suitable for the table-of-contents column — short, numeric, or scalar metrics. Typical candidates:

- `github_stars`
- `google_scholar_cites`
- `swe_bench_score`
- `user_scale`
- `valuation`
- `release_date`

`AskUserQuestion`: "Which of these summary fields do you want next to each item in the TOC?" — present the dynamic list of fields you actually found in this run's JSON files.

> **AskUserQuestion has a hard cap of four options per question.** If you found more than four candidates, either ask twice (covering different field groups), or pick the four most informative-looking candidates yourself and ask the user to confirm or override.

### Step 3 — Generate the report script

Write `{topic}/generate_report.py`. The script's behaviour is specified in [`references/report-generation-spec.md`](references/report-generation-spec.md) — read that file before writing the script. It covers JSON shape compatibility, category-name multi-language mapping, complex value formatting, extra-fields collection, uncertain-value skipping, and TOC formatting.

Why the script is regenerated each run instead of bundled as-is: each topic has slightly different field categories and value shapes. Letting the model write the script per run lets it adapt the formatting choices to what the JSON actually contains, while the spec ensures every script meets the same minimum contract.

### Step 4 — Execute the script

Run `python {topic}/generate_report.py`. Check the resulting `{topic}/report.md` exists and is non-empty; report the path back to the user.

## Output

- `{topic}/generate_report.py` — per-run conversion script
- `{topic}/report.md` — summary report

## Gotchas

- **The `CATEGORY_MAPPING` lives in two places**: in the generated `generate_report.py` and in `~/.claude/skills/research-outline/validate_json.py`. They must agree, or the report will skip categories the validator just accepted. If you add a new category in `fields.yaml`, update both files (see `references/report-generation-spec.md` for the canonical mapping).
- **`AskUserQuestion` caps at four options**. If Step 2 turns up more than four summary-field candidates, you need to either chunk the question into multiple rounds or pre-filter the list yourself before asking. Don't silently truncate to four — the user needs to know what was left off.
- **`[uncertain]` in a value and presence in the `uncertain` array are both skip-triggers**, and either alone is enough. Don't AND them.
- **Anchor slugs are markdown's auto-slug, not your own slugifier.** Make sure your TOC link `#xxx` matches what the markdown renderer derives from your `## Item Name` header — lowercase, spaces → hyphens, most punctuation stripped. If item names have unusual characters, render the section with a known-safe heading text.
- **Empty `output_dir`** means `/research-deep` either hasn't run or hasn't completed any items. Don't generate an empty report — surface the state to the user.
