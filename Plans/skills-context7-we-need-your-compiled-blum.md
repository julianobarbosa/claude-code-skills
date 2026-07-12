# Plan — Context7 Skill: Comprehensive CLI & Skill Improvements

## Context

The `Context7` skill (renamed from `context7-skill` in the previous session) ships a working but minimal TypeScript wrapper over Context7's documentation API (v2). After auditing the full CLI and comparing against well-formed sibling skills in this repo, several real defects and capability gaps were found:

1. **Bin field is broken.** `package.json#bin` maps `c7-resolve`/`c7-query`/`c7-lookup` to `.ts` files with shebang `#!/usr/bin/env npx tsx`. Help text mentions `npx tsx`, but `scripts` run with `bun`, and `engines.bun >=1.0.0` is declared. A global `bun install -g` would produce a CLI that requires `npx tsx` on PATH — defeating the bin entry.
2. **No HTTP error categorization.** All non-2xx responses surface as a generic `API request failed: <status> <statusText>`. The user (or Claude reading the error) cannot distinguish "API key invalid" (401) from "library not found" (404) from "rate limited" (429).
3. **No 429 handling.** No `Retry-After` parsing, no exponential backoff. First failure kills the process.
4. **No structured output.** All three CLIs emit decorated text with ANSI colors and emoji. There is no `--json` escape hatch, so chaining or scripting is brittle.
5. **No real test.** `"test": "bun src/cli/lookup.ts react 'useEffect hooks'"` is a live API call posing as a test — it spends quota, fails offline, and asserts nothing.
6. **No disk cache.** `COMMON_LIBRARIES` is a 24-entry in-memory map; everything else re-resolves on every invocation. Public rate limits are tight (per skill Gotchas).
7. **Missing flags.** `--json`, `--version`, `--quiet`, `--timeout`, `--api-key`, `--no-cache`, `--clear-cache` are all absent.
8. **SKILL.md description is long** (284 words). Workflow markdown lacks a Common Errors / recovery table.

This plan addresses all of the above with bounded scope: bun-only runtime, comprehensive CLI hygiene, disk cache with TTL=24h, real tests, and tightened skill documentation.

## Locked Decisions (from clarifying Q&A)

| Decision | Choice |
|----------|--------|
| Scope | **Comprehensive** — fix bin, add all flags, error categorization, 429 backoff, disk cache, real tests, refresh docs |
| Runtime | **Bun-only** — shebangs `#!/usr/bin/env bun`, drop tsx references, bin entries stay pointing at `.ts` (Bun runs TS natively) |
| Cache | **`~/.cache/context7/resolved.json`, TTL=24h** with `--no-cache` and `--clear-cache` flags |

## File-by-File Implementation

### 1. `Tools/src/lib/context7.ts` (modify existing)

Reuse the existing `Context7Client` class. Surgical changes:

- **Add HTTP error categorization** inside `fetch<T>()` and `fetchText()` (currently lines 106–112 and 155–161). After capturing status + body, throw with a typed `kind` field:
  - 401 → `kind: "auth"` — message: "Invalid CONTEXT7_API_KEY (get one at context7.com/dashboard)"
  - 404 → `kind: "not_found"` — message: "Library or doc path not found"
  - 429 → `kind: "rate_limit"` — message: "Rate limited"; capture `Retry-After` header value into `retryAfter` field on the error
  - 5xx → `kind: "server"` — message: "Context7 server error (try again shortly)"
  - else → `kind: "other"`
- **Add 429 backoff** in both fetch methods: on `kind: "rate_limit"`, if `retryAfter` is present and `maxRetries > 0`, sleep `Retry-After` seconds then retry once. Cap retries at the caller-provided `maxRetries` (default 1).
- **Extend `Context7Options`** with `maxRetries?: number` and `cache?: { enabled: boolean; ttlMs: number }` fields.
- **Do NOT change** the public API of `resolveLibrary()`, `queryDocs()`, `lookup()`, `COMMON_LIBRARIES`, `getKnownLibraryId()`, or the `log()` helper — they are reused as-is by CLIs.

Lines to touch (approximate): 40–43 (Context7Options interface), 106–122 (fetch error path), 155–172 (fetchText error path), 260–268 (Context7Error subclass — add `kind` and `retryAfter` fields).

### 2. `Tools/src/lib/cache.ts` (NEW)

Tiny module — under 80 lines. Public surface:

```ts
export interface CachedResolve { name: string; id: string; ts: number }
export function getCachePath(): string                                    // ~/.cache/context7/resolved.json
export function readCache(): Record<string, CachedResolve>                // returns {} on missing/corrupt
export function writeCache(entries: Record<string, CachedResolve>): void
export function getCached(name: string, ttlMs: number): string | null    // null on miss or expired
export function setCached(name: string, id: string): void
export function clearCache(): void
```

