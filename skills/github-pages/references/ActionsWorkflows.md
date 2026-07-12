# GitHub Actions Workflows Reference

Complete reference for deploying GitHub Pages with custom Actions workflows.

---

## Core Actions

### Official GitHub Pages Actions

| Action | Purpose |
|--------|---------|
| `actions/checkout@v4` | Clone repository |
| `actions/configure-pages@v4` | Setup Pages configuration |
| `actions/upload-pages-artifact@v3` | Package build output |
| `actions/deploy-pages@v4` | Deploy to GitHub Pages |

---

## Required Configuration

### Workflow Permissions

```yaml
permissions:
  contents: read
  pages: write
  id-token: write
```

### Concurrency Control

```yaml
concurrency:
  group: "pages"
  cancel-in-progress: false
```

### Environment Configuration

```yaml
environment:
  name: github-pages
  url: ${{ steps.deployment.outputs.page_url }}
```

---

## Workflow Templates

### Static HTML Site

For sites with no build step required.

```yaml
name: Deploy static site to Pages

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Pages
        uses: actions/configure-pages@v4

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: '.'

      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

### Jekyll Site

```yaml
name: Deploy Jekyll site to Pages

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Ruby
        uses: ruby/setup-ruby@v1
        with:
          ruby-version: '3.2'
          bundler-cache: true

      - name: Setup Pages
        id: pages
        uses: actions/configure-pages@v4

      - name: Build with Jekyll
        run: bundle exec jekyll build --baseurl "${{ steps.pages.outputs.base_path }}"
        env:
          JEKYLL_ENV: production

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3

  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    needs: build
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

### Hugo Site

```yaml
name: Deploy Hugo site to Pages

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    env:
      HUGO_VERSION: 0.121.0
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          submodules: recursive
          fetch-depth: 0

      - name: Setup Hugo
        uses: peaceiris/actions-hugo@v2
        with:
          hugo-version: ${{ env.HUGO_VERSION }}
          extended: true

      - name: Setup Pages
        id: pages
        uses: actions/configure-pages@v4

      - name: Build with Hugo
        env:
          HUGO_ENVIRONMENT: production
          HUGO_ENV: production
        run: |
          hugo \
            --gc \
            --minify \
            --baseURL "${{ steps.pages.outputs.base_url }}/"

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: ./public

  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    needs: build
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

### Next.js (Static Export)

```yaml
name: Deploy Next.js site to Pages

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Setup Pages
        uses: actions/configure-pages@v4
        with:
          static_site_generator: next

      - name: Install dependencies
        run: npm ci

      - name: Build with Next.js
        run: npm run build

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: ./out

  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    needs: build
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

**Note:** Requires `next.config.js` with:
```javascript
const nextConfig = {
  output: 'export',
  images: { unoptimized: true }
}
module.exports = nextConfig
```

### Gatsby

```yaml
name: Deploy Gatsby site to Pages

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Setup Pages
        uses: actions/configure-pages@v4
        with:
          static_site_generator: gatsby

      - name: Install dependencies
        run: npm ci

      - name: Build with Gatsby
        run: npm run build
        env:
          PREFIX_PATHS: 'true'

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: ./public

  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    needs: build
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

### Astro

```yaml
name: Deploy Astro site to Pages

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Build with Astro
        run: npm run build

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: ./dist

  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    needs: build
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

### MkDocs

```yaml
name: Deploy MkDocs site to Pages

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.x'
          cache: 'pip'

      - name: Install dependencies
        run: pip install mkdocs mkdocs-material

      - name: Build with MkDocs
        run: mkdocs build

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: ./site

  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    needs: build
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

### VuePress / VitePress

```yaml
name: Deploy VitePress site to Pages

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - name: Install dependencies
        run: npm ci

      - name: Build with VitePress
        run: npm run docs:build

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: docs/.vitepress/dist

  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    runs-on: ubuntu-latest
    needs: build
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

---

## Action Configuration Options

### configure-pages

```yaml
- uses: actions/configure-pages@v4
  with:
    # Static site generator type
    static_site_generator: ""  # next, nuxt, gatsby, sveltekit

    # Custom token
    token: ${{ secrets.GITHUB_TOKEN }}

    # Enable pages (default: true)
    enablement: true
```

**Outputs:**
- `base_url` - Full base URL
- `origin` - Site origin
- `host` - Site host
- `base_path` - Base path (for project sites)

### upload-pages-artifact

```yaml
- uses: actions/upload-pages-artifact@v3
  with:
    # Path to upload
    path: ./build

    # Artifact name
    name: github-pages

    # Retention period
    retention-days: 1
```

### deploy-pages

```yaml
- uses: actions/deploy-pages@v4
  with:
    # Custom token
    token: ${{ secrets.GITHUB_TOKEN }}

    # Deployment timeout
    timeout: 600000  # 10 minutes

    # Error count threshold
    error_count: 10

    # Reporting interval
    reporting_interval: 5000  # 5 seconds

    # Artifact name
    artifact_name: github-pages
```

**Outputs:**
- `page_url` - Deployed site URL

---

## Advanced Patterns

### Caching Dependencies

```yaml
- name: Setup Node
  uses: actions/setup-node@v4
  with:
    node-version: '20'
    cache: 'npm'  # or 'yarn', 'pnpm'

- name: Setup Ruby
  uses: ruby/setup-ruby@v1
  with:
    ruby-version: '3.2'
    bundler-cache: true

- name: Setup Python
  uses: actions/setup-python@v5
  with:
    python-version: '3.x'
    cache: 'pip'
```

### Deploy Only on Tag

```yaml
on:
  push:
    tags:
      - 'v*'
```

### Deploy with Manual Approval

```yaml
environment:
  name: production
```

Then configure environment protection rules in repository settings.

### Conditional Deployment

```yaml
- name: Deploy to GitHub Pages
  if: github.ref == 'refs/heads/main'
  uses: actions/deploy-pages@v4
```

### Matrix Build

```yaml
jobs:
  build:
    strategy:
      matrix:
        node-version: [18, 20]
    steps:
      - uses: actions/setup-node@v4
        with:
          node-version: ${{ matrix.node-version }}
```

---

## Debugging

### View Logs

```bash
# List workflow runs
gh run list --workflow=deploy.yml

# View specific run
gh run view <run-id> --log

# View failed steps only
gh run view <run-id> --log-failed
```

### Enable Debug Logging

Add repository secrets:
- `ACTIONS_RUNNER_DEBUG`: `true`
- `ACTIONS_STEP_DEBUG`: `true`

### Common Errors

**Permission denied:**
- Ensure workflow has required permissions
- Check repository settings allow Actions deployments

**Artifact not found:**
- Verify upload-pages-artifact path exists
- Check build output directory

**Timeout:**
- Increase timeout in deploy-pages action
- Optimize build process

---

## Best Practices

1. **Separate build and deploy jobs** - Easier debugging
2. **Use caching** - Faster builds
3. **Pin action versions** - Reproducible builds
4. **Enable concurrency control** - Prevent race conditions
5. **Use workflow_dispatch** - Allow manual triggers
6. **Store secrets securely** - Use repository secrets
7. **Test locally first** - Verify build before pushing
