# Fix: Docker Hub Rate Limit During `az acr build`

## Problem

When running `az acr build`, the ACR build agent pulls `nginx:1.25` directly from Docker Hub. Since ACR build agents are unauthenticated against Docker Hub, they hit the anonymous pull rate limit (100 pulls per 6 hours per IP). This results in:

```
toomanyrequests: You have reached your unauthenticated pull rate limit
```

## Solution: Import the Base Image into ACR and Reference It Locally

The fix is two steps: (1) import the nginx image into your ACR registry, and (2) update your Dockerfile to pull from ACR instead of Docker Hub.

### Step 1: Import the nginx image into your ACR

```bash
az acr import \
  --name cafehyna \
  --source docker.io/library/nginx:1.25 \
  --image nginx:1.25
```

This copies the image from Docker Hub into your `cafehyna.azurecr.io` registry. The import happens server-side through Azure's infrastructure, which has its own Docker Hub credentials and is not subject to the anonymous rate limit.

### Step 2: Update your Dockerfile

Change the `FROM` line to reference your ACR registry:

```dockerfile
# Before
FROM nginx:1.25

# After
FROM cafehyna.azurecr.io/nginx:1.25
```

Since `az acr build` runs inside the ACR registry itself, it can pull from its own registry without any additional authentication configuration. No login or credential setup is needed for this self-referencing pull.

### Step 3: Build as usual

```bash
az acr build --registry cafehyna --image myapp:latest .
```

The build agent will now pull `nginx:1.25` from `cafehyna.azurecr.io` instead of Docker Hub -- no rate limits apply.

## Keeping the Base Image Updated

The imported image is a point-in-time copy. To keep it current, you have two options:

### Option A: Scheduled Import (Recommended)

Create an ACR task that re-imports the image on a schedule:

```bash
az acr task create \
  --name import-nginx \
  --registry cafehyna \
  --cmd "az acr import --name cafehyna --source docker.io/library/nginx:1.25 --image nginx:1.25 --force" \
  --schedule "0 0 * * Mon" \
  --context /dev/null
```

This re-imports every Monday at midnight, ensuring you pick up security patches.

### Option B: Manual Re-Import

Run the `az acr import` command again with `--force` whenever you want to refresh:

```bash
az acr import \
  --name cafehyna \
  --source docker.io/library/nginx:1.25 \
  --image nginx:1.25 \
  --force
```

## Why This Works

| Approach | Pulls from Docker Hub? | Rate Limited? |
|---|---|---|
| `FROM nginx:1.25` | Yes (every build) | Yes |
| `FROM cafehyna.azurecr.io/nginx:1.25` | No (pulls from ACR) | No |
| `az acr import` | Once (server-side) | No (Azure infra) |

All subsequent builds pull entirely within ACR, eliminating Docker Hub rate limits completely.
