# Dockerfile Security Review

## Original Dockerfile

```dockerfile
FROM ubuntu:latest
RUN apt-get update && apt-get install -y openssh-server curl
RUN sed -i 's/#PasswordAuthentication yes/PasswordAuthentication yes/' /etc/ssh/sshd_config
RUN curl https://example.com/tool/latest/download | bash
EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]
```

## Security Issues Identified

### 1. Unpinned Base Image Tag (`FROM ubuntu:latest`)

**Severity: High**

Using `latest` makes builds non-reproducible and can silently introduce breaking changes or vulnerabilities. A new upstream push could change the base image without any notice.

**Remediation:** Pin to a specific version and digest, e.g. `ubuntu:24.04@sha256:<digest>`.

### 2. Running SSH Server / Exposing Port 22

**Severity: High**

Running an SSH daemon inside a container is an anti-pattern. It expands the attack surface significantly, provides a remote access vector, and is almost never necessary. Container access should be managed through orchestrator tooling (`docker exec`, `kubectl exec`).

**Remediation:** Remove the SSH server entirely. If remote debugging is absolutely required, use ephemeral debug containers or exec-based access.

### 3. Password Authentication Enabled for SSH

**Severity: High**

The Dockerfile explicitly enables password authentication, which is vulnerable to brute-force attacks. If SSH must be kept (strongly discouraged), only key-based authentication should be permitted, with `PasswordAuthentication no` and `PermitRootLogin no`.

### 4. Piping Curl Output Directly to Bash (`curl ... | bash`)

**Severity: Critical**

This is one of the most dangerous patterns in a Dockerfile:

- **No integrity verification:** The downloaded script is executed without any checksum or signature validation. A compromised server, DNS hijack, or man-in-the-middle attack could inject arbitrary code.
- **Non-reproducible:** The `/latest/` URL means the content can change between builds.
- **No audit trail:** The script contents are not visible or reviewable in the image layers.

**Remediation:** Download a pinned version of the tool, verify its checksum (SHA-256 at minimum), then install it.

### 5. Running as Root

**Severity: High**

There is no `USER` directive, so the container runs all processes as root. If an attacker exploits any vulnerability in the running service, they gain root privileges inside the container, which can be escalated to the host in certain configurations.

**Remediation:** Create a non-root user and switch to it.

### 6. Unnecessary Packages and Missing Cleanup

**Severity: Medium**

- `curl` remains installed after use, increasing the attack surface (useful for an attacker who gains access).
- `apt-get` caches are not cleaned, bloating the image and leaving package metadata available.
- No `--no-install-recommends` flag, which pulls in unnecessary packages.

**Remediation:** Use `--no-install-recommends`, remove `curl` after use if not needed at runtime, and clean up apt caches.

### 7. Multiple RUN Layers

**Severity: Low**

Each `RUN` creates an image layer. Secrets or sensitive data in earlier layers persist even if removed in later ones. Consolidating commands reduces layers and attack surface.

### 8. No HEALTHCHECK Defined

**Severity: Low**

Without a `HEALTHCHECK`, the orchestrator has no way to detect if the service inside the container has become unresponsive.

### 9. No Read-Only Filesystem Consideration

**Severity: Low**

The Dockerfile does not set up the filesystem for read-only operation. Running containers with `--read-only` at deploy time limits an attacker's ability to write malicious files.

---

## Hardened Dockerfile

```dockerfile
# Pin to a specific Ubuntu version with digest for reproducibility
FROM ubuntu:24.04@sha256:b59d21599a2b151e7f6a3250a0da397f547ab9ce1d7add77adca4f1e91ba333a

# Metadata
LABEL maintainer="your-team@example.com"
LABEL description="Hardened container - example tool"

# Install only what is needed, verify downloads, clean up
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        ca-certificates \
        curl && \
    # Download a pinned version and verify integrity
    curl -fsSL -o /tmp/tool.tar.gz https://example.com/tool/v1.2.3/download && \
    echo "expected_sha256_hash_here  /tmp/tool.tar.gz" | sha256sum -c - && \
    tar -xzf /tmp/tool.tar.gz -C /usr/local/bin/ && \
    chmod 755 /usr/local/bin/tool && \
    # Remove build-time dependencies and clean up
    apt-get purge -y --auto-remove curl && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Create a non-root user
RUN groupadd -r appuser && useradd -r -g appuser -d /home/appuser -s /sbin/nologin appuser

# Drop privileges
USER appuser

# Expose only the port your application actually needs
# EXPOSE 8080

# Health check (adjust to your application's health endpoint)
# HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
#     CMD curl -f http://localhost:8080/health || exit 1

# Run the application (not sshd)
CMD ["/usr/local/bin/tool"]
```

---

## Summary of Changes

| Issue | Original | Hardened |
|---|---|---|
| Base image | `ubuntu:latest` (unpinned) | `ubuntu:24.04@sha256:...` (pinned with digest) |
| SSH server | Installed and exposed on port 22 | Removed entirely |
| Password auth | Explicitly enabled | N/A (SSH removed) |
| Remote tool install | `curl ... \| bash` (unverified) | Pinned version with SHA-256 checksum verification |
| Runtime user | root (default) | Non-root `appuser` |
| Package management | No cleanup, no `--no-install-recommends` | Cleaned caches, removed build-only deps, used `--no-install-recommends` |
| Image layers | Multiple unnecessary layers | Consolidated into minimal layers |
| Health check | None | Template provided |

## Additional Deployment Recommendations

- Run the container with `--read-only` and mount only necessary writable volumes.
- Use `--cap-drop=ALL` and add back only required capabilities.
- Apply a `seccomp` or `AppArmor` profile.
- Scan the built image with a vulnerability scanner (e.g., Trivy, Grype) in CI/CD.
- Use a smaller base image (e.g., `debian-slim` or distroless) if the application permits.
- Never store secrets in the image; use runtime secret injection (e.g., Kubernetes Secrets, Vault).
