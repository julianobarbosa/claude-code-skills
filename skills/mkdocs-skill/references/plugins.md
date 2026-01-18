# MkDocs Plugins Guide

Complete guide to installing, configuring, and developing plugins.

## Installing Plugins

```bash
# Install from PyPI
pip install mkdocs-plugin-name

# Common naming convention
pip install mkdocs-[name]-plugin
```

## Configuring Plugins

```yaml
# Basic configuration
plugins:
  - search
  - tags
  - blog

# With options
plugins:
  - search:
      lang: en
      min_search_length: 3
  - tags:
      tags_file: tags.md

# Dictionary syntax (for inheritance)
plugins:
  search:
    lang: en
  tags:
    tags_file: tags.md

# Conditional activation
plugins:
  - search
  - code-validator:
      enabled: !ENV [CI, false]

# Disable all plugins
plugins: []
```

**Important:** Defining `plugins` disables defaults (like search). Re-add explicitly.

## Built-in Plugins

### Search Plugin

Full-text search using lunr.js. Enabled by default.

```yaml
plugins:
  - search:
      separator: '[\s\-]+'    # Word delimiters regex
      min_search_length: 3    # Minimum query length
      lang:                   # Language support
        - en
        - fr
      prebuild_index: false   # Pre-build for large sites
      indexing: full          # full, sections, titles
```

**Indexing Options:**
- `full` - Index all content
- `sections` - Index by section
- `titles` - Index titles only

## Material Theme Plugins

```bash
pip install mkdocs-material
```

**Blog Plugin:**
```yaml
plugins:
  - blog:
      enabled: true
      blog_dir: blog
      post_date_format: short
      post_url_format: "{date}/{slug}"
      archive: true
      categories: true
      pagination: true
      pagination_per_page: 10
```

**Tags Plugin:**
```yaml
plugins:
  - tags:
      tags_file: tags.md
      tags_slugify: !!python/object/apply:pymdownx.slugs.slugify
        kwds:
          case: lower
```

**Social Plugin:**
```yaml
plugins:
  - social:
      enabled: !ENV [CI, false]
      cards: true
      cards_color:
        fill: "#0FF1CE"
        text: "#FFFFFF"
      cards_font: Roboto
```

**Offline Plugin:**
```yaml
plugins:
  - offline:
      enabled: !ENV [OFFLINE, false]
```

**Privacy Plugin:**
```yaml
plugins:
  - privacy:
      enabled: !ENV [CI, false]
      assets_fetch: true
      assets_fetch_dir: assets/external
```

**Optimize Plugin (Images):**
```yaml
plugins:
  - optimize:
      enabled: !ENV [CI, false]
      optimize_png: true
      optimize_png_speed: 1
      optimize_jpg: true
      optimize_jpg_quality: 60
```

**Typeset Plugin:**
```yaml
plugins:
  - typeset
```

**Projects Plugin (Multi-project):**
```yaml
plugins:
  - projects:
      projects_dir: projects
```

## Navigation Plugins

### mkdocs-literate-nav

Navigation defined in Markdown files.

```bash
pip install mkdocs-literate-nav
```

```yaml
plugins:
  - literate-nav:
      nav_file: SUMMARY.md
      implicit_index: true
```

**docs/SUMMARY.md:**
```markdown
* [Home](index.md)
* User Guide
    * [Installation](guide/install.md)
    * [Configuration](guide/config.md)
* [API Reference](api/)
```

### mkdocs-awesome-pages

Directory-based navigation control.

```bash
pip install mkdocs-awesome-pages-plugin
```

```yaml
plugins:
  - awesome-pages:
      collapse_single_pages: true
      strict: false
```

**docs/user-guide/.pages:**
```yaml
title: User Guide
nav:
  - Introduction: index.md
  - installation.md
  - configuration.md
  - ...  # Rest alphabetically
```

### mkdocs-section-index

Section index pages (click section title).

```bash
pip install mkdocs-section-index
```

```yaml
plugins:
  - section-index
```

### mkdocs-gen-files

Generate pages dynamically during build.

```bash
pip install mkdocs-gen-files
```

```yaml
plugins:
  - gen-files:
      scripts:
        - scripts/gen_ref_pages.py
```

**scripts/gen_ref_pages.py:**
```python
import mkdocs_gen_files

with mkdocs_gen_files.open("generated.md", "w") as f:
    f.write("# Generated Page\n\nThis was generated!")

mkdocs_gen_files.set_edit_path("generated.md", "scripts/gen_ref_pages.py")
```

## Content Enhancement Plugins

### mkdocs-macros-plugin

Jinja2 templates, variables, and includes.

```bash
pip install mkdocs-macros-plugin
```