- Use Bun's `Bun.file` and `Bun.write` for I/O (no extra deps needed).
- `XDG_CACHE_HOME` respected; falls back to `~/.cache/context7/`.
- Corrupt JSON is treated as empty (no throw) — cache is opportunistic.

### 3. `Tools/src/lib/flags.ts` (NEW)

Shared positional+flag parser. Avoid heavy deps (no `commander`/`yargs`) — match `repomix-skill` lightweight pattern. Public surface:

```ts
export interface ParsedArgs {
  positional: string[]
  flags: {
    help: boolean
    version: boolean
    json: boolean
    quiet: boolean
    noCache: boolean
    clearCache: boolean
    timeoutMs?: number
    maxRetries?: number
    apiKey?: string
  }
}
export function parseArgs(argv: string[]): ParsedArgs
```

Supports: `--help`/`-h`, `--version`/`-V`, `--json`, `--quiet`/`-q`, `--no-cache`, `--clear-cache`, `--timeout <ms>`, `--max-retries <n>`, `--api-key <key>`. Unknown flags fail fast with stderr message + exit 2.

### 4. `Tools/src/lib/errors.ts` (NEW)

Translate `Context7Error` (with `kind`) into a structured CLI output + exit code map:

```ts
export interface FormattedError { exitCode: number; message: string; hint?: string }
export function formatError(err: unknown): FormattedError
```

| Error kind | Exit code | User-facing hint |
|------------|-----------|------------------|
| `auth` | 3 | "Set `CONTEXT7_API_KEY` from context7.com/dashboard" |
| `not_found` | 4 | "Run `resolve` first or check the library ID format (`/org/project`)" |
| `rate_limit` | 5 | "Rate limited; retry in N seconds or set `CONTEXT7_API_KEY`" |
| `server` | 6 | "Context7 server error — try again" |
| timeout (408) | 7 | "Request timed out; raise `--timeout` or check network" |
| other | 1 | (just the message) |

### 5. `Tools/src/cli/lookup.ts` (modify)

- Shebang: `#!/usr/bin/env bun`
- Wire `parseArgs()` first; handle `--help`, `--version`, `--clear-cache` early.
- Pass parsed flags into `new Context7Client({ apiKey, timeout, maxRetries, cache })`.
- Cache lookup: if `getCached(libraryName, 24h)` hits and not `--no-cache`, skip resolve.
- On success, `setCached(libraryName, resolvedId)`.
- Output:
  - Default: current decorated text (kept for UX).
  - `--json`: `{ library, libraryId, query, rawContent, snippets, source: "cache|resolved|known" }` to stdout, NO decorations.
  - `--quiet`: suppress `log()` info/success entirely; warn+error still go to stderr.
- Error handling: wrap try/catch around `main()`; pipe through `formatError()` and use its `exitCode`.
- Drop `npx tsx` references from `printUsage()` text — show `bun src/cli/lookup.ts ...` or `c7-lookup ...`.

### 6. `Tools/src/cli/resolve.ts` (modify)

- Same shebang + flag wiring as lookup.
- `--json` emits `{ libraries: LibraryInfo[], bestMatch, source }`.
- Honor `--no-cache`/`--clear-cache`.

### 7. `Tools/src/cli/query.ts` (modify)

- Same shebang + flag wiring.
- `--json` emits `{ libraryId, query, rawContent }` (no cache involvement — queries are always fresh).

### 8. `Tools/src/index.ts` (modify, small)

- Add `export { getCachePath, readCache, getCached, setCached, clearCache, type CachedResolve } from "./lib/cache.js";`
- Add `export { parseArgs, type ParsedArgs } from "./lib/flags.js";`
- Add `export { formatError, type FormattedError } from "./lib/errors.js";`

### 9. `Tools/package.json` (modify)

- Bump version to `1.2.0`.
- Replace `"test"` script: `"test": "bun test"` (real test runner).
- Remove the demo `lookup` call masquerading as test.
- Keep `bin` entries — they will work now that shebangs are `bun`.
- Add `"prepublishOnly": "bun test"` to gate any future publish on tests passing.

### 10. `Tools/tests/cache.test.ts` (NEW)

Bun test, fully offline. Covers:
- `readCache()` returns `{}` when file missing
- `setCached()` → `getCached()` roundtrip
- `getCached()` returns `null` when TTL exceeded (mock `Date.now`)
- `clearCache()` removes file

### 11. `Tools/tests/flags.test.ts` (NEW)

Bun test, offline. Covers:
- Positional + flag interleaving (`react --json "useEffect"` and `react "useEffect" --json` both parse correctly)
- `--timeout 10000` → `timeoutMs: 10000`
- Unknown flag exits with code 2
- `--help` short-circuits

