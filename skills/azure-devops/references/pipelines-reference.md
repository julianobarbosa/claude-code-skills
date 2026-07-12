# Pipelines and Build API Reference

Comprehensive reference for Azure DevOps Pipelines REST API operations.

## Table of Contents

- [Pipeline Concepts](#pipeline-concepts)
- [Build Status and Results](#build-status-and-results)
- [YAML Pipeline Reference](#yaml-pipeline-reference)
- [Pipeline Variables](#pipeline-variables)
- [Triggers and Resources](#triggers-and-resources)

---

## Pipeline Concepts

### Pipeline Types

| Type | Description | Definition Location |
|------|-------------|---------------------|
| YAML Pipeline | Code-as-config pipeline | Repository (azure-pipelines.yml) |
| Classic Build | UI-defined build pipeline | Azure DevOps |
| Classic Release | UI-defined release pipeline | Azure DevOps |

### Pipeline Hierarchy

```
Pipeline Definition
    └── Stages
        └── Jobs
            └── Steps (Tasks/Scripts)
```

### Run vs Build

- **Pipeline Run**: Modern YAML pipeline execution (Pipelines API)
- **Build**: Classic build or YAML execution (Build API)

---

## Build Status and Results

### Build Status Values

| Status | Value | Description |
|--------|-------|-------------|
| None | `0` | No status |
| In Progress | `1` | Currently running |
| Completed | `2` | Finished execution |
| Cancelling | `4` | Being cancelled |
| Postponed | `8` | Execution postponed |
| Not Started | `32` | Queued but not started |
| All | `47` | All statuses |

### Build Result Values

| Result | Value | Description |
|--------|-------|-------------|
| None | `0` | No result yet |
| Succeeded | `2` | All tasks passed |
| Partially Succeeded | `4` | Some tasks failed (continue on error) |
| Failed | `8` | Build failed |
| Canceled | `32` | User or system cancelled |

### Build Reason Values

| Reason | Value | Description |
|--------|-------|-------------|
| None | `0` | No reason |
| Manual | `1` | Manual trigger |
| Individual CI | `2` | Continuous integration |
| Batch CI | `4` | Batched CI trigger |
| Schedule | `8` | Scheduled trigger |
| User Created | `32` | Created by user |
| Validate Shelveset | `64` | Shelveset validation |
| Check In Shelveset | `128` | Shelveset check-in |
| Pull Request | `256` | PR trigger |
| Build Completion | `512` | Build completion trigger |
| Resource Trigger | `1024` | Resource trigger |

---

## YAML Pipeline Reference

### Basic Structure

```yaml
# azure-pipelines.yml
trigger:
  branches:
    include:
      - main
      - release/*
    exclude:
      - feature/experimental/*
  paths:
    include:
      - src/*
    exclude:
      - docs/*

pr:
  branches:
    include:
      - main
  autoCancel: true

pool:
  vmImage: 'ubuntu-latest'

variables:
  - name: buildConfiguration
    value: 'Release'
  - group: 'production-secrets'

stages:
  - stage: Build
    displayName: 'Build Stage'
    jobs:
      - job: BuildJob
        displayName: 'Build Application'
        steps:
          - task: DotNetCoreCLI@2
            displayName: 'Build'
            inputs:
              command: 'build'
              projects: '**/*.csproj'
```

### Stage Template

```yaml
stages:
  - stage: stageName
    displayName: 'Stage Display Name'
    dependsOn: [previousStage]
    condition: succeeded()
    variables:
      stageVar: 'value'
    jobs:
      - job: jobName
        # Job definition
```

### Job Template

```yaml
jobs:
  - job: JobName
    displayName: 'Job Display Name'
    pool:
      vmImage: 'ubuntu-latest'
    timeoutInMinutes: 60
    cancelTimeoutInMinutes: 5
    dependsOn: [PreviousJob]
    condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))
    continueOnError: false
    strategy:
      matrix:
        linux:
          imageName: 'ubuntu-latest'
        windows:
          imageName: 'windows-latest'
      maxParallel: 2
    steps:
      - script: echo Hello
```

### Deployment Job

```yaml
jobs:
  - deployment: DeploymentName
    displayName: 'Deploy to Production'
    environment: 'production'
    strategy:
      runOnce:
        deploy:
          steps:
            - download: current
              artifact: drop
            - script: ./deploy.sh
```

---

## Pipeline Variables

### Predefined Variables

| Variable | Description |
|----------|-------------|
| `Build.BuildId` | Unique build ID |
| `Build.BuildNumber` | Build number/name |
| `Build.DefinitionName` | Pipeline name |
| `Build.SourceBranch` | Source branch (refs/heads/main) |
| `Build.SourceBranchName` | Branch name only (main) |
| `Build.SourceVersion` | Commit SHA |
| `Build.Repository.Name` | Repository name |
| `Build.Repository.Uri` | Repository URI |
| `Build.RequestedFor` | User who triggered |
| `Build.Reason` | Trigger reason |
| `System.TeamProject` | Project name |
| `System.DefaultWorkingDirectory` | Working directory |
| `Pipeline.Workspace` | Pipeline workspace path |
| `Agent.Name` | Agent name |
| `Agent.MachineName` | Machine name |
| `Agent.OS` | Operating system |
| `Agent.TempDirectory` | Temp directory |
| `Agent.ToolsDirectory` | Tools directory |

### Variable Syntax

```yaml
# Macro syntax (compile-time)
variables:
  myVar: 'value'
steps:
  - script: echo $(myVar)

# Template expression (compile-time)
steps:
  - script: echo ${{ variables.myVar }}

# Runtime expression
steps:
  - script: echo $[variables.myVar]

# Environment variable (Bash)
steps:
  - script: echo $MYVAR
    env:
      MYVAR: $(myVar)

# PowerShell
steps:
  - powershell: Write-Host $env:MYVAR
    env:
      MYVAR: $(myVar)
```

### Variable Groups

```yaml
variables:
  - group: 'my-variable-group'
  - name: localVar
    value: 'local value'
```

### Secret Variables

```yaml
variables:
  - name: mySecret
    value: $(secretFromLibrary)  # From variable group

steps:
  - script: |
      echo "Using secret (masked in logs)"
      curl -H "Authorization: Bearer $(mySecret)" https://api.example.com
    env:
      MY_SECRET: $(mySecret)
```

---

## Triggers and Resources

### CI Triggers

```yaml
# Branch triggers
trigger:
  batch: true  # Batch changes
  branches:
    include:
      - main
      - release/*
    exclude:
      - feature/experimental/*
  paths:
    include:
      - src/*
    exclude:
      - '**/*.md'
  tags:
    include:
      - v*
    exclude:
      - v0.*

# Disable CI trigger
trigger: none
```

### PR Triggers

```yaml
pr:
  autoCancel: true
  drafts: false
  branches:
    include:
      - main
      - release/*
  paths:
    include:
      - src/*
    exclude:
      - docs/*
```

### Scheduled Triggers

```yaml
schedules:
  - cron: '0 0 * * *'  # Daily at midnight UTC
    displayName: 'Daily Build'
    branches:
      include:
        - main
    always: false  # Only if changes
  - cron: '0 12 * * 0'  # Weekly Sunday noon
    displayName: 'Weekly Build'
    branches:
      include:
        - main
    always: true  # Always run
```

### Pipeline Resources

```yaml
resources:
  repositories:
    - repository: templates
      type: git
      name: ProjectName/TemplateRepo
      ref: refs/heads/main
    - repository: external
      type: github
      name: org/repo
      endpoint: 'GitHub Connection'

  pipelines:
    - pipeline: upstream
      source: 'Upstream-Pipeline'
      trigger:
        branches:
          include:
            - main

  containers:
    - container: build-container
      image: mcr.microsoft.com/dotnet/sdk:6.0
      options: --privileged

  packages:
    - package: myPackage
      type: npm
      connection: 'npm-connection'
      name: '@scope/package'
      version: 1.0.0
```

---

## MCP Tool Usage Examples

### List Build Definitions

```python
# Using mcp__ado__pipelines_get_build_definitions
params = {
    "project": "MyProject",
    "includeLatestBuilds": True,
    "queryOrder": "LastModifiedDescending",
    "top": 50
}
```

### Get Builds

```python
# Using mcp__ado__pipelines_get_builds
params = {
    "project": "MyProject",
    "definitions": [123, 456],  # Definition IDs
    "statusFilter": 2,  # Completed
    "resultFilter": 8,  # Failed
    "queryOrder": "FinishTimeDescending",
    "top": 20
}
```

### Run Pipeline

```python
# Using mcp__ado__pipelines_run_pipeline
params = {
    "project": "MyProject",
    "pipelineId": 123,
    "resources": {
        "repositories": {
            "self": {
                "refName": "refs/heads/feature-branch"
            }
        }
    },
    "templateParameters": {
        "environment": "staging",
        "runTests": "true"
    },
    "variables": {
        "customVar": {
            "value": "custom-value",
            "isSecret": False
        }
    },
    "stagesToSkip": ["Deploy-Production"]
}
```

### Get Build Logs

```python
# Using mcp__ado__pipelines_get_build_log
params = {
    "project": "MyProject",
    "buildId": 12345
}

# Get specific log
# Using mcp__ado__pipelines_get_build_log_by_id
params = {
    "project": "MyProject",
    "buildId": 12345,
    "logId": 5,
    "startLine": 100,
    "endLine": 200
}
```

### Retry Failed Stage

```python
# Using mcp__ado__pipelines_update_build_stage
params = {
    "project": "MyProject",
    "buildId": 12345,
    "stageName": "Deploy",
    "status": "Retry",
    "forceRetryAllJobs": True
}
```

### Get Pipeline Run

```python
# Using mcp__ado__pipelines_get_run
params = {
    "project": "MyProject",
    "pipelineId": 123,
    "runId": 456
}
```

---

## Common Pipeline Tasks

### Checkout

```yaml
steps:
  - checkout: self
    clean: true
    fetchDepth: 0
    lfs: true
    submodules: recursive
    persistCredentials: true
```

### Download Artifacts

```yaml
steps:
  - download: current
    artifact: 'drop'
    patterns: '**/*.dll'

  - task: DownloadPipelineArtifact@2
    inputs:
      buildType: 'specific'
      project: 'ProjectGuid'
      definition: '123'
      buildVersionToDownload: 'latest'
      artifactName: 'drop'
      targetPath: '$(Pipeline.Workspace)/artifacts'
```

### Publish Artifacts

```yaml
steps:
  - task: PublishPipelineArtifact@1
    inputs:
      targetPath: '$(Build.ArtifactStagingDirectory)'
      artifact: 'drop'
      publishLocation: 'pipeline'
```

### Cache

```yaml
steps:
  - task: Cache@2
    inputs:
      key: 'npm | "$(Agent.OS)" | package-lock.json'
      restoreKeys: |
        npm | "$(Agent.OS)"
      path: $(npm_config_cache)
    displayName: 'Cache npm packages'
```
