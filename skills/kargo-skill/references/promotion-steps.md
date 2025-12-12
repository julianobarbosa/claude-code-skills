# Kargo Promotion Steps Reference

Complete reference for all 34 Kargo promotion steps.

## Git Operations

### git-clone

Clones a remote Git repository and checks out specified revisions.

```yaml
- uses: git-clone
  as: clone
  config:
    repoURL: https://github.com/example/repo.git
    insecureSkipTLSVerify: false
    author:
      - name: "Kargo Bot"
        email: "kargo@example.com"
        signingKey: "..."  # Optional GPG key
    checkout:
      - as: freight
        commit: ${{ commitFrom(vars.repo).ID }}
        path: /workspace/source
      - as: stage-config
        branch: ${{ vars.targetBranch }}
        path: /workspace/target
        create: true  # Create orphaned branch if missing
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `repoURL` | string | Yes | Remote repository URL |
| `insecureSkipTLSVerify` | boolean | No | Skip TLS verification |
| `author` | object[] | No | Default commit authorship |
| `checkout` | object[] | Yes | Revisions to check out |
| `checkout[].as` | string | No | Output map key |
| `checkout[].branch` | string | No | Branch name |
| `checkout[].commit` | string | No | Specific commit hash |
| `checkout[].tag` | string | No | Git tag |
| `checkout[].path` | string | Yes | Working tree path |
| `checkout[].create` | boolean | No | Create branch if missing |

**Output:** `commits` map containing checkout keys mapped to HEAD commit hashes.

### git-commit

Commits working tree changes to the checked out branch.

```yaml
- uses: git-commit
  as: commit
  config:
    path: ./out
    message: |
      Update image to ${{ imageFrom(vars.imageRepo).Tag }}

      Freight: ${{ ctx.freight.displayID }}
    author:
      name: "Kargo Automation"
      email: "kargo@example.com"
      signingKey: "..."
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `path` | string | Yes | Git working tree location |
| `message` | string | Yes | Commit message |
| `author.name` | string | No | Committer name |
| `author.email` | string | No | Committer email |
| `author.signingKey` | string | No | GPG signing key |

**Output:** `commit` - SHA of created commit (or existing HEAD if no changes).

### git-push

Pushes committed changes to remote repository.

```yaml
- uses: git-push
  as: push
  config:
    path: ./out
    targetBranch: ${{ vars.targetBranch }}
    maxAttempts: 50
    # OR for PR workflow:
    generateTargetBranch: true
    provider: github  # azure, bitbucket, gitea, github, gitlab
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `path` | string | Yes | Git working tree location |
| `targetBranch` | string | No | Remote branch destination |
| `generateTargetBranch` | boolean | No | Auto-generate branch name |
| `maxAttempts` | int32 | No | Push retry attempts (default: 50) |
| `provider` | string | No | Git provider type |

**Output:**

- `branch` - Remote branch name
- `commit` - Commit SHA pushed
- `commitURL` - URL to pushed commit

### git-open-pr

Opens a pull request.

```yaml
- uses: git-open-pr
  as: open-pr
  config:
    repoURL: https://github.com/example/repo.git
    provider: github
    sourceBranch: ${{ outputs['push'].branch }}
    targetBranch: main
    createTargetBranch: false
    title: "Promote to ${{ ctx.stage }}"
    description: "Auto-generated promotion PR"
    labels:
      - kargo
      - automated
```

**Output:**

- `pr.id` - PR number
- `pr.url` - PR URL

### git-wait-for-pr

Waits for a PR to be merged or closed.

```yaml
- uses: git-wait-for-pr
  config:
    repoURL: https://github.com/example/repo.git
    prNumber: ${{ outputs['open-pr'].pr.id }}
    provider: github
    timeout: 48h
```

**Output:** `commit` - Merge commit SHA

### git-merge-pr

Merges an open pull request.

```yaml
- uses: git-merge-pr
  config:
    repoURL: https://github.com/example/repo.git
    prNumber: ${{ outputs['open-pr'].pr.id }}
    provider: github
    wait: true  # Retry if not mergeable
```

### git-clear

Deletes entire contents of Git working tree.

```yaml
- uses: git-clear
  config:
    path: ./out