### 12. `Tools/tests/errors.test.ts` (NEW)

Bun test, offline. Covers:
- Each `Context7Error` kind maps to the expected exit code + hint
- Unknown error falls through to exit code 1

### 13. `SKILL.md` (modify)

- **Tighten description** from 284 → ~140 words. Keep all of: USE WHEN clause, NOT FOR clause, library list (shortened). Cut redundant phrasing.
- **Update Setup section**: show `bun install` + (optional) `bun link` so `c7-lookup`/`c7-resolve`/`c7-query` are on PATH globally.
- **Update CLI tools table**: include the new flags (`--json`, `--quiet`, `--no-cache`, `--timeout`, `--api-key`).
- **Quick Reference**: add a `--json` example after the regular one for each command.
- **Common Errors** section (NEW): table mapping exit code 3/4/5/6/7 to cause + remediation. Goes after Gotchas, before Examples.
- Keep Gotchas section intact (it's good).

### 14. `Workflows/ResolveLibrary.md`, `QueryDocs.md`, `FullLookup.md` (modify)

- Update commands from `cd ~/.claude/skills/context7/Tools && bun src/cli/resolve.ts ...` to also show the linked form `c7-resolve ...` for users who ran `bun link`.
- Add a **Common Errors** sub-section to each, mirroring the SKILL.md table but shortened (3 most relevant errors per workflow).

## Reused Code (do NOT rebuild)

The existing `Context7Client` class (`Tools/src/lib/context7.ts:71-255`) already encapsulates auth, timeout, JSON+text fetch paths, and the three high-level methods (`resolveLibrary`, `queryDocs`, `lookup`). This plan *extends* it, doesn't replace it. Same for `COMMON_LIBRARIES`, `getKnownLibraryId()`, `log()`, and the `Context7Error` class.

## Verification

1. **Type-check**: `cd skills/context7/Tools && bunx tsc --noEmit` — exits 0.
2. **Tests pass offline**: `bun test` — `cache.test.ts`, `flags.test.ts`, `errors.test.ts` all green; no network calls.
3. **Bin entries work** after `bun link`:
   - `c7-resolve react` returns `/facebook/react` (cached or from known-IDs map).
   - `c7-resolve --version` prints `1.2.0`.
   - `c7-resolve react --json` emits valid JSON parseable by `jq`.
4. **Error mapping** (one live probe, may be skipped if rate-limited):
   - `c7-query /nonexistent/library "test"` → exits 4, stderr shows "not_found" hint.
   - `c7-resolve --timeout 1 react` → exits 7, "timed out" hint.
5. **Cache works**:
   - First `c7-resolve some-uncommon-lib` writes to `~/.cache/context7/resolved.json`.
   - Second invocation logs `(cache hit)` and skips API call (verifiable via `--quiet=false` info log).
   - `c7-resolve --clear-cache` empties the file.
6. **Markdown integrity**: `rg -n "context7-skill" skills/context7/` returns zero hits; `rg -n "npx tsx" skills/context7/` returns zero hits (cleaned from help text and shebangs).
7. **SKILL.md description**: `wc -w` on the description line is ≤160 words (down from 284).
8. **Workflow examples**: each `Workflows/*.md` contains both the long-form `bun src/cli/...` and the short-form `c7-*` invocation.

## Out of Scope (deliberately)

- Switching to Node compatibility / `dist/` build step (locked to Bun-only).
- Replacing the in-memory `defaultClient` singleton.
- Adding a `list-libraries` command or pagination — Context7 API surface today doesn't have a clean endpoint for that.
- Color-output toggle (`--no-color`) — ANSI is already on stderr only; piping stdout is unaffected.
- Migrating to a CLI framework (commander/yargs) — current parser is fine for the flag set.
- Publishing the package — `prepublishOnly` is wired but no actual publish step.

## Execution Order

1. `lib/cache.ts` (new, leaf)
2. `lib/flags.ts` (new, leaf)
3. `lib/errors.ts` (new, depends on `Context7Error` shape — coordinate with step 4)
4. `lib/context7.ts` (modify — add `kind` to error, 429 backoff, `maxRetries`/`cache` options)
5. `tests/cache.test.ts`, `tests/flags.test.ts`, `tests/errors.test.ts` (new — run before CLI rewrites to catch type errors)
6. `cli/lookup.ts`, `cli/resolve.ts`, `cli/query.ts` (modify — shebang, flag parsing, JSON output, cache wiring)
7. `index.ts` (modify — add new exports)
8. `package.json` (bump version, fix test script)
9. `SKILL.md` (tighten description, refresh Setup, add Common Errors)
10. `Workflows/*.md` (add Common Errors sub-section, mention `c7-*` form)
11. Run `bun test`, then run verification steps 1–8 from §Verification.
