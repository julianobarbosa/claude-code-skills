# Workflow: Capture Knowledge

Extract insights from conversations and save them as vault notes.

## Steps

1. **Identify knowledge type** from conversation signals:
   - "We decided..." -> ADR
   - "What is X?" / explanation -> Concept
   - "How do I..." / steps -> How-To
   - "In the meeting..." -> Meeting Note
   - Quick insight -> Daily Append
2. **Select template** from `KnowledgeCapturePatterns.md`
3. **Extract content** from conversation context
4. **Create note** via `Tools/NoteCreator.py capture`
5. **Link to existing notes** - search vault for related content
6. **Update MOCs** if relevant Map of Content exists

## Tool Usage

```bash
# Capture a concept
python Tools/NoteCreator.py capture \
  --type concept \
  --title "Event Sourcing" \
  --content "Event sourcing stores state as a sequence of events..." \
  --tags "architecture,patterns"

# Capture an ADR
python Tools/NoteCreator.py capture \
  --type adr \
  --title "Use PostgreSQL for primary storage" \
  --content "Context: We need a relational database..." \
  --tags "decision,database"

# Capture a how-to
python Tools/NoteCreator.py capture \
  --type howto \
  --title "Deploy to Kubernetes with Helm" \
  --content "Prerequisites: kubectl, helm..." \
  --tags "howto,kubernetes,helm"

# Append to today's daily note
python Tools/NoteCreator.py capture \
  --type daily \
  --content "Learned about event sourcing patterns today"
```

### Capture Types

| Type | Template | Destination |
|------|----------|-------------|
| `concept` | Concept template | `04 - Permanent/` |
| `adr` | ADR template | `03 - Resources/decisions/` |
| `howto` | How-To template | `03 - Resources/howtos/` |
| `meeting` | Meeting template | `10 - 1-1/` |
| `moc` | MOC template | `00 - Maps of Content/` |
| `daily` | Append to daily note | `06 - Daily/YYYY/MM/YYYYMMDD.md` |

## Auto-Detection

The workflow scans conversation for these signals:

| Signal | Capture Type |
|--------|-------------|
| Decision language ("decided", "chose", "went with") | ADR |
| Explanation language ("X is", "works by", "defined as") | Concept |
| Procedural language ("steps to", "how to", "first... then") | How-To |
| Meeting context ("attendees", "agenda", "action items") | Meeting |

## Context Files

- `KnowledgeCapturePatterns.md` - All templates and linking strategy
- `VaultOrganization.md` - PARA placement rules
