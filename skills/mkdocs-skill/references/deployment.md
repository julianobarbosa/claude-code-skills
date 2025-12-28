# MkDocs Deployment Guide

Complete guide to deploying MkDocs documentation sites.

## Build for Deployment

```bash
# Build static site
mkdocs build

# Output in site/ directory by default
mkdocs build --site-dir ./output

# Clean build (remove old files)
mkdocs build --clean

# Strict mode (fail on warnings)
mkdocs build --strict
```

## GitHub Pages

### Quick Deploy

```bash
# Deploy to gh-pages branch
mkdocs gh-deploy
```

This command:
1. Builds documentation
2. Creates/updates `gh-pages` branch
3. Pushes to GitHub
4. GitHub serves from gh-pages branch

### Deploy Options

```bash
# Custom commit message
mkdocs gh-deploy --message "Deploy version 1.2.0"

# Different branch
mkdocs gh-deploy --remote-branch docs

# Different remote
mkdocs gh-deploy --remote-name upstream

# Force push (overwrites history)
mkdocs gh-deploy --force

# Single commit (no history)
mkdocs gh-deploy --no-history

# Skip version check
mkdocs gh-deploy --ignore-version

# Use git shell commands
mkdocs gh-deploy --shell
```

### Project Pages vs User Pages

**Project Pages** (default):
- URL: `username.github.io/project-name/`
- Uses: `gh-pages` branch

**User/Organization Pages:**
```bash
# From project repo, deploy to user repo
cd ../username.github.io/
mkdocs gh-deploy \
  --config-file ../my-project/mkdocs.yml \
  --remote-branch master
```

### GitHub Actions CI/CD

**.github/workflows/docs.yml:**
```yaml
name: Deploy Documentation

on:
  push:
    branches:
      - main

permissions:
  contents: write

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.x'

      - name: Install dependencies
        run: |
          pip install mkdocs
          pip install mkdocs-material
          pip install $(mkdocs get-deps)

      - name: Build and deploy
        run: mkdocs gh-deploy --force
```

**With Material Theme Insiders:**
```yaml
name: Deploy Documentation

on:
  push:
    branches:
      - main

permissions:
  contents: write

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.x'

      - run: pip install mkdocs-material

      - name: Configure Git
        run: |
          git config user.name github-actions
          git config user.email github-actions@github.com

      - run: mkdocs gh-deploy --force
```

### Custom Domain

**1. Create CNAME file:**

Create `docs/CNAME` with your domain:
```
docs.example.com
```

**2. Configure DNS:**
- CNAME record: `docs.example.com` → `username.github.io`
- Or A records for apex domain

**3. Enable HTTPS:**
- Go to repository Settings → Pages
- Enable "Enforce HTTPS"

**mkdocs.yml:**
```yaml
site_url: https://docs.example.com/
```

## Read the Docs

### Setup

1. Connect repository to [readthedocs.org](https://readthedocs.org)
2. Import project
3. Configure build settings

### Configuration

**.readthedocs.yaml:**
```yaml
version: 2

build:
  os: ubuntu-22.04
  tools:
    python: "3.11"

mkdocs:
  configuration: mkdocs.yml

python:
  install:
    - requirements: docs/requirements.txt
```

**docs/requirements.txt:**
```
mkdocs>=1.5
mkdocs-material>=9.0
pymdown-extensions>=10.0
```

### Features

- Automatic builds on push
- Version management
- PDF/EPUB generation
- Search integration
- Custom domains
- Pull request previews

## GitLab Pages

**.gitlab-ci.yml:**
```yaml
image: python:3.11-alpine

pages:
  stage: deploy
  script:
    - pip install mkdocs mkdocs-material
    - mkdocs build --site-dir public
  artifacts:
    paths:
      - public
  only:
    - main
```

## Netlify

### Automatic Deploy

1. Connect repository to Netlify
2. Configure build settings:
   - Build command: `mkdocs build`
   - Publish directory: `site`

**netlify.toml:**
```toml
[build]
  command = "mkdocs build"
  publish = "site"

[build.environment]
  PYTHON_VERSION = "3.11"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

### Deploy Previews

Netlify automatically creates preview deployments for pull requests.

## Vercel

**vercel.json:**
```json
{
  "buildCommand": "pip install mkdocs mkdocs-material && mkdocs build",
  "outputDirectory": "site",
  "installCommand": "pip install mkdocs"
}
```

## Cloudflare Pages

1. Connect repository
2. Build settings:
   - Framework preset: None
   - Build command: `pip install mkdocs && mkdocs build`
   - Build output directory: `site`

## AWS S3 + CloudFront

### Build and Upload

```bash
# Build
mkdocs build

# Sync to S3
aws s3 sync site/ s3://your-bucket-name/ \
  --delete \
  --cache-control "max-age=86400"

# Invalidate CloudFront
aws cloudfront create-invalidation \
  --distribution-id YOUR_DISTRIBUTION_ID \
  --paths "/*"
```

### Terraform Configuration

```hcl
resource "aws_s3_bucket" "docs" {
  bucket = "docs.example.com"
}

resource "aws_s3_bucket_website_configuration" "docs" {
  bucket = aws_s3_bucket.docs.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "404.html"
  }
}

