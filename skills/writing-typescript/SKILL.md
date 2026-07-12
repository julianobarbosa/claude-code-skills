---
name: writing-typescript
description: Idiomatic TypeScript development. Use when writing TypeScript code, Node.js services, React apps, or discussing TS patterns. Emphasizes strict typing, composition, and modern tooling (bun/vite).
allowed-tools: Read, Bash, Grep, Glob
---

# TypeScript Development (2025)

## Core Principles

- **Strict typing**: Enable all strict checks
- **Parse, don't validate**: Transform untrusted data at boundaries
- **Composition over inheritance**: Small, focused functions
- **Explicit over implicit**: No `any`, prefer `unknown`

## Toolchain

```bash
bun          # Runtime + package manager (fast)
vite         # Frontend bundling
vitest       # Testing
eslint       # Linting
prettier     # Formatting
```

## Quick Patterns

### Type Guards

```typescript
function isUser(value: unknown): value is User {
  return typeof value === "object" && value !== null && "id" in value;
}
```

### Discriminated Unions

```typescript
type Result<T, E = Error> = { ok: true; value: T } | { ok: false; error: E };

function processResult<T>(result: Result<T>): T {
  if (result.ok) return result.value;
  throw result.error;
}
```

### Utility Types

```typescript
type UserUpdate = Partial<User>;
type UserSummary = Pick<User, "id" | "name">;
type UserWithoutPassword = Omit<User, "password">;
type ReadonlyUser = Readonly<User>;
```

## tsconfig.json Essentials

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,
    "noImplicitReturns": true,
    "isolatedModules": true
  }
}
```

## References

- [PATTERNS.md](PATTERNS.md) - Code patterns and style
- [REACT.md](REACT.md) - React component patterns
- [TESTING.md](TESTING.md) - Testing with vitest

## Commands

```bash
bun install              # Install deps
bun run build            # Build
bun test                 # Test
bun run lint             # Lint
bun run format           # Format
```

---

## Gotchas

- **`import type` with `verbatimModuleSyntax` and named exports**: type-only import of a value triggers errors. Fix: `import { type Foo } from "mod"` (inline marker).
- **`as const` on object: readonly AND literal-narrowed** — different from `as Foo` (asserts type) or `satisfies Foo` (validates without widening).
- **`satisfies` validates without widening; `as` widens** — using `as` where you wanted `satisfies` loses literal types silently.
- **`Array<T>.includes(x)` requires `x` to be of type `T`** — narrowing-from-union doesn't work; the standard fix is a type-predicate helper.
- **`strictNullChecks: false` makes `T` mean `T | null | undefined` for ALL types** — partial migrations leave types that lie about nullability.
- **`tsconfig.json` `extends` doesn't recursively merge `compilerOptions.paths`** — child paths REPLACE parent paths, not merge.
