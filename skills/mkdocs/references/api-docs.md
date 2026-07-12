# MkDocs API Documentation Guide

Complete guide to generating API documentation from code.

## mkdocstrings

Auto-generate documentation from Python docstrings.

### Installation

```bash
pip install mkdocstrings[python]
```

### Basic Configuration

```yaml
# mkdocs.yml
plugins:
  - mkdocstrings:
      handlers:
        python:
          paths: [src]
          options:
            show_source: true
            show_root_heading: true
```

### Usage in Markdown

```markdown
# API Reference

## MyClass

::: mypackage.mymodule.MyClass
    options:
      show_source: true
      members:
        - __init__
        - process
        - save
```

### Auto-Generate All Modules

Use with gen-files plugin for automatic generation:

```yaml
plugins:
  - gen-files:
      scripts:
        - scripts/gen_ref_pages.py
  - literate-nav:
      nav_file: SUMMARY.md
  - mkdocstrings
```

**scripts/gen_ref_pages.py:**
```python
"""Generate API reference pages."""
from pathlib import Path
import mkdocs_gen_files

nav = mkdocs_gen_files.Nav()
src = Path("src")

for path in sorted(src.rglob("*.py")):
    module_path = path.relative_to(src).with_suffix("")
    doc_path = path.relative_to(src).with_suffix(".md")
    full_doc_path = Path("reference", doc_path)

    parts = tuple(module_path.parts)

    if parts[-1] == "__init__":
        parts = parts[:-1]
        doc_path = doc_path.with_name("index.md")
        full_doc_path = full_doc_path.with_name("index.md")
    elif parts[-1] == "__main__":
        continue

    nav[parts] = doc_path.as_posix()

    with mkdocs_gen_files.open(full_doc_path, "w") as fd:
        ident = ".".join(parts)
        fd.write(f"::: {ident}")

    mkdocs_gen_files.set_edit_path(full_doc_path, path)

with mkdocs_gen_files.open("reference/SUMMARY.md", "w") as nav_file:
    nav_file.writelines(nav.build_literate_nav())
```

### Configuration Options

```yaml
plugins:
  - mkdocstrings:
      default_handler: python
      handlers:
        python:
          paths: [src]
          options:
            # Headings
            show_root_heading: true
            show_root_full_path: false
            show_root_toc_entry: true
            heading_level: 2

            # Members
            members: true
            members_order: source  # source, alphabetical
            filters:
              - "!^_"  # exclude private
              - "^__init__$"  # include __init__
            group_by_category: true
            show_category_heading: true

            # Docstrings
            docstring_style: google  # google, numpy, sphinx
            docstring_options:
              ignore_init_summary: true
            show_if_no_docstring: false

            # Signatures
            show_signature: true
            show_signature_annotations: true
            separate_signature: true
            line_length: 80

            # Source
            show_source: true
            show_bases: true
            show_submodules: true

            # Inheritance
            inherited_members: false
            merge_init_into_class: true
```

### Docstring Styles

**Google Style (Recommended):**
```python
def fetch_data(url: str, timeout: int = 30) -> dict:
    """Fetch data from the specified URL.

    Args:
        url: The URL to fetch data from.
        timeout: Request timeout in seconds.

    Returns:
        A dictionary containing the response data.

    Raises:
        HTTPError: If the request fails.
        TimeoutError: If the request times out.

    Examples:
        >>> fetch_data("https://api.example.com/data")
        {'status': 'ok', 'data': [...]}
    """
```

**NumPy Style:**
```python
def fetch_data(url: str, timeout: int = 30) -> dict:
    """
    Fetch data from the specified URL.

    Parameters
    ----------
    url : str
        The URL to fetch data from.
    timeout : int, optional
        Request timeout in seconds (default: 30).

    Returns
    -------
    dict
        A dictionary containing the response data.

    Raises
    ------
    HTTPError
        If the request fails.
    TimeoutError
        If the request times out.
    """
```

