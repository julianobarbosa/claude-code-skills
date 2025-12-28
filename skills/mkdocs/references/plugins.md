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

## Popular Third-Party Plugins

### Material Theme Plugins

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

**Search Plugin (Enhanced):**
```yaml
plugins:
  - search:
      separator: '[\s\-\.]+'
      lang:
        - en
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

### Other Popular Plugins

**Minify:**
```bash
pip install mkdocs-minify-plugin
```
```yaml
plugins:
  - minify:
      minify_html: true
      minify_js: true
      minify_css: true
```

**Redirects:**
```bash
pip install mkdocs-redirects
```
```yaml
plugins:
  - redirects:
      redirect_maps:
        'old-page.md': 'new-page.md'
        'old/path.md': 'new/path.md'
```

**Macros:**
```bash
pip install mkdocs-macros-plugin
```
```yaml
plugins:
  - macros:
      module_name: main
      include_dir: snippets
```

**Git Revision Date:**
```bash
pip install mkdocs-git-revision-date-localized-plugin
```
```yaml
plugins:
  - git-revision-date-localized:
      type: date
      fallback_to_build_date: true
```

**Print Site:**
```bash
pip install mkdocs-print-site-plugin
```
```yaml
plugins:
  - print-site:
      add_to_navigation: true
      print_page_title: 'Print Site'
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
