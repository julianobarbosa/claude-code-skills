# MkDocs Configuration Reference

Complete reference for all `mkdocs.yml` configuration options.

## Site Information

| Option | Type | Required | Default | Description |
|--------|------|----------|---------|-------------|
| `site_name` | String | **Yes** | None | Main title for your project |
| `site_url` | String | No | `null` | Canonical URL (adds link tag in head) |
| `site_description` | String | No | `null` | Site description meta tag |
| `site_author` | String | No | `null` | Author name meta tag |
| `copyright` | String | No | `null` | Copyright text in footer |

## Repository Settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `repo_url` | String | `null` | Repository link (GitHub/GitLab/Bitbucket) |
| `repo_name` | String | Auto-detected | Repository link text |
| `edit_uri` | String | `edit/master/docs/` | Path for "Edit on GitHub" links |
| `edit_uri_template` | String | `null` | Template with `{path}` placeholder |
| `remote_branch` | String | `gh-pages` | GitHub Pages deploy branch |
| `remote_name` | String | `origin` | Git remote name for deploy |

## Build Directories

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `docs_dir` | String | `docs` | Source markdown directory |
| `site_dir` | String | `site` | Output HTML directory |

## Navigation

```yaml
# Automatic (alphabetically sorted if omitted)
# nav: auto-generated

# Explicit navigation
nav:
  - Home: index.md
  - 'User Guide':
    - Overview: user-guide/overview.md
    - Installation: user-guide/install.md
  - API Reference: api/index.md
  - GitHub: https://github.com/example/repo

# File patterns
exclude_docs: |
  /drafts/
  *.py
  /templates/

draft_docs: |
  drafts/

not_in_nav: |
  snippets/
```

## Theme Configuration

```yaml
theme:
  name: mkdocs              # or 'readthedocs', 'material', etc.
  locale: en                # Language code
  custom_dir: custom_theme/ # Override directory

  # mkdocs theme options
  color_mode: auto          # light, dark, auto
  user_color_mode_toggle: true
  nav_style: primary        # primary, dark, light
  highlightjs: true
  hljs_style: github
  hljs_style_dark: github-dark
  hljs_languages:
    - yaml
    - rust
  navigation_depth: 2
  shortcuts:
    help: 191               # ? key
    next: 78                # n key
    previous: 80            # p key
    search: 83              # s key
  analytics:
    gtag: G-XXXXXXXXXX

  # readthedocs theme options
  prev_next_buttons_location: bottom  # bottom, top, both, none
  navigation_depth: 4
  collapse_navigation: true
  titles_only: false
  sticky_navigation: true
  include_homepage_in_sidebar: true
  logo: img/logo.png
```

## Assets

```yaml
extra_css:
  - css/extra.css
  - css/print.css

extra_javascript:
  - js/extra.js
  - path: js/analytics.mjs
    type: module
  - path: js/deferred.js
    defer: true
  - path: js/async.js
    async: true

extra_templates:
  - sitemap.html
```

## Markdown Extensions

```yaml
markdown_extensions:
  # Built-in (always active)
  - meta          # Page metadata
  - toc:          # Table of contents
      permalink: true
      permalink_title: Link to this section
      baselevel: 1
      separator: "-"
      toc_depth: 3
  - tables        # Table syntax
  - fenced_code   # Code blocks

  # Common additions
  - smarty        # Smart quotes
  - admonition    # Note/warning boxes
  - abbr          # Abbreviations
  - attr_list     # Attribute lists
  - def_list      # Definition lists
  - footnotes     # Footnotes
  - md_in_html    # Markdown inside HTML

  # PyMdown Extensions (pip install pymdown-extensions)
  - pymdownx.highlight:
      anchor_linenums: true
  - pymdownx.superfences
  - pymdownx.tabbed:
      alternate_style: true
  - pymdownx.details
  - pymdownx.emoji
  - pymdownx.keys
  - pymdownx.mark
  - pymdownx.critic
  - pymdownx.caret
  - pymdownx.tilde
```

## Plugins

```yaml
plugins:
  - search:
      separator: '[\s\-]+'
      min_search_length: 3
      lang:
        - en
        - fr
      prebuild_index: false    # true for large sites
      indexing: full           # full, sections, titles

  - tags:
      tags_file: tags.md

  - blog:
      enabled: true
      post_date_format: short

  # Conditional activation
  - code-validator:
      enabled: !ENV [CI, false]
```

**Important:** Defining `plugins` disables defaults. Re-add `search` explicitly.

## Build Settings

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `use_directory_urls` | Boolean | `true` | Pretty URLs (`/about/` vs `/about.html`) |
| `strict` | Boolean | `false` | Fail build on warnings |
| `dev_addr` | String | `127.0.0.1:8000` | Development server address |
| `watch` | List | `[]` | Additional directories to watch |

## Validation

```yaml
validation:
  nav:
    omitted_files: warn    # warn, info, ignore
    not_found: warn
    absolute_links: warn
  links:
    not_found: warn
    anchors: warn
    absolute_links: relative_to_docs  # MkDocs 1.6+
    unrecognized_links: warn
```

## Hooks

```yaml
hooks:
  - my_hooks.py
```

**Hook file (my_hooks.py):**
```python
def on_page_markdown(markdown, page, config, files):
    return markdown.replace('OLD', 'NEW')

def on_post_build(config):
    print("Build complete!")
```

## Custom Variables

```yaml
extra:
  version: 1.0.0
  environment: production
  social:
    - icon: fontawesome/brands/github
      link: https://github.com/example
    - icon: fontawesome/brands/twitter
      link: https://twitter.com/example
```

Access in templates: `{{ config.extra.version }}`

## Environment Variables

```yaml
# Single variable
site_name: !ENV SITE_NAME

# With fallback
site_name: !ENV [SITE_NAME, 'Default Name']

# Multiple fallbacks
api_key: !ENV [API_KEY_PROD, API_KEY_DEV, 'default']
```

## Configuration Inheritance

```yaml
# child.yml
INHERIT: ../base.yml
site_name: Child Project
# Overrides base.yml settings
```

**Notes:**
- Uses deep merge for dictionaries
- Lists are replaced, not appended
- Navigation cannot be merged

## Complete Example

```yaml
site_name: My Project
site_url: https://docs.example.com/
site_description: Project documentation
site_author: John Doe
copyright: Copyright 2024 Example Inc.

repo_url: https://github.com/example/project
repo_name: GitHub
edit_uri: edit/main/docs/

docs_dir: docs
site_dir: build

nav:
  - Home: index.md
  - Getting Started:
    - Installation: getting-started/installation.md
    - Quick Start: getting-started/quickstart.md
  - User Guide:
    - Configuration: user-guide/configuration.md
    - Advanced: user-guide/advanced.md
  - API Reference: api/
  - Changelog: changelog.md
  - GitHub: https://github.com/example/project

theme:
  name: material
  palette:
    primary: indigo
  features:
    - navigation.tabs
    - search.suggest
  custom_dir: overrides/

extra_css:
  - stylesheets/extra.css

extra_javascript:
  - scripts/extra.js

markdown_extensions:
  - toc:
      permalink: true
  - admonition
  - pymdownx.highlight
  - pymdownx.superfences
  - pymdownx.tabbed:
      alternate_style: true

plugins:
  - search:
      lang: en
  - tags

validation:
  nav:
    omitted_files: warn
  links:
    not_found: warn

extra:
  version: !ENV [VERSION, 'dev']
  analytics:
    provider: google
    property: G-XXXXXXXXXX
```
