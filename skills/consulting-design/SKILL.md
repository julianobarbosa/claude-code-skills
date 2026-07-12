---
name: consulting-design
description: Consult Gemini AI for architecture alternatives, design trade-offs, and brainstorming. Use when seeking different perspectives on design, evaluating architectural approaches, comparing solutions, or generating creative ideas.
allowed-tools: Read, Grep, Glob, mcp__gemini__ask-gemini, mcp__gemini__brainstorm
---

# Design Consultation with Gemini

## Tools

| Tool                      | Use For                                     |
| ------------------------- | ------------------------------------------- |
| `mcp__gemini__ask-gemini` | Architecture, design review, trade-offs     |
| `mcp__gemini__brainstorm` | Generating alternatives, creative solutions |

## ask-gemini

```json
{
  "prompt": "I'm designing [system]. Current approach: [desc]. Trade-offs and alternatives?",
  "model": "gemini-2.5-pro"
}
```

Options: `changeMode: true` for structured edits, `sandbox: true` for code execution

## brainstorm

```json
{
  "prompt": "How might we [challenge]?",
  "domain": "software",
  "methodology": "auto",
  "ideaCount": 10
}
```

Methodologies: `divergent`, `convergent`, `scamper`, `design-thinking`, `lateral`, `auto`

---

## Gotchas

- **Gemini brainstorm output is non-deterministic** — same prompt rerun gives different ideas; save outputs you want to reference.
- **`ask-gemini` doesn't preserve conversation context across calls** — multi-turn questions need explicit history concatenation in each prompt.
- **API quota is per-project per-day** — bursting on a free tier locks the project out until midnight Pacific.
- **Output is markdown but can include LaTeX math** — downstream tooling that doesn't render math gets garbled output without warning.
- **`brainstorm` defaults to 5 ideas** — for divergent ideation, explicitly request more; the default is a hard cap.
