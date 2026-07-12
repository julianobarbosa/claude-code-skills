# Import Files — Getting Existing Content into Your Vault

Guidance for importing existing documents into the vault. Replaces the previous broken script reference with practical options.

## Option 1: Manual Drop (Simplest)

Drop files directly into `inbox/`:

Supported formats:
- `.md` — Markdown (native, works immediately)
- `.pdf` — Viewable in Obsidian with built-in PDF viewer
- `.txt` — Plain text, rename to `.md` for full features
- `.docx` — Not natively supported; convert to Markdown first (see Option 3)

Then tell Claude: **"Sort everything in inbox/"**

Claude will read each file, infer its topic, and move it to the appropriate vault folder with proper frontmatter.

## Option 2: Bulk Import Script

For importing many files at once, use the included script:

```bash
python scripts/process_docs_to_obsidian.py ~/path/to/source/files /path/to/vault
```

What it does:
- Copies `.md`, `.txt`, `.pdf` files to `inbox/`
- Adds basic frontmatter to `.md` files (created date, source path)
- Skips files that already exist in the vault (by filename)
- Reports what was imported

After running, tell Claude: **"Sort everything in inbox/"**

## Option 3: Converting DOCX/PPTX to Markdown

For Word documents and PowerPoints, convert to Markdown before importing:

```bash
# Using pandoc (install: brew install pandoc / apt install pandoc)
pandoc document.docx -o document.md
pandoc slides.pptx -o slides.md
```

Then move the `.md` files to `inbox/`.

## Option 4: Gemini-Powered Processing

If you have the `file-intel-skill` installed, it can process entire folders with AI-powered summarization:

```
/file-intel ~/path/to/folder
```

This extracts content from PDF, PPTX, XLSX, DOCX, CSV, JSON, and text formats, generating Obsidian-ready summaries.

## Tips

- **Don't overthink sorting** — drop everything in `inbox/` first, sort later
- **Keep originals** — the import script copies, not moves
- **Large libraries** — import in batches of 20-50 files to keep sorting manageable
- **Images** — put in an `attachments/` folder; Obsidian handles image embedding natively
