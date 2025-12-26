# Conventional Commits Reference

A specification for adding human and machine-readable meaning to commit messages.

## Format

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

## Commit Types

| Type | Description | Semver Impact |
|------|-------------|---------------|
| `feat` | New feature | MINOR |
| `fix` | Bug fix | PATCH |
| `docs` | Documentation only | None |
| `style` | Code style (formatting, semicolons) | None |
| `refactor` | Code change that neither fixes nor adds | None |
| `perf` | Performance improvement | PATCH |
| `test` | Adding/correcting tests | None |
| `build` | Build system or dependencies | None |
| `ci` | CI configuration files | None |
| `chore` | Other changes (no src/test) | None |
| `revert` | Reverts a previous commit | Varies |

## Breaking Changes

Indicate breaking changes with:
- `!` after type/scope: `feat!: remove deprecated API`
- `BREAKING CHANGE:` in footer

```
feat(api)!: remove deprecated endpoints

BREAKING CHANGE: The /v1/users endpoint has been removed.
Use /v2/users instead.
```

## Scope Examples

Scope provides additional context:

```
feat(auth): add OAuth2 support
fix(parser): handle empty input
docs(readme): update installation steps
style(components): fix indentation
refactor(core): extract helper functions
perf(api): cache database queries
test(utils): add edge case tests
build(deps): update webpack to v5
ci(github): add automated release
chore(release): bump version to 2.0.0
```

## Good Commit Messages

### Features

```
feat(cart): add quantity selector to cart items

Allow users to change item quantity directly in the cart
without returning to the product page.

Closes #142
```

### Bug Fixes

```
fix(auth): prevent session timeout during active use

The session was expiring even when users were actively
interacting with the application. Now activity resets
the timeout timer.

Fixes #256
```

### Breaking Changes

```
feat(api)!: change authentication to JWT

BREAKING CHANGE: Bearer token authentication now uses JWT.
All existing API keys will need to be regenerated.

Migration guide: docs/migration/v3-auth.md
```

### Reverts

```
revert: feat(cart): add quantity selector

This reverts commit abc1234.

Reason: Causes performance issues on mobile devices.
Will be reimplemented with lazy loading.
```

## Bad Commit Messages (Avoid)

```
# Too vague
fix: bug fix
update: updates
feat: new feature

# Not following convention
Fixed the login bug
Added new feature
WIP
```

## Multi-Line Messages

For complex changes, use body:

```
refactor(database): migrate from MySQL to PostgreSQL

- Updated connection pooling configuration
- Converted all raw queries to use parameterized statements
- Added migration scripts in /migrations
- Updated docker-compose for local development

Performance benchmarks show 15% improvement in read operations.

Related: #301, #302, #303
```

## Footer Conventions

| Footer | Purpose |
|--------|---------|
| `Fixes #123` | Closes issue on merge |
| `Closes #123` | Closes issue on merge |
| `Refs #123` | References without closing |
| `BREAKING CHANGE:` | Describes breaking change |
| `Reviewed-by: Name` | Code review attribution |
| `Co-authored-by:` | Multiple authors |

## Automation Benefits

Conventional commits enable:

1. **Automatic changelog generation**
2. **Semantic versioning** based on commit types
3. **Filtered git history** by type
4. **CI/CD triggers** based on commit type
5. **Better code review** with clear context

## Quick Reference

```bash
# Feature
git commit -m "feat(scope): add new feature"

# Bug fix
git commit -m "fix(scope): resolve issue description"

# Documentation
git commit -m "docs(readme): update installation guide"

# Breaking change
git commit -m "feat(api)!: change endpoint structure

BREAKING CHANGE: /api/v1 is now /api/v2"

# With issue reference
git commit -m "fix(auth): resolve login timeout

Fixes #123"
```

## Resources

- [Conventional Commits Specification](https://www.conventionalcommits.org/)
- [Angular Commit Guidelines](https://github.com/angular/angular/blob/main/CONTRIBUTING.md#commit)
- [Semantic Versioning](https://semver.org/)
