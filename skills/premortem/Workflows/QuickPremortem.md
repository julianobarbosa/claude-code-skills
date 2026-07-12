# Workflow: QuickPremortem

The lightweight premortem — a single-pass, solo analysis with **no parallel agents**. Use for
small or personal decisions, fast gut-checks, or when context is thin and a full fan-out would be
overkill. Same mechanism (prospective hindsight), a fraction of the cost.

**Voice on entry:**
```bash
curl -s -X POST http://localhost:31337/notify -H "Content-Type: application/json" \
  -d '{"message": "Running the QuickPremortem workflow in the Premortem skill for a fast failure check"}' > /dev/null 2>&1 &
```
Then: `Running the **QuickPremortem** workflow in the **Premortem** skill for a fast failure check...`

---

## How it differs from RunPremortem

| | QuickPremortem | RunPremortem |
|---|---|---|
| Cause analysis | Single pass, in one context | One parallel agent per cause |
| Anti-anchoring | Mitigated by generating the full cause list *before* analyzing any | Enforced by independent agents |
| Output | Short markdown in chat | Full transcript + optional HTML report |
| Use for | Small/personal/fast | High-stakes, needs depth + a record |

## Steps

1. **Confirm the basics (fast).** One sentence: what is being decided, and what does success look
   like? If you can't state both, ask one question — don't generate from nothing.

2. **Frame in past tense.** "It's [horizon, default ~6 months out]. [The decision] turned out
   badly. Here's why." Inhabit the certainty.

3. **List every cause first, then analyze.** Write 5–8 plan-specific failure causes *before*
   elaborating on any of them — this is the solo substitute for the parallel anti-anchoring step.
   Reject generic risks; each must cite a real detail of the decision.

4. **Score and deepen.** For each cause give: likelihood (low/med/high), severity (low/med/high),
   the one hidden assumption behind it, and one concrete mitigation. Keep each tight.

5. **Synthesize in three lines.** Most-likely failure, most-dangerous failure, and the single
   biggest hidden assumption — then the top 1–3 changes worth making now.

6. **Deliver as short markdown.** No HTML, no saved report unless asked. Offer to escalate to
   `RunPremortem` if the stakes turn out higher than they looked.

7. **Log.** Append the execution-log JSONL entry (see SKILL.md → Execution Log).

## Gotcha

- If the decision is genuinely high-stakes (irreversible, expensive, reputational), don't shortcut
  it — switch to `RunPremortem`. Quick mode trades depth for speed; spend the depth where the cost
  of being wrong is high.
