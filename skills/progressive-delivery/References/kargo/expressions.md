# Kargo Expressions Reference

Complete reference for Kargo's expression language based on expr-lang.

## Syntax

All expressions use the `${{ }}` delimiter:

```yaml
config:
  message: ${{ "Hello, world!" }}
  tag: ${{ imageFrom(vars.imageRepo).Tag }}
```

## Pre-defined Variables

### Promotion Context (`ctx`)

| Variable | Type | Description |
|----------|------|-------------|
| `ctx.project` | string | Project name |
| `ctx.stage` | string | Stage name |
| `ctx.promotion` | string | Promotion name |
| `ctx.targetFreight` | object | Target freight object |
| `ctx.targetFreight.name` | string | Freight name/hash |
| `ctx.targetFreight.displayID` | string | Human-readable freight ID |
| `ctx.meta` | object | Promotion metadata |

### Step Outputs (`outputs`)

Access output from previous steps by alias:

```yaml
${{ outputs['step-alias'].fieldName }}
${{ outputs.push.commit }}
${{ outputs['open-pr'].pr.id }}
```

### User Variables (`vars`)

Access variables defined at Stage or PromotionTemplate level:

```yaml
${{ vars.gitRepo }}
${{ vars.targetBranch }}
${{ vars.imageRepo }}
```

### Task Context (`task`)

Access outputs from previous steps within the same PromotionTask:

```yaml
${{ task.previousStep.output }}
```

## Built-in Functions

### Artifact Functions

#### commitFrom

Get Git commit information from freight.

```yaml
# Basic usage
${{ commitFrom("https://github.com/example/repo.git").ID }}
${{ commitFrom("https://github.com/example/repo.git").Branch }}
${{ commitFrom("https://github.com/example/repo.git").Message }}
${{ commitFrom("https://github.com/example/repo.git").Author }}
${{ commitFrom("https://github.com/example/repo.git").Committer }}
${{ commitFrom("https://github.com/example/repo.git").Tag }}

# With warehouse origin
${{ commitFrom("https://github.com/example/repo.git", warehouse("my-warehouse")).ID }}
```

**Available Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `ID` | string | Commit SHA |
| `Branch` | string | Branch name |
| `Tag` | string | Tag name |
| `Message` | string | Commit message |
| `Subject` | string | First line of message |
| `Author` | string | Author identity |
| `Committer` | string | Committer identity |

#### imageFrom

Get container image information from freight.

```yaml
${{ imageFrom("public.ecr.aws/nginx/nginx").Tag }}
${{ imageFrom("public.ecr.aws/nginx/nginx").Digest }}
${{ imageFrom("public.ecr.aws/nginx/nginx").RepoURL }}
${{ imageFrom("public.ecr.aws/nginx/nginx").Annotations }}

# With warehouse origin
${{ imageFrom("public.ecr.aws/nginx/nginx", warehouse("my-warehouse")).Tag }}
```

**Available Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `Tag` | string | Image tag |
| `Digest` | string | Image digest |
| `RepoURL` | string | Repository URL |
| `Annotations` | map | OCI annotations |

#### chartFrom

Get Helm chart information from freight.

```yaml
${{ chartFrom("https://charts.example.com", "my-chart").Version }}
${{ chartFrom("https://charts.example.com", "my-chart").RepoURL }}
${{ chartFrom("https://charts.example.com", "my-chart").Name }}

# OCI charts
${{ chartFrom("oci://registry.example.com/charts", "my-chart").Version }}
```

**Available Fields:**

| Field | Type | Description |
|-------|------|-------------|
| `Version` | string | Chart version |
| `RepoURL` | string | Repository URL |
| `Name` | string | Chart name |

### Origin Functions

#### warehouse

Get warehouse freight origin for artifact lookups.

```yaml
${{ warehouse("my-warehouse") }}

# Usage with artifact functions
${{ imageFrom("ghcr.io/example/app", warehouse("my-warehouse")).Tag }}
```

### Metadata Functions

#### freightMetadata

Retrieve freight metadata.

```yaml
${{ freightMetadata("freight-id").label }}
${{ freightMetadata(ctx.targetFreight.name).annotation }}
```

#### stageMetadata

Retrieve stage metadata.

```yaml
${{ stageMetadata("dev").labels.environment }}
${{ stageMetadata(ctx.stage).annotations.owner }}
```

### Kubernetes Resources

#### configMap

Read ConfigMap data.

```yaml
${{ configMap("my-config").someKey }}
${{ configMap("my-config", "custom-namespace").data }}
```

#### secret

Read Secret data.

```yaml
${{ secret("my-secret").password }}
${{ secret("my-secret", "custom-namespace").apiKey }}
```

### Status Functions

#### success

Returns true if all preceding steps succeeded.

```yaml
if: ${{ success() }}
```

#### failure

Returns true if any preceding step failed.

```yaml
if: ${{ failure() }}
```

#### always

Always returns true (for unconditional execution).

```yaml
if: ${{ always() }}
```

#### status

Get status of a specific step by alias.

```yaml
if: ${{ status("my-step") == "Succeeded" }}
if: ${{ status("my-step") == "Errored" }}
if: ${{ status("my-step") == "Skipped" }}
```

**Status Values:**

- `Succeeded`
- `Errored`
- `Skipped`
- `Running`
- `Pending`

### Utility Functions

#### quote

Convert value to quoted string.

