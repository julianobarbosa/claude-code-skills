---
name: file-intel
description: Run the Gemini file processor on any folder — extracts content from PDF, PPTX, XLSX, DOCX, CSV, JSON, and any text format, then generates Obsidian-ready summaries. Use when asked to "summarise this folder", "run file intel", "process these files", or a folder path is provided and summaries are needed.
---

# File Intel — Gemini File Processor

Runs `scripts/process_files_with_gemini.py` on a folder of files and produces Obsidian-ready summaries.

## Step 1: Get the folder

Use `AskUserQuestion`:

```
Question: "Which folder should I process?"
Options:
1. "This vault's inbox/" — process the inbox folder
2. "Custom path" — user specifies a folder
```

If the user selects option 2, they'll type the path in the "Other" input.

## Step 2: Run the script

Run via Bash from the vault root:

```bash
python scripts/process_files_with_gemini.py <folder_path>
```

- If inbox/: `python scripts/process_files_with_gemini.py inbox/`
- If custom path: pass it as the argument

Show the terminal output as it runs so the user can see files being processed live.

## Step 3: Open the output

After the script completes, open the output folder:

```bash
open "outputs/file_summaries/YYYY-MM-DD/"
```

Replace `YYYY-MM-DD` with today's date from the script output.

## Step 4: Report back

Tell the user:
- How many files were processed
- Where the summaries landed
- Point them to `MASTER_SUMMARY.md` as the single-file digest of everything
- Suggest: "Open Claude Code and say: Sort everything in inbox/ into the right folders"

## Notes

- Supported formats: PDF, PPTX, XLSX, DOCX, CSV, JSON, XML, MD, TXT, PY, JS, HTML, CSS
- Output: `outputs/file_summaries/YYYY-MM-DD/`
- Each file gets its own `*_summary.md`
- `MASTER_SUMMARY.md` combines all summaries into one digest
- Summaries are context-aware: deliverables (invoices, reports) vs reference files (code, config) get different formats
