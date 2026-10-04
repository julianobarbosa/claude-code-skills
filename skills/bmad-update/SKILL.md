---
name: bmad-update
description: Use when updating BMAD or invoking bmad-update.
---

# BMAD update

Safely update project-local BMAD modules, mitigate CIS compatibility failures, and remove authorized deprecated components. This is a Hermes profile-local maintenance skill, not an upstream BMAD command.

## When to Use

Use for BMAD installation updates, the CIS missing-module-definition failure, or authorized cleanup of deprecated BMAD modules. Do not use for Android feature implementation.

## Protect existing work

Inspect Git status, `_bmad/_config/manifest.yaml`, configured tools, custom overrides, and npm dist-tags. Preserve the release channel unless requested otherwise. Authenticate, fetch origin, and compare HEAD with origin/main before editing. Fast-forward only clean checkouts. For a dirty checkout, use an isolated worktree from fetched origin/main; never reset, stash, clean, pull into, or overwrite existing work.

On WSL, try the existing authenticated Windows Git/gh installation if Linux Git lacks credentials. Run Windows Git fetch from the authoritative checkout: Windows Git may not understand a Linux-created worktree's absolute `.git` pointer. Use Linux Git inside that worktree.

Keep changes project-local. Never modify another Hermes profile or app/backend source as part of this tooling update. Do not use uninstall --yes for selective removal: it removes all BMAD components.

## CIS compatibility mitigation

If installation fails because CIS `main` lacks `src/module.yaml`:

1. Inspect upstream tags and verify the chosen tag contains the required module definition.
2. The tested fallback is BMAD `6.12.1-next.0` with CIS `v0.3.2`, commit `97298b22fee1c7e482710d3a8414adb5cfccccd9`. Do not assume these remain the newest releases.
3. Use `--action update --pin cis=v0.3.2`, not `quick-update`: this installer version's quick-update path still resolved main despite the pin.
4. Preserve configured tools and other modules. Verify the resulting manifest records CIS `version: v0.3.2` and `channel: pinned`.

Tested invocation, replacing TARGET with the isolated checkout:

```bash
npx --yes bmad-method@6.12.1-next.0 install --directory "$TARGET" --action update --pin cis=v0.3.2 --no-shims --yes
```

Use `--no-shims` only when removing deprecated aliases is intended. Inspect configuration changes; an installer success does not prove custom values were preserved.

## Authorized deprecated removal

Only remove modules when requested or authorized for this project.

- Keep the supported module named `cis`. Its legitimate npmPackage is `bmad-creative-intelligence-suite`; never remove it through substring matching.
- Remove the separate legacy module with exact name `bmad-creative-intelligence-suite` and its project `_bmad/bmad-creative-intelligence-suite/` directory.
- Remove the exact `wds` module registration and `_bmad/wds/` directory.
- Before deleting, derive WDS-owned skills from `_bmad/_config/skill-manifest.csv` using exact `module == wds`. Remove only those project-local skill directories. WDS's `memory` and `sync` helpers are included; unrelated skills and Hermes memory are not.
- Remove WDS-specific project configuration and agent registrations. Preserve unrelated overrides, especially CIS list-valued settings.
- Preserve `_bmad-output/`, design artifacts, project history, supported `bmad-ux`, and application/backend files. Do not erase historical references in authored artifacts.
- Regenerate configuration and catalogs through the installer with the intended explicit module set. The tested retained set is `--modules bmm,bmb,cis,tea,bmad-loop` (core is implicit); adapt to the actual installation rather than silently dropping other modules.
- Verify deprecated registrations, directories, skills, and active catalog entries are absent, while CIS remains pinned and supported UX skills remain available.

## Verification and shipment

Inspect the final diff for unrelated changes and configuration regressions. Read installer warnings; distinguish retained legacy components from completed removal. Run `python3 tests/validate_project.py` when present and available BMAD configuration checks. Report actual results and skips; missing Deno is not a passing Deno check. Source-level tests are not Android runtime/build evidence.

Report the exact worktree, branch, versions, remaining warnings, and commit/push status. Do not merge into a dirty authoritative checkout. On a ship request, validate and review scoped changes before committing/pushing; unresolved high-severity defects block shipment.

For a skill-only request, install using skill_manage in the active Hermes profile and validate syntax/discovery. Do not implicitly ship unrelated pending repository changes. If a tool approval times out, do not retry the blocked operation through another tool; identify the unperformed verification honestly.
