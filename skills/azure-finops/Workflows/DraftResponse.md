# DraftResponse Workflow

Generate executive stakeholder responses from Azure FinOps analysis results.

## Prerequisites

- Analysis must be completed first (ValidateCosts, FindWaste, or CoverageAnalysis)
- Read analysis output from `Plans/` directory or current session context

## Steps

### 1. Load Analysis Context

Check for analysis results in order of preference:
1. Current session context (if analysis was just performed)
2. `Plans/reservation-coverage-analysis-*.md`
3. `Plans/response-*-*.md` (previous responses for context)

### 2. Determine Language

| Signal | Language |
|--------|----------|
| Default | **Portuguese (BR)** |
| Recipient name is Portuguese/Brazilian | Portuguese (BR) |
| User explicitly says "in English" | English |
| User explicitly says "em portugues" | Portuguese (BR) |

### 3. Determine Audience Tone

| Audience | Tone | Detail Level |
|----------|------|-------------|
| Executive (Director+) | High-level, focus on impact and savings | Summary table, key findings, next steps |
| Technical (Engineer/Architect) | Detailed, include SKUs and commands | Full breakdown with resource names |
| Finance (Controller/CFO) | Numbers-first, ROI focus | Cost tables, annual projections, recommendations |

### 4. Structure Response

```markdown
# Response Template

{Greeting — informal but professional}

{1-2 sentence summary answering the core question}

{Summary table: Service | Monthly Cost | Reservation Status}

{Key findings — 2-4 bullet points}

{Waste findings if applicable — orphaned resources, cleanup opportunity}

{Savings opportunity if applicable — estimated monthly/annual savings}

{Next steps — what you can do or present}

---

## Technical Detail (for internal reference)

{Detailed breakdown for the recipient's team}
```

### 5. Save Response

Save to: `Plans/response-{recipient-firstname}-{subject-slug}.md`

Include metadata header:
```markdown
# Resposta para {Recipient} — {Subject}

**De:** {sender}
**Para:** {recipient full name}
**Data:** {date}
**Assunto:** {subject in recipient's language}
```

## Key Principles

- **Lead with the answer** — don't make the reader hunt for the conclusion
- **Use BRL for all amounts** — this is the stakeholder's currency
- **Include the evidence chain** — "validated directly in Azure" builds credibility
- **Offer next steps** — always close with what you can do next
- **Keep executive section under 300 words** — detail goes in technical appendix

## Output

- Formatted response ready to send/share
- Saved to `Plans/` directory for future reference
- Technical appendix with full analysis detail