```yaml
${{ quote(42) }}  # "42"
${{ quote(true) }}  # "true"
```

#### unsafeQuote

Convert to string with escaped quotes (use with caution).

```yaml
${{ unsafeQuote("hello \"world\"") }}
```

#### semverDiff

Compare two semantic versions and return difference type.

```yaml
${{ semverDiff("1.2.3", "1.3.0") }}  # "Minor"
${{ semverDiff("1.2.3", "2.0.0") }}  # "Major"
${{ semverDiff("1.2.3", "1.2.4") }}  # "Patch"
${{ semverDiff("1.2.3", "1.2.3") }}  # "None"
```

**Return Values:**

- `Major` - Major version changed
- `Minor` - Minor version changed
- `Patch` - Patch version changed
- `Metadata` - Only metadata/prerelease changed
- `None` - Versions are identical
- `Incomparable` - Versions cannot be compared

## Expression Operators

### Comparison Operators

```yaml
${{ vars.value == "expected" }}
${{ vars.count != 0 }}
${{ vars.count > 5 }}
${{ vars.count >= 10 }}
${{ vars.count < 100 }}
${{ vars.count <= 50 }}
```

### Logical Operators

```yaml
${{ vars.enabled && vars.ready }}
${{ vars.dev || vars.test }}
${{ !vars.disabled }}
```

### String Operations

```yaml
${{ vars.name + "-suffix" }}
${{ vars.message contains "error" }}
${{ vars.name startsWith "prod" }}
${{ vars.name endsWith "-v1" }}
${{ vars.name matches "^prod-.*" }}
```

### Ternary Operator

```yaml
${{ vars.prod ? "production" : "development" }}
```

### Nil Coalescing

```yaml
${{ vars.optional ?? "default" }}
```

## Complex Expressions

### Conditional Logic

```yaml
# Major version check
if: ${{ semverDiff(imageFrom(vars.imageRepo).Tag, outputs['read-version'].current) == 'Major' }}

# Combined conditions
if: ${{ success() && outputs['test'].passed == true }}

# Null-safe access
message: ${{ outputs['step']?.value ?? "default" }}
```

### String Interpolation

```yaml
message: "Updated ${{ ctx.stage }} to image ${{ imageFrom(vars.imageRepo).Tag }}"

body: |
  {
    "project": "${{ ctx.project }}",
    "stage": "${{ ctx.stage }}",
    "version": "${{ imageFrom(vars.imageRepo).Tag }}"
  }
```

### JSON Construction

```yaml
body: ${{ quote({
  "channel": vars.slackChannel,
  "text": "Deployed " + ctx.freight.displayID + " to " + ctx.stage
}) }}
```

## Warehouse Expression Filters

### Git Commit Filters

Available fields for `expressionFilter`:

- `id` - Commit SHA
- `commitDate` - Commit timestamp
- `author` - Author identity
- `committer` - Committer identity
- `subject` - First line of commit message

```yaml
# Exclude bot commits
expressionFilter: !(author contains '<bot@example.com>')

# Filter by message pattern
expressionFilter: subject contains 'feat:' || subject contains 'fix:'

# Multiple conditions
expressionFilter: !(subject contains '[skip-ci]') && author != 'dependabot'
```

### Git Tag Filters

Additional fields for tag-based selection:

- `tag` - Tag name
- `creatorDate` - Tag creation date
- `tagger` - Tagger identity
- `annotation` - Tag annotation message

```yaml
# Filter by creation date
expressionFilter: creatorDate.Year() >= 2024

# Filter by tag pattern
expressionFilter: tag matches '^v[0-9]+\\.[0-9]+\\.[0-9]+$'
```

## HTTP Response Expressions

For `http` step success/failure conditions:

```yaml
successExpression: response.status >= 200 && response.status < 300
failureExpression: response.status >= 500

# Body checks (JSON)
successExpression: response.body.status == "success"
failureExpression: response.body.error != nil

# Header checks
successExpression: response.header("X-Request-Id") != ""
```

**Note:** Success/failure expressions should NOT be wrapped in `${{ }}`.

## Variable Scoping

### Priority Order (highest to lowest)

1. Step-level variables
2. PromotionTask variables
3. PromotionTemplate variables
4. Stage variables

### Example

```yaml
# Stage
spec:
  vars:
    - name: repo
      value: https://github.com/example/repo.git
    - name: branch
      value: main

# PromotionTemplate (overrides stage vars)
spec:
  vars:
    - name: branch
      value: develop  # Overrides stage value

# Step (can reference both)
steps:
  - uses: git-clone
    config:
      repoURL: ${{ vars.repo }}     # From stage
      branch: ${{ vars.branch }}    # From template (overridden)
```

## Type Handling

```yaml
# Numeric
numField: ${{ 40 + 2 }}  # 42

# String
strField: ${{ quote(40 + 2) }}  # "42"

# Boolean
enabled: ${{ vars.prod == true }}

# Array access
first: ${{ ctx.freight.images[0].tag }}

# Map access
value: ${{ ctx.freight.commits["repo-url"].ID }}
```

## Best Practices

1. **Use `quote()` for JSON strings** - Ensures proper escaping
2. **Validate expressions in expr-lang playground** - Test complex expressions before deployment
3. **Use descriptive variable names** - Improves readability
4. **Handle nil values** - Use `??` operator for optional values
5. **Keep expressions simple** - Break complex logic into multiple steps
