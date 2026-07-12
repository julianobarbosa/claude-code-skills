---
name: premortem
description: Run a premortem on any plan, launch, product, hire, pricing change, strategy, or high-stakes decision. Uses Gary Klein's prospective-hindsight method — assume it already failed at a future date and work backward to surface every plan-specific cause, then produce a revised plan, mitigations, early-warning signals, and a pre-launch checklist. USE WHEN premortem this, run a premortem, what could kill this, future-proof this, stress test this plan, what am I missing here, find the blind spots, what could go wrong, am I missing anything, poke holes in this, where will this break, before I commit to this. NOT FOR adversarial attack on an arbitrary idea or argument (use RedTeam), current-state multi-perspective debate (use Council), network/system vulnerability testing (use Security), or simple feedback/factual questions. DO trigger when someone has a concrete plan or commitment where the cost of being wrong is high and the decision is still changeable.
---

# Premortem

Imagine the plan **already failed**, then explain why. This "prospective hindsight" tense-shift
(Klein, HBR 2007) generates ~30% more failure causes than asking "what could go wrong?" — and
the causes are more specific. The skill turns that mechanism into a repeatable run that ends in
a revised plan, not just a list of worries.

## Workflow Routing

| Trigger                                                                       | Workflow                                                      |
| ----------------------------------------------------------------------------- | ------------------------------------------------------------- |
| "premortem this", "run a premortem", "what could kill this", high-stakes plan | `Workflows/RunPremortem.md` (full: parallel deep-dive agents) |
| "quick premortem", small/personal decision, fast gut-check, thin context      | `Workflows/QuickPremortem.md` (solo single-pass, no fan-out)  |
| "update the premortem skill", add/fix a workflow                              | `Workflows/Update.md`                                         |

**Default to `RunPremortem`** for anything with real stakes. Drop to `QuickPremortem` only when
the decision is small or the user explicitly wants speed.

## The Mechanism (don't skip the framing)

The entire technique is one move: **state that failure has already happened, with certainty, and
ask what caused it.** Everything else is delivery. If a step doesn't help the user inhabit
"it already failed," cut it. Full evidence and citations: `References/Methodology.md`.

## Quick Reference

- **Frame in past tense.** "It's [horizon]. [The plan] has failed. Here's why." Not "could fail."
- **Generate causes independently first.** In `RunPremortem`, parallel agents must NOT see each
  other's output — this is the anti-anchoring safeguard, and it is load-bearing.
- **Demand plan-specific causes.** Reject generic risks ("timeline slips"). Ground every cause in
  actual plan details.
- **Always land on action.** Each retained risk → a mitigation + an early-warning signal. End with
  a revised plan and a pre-launch checklist. A premortem with no follow-through is theater.
- **Markdown is canonical.** The transcript (`.md`) is the record. HTML is an optional visual
  artifact via `Tools/GenerateReport.ts --html`, never the primary output.

## When NOT to run a premortem

- **Vague concepts with no concrete plan** — gather the plan first, or you'll generate generic risk.
- **Decisions already irreversibly made** — nothing to revise; value is low.
- **Factual questions or creative feedback** — wrong tool.
- **Attacking an idea/argument in the abstract** → `RedTeam`. **Current multi-view debate** → `Council`.

## Tools

- `Tools/GenerateReport.ts` — turns a findings JSON (schema in `References/Templates.md`) into a
  markdown report (default) or a self-contained HTML report (`--html`). Run with `bun`. See
  `Tools/GenerateReport.help.md`.

## Gotchas

> The highest-density part of this skill. Add to it after every run that surprises you.

- **The "30%" stat is about quantity, not correctness.** The 1989 Mitchell/Russo/Pennington study
  found prospective hindsight produces ~30% **more reasons generated** — NOT 30% better at
  identifying the _correct_ reasons. Klein's HBR paraphrase ("correctly identify") overstates it.
  Never tell a user the premortem makes them "30% more accurate." It makes them more _prolific_ and
  _specific_. Citing it wrong makes the whole analysis look sloppy.