```yaml
plugins:
  - macros:
      module_name: main
      include_dir: snippets
      include_yaml:
        - vars.yml

extra:
  version: 1.0.0
  author: John Doe
```

**Usage in Markdown:**
```markdown
Version: {{ version }}
Author: {{ author }}

{% include 'disclaimer.md' %}

{% for item in config.nav %}
- {{ item }}
{% endfor %}
```

**main.py (custom macros):**
```python
def define_env(env):
    @env.macro
    def greet(name):
        return f"Hello, {name}!"

    env.variables['today'] = datetime.now().strftime('%Y-%m-%d')
```

### mkdocs-include-markdown

Include external Markdown files.

```bash
pip install mkdocs-include-markdown-plugin
```

```yaml
plugins:
  - include-markdown
```

**Usage:**
```markdown
{%
   include-markdown "../README.md"
   start="## Installation"
   end="## Usage"
%}

{%
   include-markdown "api/endpoints.md"
   heading-offset=1
%}
```

### mkdocs-markmap

Mindmaps from Markdown.

```bash
pip install mkdocs-markmap
```

```yaml
plugins:
  - markmap:
      base_path: docs
      d3_version: 7
      lib_version: 0.15
      view_version: 0.15
```

**Usage:**
````markdown
```markmap
# Root
## Branch 1
### Leaf 1.1
### Leaf 1.2
## Branch 2
### Leaf 2.1
```
````

### mkdocs-table-reader

Read tables from CSV, Excel, JSON.

```bash
pip install mkdocs-table-reader-plugin
```

```yaml
plugins:
  - table-reader
```

**Usage:**
```markdown
{{ read_csv('data/users.csv') }}
{{ read_excel('data/report.xlsx', sheet_name='Summary') }}
{{ read_json('data/config.json') }}
{{ read_yaml('data/settings.yml') }}
```

### neoteroi-timeline

Fancy timelines.

```bash
pip install neoteroi-mkdocs
```

```yaml
plugins:
  - neoteroi.timeline

markdown_extensions:
  - neoteroi.timeline
```

**Usage:**
```markdown
::timeline::

- date: 2024-01
  title: Project Start
  content: Initial planning and setup

- date: 2024-03
  title: Beta Release
  content: First public beta

::/timeline::
```

## Git Integration Plugins

### git-revision-date-localized

Show last updated dates.

```bash
pip install mkdocs-git-revision-date-localized-plugin
```

```yaml
plugins:
  - git-revision-date-localized:
      type: date                    # date, datetime, iso_date, iso_datetime, timeago
      fallback_to_build_date: true
      enable_creation_date: true
      timezone: America/New_York
      exclude:
        - index.md
```

**Template Usage:**
```jinja2
Last updated: {{ page.meta.git_revision_date_localized }}
Created: {{ page.meta.git_creation_date_localized }}
```

### git-committers

Show page contributors.

```bash
pip install mkdocs-git-committers-plugin-2
```

```yaml
plugins:
  - git-committers:
      repository: user/repo
      branch: main
      docs_path: docs/
      enabled: !ENV [CI, false]
```

### git-authors

Author attribution.

```bash
pip install mkdocs-git-authors-plugin
```

```yaml
plugins:
  - git-authors:
      show_contribution: true
      show_line_count: true
      count_empty_lines: false
```

## PDF Export Plugins

### mkdocs-print-site-plugin

Browser-based PDF via print.

```bash
pip install mkdocs-print-site-plugin
```

```yaml
plugins:
  - print-site:
      add_to_navigation: true
      print_page_title: 'Print Site'
      add_print_site_banner: true
      print_site_banner_template: "docs/assets/print_banner.tpl"
      add_table_of_contents: true
      toc_title: "Table of Contents"
      toc_depth: 3
      add_full_urls: true
      enumerate_headings: true
      enumerate_figures: true
      exclude:
        - index.md
        - changelog.md
```

### mkdocs-with-pdf

Direct PDF generation with WeasyPrint.

```bash
pip install mkdocs-with-pdf
```

```yaml
plugins:
  - with-pdf:
      author: John Doe
      copyright: "2024 Example Inc."
      cover: true
      cover_title: Project Documentation
      cover_subtitle: Version 1.0
      toc_title: Table of Contents
      toc_level: 3
      output_path: ../documentation.pdf
      enabled_if_env: ENABLE_PDF
```

### mkdocs-pdf-export-plugin

WeasyPrint-based export.

```bash
pip install mkdocs-pdf-export-plugin
```

```yaml
plugins:
  - pdf-export:
      combined: true
      combined_output_path: combined.pdf
      enabled_if_env: ENABLE_PDF
      media_type: print
```

### mkdocs-exporter

Highly configurable, single PDF.

```bash
pip install mkdocs-exporter
```