**Sphinx Style:**
```python
def fetch_data(url: str, timeout: int = 30) -> dict:
    """Fetch data from the specified URL.

    :param url: The URL to fetch data from.
    :type url: str
    :param timeout: Request timeout in seconds.
    :type timeout: int
    :returns: A dictionary containing the response data.
    :rtype: dict
    :raises HTTPError: If the request fails.
    :raises TimeoutError: If the request times out.
    """
```

### Cross-References

Link to other objects:

```markdown
See the [`MyClass`][mypackage.mymodule.MyClass] for more details.

The [`process`][mypackage.mymodule.MyClass.process] method handles data.
```

### Multi-Language Support

mkdocstrings supports multiple languages via handlers:

```bash
# Python (default)
pip install mkdocstrings[python]

# Crystal
pip install mkdocstrings[crystal]

# Shell/Bash
pip install mkdocstrings-shell
```

## mkdocs-click

Generate documentation for Click CLI applications.

### Installation

```bash
pip install mkdocs-click
```

### Configuration

```yaml
# mkdocs.yml
markdown_extensions:
  - mkdocs-click
```

### Usage

```markdown
# CLI Reference

::: mkdocs_click
    :module: myapp.cli
    :command: main
    :prog_name: myapp
    :depth: 2
    :style: table  # table, plain
```

### Click Application Example

```python
# myapp/cli.py
import click

@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output.')
def main(verbose):
    """MyApp - A sample CLI application.

    This application demonstrates Click documentation generation.
    """
    pass

@main.command()
@click.argument('name')
@click.option('--greeting', '-g', default='Hello', help='Greeting to use.')
def greet(name, greeting):
    """Greet a person by name.

    This command outputs a personalized greeting message.
    """
    click.echo(f"{greeting}, {name}!")

@main.command()
@click.option('--count', '-n', default=1, help='Number of times to repeat.')
def repeat(count):
    """Repeat a message multiple times."""
    for _ in range(count):
        click.echo("Repeating...")
```

## mkdocs-swagger-ui-tag

Embed OpenAPI/Swagger documentation.

### Installation

```bash
pip install mkdocs-swagger-ui-tag
```

### Configuration

```yaml
plugins:
  - swagger-ui-tag:
      supportedSubmitMethods: []  # Disable "Try it out"
      syntaxHighlightTheme: monokai
```

### Usage

```markdown
# API Documentation

<swagger-ui src="./openapi.yaml"/>
```

Or with remote spec:

```markdown
<swagger-ui src="https://petstore.swagger.io/v2/swagger.json"/>
```

### Configuration Options

```yaml
plugins:
  - swagger-ui-tag:
      background: White
      docExpansion: list  # none, list, full
      filter: true
      syntaxHighlightTheme: monokai
      tryItOutEnabled: false
      supportedSubmitMethods: []
      validatorUrl: none
```

## mkdocs-redoc

Alternative OpenAPI renderer using ReDoc.

### Installation

```bash
pip install mkdocs-render-swagger-plugin
```

### Configuration

```yaml
plugins:
  - render_swagger
```

### Usage

```markdown
# API Reference

!!swagger openapi.yaml!!
```

## mkdocs-typer

Generate documentation for Typer CLI applications.

### Installation

```bash
pip install mkdocs-typer
```

### Configuration

```yaml
markdown_extensions:
  - mkdocs-typer
```

### Usage

```markdown
::: mkdocs-typer
    :module: myapp.cli
    :command: app
    :prog_name: myapp
```

## griffe

Modern Python API documentation tool (used by mkdocstrings).

### Direct Usage

```python
# Generate API inventory
import griffe

package = griffe.load("mypackage")
for module in package.modules.values():
    print(f"Module: {module.name}")
    for cls in module.classes.values():
        print(f"  Class: {cls.name}")
        for method in cls.functions.values():
            print(f"    Method: {method.name}")
```

