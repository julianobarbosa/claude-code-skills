---
name: pre-commit
description: Pre-commit hooks framework for multi-language code quality automation. USE WHEN setting up pre-commit OR configuring git hooks OR adding linting OR code formatting OR security scanning OR Terraform validation OR Kubernetes manifests OR Helm charts OR Python linting OR JavaScript formatting. Manages .pre-commit-config.yaml, hook installation, and CI integration.
---

# PreCommit

A comprehensive skill for managing [pre-commit](https://pre-commit.com/) hooks - the framework for multi-language pre-commit hook management that automates code quality, formatting, linting, and security scanning.

## Quick Reference

| Command | Description |
|---------|-------------|
| `pre-commit install` | Install git hooks |
| `pre-commit run --all-files` | Run all hooks on all files |
| `pre-commit autoupdate` | Update hooks to latest versions |
| `pre-commit run <hook-id>` | Run specific hook |

## Workflow Routing

| Workflow | Trigger | File |
|----------|---------|------|
| **Setup** | "setup pre-commit", "initialize hooks", "create config" | `Workflows/Setup.md` |
| **AddHooks** | "add hook", "add linting", "add formatter", "add security" | `Workflows/AddHooks.md` |
| **Troubleshoot** | "fix pre-commit", "hook failing", "debug hooks" | `Workflows/Troubleshoot.md` |
| **CIIntegration** | "CI pipeline", "GitHub Actions", "GitLab CI" | `Workflows/CIIntegration.md` |
| **CustomHook** | "create custom hook", "local hook", "write hook" | `Workflows/CustomHook.md` |

## Documentation

| Document | Purpose |
|----------|---------|
| `QuickStartGuide.md` | Installation and first-time setup |
| `HooksReference.md` | Comprehensive hook catalog by language/purpose |
| `ConfigurationGuide.md` | Advanced configuration options |
| `SecurityHooks.md` | Secret detection and security scanning |

## Tools

| Tool | Purpose |
|------|---------|
| `Tools/PreCommitManager.ts` | CLI for managing pre-commit configurations |
| `Tools/HookGenerator.ts` | Generate .pre-commit-config.yaml templates |
| `Tools/HookValidator.ts` | Validate hook configurations |

## Examples

**Example 1: Setup pre-commit for a new project**
```
User: "Setup pre-commit for my Python project"
→ Invokes Setup workflow
→ Creates .pre-commit-config.yaml with Python hooks (black, isort, flake8)
→ Runs pre-commit install
```

**Example 2: Add Terraform hooks**
```
User: "Add Terraform validation hooks"
→ Invokes AddHooks workflow
→ Adds terraform_fmt, terraform_validate, terraform_docs hooks
→ Configures tflint and checkov integration
```

**Example 3: Add security scanning**
```
User: "Add secret detection to pre-commit"
→ Invokes AddHooks workflow
→ Adds gitleaks, detect-secrets, trufflehog hooks
→ Configures appropriate exclusion patterns
```

**Example 4: Debug failing hook**
```
User: "My eslint pre-commit hook is failing"
→ Invokes Troubleshoot workflow
→ Checks hook configuration and dependencies
→ Provides fix recommendations
```

## Supported Hook Categories

- **Python**: black, isort, flake8, mypy, bandit, pyupgrade
- **JavaScript/TypeScript**: prettier, eslint, biome
- **Infrastructure**: terraform, terragrunt, helm, kustomize
- **Kubernetes**: kubeconform, kubeval, checkov
- **Security**: gitleaks, detect-secrets, trufflehog, trivy
- **General**: yamllint, jsonlint, shellcheck, markdownlint

---

## Gotchas

- **Hook output disappears when run via `git commit -m` in an editor terminal** — stdout/stderr get swallowed by the editor wrapping. Run `pre-commit run --all-files` directly to see the actual failure message.
- **`pre-commit autoupdate` bumps to latest tag but doesn't update pinned config in hook repos** — a hook that pins `flake8==6.0.0` internally keeps that version. Look at each hook's `additional_dependencies` after autoupdate.
- **Hooks only run on staged files by default**, so editing a file after `git add` and then committing runs the hook against the OLD content. Use `--all-files` in CI to catch this.
- **`exclude:` regex is anchored differently than `files:`** — `exclude: tests/` does NOT exclude `tests/foo.py` in some hook versions; use `exclude: ^tests/` to be safe. Anchor everything.
- **`language: system` hooks bypass the pre-commit venv** and rely on the user's PATH — works on your machine, fails in CI with `command not found`. Prefer `language: python` with `additional_dependencies`.
- **`pre-commit install` doesn't install for `commit-msg` or `pre-push`** by default — separate `--hook-type` calls needed. Many teams add commit-msg hooks then wonder why they don't fire.
- **Skipping a hook via `SKIP=hookid git commit` is per-shell-invocation**, not per-commit — CI runs with a fresh env where SKIP is unset and the hook fires anyway.
