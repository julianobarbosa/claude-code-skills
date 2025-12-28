# MkDocs Themes Guide

Complete guide to theme selection, configuration, and customization.

## Built-in Themes

### mkdocs Theme (Default)

Bootstrap-based theme with modern features.

```yaml
theme:
  name: mkdocs
  locale: en
  color_mode: auto              # light, dark, auto
  user_color_mode_toggle: true  # Show toggle button
  nav_style: primary            # primary, dark, light
  highlightjs: true
  hljs_style: github
  hljs_style_dark: github-dark
  hljs_languages:
    - yaml
    - rust
    - go
  navigation_depth: 2
  shortcuts:
    help: 191     # ?
    next: 78      # n
    previous: 80  # p
    search: 83    # s
  analytics:
    gtag: G-XXXXXXXXXX
```

**Supported Locales:**
en, de, es, fa, fr, id, it, ja, nb, nl, nn, pl, pt_BR, ru, tr, uk, zh_CN, zh_TW

### readthedocs Theme

Classic documentation theme from Read the Docs.

```yaml
theme:
  name: readthedocs
  locale: en
  highlightjs: true
  hljs_languages:
    - yaml
  include_homepage_in_sidebar: true
  prev_next_buttons_location: bottom  # bottom, top, both, none
  navigation_depth: 4
  collapse_navigation: true
  titles_only: false
  sticky_navigation: true
  logo: img/logo.png
  analytics:
    gtag: G-XXXXXXXXXX
    anonymize_ip: true
```

**Limitations:**
- Only 2 levels of navigation in sidebar
- Limited customization options

## Material for MkDocs (Third-Party)

Most popular third-party theme with extensive features.

### Installation

```bash
pip install mkdocs-material
```

### Basic Configuration

```yaml
theme:
  name: material
  palette:
    primary: indigo
    accent: indigo
  font:
    text: Roboto
    code: Roboto Mono
  logo: assets/logo.png
  favicon: assets/favicon.png
  language: en
```

### Color Palette

```yaml
theme:
  name: material
  palette:
    # Light mode
    - scheme: default
      primary: indigo
      accent: indigo
      toggle:
        icon: material/brightness-7
        name: Switch to dark mode
    # Dark mode
    - scheme: slate
      primary: indigo
      accent: indigo
      toggle:
        icon: material/brightness-4
        name: Switch to light mode
```

### Navigation Features

```yaml
theme:
  name: material
  features:
    - navigation.tabs           # Top navigation tabs
    - navigation.tabs.sticky    # Sticky tabs
    - navigation.sections       # Expandable sections
    - navigation.expand         # Expand all by default
    - navigation.path           # Breadcrumbs
    - navigation.top            # Back to top button
    - navigation.indexes        # Section index pages
    - navigation.instant        # Instant loading
    - navigation.tracking       # Anchor tracking
    - toc.integrate             # Integrate TOC in nav
    - toc.follow                # Auto-scroll TOC
```

### Search Features

```yaml
theme:
  name: material
  features:
    - search.suggest    # Search suggestions
    - search.highlight  # Highlight matches
    - search.share      # Share search
```

### Code Features

```yaml
theme:
  name: material
  features:
    - content.code.copy       # Copy button
    - content.code.annotate   # Code annotations
    - content.tabs.link       # Link content tabs
```

### Full Material Configuration

```yaml
theme:
  name: material
  custom_dir: overrides
  language: en
  palette:
    - scheme: default
      primary: indigo
      accent: indigo
      toggle:
        icon: material/brightness-7
        name: Switch to dark mode
    - scheme: slate
      primary: indigo
      accent: indigo
      toggle:
        icon: material/brightness-4
        name: Switch to light mode
  font:
    text: Roboto
    code: Roboto Mono
  logo: assets/logo.png
  favicon: assets/favicon.png
  icon:
    repo: fontawesome/brands/github
  features:
    - navigation.tabs
    - navigation.sections
    - navigation.expand
    - navigation.path
    - navigation.top
    - navigation.indexes
    - navigation.instant
    - search.suggest
    - search.highlight
    - content.code.copy
    - content.code.annotate
    - content.tabs.link
```

## Theme Customization

### Using Extra CSS/JS

```yaml
theme:
  name: mkdocs

extra_css:
  - css/extra.css

extra_javascript:
  - js/extra.js
```

**docs/css/extra.css:**
```css
:root {
  --md-primary-fg-color: #1a73e8;
}

.md-header {
  background-color: var(--md-primary-fg-color);
}
```

### Custom Theme Directory

Override theme files without modifying the original.

```yaml
theme:
  name: mkdocs
  custom_dir: custom_theme/
```

**Directory Structure:**
```
custom_theme/
├── css/
│   └── extra.css
├── js/
│   └── extra.js
├── img/
│   └── favicon.ico
├── 404.html
└── main.html
```

### Template Block Overrides

Create `main.html` to extend base template:

```jinja2
{% extends "base.html" %}

{% block htmltitle %}
<title>Custom Title - {{ page.title }}</title>
{% endblock %}

{% block content %}
{{ super() }}
<div class="custom-section">
  Custom content here
</div>
{% endblock %}

{% block footer %}
{{ super() }}
<script>console.log("Footer loaded");</script>
{% endblock %}
```

