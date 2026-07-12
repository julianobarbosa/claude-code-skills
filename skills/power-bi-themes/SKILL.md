---
name: power-bi-themes
description: >
  Apply, inspect, and compare Power BI report themes and conditional formatting
  rules using pbi-cli. Invoke this skill whenever the user mentions "theme",
  "colours", "colors", "branding", "dark mode", "corporate theme", "styling",
  "conditional formatting", "colour scale", "gradient", "data bars",
  "background colour", "formatting rules", "visual formatting", or wants to
  change the overall look-and-feel of a report or apply data-driven formatting
  to specific visuals.
tools: pbi-cli
---

# Power BI Themes Skill

Manage report-wide themes and per-visual conditional formatting. No Power BI
Desktop connection is needed.

## Applying a Theme

Power BI themes are JSON files that define colours, fonts, and visual defaults
for the entire report. Apply one with:

```bash
pbi report set-theme --file corporate-theme.json
```

This copies the theme file into the report's `StaticResources/RegisteredResources/`
folder and updates `report.json` to reference it. The theme takes effect when
the report is opened in Power BI Desktop.

## Inspecting the Current Theme

```bash
pbi report get-theme
```

Returns:
- `base_theme` -- the built-in theme name (e.g. `"CY24SU06"`)
- `custom_theme` -- custom theme name if one is applied (or `null`)
- `theme_data` -- full JSON of the custom theme file (if it exists)

## Comparing Themes

Before applying a new theme, preview what would change:

```bash
pbi report diff-theme --file proposed-theme.json
```

Returns:
- `current` / `proposed` -- display names
- `added` -- keys in proposed but not current
- `removed` -- keys in current but not proposed
- `changed` -- keys present in both but with different values

This helps catch unintended colour changes before committing.

## Theme JSON Structure

A Power BI theme JSON file typically contains:

```json
{
  "name": "Corporate Brand",
  "dataColors": ["#0078D4", "#00BCF2", "#FFB900", "#D83B01", "#8661C5", "#00B294"],
  "background": "#FFFFFF",
  "foreground": "#252423",
  "tableAccent": "#0078D4",
  "visualStyles": { ... }
}
```

Key sections:
- `dataColors` -- palette for data series (6-12 colours recommended)
- `background` / `foreground` -- page and text defaults
- `tableAccent` -- header colour for tables and matrices
- `visualStyles` -- per-visual-type overrides (font sizes, padding, etc.)

See [Microsoft theme documentation](https://learn.microsoft.com/power-bi/create-reports/desktop-report-themes) for the full schema.

## Conditional Formatting

Apply data-driven formatting to individual visuals:

```bash
# Gradient background (colour scale from min to max)
pbi format background-gradient visual_abc --page page1 \
    --table Sales --column Revenue \
    --min-color "#FFFFFF" --max-color "#0078D4"

# Rules-based background (specific value triggers a colour)
pbi format background-conditional visual_abc --page page1 \
    --table Sales --column Status --value "Critical" --color "#FF0000"

# Measure-driven background (a DAX measure returns the colour)
pbi format background-measure visual_abc --page page1 \
    --table Sales --measure "Status Color"

# Inspect current formatting rules
pbi format get visual_abc --page page1

# Clear all formatting rules on a visual
pbi format clear visual_abc --page page1
```

## Workflow: Brand a Report

```bash
# 1. Create the theme file
cat > brand-theme.json << 'EOF'
{
  "name": "Acme Corp",
  "dataColors": ["#1B365D", "#5B8DB8", "#E87722", "#00A3E0", "#6D2077", "#43B02A"],
  "background": "#F8F8F8",
  "foreground": "#1B365D",
  "tableAccent": "#1B365D"
}
EOF

# 2. Preview the diff against the current theme
pbi report diff-theme --file brand-theme.json

# 3. Apply it
pbi report set-theme --file brand-theme.json

# 4. Verify
pbi report get-theme
```

## JSON Output

```bash
pbi --json report get-theme
pbi --json report diff-theme --file proposed.json
pbi --json format get vis1 --page p1
```

---

## Gotchas

- **Theme JSON keys are case-sensitive and partially undocumented:** One wrong key in `dataColors` or `visualStyles` is silently ignored — no error, the theme just falls back to default for that property. Diff against a known-good theme JSON before troubleshooting "theme not applying".
- **`dataColors` array order maps to series ordinal, not to series name:** Renaming a series or changing legend order rotates the colors. Lock brand colors per-series via measure-level color rules in `visualStyles`, not via array position.
- **`set-theme --file` copies the file at command time:** Later edits to the source `corporate-theme.json` don't propagate to the report — you must re-run `set-theme`. CI pipelines must re-apply the theme on every build for the latest version to land.
- **`diff-theme` does not catch missing-key regressions:** Removing a key from the proposed theme appears under `removed` but Power BI's runtime treats removal as "fall back to default" — visually this looks like a theme bug, not a missing-key bug.
- **Conditional formatting via `format background-measure` requires the color measure to return a valid hex string or named color:** Returning a number or blank produces "no formatting applied" with no error. Wrap the measure's return in `IFERROR(..., "#FFFFFF")` to fail safely.
- **`format clear` removes ALL formatting rules on a visual, not just background:** Font, data-label, and conditional title rules go too. The CLI does not currently support selective rule deletion — clear and re-add is the only workflow.

