# CustomDomain Workflow

Configure a custom domain for GitHub Pages.

## Checklist

- [ ] Determine domain type (apex vs subdomain)
- [ ] Verify domain ownership
- [ ] Configure DNS records
- [ ] Add custom domain in GitHub
- [ ] Wait for DNS propagation
- [ ] Enable HTTPS

---

## Step 1: Determine Domain Type

| Type | Example | Best For |
|------|---------|----------|
| WWW Subdomain | `www.example.com` | Most stable, recommended |
| Custom Subdomain | `blog.example.com` | Project sites |
| Apex Domain | `example.com` | Brand consistency |

**Best Practice:** Configure BOTH apex and www subdomain. GitHub auto-redirects between them.

---

## Step 2: Verify Domain (Recommended)

Prevent domain takeover by verifying ownership:

1. Go to user/org Settings > Pages
2. Click "Add a domain"
3. Enter your domain
4. Add the TXT record to your DNS
5. Click "Verify"

---

## Step 3: Configure DNS Records

### For WWW Subdomain (Recommended)

**DNS Provider Configuration:**
```
Type: CNAME
Host: www
Value: <username>.github.io
TTL: 3600 (or default)
```

### For Custom Subdomain

**DNS Provider Configuration:**
```
Type: CNAME
Host: blog (or your subdomain)
Value: <username>.github.io
TTL: 3600 (or default)
```

### For Apex Domain

**Option A: A Records (IPv4)**
```
Type: A
Host: @ (or blank)
Values:
  185.199.108.153
  185.199.109.153
  185.199.110.153
  185.199.111.153
TTL: 3600
```

**Option B: AAAA Records (IPv6)**
```
Type: AAAA
Host: @ (or blank)
Values:
  2606:50c0:8000::153
  2606:50c0:8001::153
  2606:50c0:8002::153
  2606:50c0:8003::153
TTL: 3600
```

**Option C: ALIAS/ANAME Record (If supported)**
```
Type: ALIAS or ANAME
Host: @ (or blank)
Value: <username>.github.io
TTL: 3600
```

---

## Step 4: Add Custom Domain in GitHub

### Via GitHub CLI

```bash
# Add custom domain
gh api repos/{owner}/{repo}/pages \
  --method PUT \
  --field cname='www.example.com'
```

### Via Web Interface

1. Go to repository Settings > Pages
2. Under "Custom domain", enter your domain
3. Click "Save"

**Note:** This creates a CNAME file in your repository (when using branch deploy).

---

## Step 5: Verify DNS Configuration

### Check A Records
```bash
dig example.com +noall +answer -t A
```

**Expected output:**
```
example.com.    3600    IN    A    185.199.108.153
example.com.    3600    IN    A    185.199.109.153
example.com.    3600    IN    A    185.199.110.153
example.com.    3600    IN    A    185.199.111.153
```

### Check CNAME Records
```bash
dig www.example.com +nostats +nocomments +nocmd
```

**Expected output:**
```
www.example.com.    3600    IN    CNAME    username.github.io.
```

---

## Step 6: Enable HTTPS

1. Wait for DNS to propagate (up to 24 hours)
2. Wait for SSL certificate (up to 1 hour after DNS verified)
3. Go to Settings > Pages
4. Check "Enforce HTTPS"

**Certificate Requirements:**
- Must have CAA record allowing `letsencrypt.org` OR no CAA records
- DNS must point to GitHub Pages IPs

---

## Common Issues

### DNS Not Propagating

**Solution:**
- Wait up to 24 hours
- Check for conflicting records
- Remove any wildcard records

### HTTPS Not Available

**Solution:**
- Verify DNS is correctly configured
- Wait up to 1 hour after DNS check passes
- Try removing and re-adding domain

### Certificate Errors

**Solution:**
- Check CAA records don't block Let's Encrypt
- Ensure no conflicting SSL configurations
- Contact domain registrar if CAA issues persist

---

## Security Considerations

1. **Always verify domain** before adding to prevent takeover
2. **Never use wildcard DNS** (`*.example.com`) - security risk
3. **Update DNS immediately** if disabling site
4. **Monitor for unauthorized changes** to DNS records

---

## Reference Commands

```bash
# Check current Pages configuration
gh api repos/{owner}/{repo}/pages

# Remove custom domain
gh api repos/{owner}/{repo}/pages \
  --method PUT \
  --field cname=''

# Check DNS propagation globally
# Use online tools like: whatsmydns.net
```
