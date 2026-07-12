# CI Integration Workflow

Integrate pre-commit hooks into CI/CD pipelines.

## Trigger

- "CI pipeline"
- "GitHub Actions pre-commit"
- "GitLab CI pre-commit"
- "Azure Pipelines pre-commit"
- "automate pre-commit"

## GitHub Actions

### Recommended: Official Action

```yaml
# .github/workflows/pre-commit.yml
name: Pre-commit

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main, develop]

jobs:
  pre-commit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - uses: pre-commit/action@v3.0.1
```

### With Caching

```yaml
name: Pre-commit

on: [push, pull_request]

jobs:
  pre-commit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Cache pre-commit
        uses: actions/cache@v4
        with:
          path: ~/.cache/pre-commit
          key: pre-commit-${{ hashFiles('.pre-commit-config.yaml') }}

      - uses: pre-commit/action@v3.0.1
```

### With Additional Tools (Terraform, Node)

```yaml
name: Pre-commit

on: [push, pull_request]

jobs:
  pre-commit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - uses: actions/setup-node@v4
        with:
          node-version: '20'

      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: '1.9.0'

      - name: Install tflint
        run: |
          curl -s https://raw.githubusercontent.com/terraform-linters/tflint/master/install_linux.sh | bash

      - name: Cache pre-commit
        uses: actions/cache@v4
        with:
          path: ~/.cache/pre-commit
          key: pre-commit-${{ hashFiles('.pre-commit-config.yaml') }}

      - uses: pre-commit/action@v3.0.1
```

### Manual Installation (Alternative)

```yaml
name: Pre-commit

on: [push, pull_request]

jobs:
  pre-commit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install pre-commit
        run: pip install pre-commit

      - name: Run pre-commit
        run: pre-commit run --all-files
```

---

## GitLab CI

### Basic Configuration

```yaml
# .gitlab-ci.yml
stages:
  - lint

pre-commit:
  stage: lint
  image: python:3.11
  variables:
    PRE_COMMIT_HOME: ${CI_PROJECT_DIR}/.cache/pre-commit
  cache:
    key: pre-commit
    paths:
      - .cache/pre-commit
  before_script:
    - pip install pre-commit
  script:
    - pre-commit run --all-files
  rules:
    - if: $CI_MERGE_REQUEST_ID
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

### With Terraform Tools

```yaml
pre-commit:
  stage: lint
  image: python:3.11
  variables:
    PRE_COMMIT_HOME: ${CI_PROJECT_DIR}/.cache/pre-commit
    TERRAFORM_VERSION: "1.9.0"
    TFLINT_VERSION: "0.53.0"
  cache:
    key: pre-commit-${CI_COMMIT_REF_SLUG}
    paths:
      - .cache/pre-commit
  before_script:
    - pip install pre-commit
    # Install Terraform
    - apt-get update && apt-get install -y unzip
    - curl -o terraform.zip https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip
    - unzip terraform.zip && mv terraform /usr/local/bin/
    # Install TFLint
    - curl -L -o tflint.zip https://github.com/terraform-linters/tflint/releases/download/v${TFLINT_VERSION}/tflint_linux_amd64.zip
    - unzip tflint.zip && mv tflint /usr/local/bin/
  script:
    - pre-commit run --all-files
```

---

## Azure Pipelines

### Basic Configuration

```yaml
# azure-pipelines.yml
trigger:
  - main
  - develop

pr:
  - main
  - develop

pool:
  vmImage: 'ubuntu-latest'

steps:
  - task: UsePythonVersion@0
    inputs:
      versionSpec: '3.11'

  - script: pip install pre-commit
    displayName: 'Install pre-commit'

  - script: pre-commit run --all-files
    displayName: 'Run pre-commit'
```

### With Caching

```yaml
trigger:
  - main

pool:
  vmImage: 'ubuntu-latest'

