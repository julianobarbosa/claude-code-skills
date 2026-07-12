# Workflow: Update

Maintain and extend the Premortem skill itself — add a workflow, fix the tool, refine triggers, or
record a new gotcha learned from a real run.

**Voice on entry:**
```bash
curl -s -X POST http://localhost:31337/notify -H "Content-Type: application/json" \
  -d '{"message": "Running the Update workflow in the Premortem skill to maintain it"}' > /dev/null 2>&1 &
```
Then: `Running the **Update** workflow in the **Premortem** skill to maintain it...`

---

## When to use

- A real premortem run surfaced a recurring mistake → add it to `## Gotchas` in SKILL.md.
- A new use-case needs a dedicated workflow → add `Workflows/<Name>.md` and a routing-table row.
- The report tool needs a new field or format → edit `Tools/GenerateReport.ts` + its help + the
  schema in `References/Templates.md` (keep all three in sync).
- Triggers over/under-fire → refine the `description` (see CreateSkill → OptimizeDescription).

## Rules (do not break these)

1. **Stay public-safe.** This is a `TitleCase` public skill. No personal names, paths, domains,
   customers, or credentials in any file. User-specific tweaks go in
   `~/.claude/PAI/USER/SKILLCUSTOMIZATIONS/Premortem/`, never the skill body.
2. **Keep structure flat.** Only `Workflows/`, `Tools/`, `References/`. Max 2 levels deep.
3. **Keep SKILL.md < 500 lines.** Push detail into `References/`; SKILL.md is a routing guide.
4. **Schema is a contract.** If you change the findings JSON shape, update `GenerateReport.ts`,
   `GenerateReport.help.md`, AND `References/Templates.md` together, then re-run the dry-run.
5. **Citation honesty stays.** Never "upgrade" the 30%-reasons-generated gotcha into a stronger
   claim than the 1989 study supports.

## Steps

1. Make the change (workflow / tool / docs).
2. If the tool changed: `bun ~/.claude/skills/Premortem/Tools/GenerateReport.ts <sample>.json` in
   both markdown and `--html` modes — confirm exit 0.
3. Run the public pre-flight grep:
   `rg -i "/Users/[a-z]+/|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}" ~/.claude/skills/Premortem/`
   — expect zero personal-data matches.
4. Optionally validate with `Skill("CreateSkill", "validate skill Premortem")`.
5. Append the execution-log JSONL entry.
