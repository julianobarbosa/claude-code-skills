---
name: container-security-skill
description: Container image security scanning, Dockerfile hardening, and ACR image management. Use when scanning container images for vulnerabilities with Trivy, hardening Dockerfiles (pinning versions, non-root runtime, SSH config), importing images to Azure Container Registry to avoid Docker Hub rate limits, or analyzing CVE findings. Also trigger when the user mentions image security, vulnerability scanning, CVE remediation, container hardening, Trivy scan, Docker security, or ACR image import — even if they don't explicitly say "container security".
allowed-tools: Read, Bash, Grep, Glob, Edit, Write, Agent, WebSearch
---

# Container Image Security

Complete workflow for securing container images: scan, analyze, harden, verify.

## Workflow Overview

```
Import base image to ACR → Build → Scan with Trivy → Analyze CVEs → Harden Dockerfile → Rebuild → Re-scan → Verify
```

## 1. Import Base Images to ACR

Avoid Docker Hub rate limits by importing base images into your private ACR. Azure's infrastructure pulls on your behalf — no Docker Hub auth needed.

```bash
# Import a public image into ACR
az acr import --name <registry> \
  --source docker.io/<image>:<tag> \
  --image <local-path>/<image>:<tag>

# Example: import code-server
az acr import --name cafehyna \
  --source docker.io/codercom/code-server:4.107.1 \
  --image addons/code-server:4.107.1

# Verify
az acr repository show --name <registry> --repository <local-path>/<image>
```

Then update the Dockerfile `FROM` to reference the ACR copy:
```dockerfile
# Before (hits Docker Hub rate limits in ACR cloud builds)
FROM codercom/code-server:latest

# After (pulls from local ACR — no rate limit)
FROM cafehyna.azurecr.io/addons/code-server:4.107.1
```

**Important**: ACR cloud builds (`az acr build`) are unauthenticated against Docker Hub. Any `FROM` referencing Docker Hub will eventually hit rate limits. Always import first.

## 2. Build with ACR

```bash
az acr build --registry <registry> --image <repo>:<tag> -f Dockerfile .
```

**ACR builder limitations** — these Docker features are NOT supported:
- `COPY <<'EOF'` heredoc syntax (BuildKit-only) — use `RUN printf` or `RUN cat` instead
- Multi-platform builds require `--platform` flag
- BuildKit-specific `RUN --mount` directives

## 3. Scan with Trivy

### Option A: Trivy via ACR Task (recommended for CI)

First, import Trivy itself into ACR (once):
```bash
az acr import --name <registry> \
  --source docker.io/aquasec/trivy:latest \
  --image tools/trivy:latest
```

Then scan:
```bash
# Table format for human review
az acr run --registry <registry> \
  --cmd "<registry>.azurecr.io/tools/trivy:latest image \
    --severity HIGH,CRITICAL \
    <registry>.azurecr.io/<image>:<tag>" /dev/null

# JSON format for programmatic analysis
az acr run --registry <registry> \
  --cmd "<registry>.azurecr.io/tools/trivy:latest image \
    --severity HIGH,CRITICAL --format json \
    <registry>.azurecr.io/<image>:<tag>" /dev/null
```

### Option B: Trivy locally (requires Docker daemon)

```bash
az acr login --name <registry>
trivy image --severity HIGH,CRITICAL <registry>.azurecr.io/<image>:<tag>
```

### Option C: Trivy on local Dockerfile (no build needed)

```bash
trivy config --severity HIGH,CRITICAL,MEDIUM Dockerfile
```

## 4. Analyze CVE Findings

Categorize every CRITICAL and HIGH finding:

| Category | Action | Example |
|----------|--------|---------|
| **Fixable by us** | Pin newer version in Dockerfile | Tool binary built with old Go stdlib |
| **Fixable upstream** | Track, document, revisit | Base image ships vulnerable internal dep |
| **OS-level, patch pending** | Document, monitor Debian/Ubuntu tracker | libsqlite3, openssl |
| **will_not_fix** | Accept risk or find alternative package | zlib1g in Debian |

For JSON output, extract CRITICAL summary:
```python
import json
data = json.load(open('trivy-results.json'))
for result in data.get('Results', []):
    for v in result.get('Vulnerabilities', []):
        if v.get('Severity') == 'CRITICAL':
            print(f"{v['VulnerabilityID']} | {v['PkgName']} {v.get('InstalledVersion','')} | fix: {v.get('FixedVersion','')} | {v.get('Status','')}")
```

## 5. Dockerfile Hardening Checklist

### Version Pinning (eliminates reproducibility CVEs)

