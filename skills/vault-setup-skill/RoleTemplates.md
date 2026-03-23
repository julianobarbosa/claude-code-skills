# Role Templates — Keyword-to-Folder Mapping

Used by Workflows/Setup.md Step 2 to infer vault folders from the user's free-text description. Base folders (inbox/, daily/, projects/, archive/) are always created.

| Keywords Detected | Folder | Purpose |
|---|---|---|
| pipeline, infrastructure, devops, cloud, deploy, terraform, kubernetes | `runbooks/` | Operational procedures and troubleshooting |
| client, customer, account, engagement | `clients/` | Per-client or per-team context |
| research, evaluate, architecture, tool, compare | `research/` | Investigations, tool evals, ADRs |
| content, blog, video, podcast, newsletter | `content/` | Content production pipeline |
| meeting, standup, retro, 1-on-1 | `meetings/` | Meeting notes and action items |
| personal, life, health, family, finance | `personal/` | Personal life tracking |
| notes, class, lecture, course, study | `notes/` | Study materials and course notes |
| decision, adr, tradeoff | `decisions/` | Architecture/business decision records |
| people, team, reports, manager | `people/` | People tracking, org context |
| operations, sop, procedure, runbook | `operations/` | Standard operating procedures |
| sales, deal, pipeline, crm | `sales/` | Sales pipeline and deal tracking |

## Example CLAUDE.md 'How I Work' Bullets by Domain

**DevOps / Cloud Engineer:**
- I automate everything — if it runs more than once, it gets a pipeline
- I manage many Azure subscriptions and need full tenant visibility
- I prefer concise, actionable documentation over verbose guides
- When I capture something, sort it fast — inbox should stay empty

**Business / Consultant:**
- I juggle multiple client engagements simultaneously
- I need fast access to client history and decision context
- I document decisions with rationale so I can recall why we chose X

**Developer:**
- I think in terms of systems and architecture
- I research tools before adopting — research/ is my evaluation zone
- I track client work separately from personal projects

**Content Creator:**
- I produce content across multiple formats (blog, video, podcast)
- Ideas go through a pipeline: capture → develop → produce → publish
- I need my AI to match my voice after reading recent drafts

**Student:**
- I organize by course and topic, not by date
- I need synthesis across lectures, readings, and my own notes
- Spaced repetition is part of my workflow

## Context Rules by Detected Folder Set

- **runbooks/**: When I mention a procedure → check runbooks/ first
- **clients/**: When I mention a client → look in clients/
- **research/**: When I mention a tool or evaluation → check research/
- **content/**: When I mention content or a draft → check content/
- **meetings/**: When I mention a meeting → check meetings/
- **personal/**: Personal items stay in personal/ — don't mix with work
- **decisions/**: When I mention a decision → check decisions/ first
- **people/**: When I mention someone on my team → check people/

## Companion Skill Recommendations by Domain

| Domain Keywords | Suggested Skills |
|---|---|
| devops, cloud, infrastructure | `azure-devops-skill`, `container-security-skill`, `managing-infra-skill` |
| content, blog, video | `file-intel-skill` for bulk processing |
| research, evaluate | `file-intel-skill` for document analysis |
| All domains | `daily-skill`, `tldr-skill`, `obsidian-master-skill` |