resource "aws_cloudfront_distribution" "docs" {
  origin {
    domain_name = aws_s3_bucket.docs.bucket_regional_domain_name
    origin_id   = "S3-docs"
  }

  enabled             = true
  default_root_object = "index.html"

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-docs"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 86400
    max_ttl                = 31536000
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }
}
```

## Self-Hosted / Generic Hosting

### Build and Transfer

```bash
# Build static files
mkdocs build

# Transfer via SCP
scp -r site/* user@server:/var/www/html/

# Or rsync
rsync -avz --delete site/ user@server:/var/www/html/

# Or FTP
lftp -u user,password server -e "mirror -R site/ /public_html; quit"
```

### Nginx Configuration

```nginx
server {
    listen 80;
    server_name docs.example.com;
    root /var/www/docs;
    index index.html;

    location / {
        try_files $uri $uri/ $uri.html =404;
    }

    error_page 404 /404.html;

    # Cache static assets
    location ~* \.(css|js|png|jpg|gif|ico|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### Apache Configuration

```apache
<VirtualHost *:80>
    ServerName docs.example.com
    DocumentRoot /var/www/docs

    <Directory /var/www/docs>
        Options -Indexes +FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>

    ErrorDocument 404 /404.html

    # Cache static assets
    <FilesMatch "\.(css|js|png|jpg|gif|ico|woff2)$">
        ExpiresActive On
        ExpiresDefault "access plus 1 year"
    </FilesMatch>
</VirtualHost>
```

## Offline / Local Distribution

### Configuration for Offline Use

```yaml
site_url: ""
use_directory_urls: false
plugins: []  # Disable search (requires JavaScript)
```

### Create Distribution Package

```bash
# Build with offline settings
mkdocs build

# Create archive
cd site
zip -r ../documentation.zip .
# or
tar -czvf ../documentation.tar.gz .
```

### PDF Generation

```bash
pip install mkdocs-pdf-export-plugin
```

```yaml
plugins:
  - search
  - pdf-export:
      enabled_if_env: ENABLE_PDF
      combined: true
```

## Version Management

### Multiple Versions with mike

```bash
pip install mike
```

```bash
# Deploy version
mike deploy 1.0 latest -u

# Deploy specific version
mike deploy 1.1

# Set default
mike set-default latest

# List versions
mike list
```

**mkdocs.yml:**
```yaml
extra:
  version:
    provider: mike
```

## Troubleshooting

### Common Issues

**404 errors on refresh:**
- Ensure `use_directory_urls: true`
- Configure server for SPA routing

**Broken internal links:**
- Use relative paths
- Link to `.md` files, not `.html`
- Run `mkdocs build --strict` to catch issues

**Search not working:**
- Ensure search plugin is enabled
- Check for JavaScript errors
- Verify `search_index.json` exists

**Large site slow to build:**
- Enable `prebuild_index: true` in search config
- Use `--dirty` flag for incremental builds

### Verification

```bash
# Serve locally and verify
mkdocs serve

# Check for broken links
mkdocs build --strict

# Verify all pages accessible
curl -s http://localhost:8000/sitemap.xml | grep -o '<loc>[^<]*</loc>'
```
