#!/bin/bash
# Initialize a new Python project with modern tooling
# Usage: ./init-project.sh <project-name> [--flask]

set -e

PROJECT_NAME="${1:-my-project}"
INCLUDE_FLASK=false

# Parse arguments
for arg in "$@"; do
    case $arg in
        --flask)
            INCLUDE_FLASK=true
            shift
            ;;
    esac
done

echo "🐍 Creating Python project: $PROJECT_NAME"

# Initialize with uv
uv init "$PROJECT_NAME"
cd "$PROJECT_NAME"

# Create directory structure
mkdir -p src/"${PROJECT_NAME//-/_}"
mkdir -p tests
mkdir -p scripts

# Create __init__.py
cat > src/"${PROJECT_NAME//-/_}"/__init__.py << 'EOF'
"""Package initialization."""

__version__ = "0.1.0"
EOF

# Create main module
cat > src/"${PROJECT_NAME//-/_}"/main.py << 'EOF'
"""Main module."""


def main() -> None:
    """Entry point."""
    print("Hello from the project!")


if __name__ == "__main__":
    main()
EOF

# Create test file
cat > tests/test_main.py << 'EOF'
"""Tests for main module."""

import pytest


def test_placeholder() -> None:
    """Placeholder test."""
    assert True
EOF

# Add dev dependencies
uv add --dev pytest ruff mypy

# Add Flask if requested
if [ "$INCLUDE_FLASK" = true ]; then
    echo "🌶️ Adding Flask..."
    uv add flask

    mkdir -p static/css static/js templates

    # Create Flask app
    cat > app.py << 'EOF'
"""Flask application."""

from flask import Flask, render_template

app = Flask(__name__)


@app.route("/")
def index() -> str:
    """Home page."""
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
EOF

    # Create base template
    cat > templates/base.html << 'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}App{% endblock %}</title>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
</head>
<body>
    <main>
        {% block content %}{% endblock %}
    </main>
    <script src="{{ url_for('static', filename='js/main.js') }}"></script>
</body>
</html>
EOF

    # Create index template
    cat > templates/index.html << 'EOF'
{% extends "base.html" %}

{% block title %}Home{% endblock %}

{% block content %}
<h1>Welcome!</h1>
<p>Your Flask application is running.</p>
{% endblock %}
EOF

    # Create empty CSS/JS
    touch static/css/style.css
    touch static/js/main.js
fi

# Sync dependencies
uv sync

echo "✅ Project created successfully!"
echo ""
echo "Next steps:"
echo "  cd $PROJECT_NAME"
echo "  uv run pytest              # Run tests"
echo "  uv run ruff check .        # Check code"
if [ "$INCLUDE_FLASK" = true ]; then
    echo "  uv run flask run --debug   # Start Flask server"
fi
