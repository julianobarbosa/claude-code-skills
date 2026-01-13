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
cd ~/.claude/skills/Context7/Tools && bun src/cli/resolve.ts <library_name> [query]
```

**Parameters:**
- `library_name` (required): The library name to search (e.g., "react", "next.js", "kubernetes")
- `query` (optional): Context query for LLM-powered ranking of results

## Steps

### Step 1: Run Resolve Command

```bash
cd ~/.claude/skills/Context7/Tools && bun src/cli/resolve.ts <library_name> "<optional context>"
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
cd ~/.claude/skills/Context7/Tools && bun src/cli/resolve.ts react
```

Output:
```
[INFO] Using known library ID for 'react'

Library ID: /facebook/react

Tip: Use this ID with 'bun query.ts "/facebook/react" "your query"'
```

### Resolve with Context

```bash
cd ~/.claude/skills/Context7/Tools && bun src/cli/resolve.ts next.js "authentication middleware"
```

Output includes ranked results based on the context query.

### Resolve Unknown Library

```bash
cd ~/.claude/skills/Context7/Tools && bun src/cli/resolve.ts drizzle-orm
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
