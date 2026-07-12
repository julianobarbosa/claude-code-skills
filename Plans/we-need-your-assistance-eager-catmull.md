# Plan — `.pre-commit-config.yaml` for `claude-code-skills`

## Context

This repo (`claude-code-skills`) hosts 129 skill directories under `skills/`, each with `SKILL.md` (YAML frontmatter + markdown), plus mixed `scripts/` (~25 Python, ~20 shell), `references/` (markdown), `templates/` (YAML), and a few `Workflows/` and `samples/`. Today there is no pre-commit configuration — quality is enforced by convention only ("test scripts thoroughly before commit"). Recent commit history shows ten consecutive `feat(skills):` style messages with sign-off, so contributors already follow Conventional Commits manually.

**Goal:** add a `.pre-commit-config.yaml` at the repo root that catches the bugs this codebase actually produces (broken YAML in templates, malformed `SKILL.md` frontmatter, dirty shell scripts, leaked secrets, non-conventional commit messages), without slowing contributors with rules that don't fit the repo (e.g. type-checking, full Python project linting on inline PEP-723 scripts).

**Outcome:** `git commit` runs the suite locally; CI can run the same suite via `pre-commit run --all-files`; bad commits get blocked at author time, not in review.

## Recommended Approach

Use the upstream [`pre-commit`](https://pre-commit.com) framework. Pin every external repo to a specific tag (no `HEAD`). Mix four categories of hooks:

1. **Generic file hygiene** — `pre-commit-hooks` (whitespace, EOF, large files, JSON/YAML/TOML syntax, merge markers, private keys).
2. **Language-specific linters** — `yamllint`, `markdownlint`, `shellcheck`, `shfmt`, `ruff`.
3. **Repo-specific guardrails** — local hooks that validate `SKILL.md` frontmatter (required fields, name = directory) and reject tabs in YAML.
4. **Commit metadata** — `gitleaks` (secret scan) and `conventional-pre-commit` (commit-msg gate).

Skills under `skills/*/templates/` often contain intentional `${VAR}` placeholders and partial YAML/JSON; those paths get excluded surgically rather than disabling whole hooks.

## Files to Create

| Path | Purpose |
|------|---------|
| `.pre-commit-config.yaml` | The full config below |
| `.yamllint.yaml` | yamllint rules (avoids inline `args:` blowout) |
| `.markdownlint.json` | markdownlint rules |
| `scripts/validate-skill-frontmatter.py` | Local hook: every `skills/*/SKILL.md` has `name` + `description` |
| `scripts/check-skill-name-matches-dir.py` | Local hook: `name:` in frontmatter equals parent directory |
| `docs/pre-commit.md` | Short contributor guide (install, run, CI usage) |

No `.gitignore` changes required.

---

## 1. `.pre-commit-config.yaml` (complete content)

```yaml
# Pre-commit configuration for claude-code-skills.
# Install hooks once with: pre-commit install --install-hooks
# Run on demand with:      pre-commit run --all-files
# Update tag pins with:    pre-commit autoupdate

minimum_pre_commit_version: "3.5.0"

default_install_hook_types:
  - pre-commit
  - commit-msg

default_stages: [pre-commit]

# Heavy or rarely-needed hooks live behind explicit stages so the local
# `pre-commit` run stays fast; CI runs them via `pre-commit run --hook-stage manual`.
fail_fast: false

exclude: |
  (?x)^(
      autoresearch-results\.tsv|
      LICENSE|
      .*\.min\.(js|css)|
      .*\.lock|
      .*\.svg
  )$

repos:
  # ────────────────────────────────────────────────────────────────
  # 1. Generic file hygiene
  # ────────────────────────────────────────────────────────────────
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
        args: [--markdown-linebreak-ext=md]
      - id: end-of-file-fixer
      - id: check-merge-conflict
      - id: check-case-conflict
      - id: check-symlinks
      - id: destroyed-symlinks
      - id: mixed-line-ending
        args: [--fix=lf]
      - id: check-added-large-files
        args: [--maxkb=1024]
      - id: check-executables-have-shebangs
      - id: check-shebang-scripts-are-executable
      - id: detect-private-key
      - id: check-json
        # Skill templates frequently include illustrative-but-invalid JSON.
        exclude: '^skills/.*/templates/.*\.json$'
      - id: check-toml
      - id: check-yaml
        # `--allow-multiple-documents` covers Kubernetes manifests bundled
        # in many skills (knative, argocd, gitops, etc.).
        args: [--allow-multiple-documents, --unsafe]
        exclude: '^skills/.*/(templates|samples|workflows)/.*\.ya?ml$'

  # ────────────────────────────────────────────────────────────────
  # 2. YAML lint (style + structural)
  # ────────────────────────────────────────────────────────────────
  - repo: https://github.com/adrienverge/yamllint
    rev: v1.35.1
    hooks:
      - id: yamllint
        args: [-c, .yamllint.yaml, --strict]
        # yamllint already reads the config file; templates are exempt
        # because they contain intentional `${VARS}` and partial docs.
        exclude: '^skills/.*/(templates|samples)/.*\.ya?ml$'

  # ────────────────────────────────────────────────────────────────
  # 3. Markdown lint
  # ────────────────────────────────────────────────────────────────
  - repo: https://github.com/igorshubovych/markdownlint-cli
    rev: v0.43.0
    hooks:
      - id: markdownlint
        args: [--config, .markdownlint.json, --ignore, autoresearch-results.tsv]
        exclude: '^(LICENSE|.*\.tsv)$'

  # ────────────────────────────────────────────────────────────────
  # 4. Shell scripts — lint then format
  # ────────────────────────────────────────────────────────────────
  - repo: https://github.com/koalaman/shellcheck-precommit
    rev: v0.10.0
    hooks:
      - id: shellcheck
        # `-x` follows sourced files; `SC1091` would fire on every
        # `source $HOME/.config/...` we cannot resolve at lint time.
        args: [-x, -e, SC1091, -e, SC2155]

  - repo: https://github.com/scop/pre-commit-shfmt
    rev: v3.10.0-1
    hooks:
      - id: shfmt
        # 2-space indent, indent switch cases, simplify, redirect-operators
        # padded — matches the style the existing scripts already use.
        args: [-i, "2", -ci, -sr, -s, -w]

  # ────────────────────────────────────────────────────────────────
  # 5. Python — ruff handles lint + format (replaces flake8/black/isort)
  # ────────────────────────────────────────────────────────────────
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.8.4
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format

  # ────────────────────────────────────────────────────────────────
  # 6. Secret scanning
  # ────────────────────────────────────────────────────────────────
  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.21.2
    hooks:
      - id: gitleaks

  # ────────────────────────────────────────────────────────────────
  # 7. Conventional Commits (commit-msg stage)
  # ────────────────────────────────────────────────────────────────
  - repo: https://github.com/compilerla/conventional-pre-commit
    rev: v3.6.0
    hooks:
      - id: conventional-pre-commit
        stages: [commit-msg]
        args:
          - feat
          - fix
          - docs
          - style
          - refactor
          - perf
          - test
          - build
          - ci
          - chore
          - revert

  # ────────────────────────────────────────────────────────────────
  # 8. Local repo-specific hooks
  # ────────────────────────────────────────────────────────────────
  - repo: local
    hooks:
      - id: skill-md-frontmatter
        name: SKILL.md has required frontmatter (name, description)
        entry: scripts/validate-skill-frontmatter.py
        language: python
        files: '^skills/[^/]+/SKILL\.md$'
        pass_filenames: true

      - id: skill-name-matches-dir
        name: SKILL.md `name:` matches its directory
        entry: scripts/check-skill-name-matches-dir.py
        language: python
        files: '^skills/[^/]+/SKILL\.md$'
        pass_filenames: true

      - id: no-tabs-in-yaml
        name: No tabs in YAML files
        entry: '\t'
        language: pygrep
        types: [yaml]

      - id: no-bom
        name: No UTF-8 BOM at file start
        entry: '^\xEF\xBB\xBF'
        language: pygrep
        types: [text]
```

---

## 2. `.yamllint.yaml`

```yaml
extends: default

rules:
  line-length:
    max: 200
    level: warning
  document-start: disable
  truthy:
    check-keys: false  # Allows GitHub Actions' `on:` key
  comments:
    min-spaces-from-content: 1
  indentation:
    spaces: 2
    indent-sequences: consistent
  braces:
    max-spaces-inside: 1
  brackets:
    max-spaces-inside: 1

ignore: |
  skills/*/templates/
  skills/*/samples/
  skills/*/workflows/
```

---

## 3. `.markdownlint.json`

```json
{
  "default": true,
  "MD013": false,
  "MD024": { "siblings_only": true },
  "MD033": false,
  "MD034": false,
  "MD036": false,
  "MD041": false,
  "MD046": { "style": "fenced" }
}
```

---

## 4. `scripts/validate-skill-frontmatter.py`

PEP-723 inline-deps, stdlib only — matches the `network-calc.py` pattern already used in this repo.

```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Fail commit if any skills/*/SKILL.md lacks required frontmatter."""
from __future__ import annotations

import re
import sys
from pathlib import Path

REQUIRED = ("name", "description")
FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def check(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    m = FRONTMATTER_RE.match(text)
    if not m:
        return [f"{path}: missing YAML frontmatter (--- ... ---)"]
    block = m.group(1)
    keys = {line.split(":", 1)[0].strip() for line in block.splitlines() if ":" in line}
    missing = [k for k in REQUIRED if k not in keys]
    return [f"{path}: missing required key '{k}'" for k in missing]


def main(argv: list[str]) -> int:
    errors: list[str] = []
    for arg in argv[1:]:
        errors.extend(check(Path(arg)))
    for e in errors:
        print(e, file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
```

---

## 5. `scripts/check-skill-name-matches-dir.py`

```python
#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Fail commit if SKILL.md `name:` does not equal its parent directory name."""
from __future__ import annotations

import re
import sys
from pathlib import Path

NAME_RE = re.compile(r"^name:\s*['\"]?([A-Za-z0-9_\-]+)['\"]?\s*$", re.MULTILINE)
FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def check(path: Path) -> str | None:
    expected = path.parent.name
    block = FRONTMATTER_RE.match(path.read_text(encoding="utf-8"))
    if not block:
        return None  # validate-skill-frontmatter handles the missing-FM case
    m = NAME_RE.search(block.group(1))
    if not m:
        return f"{path}: no `name:` field in frontmatter"
    actual = m.group(1)
    if actual != expected:
        return f"{path}: name '{actual}' != directory '{expected}'"
    return None


def main(argv: list[str]) -> int:
    errors = [e for arg in argv[1:] if (e := check(Path(arg)))]
    for e in errors:
        print(e, file=sys.stderr)
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
```

---

## 6. `docs/pre-commit.md` (short contributor guide)

```markdown
# Pre-commit Hooks

## Install (one-time)

```bash
pipx install pre-commit          # or: brew install pre-commit
pre-commit install --install-hooks
```

## Run

- On every `git commit` (automatic).
- Manually across the whole repo: `pre-commit run --all-files`.
- One hook only: `pre-commit run shellcheck --all-files`.

## CI

```yaml
- uses: actions/checkout@v4
- uses: actions/setup-python@v5
  with: { python-version: "3.12" }
- run: pip install pre-commit
- run: pre-commit run --all-files --show-diff-on-failure
```

## Updating pins

```bash
pre-commit autoupdate
```
```

---

## Verification

1. **Static checks** — install pre-commit then run on a fresh clone:
   ```bash
   pipx install pre-commit
   pre-commit install --install-hooks
   pre-commit run --all-files --show-diff-on-failure
   ```
   Expect non-zero exit on the first run (existing repo will surface real findings); fix or scope-exclude before merging.

2. **SKILL.md sanity sweep** — confirm both validators pass on the 129 existing skills:
   ```bash
   pre-commit run skill-md-frontmatter --all-files
   pre-commit run skill-name-matches-dir --all-files
   ```

3. **Conventional Commits gate** — try a malformed commit:
   ```bash
   git commit --allow-empty -m "broken message"        # expect FAIL
   git commit --allow-empty -m "chore: probe gate"     # expect PASS
   ```

4. **Secret scan** — drop a fake key into a scratch file and confirm `gitleaks` blocks it; remove before staging.

5. **CI parity** — once the repo gets a GitHub Actions workflow, copy the snippet from `docs/pre-commit.md` and confirm the same hooks fail/pass identically.

## Critical Files Referenced

- `templates/skill-template/SKILL.md` — frontmatter shape the validators enforce.
- `skills/argocd-cluster-bootstrapping-skill/references/guidance.md` — existing language-system / language-script examples that informed the local-hook style.
- `skills/devops-network-calculator-for-azure-skill/scripts/network-calc.py` — PEP-723 stdlib-only Python pattern reused for the validators.
- `scripts/install-skills.sh`, `scripts/link-skills.sh` — existing shell scripts that will get linted on first run; expect minor shfmt/shellcheck nits to fix.

## Out of Scope (intentional)

- Type-checking (mypy / pyright) — repo's Python is small inline scripts; ROI not there yet.
- Full repo formatter (prettier) — markdownlint already covers the markdown heavy hitters.
- Project-wide `pyproject.toml` — each Python script declares its own deps via PEP-723; introducing a global toml would change the existing convention without benefit.
- Editing of any existing skill content — this plan only adds quality gates; broken-but-merged content gets fixed in follow-ups, not bundled here.