variables:
  PRE_COMMIT_HOME: $(Pipeline.Workspace)/.cache/pre-commit

steps:
  - task: UsePythonVersion@0
    inputs:
      versionSpec: '3.11'

  - task: Cache@2
    inputs:
      key: 'pre-commit | "$(Agent.OS)" | .pre-commit-config.yaml'
      path: $(PRE_COMMIT_HOME)
    displayName: 'Cache pre-commit'

  - script: pip install pre-commit
    displayName: 'Install pre-commit'

  - script: pre-commit run --all-files
    displayName: 'Run pre-commit'
```

---

## CircleCI

```yaml
# .circleci/config.yml
version: 2.1

jobs:
  pre-commit:
    docker:
      - image: cimg/python:3.11
    steps:
      - checkout
      - restore_cache:
          keys:
            - pre-commit-{{ checksum ".pre-commit-config.yaml" }}
      - run:
          name: Install pre-commit
          command: pip install pre-commit
      - run:
          name: Run pre-commit
          command: pre-commit run --all-files
      - save_cache:
          key: pre-commit-{{ checksum ".pre-commit-config.yaml" }}
          paths:
            - ~/.cache/pre-commit

workflows:
  version: 2
  lint:
    jobs:
      - pre-commit
```

---

## Bitbucket Pipelines

```yaml
# bitbucket-pipelines.yml
image: python:3.11

pipelines:
  default:
    - step:
        name: Pre-commit
        caches:
          - pre-commit
        script:
          - pip install pre-commit
          - pre-commit run --all-files

definitions:
  caches:
    pre-commit: ~/.cache/pre-commit
```

---

## Jenkins

### Jenkinsfile (Declarative)

```groovy
// Jenkinsfile
pipeline {
    agent {
        docker {
            image 'python:3.11'
        }
    }

    stages {
        stage('Pre-commit') {
            steps {
                sh 'pip install pre-commit'
                sh 'pre-commit run --all-files'
            }
        }
    }

    post {
        always {
            cleanWs()
        }
    }
}
```

---

## pre-commit.ci (Dedicated Service)

### Auto-fix PRs

Add `.pre-commit-ci.yaml` to repository root:

```yaml
# .pre-commit-ci.yaml
ci:
  autofix_prs: true
  autofix_commit_msg: 'style: auto-fix from pre-commit.ci'
  autoupdate_schedule: monthly
  autoupdate_commit_msg: 'chore: pre-commit autoupdate'
  skip: [terraform_validate]  # Skip hooks that need external tools
```

### Badge

Add to README.md:
```markdown
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/OWNER/REPO/main.svg)](https://results.pre-commit.ci/latest/github/OWNER/REPO/main)
```

---

## Best Practices

### 1. Run on Changed Files Only (for PRs)

```yaml
# GitHub Actions
- uses: pre-commit/action@v3.0.1
  with:
    extra_args: --from-ref origin/${{ github.base_ref }} --to-ref HEAD
```

### 2. Fail Fast in CI

```yaml
# .pre-commit-config.yaml
fail_fast: true  # Stop after first failure
```

### 3. Skip CI-Incompatible Hooks

Some hooks require local tools or user interaction:

```yaml
# .pre-commit-config.yaml
- id: terraform_validate
  stages: [pre-commit]  # Won't run in CI with --all-files
```

Or skip in CI:

```bash
SKIP=interactive-hook pre-commit run --all-files
```

### 4. Separate Security Scanning

Run security hooks separately for better visibility:

```yaml
# GitHub Actions
jobs:
  pre-commit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pre-commit/action@v3.0.1

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install pre-commit
      - run: pre-commit run gitleaks --all-files
      - run: pre-commit run checkov --all-files
```

### 5. Cache Effectively

Always cache `~/.cache/pre-commit` with config hash as key:

```yaml
key: pre-commit-${{ hashFiles('.pre-commit-config.yaml') }}
```
