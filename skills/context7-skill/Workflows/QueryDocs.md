# QueryDocs Workflow

> **Trigger:** "lookup docs", "get documentation", "code examples for", "how to use"

## Purpose

Query up-to-date documentation and code examples from a specific library using its Context7 library ID.

## Prerequisites

- You must have a valid Context7 library ID (from `ResolveLibrary` workflow or known ID)
- Library ID format: `/org/project` or `/org/project/version`

## Command

```bash
cd ~/.claude/skills/Context7/Tools && bun src/cli/query.ts <library_id> "<query>"
```

**Parameters:**
- `library_id` (required): Context7-compatible library ID (e.g., `/facebook/react`)
- `query` (required): Natural language question about the library

## Steps

### Step 1: Run Query Command

```bash
cd ~/.claude/skills/Context7/Tools && bun src/cli/query.ts "/org/project" "specific question"
```

### Step 2: Process Results

Results include:
- Documentation snippets relevant to your query
- Code examples from actual library documentation
- Version-specific information when available

### Step 3: Apply to Task

Use the retrieved documentation to:
- Verify API signatures before writing code
- Get current best practices
- Find working code examples to adapt

## Query Tips

| Goal | Query Example |
|------|---------------|
| API reference | "useState hook signature and return values" |
| Code example | "useEffect with cleanup function example" |
| Configuration | "webpack configuration for typescript" |
| Migration | "migrate from pages router to app router" |
| Troubleshooting | "common errors with async components" |
| Best practices | "when to use useMemo vs useCallback" |

## Examples

### React Hooks

```bash
cd ~/.claude/skills/Context7/Tools && bun src/cli/query.ts /facebook/react "useCallback hook usage and when to use it"
```

### Next.js Middleware

```bash
cd ~/.claude/skills/Context7/Tools && bun src/cli/query.ts /vercel/next.js "middleware authentication redirect"
```

### Kubernetes Deployments

```bash
cd ~/.claude/skills/Context7/Tools && bun src/cli/query.ts /kubernetes/kubernetes "deployment strategy rolling update maxSurge"
```

### TypeScript Generics

```bash
cd ~/.claude/skills/Context7/Tools && bun src/cli/query.ts /microsoft/typescript "generic constraints extends keyof"
```

### Prisma Queries

```bash
cd ~/.claude/skills/Context7/Tools && bun src/cli/query.ts /prisma/prisma "findMany with include nested relations"
```

## Common Library IDs

| Library | ID |
|---------|-----|
| React | `/facebook/react` |
| Next.js | `/vercel/next.js` |
| Vue | `/vuejs/vue` |
| Kubernetes | `/kubernetes/kubernetes` |
| Go | `/golang/go` |
| Python | `/python/cpython` |
| Node.js | `/nodejs/node` |
| TypeScript | `/microsoft/typescript` |
| Prisma | `/prisma/prisma` |
| Tailwind | `/tailwindlabs/tailwindcss` |

## Important Notes

- **Be specific** - vague queries return less useful results
- **Max 3 calls per question** - refine your query if first attempt isn't helpful
- **Don't include sensitive info** in query parameter
- Library ID must start with `/` (e.g., `/facebook/react`, not `facebook/react`)
- Use the `lookup.ts` command if you don't know the library ID
