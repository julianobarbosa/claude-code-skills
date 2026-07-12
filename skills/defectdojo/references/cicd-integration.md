# DefectDojo CI/CD Integration Guide

## Overview

DefectDojo integrates with CI/CD pipelines to automatically import security scan results. This enables:

- Automated vulnerability tracking per build/commit
- Historical trend analysis
- Build-level security gates
- Deduplication across scans

## Integration Patterns

### Pattern 1: Direct API Integration

The simplest approach - directly call the DefectDojo API from your pipeline.

**Advantages:**

- No additional dependencies
- Full control over parameters
- Works with any CI/CD system

**Disadvantages:**

- More code to maintain
- Error handling must be implemented

### Pattern 2: Jenkins Plugin

Use the official DefectDojo Jenkins plugin for native integration.

**Advantages:**

- Native Jenkins integration
- UI-based configuration
- Built-in error handling

**Disadvantages:**

- Jenkins-specific
- Plugin updates needed

### Pattern 3: Python Script

Use a reusable Python script for consistent behavior across pipelines.

**Advantages:**

- Reusable across projects
- Easy to customize
- Better error handling

## GitLab CI Integration

### Basic Integration

```yaml
stages:
  - security
  - upload

variables:
  DEFECTDOJO_URL: "https://defectdojo.example.com"
  # Store DEFECTDOJO_TOKEN in CI/CD Variables

# Security Scanning Stage
trivy-scan:
  stage: security
  image: aquasec/trivy:latest
  script:
    - trivy image --format json --output trivy-results.json ${CI_REGISTRY_IMAGE}:${CI_COMMIT_SHA}
  artifacts:
    paths:
      - trivy-results.json
    expire_in: 1 day

semgrep-scan:
  stage: security
  image: returntocorp/semgrep
  script:
    - semgrep --config=auto --json --output=semgrep-results.json .
  artifacts:
    paths:
      - semgrep-results.json
    expire_in: 1 day

# Upload to DefectDojo Stage
upload-results:
  stage: upload
  image: curlimages/curl:latest
  dependencies:
    - trivy-scan
    - semgrep-scan
  script:
    # Upload Trivy results
    - |
      curl -X POST "${DEFECTDOJO_URL}/api/v2/reimport-scan/" \
        -H "Authorization: Token ${DEFECTDOJO_TOKEN}" \
        -F "scan_type=Trivy Scan" \
        -F "file=@trivy-results.json" \
        -F "product_name=${CI_PROJECT_NAME}" \
        -F "engagement_name=CI/CD" \
        -F "auto_create_context=true" \
        -F "minimum_severity=Low" \
        -F "active=true" \
        -F "verified=false" \
        -F "build_id=${CI_PIPELINE_ID}" \
        -F "commit_hash=${CI_COMMIT_SHA}" \
        -F "branch_tag=${CI_COMMIT_REF_NAME}"
    # Upload Semgrep results
    - |
      curl -X POST "${DEFECTDOJO_URL}/api/v2/reimport-scan/" \
        -H "Authorization: Token ${DEFECTDOJO_TOKEN}" \
        -F "scan_type=Semgrep JSON Report" \
        -F "file=@semgrep-results.json" \
        -F "product_name=${CI_PROJECT_NAME}" \
        -F "engagement_name=CI/CD" \
        -F "auto_create_context=true"
```

### Advanced: Create Engagement Per Pipeline

```yaml
.defectdojo-upload:
  image: curlimages/curl:latest
  script:
    - |
      # Create engagement for this pipeline
      ENGAGEMENT_RESPONSE=$(curl -s -X POST "${DEFECTDOJO_URL}/api/v2/engagements/" \
        -H "Authorization: Token ${DEFECTDOJO_TOKEN}" \
        -H "Content-Type: application/json" \
        -d "{
          \"name\": \"Pipeline-${CI_PIPELINE_ID}\",
          \"product\": ${PRODUCT_ID},
          \"target_start\": \"$(date +%Y-%m-%d)\",
          \"target_end\": \"$(date +%Y-%m-%d)\",
          \"engagement_type\": \"CI/CD\",
          \"build_id\": \"${CI_PIPELINE_ID}\",
          \"commit_hash\": \"${CI_COMMIT_SHA}\",
          \"branch_tag\": \"${CI_COMMIT_REF_NAME}\"
        }")
      ENGAGEMENT_ID=$(echo $ENGAGEMENT_RESPONSE | jq -r '.id')

      # Import scan with specific engagement
      curl -X POST "${DEFECTDOJO_URL}/api/v2/import-scan/" \
        -H "Authorization: Token ${DEFECTDOJO_TOKEN}" \
        -F "scan_type=${SCAN_TYPE}" \
        -F "file=@${SCAN_FILE}" \
        -F "engagement=${ENGAGEMENT_ID}"
```

