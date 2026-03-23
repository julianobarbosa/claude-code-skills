# Runbook — Create or load an operational runbook

When invoked with a topic (e.g., `/runbook ARI management group`):
1. Search `runbooks/` for existing runbooks matching the topic
2. If found, load and display the runbook
3. If not found, create a new one using this template:

```markdown
# Runbook: {{title}}

## Purpose
[One sentence — when and why to use this]

## Prerequisites
-

## Steps
1.

## Verification
- [ ]

## Troubleshooting
| Symptom | Cause | Fix |
|---------|-------|-----|

## Last Tested
{{date}}
```

Save to `runbooks/` with a kebab-case filename.
