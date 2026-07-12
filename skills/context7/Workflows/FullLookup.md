# FullLookup Workflow

> **Trigger:** "help me with [library]", "how do I use [feature] in [library]", "show me [library] docs"

## Purpose

Complete end-to-end documentation lookup: resolve library ID and query documentation in one command.

## When to Use

- User asks about a specific library feature
- Need to verify API usage before writing code
- Looking for current best practices or code examples

## Command

```bash
c7-lookup <library> "<query>"
```

## Steps

### Step 1: Identify Library and Query

From user request, extract:
- **Library name**: What library/framework they're asking about
- **Specific query**: What aspect/feature they need help with

### Step 2: Run Full Lookup

```bash
c7-lookup <library> "<specific feature/topic>"
```

### Step 3: Synthesize Response

Combine Context7 results with:
- User's specific context/codebase
- Any constraints they mentioned
- Best practices for their use case

## Complete Example

```
User: "How do I implement server-side rendering with data fetching in Next.js 14?"

Step 1: Extract
  - Library: "next.js"
  - Query: "server-side rendering data fetching app router"

Step 2: Run Command
  c7-lookup next.js "server components data fetching app router"

Step 3: Synthesize
  -> Provide user with current Next.js 14 patterns for SSR data fetching,
     including Server Components approach (not old getServerSideProps)
```

## Common Library Mappings

| User Says | Library Name |
|-----------|--------------|
| "React", "react hooks" | `react` |
| "Next", "Next.js", "nextjs" | `next.js` |
| "Vue", "Vue 3" | `vue` |
| "K8s", "Kubernetes" | `kubernetes` |
| "Go", "Golang" | `go` |
| "Node", "Node.js" | `node` |
| "TS", "TypeScript" | `typescript` |
| "Python" | `python` |
| "Tailwind", "TailwindCSS" | `tailwind` |
| "Prisma" | `prisma` |

## More Examples

### React Hooks

```bash
c7-lookup react "useCallback useMemo when to use"
```

### Kubernetes Resources

```bash
c7-lookup kubernetes "ingress nginx annotations"
```

### Prisma Relations

```bash
c7-lookup prisma "many-to-many relations"
```

## Failure Handling

If lookup returns insufficient results:
1. Try broader query terms
2. Try more specific query terms
3. Use step-by-step workflow (resolve then query separately)
4. Inform user and proceed with general knowledge after 3 attempts

## Common Errors

| Exit | Meaning | Recovery |
|------|---------|----------|
| `3` | Bad/missing `CONTEXT7_API_KEY` | Set env var or pass `--api-key <key>` |
| `4` | Library not found at resolve step | Check spelling; try a different name; consult Common Library Mappings |
| `5` | Rate limited (429) | Set `CONTEXT7_API_KEY` or raise `--max-retries` |
| `7` | Timed out | Raise `--timeout <ms>` (e.g. `--timeout 60000`) |

Without `bun link`, prefix any command with `cd ~/.claude/skills/context7/Tools && bun src/cli/lookup.ts ...`
