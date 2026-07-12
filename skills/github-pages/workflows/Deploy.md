# Deploy Workflow

Deploy changes to GitHub Pages.

## Checklist

- [ ] Verify local changes
- [ ] Test locally (optional)
- [ ] Commit and push
- [ ] Monitor deployment
- [ ] Verify live site

---

## Quick Deploy

### Standard Deployment (Branch-based)

```bash
# Stage changes
git add .

# Commit
git commit -m "Update site content"

# Push to trigger deployment
git push origin main
```

### Force Rebuild

```bash
# Empty commit to trigger rebuild
git commit --allow-empty -m "Trigger Pages rebuild"
git push
```

---

## Pre-Deploy Checklist

### 1. Verify Changes Locally

```bash
# Check what will be committed
git status
git diff --staged

# Review file changes
git diff HEAD
```

### 2. Test Jekyll Build (If Applicable)

```bash
# Install dependencies
bundle install

# Build and serve locally
bundle exec jekyll serve

# Visit http://localhost:4000
```

### 3. Check for Common Issues

```bash
# Check for broken links (if using htmlproofer)
bundle exec htmlproofer ./_site

# Validate HTML
bundle exec jekyll build
# Then check _site/ output

# Check for large files
find . -type f -size +10M

# Check for sensitive data
git diff --staged | grep -E "(password|secret|api.?key|token)" -i
```

---

## Deployment Methods

### Method 1: Push to Branch

**When:** Publishing source is set to "Deploy from branch"

```bash
# Ensure you're on the correct branch
git checkout main  # or gh-pages

# Push changes
git push origin main
```

**What happens:**
1. Push triggers GitHub Pages build
2. Jekyll processes files (unless .nojekyll exists)
3. Site deploys automatically
4. Takes up to 10 minutes

### Method 2: GitHub Actions

**When:** Publishing source is set to "GitHub Actions"

```bash
# Push changes to trigger workflow
git push origin main

# Or manually trigger workflow
gh workflow run deploy-pages.yml
```

**What happens:**
1. Push triggers workflow
2. Workflow runs build steps
3. Artifacts uploaded
4. Deploy action publishes site

### Method 3: Manual Trigger

```bash
# Trigger workflow manually
gh workflow run deploy-pages.yml --ref main

# Or via API
gh api repos/{owner}/{repo}/actions/workflows/deploy-pages.yml/dispatches \
  --method POST \
  --field ref=main
```

---

## Monitor Deployment

### Check Build Status

```bash
# For branch deployment
gh api repos/{owner}/{repo}/pages/builds --jq '.[0]'

# For Actions deployment
gh run list --workflow=pages --limit 1

# Watch deployment in real-time
gh run watch
```

### View Logs

```bash
# List recent runs
gh run list --workflow=pages

# View specific run logs
gh run view <run-id> --log

# View failed step
gh run view <run-id> --log-failed
```

---

## Verify Deployment

### 1. Check Site is Live

```bash
# Test site responds
curl -I https://<username>.github.io/<repo>

# Check for correct content
curl -s https://<username>.github.io/<repo> | head -50
```

### 2. Verify Specific Changes

```bash
# Check specific page
curl -s https://<username>.github.io/<repo>/new-page/

# Check assets load
curl -I https://<username>.github.io/<repo>/assets/css/style.css
```

### 3. Clear Cache and Test

```bash
# Append cache-busting parameter
curl -s "https://<username>.github.io/<repo>?nocache=$(date +%s)"
```

---

## Rollback

### Quick Rollback

```bash
# Revert last commit
git revert HEAD
git push origin main
```

### Rollback to Specific Commit

```bash
# Find the commit to rollback to
git log --oneline -10

# Reset to that commit (creates new commit)
git revert --no-commit HEAD~3..HEAD
git commit -m "Rollback to previous version"
git push origin main
```

### Emergency Rollback

```bash
# Force push to previous known good state
# WARNING: This rewrites history
git reset --hard <good-commit-sha>
git push --force origin main
```

---

## Deploy to Specific Environment

### Staging (Preview)

Use pull request previews or separate branch:

```bash
# Create staging branch
git checkout -b staging
git push origin staging

# Configure Pages for staging branch
# Or use PR preview feature if available
```

### Production

```bash
# Merge to main for production
git checkout main
git merge staging
git push origin main
```

---

## Deployment Best Practices

### Before Deploy

1. **Test locally** - Run `bundle exec jekyll serve`
2. **Check links** - Verify internal links work
3. **Validate HTML** - Ensure valid markup
4. **Review diff** - Check staged changes
5. **No secrets** - Verify no sensitive data

### During Deploy

1. **Monitor build** - Watch for errors
2. **Set expectations** - Up to 10 minutes
3. **Don't spam pushes** - Rate limit: 10 builds/hour

### After Deploy

1. **Verify live site** - Check changes appear
2. **Test critical paths** - Navigation, links, forms
3. **Check mobile** - Responsive design
4. **Monitor errors** - Check browser console

---

## Automation Tips

### Deploy on Schedule

```yaml
# .github/workflows/scheduled-deploy.yml
name: Scheduled Deploy

on:
  schedule:
    - cron: '0 0 * * *'  # Daily at midnight
  workflow_dispatch:

jobs:
  deploy:
    # ... deployment steps
```

### Deploy Only on Tag

```yaml
on:
  push:
    tags:
      - 'v*'
```

### Deploy with Approval

```yaml
jobs:
  deploy:
    environment: production  # Requires approval if configured
```

---

## Quick Reference

| Command | Purpose |
|---------|---------|
| `git push origin main` | Deploy changes |
| `gh run list --workflow=pages` | Check deployment status |
| `gh run watch` | Monitor deployment live |
| `curl -I <site-url>` | Verify site is up |
| `git revert HEAD && git push` | Rollback last change |
