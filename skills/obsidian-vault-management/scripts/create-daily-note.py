#!/usr/bin/env python3
"""
Create a daily note with proper frontmatter and structure.
Usage: python create-daily-note.py [YYYY-MM-DD]
If no date provided, uses today's date.
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

def create_daily_note(date_str: str = None, vault_path: str = "."):
    """Create a daily note for the specified date."""

    if date_str:
        target_date = datetime.strptime(date_str, "%Y-%m-%d")
    else:
        target_date = datetime.now()

    # Calculate dates
    yesterday = target_date - timedelta(days=1)
    tomorrow = target_date + timedelta(days=1)
    review_date = target_date + timedelta(days=7)

    # Format dates
    date_formatted = target_date.strftime("%Y-%m-%d")
    filename = target_date.strftime("%Y%m%d")
    year = target_date.strftime("%Y")
    month = target_date.strftime("%m")
    year_month = target_date.strftime("%Y-%m")
    created = target_date.strftime("%Y-%m-%dT09:00")
    yesterday_str = yesterday.strftime("%Y-%m-%d")
    tomorrow_str = tomorrow.strftime("%Y-%m-%d")
    review_str = review_date.strftime("%Y-%m-%d")

    # Create directory structure
    daily_dir = Path(vault_path) / "06 - Daily" / year / month
    daily_dir.mkdir(parents=True, exist_ok=True)

    # Note path
    note_path = daily_dir / f"{filename}.md"

    if note_path.exists():
        print(f"Daily note already exists: {note_path}")
        return str(note_path)

    # Generate content
    content = f'''---
created: {created}
updated: {created}
toc: true
title: "{filename}"
template-type: Note
template-version: "1.8"
type: daily-note
status: true
weather: ""
location: ""
mood: ""
energy: /10
score: ""
tags:
  - daily
  - journal
  - {year}
  - {year_month}
aliases:
  - "{date_formatted}"
date_formatted: {date_formatted}
topics:
  - "[[daily]]"
  - "[[journal]]"
  - "[[{year}]]"
  - "[[{year_month}]]"
related:
  - "[[{yesterday_str}]]"
  - "[[{tomorrow_str}]]"
cssclasses:
  - daily
review_date: {review_str}
tasks_completed: 0
tasks_total: 0
sleep_hours: ""
exercise: false
---

# Daily Note - {date_formatted}

### Journal

#### TIME

...

***

### Tasks
- [ ] Task 1
- [ ] Task 2
- [ ] Task 3

# errors

# reference

```dataview
LIST
FROM "Clippings"
WHERE file.cday = this.file.cday
SORT file.ctime DESC
```

# navigate
<< [[{yesterday_str}]] | **Today** | [[{tomorrow_str}]] >>
'''

    # Write file
    note_path.write_text(content)
    print(f"Created daily note: {note_path}")
    return str(note_path)


if __name__ == "__main__":
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    vault_path = os.environ.get("VAULT_PATH", ".")
    create_daily_note(date_arg, vault_path)
