# ship CLI contract (parity catalog)

Taken from `skills/ship/scripts/*.ts` on 2026-11-08 (commit `3ab2752`). The Rust binary must accept these flags, read these environment variables, and print these `key=value` stdout keys. The TS script is the reference for formats and edge cases.

| Subcommand | Replaces | Flags | Stdout keys |
|---|---|---|---|
| `detect` | `ship-detect.ts [remote]` | positional remote | `platform` `remote` `url` `org_url` `project` `repo` `branch` `work_item` |
| `preflight` | `ship-preflight.ts [remote]` | positional remote | `branch` `commits_ahead_of_upstream` `staged` `unstaged` `untracked` `scope_clean` |
| `push` | `ship-push.ts` | `-r/--remote` `-b/--branch` | `push_ok` (`oauth-bearer` or `normal`) |
| `pr` | `ship-pr.ts` | `--title` `--body` `--body-file` `--source` `--target` `--remote` `--draft` `--work-item` `--work-item-type` `--task` `--tasks-file` `--assignee` `--no-create-work-item` `--transition` `--related` `--tag` `--no-tag` `--reviewer` `--required-reviewer` `--no-reviewer` `--no-complete-transition` | `platform` `pr_url` `pr_id` `pr_number` `work_item` `work_item_created` `work_items` `related_linked` `tag_added` `reviewer_added` `reviewer_skipped` `complete_transitions_work_items` |
| `tag` | `ship-tag.ts <pr-id>` | `--pr` `--add` `--remove` `--list` `--remote` | `pr_id` `pr_number` `tag_added` `tag_removed` |
| `open` | `ship-open.ts <url>` | `--profile` `--browser` `--dry-run` `--list-profiles` `--set-default` | `browser` `local_state` `profile` `profile_dir` `profile_email` `default_profile_email` `opened_url` |
| `snapshot` | `ship-snapshot.ts` | `-m/--message` (repeatable, one paragraph each) `--daily` `--name` `--push` | `tag` `commit` `branch` `pushed` |

Every subcommand takes `--help`. `pr --tag` and `--reviewer` are comma-separated and repeatable. `--related` and `--task` are repeatable.

## Exit codes

- `0`: success, and `--help`. `preflight` always exits 0 (advisory).
- `3`: `snapshot` refused because the tag already exists.
- Non-zero on any other failure. The TS scripts are the reference for each code.

## Environment variables

| Variable | Read by | Meaning |
|---|---|---|
| `SHIP_PLATFORM` | all | Force `azure` or `github` when detection returns `unknown` |
| `SHIP_ADO_ASSIGNEE` | `pr` | Assignee for created work items |
| `SHIP_ADO_DEFAULT_REVIEWER` | `pr` | Optional reviewer when none is given (Azure only) |
| `AZURE_DEVOPS_EXT_PAT`, `AZURE_DEVOPS_PAT` | Azure calls | Fallback after a 401/403, or when `az` is logged out |
| `GH_TOKEN`, `GITHUB_TOKEN` | GitHub calls | Override every other token source |
| `WSL_DISTRO_NAME` | `open` | Detects WSL, which means launching the Windows browser |
| `XDG_CONFIG_HOME` | `open` | Base directory for `ship/open.json` |

## Platform specifics

- **Azure:** the PR is created with the work item, tags and reviewers in one call. `completionOptions.transitionWorkItems` is set by a separate update, because create drops it, and is read back from that response.
- **GitHub:** labels and reviewers are attached after create. A 404 on create usually means the wrong account, not a missing repo.
- **`open` on WSL:** reads `/mnt/c/Users/<u>/AppData/Local/<Vendor>/<Browser>/User Data/Local State` and launches the browser with `cmd.exe start`. On macOS it reads `~/Library/Application Support/...` and launches with `open -a`.
