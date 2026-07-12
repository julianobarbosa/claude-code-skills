---
name: knowledge-base-health-check
description: >-
  Audits a local Claude-managed knowledge base in Simon's '/Users/simon/Claude CoWork/Knowledge Base/' system. Surfaces contradictions between articles, broken backlinks, unsourced claims, stale articles, writing-rules violations, and three suggested new articles. Files a full report into the KB's 'Outputs/' folder, appends a one-line CHANGELOG entry, and (in interactive sessions) walks through which findings to action. Use this skill whenever the user says "run a health check", "audit the [name] KB", "audit my knowledge base", "check the wiki", "let's go through the health check report", or "action the latest health check". Also use when the monthly scheduled task 'knowledge-base-monthly-health-check' fires. Use this skill for any audit-style request against a folder under 'Knowledge Base/' even if the user doesn't say the word "health check" - the protocol is the same.
---

# Knowledge Base Health Check Skill

This skill is the source of truth for the monthly knowledge base health check.
The librarian reads it and follows it whenever a health check is invoked, on demand or via the scheduled task. The protocol is deliberately the same for both trigger paths so the output format is stable across runs.

## When to invoke

Run this skill when any of the following happens:
• The user says "run a health check", "audit the [name] KB", "check the wiki", or similar. or writes "/healthcheck"
• The user says "action the latest health check" or "let's go through the health check report" - in that case, jump straight to Phase 2 using the most recent health-check report in the relevant KB's Outputs/ folder.
• The monthly scheduled task fires it (taskld: knowledge-base-monthly-health-check ).
If the user doesn't specify which KB, askl Don't run on every KB unless explicitly asked.

## The two phases

The skill runs in two phases. Phase 1 always runs. Phase 2 runs only in interactive sessions - the scheduled task stops at the end of Phase 1.

### Phase 1 — Audit and file (always)

1. Read the rules. Open About me/writing-rules. md and the per-KB
   CLAUDE.md for the KB being audited. The writing rules govern the writing-rules check; the per-KB rules govern Wiki structure and source provenance.
2. Read state files. <KB>/CHANGELOG.md (last health check date and what's happened since), <KB>/Wiki/QUESTIONS.md (already-flagged gaps so they aren't double-flagged), <KB>/RAW/\_INGESTED. md (registry of what's in RAW).
3. Read everything in scope. Every article in <KB>/Wiki/, every file in <KB>/RAW/ (at least the frontmatter and titles — full read only when verifying a specific claim), every output in <KB>/Outputs/ filed since the last health check.
4. Run the seven audits. Detailed below.
5. Write the full report to <KB>/Outputs/YYYY-MM-DD_health-check.md
6. Append a one-line summary to <KB>/CHANGELOG.md at the top, format as in Logging below.
7. Surface the chat summary. Print a tight summary into chat — counts only, plus the top three findings worth the user's attention, and a link to the full report. Do not dump the whole report.

### Phase 2 - Ask and action (interactive only)

8. Ask which findings to action. Use AskUserQuestion with multi-select options drawn from the categories that actually have findings. Skip categories that came up clean.
