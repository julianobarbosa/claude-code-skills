# URL Gotchas — NotebookLM source adds

Rules learned from real notebook builds. Consult before calling `mcp__notebooklm-rpc__notebook_add_url`.

## Domain blocklist (known-failing)

NotebookLM's URL fetcher silently fails — or registers a broken placeholder source — on these domains. **Scrape content with WebFetch/WebSearch, then add as text via `notebook_add_text` instead.**

| Domain | Failure mode | Verified |
|--------|--------------|----------|
| `medium.com/*` | Silent fail; common user frustration | Recurring in NotebookLM community discussion |
| `*.medium.com` | Same as above | Same |
| `quora.com/*` | Returns `status: error, Failed to add URL source`; bot detection | 2026-04-21 |
| `linkedin.com/*` | Auth-gated; typically fails | Reported pattern |

If a Quora or Medium URL add fails, NotebookLM may still create a broken placeholder source in the notebook — visible as the raw URL string with no title. Remove these via `source_delete` if they appear.

## Sequential-only rule

`notebook_add_url` **cascade-fails when called in parallel**. The second call while the first is pending will frequently error or produce an incomplete source.

**Always add URLs sequentially** — wait for each call's success response before issuing the next. Parallel-tool-call is the wrong pattern here.

Same rule applies to `notebook_add_text` if you're adding many text sources back-to-back, though text adds are more tolerant.

## URL cleaning

### llms.txt

Strip any trailing `.md` from `llms.txt` URLs before adding:

- ✅ `https://example.com/llms.txt`
- ❌ `https://example.com/llms.txt.md`

NotebookLM fetches the URL literally; `.md` suffix produces a 404 or wrong content type.

### Reddit

Reddit is tolerant of both forms, but prefer the `old.reddit.com` redirect target or the canonical `reddit.com` form with the trailing slug. Example:

- ✅ `https://reddit.com/r/ClaudeCode/comments/1r9g45u/i_made_a_ghosttybased_terminal_with_vertical_tabs/`
- ❌ `https://www.reddit.com/r/ClaudeCode/comments/1r9g45u/` (works but loses the slug — title may be less informative)

### GitHub

Direct links to `/blob/main/README.md` work. Prefer the root repo URL (e.g., `github.com/org/repo`) for the best auto-title; NotebookLM fetches the README automatically.

GitHub Discussions (`/discussions/NNN`) and Issues (`/issues/NNN`) load fine as URLs.

### Hacker News

`news.ycombinator.com/item?id=NNNNN` works reliably. Include the top-level discussion, not individual comment permalinks.

### YouTube

Full watch URLs work: `youtube.com/watch?v=ID` or `youtu.be/ID`. Short URLs are fine.

## When in doubt, probe first

If the domain isn't on this list but you're unsure:

1. Run `WebFetch` on the URL with a trivial prompt
2. If WebFetch returns bot-detection content, auth-wall language, or empty body → NotebookLM will likely fail too. Scrape content and add as text.
3. If WebFetch returns real content → `notebook_add_url` usually succeeds.

## Recovery if a bad URL was added

```
mcp__notebooklm-rpc__source_delete(notebook_id=NB, source_id=<bad_source_id>)
```

Source IDs are in the error-response metadata or visible via `notebook_get`.