## GitHub Actions Integration

### Basic Integration

```yaml
name: Security Scan

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  DEFECTDOJO_URL: ${{ secrets.DEFECTDOJO_URL }}
  DEFECTDOJO_TOKEN: ${{ secrets.DEFECTDOJO_TOKEN }}

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          format: 'json'
          output: 'trivy-results.json'
          severity: 'CRITICAL,HIGH,MEDIUM,LOW'

      - name: Run Semgrep
        uses: returntocorp/semgrep-action@v1
        with:
          config: auto
          output: semgrep-results.json
          json: true

      - name: Run Gitleaks
        uses: gitleaks/gitleaks-action@v2
        env:
          GITLEAKS_ENABLE_UPLOAD_ARTIFACT: false
        continue-on-error: true

      - name: Upload Trivy to DefectDojo
        run: |
          curl -X POST "${{ env.DEFECTDOJO_URL }}/api/v2/reimport-scan/" \
            -H "Authorization: Token ${{ env.DEFECTDOJO_TOKEN }}" \
            -F "scan_type=Trivy Scan" \
            -F "file=@trivy-results.json" \
            -F "product_name=${{ github.repository }}" \
            -F "engagement_name=GitHub-Actions" \
            -F "auto_create_context=true" \
            -F "minimum_severity=Info" \
            -F "build_id=${{ github.run_id }}" \
            -F "commit_hash=${{ github.sha }}" \
            -F "branch_tag=${{ github.ref_name }}"

      - name: Upload Semgrep to DefectDojo
        if: always()
        run: |
          curl -X POST "${{ env.DEFECTDOJO_URL }}/api/v2/reimport-scan/" \
            -H "Authorization: Token ${{ env.DEFECTDOJO_TOKEN }}" \
            -F "scan_type=Semgrep JSON Report" \
            -F "file=@semgrep-results.json" \
            -F "product_name=${{ github.repository }}" \
            -F "engagement_name=GitHub-Actions" \
            -F "auto_create_context=true"
```

### Security Gate (Fail Build on Critical Findings)

```yaml
  check-critical-findings:
    runs-on: ubuntu-latest
    needs: security-scan
    steps:
      - name: Check for critical findings
        run: |
          CRITICAL_COUNT=$(curl -s "${{ env.DEFECTDOJO_URL }}/api/v2/findings/?product_name=${{ github.repository }}&severity=Critical&active=true" \
            -H "Authorization: Token ${{ env.DEFECTDOJO_TOKEN }}" | jq '.count')

          if [ "$CRITICAL_COUNT" -gt 0 ]; then
            echo "::error::Found $CRITICAL_COUNT critical vulnerabilities!"
            exit 1
          fi
          echo "No critical vulnerabilities found"
```

## Jenkins Integration

### Using DefectDojo Plugin

1. Install the DefectDojo plugin from Jenkins plugin manager
2. Configure in Jenkins > System Configuration:
   - DefectDojo Backend URL
   - API Key
   - Auto Create Products/Engagements

**Declarative Pipeline:**

