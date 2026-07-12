# GenerateReport.ts — Help

Turns a premortem **findings JSON** file into a report. Markdown by default; self-contained HTML
with `--html`. Runs on the Bun runtime, no external dependencies.

## Usage

```bash
bun ~/.claude/skills/Premortem/Tools/GenerateReport.ts <findings.json> [--html] [--out <path>]
```

| Flag | Effect |
|------|--------|
| *(none)* | Render a clean **markdown** report to stdout. |
| `--out <path>` | Write the report to `<path>` instead of stdout. |
| `--html` | Render a **self-contained HTML** report (dark theme, inline CSS, no external assets). |
| `--html --out <path>` | Write the HTML report to `<path>`. |
| `--html` (no `--out`) | Write to `premortem-report-<timestamp>.html` in the cwd and print the path. |

## Examples

```bash
# Markdown to stdout
bun ~/.claude/skills/Premortem/Tools/GenerateReport.ts findings.json

# Markdown to a file
bun ~/.claude/skills/Premortem/Tools/GenerateReport.ts findings.json --out report.md

# Visual HTML report
bun ~/.claude/skills/Premortem/Tools/GenerateReport.ts findings.json --html --out report.html
```

## Input

A findings JSON file matching the schema in `References/Templates.md §1`. Required keys: `subject`,
`failures[]`, `synthesis`. Optional: `successDefinition`, `stakeholders`, `horizon`, `timestamp`.
Each failure: `{id, title, likelihood, severity, story, assumption, warningSigns[], mitigation, owner?}`.

## Behavior

- Validates the input shape; on a missing file or malformed JSON it prints a helpful error to
  stderr and exits `1`. Success exits `0`.
- The synthesis (most-likely, most-dangerous, hidden assumption, revised plan, pre-launch
  checklist) is pinned at the top; one card/section per failure with likelihood + severity badges.
- HTML output escapes all user-supplied strings.

## Note

Markdown is the canonical premortem record (PAI convention). Use `--html` only when a user wants a
visual or shareable artifact.
