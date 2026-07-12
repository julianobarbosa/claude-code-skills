---
name: reviewing-code
description: Get code review from Codex AI for implementation quality, bug detection, and best practices. Use when asked to review code, check for bugs, find security issues, or get feedback on implementation patterns.
allowed-tools: Read, Grep, Glob, mcp__codex__spawn_agent
---

# Code Review with Codex

Use `mcp__codex__spawn_agent` for code review.

## When to Use

- Review code quality and patterns
- Find potential bugs or edge cases
- Validate against best practices
- Check for security issues

## Usage

```json
{
  "prompt": "Review this code for [quality/bugs/security]: [code or file]"
}
```

## Prompt Examples

- "Review for code quality and Go best practices: [code]"
- "Analyze for security vulnerabilities: [code]"
- "Review for performance issues: [code]"
- "Does this follow idiomatic patterns? [code]"

---

## Gotchas

- **Codex review is non-deterministic** — same code with different invocations gets different priority orderings; pin model version when reproducibility matters.
- **Codex doesn't see staged-but-uncommitted changes by default** — pass them explicitly via `--include-staged` or piped diff.
- **Diff-only review misses cross-file effects** — a renamed function's callsite in another file isn't in the diff, so the rename's blast radius isn't surfaced.
- **Review output ranks by Codex's internal severity heuristic** — not by user-defined priority; re-rank manually for project-specific concerns.
- **Whitespace-only diffs trigger reviews** — pass `--ignore-whitespace` or you get noise.
- **Large diffs (>500 LOC) get summarized**, not reviewed line-by-line — split into focused reviews per file group.
