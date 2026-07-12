# Best Practices Reference

Recommended practices for GitHub Pages sites.

---

## Site Setup

### Choose the Right Publishing Source

| Use Case | Recommended Source |
|----------|-------------------|
| Simple static HTML | Branch (root) |
| Jekyll blog | Branch (root) |
| Documentation in repo | Branch (/docs) |
| Custom build (Hugo, Next.js) | GitHub Actions |
| Non-Jekyll generator | GitHub Actions |

### Repository Structure

**For Branch Deployment:**
```
.
├── index.html          # or index.md
├── _config.yml         # Jekyll config
├── assets/
│   ├── css/
│   ├── images/
│   └── js/
├── _posts/             # Blog posts
├── _layouts/           # Custom layouts
├── _includes/          # Partials
└── CNAME               # Custom domain (if used)
```

**For Actions Deployment:**
```
.
├── src/                # Source files
├── public/             # Static assets
├── .github/
│   └── workflows/
│       └── deploy.yml  # Deployment workflow
├── package.json        # Dependencies
└── .nojekyll           # Skip Jekyll processing
```

---

## Security

### Domain Security

1. **Always verify domains** before adding to prevent takeover attacks
2. **Never use wildcard DNS** (`*.example.com`) - creates security risk
3. **Update DNS immediately** when disabling Pages
4. **Monitor domain records** for unauthorized changes

### Content Security

1. **Never commit secrets** - API keys, passwords, tokens
2. **Use .gitignore** for sensitive files
3. **Remember: public sites from private repos** - Private repos can have public Pages

```gitignore
# .gitignore
.env
.env.local
*.pem
secrets/
```

### HTTPS

1. **Always enable HTTPS** after certificate provisioning
2. **Fix mixed content** - No HTTP resources on HTTPS sites
3. **Use protocol-relative URLs** when possible: `//example.com/resource`

---

## Performance

### Keep Sites Small

| Resource | Recommended Limit |
|----------|------------------|
| Repository size | < 1 GB |
| Site size | < 1 GB |
| Individual files | < 100 MB |
| Total images | Optimize before upload |

### Optimize Assets

**Images:**
```bash
# Compress images before upload
# Use WebP format when possible
# Implement lazy loading

<img loading="lazy" src="image.webp" alt="Description">
```

**CSS/JS:**
```yaml
# Jekyll: Use Sass compression
sass:
  style: compressed
```

**Fonts:**
- Use system fonts when possible
- Subset custom fonts
- Use `font-display: swap`

### Caching Strategy

GitHub Pages sets these cache headers:
- Static assets: 10 minutes
- HTML: Short cache with revalidation

**Cache busting for updates:**
```html
<link rel="stylesheet" href="/assets/css/style.css?v=1.0.0">
```

---

## SEO

### Essential Meta Tags

```html
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{{ page.title }} | {{ site.title }}</title>
  <meta name="description" content="{{ page.description | default: site.description }}">

  <!-- Open Graph -->
  <meta property="og:title" content="{{ page.title }}">
  <meta property="og:description" content="{{ page.description }}">
  <meta property="og:image" content="{{ page.image | absolute_url }}">

  <!-- Twitter Card -->
  <meta name="twitter:card" content="summary_large_image">
</head>
```

### Use Jekyll SEO Tag Plugin

```yaml
# _config.yml
plugins:
  - jekyll-seo-tag
```

```html
<!-- In layout -->
{% seo %}
```

### Sitemap

```yaml
# _config.yml
plugins:
  - jekyll-sitemap
```

Automatically generates `/sitemap.xml`.

### Canonical URLs

```html
<link rel="canonical" href="{{ page.url | absolute_url }}">
```

---

## Accessibility

### Semantic HTML

```html
<header>...</header>
<nav>...</nav>
<main>
  <article>...</article>
  <aside>...</aside>
</main>
<footer>...</footer>
```

### Alt Text

```markdown
![Descriptive alt text for screen readers](image.jpg)
```

### Color Contrast

- Text: minimum 4.5:1 contrast ratio
- Large text: minimum 3:1 contrast ratio
- Use tools like WebAIM Contrast Checker

### Keyboard Navigation

```html
<a href="#main-content" class="skip-link">Skip to content</a>
```

---

## Content Organization

### URL Structure

```yaml
# Clean URLs
permalink: pretty

# Custom permalinks
permalink: /:categories/:title/
```