```groovy
pipeline {
    agent any

    environment {
        DEFECTDOJO_URL = 'https://defectdojo.example.com'
        DEFECTDOJO_API_KEY = credentials('defectdojo-api-key')
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Security Scans') {
            parallel {
                stage('Trivy Scan') {
                    steps {
                        sh 'trivy fs --format json -o trivy-results.json .'
                    }
                }
                stage('Semgrep Scan') {
                    steps {
                        sh 'semgrep --config=auto --json -o semgrep-results.json .'
                    }
                }
                stage('Dependency Check') {
                    steps {
                        sh 'dependency-check --scan . --format JSON -o dependency-check-results.json'
                    }
                }
            }
        }

        stage('Upload to DefectDojo') {
            steps {
                // Using DefectDojo Plugin
                defectDojoPublisher(
                    artifact: 'trivy-results.json',
                    productName: env.JOB_NAME,
                    scanType: 'Trivy Scan',
                    engagementName: "Build-${BUILD_NUMBER}"
                )

                defectDojoPublisher(
                    artifact: 'semgrep-results.json',
                    productName: env.JOB_NAME,
                    scanType: 'Semgrep JSON Report',
                    engagementName: "Build-${BUILD_NUMBER}"
                )

                defectDojoPublisher(
                    artifact: 'dependency-check-results.json',
                    productName: env.JOB_NAME,
                    scanType: 'Dependency Check Scan',
                    engagementName: "Build-${BUILD_NUMBER}"
                )
            }
        }

        stage('Security Gate') {
            steps {
                script {
                    def response = httpRequest(
                        url: "${DEFECTDOJO_URL}/api/v2/findings/?product_name=${env.JOB_NAME}&severity=Critical&active=true",
                        customHeaders: [[name: 'Authorization', value: "Token ${DEFECTDOJO_API_KEY}"]]
                    )
                    def findings = readJSON text: response.content

                    if (findings.count > 0) {
                        error "Found ${findings.count} critical vulnerabilities! Build failed."
                    }
                }
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: '*-results.json', fingerprint: true
        }
    }
}
```

### Using Shell Commands (Without Plugin)

```groovy
stage('Upload to DefectDojo') {
    steps {
        withCredentials([string(credentialsId: 'defectdojo-token', variable: 'DD_TOKEN')]) {
            sh """
                curl -X POST "${DEFECTDOJO_URL}/api/v2/reimport-scan/" \
                    -H "Authorization: Token \${DD_TOKEN}" \
                    -F "scan_type=Trivy Scan" \
                    -F "file=@trivy-results.json" \
                    -F "product_name=${env.JOB_NAME}" \
                    -F "engagement_name=Build-${BUILD_NUMBER}" \
                    -F "auto_create_context=true" \
                    -F "build_id=${BUILD_NUMBER}" \
                    -F "commit_hash=${GIT_COMMIT}"
            """
        }
    }
}
```

## Azure DevOps Integration

```yaml
trigger:
  - main
  - develop

pool:
  vmImage: 'ubuntu-latest'

variables:
  - group: defectdojo-credentials

stages:
  - stage: SecurityScan
    jobs:
      - job: ScanAndUpload
        steps:
          - task: Bash@3
            displayName: 'Run Trivy Scan'
            inputs:
              targetType: 'inline'
              script: |
                docker run --rm -v $(pwd):/project aquasec/trivy:latest \
                  fs --format json -o /project/trivy-results.json /project

          - task: Bash@3
            displayName: 'Upload to DefectDojo'
            inputs:
              targetType: 'inline'
              script: |
                curl -X POST "$(DEFECTDOJO_URL)/api/v2/reimport-scan/" \
                  -H "Authorization: Token $(DEFECTDOJO_TOKEN)" \
                  -F "scan_type=Trivy Scan" \
                  -F "file=@trivy-results.json" \
                  -F "product_name=$(Build.Repository.Name)" \
                  -F "engagement_name=AzureDevOps" \
                  -F "auto_create_context=true" \
                  -F "build_id=$(Build.BuildId)" \
                  -F "commit_hash=$(Build.SourceVersion)" \
                  -F "branch_tag=$(Build.SourceBranchName)"
```

## Python Upload Script

Reusable script for consistent uploads across pipelines:

