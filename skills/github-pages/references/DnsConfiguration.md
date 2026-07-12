# DNS Configuration Reference

Complete DNS configuration guide for GitHub Pages custom domains.

---

## Overview

GitHub Pages supports three types of custom domains:
1. **Apex domains** (bare/root): `example.com`
2. **WWW subdomains**: `www.example.com`
3. **Custom subdomains**: `blog.example.com`, `docs.example.com`

**Recommendation:** Always configure BOTH apex AND www subdomain for automatic redirects.

---

## DNS Record Types

### A Records (IPv4)

Used for apex domains. Point directly to GitHub's IP addresses.

```
Type: A
Host: @ (or leave blank)
TTL: 3600 (or 1 hour)

Values (add ALL four):
185.199.108.153
185.199.109.153
185.199.110.153
185.199.111.153
```

### AAAA Records (IPv6)

Optional but recommended for IPv6 support.

```
Type: AAAA
Host: @ (or leave blank)
TTL: 3600

Values (add ALL four):
2606:50c0:8000::153
2606:50c0:8001::153
2606:50c0:8002::153
2606:50c0:8003::153
```

### CNAME Records

Used for subdomains. Point to your GitHub Pages URL.

```
Type: CNAME
Host: www (or your subdomain)
TTL: 3600

Value: <username>.github.io.
```

**Note:** The trailing dot (`.`) is standard DNS notation and may or may not be required by your DNS provider.

### ALIAS/ANAME Records

Alternative to A records for apex domains (if your DNS provider supports it).

```
Type: ALIAS (or ANAME)
Host: @ (or leave blank)
TTL: 3600

Value: <username>.github.io.
```

---

## Configuration by Domain Type

### Apex Domain Only

```
example.com → A records pointing to GitHub IPs
```

**DNS Records:**
| Type | Host | Value |
|------|------|-------|
| A | @ | 185.199.108.153 |
| A | @ | 185.199.109.153 |
| A | @ | 185.199.110.153 |
| A | @ | 185.199.111.153 |

### WWW Subdomain Only

```
www.example.com → CNAME to username.github.io
```

**DNS Records:**
| Type | Host | Value |
|------|------|-------|
| CNAME | www | username.github.io |

### Both Apex and WWW (Recommended)

```
example.com → A records to GitHub IPs
www.example.com → CNAME to username.github.io
```

**DNS Records:**
| Type | Host | Value |
|------|------|-------|
| A | @ | 185.199.108.153 |
| A | @ | 185.199.109.153 |
| A | @ | 185.199.110.153 |
| A | @ | 185.199.111.153 |
| CNAME | www | username.github.io |

**Behavior:** GitHub automatically redirects between apex and www based on which is configured in Pages settings.

### Custom Subdomain

```
blog.example.com → CNAME to username.github.io
```

**DNS Records:**
| Type | Host | Value |
|------|------|-------|
| CNAME | blog | username.github.io |

---

## DNS Provider Examples

### Cloudflare

1. Log into Cloudflare dashboard
2. Select your domain
3. Go to DNS tab
4. Click "Add record"

For apex domain:
- Type: A
- Name: @
- IPv4 address: 185.199.108.153
- Proxy status: DNS only (gray cloud) recommended initially
- TTL: Auto

For www:
- Type: CNAME
- Name: www
- Target: username.github.io
- Proxy status: DNS only recommended initially

### Namecheap

1. Log into Namecheap
2. Domain List > Manage
3. Advanced DNS tab

For apex domain:
- Type: A Record
- Host: @
- Value: 185.199.108.153
- TTL: Automatic

For www:
- Type: CNAME Record
- Host: www
- Value: username.github.io.
- TTL: Automatic

### GoDaddy

1. Log into GoDaddy
2. My Products > DNS
3. Add record

For apex domain:
- Type: A
- Name: @
- Value: 185.199.108.153
- TTL: 1 Hour

For www:
- Type: CNAME
- Name: www
- Value: username.github.io
- TTL: 1 Hour

### Google Domains / Squarespace Domains

1. Log into Google Domains
2. DNS tab
3. Manage custom records

