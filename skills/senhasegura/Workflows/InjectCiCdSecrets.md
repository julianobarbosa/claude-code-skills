# Workflow: Inject Senhasegura Secrets into CI/CD

Fetch DSM secrets at pipeline runtime via `dsm runb`, source them as environment variables, and clean up before the job ends.

## Prerequisites
- DSM CLI available in the runner image
- A2A OAuth 2.0 credentials (`Workflows/SetupA2A.md`), stored as masked CI/CD secrets
- Application/system/environment registered in DSM

## Steps

### 1. Store senhasegura credentials in the CI/CD platform

| Platform | Where |
|----------|-------|
| GitHub Actions | Settings → Secrets and variables → Actions → `SENHASEGURA_URL`, `SENHASEGURA_CLIENT_ID`, `SENHASEGURA_CLIENT_SECRET` |
| GitLab CI | Settings → CI/CD → Variables (mark as masked + protected) |
| Azure DevOps | Pipelines → Library → Variable group `senhasegura-credentials` (linked from each pipeline) |
| Jenkins | Credentials → Add → secret text for each variable |

### 2. Install the DSM CLI in the runner

```bash
curl -LO https://github.com/senhasegura/dsmcli/releases/latest/download/dsm-linux-amd64
chmod +x dsm-linux-amd64
sudo mv dsm-linux-amd64 /usr/local/bin/dsm
dsm --version
```

For GitHub Actions, see `References/GithubActionsExample.yaml`. For Azure DevOps, see `References/AzurePipelinesExample.yaml`. For GitLab, see `References/GitlabCiExample.yaml`.

### 3. Fetch secrets

Run from a temp directory (Gotcha #5 — never let `.runb.vars` land in the repo root):

```bash
mkdir -p /tmp/senhasegura && cd /tmp/senhasegura

dsm runb \
  --tool-name github \         # or azure-devops / gitlab / linux
  --application my-app \
  --system production \
  --environment prod
```

`--tool-name` controls log masking — match the actual runner. Mismatched values can leak secrets to the log (Gotcha #7).

### 4. Source secrets into the environment

```bash
source /tmp/senhasegura/.runb.vars

# In GitHub Actions, you can also export across steps:
cat /tmp/senhasegura/.runb.vars >> "$GITHUB_ENV"
```

### 5. Use and clean up

```bash
echo "Deploying with database host: $DB_HOST"
./deploy.sh
```

Cleanup must always run, even on failure:

```yaml
# GitHub Actions
- name: Cleanup
  if: always()
  run: rm -f /tmp/senhasegura/.runb.vars
```

```yaml
# Azure DevOps
- script: rm -f /tmp/senhasegura/.runb.vars
  displayName: Cleanup
  condition: always()
```

```yaml
# GitLab CI
after_script:
  - rm -f /tmp/senhasegura/.runb.vars
```

## Mapping file (optional — write secrets back from CI)

For pipelines that *register* or *update* secrets, use a mapping file. See `References/MappingExample.json` for the full shape:

```json
{
  "credentials": [
    {
      "name": "DATABASE_CREDS",
      "fields": {
        "user": "DB_USER",
        "password": "DB_PASSWORD",
        "host": "DB_HOST"
      }
    }
  ]
}
```

Set `SENHASEGURA_MAPPING_FILE=/path/to/mapping.json` and DSM will sync changes.

## Common failures

| Symptom | Cause |
|---------|-------|
| `command not found: dsm` | CLI not installed in the runner |
| Empty `.runb.vars` | Application/system/environment combination doesn't exist in DSM |
| Secrets visible in log output | Wrong `--tool-name` (Gotcha #7) |
| `.runb.vars` committed to repo | Ran from repo root (Gotcha #5) — switch to a tmpdir |
| `401` mid-pipeline | Token expired during a long-running step — fetch right before use, not at job start |
