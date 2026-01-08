---
name: dependency-track-skill
description: Comprehensive guide for Dependency-Track - Software Composition Analysis (SCA) and SBOM management platform. USE WHEN deploying Dependency-Track, integrating with CI/CD pipelines, configuring vulnerability scanning, managing SBOMs, setting up policy compliance, troubleshooting installation issues, or working with the REST API.
triggers:
  - dependency-track
  - dependencytrack
  - dtrack
  - sbom
  - software bill of materials
  - software composition analysis
  - sca platform
  - vulnerability scanning
  - component analysis
  - cyclonedx
  - bom upload
  - license compliance
  - supply chain security
  - hyades
---

# Dependency-Track Skill

Comprehensive guide for implementing, deploying, and operating **Dependency-Track** - an intelligent Software Composition Analysis (SCA) platform that identifies and reduces risk in the software supply chain through SBOM management.

**Current Versions:**

- Helm Chart: `0.40.0`
- App Version: `4.13.6`
- Helm Repository: `https://dependencytrack.github.io/helm-charts`

## Overview

Dependency-Track is an API-first platform that:

- Consumes and produces CycloneDX SBOMs and VEX documents
- Monitors components for known vulnerabilities across the entire portfolio
- Integrates with NVD, GitHub Advisories, OSS Index, Snyk, Trivy, OSV, and VulnDB
- Provides policy enforcement for security, license, and operational compliance
- Supports OAuth 2.0, OIDC, LDAP, Active Directory authentication
- Supports EPSS (Exploit Prediction Scoring System) for prioritization
- Identifies APIs and external service components

## Quick Reference

| Resource | Path |
|----------|------|
| Deployment Templates | `references/deployment/` |
| CI/CD Integration | `references/cicd/` |
| API Examples | `references/api/` |
| Policy Templates | `references/policies/` |
| Troubleshooting | `references/troubleshooting.md` |

---

## 1. Deployment Options

### Docker Compose (Recommended for Production)

```bash
# Download official docker-compose
curl -LO https://dependencytrack.org/docker-compose.yml

# Start services
docker compose up -d

# Access UI at http://localhost:8080
# Default credentials: admin / admin
```

**Minimum Requirements:**

- API Server: 4.5GB RAM, 2 CPU cores
- Frontend: 512MB RAM, 1 CPU core

**Recommended Requirements:**

- API Server: 16GB RAM, 4 CPU cores
- Frontend: 1GB RAM, 2 CPU cores

### Kubernetes with Helm

```bash
# Add Helm repository
helm repo add dependency-track https://dependencytrack.github.io/helm-charts
helm repo update

# View available charts
helm search repo dependency-track

# Install with custom values
helm install dtrack dependency-track/dependency-track \
    --namespace dtrack \
    --create-namespace \
    -f values-production.yaml

# Upgrade existing installation
helm upgrade dtrack dependency-track/dependency-track \
    --namespace dtrack \
    -f values-production.yaml
```

**Available Charts:**

| Chart | Description | Status |
|-------|-------------|--------|
| `dependency-track/dependency-track` | Monolithic deployment (v4.x) | Production Ready |
| `dependency-track/hyades` | Microservices deployment (v5.x) | Incubating (Not GA) |

See `references/deployment/` for complete manifests and Helm values.

### Kubernetes Ingress Configuration (CRITICAL)

> **IMPORTANT**: The dependency-track Helm chart expects `ingress:` at the
> **ROOT level**, NOT under `frontend.ingress:`. This is a common mistake
> that causes the Ingress resource to not be created.

**Correct Structure:**

```yaml
# CORRECT - Ingress at root level
ingress:
  enabled: true
  hostname: dtrack.example.com
  ingressClassName: nginx
  annotations:
    cert-manager.io/cluster-issuer: letsencrypt-prod
    external-dns.alpha.kubernetes.io/hostname: dtrack.example.com
  tls:
    - secretName: dtrack-tls
      hosts:
        - dtrack.example.com

# Frontend config (NO ingress here!)
frontend:
  enabled: true
  apiBaseUrl: https://dtrack.example.com
  # ...
```

