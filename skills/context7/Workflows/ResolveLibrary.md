# ResolveLibrary Workflow

> **Trigger:** "find library ID", "resolve library", "what's the context7 ID for"

## Purpose

Convert a library/package name to a Context7-compatible library ID that can be used with the query command.

## When to Use

- When you need only the library ID (not full documentation)
- When exploring what libraries are available
- When the full lookup command fails and you need to debug

## Command

```bash
c7-resolve <library_name> [query]
```

**Parameters:**
- `library_name` (required): The library name to search (e.g., "react", "next.js", "kubernetes")
- `query` (optional): Context query for LLM-powered ranking of results

## Steps

### Step 1: Run Resolve Command

```bash
c7-resolve <library_name> "<optional context>"
```

### Step 2: Analyze Results

The tool returns matching libraries with:
- Library ID (e.g., `/facebook/react`)
- Name and description
- Documentation coverage information

### Step 3: Select Best Match

**Selection criteria (in order):**
1. Name similarity to query (exact matches prioritized)
2. Description relevance to query's intent
3. Higher documentation coverage
4. Official/verified sources

## Examples

### Basic Resolve

```bash
c7-resolve react
```

Output:
```
[INFO] Using known library ID for 'react'

Library ID: /facebook/react

Tip: c7-query "/facebook/react" "your query"
```

### Resolve with Context

```bash
c7-resolve next.js "authentication middleware"
```

Output includes ranked results based on the context query.

### Resolve Unknown Library

```bash
c7-resolve drizzle-orm
```

## Known Library IDs (Skip API Call)

These common libraries are cached locally - no API call needed:

| Library | ID |
|---------|-----|
| react | `/facebook/react` |
| next.js, nextjs | `/vercel/next.js` |
| vue | `/vuejs/vue` |
| kubernetes, k8s | `/kubernetes/kubernetes` |
| go, golang | `/golang/go` |
| python | `/python/cpython` |
| node, nodejs | `/nodejs/node` |
| typescript, ts | `/microsoft/typescript` |
| angular | `/angular/angular` |
| svelte | `/sveltejs/svelte` |
| express | `/expressjs/express` |
| fastify | `/fastify/fastify` |
| nest, nestjs | `/nestjs/nest` |
| prisma | `/prisma/prisma` |
| drizzle | `/drizzle-team/drizzle-orm` |
| tailwind, tailwindcss | `/tailwindlabs/tailwindcss` |

## Important Notes

- **Max 3 calls per question** - if you can't find a match after 3 attempts, use best available
- **Don't include sensitive info** in query parameter (no API keys, passwords, personal data)
- The library ID format is always `/org/project` or `/org/project/version`
- Known libraries skip the API call entirely for faster response
- Resolved IDs are cached at `~/.cache/context7/resolved.json` for 24h; pass `--no-cache` to skip or `--clear-cache` to wipe
- Add `--json` to emit a parseable structure on stdout (decorative logs go to stderr)
- Without `bun link`, prefix any command with `cd ~/.claude/skills/context7/Tools && bun src/cli/resolve.ts ...`

## Common Errors

| Exit | Meaning | Recovery |
|------|---------|----------|
| `3` | Bad/missing `CONTEXT7_API_KEY` | Set env var or pass `--api-key <key>` |
| `4` | Library not found | Check name spelling; try a broader query; consult Known Library IDs table |
| `5` | Rate limited (429) | Wait the `Retry-After` window, raise `--max-retries`, or set an API key |
| `7` | Timed out | Raise `--timeout <ms>` |
