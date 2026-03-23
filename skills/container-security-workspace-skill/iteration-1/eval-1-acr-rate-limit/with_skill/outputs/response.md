# Fix: Docker Hub Rate Limit During `az acr build`

## Problem

When running `az acr build`, the ACR cloud builder pulls `nginx:1.25` directly from Docker Hub. ACR cloud builds are **unauthenticated** against Docker Hub, so they share a limited anonymous pull quota. Once that quota is exhausted, you get:

```
toomanyrequests: You have reached your unauthenticated pull rate limit
```

## Solution: Import the Base Image into ACR

The fix is two steps: import the image into your ACR, then update the Dockerfile to reference the ACR copy. All subsequent builds pull from ACR internally, with no Docker Hub dependency.

### Step 1 -- Import `nginx:1.25` into ACR

```bash
az acr import --name cafehyna \
  --source docker.io/library/nginx:1.25 \
  --image base/nginx:1.25
```

This tells Azure to pull `nginx:1.25` from Docker Hub on your behalf (using Azure's infrastructure, which has its own higher-tier access) and store it as `base/nginx:1.25` inside the `cafehyna` registry.

Verify the import succeeded:

```bash
az acr repository show --name cafehyna --repository base/nginx
```

### Step 2 -- Update the Dockerfile

Change the `FROM` line to reference the ACR copy:

```dockerfile
# Before (pulls from Docker Hub -- hits rate limits in ACR cloud builds)
FROM nginx:1.25

# After (pulls from local ACR -- no rate limit)
FROM cafehyna.azurecr.io/base/nginx:1.25
```

### Step 3 -- Rebuild

```bash
az acr build --registry cafehyna --image <your-app>:<tag> -f Dockerfile .
```

The build now pulls `nginx:1.25` from ACR itself, so there is no Docker Hub request and no rate limit.

## Why This Works

- `az acr import` uses Azure-side networking to fetch the image. It is not subject to the same anonymous rate limits as ACR cloud builds.
- Once the image is stored in your registry, `az acr build` resolves `cafehyna.azurecr.io/base/nginx:1.25` internally with no external pull at all.

## If `az acr import` Itself Hits Rate Limits

Under heavy burst imports, even `az acr import` can occasionally be rate-limited. If that happens, authenticate with a Docker Hub account:

```bash
az acr import --name cafehyna \
  --source docker.io/library/nginx:1.25 \
  --image base/nginx:1.25 \
  --username <dockerhub-user> --password <dockerhub-token>
```

Or simply wait 15 minutes for the rate limit window to reset and retry.

## Best Practice Going Forward

Apply this pattern to **every** public base image referenced in your Dockerfiles:

1. Import the pinned image into ACR under a logical path (e.g., `base/`, `tools/`).
2. Update the `FROM` line to `cafehyna.azurecr.io/<path>:<pinned-tag>`.
3. Avoid `:latest` tags -- always pin to a specific version for reproducibility and auditability.

This eliminates Docker Hub as a runtime dependency for all ACR cloud builds.