### Extensions

Create custom griffe extensions:

```python
# extensions.py
from griffe import Extension, Object, ObjectNode

class MyExtension(Extension):
    def on_instance(self, node: ObjectNode, obj: Object) -> None:
        # Modify object attributes
        if obj.is_function:
            obj.labels.add("custom-label")
```

```yaml
plugins:
  - mkdocstrings:
      handlers:
        python:
          options:
            extensions:
              - extensions:MyExtension
```

## Combining Tools

### Full API Documentation Setup

```yaml
# mkdocs.yml
theme:
  name: material

plugins:
  - search
  - gen-files:
      scripts:
        - scripts/gen_ref_pages.py
  - literate-nav:
      nav_file: SUMMARY.md
  - section-index
  - mkdocstrings:
      handlers:
        python:
          paths: [src]
          options:
            show_source: true
            show_root_heading: true
            docstring_style: google
            merge_init_into_class: true
            group_by_category: true
  - swagger-ui-tag

markdown_extensions:
  - mkdocs-click
  - pymdownx.highlight
  - pymdownx.superfences
```

### Navigation Structure

```yaml
nav:
  - Home: index.md
  - User Guide:
    - Getting Started: guide/getting-started.md
    - Configuration: guide/configuration.md
  - API Reference:
    - Overview: reference/index.md
    - Python API: reference/  # Auto-generated
  - REST API:
    - Endpoints: api/endpoints.md  # Swagger UI
  - CLI Reference:
    - Commands: cli/commands.md  # mkdocs-click
```

## Best Practices

### Write Good Docstrings

```python
class DataProcessor:
    """Process and transform data from various sources.

    This class provides methods for loading, transforming, and
    exporting data in multiple formats.

    Attributes:
        source: The data source path or URL.
        format: The output format (json, csv, parquet).

    Example:
        >>> processor = DataProcessor("data.csv")
        >>> processor.transform()
        >>> processor.export("output.json")
    """

    def __init__(self, source: str, format: str = "json") -> None:
        """Initialize the data processor.

        Args:
            source: Path or URL to the data source.
            format: Output format. Defaults to "json".
        """
        self.source = source
        self.format = format
```

### Organize API Reference

```
docs/
├── reference/
│   ├── index.md          # API overview
│   ├── SUMMARY.md        # Auto-generated nav
│   ├── core/
│   │   ├── index.md
│   │   └── processor.md
│   └── utils/
│       ├── index.md
│       └── helpers.md
```

### Use Type Hints

```python
from typing import Optional, List, Dict, Any

def process_items(
    items: List[Dict[str, Any]],
    filter_fn: Optional[callable] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """Process a list of items with optional filtering.

    Args:
        items: List of item dictionaries to process.
        filter_fn: Optional function to filter items.
        limit: Maximum number of items to return.

    Returns:
        Processed and optionally filtered list of items.
    """
```

### Add Examples

```python
def parse_config(path: str) -> dict:
    """Parse a configuration file.

    Args:
        path: Path to the configuration file.

    Returns:
        Parsed configuration as a dictionary.

    Examples:
        Basic usage:

        >>> config = parse_config("config.yaml")
        >>> config["database"]["host"]
        'localhost'

        With environment variables:

        >>> import os
        >>> os.environ["DB_HOST"] = "production.db"
        >>> config = parse_config("config.yaml")
        >>> config["database"]["host"]
        'production.db'
    """
```

## Comparison Table

| Tool | Purpose | Input | Output |
|------|---------|-------|--------|
| mkdocstrings | Python API docs | Docstrings | Markdown |
| mkdocs-click | Click CLI docs | Click app | Markdown |
| mkdocs-typer | Typer CLI docs | Typer app | Markdown |
| swagger-ui-tag | REST API docs | OpenAPI spec | Interactive UI |
| gen-files | Auto-generate | Python | Markdown files |
