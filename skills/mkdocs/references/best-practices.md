# MkDocs Best Practices

Guidelines for creating high-quality documentation sites.

## Project Organization

### Directory Structure

```
project/
├── mkdocs.yml              # Configuration
├── docs/
│   ├── index.md            # Homepage
│   ├── getting-started/
│   │   ├── index.md        # Section intro
│   │   ├── installation.md
│   │   └── quick-start.md
│   ├── user-guide/
│   │   ├── index.md
│   │   ├── configuration.md
│   │   └── advanced.md
│   ├── api/
│   │   └── reference.md
│   ├── assets/
│   │   ├── images/
│   │   └── files/
│   └── stylesheets/
│       └── extra.css
├── overrides/              # Theme customizations
│   └── main.html
└── scripts/                # Build scripts
    └── generate-api-docs.py
```

### Naming Conventions

- Use lowercase filenames: `getting-started.md`
- Use hyphens for spaces: `user-guide.md` not `user_guide.md`
- Use `index.md` for directory homepages
- Consistent naming across sections

### File Organization

- **One topic per file**: Each file covers one concept
- **Logical grouping**: Related topics in same directory
- **Progressive depth**: Overview → Details → Advanced
- **Keep files focused**: Under 500 lines ideally

## Writing Quality

### Document Structure

```markdown
# Page Title

Brief introduction explaining what this page covers.

## First Major Section

Content here...

### Subsection

More detailed content...

## Second Major Section

More content...

## See Also

- [Related Page](related.md)
- [External Resource](https://example.com)
```

### Heading Hierarchy

- One `#` heading per page (document title)
- Use sequential levels: `##` → `###` → `####`
- Don't skip levels
- Keep headings concise

### Code Examples

**Always include language identifier:**
````markdown
```python
def hello():
    print("Hello, World!")
```
````

**Show both input and output:**
````markdown
```bash
$ mkdocs serve
INFO    -  Building documentation...
INFO    -  Serving on http://127.0.0.1:8000
```
````

**Use annotations (Material theme):**
````markdown
```python
def process(data):  # (1)!
    return data.strip()  # (2)!
```

1. Function accepts any string data
2. Removes leading/trailing whitespace
````

### Links

**Internal links - use relative paths:**
```markdown
[Configuration Guide](configuration.md)
[Installation](../getting-started/installation.md)
[Options Section](configuration.md#options)
```

**External links - open in new tab (Material):**
```markdown
[Python Docs](https://docs.python.org/){target=_blank}
```

**Avoid:**
- Absolute paths: `/docs/guide.md`
- URLs for internal links
- Broken anchors

## Configuration

### Essential Settings

```yaml
# Always set these
site_name: Project Name
site_url: https://docs.example.com/

# Highly recommended
site_description: Brief project description
repo_url: https://github.com/org/project

# SEO and linking
edit_uri: edit/main/docs/
copyright: Copyright 2024 Organization
```

### Navigation Best Practices

```yaml
nav:
  - Home: index.md
  # Group related items
  - Getting Started:
    - Installation: getting-started/installation.md
    - Quick Start: getting-started/quick-start.md
  # Limit nesting to 2-3 levels
  - User Guide:
    - Overview: user-guide/index.md
    - Configuration: user-guide/configuration.md
  # Keep most important items first
  - API Reference: api/
  # External links at end
  - GitHub: https://github.com/org/project
```

### Validation

```yaml
# Enable strict validation
strict: true

validation:
  nav:
    omitted_files: warn
    not_found: warn
    absolute_links: warn
  links:
    not_found: warn
    anchors: warn
```

## Performance

### Build Performance

```yaml
# For large sites, pre-build search index
plugins:
  - search:
      prebuild_index: true

# During development, use dirty builds
# mkdocs serve --dirty
```

### Page Load Performance

```yaml
# Minify output
plugins:
  - minify:
      minify_html: true
      minify_js: true

# Optimize images before adding to docs
# Use WebP format when possible
```

### Image Optimization

```bash
# Optimize PNGs
optipng -o7 docs/images/*.png

# Convert to WebP
cwebp -q 80 image.png -o image.webp
```

**Include proper alt text:**
```markdown
![Screenshot of configuration page](images/config.png)
```

## SEO

### Page Metadata

```yaml
---
title: Configuration Guide
description: Complete guide to configuring Project Name
---

# Configuration Guide
```

### Site Configuration

```yaml
site_name: Project Name
site_url: https://docs.example.com/
site_description: Documentation for Project Name

# Social metadata (Material theme)
extra:
  social:
    - icon: fontawesome/brands/github
      link: https://github.com/org/project
    - icon: fontawesome/brands/twitter
      link: https://twitter.com/project
```

### Sitemap

MkDocs generates `sitemap.xml` automatically when `site_url` is set.

## Accessibility

### Images

```markdown
![Descriptive alt text](image.png)
```

### Links

```markdown
<!-- Good: Descriptive text -->
[Read the installation guide](installation.md)

<!-- Avoid: Vague text -->
[Click here](installation.md)
```

### Headings

- Use proper heading hierarchy
- Don't use headings just for styling
- Keep headings descriptive

### Colors

- Ensure sufficient contrast
- Don't rely on color alone
- Test with accessibility tools

## Version Control

### .gitignore

```gitignore
# MkDocs build output
site/

# Python
__pycache__/
*.py[cod]
.venv/
venv/

# IDE
.idea/
.vscode/

# OS
.DS_Store
Thumbs.db
```

### CI/CD Checks

```yaml
# .github/workflows/docs.yml
name: Documentation

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.x'
      - run: pip install mkdocs mkdocs-material
      - run: mkdocs build --strict
```

## Content Maintenance

### Regular Reviews

- Check for broken links quarterly
- Update outdated content
- Remove deprecated sections
- Verify code examples work

### Changelog

Maintain a changelog for documentation:
```markdown
# Changelog

## 2024-01-15
- Added API authentication section
- Updated installation guide for v2.0
- Fixed broken links in user guide
```

### Deprecation

```markdown
!!! warning "Deprecated"
    This feature is deprecated and will be removed in v3.0.
    See [New Feature](new-feature.md) for the replacement.
```

## Common Patterns

### Tabbed Content (Material)

```markdown
=== "Python"

    ```python
    print("Hello")
    ```

=== "JavaScript"

    ```javascript
    console.log("Hello");
    ```
```

### Admonitions

```markdown
!!! note
    This is a note.

!!! warning
    This is a warning.

!!! danger
    This is dangerous!

!!! tip
    This is a helpful tip.
```

### Collapsible Sections

```markdown
??? note "Click to expand"
    Hidden content here.

???+ note "Expanded by default"
    Visible content here.
```

## Checklist

### Before Publishing

- [ ] All pages have descriptive titles
- [ ] Navigation is logical and complete
- [ ] Internal links work (`mkdocs build --strict`)
- [ ] Code examples are tested
- [ ] Images have alt text
- [ ] site_url is configured correctly
- [ ] Search works properly
- [ ] Mobile view is acceptable
- [ ] 404 page exists

### Regular Maintenance

- [ ] Check for broken external links
- [ ] Update deprecated content
- [ ] Review and update code examples
- [ ] Check analytics for problem pages
- [ ] Test search functionality
- [ ] Verify deployment pipeline works
