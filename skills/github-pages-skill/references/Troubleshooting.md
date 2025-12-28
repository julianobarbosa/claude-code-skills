# Troubleshooting Reference

Comprehensive troubleshooting guide for GitHub Pages issues.

---

## Diagnostic Commands

```bash
# Check Pages configuration
gh api repos/{owner}/{repo}/pages

# Check build status
gh api repos/{owner}/{repo}/pages/builds --jq '.[0]'

# View deployment status
gh api repos/{owner}/{repo}/deployments --jq '.[0]'

# Test site availability
curl -I https://<username>.github.io/<repo>

# Check DNS records
dig <domain> A
dig <domain> AAAA
dig www.<domain> CNAME

# View workflow logs
gh run list --workflow=pages
gh run view <run-id> --log
```

---

## Issue Categories

### 1. Site Not Publishing

**Symptoms:**
- No site at expected URL
- Repository shows no Pages deployment
- Settings shows "Your site is ready to be published"

**Possible Causes & Solutions:**

| Cause | Solution |
|-------|----------|
| Pages not enabled | Go to Settings > Pages and enable |
| Wrong publishing source | Verify branch and folder settings |
| No entry file | Add `index.html`, `index.md`, or `README.md` |
| Unverified email | Verify email in account settings |
| Using deploy key | Use machine user account instead |

**Verification:**
```bash
# Check if Pages is enabled
gh api repos/{owner}/{repo}/pages

# Check publishing source
gh api repos/{owner}/{repo}/pages --jq '.source'

# Verify entry file exists
ls -la index.html index.md README.md
```

---

### 2. 404 Errors

**Symptoms:**
- GitHub 404 page appears
- Some pages work, others don't
- Assets not loading

**Possible Causes & Solutions:**

| Cause | Solution |
|-------|----------|
| Entry file missing | Add `index.html` or `index.md` at root |
| Wrong baseurl | Set correct baseurl for project sites |
| Case sensitivity | Match exact file names (Linux is case-sensitive) |
| Jekyll excluding files | Check `_config.yml` exclude settings |
| Build failure | Check Actions tab for errors |

**For Project Sites:**
```yaml
# _config.yml
baseurl: "/repository-name"
```

**Link Format:**
```html
<!-- Wrong -->
<a href="/about">About</a>

<!-- Correct for project sites -->
<a href="{{ '/about' | relative_url }}">About</a>
```

---

### 3. Custom Domain Issues

**Symptoms:**
- Domain shows error
- Wrong site appears
- HTTPS not available
- Verification failed

#### DNS Not Propagating

**Verification:**
```bash
# Check current DNS
dig example.com +noall +answer -t A
dig www.example.com +noall +answer -t CNAME

# Check propagation globally
# Use: whatsmydns.net
```

**Solutions:**
- Wait up to 24-48 hours
- Lower TTL before making changes
- Remove conflicting records

#### CNAME File Issues

**Requirements:**
- File must be named `CNAME` (uppercase)
- Contains only the domain name
- No protocol prefix (no `https://`)
- One domain only

**Correct CNAME file:**
```
www.example.com
```

**Create/fix CNAME:**
```bash
echo "www.example.com" > CNAME
git add CNAME && git commit -m "Fix CNAME" && git push
```

#### Domain Verification

**Steps:**
1. Go to user/org Settings > Pages
2. Add domain
3. Add TXT record to DNS
4. Wait for verification

---

### 4. HTTPS Issues

**Symptoms:**
- "Enforce HTTPS" greyed out
- Certificate errors
- Mixed content warnings

**Solutions:**

**Certificate not provisioning:**
```bash
# Remove and re-add domain
gh api repos/{owner}/{repo}/pages --method PUT --field cname=''
# Wait 1 minute
gh api repos/{owner}/{repo}/pages --method PUT --field cname='example.com'
```

**CAA records blocking:**
```bash
# Check CAA records
dig example.com CAA

# Must allow letsencrypt.org or have no CAA records
# Add if needed:
# Type: CAA
# Value: 0 issue "letsencrypt.org"
```

**Mixed content:**
```bash
# Find HTTP references
grep -r "http://" --include="*.html" --include="*.md" --include="*.scss" .

# Replace with https:// or //
```

---

### 5. Build Failures

**Symptoms:**
- Deployment never completes
- Error notification email
- Red X on Actions tab

**Common Jekyll Errors:**

| Error | Cause | Solution |
|-------|-------|----------|
| `invalid byte sequence` | Encoding issue | Save files as UTF-8 |
| `undefined method` | Liquid syntax error | Check {{ }} and {% %} |
| `could not read file` | Include not found | Verify _includes/ files |
| `invalid date` | Bad date format | Use YYYY-MM-DD format |
| `found character that cannot start` | YAML error | Check _config.yml syntax |