```dockerfile
# Bad — unpinned, non-reproducible, may pull vulnerable versions
FROM image:latest
RUN curl .../releases/latest/download/tool | bash

# Good — pinned, reproducible, auditable
FROM registry.azurecr.io/addons/image:4.107.1

ARG TOOL_VERSION=v1.2.3
RUN curl -fsSL "https://github.com/org/tool/releases/download/${TOOL_VERSION}/tool_linux_amd64.tar.gz" \
    | tar xz -C /usr/local/bin tool
```

Use `ARG` for version variables — makes updates a single-line change and is visible in `docker history`.

### SSH Hardening

```dockerfile
# Disable password auth, enable key-based only
RUN mkdir -p /run/sshd && \
    sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config && \
    sed -i 's/#PubkeyAuthentication yes/PubkeyAuthentication yes/' /etc/ssh/sshd_config && \
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin no/' /etc/ssh/sshd_config && \
    echo "AllowUsers <user>" >> /etc/ssh/sshd_config && \
    ssh-keygen -A && \
    mkdir -p /home/<user>/.ssh && \
    chmod 700 /home/<user>/.ssh && \
    chown <user>:<user> /home/<user>/.ssh
```

### Non-root Runtime

```dockerfile
# Start privileged services as root, then drop privileges
RUN printf '#!/bin/bash\nset -e\n/usr/sbin/sshd\nexec su - <user> -c "<main-process>"\n' \
    > /usr/local/bin/entrypoint.sh && \
    chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
```

If no privileged services are needed, simply:
```dockerfile
USER <non-root-user>
ENTRYPOINT ["<main-process>"]
```

### Additional Hardening

- **Minimize layers**: combine related `RUN` commands
- **Clean apt caches**: always end with `&& rm -rf /var/lib/apt/lists/*`
- **No secrets in image**: use runtime injection (env vars, mounted secrets)
- **Verify downloads**: checksum or GPG verify binaries when possible
- **Read-only filesystem**: add `--read-only` at runtime where possible

## 6. Rebuild and Re-scan

After hardening, always rebuild and re-scan to verify fixes:

```bash
# Rebuild with new tag
az acr build --registry <registry> --image <repo>:<new-tag> -f Dockerfile .

# Re-scan
az acr run --registry <registry> \
  --cmd "<registry>.azurecr.io/tools/trivy:latest image \
    --severity HIGH,CRITICAL \
    <registry>.azurecr.io/<repo>:<new-tag>" /dev/null

# Compare CRITICAL counts: before vs after
```

## 7. Verification Checklist

After completing the security cycle, verify:

- [ ] `az acr repository show` — base image exists in ACR
- [ ] `az acr build` — completes without rate limit errors
- [ ] Trivy scan — CRITICAL count reduced (document remaining upstream CVEs)
- [ ] `az acr repository show` — final image exists in ACR
- [ ] Dockerfile uses pinned versions (no `:latest` for tools)
- [ ] SSH configured for key-only auth (if applicable)
- [ ] Container runs as non-root user
- [ ] No secrets baked into image layers

## Common Patterns

### Rate limit recovery
When `az acr import` also hits rate limits (happens with burst imports), wait 15 minutes or use an authenticated Docker Hub account:
```bash
az acr import --name <registry> \
  --source docker.io/<image>:<tag> \
  --image <local-path>/<image>:<tag> \
  --username <dockerhub-user> --password <dockerhub-token>
```

### Multi-tool Dockerfile with pinned versions
```dockerfile
ARG K9S_VERSION=v0.50.18
ARG ARGOCD_VERSION=v3.3.3
ARG YQ_VERSION=v4.52.4
ARG KUSTOMIZE_VERSION=v5.8.0

RUN curl -fsSL "https://github.com/derailed/k9s/releases/download/${K9S_VERSION}/k9s_Linux_amd64.tar.gz" | tar xz -C /usr/local/bin k9s
RUN curl -sSL -o /usr/local/bin/argocd "https://github.com/argoproj/argo-cd/releases/download/${ARGOCD_VERSION}/argocd-linux-amd64" && chmod +x /usr/local/bin/argocd
RUN curl -fsSL "https://github.com/mikefarah/yq/releases/download/${YQ_VERSION}/yq_linux_amd64" -o /usr/local/bin/yq && chmod +x /usr/local/bin/yq
RUN curl -fsSL "https://github.com/kubernetes-sigs/kustomize/releases/download/kustomize%2F${KUSTOMIZE_VERSION}/kustomize_${KUSTOMIZE_VERSION}_linux_amd64.tar.gz" | tar xz -C /usr/local/bin kustomize
```