```

## Configuration Management

### kustomize-set-image

Updates container image references in kustomization.yaml.

```yaml
- uses: kustomize-set-image
  config:
    path: ./out/overlays/test
    images:
    - image: ghcr.io/example/app
      tag: ${{ imageFrom(vars.imageRepo).Tag }}
    - image: ghcr.io/example/other
      newName: registry.example.com/other
      digest: ${{ imageFrom('ghcr.io/example/other').Digest }}
```

**Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `path` | string | Yes | Directory with kustomization.yaml |
| `images[].image` | string | Yes | Container image name |
| `images[].tag` | string | No | Image tag |
| `images[].digest` | string | No | Image digest |
| `images[].newName` | string | No | Replacement image name |

**Output:** `commitMessage` - Description of changes

### kustomize-build

Renders manifests from kustomization.yaml.

```yaml
- uses: kustomize-build
  config:
    path: ./src/overlays/test
    outPath: ./out/manifests.yaml
    plugin.helm.kubeVersion: "1.28.0"
    plugin.helm.apiVersions:
      - apps/v1
```

### helm-template

Renders Helm charts.

```yaml
- uses: helm-template
  config:
    path: ./charts/my-chart
    outPath: ./out/manifests.yaml
    releaseName: my-release
    namespace: default
    outLayout: helm  # or 'flat'
    valuesFiles:
      - ./values-prod.yaml
    buildDependencies: true
    includeCRDs: true
    disableHooks: false
    skipTests: false
    kubeVersion: "1.28.0"
    apiVersions:
      - apps/v1
    setValues:
      - key: image.tag
        value: ${{ imageFrom(vars.imageRepo).Tag }}
```

### helm-update-chart

Updates Helm chart dependencies in Chart.yaml.

```yaml
- uses: helm-update-chart
  config:
    path: ./src/my-chart
    charts:
      - repository: https://charts.example.com
        name: dependency-chart
        version: 2.0.0
      - repository: oci://registry.example.com
        name: oci-dependency
        version: 1.5.0
```

**Output:** `commitMessage`

### yaml-update

Updates YAML file values.

```yaml
- uses: yaml-update
  config:
    path: ./src/values.yaml
    updates:
      - key: image.tag
        value: ${{ imageFrom(vars.imageRepo).Tag }}
      - key: replicas
        value: "3"
      - key: config.nested.value
        value: updated-value
```

**Output:** `commitMessage`

### yaml-parse

Extracts values from YAML files.

```yaml
- uses: yaml-parse
  as: get-version
  config:
    filePath: ./src/source.yaml
    expression: version
```

**Output:** `value` - Extracted value

### json-update

Updates JSON file values.

```yaml
- uses: json-update
  config:
    path: ./src/config.json
    updates:
      - key: version
        value: ${{ imageFrom(vars.imageRepo).Tag }}
      - key: enabled
        value: true
```

### json-parse

Extracts values from JSON files.

```yaml
- uses: json-parse
  as: get-config
  config:
    filePath: ./src/config.json
    expression: settings.version
```

## ArgoCD Integration

### argocd-update

Updates ArgoCD Application resources.

```yaml
- uses: argocd-update
  config:
    apps:
    - name: my-app
      namespace: argocd
      sources:
      - repoURL: https://github.com/example/repo.git
        desiredRevision: ${{ outputs.push.commit }}
        updateTargetRevision: true
      - repoURL: ghcr.io/example/app
        tag: v1.2.3
        newName: registry.example.com/app
        updateTargetRevision: true
      # Helm parameters
      - repoURL: https://github.com/example/repo.git
        helm:
          parameters:
          - key: image.tag
            value: v1.2.3
        updateTargetRevision: true
```

**Kustomize Images:**

```yaml
sources:
- repoURL: ghcr.io/example/app
  tag: v1.2.3
  newName: registry.example.com/app
```

**Helm Parameters:**

```yaml
sources:
- repoURL: https://github.com/example/repo.git
  helm:
    parameters:
    - key: image.tag
      value: v1.2.3
```

**Required Application Annotation:**

```yaml
annotations:
  kargo.akuity.io/authorized-stage: "project:stage"
```

## File Operations

### copy

Copies files or directories.

```yaml
- uses: copy
  config:
    inPath: ./overlay/kustomization.yaml
    outPath: ./src/kustomization.yaml
```

### delete

Removes files or directories.

```yaml
- uses: delete
  config:
    path: ./temp