**View build errors:**
```bash
# Via Actions
gh run list --workflow=pages --limit 5
gh run view <run-id> --log-failed

# Build locally to see errors
bundle exec jekyll build --verbose
```

**Common fixes:**

```yaml
# Fix YAML special characters
title: "My Site: A Subtitle"  # Quote strings with colons

# Escape Liquid in code blocks
{% raw %}
{{ variable }}
{% endraw %}
```

---

### 6. Changes Not Appearing

**Symptoms:**
- Pushed changes not visible
- Old content still showing
- Random caching

**Solutions:**

**Verify deployment completed:**
```bash
# Check latest build
gh api repos/{owner}/{repo}/pages/builds --jq '.[0].status'

# Check commit deployed
gh api repos/{owner}/{repo}/pages/builds --jq '.[0].commit'
```

**Clear caches:**
```bash
# Browser: Ctrl+Shift+R (Cmd+Shift+R on Mac)

# Append cache buster
# https://site.github.io/?v=timestamp

# Clear CDN (wait)
# GitHub's CDN caches for ~10 minutes
```

**Force rebuild:**
```bash
git commit --allow-empty -m "Trigger rebuild"
git push
```

---

### 7. Theme Issues

**Symptoms:**
- Unstyled content
- Wrong theme
- Custom CSS not loading

**Solutions:**

**Theme not applying:**
```yaml
# Verify exact theme name in _config.yml
theme: jekyll-theme-minimal  # Correct
theme: minimal              # Wrong (except for minima)
```

**Custom CSS not loading:**
```scss
/* assets/css/style.scss - REQUIRES front matter */
---
---

@import "{{ site.theme }}";

/* Custom styles after the import */
```

**Remote theme issues:**
```yaml
# Use correct format
remote_theme: owner/repo@version
```

---

### 8. Jekyll-Specific Issues

**Files not being processed:**
```yaml
# _config.yml - include hidden or excluded files
include:
  - .htaccess
  - _pages
```

**Files being excluded:**
Jekyll ignores by default:
- Files starting with `_`, `.`, or `#`
- Files ending with `~`
- Files in `node_modules/`, `vendor/`

**Permalinks not working:**
```yaml
# _config.yml
permalink: pretty  # Creates clean URLs

# Or in front matter
---
permalink: /custom-url/
---
```

---

### 9. Actions Workflow Issues

**Permission errors:**
```yaml
# Ensure permissions are set
permissions:
  contents: read
  pages: write
  id-token: write
```

**Artifact issues:**
```yaml
# Verify path exists
- name: Upload artifact
  uses: actions/upload-pages-artifact@v3
  with:
    path: ./build  # Must match your build output
```

**Timeout:**
```yaml
# Increase timeout (max 10 minutes for Pages)
- name: Deploy
  uses: actions/deploy-pages@v4
  with:
    timeout: 600000
```

---

## Error Messages Reference

| Error Message | Likely Cause | Solution |
|---------------|--------------|----------|
| "Page build failed" | Various build errors | Check Actions logs |
| "Your site is having problems" | Configuration error | Review _config.yml |
| "404 - File not found" | Missing entry file | Add index.html/index.md |
| "Certificate not yet available" | DNS pending | Wait up to 1 hour |
| "Domain is already taken" | Duplicate CNAME | Use unique domain |
| "Unable to build page" | Syntax error | Check Liquid/YAML syntax |
| "Symlink does not exist" | Broken symlink | Remove or fix symlinks |
| "Invalid date" | Wrong date format | Use YYYY-MM-DD |
| "Unable to parse _config.yml" | YAML syntax error | Validate YAML |

---

## When to Contact Support

Contact GitHub Support when:
- Build failures with no clear error after troubleshooting
- DNS correctly configured but domain not working after 48 hours
- HTTPS not available after 24 hours with correct setup
- Account-specific Pages limitations

**Before contacting:**
1. Document all troubleshooting steps
2. Include repository name and URLs
3. Provide `dig` output for DNS issues
4. Include build log excerpts
5. Note when the issue started

---

## Quick Fixes Checklist

- [ ] Pages enabled in Settings
- [ ] Correct publishing source (branch/folder)
- [ ] Entry file exists (index.html/index.md/README.md)
- [ ] Valid _config.yml (if using Jekyll)
- [ ] Correct baseurl for project sites
- [ ] DNS records pointing to GitHub
- [ ] No build errors in Actions tab
- [ ] Browser cache cleared
- [ ] Waited sufficient time for propagation
