# Mirror.ts — seed or re-sync a GitHub mirror of an Azure Repos repo

    bun Mirror.ts [--source <ado-git-url>] [--github-org <org>] [--name <repo>]
                  [--visibility private|internal] [--ado-bearer] [--dry-run]
                  [--write-pipeline <checkout-dir>]

| Flag | Default | Meaning |
|------|---------|---------|
| `--source` | `origin` of the current checkout | Azure Repos clone URL |
| `--github-org` | `githubOrg` in Config.json | Target GitHub org |
| `--name` | source repo name | Target repo name |
| `--visibility` | `visibility` in Config.json, else `private` | EMU orgs cannot create public repos |
| `--ado-bearer` | off | Authenticate the ADO fetch with the az login's AAD token |
| `--dry-run` | off | Preflight only: auth on both sides + ref count, no writes |
| `--write-pipeline` | off | Write the sync pipeline YAML into that checkout |

Exit codes: 0 verified mirror · 1 command failed · 2 bad input · 3 auth preflight failed · 4 ref mismatch after push.
Config: `~/.claude/lifeos/USER/CUSTOMIZATIONS/SKILLS/AdoGithubMirror/Config.json`.
