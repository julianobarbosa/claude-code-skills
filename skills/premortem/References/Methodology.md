# Premortem — Methodology & Evidence

Reference material for the Premortem skill. Loaded on demand by the workflows. This file
is the *why* behind the protocol; the workflows are the *how*.

---

## 1. Origins & Evidence

The premortem was named and popularized by cognitive psychologist **Gary Klein** in his
September 2007 *Harvard Business Review* article **"Performing a Project Premortem"**
(reprint F0709A). It rests on a single empirical foundation Klein cites:

> "Research conducted in 1989 by Deborah J. Mitchell, of the Wharton School; Jay Russo,
> of Cornell; and Nancy Pennington, of the University of Colorado, found that prospective
> hindsight — imagining that an event has already occurred — increases the ability to
> correctly identify reasons for future outcomes by 30%."

The underlying study: **Mitchell, D. J., Russo, J. E., & Pennington, N. (1989). "Back to
the Future: Temporal Perspective in the Explanation of Events." *Journal of Behavioral
Decision Making*, 2(1), 25–38** (doi:10.1002/bdm.3960020103).

> ⚠️ **Citation-accuracy correction (important).** The 1989 study measured that framing an
> event in the **past tense** ("the event happened") rather than future/conditional
> increased the **number of reasons generated** by roughly 30%. It did **not** measure that
> the reasons were *correctly* identified. Klein's gloss ("correctly identify") subtly
> overstates the finding. **Use the defensible claim: "~30% more reasons generated."** Never
> tell a user the premortem makes them "30% better at finding the right reasons" — that is
> not what the data shows, and stating it makes the whole analysis look sloppy.

**Daniel Kahneman** endorsed the premortem in *Thinking, Fast and Slow* (2011) as a partial
remedy for overconfidence and the illusion of validity — which is largely why it entered
mainstream business vocabulary.

Later support: **Veinott, Klein & Wiggins (2010)** found a premortem condition reduced
overconfidence more reliably than plain critique, pros/cons, or cons-only conditions. The
evidence base is still thin — be honest about that rather than overselling.

Organizations including Google, Goldman Sachs, and Procter & Gamble use premortems for
major decisions.

---

## 2. The Mechanism — why it works

The premortem inverts the usual question. Instead of *prospective foresight*
("what could go wrong?"), it uses **prospective hindsight**: you stand at a fixed future
point where failure has **already happened with certainty** and explain why.

Klein: "the premortem operates on the assumption that the 'patient' has died, and so asks
what *did* go wrong."

Three cognitive effects:

- **Overconfidence / planning fallacy** — certainty of the outcome forces concrete causal
  storytelling rather than vague hedging. Past-tense narrative is more specific than an
  abstract risk list.
- **Groupthink & social pressure** — there is "silent pressure not to surface doubts." The
  premortem makes dissent the *assigned task*, so people compete on the quality of the
  problems they raise.
- **Legitimizing the doubter** — it gives knowledgeable skeptics permission to speak without
  seeming disloyal.

**This tense-shift is the entire mechanism.** Every design choice in this skill serves it.
If a step does not help the user inhabit "it already failed," it is decoration.

---

## 3. Canonical Process (Klein's facilitation)

The original group protocol, adapted in this skill for AI-assisted runs:

1. **Set the scene.** State explicitly: assume the project has failed — spectacularly.
2. **Write independently first.** Everyone lists every reason for the failure *before*
   anyone shares. This independent-then-share step is the **anti-anchoring safeguard** — it
   is load-bearing, not optional. (In the AI version, parallel agents must not see each
   other's output.)
3. **Share round-robin.** Each person reads one distinct reason until all are recorded;
   starting with the leader models candor.
4. **Review & strengthen.** Afterward, review the list for ways to strengthen the plan.
5. **Revisit periodically** — the list becomes an early-warning radar during execution.

Klein notes it can take as little as 20–30 minutes. Practitioner guidance: small
cross-functional groups (~4–8) so every voice is heard; run it **during planning, before
commitment**.

---

## 4. Variations & Adjacent Techniques

| Technique | Relationship to premortem |
|-----------|---------------------------|
| **Pre-parade / "pre-mortem positive"** | Imagine wild success and ask what made it happen (backcasting). Pairs with the failure version but can re-inflate optimism. |
| **Postmortem** | Same diagnostic logic, opposite timing. Premortem improves the plan; postmortem dissects the corpse. |
| **Red teaming** | Adversarial, externally staffed, resource-heavy. The premortem is fast, internal, and structured imagination. |
| **SWOT** | A balanced static inventory. The premortem is failure-focused and narrative — it surfaces risks SWOT's boxes flatten. |
| **"Kill the company"** (Stalk & Lachenauer) | The same prospective-hindsight engine scaled to existential/strategic threats. |
| **Scenario planning / Tetlock-style judgment** | Prospective hindsight underpins structured forecasting. |

---

## 5. Failure Modes & Gotchas (when *running* a premortem)

- **Anchoring on the first failure named** — skipping independent generation lets the
  loudest voice (or the first agent) set the frame. Generate independently, then merge.
- **Sandbagging / theater** — going through the motions, or producing findings nobody owns.
  A premortem with no mitigation follow-through is worthless.
- **Running it too late** — after psychological/financial commitment it becomes ritual, not
  redirection. Run it while the plan is still changeable.
- **Generic risks** — "the timeline slips," "budget overruns." Plan-agnostic risks signal
  weak engagement. Demand plan-specific, concrete causal chains.
- **Irreversible decisions** — value is low when nothing can change. Best applied where the
  plan can still be revised.
- **Confusing it with general pessimism** — the goal is specific, actionable causal stories,
  not a bad mood.

---

## 6. Practitioner Best Practices

- **Make each failure specific and grounded** — a concrete causal chain, not a category.
- **Score it** — assign likelihood × severity to prioritize.
- **Derive early-warning indicators** — for each top risk, define the observable signal that
  it is materializing.
- **Convert to mitigations + a pre-launch checklist** — every retained risk gets an owner
  and a preventive/contingent action.
- **Facilitation** — ideally a neutral facilitator; the leader speaks first to model candor
  but should not dominate.
- **Document and revisit** — keep the risk list live; check it at milestones.

---

## Sources

- Klein, G. (2007). "Performing a Project Premortem." *Harvard Business Review*, Sept 2007. <https://hbr.org/2007/09/performing-a-project-premortem>
- Mitchell, D. J., Russo, J. E., & Pennington, N. (1989). "Back to the Future: Temporal Perspective in the Explanation of Events." *Journal of Behavioral Decision Making*, 2(1), 25–38. <https://onlinelibrary.wiley.com/doi/10.1002/bdm.3960020103>
- Klein, G. (2021). "The Pre-Mortem Method." *Psychology Today*. <https://www.psychologytoday.com/us/blog/seeing-what-others-dont/202101/the-pre-mortem-method>
- Veinott, Klein & Wiggins (2010). "Evaluating the Effectiveness of the PreMortem Technique on Plan Confidence."
- Kahneman, D. (2011). *Thinking, Fast and Slow*.
- Jason Collins — evidence critique of the "30%" claim. <https://corporate.jasoncollins.blog/premortem>
