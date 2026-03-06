---
name: AzureFinOps
description: Azure FinOps reservation analysis, cost validation, waste discovery, and executive reporting. USE WHEN user says 'validate costs', 'check reservations', 'find waste', 'orphaned resources', 'reservation coverage', 'savings analysis', 'draft response for', 'cost analysis', 'are these reservations', 'reservation gaps', OR any Azure cost optimization request.
---

# AzureFinOps Skill

Azure cost optimization through reservation analysis, waste discovery, and stakeholder reporting.

## Important

- All Azure operations are **READ-ONLY** — zero modifications to any resource
- Primary output language: **Portuguese (BR)** for stakeholder responses
- Python CLI fallback: `uv run python -m azure_finops` when MCP/CLI auth unavailable

## Context Files

- `AzureToolReference.md` — MCP tools + CLI commands quick reference
- `ReservationInventory.md` — SKU matching and reservation interpretation SOP
- `PricingComparison.md` — PAYG vs RI pricing methodology and savings formulas

## Workflow Routing

| Workflow | Trigger | File |
|----------|---------|------|
| ValidateCosts | "validate costs", "are these reservations or PAYG", "check billing" | `Workflows/ValidateCosts.md` |
| FindWaste | "find waste", "orphaned disks", "orphaned resources" | `Workflows/FindWaste.md` |
| CoverageAnalysis | "reservation coverage", "reservation gaps", "savings analysis" | `Workflows/CoverageAnalysis.md` |
| DraftResponse | "draft response for", "resposta para", "executive summary" | `Workflows/DraftResponse.md` |

## Examples

**Example 1 — Cost Validation:**
> "Are these January costs reservations or pay-as-you-go?"
> Routes to: `Workflows/ValidateCosts.md`

**Example 2 — Waste Discovery:**
> "Find orphaned disks and wasted resources across all subscriptions"
> Routes to: `Workflows/FindWaste.md`

**Example 3 — Executive Response:**
> "Draft a response for Jean about the January billing anomalies"
> Routes to: `Workflows/DraftResponse.md`
