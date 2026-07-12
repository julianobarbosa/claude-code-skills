---
name: context7
description: Up-to-date, version-specific library documentation and working code examples sourced from real project repos via the Context7 documentation aggregation API — covers 1000+ libraries (React, Next.js, Vue, Kubernetes, Go, Python, TypeScript, Prisma, Tailwind, and more). USE WHEN looking up API signatures, framework docs, version-specific behavior, code examples, library configuration, migration guides, OR before writing code against a library you might be guessing about. NOT FOR refactoring existing code, debugging business logic, general programming concepts, or libraries Context7 doesn't index (use web search instead). Grounds answers in real source documentation to prevent hallucinated APIs.
---

# Context7

Query up-to-date, version-specific documentation and code examples directly from source libraries via Context7's documentation aggregation platform.

## Why Context7

| Benefit | Description |
|---------|-------------|
| **Current APIs** | No hallucinated or outdated patterns - documentation comes from actual sources |
| **Version-Specific** | Gets docs for exact library versions you're using |
| **Code Examples** | Real, working code extracted from actual documentation |
| **Broad Coverage** | 1000+ libraries including React, Next.js, Vue, Go, Python, Kubernetes, etc. |

## Setup

```bash
# Install dependencies
cd ~/.claude/skills/context7/Tools
bun install

# Optional: link binaries globally so c7-lookup / c7-resolve / c7-query are on PATH
bun link

# Optional: API key for higher rate limits
export CONTEXT7_API_KEY="ctx7sk_your_key_here"   # context7.com/dashboard
```

## Available CLI Tools

| Tool | Purpose | Short form (after `bun link`) | Long form |
|------|---------|-------------------------------|-----------|
| `lookup` | Resolve + query in one shot | `c7-lookup <library> <query>` | `bun src/cli/lookup.ts <library> <query>` |
| `resolve` | Find Context7 library ID | `c7-resolve <library> [query]` | `bun src/cli/resolve.ts <library> [query]` |
| `query` | Query docs by known ID | `c7-query <library_id> <query>` | `bun src/cli/query.ts <library_id> <query>` |

## CLI Flags

All three CLIs accept the same flag set.

| Flag | Effect |
|------|--------|
| `--json` | Emit JSON on stdout; suppress decorative output. Pipe to `jq`. |
| `--quiet`, `-q` | Suppress info/success logs (warn/error still print to stderr). |
| `--no-cache` | Skip the 24h disk cache (`~/.cache/context7/resolved.json`) for this call. |
| `--clear-cache` | Wipe the disk cache and exit. |
| `--timeout <ms>` | HTTP timeout in milliseconds. Default `30000`. |
| `--max-retries <n>` | Retry budget for `429 Rate Limit` responses (with `Retry-After`). Default `1`. |
| `--api-key <key>` | Override `CONTEXT7_API_KEY` env var. |
| `--version`, `-V` | Print version and exit. |
| `--help`, `-h` | Print usage and exit. |

## Quick Reference

### Full Lookup (Recommended)

One command to resolve library and query documentation:

```bash
# After `bun link`:
c7-lookup react "useEffect cleanup function"
c7-lookup next.js "app router middleware"
c7-lookup kubernetes "deployment rolling update"

# Or without linking:
cd ~/.claude/skills/context7/Tools && bun src/cli/lookup.ts react "useEffect cleanup function"
```

### JSON output (for scripting / piping)

```bash
c7-lookup react "useState" --json | jq '.libraryId'
c7-resolve drizzle "many to many" --json | jq '.bestMatch'
```

### Step-by-Step (when needed)

```bash
c7-resolve react                                    # → /facebook/react
c7-resolve next.js "authentication"                 # → ranked candidates
c7-query /facebook/react "useEffect cleanup"        # → docs for known ID
```

## Common Library IDs

| Library | Context7 ID | CLI Shortcut |
|---------|-------------|--------------|
| React | `/facebook/react` | `react` |
| Next.js | `/vercel/next.js` | `next.js`, `nextjs` |
| Vue | `/vuejs/vue` | `vue` |
| Kubernetes | `/kubernetes/kubernetes` | `kubernetes`, `k8s` |
| Go stdlib | `/golang/go` | `go`, `golang` |
| Python | `/python/cpython` | `python` |
| Node.js | `/nodejs/node` | `node`, `nodejs` |
| TypeScript | `/microsoft/typescript` | `typescript`, `ts` |
| Prisma | `/prisma/prisma` | `prisma` |
| Tailwind | `/tailwindlabs/tailwindcss` | `tailwind`, `tailwindcss` |

## Workflow Routing

| Workflow | Trigger | File |
|----------|---------|------|
| **ResolveLibrary** | "find library ID", "resolve library" | `Workflows/ResolveLibrary.md` |
| **QueryDocs** | "lookup docs", "get documentation", "code examples" | `Workflows/QueryDocs.md` |
| **FullLookup** | "help me with [library]", "how do I use [feature]" | `Workflows/FullLookup.md` |

## Gotchas

These are real Context7 API behaviors that bite if you don't know about them. Add to this list whenever a query goes wrong in a way that wasn't already documented.