**Common Mistakes:**

```yaml
# WRONG - This will NOT create an Ingress resource!
frontend:
  ingress:  # <-- WRONG LOCATION
    enabled: true
    className: nginx
    hosts:
      - host: dtrack.example.com
```

**Key Differences from Standard Ingress:**

| Chart Expects | Standard nginx-ingress |
|--------------|------------------------|
| `hostname` (string) | `hosts` (array) |
| `ingressClassName` | `className` or `class` |
| Root level `ingress:` | Component level `frontend.ingress:` |

**Integration with cert-manager and external-dns:**

```yaml
ingress:
  enabled: true
  hostname: dtrack.dev.cafehyna.com.br
  ingressClassName: nginx
  annotations:
    # cert-manager for TLS certificates
    cert-manager.io/cluster-issuer: letsencrypt-staging-cloudflare  # dev
    # cert-manager.io/cluster-issuer: letsencrypt-prod-cloudflare   # prod

    # external-dns for automatic DNS record creation
    external-dns.alpha.kubernetes.io/hostname: dtrack.dev.cafehyna.com.br
    external-dns.alpha.kubernetes.io/cloudflare-proxied: "true"
    external-dns.alpha.kubernetes.io/ttl: "300"

    # nginx-ingress proxy settings (for large SBOM uploads)
    nginx.ingress.kubernetes.io/proxy-body-size: 100m
    nginx.ingress.kubernetes.io/proxy-connect-timeout: "300"
    nginx.ingress.kubernetes.io/proxy-read-timeout: "300"
    nginx.ingress.kubernetes.io/proxy-send-timeout: "300"

    # NOTE: configuration-snippet may be DISABLED by nginx-ingress admin
    # If you get "Snippet directives are disabled" error, remove it
    # Configure security headers at controller level via ConfigMap instead
  tls:
    - secretName: dtrack-tls
      hosts:
        - dtrack.dev.cafehyna.com.br
```

**Ingress Routes Created by Chart:**

The Helm chart automatically creates routing rules:

- `/api` → `dependency-track-api-server:web`
- `/health` → `dependency-track-api-server:web`
- `/` → `dependency-track-frontend:web`

### Hyades (Next-Generation Architecture)

Hyades is the incubating project for Dependency-Track v5, decoupling the monolithic API server into separate, scalable microservices.

**Components:**

- `hyades-apiserver` - Core API server
- `hyades-frontend` - Web UI
- `hyades-notification-publisher` - Notification handling
- `hyades-repository-meta-analyzer` - Repository metadata analysis
- `hyades-vulnerability-analyzer` - Vulnerability scanning

**Requirements:**

- External PostgreSQL database
- Apache Kafka cluster
- Kubernetes 1.19+

```bash
# Install Hyades (NOT PRODUCTION READY)
helm install hyades dependency-track/hyades \
    --namespace dtrack \
    --create-namespace \
    --set common.database.jdbcUrl="jdbc:postgresql://postgres:5432/dtrack" \
    --set common.database.username="dtrack" \
    --set common.database.password="secret" \
    --set common.kafka.bootstrapServers="kafka:9092"
```

> **Warning:** Hyades is NOT generally available. Breaking changes may occur without notice. Use only in test environments. GA roadmap: <https://github.com/DependencyTrack/hyades/issues/860>

---

## 2. Initial Configuration

### First-Time Setup

1. **Wait for initialization** (10-30+ minutes):
   - Creates default users, teams, permissions
   - Mirrors NVD, GitHub Advisories (do not interrupt)
   - Check progress: `docker logs -f dependency-track-apiserver`

2. **Change default password** immediately after first login