For apex domain:
- Host name: (leave blank)
- Type: A
- TTL: 1H
- Data: 185.199.108.153

For www:
- Host name: www
- Type: CNAME
- TTL: 1H
- Data: username.github.io.

---

## Verification Commands

### Check A Records

```bash
dig example.com +noall +answer -t A
```

**Expected output:**
```
example.com.        3600    IN      A       185.199.108.153
example.com.        3600    IN      A       185.199.109.153
example.com.        3600    IN      A       185.199.110.153
example.com.        3600    IN      A       185.199.111.153
```

### Check AAAA Records

```bash
dig example.com +noall +answer -t AAAA
```

**Expected output:**
```
example.com.        3600    IN      AAAA    2606:50c0:8000::153
example.com.        3600    IN      AAAA    2606:50c0:8001::153
example.com.        3600    IN      AAAA    2606:50c0:8002::153
example.com.        3600    IN      AAAA    2606:50c0:8003::153
```

### Check CNAME Records

```bash
dig www.example.com +noall +answer -t CNAME
```

**Expected output:**
```
www.example.com.    3600    IN      CNAME   username.github.io.
```

### Check All Records for Domain

```bash
dig example.com ANY +noall +answer
```

### Check Global Propagation

Use online tools:
- https://www.whatsmydns.net/
- https://dnschecker.org/

---

## CAA Records (HTTPS Certificates)

For HTTPS to work, Let's Encrypt must be able to issue certificates.

**If you have CAA records configured:**

Ensure at least one allows Let's Encrypt:

```
Type: CAA
Host: @
Value: 0 issue "letsencrypt.org"
```

**Check existing CAA records:**

```bash
dig example.com CAA
```

**If no CAA records exist:** Let's Encrypt can issue certificates (default behavior).

---

## Common Issues

### DNS Not Propagating

**Causes:**
- TTL from previous records not expired
- Caching at various DNS levels
- Wrong DNS server being queried

**Solutions:**
- Wait up to 24-48 hours
- Use `dig @8.8.8.8 example.com A` to query Google DNS directly
- Lower TTL before making changes, then change

### Conflicting Records

**Problem:** Old records conflicting with new GitHub Pages records.

**Solution:** Remove these before adding GitHub Pages records:
- Old A records
- Old AAAA records
- Old CNAME for @
- Wildcard records

### Wildcard Records Warning

**Never use wildcard DNS records for GitHub Pages:**

```
# DO NOT DO THIS
*.example.com → anything
```

**Risk:** Creates domain takeover vulnerability. Attackers can claim any unused subdomain.

### Wrong Record Type

**Problem:** Using CNAME for apex domain.

**Solution:** Most DNS providers don't allow CNAME on apex. Use A records or ALIAS/ANAME if supported.

### Missing Trailing Dot

**Problem:** CNAME value without trailing dot.

**Note:** Some providers require `username.github.io.` (with dot), others require `username.github.io` (without). Check your provider's documentation.

---

## Security Considerations

1. **Verify domain ownership** in GitHub before adding DNS records
2. **Remove DNS records** if disabling GitHub Pages
3. **Monitor for unauthorized changes** to DNS records
4. **Avoid wildcard records** - security risk
5. **Use DNSSEC** if available from your registrar

---

## Quick Reference Table

| Domain Type | Record Type | Host | Value |
|-------------|-------------|------|-------|
| Apex | A | @ | 185.199.108.153 |
| Apex | A | @ | 185.199.109.153 |
| Apex | A | @ | 185.199.110.153 |
| Apex | A | @ | 185.199.111.153 |
| Apex (IPv6) | AAAA | @ | 2606:50c0:8000::153 |
| Apex (IPv6) | AAAA | @ | 2606:50c0:8001::153 |
| Apex (IPv6) | AAAA | @ | 2606:50c0:8002::153 |
| Apex (IPv6) | AAAA | @ | 2606:50c0:8003::153 |
| WWW | CNAME | www | username.github.io |
| Custom Sub | CNAME | blog | username.github.io |
| Apex (alt) | ALIAS | @ | username.github.io |
