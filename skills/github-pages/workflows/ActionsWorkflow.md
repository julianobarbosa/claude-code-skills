# ActionsWorkflow Workflow

Setup custom GitHub Actions workflow for GitHub Pages deployment.

## Checklist

- [ ] Identify static site generator
- [ ] Configure GitHub Pages for Actions
- [ ] Create workflow file
- [ ] Configure build settings
- [ ] Deploy and verify

---

## When to Use Actions

Use GitHub Actions instead of branch deployment when:

- Using non-Jekyll static site generators (Hugo, Gatsby, Next.js, etc.)
- Need custom build process
- Require specific Node.js/Ruby versions
- Want build caching for faster deploys
- Need to run tests before deployment

---

## Step 1: Configure GitHub Pages

1. Go to repository Settings > Pages
2. Under "Build and deployment", select "GitHub Actions"
3. This enables Actions-based deployment

---

## Step 2: Create Workflow File

Create `.github/workflows/deploy-pages.yml`

### Generic Static Site

```yaml
name: Deploy to GitHub Pages

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

      - name: Setup Pages
        uses: actions/configure-pages@v4

      - name: Upload artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: '.'  # Upload entire repository

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

### Astro Site

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

---

## Step 3: Disable Jekyll (If Not Using)

Create `.nojekyll` file in repository root:

```bash
touch .nojekyll
git add .nojekyll
git commit -m "Disable Jekyll processing"
```

---

## Key Actions Reference

| Action | Purpose |
|--------|---------|
| `actions/checkout@v4` | Clone repository |
| `actions/configure-pages@v4` | Configure Pages settings |
| `actions/upload-pages-artifact@v3` | Package build for deployment |
| `actions/deploy-pages@v4` | Deploy to GitHub Pages |

---

## Configuration Options

### configure-pages Options

```yaml
- uses: actions/configure-pages@v4
  with:
    # For generators that need base path
    static_site_generator: next  # or: nuxt, gatsby, sveltekit

    # Custom token (if needed)
    token: ${{ secrets.GITHUB_TOKEN }}
```

### upload-pages-artifact Options

```yaml
- uses: actions/upload-pages-artifact@v3
  with:
    # Directory to upload
    path: ./build

    # Artifact name (default: github-pages)
    name: github-pages

    # Retention days
    retention-days: 1
```

---

## Troubleshooting

### Deployment Timeout

- Ensure build completes within 10 minutes
- Optimize build process or split into stages
- Check artifact size (max 10GB compressed)

### Permission Errors

Ensure workflow has correct permissions:

```yaml
permissions:
  contents: read
  pages: write
  id-token: write
```

### Base Path Issues

For project sites, configure base path:

```yaml
- name: Setup Pages
  id: pages
  uses: actions/configure-pages@v4

- name: Build
  run: npm run build
  env:
    BASE_PATH: ${{ steps.pages.outputs.base_path }}
```

---

## Best Practices

1. **Use caching** - Cache dependencies for faster builds
2. **Pin action versions** - Use specific versions (@v4 not @latest)
3. **Separate build and deploy** - Easier debugging
4. **Use concurrency** - Prevent overlapping deployments
5. **Enable workflow_dispatch** - Allow manual triggers