1. **Library ID requires a leading slash.** `/facebook/react` works; `facebook/react` fails with a cryptic "library not found." The error doesn't tell you the slash is missing.
2. **The resolver is fuzzy and ranked, not deterministic.** `resolve.ts <name>` returns multiple candidates ordered by an LLM-powered ranker that takes your optional context query into account. A narrow context can promote a less-canonical fork above the official repo. Always inspect the top match before passing the ID to `query.ts`.
3. **Version pinning matters at major boundaries.** Library IDs may include a version segment: `/vercel/next.js/14.2.0`. The bare ID resolves to whatever Context7 currently treats as "latest stable," which can lag behind real releases — asking about Next.js "app router" without a pin can return Next 13 docs. Pin the version when the framework changed shape across majors.
4. **Public rate limits are tight.** Without `CONTEXT7_API_KEY`, you'll hit limits in fewer queries than you expect. The "max 3 calls per question" tip in this skill is a defensive ceiling on Claude's behavior — it is not the real API budget. Set the API key from `context7.com/dashboard` for any sustained use.
5. **Snippet truncation is silent.** Long doc pages return excerpts, not full content. If a returned example references a function or symbol the snippet didn't define, do NOT guess what it does — re-query with a tighter, more specific question rather than fabricating the missing piece.
6. **The known-IDs cache can go stale.** Common libraries (`react`, `next.js`, `kubernetes`, etc.) shortcut to hardcoded IDs in `Tools/src/lib/context7.ts` and skip the resolver entirely. If an upstream project renames its repo or moves orgs, the cached ID becomes wrong and queries silently miss. To force a fresh resolve, use an alias the cache doesn't know or pass `--no-cache`.

## Common Errors

The CLIs use typed exit codes so callers (Claude included) can distinguish failure categories without parsing strings.

| Exit | Kind | Cause | Recovery |
|------|------|-------|----------|
| `3` | `auth` | 401 — bad or missing `CONTEXT7_API_KEY` | Set the env var from `context7.com/dashboard` or pass `--api-key <key>`. |
| `4` | `not_found` | 404 — library or doc path missing; or malformed ID (missing leading `/`) | Run `c7-resolve <name>` to get a valid ID; check the `/org/project` shape. |
| `5` | `rate_limit` | 429 — public rate limit hit; auto-retries once if `Retry-After` is present | Set `CONTEXT7_API_KEY` for higher limits, or raise `--max-retries`. |
| `6` | `server` | 5xx — transient Context7 server error | Wait briefly and retry. |
| `7` | `timeout` | 408 — request aborted by client timeout | Raise `--timeout` (e.g. `--timeout 60000`) or check network. |
| `2` | (arg) | Unknown flag, bad value, missing required flag arg | Run `--help`. |
| `1` | (other) | Anything else, including `0`-status network errors | Check `stderr` message; retry. |

Errors always print `Error: <message>` and a `Hint: <remediation>` line to stderr. With `--json`, stdout stays clean and parseable; stderr keeps the human-readable error.

## Examples

### Example 1: React Hooks Documentation

```bash
cd ~/.claude/skills/context7/Tools
bun src/cli/lookup.ts react "useEffect cleanup function"
```

Output includes current React docs with cleanup pattern examples.

### Example 2: Kubernetes Deployment Spec

```bash
bun src/cli/lookup.ts kubernetes "deployment spec rolling update strategy"
```

Output includes current K8s API reference for Deployment.

### Example 3: Next.js App Router

```bash
bun src/cli/lookup.ts next.js "middleware authentication app router"
```

Output includes latest Next.js middleware documentation.

### Example 4: Using in Claude Code Session

When you need documentation during a coding session:

```
User: "How do I implement server-side data fetching in Next.js 14?"

Claude runs:
  cd ~/.claude/skills/context7/Tools && bun src/cli/lookup.ts next.js "server components data fetching"

Then synthesizes response with current patterns (Server Components, not old getServerSideProps)
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `CONTEXT7_API_KEY` | API key for higher rate limits | None (uses public rate limits) |

Get your API key at [context7.com/dashboard](https://context7.com/dashboard)

## Tips

- **Be specific** in your query for better results
- **Max 3 calls** per question - if you can't find it after 3 tries, use best available info
- **Include version** in query if you need specific version docs (e.g., "React 18 concurrent features")
- **Combine with local context** - use Context7 to verify APIs, then apply to your codebase
- **Known IDs skip API** - common libraries like `react`, `next.js` use cached IDs to skip the resolve step

## Project Structure

```
Tools/
├── package.json              # Bun + bin entries (c7-resolve, c7-query, c7-lookup)
├── tsconfig.json             # TypeScript strict config
├── src/
│   ├── index.ts              # Public exports (client, types, helpers)
│   ├── lib/
│   │   ├── context7.ts       # Core API client + retry + typed errors
│   │   ├── cache.ts          # Disk cache for resolved library IDs (24h TTL)
│   │   ├── flags.ts          # Shared CLI argument parser
│   │   └── errors.ts         # Error → exit-code + hint formatter
│   └── cli/
│       ├── lookup.ts         # Full lookup command (c7-lookup)
│       ├── resolve.ts        # Library ID resolver (c7-resolve)
│       └── query.ts          # Documentation query (c7-query)
└── tests/
    ├── cache.test.ts         # Cache I/O + TTL roundtrips
    ├── flags.test.ts         # Argument parsing edge cases
    └── errors.test.ts        # Exit code + hint mapping
```

## API Reference

The TypeScript client can also be imported programmatically:

```typescript
import {
  Context7Client,
  getKnownLibraryId,
  setLogLevel,
  formatError,
  getCached,
  setCached,
} from "./src/index.js";

setLogLevel("warn"); // silence info/success logs

const client = new Context7Client({
  apiKey: process.env.CONTEXT7_API_KEY,
  timeout: 30_000,
  maxRetries: 2,
});

// Full lookup with disk cache
const cached = await getCached("react", 24 * 60 * 60 * 1000);
if (cached) {
  const docs = await client.queryDocs(cached, "useEffect cleanup");
  console.log(docs.rawContent);
} else {
  const result = await client.lookup("react", "useEffect hooks");
  if (result.library) await setCached("react", result.library.id);
  console.log(result.rawContent);
}
```