3. **Enable analyzers** in Administration > Analyzers:
   - Internal Analyzer (built-in)
   - OSS Index (requires API token from ossindex.sonatype.org)
   - Snyk (optional, requires token)
   - Trivy (optional)

### Database Configuration (Production)

```yaml
# docker-compose override for PostgreSQL
services:
  apiserver:
    environment:
      ALPINE_DATABASE_MODE: external
      ALPINE_DATABASE_URL: jdbc:postgresql://postgres:5432/dtrack
      ALPINE_DATABASE_DRIVER: org.postgresql.Driver
      ALPINE_DATABASE_USERNAME: dtrack
      ALPINE_DATABASE_PASSWORD: ${DB_PASSWORD}
```

### LDAP/Active Directory

```properties
# Active Directory configuration
ALPINE_LDAP_ENABLED=true
ALPINE_LDAP_SERVER_URL=ldap://ldap.example.com:3268
ALPINE_LDAP_BASEDN=dc=example,dc=com
ALPINE_LDAP_SECURITY_AUTH=simple
ALPINE_LDAP_AUTH_USERNAME_FORMAT=%s@example.com
ALPINE_LDAP_ATTRIBUTE_NAME=userPrincipalName
ALPINE_LDAP_ATTRIBUTE_MAIL=mail
ALPINE_LDAP_GROUPS_FILTER=(&(objectClass=group)(objectCategory=Group))
ALPINE_LDAP_USER_GROUPS_FILTER=(&(objectClass=group)(member:1.2.840.113556.1.4.1941:={USER_DN}))
```

### OpenID Connect (Azure AD, Okta, Keycloak)

```properties
ALPINE_OIDC_ENABLED=true
ALPINE_OIDC_ISSUER=https://login.microsoftonline.com/{tenant}/v2.0
ALPINE_OIDC_CLIENT_ID=your-client-id
ALPINE_OIDC_USERNAME_CLAIM=preferred_username
ALPINE_OIDC_TEAMS_CLAIM=groups
ALPINE_OIDC_USER_PROVISIONING=true
ALPINE_OIDC_TEAM_SYNCHRONIZATION=true
```

### Azure AD App Registration (CRITICAL)

> **IMPORTANT**: The Azure AD App Registration **MUST** have the correct
> redirect URI configured, or you will get error `AADSTS50011`.

**Required Redirect URI:**

```text
https://<your-dtrack-hostname>/static/oidc-callback.html
```

**Example for dev environment:**

```text
https://dtrack.dev.cafehyna.com.br/static/oidc-callback.html
```

**Configure via Azure CLI:**

```bash
# Add redirect URI to existing App Registration
az ad app update \
  --id <app-registration-id> \
  --web-redirect-uris "https://dtrack.example.com/static/oidc-callback.html"

# Verify the redirect URI was added
az ad app show --id <app-registration-id> --query "web.redirectUris" -o tsv
```

**Configure via Azure Portal:**

1. Go to **Azure AD** → **App registrations**
2. Select your Dependency-Track application
3. Click **Authentication** (left menu)
4. Under **Platform configurations** → **Web** → **Redirect URIs**
5. Add: `https://<your-hostname>/static/oidc-callback.html`
6. Click **Save**

**Common OIDC Errors:**

| Error Code | Cause | Solution |
|------------|-------|----------|
| AADSTS50011 | Redirect URI mismatch | Add correct URI to App Registration |
| AADSTS700016 | App not found in tenant | Verify app ID and tenant |
| AADSTS65001 | User consent required | Grant admin consent in portal |

---

## 3. CI/CD Integration

### Workflow: BOM Upload Pipeline

```text
┌─────────────┐     ┌─────────────┐     ┌──────────────────┐
│   Build     │────▶│ Generate    │────▶│    Upload to     │
│   Project   │     │ CycloneDX   │     │ Dependency-Track │
└─────────────┘     │    SBOM     │     └──────────────────┘
                    └─────────────┘              │
                                                 ▼
                    ┌─────────────┐     ┌──────────────────┐
                    │   Break     │◀────│    Evaluate      │
                    │   Build?    │     │    Policies      │
                    └─────────────┘     └──────────────────┘
```

