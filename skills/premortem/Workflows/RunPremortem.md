# Workflow: RunPremortem

The full premortem — parallel deep-dive agents, synthesis, and a written record. Use for any
plan, launch, hire, pricing change, partnership, or strategic decision where the cost of being
wrong is high and the plan is still changeable.

**Voice on entry:**
```bash
curl -s -X POST http://localhost:31337/notify -H "Content-Type: application/json" \
  -d '{"message": "Running the RunPremortem workflow in the Premortem skill to stress-test the plan"}' > /dev/null 2>&1 &
```
Then: `Running the **RunPremortem** workflow in the **Premortem** skill to stress-test the plan...`

---

## Step 0 — Context gathering & sufficiency gate (BLOCKING)

A premortem on thin context produces generic risk — exactly what the technique exists to avoid.
First, **scan existing context** (~30s): the conversation, attached materials, and workspace
planning files (`CLAUDE.md`, briefs, docs). Then confirm three things:

1. **Clarity** — what is being premortemed? State it in one sentence.
2. **Stakeholders** — who is affected? (audience, customers, team)
3. **Success definition** — what does winning look like? (failure is its inversion)

If any is missing and you cannot infer it, **ask for the single most critical gap, one question
at a time.** Do not make the user fill a form. Do not proceed to Step 1 until all three are known.

## Step 1 — Frame the failure (the mechanism)

State the premise **explicitly and in past tense**:

> "It's [horizon — default 6 months from now]. [The plan] has failed. We're examining what went
> wrong."

This is not optional flavor — the tense-shift is the entire technique. Carry this framing into
every subsequent prompt: failure is certain; we explain it, we don't predict it.

## Step 2 — Generate raw failure causes (independently)

Generate **every genuine, plan-specific reason** the plan failed. Each cause must be:
- **Specific to this plan** — would not survive find-and-replace of the subject.
- **Grounded** in the actual plan details from Step 0.
- **A real threat** — not trivial, not absurdly unlikely.

Aim for comprehensive coverage (typically 5–12), not padding. Do not yet analyze them.

## Step 3 — Deep-dive fan-out (PARALLEL, INDEPENDENT)

Spawn **one agent per failure cause**, all at once, in a single message (`Agent` tool, or
`parallel()` in a Workflow). **Agents must run independently — never let one see another's
output.** This is the anti-anchoring safeguard from Klein's protocol; sequential analysis lets
the first cause frame the rest.

Give each agent exactly one cause and the per-agent prompt from `References/Templates.md §3`. Each
returns JSON: `{id, title, likelihood, severity, story, assumption, warningSigns[], mitigation, owner?}`
— under 300 words, past tense, no hedging.

> Degrees of freedom: for very large premortems, cap the fan-out (e.g. top 10 causes by stakes)
> and say so in the transcript. Never silently drop causes.

## Step 4 — Synthesis

Collect all agent results. **First prioritize:** rank failures by likelihood × severity so the
synthesis spends attention where the expected cost is highest. Then produce:

1. **Most likely failure** — the probable scenario given the plan.
2. **Most dangerous failure** — maximum damage, even if less probable. (Usually *not* the same as
   most-likely — that gap is often the key insight.)
3. **Biggest hidden assumption** — the single unexamined premise underlying the whole plan.
4. **Revised plan** — specific, actionable modifications addressing the top failure modes, each
   with an **owner**. State "test a $X pilot with N people before committing," not "be careful."
   An un-owned mitigation rarely happens — assign accountability or the premortem becomes theater.
5. **Pre-launch checklist** — 3–5 concrete verification steps, each preventing or detecting a
   failure mode.

## Step 5 — Write the record (markdown canonical)

Assemble a findings JSON (schema: `References/Templates.md §1`) and the markdown transcript
(`References/Templates.md §2`). Save:

- `premortem-transcript-<timestamp>.md` — **canonical record** (always).

Then, optionally, generate the report artifact:
```bash
bun ~/.claude/skills/Premortem/Tools/GenerateReport.ts findings.json --out premortem-report-<timestamp>.md
# visual HTML (opt-in, not canonical):
bun ~/.claude/skills/Premortem/Tools/GenerateReport.ts findings.json --html --out premortem-report-<timestamp>.html
```
Only produce HTML if the user wants a visual/shareable artifact — markdown is the default per PAI.

## Step 6 — Chat summary

Give a **three-sentence** summary in chat: the most-likely failure, the biggest hidden assumption,
and the single most important plan revision. Point to the saved transcript.

## Step 7 — Log

Append the execution-log JSONL entry (see SKILL.md → Execution Log).

---

## Gotchas (workflow-specific)

- If Step 3 agents come back with generic causes, the input plan was too thin — return to Step 0.
- Likelihood and severity are independent; sort by `severity` for "most dangerous," by
  `likelihood` for "most likely."
- Don't let the fan-out balloon cost on a small decision — that's what `QuickPremortem` is for.