```yaml
plugins:
  - exporter:
      formats:
        pdf:
          enabled: !ENV [ENABLE_PDF, false]
          aggregator:
            enabled: true
            output: documentation.pdf
```

## Performance & Optimization Plugins

### mkdocs-minify-plugin

Minify HTML/CSS/JS output.

```bash
pip install mkdocs-minify-plugin
```

```yaml
plugins:
  - minify:
      minify_html: true
      minify_js: true
      minify_css: true
      htmlmin_opts:
        remove_comments: true
        remove_empty_space: true
      js_files:
        - js/*.js
      css_files:
        - css/*.css
```

### mkdocs-exclude

Exclude files from build.

```bash
pip install mkdocs-exclude
```

```yaml
plugins:
  - exclude:
      glob:
        - "*.tmp"
        - "drafts/*"
      regex:
        - '.*\.(bak|swp)$'
```

## Redirects Plugin

Handle URL changes.

```bash
pip install mkdocs-redirects
```

```yaml
plugins:
  - redirects:
      redirect_maps:
        'old-page.md': 'new-page.md'
        'old/path.md': 'new/path.md'
        'old-name.md': 'https://external.com/page'
```

## i18n / Internationalization

### mkdocs-static-i18n

Static translation files.

```bash
pip install mkdocs-static-i18n
```

```yaml
plugins:
  - i18n:
      docs_structure: suffix      # suffix or folder
      languages:
        - locale: en
          default: true
          name: English
          build: true
        - locale: fr
          name: Français
          build: true
          nav_translations:
            Home: Accueil
            User Guide: Guide Utilisateur
```

**With suffix structure:**
```
docs/
├── index.md          # English (default)
├── index.fr.md       # French
├── about.md
└── about.fr.md
```

**With folder structure:**
```
docs/
├── en/
│   ├── index.md
│   └── about.md
└── fr/
    ├── index.md
    └── about.md
```

## Plugin Development

### Basic Plugin Structure

```python
from mkdocs.plugins import BasePlugin
from mkdocs.config import config_options

class MyPlugin(BasePlugin):
    config_scheme = (
        ('option_name', config_options.Type(str, default='default')),
        ('enabled', config_options.Type(bool, default=True)),
        ('count', config_options.Type(int, default=10)),
    )

    def on_config(self, config, **kwargs):
        if not self.config['enabled']:
            return config
        # Modify config
        return config

    def on_page_markdown(self, markdown, page, config, files):
        # Process markdown
        return markdown.replace('OLD', 'NEW')
```

### Modern Config Pattern (MkDocs 1.4+)

```python
from mkdocs.plugins import BasePlugin
from mkdocs.config.base import Config
from mkdocs.config.config_options import Type, Optional, ListOfItems

class MyPluginConfig(Config):
    option_name = Type(str, default='default')
    enabled = Type(bool, default=True)
    items = ListOfItems(Type(str), default=[])

class MyPlugin(BasePlugin[MyPluginConfig]):
    def on_pre_build(self, config, **kwargs):
        # Access config as attributes
        if self.config.enabled:
            print(f"Option: {self.config.option_name}")
```

### Available Config Options

| Option Type | Description |
|-------------|-------------|
| `Type(type, default=value)` | Basic typed option |
| `Optional(option)` | Optional value |
| `File()` | File path validation |
| `Dir()` | Directory path validation |
| `Boolean()` | Boolean values |
| `Integer()` | Integer values |
| `Choice(choices)` | Restricted choices |
| `URL()` | URL format validation |
| `SubConfig(config_class)` | Nested configuration |
| `ListOfItems(option)` | List of validated items |

### Plugin Events

**One-Time Events:**
| Event | Description |
|-------|-------------|
| `on_startup(command, dirty)` | Invocation start |
| `on_shutdown()` | Invocation end |
| `on_serve(server, config, builder)` | Server start |

**Global Events:**
| Event | Description |
|-------|-------------|
| `on_config(config)` | After config loaded |
| `on_pre_build(config)` | Before build |
| `on_files(files, config)` | After files collected |
| `on_nav(nav, config, files)` | After nav created |
| `on_env(env, config, files)` | After Jinja env created |
| `on_post_build(config)` | After build complete |
| `on_build_error(error)` | On any error |

**Page Events:**
| Event | Description |
|-------|-------------|
| `on_pre_page(page, config, files)` | Before page actions |
| `on_page_markdown(markdown, page, config, files)` | After markdown loaded |
| `on_page_content(html, page, config, files)` | After HTML rendered |
| `on_page_context(context, page, config, nav)` | After context created |
| `on_post_page(output, page, config)` | After page rendered |