### Jenkins Pipeline

```groovy
pipeline {
    agent any

    environment {
        DTRACK_URL = 'https://dtrack.example.com'
        DTRACK_API_KEY = credentials('dependency-track-api-key')
    }

    stages {
        stage('Build') {
            steps {
                sh 'mvn clean package'
            }
        }

        stage('Generate SBOM') {
            steps {
                sh 'mvn org.cyclonedx:cyclonedx-maven-plugin:makeAggregateBom'
            }
        }

        stage('Upload SBOM') {
            steps {
                dependencyTrackPublisher(
                    artifact: 'target/bom.xml',
                    projectId: env.PROJECT_UUID,
                    synchronous: true,
                    failedTotalCritical: 0,
                    failedTotalHigh: 5
                )
            }
        }
    }
}
```

### GitHub Actions

```yaml
name: SBOM Security Scan

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  sbom-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Generate SBOM
        uses: CycloneDX/gh-node-module-generatebom@v1
        with:
          output: ./bom.json

      - name: Upload to Dependency-Track
        uses: DependencyTrack/gh-upload-sbom@v3
        with:
          serverHostname: ${{ secrets.DTRACK_URL }}
          apiKey: ${{ secrets.DTRACK_API_KEY }}
          projectName: ${{ github.repository }}
          projectVersion: ${{ github.ref_name }}
          bomFilename: ./bom.json
          autoCreate: true
```

**Official GitHub Action Options (`DependencyTrack/gh-upload-sbom@v3`):**

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `serverHostname` | Yes | - | Dependency-Track server URL |
| `apiKey` | Yes | - | API key with BOM_UPLOAD permission |
| `projectName` | Yes | - | Name of the project |
| `projectVersion` | Yes | - | Version of the project |
| `bomFilename` | Yes | - | Path to CycloneDX SBOM file |
| `autoCreate` | No | `false` | Auto-create project if not exists |
| `parentName` | No | - | Parent project name |
| `parentVersion` | No | - | Parent project version |
| `projectUuid` | No | - | Use UUID instead of name/version |

### GitLab CI

```yaml
stages:
  - build
  - security

generate-sbom:
  stage: build
  image: cyclonedx/cyclonedx-cli
  script:
    - cyclonedx-py -r requirements.txt -o bom.json
  artifacts:
    paths:
      - bom.json

upload-sbom:
  stage: security
  image: curlimages/curl
  script:
    - |
      curl -X PUT "${DTRACK_URL}/api/v1/bom" \
        -H "X-Api-Key: ${DTRACK_API_KEY}" \
        -H "Content-Type: application/json" \
        -d @- << EOF
      {
        "projectName": "${CI_PROJECT_NAME}",
        "projectVersion": "${CI_COMMIT_REF_NAME}",
        "autoCreate": true,
        "bom": "$(base64 -w0 bom.json)"
      }
      EOF
```

### Azure DevOps Pipeline

```yaml
trigger:
  - main

pool:
  vmImage: 'ubuntu-latest'

variables:
  - group: dependency-track-credentials

steps:
  - task: Maven@4
    inputs:
      mavenPomFile: 'pom.xml'
      goals: 'package org.cyclonedx:cyclonedx-maven-plugin:makeAggregateBom'

  - task: Bash@3
    displayName: 'Upload SBOM to Dependency-Track'
    inputs:
      targetType: 'inline'
      script: |
        BOM_CONTENT=$(base64 -w0 target/bom.xml)
        curl -X PUT "$(DTRACK_URL)/api/v1/bom" \
          -H "X-Api-Key: $(DTRACK_API_KEY)" \
          -H "Content-Type: application/json" \
          -d "{\"projectName\":\"$(Build.Repository.Name)\",\"projectVersion\":\"$(Build.SourceBranchName)\",\"autoCreate\":true,\"bom\":\"${BOM_CONTENT}\"}"
```

