# Premortem — Templates

Copy-paste scaffolds for a premortem run: the **findings JSON** (consumed by
`Tools/GenerateReport.ts`), the **markdown transcript**, and the **per-agent prompt**.

---

## 1. Findings JSON schema (contract with `GenerateReport.ts`)

This is the exact shape `Tools/GenerateReport.ts` consumes. Field names must match.

```json
{
  "subject": "One-line description of what was premortemed",
  "successDefinition": "What winning looks like (optional)",
  "stakeholders": "Who is affected (optional)",
  "horizon": "6 months from now",
  "timestamp": "2026-05-29T15:00:00Z",
  "failures": [
    {
      "id": "F1",
      "title": "Short failure name",
      "likelihood": "low | medium | high",
      "severity": "low | medium | high",
      "story": "2-3 paragraph past-tense narrative of how this specific failure played out, grounded in plan details.",
      "assumption": "One sentence naming the unquestioned premise that enabled this failure.",
      "warningSigns": [
        "Observable, measurable early signal #1",
        "Observable, measurable early signal #2"
      ],
      "mitigation": "Concrete, specific action that prevents or detects this failure mode.",
      "owner": "Who is accountable for the mitigation (optional but strongly recommended)."
    }
  ],
  "synthesis": {
    "mostLikely": "The probable failure scenario given the plan details.",
    "mostDangerous": "The scenario causing maximum damage, even if less probable.",
    "hiddenAssumption": "The single biggest unexamined assumption underlying the whole plan.",
    "revisedPlan": [
      "Specific, actionable modification #1",
      "Specific, actionable modification #2"
    ],
    "preLaunchChecklist": [
      "Concrete verification step #1",
      "Concrete verification step #2"
    ]
  }
}
```

**Field notes**
- `subject`, `failures`, `synthesis` are **required**. `successDefinition`, `stakeholders`,
  `horizon`, `timestamp` are optional (`timestamp` auto-fills to generation time if absent; the
  others render only if present).
- `likelihood` / `severity` ∈ `low | medium | high` — drives the report's badges and the
  most-likely / most-dangerous synthesis.
- `owner` is optional but strongly recommended — an un-owned mitigation rarely happens. A
  premortem that ends in a prioritized, *owned* action list produces decisions; one that ends in
  a list of fears produces anxiety. Prioritize failures by likelihood × severity.
- `warningSigns`, `revisedPlan`, `preLaunchChecklist` are arrays of strings.

Render: `bun ~/.claude/skills/Premortem/Tools/GenerateReport.ts findings.json --out report.md`
HTML: `bun ~/.claude/skills/Premortem/Tools/GenerateReport.ts findings.json --html --out report.html`

---

## 2. Markdown transcript template

`premortem-transcript-<timestamp>.md` — the canonical, human-readable record.

```markdown
# Premortem Transcript — <subject>

> Horizon: <e.g. 6 months from now> · Generated: <ISO-8601>

## Context
- **What was premortemed:** <one sentence>
- **Stakeholders:** <who is affected>
- **Success definition:** <what winning looks like — failure is its inversion>

## Frame
It is <horizon>. <The plan> has failed. The following explains what went wrong.

## Raw Failure Causes (independent generation)
1. <plan-specific cause>
2. <plan-specific cause>
...

## Deep Dives
### F1 — <title>  (likelihood: <l> · severity: <s>)
**Failure story.** <2-3 paragraphs>
**Hidden assumption.** <one sentence>
**Early-warning signs.** <1-2 observable signals>
**Mitigation.** <concrete action>  ·  **Owner.** <who is accountable>

### F2 — <title> ...

## Synthesis
- **Most likely failure:** <...>
- **Most dangerous failure:** <...>
- **Biggest hidden assumption:** <...>
- **Revised plan:**
  1. <change>
- **Pre-launch checklist:**
  - [ ] <verification step>
```

---

## 3. Per-agent deep-dive prompt (for the parallel fan-out in RunPremortem)

Give each agent **exactly one** failure cause. Agents run **independently** (anti-anchoring)
— never let them see each other's output.

```
You are analyzing ONE failure mode of this plan. The plan has ALREADY FAILED — write in
past tense, with certainty, not "could."

PLAN CONTEXT:
<subject, success definition, stakeholders, key plan details>

YOUR ASSIGNED FAILURE CAUSE:
<the single cause>

Produce, in under 300 words, no hedging:
1. FAILURE STORY — 2-3 short paragraphs showing how this specific failure played out, using
   real plan details.
2. HIDDEN ASSUMPTION — one sentence naming the unquestioned premise that enabled it.
3. EARLY-WARNING SIGNS — 1-2 observable, measurable signals that this mode is emerging.
4. LIKELIHOOD and SEVERITY — each one of: low | medium | high.
5. MITIGATION — one concrete, specific action (not "monitor closely").
6. OWNER — who should be accountable for the mitigation (role is fine if no name).

Return JSON matching the failure object schema: {id,title,likelihood,severity,story,
assumption,warningSigns[],mitigation,owner}.
```
