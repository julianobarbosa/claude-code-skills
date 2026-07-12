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

---

## Gotchas

- **Encoding detection is best-effort, not deterministic:** Files saved as Windows-1252 or Latin-1 may be processed as garbled UTF-8 instead of failing loudly. Spot-check the first summary of any batch from unknown sources — if accented characters render as mojibake, the source encoding was misdetected.
- **Password-protected and encrypted PDFs return blank summaries:** Gemini cannot extract text from locked PDFs but the script does not flag them as failures. Check the file size of each `*_summary.md` — anything under ~200 bytes is suspect.
- **Scanned-image PDFs depend on OCR confidence:** Low-DPI scans, handwriting, or rotated pages produce summaries with hallucinated content rather than honest "could not read." Verify scanned documents against the original before trusting downstream decisions.
- **XLSX files with multiple sheets summarize only the active sheet:** The processor reads what the workbook opens to by default; other sheets are skipped silently. For multi-sheet financials, split into separate files or expect partial coverage.
- **MASTER_SUMMARY.md grows linearly and exceeds context on large folders:** A 200-file inbox produces a digest too large to feed back into another LLM call without truncation. For batches over ~50 files, work from the per-file summaries instead of the master.
- **Re-running on the same folder writes to a new `YYYY-MM-DD/` subdirectory:** Two runs on the same day overwrite each other; runs on different days produce duplicates without cross-reference. Clear or archive prior output before re-processing.