---

## 4. REST API Usage

### Authentication

Generate API keys in Administration > Access Management > Teams > [Team] > API Keys.

```bash
# All API calls require the X-Api-Key header
curl -H "X-Api-Key: YOUR_API_KEY" \
     https://dtrack.example.com/api/v1/project
```

### OpenAPI Specification

Access at:

- JSON: `http://localhost:8081/api/openapi.json`
- YAML: `http://localhost:8081/api/openapi.yaml`

**Note:** Use port 8081 (API server), not 8080 (frontend).

### Common API Operations

```bash
# List all projects
curl -s -H "X-Api-Key: ${API_KEY}" \
     "${DTRACK_URL}/api/v1/project" | jq

# Get project by name and version
curl -s -H "X-Api-Key: ${API_KEY}" \
     "${DTRACK_URL}/api/v1/project/lookup?name=myapp&version=1.0.0" | jq

# Upload SBOM (Base64 encoded)
curl -X PUT "${DTRACK_URL}/api/v1/bom" \
     -H "X-Api-Key: ${API_KEY}" \
     -H "Content-Type: application/json" \
     -d "{
       \"projectName\": \"my-application\",
       \"projectVersion\": \"1.0.0\",
       \"autoCreate\": true,
       \"bom\": \"$(base64 -w0 bom.json)\"
     }"

# Upload SBOM (multipart - no encoding needed)
curl -X POST "${DTRACK_URL}/api/v1/bom" \
     -H "X-Api-Key: ${API_KEY}" \
     -F "projectName=my-application" \
     -F "projectVersion=1.0.0" \
     -F "autoCreate=true" \
     -F "bom=@bom.json"

# Get vulnerabilities for a project
curl -s -H "X-Api-Key: ${API_KEY}" \
     "${DTRACK_URL}/api/v1/vulnerability/project/${PROJECT_UUID}" | jq

# Get policy violations
curl -s -H "X-Api-Key: ${API_KEY}" \
     "${DTRACK_URL}/api/v1/violation/project/${PROJECT_UUID}" | jq

# Get component dependencies
curl -s -H "X-Api-Key: ${API_KEY}" \
     "${DTRACK_URL}/api/v1/component/project/${PROJECT_UUID}" | jq

# Create project
curl -X PUT "${DTRACK_URL}/api/v1/project" \
     -H "X-Api-Key: ${API_KEY}" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "new-project",
       "version": "1.0.0",
       "description": "Project description",
       "tags": [{"name": "production"}]
     }'
```

---

## 5. Policy Configuration

### Policy Types

| Type | Purpose | Example Conditions |
|------|---------|-------------------|
| **License** | Control allowed/forbidden licenses | Apache-2.0 allowed, GPL-3.0 forbidden |
| **Security** | Vulnerability severity thresholds | No Critical, max 5 High |
| **Operational** | Component allowlists/denylists | Block log4j < 2.17.0 |

### Creating Policies via API

```bash
# Create a security policy
curl -X PUT "${DTRACK_URL}/api/v1/policy" \
     -H "X-Api-Key: ${API_KEY}" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "No Critical Vulnerabilities",
       "operator": "ANY",
       "violationState": "FAIL",
       "policyConditions": [
         {
           "subject": "SEVERITY",
           "operator": "IS",
           "value": "CRITICAL"
         }
       ]
     }'

# Create a license policy (denylist approach)
curl -X PUT "${DTRACK_URL}/api/v1/policy" \
     -H "X-Api-Key: ${API_KEY}" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "No Copyleft Licenses",
       "operator": "ANY",
       "violationState": "WARN",
       "policyConditions": [
         {
           "subject": "LICENSE_GROUP",
           "operator": "IS",
           "value": "Copyleft"
         }
       ]
     }'

# Create operational policy (block specific component)
curl -X PUT "${DTRACK_URL}/api/v1/policy" \
     -H "X-Api-Key: ${API_KEY}" \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Block Vulnerable Log4j",
       "operator": "ALL",
       "violationState": "FAIL",
       "policyConditions": [
         {
           "subject": "COORDINATES",
           "operator": "MATCHES",
           "value": "{\"group\":\"org.apache.logging.log4j\",\"name\":\"log4j-core\",\"version\":\"<2.17.0\"}"
         }
       ]
     }'
```