**Template Events:**
| Event | Description |
|-------|-------------|
| `on_pre_template(template, name, config)` | After template loaded |
| `on_template_context(context, name, config)` | After context created |
| `on_post_template(output, name, config)` | After template rendered |

### Event Priority

```python
from mkdocs.plugins import event_priority, BasePlugin

class MyPlugin(BasePlugin):
    @event_priority(100)  # Run first
    def on_files(self, files, config, **kwargs):
        pass

    @event_priority(-100)  # Run last
    def on_post_build(self, config, **kwargs):
        pass
```

**Priority Values:**
- `100+` - Run first
- `50` - Run early
- `0` - Default
- `-50` - Run late
- `-100` - Run last

### Combined Events (MkDocs 1.6+)

```python
from mkdocs.plugins import event_priority, CombinedEvent, BasePlugin

class MyPlugin(BasePlugin):
    @event_priority(100)
    def _on_page_markdown_first(self, markdown, **kwargs):
        return markdown.upper()

    @event_priority(-50)
    def _on_page_markdown_last(self, markdown, **kwargs):
        return markdown + "\n\n---\nGenerated content"

    on_page_markdown = CombinedEvent(
        _on_page_markdown_first,
        _on_page_markdown_last
    )
```

### Error Handling

```python
from mkdocs.exceptions import PluginError
from mkdocs.plugins import BasePlugin

class MyPlugin(BasePlugin):
    def on_page_markdown(self, markdown, page, **kwargs):
        try:
            result = self.process(markdown)
        except KeyError as e:
            raise PluginError(f"Missing required key: {e}")
        return result

    def on_build_error(self, error, **kwargs):
        # Cleanup on error
        self.cleanup()
```

### Logging

```python
import logging
from mkdocs.plugins import get_plugin_logger

# Option 1: Direct logging
log = logging.getLogger(f"mkdocs.plugins.{__name__}")

# Option 2: Convenience function (MkDocs 1.5+)
log = get_plugin_logger(__name__)

class MyPlugin(BasePlugin):
    def on_pre_build(self, config, **kwargs):
        log.warning("Always shown")   # Also fails in strict mode
        log.info("With --verbose")
        log.debug("With --debug")
```

### Packaging for Distribution

**Project Structure:**
```
mkdocs-myplugin/
├── setup.py
├── README.md
├── mkdocs_myplugin/
│   ├── __init__.py
│   └── plugin.py
```

**setup.py:**
```python
from setuptools import setup, find_packages

setup(
    name='mkdocs-myplugin',
    version='1.0.0',
    packages=find_packages(),
    install_requires=['mkdocs>=1.0'],
    entry_points={
        'mkdocs.plugins': [
            'myplugin = mkdocs_myplugin.plugin:MyPlugin',
        ]
    },
    python_requires='>=3.8',
)
```

## Native Hooks (MkDocs 1.4+)

Simple hooks without creating a package.

```yaml
hooks:
  - my_hooks.py
```

**my_hooks.py:**
```python
def on_page_markdown(markdown, page, config, files):
    """Process markdown before rendering."""
    return markdown.replace('{{VERSION}}', '1.0.0')

def on_post_build(config):
    """Run after build completes."""
    print("Build complete!")

def on_files(files, config):
    """Modify files collection."""
    for file in files:
        if file.src_uri.endswith('.draft.md'):
            files.remove(file)
    return files

def on_page_context(context, page, config, nav):
    """Add variables to page context."""
    context['custom_var'] = 'Custom Value'
    return context
```

## Plugin Discovery

Find plugins in the [MkDocs Catalog](https://github.com/mkdocs/catalog).

**Show Required Dependencies:**
```bash
mkdocs get-deps
pip install $(mkdocs get-deps)
```

## Quick Reference: Popular Plugins

| Category | Plugin | Purpose |
|----------|--------|---------|
| **Navigation** | literate-nav | Markdown-based nav |
| **Navigation** | awesome-pages | Directory `.pages` control |
| **Navigation** | section-index | Clickable section titles |
| **Content** | macros | Jinja2 variables/macros |
| **Content** | include-markdown | Include external files |
| **Content** | table-reader | CSV/Excel/JSON tables |
| **Git** | git-revision-date-localized | Last updated dates |
| **Git** | git-committers | Show contributors |
| **PDF** | print-site | Browser print to PDF |
| **PDF** | with-pdf | Direct PDF generation |
| **Performance** | minify | Minify HTML/CSS/JS |
| **Performance** | optimize | Image compression |
| **i18n** | static-i18n | Multi-language support |
| **Diagrams** | See [diagrams.md](diagrams.md) | Mermaid, PlantUML, D2 |
| **Versioning** | See [versioning.md](versioning.md) | mike multi-version |
| **API Docs** | See [api-docs.md](api-docs.md) | mkdocstrings, swagger |
