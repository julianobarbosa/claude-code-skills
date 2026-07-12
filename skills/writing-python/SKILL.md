---
name: writing-python
description: Idiomatic Python 3.14+ development. Use when writing Python code, CLI tools, scripts, or services. Emphasizes stdlib, type hints, uv/ruff toolchain, and minimal dependencies.
allowed-tools: Read, Bash, Grep, Glob
---

# Python Development (3.14+)

## Core Principles

- **Stdlib first**: External deps only when justified
- **Type hints everywhere**: All functions, all parameters
- **Explicit over implicit**: Clear is better than clever
- **Fail fast**: Raise early with informative errors

## Toolchain

```bash
uv           # Package management (not pip/poetry)
ruff         # Lint + format (not flake8/black)
pytest       # Testing
mypy         # Type checking
```

## Quick Patterns

### Type Hints

```python
def process_users(users: list[User], limit: int | None = None) -> list[Result]:
    ...

async def fetch_data(url: str, timeout: float = 30.0) -> dict[str, Any]:
    ...
```

### Dataclasses

```python
from dataclasses import dataclass, field

@dataclass
class Config:
    host: str
    port: int = 8080
    tags: list[str] = field(default_factory=list)
```

### Pattern Matching

```python
match event:
    case {"type": "click", "x": x, "y": y}:
        handle_click(x, y)
    case {"type": "key", "code": code}:
        handle_key(code)
    case _:
        raise ValueError(f"Unknown event: {event}")
```

## Python 3.14 Features

- **Deferred annotations**: No more `from __future__ import annotations`
- **Template strings (t"")**: `t"Hello {name}"` returns Template object
- **except without parens**: `except ValueError, TypeError:`
- **concurrent.interpreters**: True parallelism via subinterpreters
- **compression.zstd**: Zstandard in stdlib
- **Free-threaded build**: No GIL (opt-in)

## References

- [PATTERNS.md](PATTERNS.md) - Code patterns and style
- [CLI.md](CLI.md) - CLI application patterns
- [TESTING.md](TESTING.md) - Testing with pytest

## Tooling

```bash
uv sync                    # Install deps
ruff check --fix .         # Lint and autofix
ruff format .              # Format
pytest -v                  # Test
mypy .                     # Type check
```

---

## Absorbed sub-skills (post-consolidation)

This skill now subsumes the former `python-code-style` and `python-type-safety` skills. Their original SKILL.md content is preserved as deep reference:

| Subject | Path |
|---------|------|
| ruff, mypy, naming, imports, docstrings (Google style) | `References/code-style.md` |
| Type annotations, generics, protocols, strict checking patterns | `References/type-safety.md` |

For system-reliability concerns (background jobs, retries, observability), see the sibling **`python-infrastructure`** skill. For dependency management and project scaffolding, see **`uv`**.

---

## Gotchas

- **`from __future__ import annotations` makes ALL annotations strings** — runtime introspection (`typing.get_type_hints`) needs the actual types available; forward refs to local-scope classes fail.
- **f-string debug syntax (`f"{var=}"`) is 3.8+** — quietly fails (treats `=` as literal) in 3.7 and earlier.
- **`dataclass(slots=True)` is 3.10+** — silently does nothing in 3.9. Use `__slots__` manually for portability.
- **PEP 604 union syntax (`int | None`) is 3.10+ at runtime** — works as a string annotation in 3.9 with `from __future__ import annotations`, fails at runtime introspection.
- **`async def` vs `def` for FastAPI dependencies**: async deps run in the event loop; sync deps run in a thread pool. Mixing without thought causes either blocking or extra context-switch overhead.
