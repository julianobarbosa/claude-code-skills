# Knowledge Capture Patterns

Templates and workflows for extracting knowledge from conversations into vault notes.

## Capture Types

| Type | When to Use | Destination |
|------|------------|-------------|
| ADR | Architecture/design decisions | `03 - Resources/decisions/` |
| Concept | New concept or mental model | `04 - Permanent/` |
| How-To | Step-by-step procedure | `03 - Resources/howtos/` |
| Meeting Note | Meeting outcomes and actions | `10 - 1-1/` or `01 - Projects/` |
| MOC Update | New topic index or update | `00 - Maps of Content/` |
| Daily Append | Quick insight to today's note | `06 - Daily/YYYY/MM/YYYYMMDD.md` |

## ADR Template (Architecture Decision Record)

```yaml
---
created: YYYY-MM-DDTHH:mm
updated: YYYY-MM-DDTHH:mm
type: adr
status: accepted | proposed | deprecated | superseded
tags:
  - decision
  - topic/subtopic
---
```

```markdown
# ADR: [Decision Title]

## Status
Accepted

## Context
What is the issue we're deciding on? What forces are at play?

## Decision
What is the change that we're proposing and/or doing?

## Consequences
What becomes easier or harder as a result of this decision?

### Positive
- Benefit 1
- Benefit 2

### Negative
- Tradeoff 1
- Tradeoff 2

## Related
- [[Previous ADR]]
- [[Related Project]]
```

## Concept Template

```yaml
---
created: YYYY-MM-DDTHH:mm
updated: YYYY-MM-DDTHH:mm
type: zettelkasten
tags:
  - permanent
  - concept
  - topic
---
```

```markdown
# [Concept Name]

## Definition
One-paragraph explanation in your own words.

## Key Insight
**Core idea**: [Single sentence capturing the essence]

## How It Works
Explain the mechanism or model.

## Examples
- Example 1
- Example 2

## Connections
- [[Related Concept 1]] - how it relates
- [[Related Concept 2]] - how it relates

## Sources
- Where you learned this
```

## How-To Template

```yaml
---
created: YYYY-MM-DDTHH:mm
updated: YYYY-MM-DDTHH:mm
type: howto
tags:
  - howto
  - tool/technology
---
```

```markdown
# How To: [Task Description]

## Prerequisites
- Requirement 1
- Requirement 2

## Steps

### 1. [First Step]
Details and commands.

### 2. [Second Step]
Details and commands.

### 3. [Third Step]
Details and commands.

## Verification
How to confirm it worked.

## Troubleshooting
Common issues and fixes.

## Related
- [[Related How-To]]
- [[Tool Documentation]]
```

## Meeting Note Template

```yaml
---
created: YYYY-MM-DDTHH:mm
updated: YYYY-MM-DDTHH:mm
type: meeting
attendees:
  - "[[Person 1]]"
  - "[[Person 2]]"
tags:
  - meeting
  - project/name
---
```

```markdown
# Meeting: [Topic] - YYYY-MM-DD

## Attendees
- [[Person 1]]
- [[Person 2]]

## Agenda
1. Topic 1
2. Topic 2

## Notes
Key discussion points.

## Decisions
- Decision 1
- Decision 2

## Action Items
- [ ] @[[Person 1]] - Action by YYYY-MM-DD
- [ ] @[[Person 2]] - Action by YYYY-MM-DD

## Follow-up
Next meeting: [[YYYYMMDD]]
```

## MOC (Map of Content) Template

```yaml
---
created: YYYY-MM-DDTHH:mm
updated: YYYY-MM-DDTHH:mm
type: moc
tags:
  - moc
  - topic
---
```

```markdown
# [Topic] MOC

## Overview
Brief description of this knowledge area.

## Core Concepts
- [[Concept 1]] - brief description
- [[Concept 2]] - brief description

## How-Tos
- [[How To: Task 1]]
- [[How To: Task 2]]

## Decisions
- [[ADR: Decision 1]]
- [[ADR: Decision 2]]

## Projects
- [[Project using this topic]]

## Resources
- [[External reference]]
- [[Book notes]]
```

## Capture Workflow

### From Conversation to Note

1. **Identify capture type** - What kind of knowledge is this? (ADR, concept, howto, etc.)
2. **Select template** - Use appropriate template above
3. **Extract key content** - Pull relevant information from conversation
4. **Add metadata** - Frontmatter with timestamps, tags, type
5. **Create wikilinks** - Link to existing related notes in vault
6. **Place in PARA folder** - Put in correct location
7. **Update MOCs** - Add link to relevant Maps of Content if they exist

### Auto-Detection Signals

| Signal in Conversation | Capture Type |
|----------------------|--------------|
| "We decided to..." / "Let's go with..." | ADR |
| "What is X?" / "X works by..." | Concept |
| "How do I..." / "Steps to..." | How-To |
| "In the meeting..." / "We discussed..." | Meeting Note |
| "I want to track all notes about..." | MOC |
| Quick insight or todo | Daily Append |

### Linking Strategy

When creating a captured note:
1. Search vault for existing notes on the same topic
2. Add `[[wikilinks]]` to those notes
3. Check if a relevant MOC exists and add entry
4. Add backlinks from related notes to new note
5. Tag with hierarchical tags matching vault conventions