```python
#!/usr/bin/env python3
"""
DefectDojo CI/CD Upload Script
Usage: python upload_to_defectdojo.py --url <url> --token <token> --product <name> --scan-type <type> --file <path>
"""

import argparse
import requests
import sys
import os
from datetime import date

def upload_scan(args):
    """Upload scan results to DefectDojo."""

    headers = {
        'Authorization': f'Token {args.token}'
    }

    # Prepare form data
    data = {
        'scan_type': args.scan_type,
        'minimum_severity': args.minimum_severity or 'Info',
        'active': 'true',
        'verified': 'false',
        'auto_create_context': 'true',
        'close_old_findings': 'true',
    }

    # Add product/engagement context
    if args.product:
        data['product_name'] = args.product
    if args.engagement:
        data['engagement_name'] = args.engagement
    if args.test_title:
        data['test_title'] = args.test_title

    # Add CI/CD metadata
    if args.build_id:
        data['build_id'] = args.build_id
    if args.commit_hash:
        data['commit_hash'] = args.commit_hash
    if args.branch:
        data['branch_tag'] = args.branch

    # Upload file
    with open(args.file, 'rb') as f:
        files = {'file': (os.path.basename(args.file), f)}

        endpoint = f'{args.url.rstrip("/")}/api/v2/reimport-scan/'

        try:
            response = requests.post(
                endpoint,
                headers=headers,
                data=data,
                files=files,
                timeout=300
            )
            response.raise_for_status()

            result = response.json()
            print(f"Successfully uploaded scan results!")
            print(f"Test ID: {result.get('test', 'N/A')}")
            print(f"Findings created: {result.get('statistics', {}).get('created', 0)}")
            print(f"Findings closed: {result.get('statistics', {}).get('closed', 0)}")

            return 0

        except requests.exceptions.HTTPError as e:
            print(f"HTTP Error: {e}")
            print(f"Response: {e.response.text}")
            return 1
        except requests.exceptions.RequestException as e:
            print(f"Request Error: {e}")
            return 1

def main():
    parser = argparse.ArgumentParser(description='Upload scan results to DefectDojo')
    parser.add_argument('--url', required=True, help='DefectDojo URL')
    parser.add_argument('--token', required=True, help='API Token')
    parser.add_argument('--product', required=True, help='Product name')
    parser.add_argument('--scan-type', required=True, help='Scanner type (e.g., "Trivy Scan")')
    parser.add_argument('--file', required=True, help='Scan results file path')
    parser.add_argument('--engagement', default='CI/CD', help='Engagement name')
    parser.add_argument('--test-title', help='Custom test title')
    parser.add_argument('--minimum-severity', default='Info',
                       choices=['Info', 'Low', 'Medium', 'High', 'Critical'],
                       help='Minimum severity to import')
    parser.add_argument('--build-id', help='CI/CD build ID')
    parser.add_argument('--commit-hash', help='Git commit hash')
    parser.add_argument('--branch', help='Git branch name')

    args = parser.parse_args()

    sys.exit(upload_scan(args))

if __name__ == '__main__':
    main()
```

**Usage:**

```bash
python upload_to_defectdojo.py \
  --url https://defectdojo.example.com \
  --token $DEFECTDOJO_TOKEN \
  --product "MyApp" \
  --scan-type "Trivy Scan" \
  --file trivy-results.json \
  --build-id $CI_PIPELINE_ID \
  --commit-hash $CI_COMMIT_SHA \
  --branch $CI_BRANCH
```

## Best Practices

### 1. Use Reimport for Continuous Scanning

```bash
# Always use reimport-scan for CI/CD
/api/v2/reimport-scan/  # Preferred - handles deduplication

# Only use import-scan for first-time imports
/api/v2/import-scan/    # Creates new test each time
```

### 2. Enable Auto-Create Context

```bash
-F "auto_create_context=true"
```

This automatically creates Product/Engagement if they don't exist.

### 3. Track Build Metadata

```bash
-F "build_id=${BUILD_ID}" \
-F "commit_hash=${GIT_COMMIT}" \
-F "branch_tag=${GIT_BRANCH}" \
-F "source_code_management_uri=${GIT_URL}"
```

### 4. Set Appropriate Minimum Severity

```bash
# Development: All findings
-F "minimum_severity=Info"

# Production: Focus on actionable items
-F "minimum_severity=Medium"
```

### 5. Implement Security Gates

Query DefectDojo API to fail builds on critical findings:

```bash
CRITICAL=$(curl -s "${DEFECTDOJO_URL}/api/v2/findings/?severity=Critical&active=true&product_name=${PRODUCT}" \
  -H "Authorization: Token ${TOKEN}" | jq '.count')

if [ "$CRITICAL" -gt 0 ]; then
  echo "Build failed: $CRITICAL critical vulnerabilities found"
  exit 1
fi
```

### 6. Use Consistent Product Naming

```bash
# Use repository name for consistency
-F "product_name=${CI_PROJECT_NAME}"
-F "product_name=${{ github.repository }}"
-F "product_name=${env.JOB_NAME}"
```

### 7. Handle Upload Failures Gracefully

```yaml
# Continue pipeline even if upload fails
- name: Upload to DefectDojo
  continue-on-error: true
  run: |
    curl ... || echo "Warning: Failed to upload to DefectDojo"
```
