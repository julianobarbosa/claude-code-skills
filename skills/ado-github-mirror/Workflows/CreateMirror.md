# CreateMirror

## Done means

1. `github.com/<org>/<name>` exists with the configured visibility, issues/wiki off, description naming the ADO source.
2. Every `refs/heads/*` and `refs/tags/*` SHA on GitHub equals the ADO source (`Mirror.ts` exit 0 is the evidence; quote its `✓ verified` line).
3. The repo carries the sync pipeline file, delivered through a PR — not a direct push.
4. The operator knows the exact remaining actions (PAT, variable group, pipeline registration), each as a copy-pasteable command, and the first pipeline run is checked green once they're done.

## Sufficiency

Needs: the source repo (default: the current checkout's `origin`) and the target org (default: `config.json`). If the target name should differ from the source name, that must come from the user — ask.

## Tool contract

```bash
T="${SKILL_DIR:-.}/Tools"
bun "$T/Mirror.ts" --dry-run                       # auth on both sides, ref count, no writes
bun "$T/Mirror.ts" --write-pipeline "$PWD"         # create + seed + verify + write pipeline YAML
bun "$T/Mirror.ts" --ado-bearer ...                # when ADO git credentials fail but az is logged in
```

| User says | Flag |
|-----------|------|
| "to org X" | `--github-org X` |
| "call it Y" | `--name Y` |
| "internal to the enterprise" | `--visibility internal` |
| "just check" / "dry run" | `--dry-run` |

Exit 3 = auth preflight failed: relay the printed fix to the principal (interactive logins are theirs: `! gh auth login -h github.com`, `! az login`), then re-run.

## Operator actions (the agent cannot do these)

```bash
# 1. Fine-grained PAT in the GitHub org: repo <org>/<name>, Contents: Read and write, then SSO-authorize it.
# 2. Variable group in the ADO project that owns the repo (secret value typed by the operator, never pasted to chat):
az pipelines variable-group create --org <org-url> --project <project> --name <variableGroup> --variables placeholder=1 --authorize true
az pipelines variable-group variable create --org <org-url> --project <project> --group-id <id> --name <tokenVariable> --secret true   # prompts for value
# 3. After the PR merges:
az pipelines create --org <org-url> --project <project> --name mirror-github-<name> --repository <name> --repository-type tfsgit --branch main --yml-path /.azure-pipeline-mirror-github.yaml
```
If the variable group already exists (one PAT covering several repos), add the new repo to that PAT's repository list instead of creating another group.