### Policy Condition Subjects

- `AGE` - Component age
- `COORDINATES` - Group/Name/Version
- `CPE` - Common Platform Enumeration
- `CWE` - Common Weakness Enumeration
- `EPSS` - Exploit Prediction Scoring System
- `LICENSE` - Specific license
- `LICENSE_GROUP` - License category
- `PACKAGE_URL` - Package URL (PURL)
- `SEVERITY` - Vulnerability severity
- `SWID_TAGID` - Software ID tag
- `VERSION` - Component version
- `COMPONENT_HASH` - MD5, SHA, Blake hashes

---

## 6. Notifications & Integrations

### Webhook Configuration

```json
{
  "notification": {
    "level": "INFORMATIONAL",
    "scope": "PORTFOLIO",
    "group": "NEW_VULNERABILITY",
    "timestamp": "2024-01-15T10:30:00Z",
    "subject": {
      "component": {
        "name": "log4j-core",
        "version": "2.14.1"
      },
      "vulnerability": {
        "vulnId": "CVE-2021-44228",
        "severity": "CRITICAL"
      },
      "affectedProjects": [...]
    }
  }
}
```

### Notification Groups

- `NEW_VULNERABILITY` - New vulnerability identified
- `NEW_VULNERABLE_DEPENDENCY` - New vulnerable component added
- `ANALYSIS_DECISION_CHANGE` - Audit decision modified
- `POLICY_VIOLATION` - Policy violation detected
- `BOM_CONSUMED` - SBOM processed
- `BOM_PROCESSED` - SBOM analysis complete
- `VEX_CONSUMED` - VEX document processed

### Integration Targets

- **Slack/Teams**: Direct webhook support
- **Email**: SMTP configuration
- **Jira**: Native integration
- **DefectDojo**: Vulnerability aggregation
- **Fortify SSC**: AppSec platform
- **ThreadFix**: Vulnerability management
- **Kenna Security**: Risk prioritization

---

## 7. SBOM Generation Tools

### By Language/Ecosystem

| Language | Tool | Command |
|----------|------|---------|
| Java/Maven | cyclonedx-maven-plugin | `mvn org.cyclonedx:cyclonedx-maven-plugin:makeAggregateBom` |
| Java/Gradle | cyclonedx-gradle-plugin | `gradle cyclonedxBom` |
| Node.js | @cyclonedx/cyclonedx-npm | `npx @cyclonedx/cyclonedx-npm --output-file bom.json` |
| Python | cyclonedx-py | `cyclonedx-py -r requirements.txt -o bom.json` |
| Go | cyclonedx-gomod | `cyclonedx-gomod mod -json -output bom.json` |
| .NET | CycloneDX | `dotnet CycloneDX <project> -o bom.json` |
| Rust | cargo-cyclonedx | `cargo cyclonedx -f json` |
| Container | Syft | `syft <image> -o cyclonedx-json > bom.json` |

### Universal Tools

```bash
# Syft - multi-ecosystem SBOM generator
syft packages dir:. -o cyclonedx-json > bom.json

# Trivy - with vulnerability scanning
trivy fs --format cyclonedx --output bom.json .

# cdxgen - comprehensive generator
cdxgen -o bom.json
```

---

## 8. Best Practices

### Deployment

1. **Use external PostgreSQL** for production (not embedded H2)
2. **Allocate sufficient RAM** (minimum 4.5GB for API server)
3. **Configure persistent storage** for `/data` directory
4. **Enable TLS** with proper certificates
5. **Set up regular backups** of database and configuration

