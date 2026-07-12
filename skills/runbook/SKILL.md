---
name: runbook
description: Create or load an operational runbook for a given topic. Searches `runbooks/` for an existing match; if none, scaffolds a new one from the standard template (Purpose / Prerequisites / Steps / Verification / Troubleshooting / Last Tested). Use when asked to "create a runbook", "load runbook for X", document a procedure, or look up an SOP.
---

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

---

## Gotchas

- **Stale runbooks are worse than no runbook:** A runbook last tested 18 months ago lies confidently about command flags, dashboard URLs, and rollback paths. Treat anything past `Last Tested` of 90 days as suspect and re-validate before trusting it under incident pressure.
- **Untested rollback steps are decorative:** "Run `terraform destroy`" without ever having executed it from this state means you don't know if it works. Rollback steps must have been rehearsed at least once on a non-prod replica, not just written down.
- **Missing prerequisites cause runbooks to fail at 2am:** "Just run the script" assumes kubectl context, VPN, sudo on the bastion, and an active token. List every prerequisite with the exact verification command — the on-call engineer is not you with your terminal open.
- **Copy-pasted steps that worked once are not procedure:** A `kubectl patch` command captured from a working session may hardcode a pod name, timestamp, or specific resource version. Parameterize anything that varies between executions or it will fail the second time.
- **Verification checkboxes without commands are aspirational:** "Verify the service is healthy" is not a step — `curl -fsS https://x/healthz | jq .status` is. Every verification line should be a copy-pasteable command with the expected output noted.
- **Runbooks rot silently when systems change:** Renaming a deployment, rotating a key vault name, or changing an ingress host invalidates the runbook with no signal. Link each runbook from the system's IaC repo so changes to infrastructure trigger a runbook review.
