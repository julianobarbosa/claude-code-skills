# MkDocs Versioning Guide

Complete guide to managing multiple documentation versions with mike and other tools.

## mike - Multi-Version Documentation

mike is the standard tool for deploying multiple documentation versions to GitHub Pages.

### Installation

```bash
pip install mike
```

### How mike Works

mike deploys documentation versions to separate directories on your `gh-pages` branch:

```
gh-pages/
├── 1.0/
│   └── (docs for v1.0)
├── 1.1/
│   └── (docs for v1.1)
├── latest/
│   └── (alias pointing to 1.1)
├── versions.json
└── index.html (redirect)
```

## Basic Usage

### Deploy a Version

```bash
# Deploy current docs as version 1.0
mike deploy 1.0

# Deploy and set as default alias
mike deploy 1.0 latest

# Update latest to point to new version
mike deploy 1.1 latest --update-aliases
```

### Aliases

Aliases are symbolic names that point to versions:

```bash
# Create alias "latest" pointing to 1.0
mike alias 1.0 latest

# Create alias "stable" pointing to 1.0
mike alias 1.0 stable

# Update "latest" to point to 1.1
mike alias 1.1 latest --update
```

### Set Default Version

```bash
# Set "latest" as the default (shown at root URL)
mike set-default latest

# Set specific version as default
mike set-default 1.0
```

### List Versions

```bash
# Show all deployed versions
mike list
```

Output:
```
1.1 [latest]
1.0 [stable]
0.9
```

### Delete Versions

```bash
# Delete a specific version
mike delete 0.9

# Delete all versions
mike delete --all
```

### Local Preview

```bash
# Serve all versions locally
mike serve
```

Access at http://localhost:8000 - navigate between versions.

## Configuration

### mkdocs.yml Setup

```yaml
site_url: https://username.github.io/project/

theme:
  name: material

extra:
  version:
    provider: mike
    default: latest
```

### Version Selector (Material Theme)

The Material theme automatically shows a version selector when `version.provider: mike` is configured.

```yaml
theme:
  name: material

extra:
  version:
    provider: mike
    default: latest
    alias: true  # Show aliases in selector
```

### Custom Version Warning

Add a banner for old versions:

```yaml
# mkdocs.yml
extra:
  version:
    provider: mike
    default: latest
```

**docs/overrides/main.html:**
```jinja2
{% extends "base.html" %}

{% block announce %}
  {% if config.extra.version %}
    {% set versions = config.extra.versions | default([]) %}
    {% if version != "latest" %}
      <div class="md-banner">
        <div class="md-banner__inner md-grid md-typeset">
          You're viewing an old version.
          <a href="{{ config.site_url }}latest/">View latest</a>
        </div>
      </div>
    {% endif %}
  {% endif %}
{% endblock %}
```

## CI/CD Integration

### GitHub Actions - On Release

```yaml
# .github/workflows/docs.yml
name: Deploy Docs

on:
  push:
    tags:
      - 'v*'

permissions:
  contents: write

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: actions/setup-python@v5
        with:
          python-version: '3.x'

      - name: Install dependencies
        run: |
          pip install mkdocs-material mike

      - name: Configure Git
        run: |
          git config user.name github-actions
          git config user.email github-actions@github.com

      - name: Get version
        id: version
        run: echo "version=${GITHUB_REF#refs/tags/v}" >> $GITHUB_OUTPUT

      - name: Deploy docs
        run: |
          mike deploy ${{ steps.version.outputs.version }} latest --update-aliases --push
```

### GitHub Actions - On Push to Main

For dev/nightly documentation:

```yaml
name: Deploy Dev Docs

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
        with:
          fetch-depth: 0

      - uses: actions/setup-python@v5
        with:
          python-version: '3.x'

      - run: pip install mkdocs-material mike

      - name: Configure Git
        run: |
          git config user.name github-actions
          git config user.email github-actions@github.com

      - name: Deploy dev docs
        run: mike deploy dev --push
```

### Combined Workflow

```yaml
name: Documentation

on:
  push:
    branches:
      - main
    tags:
      - 'v*'

permissions:
  contents: write

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: actions/setup-python@v5
        with:
          python-version: '3.x'

      - run: pip install mkdocs-material mike

      - name: Configure Git
        run: |
          git config user.name github-actions
          git config user.email github-actions@github.com

      - name: Deploy version
        run: |
          if [[ "$GITHUB_REF" == refs/tags/v* ]]; then
            VERSION="${GITHUB_REF#refs/tags/v}"
            mike deploy "$VERSION" latest --update-aliases --push
          else
            mike deploy dev --push
          fi
```

## Version Strategies

### Semantic Versioning

Deploy each minor version:

```bash
# Major versions
mike deploy 1.0 --push
mike deploy 2.0 --push

# With minor versions
mike deploy 1.0.0 --push
mike deploy 1.0.1 --push
mike deploy 1.1.0 --push
```

### Major Version Only

Keep only major versions to reduce clutter:

```bash
mike deploy 1 latest --update-aliases --push
mike deploy 2 latest --update-aliases --push
```

### Named Releases

Use meaningful aliases:

```bash
mike deploy 1.0 stable --push
mike deploy 1.1 beta --push
mike deploy main dev --push
```

### Branch-Based

Deploy docs from different branches:

```bash
# On main branch
mike deploy dev --push

# On release/1.0 branch
mike deploy 1.0 stable --push

# On release/2.0 branch
mike deploy 2.0 latest --push
```

## Advanced Configuration

### Custom Branch

Deploy to a different branch:

```bash
mike deploy 1.0 --branch docs-versions --push
```

```yaml
# mkdocs.yml
remote_branch: docs-versions
```

### Custom Remote

Deploy to a different remote:

```bash
mike deploy 1.0 --remote upstream --push
```

### Prefix Path

For project pages with subdirectory:

```yaml
# mkdocs.yml
site_url: https://org.github.io/project/
```

### Version Warning Script

Add a script to warn users on old versions:

**docs/javascripts/version-warning.js:**
```javascript
document.addEventListener("DOMContentLoaded", function() {
  var defined = document.body.dataset.mdVersion !== undefined;
  var version = document.body.dataset.mdVersion;

  if (defined && version !== "latest" && version !== "dev") {
    var banner = document.createElement("div");
    banner.className = "version-warning";
    banner.innerHTML =
      "This is documentation for version " + version + ". " +
      "<a href='/latest/'>View the latest version</a>.";
    document.body.insertBefore(banner, document.body.firstChild);
  }
});
```

```yaml
# mkdocs.yml
extra_javascript:
  - javascripts/version-warning.js
```

## Alternative: mkdocs-versioning

Alternative plugin for version management.

### Installation

```bash
pip install mkdocs-versioning
```

### Configuration

```yaml
plugins:
  - versioning:
      version: 1.0
      version_selector: true
      exclude:
        - changelog.md
```

## Alternative: Manual Versioning

For simple cases, manage versions manually:

### Directory Structure

```
docs-repo/
├── v1/
│   ├── mkdocs.yml
│   └── docs/
├── v2/
│   ├── mkdocs.yml
│   └── docs/
└── build-all.sh
```

### Build Script

```bash
#!/bin/bash
# build-all.sh

for version in v1 v2; do
  cd "$version"
  mkdocs build --site-dir "../site/$version"
  cd ..
done

# Create redirect at root
echo '<meta http-equiv="refresh" content="0; url=v2/">' > site/index.html
```

## Troubleshooting

### Version Not Showing

1. Check `versions.json` exists on gh-pages:
```bash
git checkout gh-pages
cat versions.json
```

2. Verify mike configuration:
```yaml
extra:
  version:
    provider: mike
```

### Alias Not Updating

Use `--update-aliases` flag:
```bash
mike deploy 1.1 latest --update-aliases --push
```

### Broken Links Between Versions

Use relative links in documentation:
```markdown
[See configuration](../configuration.md)
```

Avoid absolute paths that include version:
```markdown
<!-- Bad -->
[Docs](/1.0/configuration/)

<!-- Good -->
[Docs](configuration.md)
```

### Local Preview Issues

Ensure you're serving with mike:
```bash
# Correct
mike serve

# Wrong (won't show version selector)
mkdocs serve
```

## Command Reference

| Command | Description |
|---------|-------------|
| `mike deploy VERSION [ALIAS...]` | Deploy docs as VERSION |
| `mike alias VERSION ALIAS` | Create/update alias |
| `mike retitle VERSION TITLE` | Change version title |
| `mike set-default VERSION` | Set default redirect |
| `mike delete VERSION` | Delete a version |
| `mike list` | List all versions |
| `mike serve` | Serve locally |

**Common Flags:**
- `--push` - Push to remote after deploy
- `--update-aliases` - Update existing aliases
- `--branch BRANCH` - Use different branch
- `--remote REMOTE` - Use different remote
- `--prefix PREFIX` - Add URL prefix

## Best Practices

1. **Use Aliases** - Always use `latest` alias for current stable
2. **Automate Deploys** - Use CI/CD for consistent deployments
3. **Version Warning** - Show banner on old versions
4. **Clean Up** - Delete very old versions periodically
5. **Semantic Names** - Use `latest`, `stable`, `dev` aliases
6. **Test Locally** - Preview with `mike serve` before deploying