### Operations

1. **Generate SBOMs in CI/CD** - automate at build time
2. **Enable OSS Index Analyzer** - required for PURL-based scanning
3. **Mirror NVD locally** - improves performance
4. **Use synchronous uploads** in pipelines for immediate feedback
5. **Implement policy gates** - fail builds on violations

### Security

1. **Rotate API keys** regularly
2. **Use team-scoped keys** with minimal permissions
3. **Enable audit logging** for compliance
4. **Configure OIDC/LDAP** for enterprise authentication
5. **Contractually require SBOMs** from vendors

### Performance

1. **Schedule heavy operations** during off-hours
2. **Use pagination** for large API responses
3. **Implement caching** for frequently accessed data
4. **Monitor analyzer queue** depth
5. **Scale horizontally** with multiple API server replicas

---

## 9. Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| No vulnerabilities found | OSS Index not enabled | Enable in Admin > Analyzers, get API token |
| Analyzer not running | 6-hour schedule | Re-upload SBOM or wait for scheduled run |
| Container crashes | Insufficient RAM | Allocate minimum 4.5GB to API server |
| 413 Request Entity Too Large | Nginx body size limit | Add `nginx.ingress.kubernetes.io/proxy-body-size: "100m"` |
| PKIX path building error | Self-signed certificates | Configure internal CA in settings |
| LDAP sync delays | Async job queue | Wait or manually create accounts |
| Service stops after 1-2 weeks | OS temp cleanup | Set `-Djava.io.tmpdir=/path/to/tmpdir` |

### Debug Commands

```bash
# Check API server logs
docker logs -f dependency-track-apiserver

# Verify database connectivity
docker exec -it dependency-track-apiserver \
  curl -s http://localhost:8080/api/version

# Check analyzer status
curl -s -H "X-Api-Key: ${API_KEY}" \
     "${DTRACK_URL}/api/v1/configProperty?groupName=analyzer"

# Monitor mirror status
curl -s -H "X-Api-Key: ${API_KEY}" \
     "${DTRACK_URL}/api/v1/mirror/nvd"

# Health check
curl -s "${DTRACK_URL}/api/version"
```

### Performance Tuning

```yaml
# JVM settings for high-load environments
environment:
  JAVA_OPTIONS: >-
    -Xms8g
    -Xmx16g
    -XX:+UseG1GC
    -XX:MaxGCPauseMillis=200
    -XX:+ParallelRefProcEnabled
```

---

## 10. Reference Files

Additional templates and examples are in the `references/` directory:

**Deployment:**

- `references/deployment/docker-compose-production.yaml` - Docker Compose for production
- `references/deployment/helm-values.yaml` - Helm values for v4.x (Chart v0.40.0)
- `references/deployment/helm-values-hyades.yaml` - Helm values for Hyades v5.x (Chart v0.10.0)
- `references/deployment/kubernetes-manifests/` - Raw Kubernetes manifests

**CI/CD Integration:**

- `references/cicd/jenkinsfile` - Jenkins Pipeline example
- `references/cicd/github-action.yaml` - GitHub Actions workflow
- `references/cicd/gitlab-ci.yaml` - GitLab CI/CD pipeline
- `references/cicd/azure-pipeline.yaml` - Azure DevOps Pipeline

**API & Scripts:**

- `references/api/python-client.py` - Python client library example
- `references/api/bash-scripts/` - Shell scripts for common operations

**Policies:**

- `references/policies/security-policies.json` - Security policy templates
- `references/policies/license-policies.json` - License policy templates
- `references/policies/operational-policies.json` - Operational policy templates

**Troubleshooting:**

- `references/troubleshooting.md` - Common issues and solutions

---

## Related Skills

- `defectdojo-skill` - Vulnerability management integration
- `argocd-skill` - GitOps deployment of Dependency-Track
- `quality-guardian` - Security testing integration