**Good URL examples:**
- `/about/`
- `/blog/2024/my-post/`
- `/docs/getting-started/`

**Avoid:**
- `/about.html`
- `/page1/`
- `/2024/01/15/my-post.html`

### Navigation

```yaml
# _data/navigation.yml
main:
  - title: Home
    url: /
  - title: Blog
    url: /blog/
  - title: About
    url: /about/
```

```html
<nav>
  {% for item in site.data.navigation.main %}
    <a href="{{ item.url }}" {% if page.url == item.url %}aria-current="page"{% endif %}>
      {{ item.title }}
    </a>
  {% endfor %}
</nav>
```

---

## Development Workflow

### Local Development

```bash
# Always test locally before pushing
bundle exec jekyll serve --livereload

# Test with drafts
bundle exec jekyll serve --drafts

# Build for production
JEKYLL_ENV=production bundle exec jekyll build
```

### Version Control

```gitignore
# .gitignore
_site/
.jekyll-cache/
.jekyll-metadata
.sass-cache/
node_modules/
.bundle/
vendor/
```

### Keep Dependencies Updated

```bash
# Update GitHub Pages gem
bundle update github-pages

# Check for outdated gems
bundle outdated
```

---

## Custom Domains

### Recommended Configuration

1. **Use www subdomain** as primary - most stable
2. **Configure both apex and www** - automatic redirects
3. **Verify domain ownership** - prevents takeover
4. **Enable HTTPS** - always enforce

### DNS Best Practices

```
# Apex domain (A records)
@ → 185.199.108.153
@ → 185.199.109.153
@ → 185.199.110.153
@ → 185.199.111.153

# WWW subdomain (CNAME)
www → username.github.io
```

---

## Deployment

### Branch Deployment Best Practices

1. **Use protected branch** for publishing source
2. **Require reviews** before merging
3. **Test in preview** before production

### Actions Deployment Best Practices

1. **Separate build and deploy jobs**
2. **Use caching** for faster builds
3. **Pin action versions** for stability
4. **Enable concurrency control**

```yaml
concurrency:
  group: "pages"
  cancel-in-progress: false
```

### Pre-Deploy Checklist

- [ ] Content reviewed for accuracy
- [ ] Links tested
- [ ] Images optimized
- [ ] No sensitive data exposed
- [ ] Meta tags complete
- [ ] Local build successful
- [ ] Accessibility checked

---

## Monitoring

### Check Site Health

```bash
# Verify site is responding
curl -IL https://example.github.io

# Check response time
curl -w "@curl-format.txt" -o /dev/null -s https://example.github.io
```

### Monitor Builds

```bash
# Set up notifications for failed builds
# Check Actions tab regularly
gh run list --workflow=pages --limit 5
```

### Track Analytics

Use privacy-respecting analytics:
- Plausible Analytics
- Simple Analytics
- Fathom Analytics

Or self-hosted:
- Umami
- GoatCounter

---

## Common Mistakes to Avoid

| Mistake | Better Approach |
|---------|-----------------|
| Committing `_site/` | Add to .gitignore |
| Using absolute URLs | Use `{{ '' | relative_url }}` |
| Large unoptimized images | Compress and resize |
| No custom 404 page | Create `404.html` |
| Forgetting baseurl | Set for project sites |
| No meta descriptions | Add to all pages |
| Breaking changes on main | Use branches and PRs |
| Ignoring build errors | Monitor and fix promptly |

---

## Checklist for New Sites

### Initial Setup
- [ ] Repository created with correct name
- [ ] GitHub Pages enabled
- [ ] Publishing source configured
- [ ] Entry file (index.html/md) created
- [ ] Basic content added

### Configuration
- [ ] _config.yml configured (Jekyll)
- [ ] Theme selected
- [ ] Plugins enabled
- [ ] Baseurl set (project sites)
- [ ] CNAME added (custom domain)

### Content
- [ ] Homepage complete
- [ ] About page
- [ ] 404 page
- [ ] Navigation structure
- [ ] Meta tags and SEO

### Quality
- [ ] Mobile responsive
- [ ] Links tested
- [ ] Images optimized
- [ ] Accessibility checked
- [ ] Performance acceptable

### Security & Compliance
- [ ] HTTPS enabled
- [ ] No secrets exposed
- [ ] Domain verified
- [ ] Privacy policy (if collecting data)
