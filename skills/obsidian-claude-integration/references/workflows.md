# Common Workflows Reference

## Daily Workflows

### Morning Review

```text
User: "Review my daily note template and create today's note"

Claude Code Actions:
1. Read daily note template from Templates/
2. Generate today's date (YYYY-MM-DD)
3. Create note in Daily/YYYY/MM/YYYY-MM-DD.md
4. Fill template variables
5. Add navigation links (yesterday/tomorrow)
```

**Example Prompt:**
```
Create my daily note for today. Include:
- Link to yesterday's note
- Any unfinished tasks from yesterday
- Today's date properly formatted
```

### Evening Processing

```text
User: "Process today's daily note"

Claude Code Actions:
1. Read today's daily note
2. Extract mentions of people → create/link @person notes
3. Extract action items → format as tasks
4. Identify topics → add relevant tags
5. Suggest connections to existing notes
```

**Example Prompt:**
```
Review today's daily note and:
- Add wikilinks to all people mentioned
- Convert action items to - [ ] format
- Tag with relevant topics
- Suggest related notes to link
```

## Weekly Workflows

### Weekly Review

```text
User: "Generate my weekly review"

Claude Code Actions:
1. Find all daily notes from this week
2. Extract highlights, wins, challenges
3. Compile open tasks
4. Identify patterns in mood/energy
5. Create weekly review note
```

**Example Prompt:**
```
Create a weekly review note that summarizes:
- What I worked on (from daily notes)
- Key wins and challenges
- Open tasks carried forward
- Patterns in energy/mood if tracked
```

### Orphan Note Processing

```text
User: "Find and process orphan notes"

Claude Code Actions:
1. Identify notes with no incoming links
2. Analyze content for potential connections
3. Suggest or create links
4. Update MOCs if appropriate
```

**Example Prompt:**
```
Find notes with no backlinks. For each:
- Analyze the content
- Suggest 2-3 related notes to link from
- Ask before making changes
```

## Content Workflows

### Auto-Linking Entities

```text
User: "Add backlinks to all people, places, and books in this note"

Claude Code Actions:
1. Parse note content for entity mentions
2. For each entity:
   - Search for existing note
   - If found: add [[wikilink]]
   - If not found: create stub note
3. Update frontmatter with related entities
```

**Example Prompt:**
```
Read [[Meeting Notes 2025-01-05]] and:
- Find all people mentioned
- Create @person notes if they don't exist
- Add [[wikilinks]] in the text
- Update the 'people' frontmatter field
```

### Research Synthesis

```text
User: "Synthesize all notes on [topic]"

Claude Code Actions:
1. Search for notes tagged/about topic
2. Extract key insights from each
3. Identify connections and contradictions
4. Create synthesis note with outline
5. Link back to all sources
```

**Example Prompt:**
```
Create a synthesis note on "machine learning":
- Find all notes tagged #topic/ml or mentioning ML
- Extract the main insight from each
- Organize into coherent structure
- Include links to all source notes
```

### Book Note Creation

```text
User: "Create a book note for [title]"

Claude Code Actions:
1. Create note with BOOK- prefix
2. Add proper frontmatter (author, genre, etc.)
3. Create standard book note structure
4. Link to @author note
5. Tag appropriately
```

**Example Prompt:**
```
Create a book note for "Atomic Habits" by James Clear:
- Use BOOK-atomic-habits-james-clear.md
- Add frontmatter with author, year, genre
- Create sections for summary, key ideas, quotes
- Link to @james-clear (create if missing)
```

## Maintenance Workflows

### Broken Link Repair

```text
User: "Fix all broken wikilinks"

Claude Code Actions:
1. Find all [[wikilinks]] in vault
2. Check each link resolves
3. For broken links:
   - Search for similar file names
   - Suggest corrections
   - Fix with confirmation
```

**Example Prompt:**
```
Find all broken wikilinks in the vault.
For each one:
- Show me the context
- Suggest the correct target
- Wait for my approval before fixing
```

### Frontmatter Standardization

```text
User: "Standardize frontmatter across all notes"

Claude Code Actions:
1. Read CLAUDE.md for schema
2. Find notes missing required fields
3. Add missing fields with defaults
4. Normalize date formats
```

**Example Prompt:**
```
Check all notes in Projects/ folder:
- Ensure all have 'created' and 'updated' fields
- Add 'status: active' if missing status
- Add 'type: project' if missing type
- Show me a summary of changes made
```

### Tag Cleanup

```text
User: "Clean up and consolidate tags"

Claude Code Actions:
1. List all unique tags
2. Find similar/duplicate tags
3. Suggest consolidation
4. Rename with confirmation
```

**Example Prompt:**
```
Analyze all tags in the vault:
- Find duplicates (ml vs machine-learning)
- Find orphan tags (used only once)
- Suggest hierarchy improvements
- Don't change anything without asking
```

## Project Workflows

### Project Setup

```text
User: "Create a new project structure"

Claude Code Actions:
1. Create PROJECT-name folder
2. Create index note with template
3. Add standard sections
4. Link to project MOC
```

**Example Prompt:**
```
Create a new project "Website Redesign":
- Create Projects/website-redesign/ folder
- Create PROJECT-website-redesign.md index
- Add sections: Overview, Goals, Tasks, Notes, Resources
- Link from [[Projects MOC]]
```

### Project Archive

```text
User: "Archive completed project [name]"

Claude Code Actions:
1. Update project status to complete
2. Move folder to Archive/
3. Update all incoming links
4. Add completion date
5. Generate project summary
```

**Example Prompt:**
```
Archive the "Website Redesign" project:
- Set status to complete
- Move to Archive/2025/
- Update links from other notes
- Add 'completed' date to frontmatter
- Create a brief summary of outcomes
```

## Integration Workflows

### External Content Import

```text
User: "Import article from [URL]"

Claude Code Actions:
1. Fetch URL content
2. Extract main content
3. Create note with proper frontmatter
4. Add source attribution
5. Suggest related notes
```

**Example Prompt:**
```
Import this article: [URL]
- Create note in Resources/articles/
- Add frontmatter: source, author, date
- Extract key quotes
- Suggest existing notes to link
```

### Export for Sharing

```text
User: "Export [note] for sharing"

Claude Code Actions:
1. Read note content
2. Resolve embeds and transclusions
3. Convert wikilinks to readable format
4. Export as clean markdown
```

**Example Prompt:**
```
Prepare [[Project Summary]] for sharing:
- Expand all embedded notes
- Convert [[wikilinks]] to plain text
- Remove internal frontmatter
- Output clean markdown I can copy
```

## Workflow Templates

### Custom Workflow Definition

```markdown
## Workflow: [Name]

### Trigger
[When to run this workflow]

### Inputs
- [What information is needed]

### Steps
1. [First action]
2. [Second action]
3. [Third action]

### Outputs
- [What is created/modified]

### Example Prompt
```
[Example user prompt to trigger this workflow]
```
```

### Automated Workflow (Git Hook)

```bash
#!/bin/bash
# .git/hooks/post-commit

# Trigger workflow on specific file patterns
changed=$(git diff-tree --no-commit-id --name-only -r HEAD)

# Run inbox processing
if echo "$changed" | grep -q "inbox/"; then
  claude --print "Process new notes in inbox/"
fi

# Run link repair after renames
if git log -1 --diff-filter=R --summary | grep -q "rename"; then
  claude --print "Check for broken links after recent file renames"
fi
```
