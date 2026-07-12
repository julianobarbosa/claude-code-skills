# COG Self-Evolving Pattern Reference

## Overview

COG (Claude-Obsidian-Git) is a self-evolving second brain pattern that combines:
- **Claude Code** for AI-powered organization
- **Obsidian** for knowledge storage and linking
- **Git** for version control and automation triggers

No database, no vendor lock-in - just markdown files that self-organize.

## Architecture

```text
vault/
├── .git/                        # Version control
│   └── hooks/
│       ├── post-commit          # Trigger maintenance
│       └── pre-push             # Validate integrity
├── CLAUDE.md                    # AI manifest
├── _meta/
│   ├── patterns.md              # Learned conventions
│   ├── conventions.md           # Auto-discovered rules
│   ├── maintenance-log.md       # Self-healing audit
│   └── orphan-candidates.md     # Notes needing links
├── inbox/                       # Quick capture
├── notes/                       # Organized content
├── daily/                       # Journal entries
├── projects/                    # Active work
└── archive/                     # Completed items
```

## Self-Evolving Features

### 1. Pattern Learning

Claude Code observes your vault and learns:
- Naming conventions (kebab-case, PascalCase, etc.)
- Frontmatter schemas (which fields you use)
- Tag hierarchies (how you organize topics)
- Folder structures (where notes belong)

**Pattern Discovery:**

```markdown
<!-- _meta/patterns.md -->
# Discovered Patterns

## Naming
- Notes: kebab-case-titles.md
- Daily: YYYY-MM-DD.md format
- Projects: PROJECT-name.md prefix

## Frontmatter
- Always includes: created, updated, tags
- Projects add: status, priority, due
- Daily adds: mood, energy, highlights

## Tags
- Hierarchy: #category/subcategory
- Status: #status/active, #status/review
- Type: #type/note, #type/project
```

### 2. Auto Cross-References

When notes are moved or renamed, Claude Code:
1. Detects file changes via git
2. Finds all broken wikilinks
3. Updates references to new paths
4. Logs changes in maintenance-log.md

**Self-Healing Script:**

```bash
#!/bin/bash
# .git/hooks/post-commit

# Get changed files
changed=$(git diff-tree --no-commit-id --name-only -r HEAD)

# Check for renames/moves
if echo "$changed" | grep -q ".md"; then
  claude --print "
  Recent commit changed files:
  $changed

  Check for broken wikilinks caused by these changes.
  Update any broken references and log to _meta/maintenance-log.md
  "
fi
```

### 3. Orphan Detection

Identifies notes with no connections:

```markdown
<!-- _meta/orphan-candidates.md -->
# Orphan Notes (Auto-Generated)

Notes with no incoming or outgoing links:

## High Priority (30+ days old)
- [[Random Thought 2024-10-15]] - Consider linking to #topic/philosophy
- [[Meeting Notes ABC]] - May belong in projects/

## Recent (< 7 days)
- [[Quick Capture]] - Needs processing
```

### 4. Consistency Validation

Pre-push hook validates vault integrity:

```bash
#!/bin/bash
# .git/hooks/pre-push

# Check for missing frontmatter
missing=$(find . -name "*.md" -exec grep -L "^---" {} \;)
if [ -n "$missing" ]; then
  echo "Notes missing frontmatter:"
  echo "$missing"
  exit 1
fi

# Validate no broken internal links
broken=$(claude --print "List all broken wikilinks in vault" 2>/dev/null)
if [ -n "$broken" ]; then
  echo "Broken links detected:"
  echo "$broken"
  exit 1
fi

exit 0
```

## Implementation Guide

### Step 1: Initialize Git

```bash
cd /path/to/vault
git init
echo ".obsidian/workspace.json" >> .gitignore
echo ".obsidian/cache" >> .gitignore
git add .
git commit -m "Initial vault commit"
```

### Step 2: Create Meta Structure

```bash
mkdir -p _meta
touch _meta/patterns.md
touch _meta/conventions.md
touch _meta/maintenance-log.md
touch _meta/orphan-candidates.md
```

### Step 3: Create CLAUDE.md Manifest

```markdown
# COG Vault Manifest

## System Behavior
This vault uses the COG self-evolving pattern. Claude Code should:
1. Learn and enforce discovered patterns
2. Fix broken links automatically
3. Log all maintenance actions
4. Suggest connections for orphan notes

## Meta Files
- `_meta/patterns.md` - Update when new patterns discovered
- `_meta/conventions.md` - Document naming rules
- `_meta/maintenance-log.md` - Append maintenance actions
- `_meta/orphan-candidates.md` - Regenerate on request

## Maintenance Commands
- "Run vault maintenance" - Full health check
- "Find orphan notes" - Update orphan-candidates.md
- "Validate consistency" - Check frontmatter/links
- "Learn patterns" - Analyze and update patterns.md
```

### Step 4: Add Git Hooks

```bash
# Make hooks executable
chmod +x .git/hooks/post-commit
chmod +x .git/hooks/pre-push
```

### Step 5: Initial Pattern Learning

```bash
claude "Analyze this vault and document all patterns you find.
Update _meta/patterns.md with naming, frontmatter, and tag conventions."
```

## Maintenance Workflows

### Daily Maintenance

```bash
# Run during daily review
claude "Process inbox notes:
1. Add proper frontmatter
2. Suggest appropriate folders
3. Add relevant tags
4. Link to related notes"
```

### Weekly Maintenance

```bash
# Run weekly
claude "Run full vault maintenance:
1. Find orphan notes
2. Check for broken links
3. Update pattern documentation
4. Identify stale notes (no updates in 90 days)"
```

### Monthly Maintenance

```bash
# Run monthly
claude "Deep vault analysis:
1. Review and consolidate similar notes
2. Update MOCs (Maps of Content)
3. Archive completed projects
4. Generate vault statistics"
```

## Maintenance Log Format

```markdown
<!-- _meta/maintenance-log.md -->
# Vault Maintenance Log

## 2025-01-05 14:30

### Actions Taken
- Fixed 3 broken wikilinks from file renames
- Added frontmatter to 2 notes in inbox/
- Linked orphan note [[random-idea]] to [[project-brainstorm]]

### Files Modified
- notes/project-brainstorm.md (added link)
- inbox/random-idea.md (moved to notes/, added frontmatter)
- projects/old-project.md (fixed broken link)

---

## 2025-01-04 09:15
...
```

## Advanced Features

### Smart Archive

```bash
claude "Find notes marked #status/complete or with due dates passed.
Move to archive/ folder, update all references, log the action."
```

### Knowledge Synthesis

```bash
claude "Find all notes tagged #topic/machine-learning.
Create a synthesis note summarizing key insights.
Link back to all source notes."
```

### Conflict Resolution

When simultaneous edits occur:

```bash
claude "Compare my local changes with the version in git.
Show me conflicts and suggest resolution strategy."
```

## Best Practices

1. **Commit frequently** - More granular history = better self-healing
2. **Review changes** - Check git diff before committing AI edits
3. **Document exceptions** - Update patterns.md when breaking conventions
4. **Regular maintenance** - Schedule weekly/monthly cleanup
5. **Backup strategy** - Push to remote regularly

## Troubleshooting

### Hooks Not Running

```bash
# Check permissions
ls -la .git/hooks/

# Make executable
chmod +x .git/hooks/*
```

### Too Many Changes

```bash
# Limit maintenance scope
claude "Only process inbox/ folder today"
```

### Pattern Drift

```bash
# Reset to documented patterns
claude "Enforce patterns in _meta/patterns.md strictly.
Correct any deviations found in the vault."
```
