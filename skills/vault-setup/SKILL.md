---
name: vault-setup
description: >-
  Interactive Obsidian vault configurator. USE WHEN setting up obsidian vault,
  creating second brain, initializing knowledge base, new vault, vault bootstrap,
  configure obsidian, obsidian setup, OR personal knowledge management setup.
---

# vault-setup-skill

Interactive vault configurator — asks one free-text question, infers your role and folders, builds a personalized Obsidian vault with CLAUDE.md and companion skill links.

## Directory Structure

```
vault-setup-skill/
├── SKILL.md                          # This file (routing + quick ref)
├── RoleTemplates.md                  # Keyword-to-folder mapping table
├── PluginRecommendations.md          # Obsidian plugins by role type
├── Workflows/
│   ├── Setup.md                      # Main 6-step setup flow
│   ├── ImportFiles.md                # File import guidance
│   └── Verify.md                     # Post-setup verification
├── Tools/
│   ├── VaultBuilder.py               # CLI: create, verify, inject-global
│   └── VaultBuilder.help.md          # Tool documentation
└── scripts/
    └── process_docs_to_obsidian.py   # Bulk file import to inbox/
```

## Workflow Routing

| Intent | Workflow | Tool |
|--------|----------|------|
| Set up a new vault | `Workflows/Setup.md` | `Tools/VaultBuilder.py create` |
| Import existing files | `Workflows/ImportFiles.md` | `scripts/process_docs_to_obsidian.py` |
| Verify vault setup | `Workflows/Verify.md` | `Tools/VaultBuilder.py verify` |
| Add vault to global context | `Workflows/Setup.md` Step 5 | `Tools/VaultBuilder.py inject-global` |
| Choose Obsidian plugins | `PluginRecommendations.md` | — |
| Understand folder mapping | `RoleTemplates.md` | — |

## Examples

```
"Set up my Obsidian vault"              → Workflows/Setup.md
"I want to create a second brain"       → Workflows/Setup.md
"Import my documents into the vault"    → Workflows/ImportFiles.md
"Verify my vault is set up correctly"   → Workflows/Verify.md
"What plugins should I install?"        → PluginRecommendations.md
"Add this vault to my global config"    → Workflows/Setup.md Step 5
```

## Quick Reference

**Base folders** (always created): `inbox/`, `daily/`, `projects/`, `archive/`

**Additional folders** detected from keywords — see `RoleTemplates.md` for full mapping.

**Companion skills** (linked, not created): `daily-skill`, `tldr-skill`, `obsidian-master-skill`

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| `click` not found when running VaultBuilder.py | Missing dependency | `pip install click` |
| Vault folders created but Obsidian doesn't see them | Obsidian not pointed at vault root | Open Obsidian → "Open folder as vault" → select the vault directory |
| `inject-global` says "Already configured" but Claude doesn't see context | Vault path in CLAUDE.md doesn't match exactly | Check `~/.claude/CLAUDE.md` for the vault path — it must be the resolved absolute path |
| Symlink shows `[BROKEN]` in verify | Target skill directory was moved or deleted | Re-create the symlink: `ln -sf /path/to/skill ~/.claude/skills/skill-name` |
| `process_docs_to_obsidian.py` shows encoding warnings | Source files contain non-UTF-8 characters | Review warned files manually; convert source encoding with `iconv` if needed |

### Edge Cases

- **Empty keywords**: If `--role-keywords` is empty, only base folders are created (inbox, daily, projects, archive)
- **Vault path doesn't exist**: VaultBuilder creates it automatically via `mkdir -p`
- **Running create twice**: Safe — folders use `exist_ok=True`, CLAUDE.md is overwritten (back up first if customized)

---

## Gotchas

- **`inject-global` mutates `~/.claude/CLAUDE.md` with absolute path:** If you later move the vault, the global config still points to the old path and Claude silently loads nothing. Re-run `inject-global` after any vault relocation.
- **Re-running `create` overwrites a customized CLAUDE.md:** Folder creation uses `exist_ok=True` (safe) but CLAUDE.md is unconditionally rewritten. Back up first if you've hand-edited vault-level instructions.
- **`process_docs_to_obsidian.py` silently skips non-UTF-8 files:** Latin-1 or Windows-1252 source files emit a warning and are not imported. The summary report doesn't flag them as failures — grep stderr for "encoding" before trusting the count.
- **Symlinks to companion skills break on PAI directory restructure:** Verify shows `[BROKEN]` only if the symlink target is missing entirely; a renamed-but-existing target appears valid yet routes to the wrong skill. Re-run verify after any PAI skill reorganization.
- **Empty `--role-keywords` is not an error:** The vault gets only base folders (inbox/daily/projects/archive) with no warning. If you expected role-specific folders, check the inferred keywords in the setup transcript.
- **Obsidian doesn't see the vault until "Open folder as vault":** Creating the directory tree is not enough — Obsidian must be pointed at the vault root explicitly. New users often think the script failed because Obsidian shows an empty workspace.
