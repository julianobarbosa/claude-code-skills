# Troubleshoot Workflow

Diagnose and fix common GitHub Pages issues.

## Checklist

- [ ] Identify the symptom
- [ ] Check build status
- [ ] Verify configuration
- [ ] Apply fix
- [ ] Confirm resolution

---

## Quick Diagnosis

### Check Build Status

```bash
# Via GitHub CLI
gh api repos/{owner}/{repo}/pages

# Check recent deployments
gh api repos/{owner}/{repo}/deployments --jq '.[0:5]'

# View workflow runs (if using Actions)
gh run list --workflow=pages
```

### Check Site Status

```bash
# Test if site responds
curl -I https://<username>.github.io/<repo>

# Check for redirects
curl -ILs https://<username>.github.io/<repo> | grep -i location
```

---

## Common Issues

### Issue: Site Not Publishing

**Symptoms:**
- No site at expected URL
- 404 error on site URL

**Diagnosis:**
1. Is Pages enabled? Check Settings > Pages
2. Is there an entry file? (index.html, index.md, or README.md)
3. Is the publishing source correct?
4. Are there build errors?

**Solutions:**

```bash
# Verify Pages is enabled
gh api repos/{owner}/{repo}/pages

# Check if entry file exists
ls -la index.html index.md README.md 2>/dev/null

# Check publishing source settings
gh api repos/{owner}/{repo}/pages --jq '.source'
```

---

### Issue: 404 Error

**Symptoms:**
- Site shows GitHub 404 page
- Only some pages return 404

**Diagnosis:**
1. Entry file at correct location?
2. Correct base URL for links?
3. Case-sensitive file names?
4. Jekyll build excluding files?

**Solutions:**

For root path 404:
```bash
# Ensure entry file exists at publishing source
# For root: ./index.html or ./index.md
# For /docs: ./docs/index.html or ./docs/index.md
```

For broken links:
```yaml
# In _config.yml for project sites
baseurl: "/repository-name"
```

For Jekyll excluding files:
```yaml
# In _config.yml, check include/exclude settings
include:
  - _pages
  - important-file.md
```

---

### Issue: Custom Domain Not Working

**Symptoms:**
- Domain shows error or wrong site
- HTTPS not available
- Domain verification failed

**Diagnosis:**
1. DNS records correct?
2. CNAME file present?
3. DNS propagated?
4. Domain verified?

**Solutions:**

Check DNS:
```bash
# For apex domain
dig example.com +noall +answer -t A

# Expected IPs:
# 185.199.108.153
# 185.199.109.153
# 185.199.110.153
# 185.199.111.153

# For subdomain
dig www.example.com +noall +answer -t CNAME

# Expected: username.github.io
```

Fix CNAME file:
```bash
# CNAME file must be uppercase
# Contains only the domain, nothing else
echo "www.example.com" > CNAME
git add CNAME && git commit -m "Add CNAME" && git push
```

Wait for propagation:
- DNS changes take up to 24 hours
- HTTPS takes up to 1 hour after DNS verification

---

### Issue: HTTPS Not Available

**Symptoms:**
- "Enforce HTTPS" checkbox disabled
- Certificate errors
- Mixed content warnings

**Diagnosis:**
1. DNS fully propagated?
2. CAA records blocking?
3. Domain recently changed?

**Solutions:**

Wait and retry:
```bash
# Remove and re-add custom domain to trigger new certificate
gh api repos/{owner}/{repo}/pages \
  --method PUT --field cname=''

# Wait a minute, then re-add
gh api repos/{owner}/{repo}/pages \
  --method PUT --field cname='www.example.com'
```

Check CAA records:
```bash
dig example.com CAA

# Must include or not block: letsencrypt.org
```

Fix mixed content:
```bash
# Search for http:// in your files
grep -r "http://" --include="*.html" --include="*.md" --include="*.scss"

# Replace with https:// or protocol-relative //
```

---

### Issue: Build Failures

**Symptoms:**
- Deployment never completes
- Error emails from GitHub
- Build status shows failure

**Diagnosis:**
1. Check Actions tab for logs
2. Check email for error message
3. Test local build

**Solutions:**

View build logs:
```bash
# List recent workflow runs
gh run list --workflow=pages --limit 5

# View specific run
gh run view <run-id> --log
```

Common build errors:

**Liquid syntax error:**
```
# Escape Liquid tags in code blocks
{% raw %}
{{ variable }}
{% endraw %}
```

**Invalid YAML:**
```yaml
# Check for:
# - Inconsistent indentation
# - Missing quotes around special characters
# - Tab characters (use spaces)
```

**Missing dependencies:**
```ruby
# In Gemfile, ensure github-pages gem is included
source "https://rubygems.org"
gem "github-pages", group: :jekyll_plugins
```

---

### Issue: Changes Not Appearing

**Symptoms:**
- Pushed changes not visible
- Old content still showing
- Cache issues

**Diagnosis:**
1. Was push successful?
2. Did build complete?
3. Browser cache?
4. CDN cache?

**Solutions:**

Verify push and build:
```bash
# Check last commit
git log -1

# Check if deployed
gh api repos/{owner}/{repo}/pages/builds --jq '.[0]'
```

Clear caches:
```bash
# Force browser refresh
# Chrome/Firefox: Ctrl+Shift+R (Cmd+Shift+R on Mac)

# Or append query string
# https://site.github.io/?v=2
```

Force rebuild:
```bash
# Empty commit to trigger rebuild
git commit --allow-empty -m "Trigger rebuild"
git push
```

---

### Issue: Theme Not Applying

**Symptoms:**
- Site shows unstyled content
- Wrong theme appearing
- Custom CSS not loading

**Diagnosis:**
1. Theme name correct in _config.yml?
2. Theme supported by GitHub Pages?
3. Custom CSS file has front matter?

**Solutions:**

Verify theme configuration:
```yaml
# _config.yml - use exact theme name
theme: jekyll-theme-minimal

# Or for remote themes
remote_theme: pages-themes/minimal@v0.2.0
```

Fix custom CSS:
```scss
/* assets/css/style.scss - MUST have front matter */
---
---

@import "{{ site.theme }}";

/* Custom styles below */
```

---

## Diagnostic Commands Reference

```bash
# Check Pages configuration
gh api repos/{owner}/{repo}/pages

# Check build status
gh api repos/{owner}/{repo}/pages/builds

# View deployment history
gh api repos/{owner}/{repo}/deployments

# Test site response
curl -IL https://<username>.github.io/<repo>

# Check DNS records
dig <domain> A
dig <domain> AAAA
dig www.<domain> CNAME

# View workflow logs
gh run list --workflow=pages
gh run view <run-id> --log

# Test local Jekyll build
bundle exec jekyll build --verbose
```

---

## When to Contact GitHub Support

Contact support if:
- Build failures with no clear error
- DNS correctly configured but domain not working after 48 hours
- HTTPS not available after 24 hours despite correct setup
- Account-specific Pages issues

Before contacting:
1. Document all troubleshooting steps taken
2. Include repository name and URLs
3. Provide dig output for DNS issues
4. Include build log excerpts for build failures
