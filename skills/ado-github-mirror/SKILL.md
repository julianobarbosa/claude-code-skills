---
name: ado-github-mirror
version: 1.0.0
description: "Mirror an Azure DevOps (Azure Repos) repository into a GitHub or GitHub Enterprise org as a read-only copy: create the GitHub repo, seed every branch and tag, prove each ref SHA matches on both sides, and add an Azure Pipeline that keeps it in sync on every push plus nightly. Handles SAML/SSO-enforced (EMU) orgs and ADO Bearer-token auth. USE WHEN mirror a repo to GitHub, Azure repo mirror, ADO to GitHub mirror, GitHub Enterprise mirror, copy Azure Repos to GitHub, keep GitHub in sync with Azure DevOps, mirror pipeline, re-sync a mirror, mirror is stale. NOT FOR migrating a repo off Azure DevOps for good (a migration makes GitHub the source of truth), cloning a whole ADO project locally (use RepoFleet), or opening a PR (use ship)."
argument-hint: [ado repo url or checkout, optional target org/name]
---

# ado-github-mirror

Azure DevOps stays the source of truth; GitHub gets a read-only copy of `refs/heads/*` and `refs/tags/*` that a pipeline keeps current.

## Configuration

Optional config file at `$ADO_GITHUB_MIRROR_CONFIG` (defaults to `~/.config/ado-github-mirror/config.json`): holds the default `githubOrg`, `visibility`, `pipelineFile`, `variableGroup`, and `tokenVariable` names (the tool reads it automatically).

## Workflow Routing

| Workflow | Trigger | File |
|----------|---------|------|
| **CreateMirror** | "mirror this repo to GitHub", "create a GitHub mirror", "re-sync the mirror" | `Workflows/CreateMirror.md` |

## Tools

- `Tools/Mirror.ts` — create repo if missing → bare clone → `push --force --prune` heads+tags → verify every ref. `--dry-run` checks auth on both sides without writing. Help: `Tools/Mirror.help.md`.
- `Tools/MirrorPipeline.yaml` — the sync pipeline template (`__GITHUB_REPO__`, `__VARIABLE_GROUP__`, `__TOKEN_VARIABLE__`); `Mirror.ts --write-pipeline <dir>` fills it in.

## Gotchas

- **SAML/SSO orgs return 403 "Resource protected by organization SAML enforcement"** — and `repos/<org>/<name>` can 404 for the same reason, which looks like "repo missing". The gh token must be SSO-authorized for that org; for EMU enterprises only the enterprise-managed account can write at all. `Mirror.ts` preflights via `user/memberships/orgs/<org>`: listing org repos is useless as a probe, it succeeds and returns an empty list under SAML.
- **Never `git push --mirror` from a normal clone.** It pushes `refs/remotes/*` and ADO's `refs/pull/*`, which GitHub rejects. Push the explicit heads+tags refspecs from a bare clone.
- **`--prune` is scoped to the refspecs.** Refs outside heads/tags already on GitHub (e.g. from a hand seed with `--mirror`) are left alone, never deleted.
- **EMU orgs cannot hold public repos** — `--visibility` is `private` or `internal` only.
- **The pipeline needs its own credential.** `System.AccessToken` clones the source; the GitHub push needs a fine-grained PAT (Contents: read/write, SSO-authorized) in a secret variable group. The agent cannot mint that PAT — it is an operator action.
- **Self-hosted in-VNet agents may lack github.com egress**; the template pins Microsoft-hosted `ubuntu-latest`.
- **ADO auth fallback:** when git credentials fail and `az` is logged in to the right tenant, `--ado-bearer` sends the AAD token as a Bearer header via env (not argv). A `302` from `dev.azure.com` REST means the az identity is not an org member — switch identities, don't retry.
- **Adding the pipeline file is a repo change** — ship it through the repo's normal PR flow, then register the pipeline.

## Examples

```
User: "mirror this repo to GitHub"
→ CreateMirror: dry-run preflight → Mirror.ts seeds + verifies → --write-pipeline → PR → operator registers pipeline
```
```
User: "the GitHub mirror of X is stale"
→ Mirror.ts on X re-syncs and reports which refs differed; then check the pipeline's last run
```
