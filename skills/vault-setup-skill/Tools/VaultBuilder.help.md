# VaultBuilder — CLI Reference

Python CLI tool for creating and verifying Obsidian vaults.

## Prerequisites

```bash
pip install click
```

## Commands

### `create` — Build vault structure

Creates folders and CLAUDE.md based on keyword detection.

```bash
python Tools/VaultBuilder.py create \
  --role-keywords "devops,cloud,pipeline" \
  --scope work \
  --vault-path /path/to/vault \
  --role-description "DevOps engineer managing Azure infrastructure"
```

**Flags:**

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--role-keywords` | Yes | — | Comma-separated keywords for folder detection |
| `--scope` | No | `work` | `work`, `personal`, or `both` |
| `--vault-path` | No | `.` | Path to create vault in |
| `--role-description` | No | — | Free-text description for CLAUDE.md |
| `--open-obsidian` / `--no-open-obsidian` | No | `--open-obsidian` | Open vault in Obsidian after creation |

### `verify` — Check vault setup

Runs post-setup verification checks.

```bash
python Tools/VaultBuilder.py verify --vault-path /path/to/vault
```

**Flags:**

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--vault-path` | No | `.` | Path to vault |

**Output:** Structured `[ok]` / `[MISSING]` / `[BROKEN]` / `[--]` status for each check.

### `inject-global` — Safe global context injection

Adds vault path to `~/.claude/CLAUDE.md`. Idempotent — safe to run multiple times.

```bash
python Tools/VaultBuilder.py inject-global --vault-path /absolute/path/to/vault
```

**Flags:**

| Flag | Required | Default | Description |
|------|----------|---------|-------------|
| `--vault-path` | Yes | — | Absolute path to vault |

**Behavior:**
- If vault path already in `~/.claude/CLAUDE.md` → skips ("Already configured")
- If `## My Personal Context` section exists → appends under it
- If section doesn't exist → adds section at end
- If file doesn't exist → creates it with the section

## Examples

```bash
# DevOps engineer, work-only vault
python Tools/VaultBuilder.py create --role-keywords "devops,cloud,pipeline,terraform" --scope work

# Student with personal tracking
python Tools/VaultBuilder.py create --role-keywords "notes,class,study,personal" --scope both --vault-path ~/vaults/school

# Verify an existing vault
python Tools/VaultBuilder.py verify --vault-path ~/vaults/work

# Add vault to global context
python Tools/VaultBuilder.py inject-global --vault-path /Users/me/vaults/work
```