```

### untar

Extracts tar/gzipped archives.

```yaml
- uses: untar
  config:
    inPath: ./archive.tar.gz
    outPath: ./extracted
```

## External Integrations

### http

Makes HTTP/S requests.

```yaml
- uses: http
  config:
    method: POST
    url: https://api.example.com/deploy
    headers:
      - name: Authorization
        value: "Bearer ${{ secrets.apiToken }}"
      - name: Content-Type
        value: application/json
    queryParams:
      - name: stage
        value: ${{ ctx.stage }}
    body: '{"version":"${{ ctx.freight.displayID }}"}'
    timeout: 5m
    successExpression: response.status >= 200 && response.status < 300
    failureExpression: response.status >= 500
```

**Response Object (in expressions):**

- `response.status` - HTTP status code
- `response.headers` - Header map
- `response.header("name")` - Header accessor
- `response.body` - Unmarshaled JSON

### http-download

Downloads files from HTTP/S URLs.

```yaml
- uses: http-download
  config:
    url: https://example.com/file.tar.gz
    outPath: ./downloads/file.tar.gz
    headers:
      - name: Authorization
        value: "Bearer ${{ secrets.token }}"
```

### oci-download

Downloads OCI artifacts.

```yaml
- uses: oci-download
  config:
    repoURL: ghcr.io/example/artifact
    tag: latest
    outPath: ./artifacts
```

### gha-dispatch-workflow

Dispatches GitHub Actions workflows.

```yaml
- uses: gha-dispatch-workflow
  as: dispatch
  config:
    repoURL: https://github.com/example/repo
    workflowFileName: deploy.yaml
    ref: main
    inputs:
      environment: production
      version: ${{ imageFrom(vars.imageRepo).Tag }}
```

### gha-wait-for-workflow

Waits for GitHub Actions workflow completion.

```yaml
- uses: gha-wait-for-workflow
  config:
    repoURL: https://github.com/example/repo
    runID: ${{ outputs['dispatch'].runID }}
    timeout: 30m
```

### jira

Manages Jira issues.

```yaml
- uses: jira
  config:
    url: https://example.atlassian.net
    projectKey: DEPLOY
    issueType: Task
    summary: "Deployment to ${{ ctx.stage }}"
    description: "Deploying ${{ ctx.freight.displayID }}"
```

### send-message

Sends notifications to Slack, email, etc.

```yaml
- uses: send-message
  config:
    channel: slack-notifications
    message: |
      Deployed ${{ ctx.freight.displayID }} to ${{ ctx.stage }}
```

## Workflow Utilities

### compose-output

Combines outputs from multiple steps.

```yaml
- uses: compose-output
  config:
    pr_url: "${{ vars.repoURL }}/pull/${{ outputs['open-pr'].pr.id }}"
    commit_sha: "${{ outputs['commit'].commit }}"
    summary: "Deployed ${{ ctx.freight.displayID }}"
```

### set-metadata

Updates Stage or Freight resource metadata.

```yaml
- uses: set-metadata
  config:
    stage:
      labels:
        last-promoted: ${{ ctx.freight.displayID }}
    freight:
      annotations:
        deployed-at: ${{ now() }}
```

## Conditional Execution & Error Handling

### Conditional Steps

```yaml
steps:
  - uses: some-step
    as: my-step

  - uses: another-step
    if: ${{ success() }}  # Only if all previous succeeded

  - uses: error-handler
    if: ${{ failure() }}  # Only if any previous failed

  - uses: cleanup
    if: ${{ always() }}   # Always execute

  - uses: conditional
    if: ${{ status('my-step') == 'Errored' }}
```

### Error Handling

```yaml
steps:
  - uses: git-wait-for-pr
    continueOnError: true
    retry:
      errorThreshold: 3
      timeout: 48h
```

## Step Aliasing & Output References

```yaml
steps:
  - uses: git-clone
    as: clone
    config:
      repoURL: ${{ vars.repo }}

  - uses: git-commit
    as: commit
    config:
      path: ./out
      message: "Update"

  - uses: git-push
    as: push
    config:
      path: ./out

  - uses: argocd-update
    config:
      apps:
      - name: my-app
        sources:
        - repoURL: ${{ vars.repo }}
          desiredRevision: ${{ outputs.push.commit }}
```
