---
id: SPEC-ship-rust-port
companions:
  - cli-contract.md
  - ../../../skills/ship/SKILL.md
sources: []
---

> **Canonical contract.** This SPEC and the files in `companions:` are the complete, preservation-validated contract for what to build, test, and validate. Source documents listed in frontmatter are for traceability — consult them only if you need narrative rationale or prose color this contract intentionally omits.

# Port the ship skill to a Rust binary

## Why

A vision to realize, with an operator pain behind it. The `ship` skill delivers branches as PRs with linked work items on Azure Repos and GitHub. Today it is seven TypeScript scripts plus a shared lib (`skills/ship/scripts/`, 1,587 lines including tests) that need `bun` and an `npm`-style `node_modules` install before first use. A single compiled binary removes that runtime and install step. Four forces apply together (Barbosa, 2026-11-08): no bun or `node_modules` before first use, a binary that can be handed to other machines, faster startup per call, and a real project to learn Rust on. Distribution is load-bearing, so CAP-8 is a first-class capability, not a side effect.

## Capabilities

- **CAP-1**
  - **intent:** The operator can detect the delivery platform, remote, Azure coordinates, branch and inferred work item of the current repo.
  - **success:** `ship detect` prints the same keys and values as `ship-detect.ts` on one Azure Repos clone and one GitHub clone, and `SHIP_PLATFORM` overrides the result.
- **CAP-2**
  - **intent:** The operator can audit what would be delivered and whether the working tree is in scope before committing.
  - **success:** `ship preflight` prints `commits_ahead_of_upstream`, the staged, unstaged and untracked counts and `scope_clean`, matching the TS output, and always exits 0.
- **CAP-3**
  - **intent:** The operator can push the current branch and set its upstream on either platform.
  - **success:** On Azure the push succeeds through an `az` Bearer token with `credential.helper` emptied, falls back to the stored credential when `az` is logged out, and reports `push_ok=oauth-bearer|normal`. A rejected push is reported, never forced.
- **CAP-4**
  - **intent:** The operator can open a PR that is never left without a linked Board work item on Azure, carrying tags and reviewers.
  - **success:** With and without `--work-item`, the Azure PR ends linked to a verified or newly created item assigned to `SHIP_ADO_ASSIGNEE`. `--related` items are linked to the own item, not the PR. `complete_transitions_work_items` is read back from the update response. GitHub labels and reviewers land on the PR.
- **CAP-5**
  - **intent:** The operator can add, remove and list tags (Azure) or labels (GitHub) on an existing PR.
  - **success:** `ship tag <id> --add/--remove/--list` gives the same results and output as `ship-tag.ts` on both platforms.
- **CAP-6**
  - **intent:** The operator can open a PR URL in the browser profile signed in with a chosen email.
  - **success:** `ship open --list-profiles` lists the same accounts as the TS script, `--dry-run` resolves the same profile directory, and `--set-default` writes `~/.config/ship/open.json` in the same format. This holds from WSL (Windows Edge or Chrome) and on macOS.
- **CAP-7**
  - **intent:** The operator can save the current state as an annotated git tag on `HEAD`.
  - **success:** The default name is `v<YYYY.MM.DD-HHMM>` (`--daily` gives `v<YYYY.MM.DD>`), an existing tag is refused with exit 3, and `--push` pushes the tag the same way CAP-3 does.
- **CAP-8**
  - **intent:** The operator can run ship on a supported machine without installing bun or `node_modules`.
  - **success:** On a clean Linux/WSL2 and a clean macOS host with no bun, a prebuilt binary runs all seven subcommands.

## Constraints

- Behavioral parity with the TS scripts: every flag, environment variable, `key=value` stdout line and exit code in `cli-contract.md` is preserved, so the flow in `SKILL.md` keeps working with only the invocation changed.
- `git`, `az` and `gh` stay subprocess calls built from argument arrays, never a shell string.
- Tokens go only in `Authorization` headers, stay short-lived, and are never printed, logged or put in URLs. Every Bearer git call empties `credential.helper`.
- No AI attribution in any commit, PR title or PR body the binary writes.
- Azure auth order: `az account get-access-token` first. `AZURE_DEVOPS_EXT_PAT`/`AZURE_DEVOPS_PAT` are used only after a 401/403, or alone when `az` is logged out.
- GitHub auth order: `GH_TOKEN`/`GITHUB_TOKEN` override everything, then `gh auth token -u <owner>`, then the active account.
- Supported hosts are Linux/WSL2 and macOS.
- Rust is the language of the binary. No Python, and no npm or npx anywhere in build, test or install.

## Non-goals

- New features or behavior changes during the port. The PR and work-item flow stays as `SKILL.md` describes it.
- Windows-native (non-WSL) support.
- Changing the `merge`, `commit` or `azure-devops` skills.

## Success signal

- The same delivery (open a PR, link or create the work item, add tags and reviewers) on one Azure Repos repo and one GitHub repo, run from a machine without bun, produces the same `key=value` output with `ship <subcommand>` as with the TS scripts, and the existing `ship-lib` test cases pass against the Rust implementation.

## Assumptions

- One binary with subcommands (`ship detect|preflight|push|pr|tag|open|snapshot`) replaces the seven scripts, so `SKILL.md` changes `bun scripts/ship-x.ts` to `ship x`.
- The TypeScript scripts are retired after cutover rather than kept side by side.
- The existing `ship-lib.test.ts` cases are the parity baseline and get ported.

## Open Questions

- How is the binary distributed: per-platform builds committed to the repo, `cargo install` from the repo, or GitHub Releases?
- Does the `ship-tag` release skill also move to Rust, or only `ship`?
- Is there a maintained Rust crate for the Azure DevOps REST API good enough to replace `azure-devops-node-api`, or should the binary call REST directly? Same question for GitHub (`octocrab` versus raw REST).
- The worktree is named `ship-from-python-to-rust`, but `ship` has no Python today. Is a Python component missing from this picture?
