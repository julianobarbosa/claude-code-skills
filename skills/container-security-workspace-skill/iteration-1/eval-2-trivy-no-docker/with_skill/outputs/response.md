# Scanning a Container Image Without a Local Docker Daemon

Since Docker is not running locally, you cannot use `trivy image` directly (Option B in the workflow) because it requires a Docker daemon to pull the image. However, you have two viable alternatives that do not require a local Docker installation at all.

## Recommended: Trivy via ACR Task (Option A)

This approach runs Trivy entirely in the cloud using Azure Container Registry Tasks. ACR pulls and scans the image on its own infrastructure -- no local Docker needed.

### One-time setup: Import Trivy into your ACR

If you have not already imported the Trivy scanner image into your registry, do so first:

```bash
az acr import --name cafehyna \
  --source docker.io/aquasec/trivy:latest \
  --image tools/trivy:latest
```

### Run the scan (human-readable table output)

```bash
az acr run --registry cafehyna \
  --cmd "cafehyna.azurecr.io/tools/trivy:latest image \
    --severity HIGH,CRITICAL \
    cafehyna.azurecr.io/apps/myapp:2.0.0" /dev/null
```

### Run the scan (JSON output for programmatic analysis)

```bash
az acr run --registry cafehyna \
  --cmd "cafehyna.azurecr.io/tools/trivy:latest image \
    --severity HIGH,CRITICAL --format json \
    cafehyna.azurecr.io/apps/myapp:2.0.0" /dev/null
```

## How This Works

`az acr run` executes a container task inside Azure's infrastructure. By pointing it at the Trivy image already stored in your ACR, it:

1. Pulls the Trivy scanner from `cafehyna.azurecr.io/tools/trivy:latest`.
2. Runs `trivy image` against `cafehyna.azurecr.io/apps/myapp:2.0.0`.
3. Since both images are in the same ACR, there are no authentication or network issues -- the scan happens entirely within Azure.

The `/dev/null` at the end is required by `az acr run` as a source argument (it expects a build context), but since we are only running a command, we pass `/dev/null` as a no-op.

## Analyzing the Results

Once you have the scan output, categorize the findings:

| Category | Action | Example |
|----------|--------|---------|
| **Fixable by us** | Pin a newer version in the Dockerfile | Tool binary built with an old Go stdlib |
| **Fixable upstream** | Track, document, revisit later | Base image ships a vulnerable internal dep |
| **OS-level, patch pending** | Document, monitor Debian/Ubuntu tracker | libsqlite3, openssl |
| **will_not_fix** | Accept risk or find an alternative package | zlib1g in Debian |

For JSON output, you can extract a CRITICAL summary with:

```python
import json
data = json.load(open('trivy-results.json'))
for result in data.get('Results', []):
    for v in result.get('Vulnerabilities', []):
        if v.get('Severity') == 'CRITICAL':
            print(f"{v['VulnerabilityID']} | {v['PkgName']} {v.get('InstalledVersion','')} | fix: {v.get('FixedVersion','')} | {v.get('Status','')}")
```

## Alternative: Scan a Local Dockerfile (No Image Pull Needed)

If you also have the Dockerfile for this image locally, you can scan the Dockerfile configuration itself (not the built image) without Docker:

```bash
trivy config --severity HIGH,CRITICAL,MEDIUM Dockerfile
```

This checks for Dockerfile misconfigurations (unpinned versions, running as root, etc.) but does not scan the actual image contents for CVEs. Use this as a complement, not a replacement, for the ACR-based image scan above.

## Next Steps After Scanning

1. Review CRITICAL and HIGH findings from the scan output.
2. Harden the Dockerfile based on findings (pin versions, use non-root user, clean caches).
3. Rebuild the image: `az acr build --registry cafehyna --image apps/myapp:2.0.1 -f Dockerfile .`
4. Re-scan the new image to verify the fix reduced the vulnerability count.