**Available Blocks:**

| Block | Description |
|-------|-------------|
| `site_meta` | Meta tags in head |
| `htmltitle` | Page title |
| `styles` | Stylesheet links |
| `libs` | JavaScript libraries |
| `scripts` | JavaScript after page load |
| `analytics` | Analytics scripts |
| `extrahead` | Custom content in head |
| `site_name` | Site name in nav |
| `site_nav` | Navigation |
| `search_button` | Search box |
| `next_prev` | Next/Previous buttons |
| `repo` | Repository link |
| `content` | Page content |
| `footer` | Page footer |

### Custom 404 Page

Create `custom_theme/404.html`:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Page Not Found</title>
</head>
<body>
    <h1>404 - Page Not Found</h1>
    <p>The page you're looking for doesn't exist.</p>
    <a href="{{ base_url }}">Go to Homepage</a>
</body>
</html>
```

## Template Variables

### Global Variables

| Variable | Description |
|----------|-------------|
| `config` | MkDocsConfig object |
| `nav` | Navigation structure |
| `base_url` | Relative path to root |
| `mkdocs_version` | MkDocs version |
| `build_date_utc` | Build timestamp |
| `pages` | All File objects |
| `page` | Current page object |

### Page Object

| Attribute | Description |
|-----------|-------------|
| `page.title` | Page title |
| `page.content` | Rendered HTML |
| `page.toc` | Table of contents |
| `page.meta` | Page metadata |
| `page.url` | Relative URL |
| `page.abs_url` | Absolute URL |
| `page.canonical_url` | Full canonical URL |
| `page.edit_url` | Edit on GitHub link |
| `page.is_homepage` | Boolean |
| `page.previous_page` | Previous page object |
| `page.next_page` | Next page object |

### Template Filters

| Filter | Description |
|--------|-------------|
| `url` | Normalize URLs |
| `tojson` | Convert to JSON |
| `script_tag` | Generate script tag |

**Usage:**
```jinja2
<link href="{{ 'css/extra.css' | url }}" rel="stylesheet">
<script>var data = {{ config.extra | tojson }};</script>
{{ 'js/extra.js' | script_tag }}
```

## Creating Custom Themes

### Minimal Theme Structure

```
my-theme/
├── main.html       # Required - main template
└── mkdocs_theme.yml  # Theme configuration
```

**main.html:**
```jinja2
<!DOCTYPE html>
<html>
<head>
    <title>{% if page.title %}{{ page.title }} - {% endif %}{{ config.site_name }}</title>
    {% for path in config.extra_css %}
    <link href="{{ path | url }}" rel="stylesheet">
    {% endfor %}
</head>
<body>
    <nav>
        {% for nav_item in nav %}
            <a href="{{ nav_item.url | url }}">{{ nav_item.title }}</a>
        {% endfor %}
    </nav>
    <main>
        {{ page.content }}
    </main>
    {% for script in config.extra_javascript %}
    {{ script | script_tag }}
    {% endfor %}
</body>
</html>
```

**mkdocs_theme.yml:**
```yaml
extends: null
locale: en
static_templates:
  - 404.html
include_search_page: true
search_index_only: false
```

### Packaging for Distribution

**Project Structure:**
```
mkdocs-mytheme/
├── setup.py
├── MANIFEST.in
├── README.md
└── mkdocs_mytheme/
    ├── __init__.py
    ├── mkdocs_theme.yml
    ├── main.html
    ├── css/
    │   └── style.css
    └── js/
        └── app.js
```

**setup.py:**
```python
from setuptools import setup

setup(
    name='mkdocs-mytheme',
    version='1.0.0',
    packages=['mkdocs_mytheme'],
    include_package_data=True,
    entry_points={
        'mkdocs.themes': [
            'mytheme = mkdocs_mytheme',
        ]
    }
)
```

**MANIFEST.in:**
```
recursive-include mkdocs_mytheme *.html *.css *.js *.yml
```

## Popular Third-Party Themes

| Theme | Description |
|-------|-------------|
| **Material** | Feature-rich, modern design |
| **Cinder** | Clean, sidebar navigation |
| **Windmill** | Light/dark mode support |
| **ReadTheDocs Dropdown** | Enhanced ReadTheDocs |
| **GitBook** | GitBook-style layout |
| **Bootstrap4** | Bootstrap framework |
| **Ivory** | Minimal, clean design |
| **Terminal** | Terminal/CLI aesthetic |
| **Dracula** | Dark theme with Dracula colors |

Install via pip:
```bash
pip install mkdocs-material
pip install mkdocs-cinder
pip install mkdocs-windmill
```

## Theme Localization

### Enable i18n Support

```bash
pip install 'mkdocs[i18n]'
```

### Configure Locale

```yaml
theme:
  name: mkdocs
  locale: fr
```

**Notes:**
- Theme translations only affect UI elements (Next, Previous, Search, etc.)
- Content translation requires separate i18n plugin
- Locales use ISO 639-1 codes (en, de, fr, etc.)
