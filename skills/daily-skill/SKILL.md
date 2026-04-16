---
name: daily-skill
description: Start the day with vault context, continuity from yesterday, and prioritized action items. Read or create today's daily note, carry forward unfinished tasks, surface active projects, and check inbox. USE WHEN good morning, start my day, daily, what's open, daily standup, what should I work on, morning routine, begin day, daily check-in, what's pending.
---

# Daily Skill

This skill opens the day with full context so you can hit the ground running. It bridges yesterday's loose ends with today's priorities, keeping nothing lost between sessions.

## Step 1: Find Yesterday's Context

Look in `daily/` for the most recent daily note before today. Read it and extract:
- Any unchecked tasks (`- [ ]`) or items under **End of Day** that signal unfinished work
- Any **Blockers** that were listed

These become the **Carry Forward** section in today's note.

If no previous daily note exists, skip this step — it's a fresh start.

## Step 2: Read or Create Today's Daily Note

Check for `daily/YYYY-MM-DD.md` using today's actual date.

**If it exists:** Read it and use it as the basis for the briefing. Don't overwrite the user's content.

**If it doesn't exist:** Create it using the template from `references/templates.md`:
- Use the **Standard Weekday** template as the base
- On **Mondays**, add the **Week Focus** section
- On **Fridays**, add the **Week Retro** section
- Populate **Carry Forward** with items extracted in Step 1
- Replace `{{DATE}}` with today's date in `YYYY-MM-DD` format

## Step 3: Scan Active Work

Scan `projects/` for any files. For each project file found, check if it mentions a status — surface anything that isn't explicitly marked as completed or archived. Rank by file modification time (most recent first).

Also check `inbox/` — list any unprocessed files. If the inbox philosophy from CLAUDE.md applies ("inbox should stay empty"), mention how many items are waiting.

## Step 4: Briefing

Present a concise morning briefing:

```
Good morning, Juliano.

**Carried forward:**
- [items from yesterday, or "Clean slate — nothing carried forward"]

**Active projects:**
- [project name] — [status/next action from file]

**Inbox:** [N items waiting | Empty]

What are we working on today?
```

Keep it tight — this is a launchpad, not a report. If there are blockers from yesterday, call them out prominently.

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| No previous daily note found | First time using the skill, or `daily/` folder is empty | Skip carry-forward — start with a clean slate |
| Template not found | `references/templates.md` missing (located relative to this skill's root directory) | Create the daily note with a minimal template: heading + sections for capture, tasks, log |
| `projects/` folder missing | Vault doesn't use this folder name | Check CLAUDE.md for the vault's actual project folder name and scan that instead |
| Briefing shows stale data | Daily note was created by another tool with different structure | Read whatever exists — adapt to the note's actual sections rather than forcing the template |

### Edge Cases

- **Weekend/holiday gap**: If the last daily note is several days old, still carry forward its open items
- **Multiple daily notes for same date**: Use the one matching `YYYY-MM-DD.md` exactly; ignore timestamped variants
- **Empty inbox**: Report "Inbox: Empty" — this is a positive signal, not an error

### Platform Notes

This skill works on macOS, Linux, and Windows. File paths use forward slashes in vault context regardless of platform — Obsidian normalizes paths internally.