- **Anchoring kills the run.** If you generate causes sequentially (or let one agent see another's
  output), the first failure named frames everything after it. Generate independently, then merge.
  This is why `RunPremortem` fans out parallel agents and explicitly forbids cross-talk.
- **Generic risks are the #1 quality failure.** "Budget overruns," "team gets distracted,"
  "market shifts" apply to every plan and help no one. If a cause would survive find-and-replace of
  the subject, it's too generic — force it to cite a real plan detail.
- **Run it BEFORE commitment.** A premortem after the money is spent and the team is emotionally
  bought in becomes a ritual. Its value is in _changing_ the plan, so it needs a changeable plan.
- **Don't confuse it with RedTeam or Council.** Premortem = imagined _future failure_ of a
  _concrete plan_, ending in a revised plan. RedTeam = adversarial attack on an arbitrary idea.
  Council = multiple _current_ perspectives debating. Overlapping vocabulary, different mechanisms.
- **Thin context → generic output.** If you can't state (1) what's being premortemed in one
  sentence, (2) who's affected, (3) what success means, STOP and ask one question at a time. Don't
  generate failures from nothing — that produces exactly the generic risk this technique exists to
  avoid.
- **Failure ≠ pessimism.** The output is specific causal stories with mitigations, not a doom mood.
  If the run reads as "everything is risky," it failed.
- **Likelihood and severity are different axes.** The _most likely_ failure and the _most dangerous_
  failure are usually not the same one. Surface both — that distinction is often the insight.

## Customization

Before executing, check for user customizations at
`~/.claude/PAI/USER/SKILLCUSTOMIZATIONS/Premortem/`. If `PREFERENCES.md` exists, load and apply it
(e.g. preferred default horizon, report theme, number of failure agents). These override defaults.
If the directory does not exist, proceed with skill defaults. Do not put private/identity content
in this skill body — it belongs in SKILLCUSTOMIZATIONS.

## 🚨 Voice Notification (run on invocation)

```bash
curl -s -X POST http://localhost:31337/notify \
  -H "Content-Type: application/json" \
  -d '{"message": "Running the WORKFLOWNAME workflow in the Premortem skill to ACTION"}' \
  > /dev/null 2>&1 &
```

Then output: `Running the **WorkflowName** workflow in the **Premortem** skill to ACTION...`

## Examples

**Example 1: Full premortem on a launch**

```
User: "Premortem our paid-newsletter launch next month"
→ RunPremortem: gather context (what/who/success) → frame "it's 6 months out, the launch failed"
→ generate plan-specific causes → fan out 1 agent per cause (independent) → synthesize
   most-likely + most-dangerous + hidden assumption + revised plan + checklist
→ write transcript .md, optionally GenerateReport.ts --html → 3-sentence chat summary
```

**Example 2: Quick solo gut-check**

```
User: "quick premortem on accepting this contractor role"
→ QuickPremortem: single-pass, no agents → past-tense framing → 5-8 specific causes with
   likelihood/severity, hidden assumption, top mitigations → short markdown, no HTML
```

**Example 3: Disambiguation from RedTeam**

```
User: "poke holes in my argument that we should go remote-first"
→ This is attacking an ARGUMENT, not a plan-with-stakes → suggest RedTeam instead, or
   reframe: "if you want to premortem the remote-first *rollout plan*, I can do that."
```

## Execution Log

After completing any workflow, append a single JSONL entry:

```bash
echo '{"ts":"'$(date -u +%Y-%m-%dT%H:%M:%SZ)'","skill":"Premortem","workflow":"WORKFLOW_USED","input":"8_WORD_SUMMARY","status":"ok|error","duration_s":SECONDS}' >> ~/.claude/PAI/MEMORY/SKILLS/execution.jsonl
```
