# QuickStart Workflow

Setup a new GitHub Pages site from scratch.

## Checklist

- [ ] Determine site type (user/org vs project)
- [ ] Verify repository name requirements
- [ ] Choose publishing source
- [ ] Create initial content
- [ ] Enable GitHub Pages
- [ ] Verify deployment

---

## Step 1: Determine Site Type

**Ask the user:**
- Is this for a personal/organization homepage? → User/Org Site
- Is this for a specific project? → Project Site

### User/Organization Site

**Requirements:**
```
Repository name: <username>.github.io
URL: https://<username>.github.io
Limit: ONE per account
```

**Create repository:**
```bash
# Via GitHub CLI
gh repo create <username>.github.io --public --description "My personal site"

# Or via web interface at github.com/new
```

### Project Site

**Requirements:**
```
Repository name: any-name
URL: https://<username>.github.io/<repo-name>
Limit: One per repository
```

---

## Step 2: Choose Publishing Source

### Option A: Deploy from Branch (Recommended for Jekyll)

1. Create content in repository root or `/docs` folder
2. Go to Settings > Pages
3. Select "Deploy from a branch"
4. Choose branch and folder

**Supported folders:**
- `/` (root) - Most common
- `/docs` - Useful for project documentation

### Option B: GitHub Actions (Custom Builds)

1. Go to Settings > Pages
2. Select "GitHub Actions"
3. Create workflow file (see ActionsWorkflow.md)

---

## Step 3: Create Initial Content

### Minimal Setup

Create `index.html`:
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>My Site</title>
</head>
<body>
    <h1>Welcome to My Site</h1>
    <p>This site is hosted on GitHub Pages.</p>
</body>
</html>
```

### Jekyll Setup (Markdown)

Create `index.md`:
```markdown
---
layout: default
title: Home
---

# Welcome to My Site

This site is hosted on GitHub Pages.
```

Create `_config.yml`:
```yaml
theme: jekyll-theme-minimal
title: My Site
description: A GitHub Pages site
```

---

## Step 4: Enable GitHub Pages

```bash
# Via GitHub CLI
gh api repos/{owner}/{repo}/pages \
  --method POST \
  --field source='{"branch":"main","path":"/"}'

# Or manually via Settings > Pages
```

---

## Step 5: Verify Deployment

1. Check deployment status in Actions tab
2. Wait up to 10 minutes for initial deployment
3. Visit your site URL

**Verification commands:**
```bash
# Check if site is responding
curl -I https://<username>.github.io

# Check deployment status via API
gh api repos/{owner}/{repo}/pages
```

---

## Troubleshooting

**Site not appearing:**
- Verify Pages is enabled in Settings
- Check Actions tab for build errors
- Ensure entry file exists (index.html, index.md, or README.md)

**404 Error:**
- Check publishing source configuration
- Verify files are in correct folder
- Wait a few minutes and clear browser cache

---

## Next Steps

- Add custom domain (CustomDomain.md)
- Configure Jekyll theme (JekyllSetup.md)
- Setup custom build process (ActionsWorkflow.md)
